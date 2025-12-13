"""Comprehensive audit logging system.

Tracks all system activities for security and compliance.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import logging
from typing import Any, Dict, Optional, List
from functools import wraps
from django.conf import settings
from app.core.db.connection import get_db_session
from app.core.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking system activities.

    Features:
    - Automatic activity tracking
    - Model change detection
    - Request/response logging
    - User activity monitoring
    - Configurable audit levels
    """

    def __init__(self):
        """Initialize audit logger."""
        self.enabled = getattr(settings, 'AUDIT_ENABLED', True)
        self.log_models = getattr(settings, 'AUDIT_LOG_MODELS', True)
        self.log_requests = getattr(settings, 'AUDIT_LOG_REQUESTS', True)
        self.log_authentication = getattr(settings, 'AUDIT_LOG_AUTHENTICATION', True)

    def log_activity(self,
                     action: str,
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None,
                     resource_type: Optional[str] = None,
                     resource_id: Optional[str] = None,
                     resource_repr: Optional[str] = None,
                     old_values: Optional[Dict] = None,
                     new_values: Optional[Dict] = None,
                     request_method: Optional[str] = None,
                     request_path: Optional[str] = None,
                     request_data: Optional[Dict] = None,
                     response_status: Optional[int] = None,
                     metadata: Optional[Dict] = None,
                     message: Optional[str] = None) -> Optional[str]:
        """
        Log an activity to the audit trail.

        Args:
            action: Action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
            user_id: UUID of user performing the action
            session_id: Session ID
            ip_address: Client IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of affected resource
            resource_repr: String representation of resource
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            request_method: HTTP method
            request_path: Request URL path
            request_data: Request data (sanitized)
            response_status: HTTP response status
            metadata: Additional metadata
            message: Human-readable message

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Sanitize sensitive data
            sanitized_request_data = self._sanitize_data(request_data) if request_data else None
            sanitized_old_values = self._sanitize_data(old_values) if old_values else None
            sanitized_new_values = self._sanitize_data(new_values) if new_values else None

            with get_db_session() as session:
                audit_log = AuditLog(
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_repr=resource_repr,
                    old_values=sanitized_old_values,
                    new_values=sanitized_new_values,
                    request_method=request_method,
                    request_path=request_path,
                    request_data=sanitized_request_data,
                    response_status=response_status,
                    metadata=metadata,
                    message=message
                )

                session.add(audit_log)
                session.commit()

                logger.debug(f"Logged audit activity: {action} by user {user_id}")
                return str(audit_log.id)

        except Exception as e:
            logger.error(f"Failed to log audit activity: {str(e)}")
            return None

    def log_model_change(self,
                         action: str,
                         model_instance: Any,
                         user_id: Optional[str] = None,
                         old_values: Optional[Dict] = None,
                         session_info: Optional[Dict] = None) -> Optional[str]:
        """
        Log model changes (create, update, delete).

        Args:
            action: Action performed (CREATE, UPDATE, DELETE)
            model_instance: Model instance
            user_id: UUID of user performing the action
            old_values: Previous values (for updates)
            session_info: Session information

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_models:
            return None

        try:
            resource_type = model_instance.__class__.__name__
            resource_id = str(getattr(model_instance, 'id', None))
            resource_repr = str(model_instance)

            new_values = None
            if hasattr(model_instance, 'to_dict'):
                new_values = model_instance.to_dict()

            return self.log_activity(
                action=action,
                user_id=user_id,
                session_id=session_info.get('session_id') if session_info else None,
                ip_address=session_info.get('ip_address') if session_info else None,
                user_agent=session_info.get('user_agent') if session_info else None,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_repr=resource_repr,
                old_values=old_values,
                new_values=new_values
            )

        except Exception as e:
            logger.error(f"Failed to log model change: {str(e)}")
            return None

    def log_authentication(self,
                           action: str,
                           user_id: Optional[str] = None,
                           username: Optional[str] = None,
                           success: bool = True,
                           session_info: Optional[Dict] = None,
                           metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Log authentication events.

        Args:
            action: Authentication action (LOGIN, LOGOUT, LOGIN_FAILED, etc.)
            user_id: UUID of user
            username: Username attempted
            success: Whether authentication was successful
            session_info: Session information
            metadata: Additional metadata

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_authentication:
            return None

        auth_metadata = metadata or {}
        auth_metadata.update({
            'success': success,
            'username': username
        })

        message = f"Authentication {action.lower()}"
        if username:
            message += f" for user {username}"
        if not success:
            message += " (failed)"

        return self.log_activity(
            action=action,
            user_id=user_id,
            session_id=session_info.get('session_id') if session_info else None,
            ip_address=session_info.get('ip_address') if session_info else None,
            user_agent=session_info.get('user_agent') if session_info else None,
            resource_type='Authentication',
            metadata=auth_metadata,
            message=message
        )

    def log_request(self,
                    request_method: str,
                    request_path: str,
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None,
                    request_data: Optional[Dict] = None,
                    response_status: Optional[int] = None,
                    metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Log HTTP requests.

        Args:
            request_method: HTTP method
            request_path: Request URL path
            user_id: UUID of authenticated user
            session_id: Session ID
            ip_address: Client IP address
            user_agent: User agent string
            request_data: Request data
            response_status: HTTP response status
            metadata: Additional metadata

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_requests:
            return None

        return self.log_activity(
            action='HTTP_REQUEST',
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            request_data=request_data,
            response_status=response_status,
            metadata=metadata
        )

    def get_user_activity(self,
                          user_id: str,
                          limit: int = 100,
                          offset: int = 0,
                          action_filter: Optional[str] = None) -> List[Dict]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User UUID
            limit: Maximum number of records
            offset: Number of records to skip
            action_filter: Filter by action type

        Returns:
            List of audit log dictionaries
        """
        try:
            with get_db_session() as session:
                query = session.query(AuditLog).filter(AuditLog.user_id == user_id)

                if action_filter:
                    query = query.filter(AuditLog.action == action_filter)

                query = query.order_by(AuditLog.created_at.desc())
                query = query.offset(offset).limit(limit)

                logs = query.all()
                return [log.to_dict() for log in logs]

        except Exception as e:
            logger.error(f"Failed to get user activity: {str(e)}")
            return []

    def get_resource_history(self,
                             resource_type: str,
                             resource_id: str,
                             limit: int = 100) -> List[Dict]:
        """
        Get audit history for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Maximum number of records

        Returns:
            List of audit log dictionaries
        """
        try:
            with get_db_session() as session:
                query = session.query(AuditLog).filter(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                )

                query = query.order_by(AuditLog.created_at.desc())
                query = query.limit(limit)

                logs = query.all()
                return [log.to_dict() for log in logs]

        except Exception as e:
            logger.error(f"Failed to get resource history: {str(e)}")
            return []

    def _sanitize_data(self, data: Dict) -> Dict:
        """
        Sanitize sensitive data from logs.

        Args:
            data: Data dictionary

        Returns:
            Sanitized data dictionary
        """
        if not isinstance(data, dict):
            return data

        sensitive_fields = {
            'password', 'password_hash', 'token', 'secret', 'key',
            'authorization', 'cookie', 'session', 'csrf_token'
        }

        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized


# Global audit logger instance
audit_logger = AuditLogger()


# Decorator functions for automatic auditing
def audit_activity(action: str, resource_type: Optional[str] = None):
    """
    Decorate function to automatically audit function calls.

    Args:
        action: Action being performed
        resource_type: Type of resource being affected

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user and session info from kwargs if available
            user_id = kwargs.get('user_id')
            session_info = kwargs.get('session_info', {})

            try:
                result = func(*args, **kwargs)

                # Log successful activity
                audit_logger.log_activity(
                    action=action,
                    user_id=user_id,
                    session_id=session_info.get('session_id'),
                    ip_address=session_info.get('ip_address'),
                    user_agent=session_info.get('user_agent'),
                    resource_type=resource_type,
                    metadata={
                        'function': f"{func.__module__}.{func.__name__}",
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )

                return result

            except Exception as e:
                # Log failed activity
                audit_logger.log_activity(
                    action=f"{action}_FAILED",
                    user_id=user_id,
                    session_id=session_info.get('session_id'),
                    ip_address=session_info.get('ip_address'),
                    user_agent=session_info.get('user_agent'),
                    resource_type=resource_type,
                    metadata={
                        'function': f"{func.__module__}.{func.__name__}",
                        'error': str(e),
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    },
                    message=f"Failed to {action.lower()}: {str(e)}"
                )
                raise

        return wrapper
    return decorator


def audit_model_changes(model_class):
    """
    Class decorator to automatically audit model changes.

    Args:
        model_class: Model class to audit

    Returns:
        Decorated model class
    """
    original_init = model_class.__init__

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._audit_original_values = None
        if hasattr(self, 'to_dict'):
            self._audit_original_values = self.to_dict()

    model_class.__init__ = __init__
    return model_class


# Helper functions
def get_audit_logger() -> AuditLogger:
    """
    Get the global audit logger instance.

    Returns:
        AuditLogger instance
    """
    return audit_logger


def log_user_activity(action: str, user_id: str, **kwargs) -> Optional[str]:
    """
    Log user activity.

    Args:
        action: Action performed
        user_id: User UUID
        **kwargs: Additional audit parameters

    Returns:
        Audit log UUID if successful, None otherwise
    """
    return audit_logger.log_activity(action=action, user_id=user_id, **kwargs)
