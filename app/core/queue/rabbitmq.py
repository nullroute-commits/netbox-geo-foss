"""RabbitMQ client configuration and utilities.

Provides message queuing functionality for the application.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import os
import json
import time
import logging
import threading
import pika
from typing import Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# Thread local storage for RabbitMQ connections
_thread_locals = threading.local()


class RabbitMQClient:
    """
    RabbitMQ client wrapper with additional functionality.

    Features:
    - Connection pooling
    - Automatic reconnection
    - Queue declaration
    - Dead-letter handling
    - Message acknowledgment
    - Serialization
    """

    def __init__(self, host: str, port: int, username: str, password: str,
                 virtual_host: str = '/', **kwargs):
        """
        Initialize the RabbitMQ client.

        Args:
            host: RabbitMQ server hostname
            port: RabbitMQ server port
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
            **kwargs: Additional arguments for pika.ConnectionParameters
        """
        self.connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            credentials=pika.PlainCredentials(username, password),
            heartbeat=int(os.environ.get('RABBITMQ_HEARTBEAT', '60')),
            blocked_connection_timeout=int(os.environ.get('RABBITMQ_BLOCKED_TIMEOUT', '300')),
            **kwargs
        )
        self.connection = None
        self.channel = None
        self.exchange = os.environ.get('RABBITMQ_EXCHANGE', 'app.topic')
        self.connect()
        logger.info(f"Initialized RabbitMQ client with host: {host}:{port}")

    def connect(self) -> None:
        """
        Establish connection to RabbitMQ server.

        Raises:
            pika.exceptions.AMQPConnectionError: If connection fails
        """
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()

            # Declare default exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='topic',
                durable=True
            )

            # Declare dead-letter exchange
            self.channel.exchange_declare(
                exchange=f"{self.exchange}.dlx",
                exchange_type='topic',
                durable=True
            )

            logger.info("Connected to RabbitMQ")
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def ensure_connected(self) -> None:
        """
        Ensure connection to RabbitMQ is active.

        Reconnects if connection is closed.
        """
        if not self.connection or self.connection.is_closed:
            logger.warning("RabbitMQ connection is closed, reconnecting...")
            self.connect()

    def declare_queue(self, queue_name: str, durable: bool = True,
                      dead_letter: bool = True) -> str:
        """
        Declare a queue.

        Args:
            queue_name: Name of the queue
            durable: Whether queue should survive server restarts
            dead_letter: Whether to set up dead-letter queue

        Returns:
            Queue name
        """
        self.ensure_connected()

        arguments = {}
        if dead_letter:
            arguments['x-dead-letter-exchange'] = f"{self.exchange}.dlx"
            arguments['x-dead-letter-routing-key'] = f"{queue_name}.dead"

        self.channel.queue_declare(
            queue=queue_name,
            durable=durable,
            arguments=arguments
        )

        if dead_letter:
            # Declare the dead-letter queue
            self.channel.queue_declare(
                queue=f"{queue_name}.dead",
                durable=True
            )

            # Bind the dead-letter queue to the dead-letter exchange
            self.channel.queue_bind(
                exchange=f"{self.exchange}.dlx",
                queue=f"{queue_name}.dead",
                routing_key=f"{queue_name}.dead"
            )

        logger.debug(f"Declared queue: {queue_name}")
        return queue_name

    def publish(self, routing_key: str, message: Any,
                persistent: bool = True, **properties) -> bool:
        """
        Publish a message.

        Args:
            routing_key: Routing key
            message: Message to publish (will be JSON serialized)
            persistent: Whether message should survive server restarts
            **properties: Additional message properties

        Returns:
            True if successful, False otherwise
        """
        self.ensure_connected()

        try:
            # Serialize message to JSON if it's not already a string
            if not isinstance(message, str):
                message = json.dumps(message)

            # Convert string to bytes if necessary
            if isinstance(message, str):
                message = message.encode('utf-8')

            # Default properties
            props = {
                'delivery_mode': 2 if persistent else 1,  # 2 for persistent
                'timestamp': int(time.time()),
                'content_type': 'application/json',
            }
            # Update with user-provided properties
            props.update(properties)

            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(**props)
            )
            logger.debug(f"Published message to {routing_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {routing_key}: {str(e)}")
            return False

    def consume(self, queue_name: str, callback: Callable,
                auto_ack: bool = False) -> None:
        """
        Consume messages from a queue.

        Args:
            queue_name: Name of the queue
            callback: Callback function for messages
            auto_ack: Whether to auto-acknowledge messages
        """
        self.ensure_connected()

        # Ensure queue exists
        self.declare_queue(queue_name)

        # Bind queue to exchange with routing key
        self.channel.queue_bind(
            exchange=self.exchange,
            queue=queue_name,
            routing_key=queue_name
        )

        def wrapped_callback(ch, method, properties, body):
            try:
                # Deserialize JSON
                try:
                    message = json.loads(body)
                except json.JSONDecodeError:
                    message = body.decode('utf-8')

                # Call user callback
                result = callback(message, properties, method)

                # Acknowledge message if auto_ack is False and callback didn't raise exception
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                return result
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                # Reject message and requeue if it's not auto-acknowledged
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # Set QoS
        self.channel.basic_qos(prefetch_count=int(os.environ.get('RABBITMQ_PREFETCH_COUNT', '10')))

        # Start consuming
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapped_callback,
            auto_ack=auto_ack
        )

        logger.info(f"Started consuming from queue: {queue_name}")

        # Start consuming in a blocking way
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer due to keyboard interrupt")
            self.channel.stop_consuming()

    def close(self) -> None:
        """Close the connection to RabbitMQ."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")


def get_rabbitmq_client() -> RabbitMQClient:
    """
    Get or create a thread-local RabbitMQ client.

    Returns:
        RabbitMQClient instance
    """
    if not hasattr(_thread_locals, 'rabbitmq_client'):
        _thread_locals.rabbitmq_client = RabbitMQClient(
            host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
            port=int(os.environ.get('RABBITMQ_PORT', '5672')),
            username=os.environ.get('RABBITMQ_USERNAME', 'guest'),
            password=os.environ.get('RABBITMQ_PASSWORD', 'guest'),
            virtual_host=os.environ.get('RABBITMQ_VHOST', '/'),
        )

    return _thread_locals.rabbitmq_client


# Helper functions for common queue operations

def publish_message(routing_key: str, message: Any, **kwargs) -> bool:
    """
    Publish a message to RabbitMQ.

    Args:
        routing_key: Routing key
        message: Message to publish
        **kwargs: Additional message properties

    Returns:
        True if successful, False otherwise
    """
    return get_rabbitmq_client().publish(routing_key, message, **kwargs)


def task_queue(queue_name: str):
    """
    Decorate function to queue function calls as tasks.

    Args:
        queue_name: Name of the queue

    Returns:
        Decorated function that queues task for async execution
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create task message
            task = {
                'function': f"{func.__module__}.{func.__name__}",
                'args': args,
                'kwargs': kwargs,
                'created_at': time.time(),
            }

            # Publish to queue
            return publish_message(queue_name, task)

        # Add reference to original function
        wrapper.original_func = func
        return wrapper

    return decorator
