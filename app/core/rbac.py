"""Role-Based Access Control (RBAC) system.

Provides comprehensive access control functionality for the application.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import logging
from typing import List, Optional, Set
from functools import wraps
from django.core.cache import cache
from app.core.db.connection import get_db_session
from app.core.models import User, Role, Permission
from app.core.cache.memcached import cache_get, cache_set

logger = logging.getLogger(__name__)


class RBACManager:
    """
    RBAC Manager for handling role and permission operations.

    Features:
    - User role assignment
    - Permission checking
    - Role hierarchy
    - Caching for performance
    - Audit logging integration
    """

    def __init__(self, cache_timeout: int = 300):
        """
        Initialize RBAC Manager.

        Args:
            cache_timeout: Cache timeout in seconds
        """
        self.cache_timeout = cache_timeout

    def get_user_permissions(self, user_id: str, use_cache: bool = True) -> Set[str]:
        """
        Get all permissions for a user.

        Args:
            user_id: User UUID
            use_cache: Whether to use cache

        Returns:
            Set of permission names
        """
        cache_key = f"user_permissions:{user_id}"

        if use_cache:
            cached_permissions = cache_get(cache_key)
            if cached_permissions is not None:
                return set(cached_permissions)

        permissions = set()

        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return permissions

            # Superuser has all permissions
            if user.is_superuser:
                all_permissions = session.query(Permission).filter(Permission.is_active.is_(True)).all()
                permissions = {perm.name for perm in all_permissions}
            else:
                # Get permissions from active roles
                for role in user.roles:
                    if role.is_active:
                        for permission in role.permissions:
                            if permission.is_active:
                                permissions.add(permission.name)

        # Cache the result
        if use_cache:
            cache_set(cache_key, list(permissions), self.cache_timeout)

        return permissions

    def get_user_roles(self, user_id: str, use_cache: bool = True) -> Set[str]:
        """
        Get all roles for a user.

        Args:
            user_id: User UUID
            use_cache: Whether to use cache

        Returns:
            Set of role names
        """
        cache_key = f"user_roles:{user_id}"

        if use_cache:
            cached_roles = cache_get(cache_key)
            if cached_roles is not None:
                return set(cached_roles)

        roles = set()

        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                roles = {role.name for role in user.roles if role.is_active}

        # Cache the result
        if use_cache:
            cache_set(cache_key, list(roles), self.cache_timeout)

        return roles

    def has_permission(self, user_id: str, permission_name: str, use_cache: bool = True) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User UUID
            permission_name: Permission name to check
            use_cache: Whether to use cache

        Returns:
            True if user has permission, False otherwise
        """
        permissions = self.get_user_permissions(user_id, use_cache)
        return permission_name in permissions

    def has_role(self, user_id: str, role_name: str, use_cache: bool = True) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User UUID
            role_name: Role name to check
            use_cache: Whether to use cache

        Returns:
            True if user has role, False otherwise
        """
        roles = self.get_user_roles(user_id, use_cache)
        return role_name in roles

    def assign_role(self, user_id: str, role_name: str, assigned_by: Optional[str] = None) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: User UUID
            role_name: Role name to assign
            assigned_by: UUID of user performing the assignment

        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                role = session.query(Role).filter(Role.name == role_name, Role.is_active.is_(True)).first()

                if not user or not role:
                    logger.warning(f"User {user_id} or role {role_name} not found")
                    return False

                # Check if user already has the role
                if role in user.roles:
                    logger.info(f"User {user_id} already has role {role_name}")
                    return True

                # Assign the role
                user.roles.append(role)
                if assigned_by:
                    user.updated_by = assigned_by

                session.commit()

                # Clear cache
                self._clear_user_cache(user_id)

                logger.info(f"Assigned role {role_name} to user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to assign role {role_name} to user {user_id}: {str(e)}")
            return False

    def revoke_role(self, user_id: str, role_name: str, revoked_by: Optional[str] = None) -> bool:
        """
        Revoke a role from a user.

        Args:
            user_id: User UUID
            role_name: Role name to revoke
            revoked_by: UUID of user performing the revocation

        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                role = session.query(Role).filter(Role.name == role_name).first()

                if not user or not role:
                    logger.warning(f"User {user_id} or role {role_name} not found")
                    return False

                # Check if user has the role
                if role not in user.roles:
                    logger.info(f"User {user_id} does not have role {role_name}")
                    return True

                # Revoke the role
                user.roles.remove(role)
                if revoked_by:
                    user.updated_by = revoked_by

                session.commit()

                # Clear cache
                self._clear_user_cache(user_id)

                logger.info(f"Revoked role {role_name} from user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to revoke role {role_name} from user {user_id}: {str(e)}")
            return False

    def create_role(self, name: str, description: str = None, permissions: List[str] = None,
                    created_by: Optional[str] = None) -> Optional[str]:
        """
        Create a new role.

        Args:
            name: Role name
            description: Role description
            permissions: List of permission names to assign
            created_by: UUID of user creating the role

        Returns:
            Role UUID if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                # Check if role already exists
                existing_role = session.query(Role).filter(Role.name == name).first()
                if existing_role:
                    logger.warning(f"Role {name} already exists")
                    return None

                # Create the role
                role = Role(
                    name=name,
                    description=description,
                    created_by=created_by
                )

                # Assign permissions if provided
                if permissions:
                    permission_objects = session.query(Permission).filter(
                        Permission.name.in_(permissions),
                        Permission.is_active.is_(True)
                    ).all()
                    role.permissions.extend(permission_objects)

                session.add(role)
                session.commit()

                logger.info(f"Created role {name}")
                return str(role.id)

        except Exception as e:
            logger.error(f"Failed to create role {name}: {str(e)}")
            return None

    def create_permission(self, name: str, resource: str, action: str,
                          description: str = None, created_by: Optional[str] = None) -> Optional[str]:
        """
        Create a new permission.

        Args:
            name: Permission name
            resource: Resource type
            action: Action type
            description: Permission description
            created_by: UUID of user creating the permission

        Returns:
            Permission UUID if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                # Check if permission already exists
                existing_permission = session.query(Permission).filter(Permission.name == name).first()
                if existing_permission:
                    logger.warning(f"Permission {name} already exists")
                    return None

                # Create the permission
                permission = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description,
                    created_by=created_by
                )

                session.add(permission)
                session.commit()

                logger.info(f"Created permission {name}")
                return str(permission.id)

        except Exception as e:
            logger.error(f"Failed to create permission {name}: {str(e)}")
            return None

    def _clear_user_cache(self, user_id: str):
        """Clear cached data for a user."""
        cache_keys = [
            f"user_permissions:{user_id}",
            f"user_roles:{user_id}"
        ]

        for key in cache_keys:
            cache.delete(key)


# Global RBAC manager instance
rbac_manager = RBACManager()


# Decorator functions for permission checking
def require_permission(permission_name: str):
    """
    Decorate function to require a specific permission.

    Args:
        permission_name: Required permission name

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from request context (this would be implemented based on your auth system)
            user_id = getattr(kwargs.get('request'), 'user_id', None)

            if not user_id:
                raise PermissionError("User not authenticated")

            if not rbac_manager.has_permission(user_id, permission_name):
                raise PermissionError(f"User does not have permission: {permission_name}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorate function to require a specific role.

    Args:
        role_name: Required role name

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from request context (this would be implemented based on your auth system)
            user_id = getattr(kwargs.get('request'), 'user_id', None)

            if not user_id:
                raise PermissionError("User not authenticated")

            if not rbac_manager.has_role(user_id, role_name):
                raise PermissionError(f"User does not have role: {role_name}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_names: str):
    """
    Decorate function to require any of the specified permissions.

    Args:
        permission_names: List of permission names (user needs at least one)

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from request context (this would be implemented based on your auth system)
            user_id = getattr(kwargs.get('request'), 'user_id', None)

            if not user_id:
                raise PermissionError("User not authenticated")

            user_permissions = rbac_manager.get_user_permissions(user_id)

            if not any(perm in user_permissions for perm in permission_names):
                raise PermissionError(
                    f"User does not have any of the required permissions: {
                        ', '.join(permission_names)}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Helper functions
def get_rbac_manager() -> RBACManager:
    """
    Get the global RBAC manager instance.

    Returns:
        RBACManager instance
    """
    return rbac_manager
