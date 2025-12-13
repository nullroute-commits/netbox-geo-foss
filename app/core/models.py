"""Core models for the application.

SQLAlchemy models for User, Role, Permission, and audit logging.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.db.connection import Base

# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class BaseModel(Base):
    """Base model with common fields for all entities."""

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class User(BaseModel):
    """User model for authentication and RBAC."""

    __tablename__ = 'users'

    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    date_joined = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    audit_logs_created = relationship('AuditLog', foreign_keys='AuditLog.user_id', back_populates='user')

    def __repr__(self):
        """Return string representation of User."""
        return f'<User(username={self.username}, email={self.email})>'

    @property
    def full_name(self):
        """Get user's full name."""
        return f'{self.first_name} {self.last_name}'.strip()

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission_name: Name of the permission to check

        Returns:
            True if user has permission, False otherwise
        """
        if self.is_superuser:
            return True

        for role in self.roles:
            if role.is_active and any(perm.name == permission_name and perm.is_active
                                      for perm in role.permissions):
                return True

        return False

    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role_name: Name of the role to check

        Returns:
            True if user has role, False otherwise
        """
        return any(role.name == role_name and role.is_active for role in self.roles)


class Role(BaseModel):
    """Role model for RBAC."""

    __tablename__ = 'roles'

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted

    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')

    def __repr__(self):
        """Return string representation of Role."""
        return f'<Role(name={self.name})>'


class Permission(BaseModel):
    """Permission model for RBAC."""

    __tablename__ = 'permissions'

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)  # e.g., 'user', 'role', 'permission'
    action = Column(String(50), nullable=False)     # e.g., 'create', 'read', 'update', 'delete'
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System permissions cannot be deleted

    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')

    def __repr__(self):
        """Return string representation of Permission."""
        return f'<Permission(name={self.name}, resource={self.resource}, action={self.action})>'


class AuditLog(BaseModel):
    """Audit log model for tracking all system activities."""

    __tablename__ = 'audit_logs'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    session_id = Column(String(40), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Action details
    action = Column(String(50), nullable=False)  # e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'
    resource_type = Column(String(100), nullable=True)  # Model name or resource type
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_repr = Column(String(255), nullable=True)  # String representation of the resource

    # Change tracking
    old_values = Column(JSONB, nullable=True)  # Previous values for updates
    new_values = Column(JSONB, nullable=True)  # New values for creates/updates

    # Request details
    request_method = Column(String(10), nullable=True)  # HTTP method
    request_path = Column(String(255), nullable=True)   # URL path
    request_data = Column(JSONB, nullable=True)         # Request data (sanitized)

    # Response details
    response_status = Column(Integer, nullable=True)    # HTTP status code

    # Additional metadata
    metadata = Column(JSONB, nullable=True)
    message = Column(Text, nullable=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='audit_logs_created')

    def __repr__(self):
        """Return string representation of AuditLog."""
        return f'<AuditLog(action={self.action}, resource_type={self.resource_type}, user_id={self.user_id})>'


class SystemConfiguration(BaseModel):
    """System configuration model for storing application settings."""

    __tablename__ = 'system_configurations'

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        """Return string representation of SystemConfiguration."""
        return f'<SystemConfiguration(key={self.key})>'
