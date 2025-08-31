from typing import List, Optional, Dict, Any, Callable
from functools import wraps
from enum import Enum
import logging

from ..database.models import UserDB
from ..database.crud import SimulationSessionCRUD
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    """
    System permissions
    """
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # Simulation management
    SIMULATION_CREATE = "simulation:create"
    SIMULATION_READ = "simulation:read"
    SIMULATION_UPDATE = "simulation:update"
    SIMULATION_DELETE = "simulation:delete"
    SIMULATION_CONTROL = "simulation:control"
    SIMULATION_LIST = "simulation:list"
    
    # System administration
    ADMIN_SYSTEM = "admin:system"
    ADMIN_USERS = "admin:users"
    ADMIN_SIMULATIONS = "admin:simulations"
    ADMIN_LOGS = "admin:logs"
    
    # Data access
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    
    # WebSocket connections
    WEBSOCKET_CONNECT = "websocket:connect"
    WEBSOCKET_SUBSCRIBE = "websocket:subscribe"

class Role(str, Enum):
    """
    User roles with predefined permissions
    """
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"

# Role-based permissions mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.GUEST: [
        Permission.SIMULATION_READ,
        Permission.DATA_READ,
    ],
    Role.USER: [
        Permission.USER_READ,
        Permission.USER_UPDATE,  # Own profile only
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_READ,
        Permission.SIMULATION_UPDATE,  # Own simulations only
        Permission.SIMULATION_DELETE,  # Own simulations only
        Permission.SIMULATION_CONTROL,  # Own simulations only
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_EXPORT,
        Permission.WEBSOCKET_CONNECT,
        Permission.WEBSOCKET_SUBSCRIBE,
    ],
    Role.MODERATOR: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_LIST,
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_READ,
        Permission.SIMULATION_UPDATE,
        Permission.SIMULATION_DELETE,
        Permission.SIMULATION_CONTROL,
        Permission.SIMULATION_LIST,
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_DELETE,
        Permission.DATA_EXPORT,
        Permission.WEBSOCKET_CONNECT,
        Permission.WEBSOCKET_SUBSCRIBE,
    ],
    Role.ADMIN: [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_LIST,
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_READ,
        Permission.SIMULATION_UPDATE,
        Permission.SIMULATION_DELETE,
        Permission.SIMULATION_CONTROL,
        Permission.SIMULATION_LIST,
        Permission.ADMIN_USERS,
        Permission.ADMIN_SIMULATIONS,
        Permission.ADMIN_LOGS,
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_DELETE,
        Permission.DATA_EXPORT,
        Permission.WEBSOCKET_CONNECT,
        Permission.WEBSOCKET_SUBSCRIBE,
    ],
    Role.SUPERUSER: list(Permission),  # All permissions
}

class AuthorizationError(Exception):
    """Authorization related errors"""
    pass

class PermissionChecker:
    """
    Permission checking logic
    """
    
    @staticmethod
    def get_user_role(user: UserDB) -> Role:
        """
        Get user role based on user attributes
        """
        if user.is_superuser:
            return Role.SUPERUSER
        
        # Check user preferences for role
        if user.preferences and "role" in user.preferences:
            role_str = user.preferences["role"]
            try:
                return Role(role_str)
            except ValueError:
                logger.warning(f"Invalid role in user preferences: {role_str}")
        
        # Default role for active users
        return Role.USER if user.is_active else Role.GUEST
    
    @staticmethod
    def get_user_permissions(user: UserDB) -> List[Permission]:
        """
        Get all permissions for a user
        """
        role = PermissionChecker.get_user_role(user)
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        # Add custom permissions from user preferences
        if user.preferences and "custom_permissions" in user.preferences:
            custom_perms = user.preferences["custom_permissions"]
            if isinstance(custom_perms, list):
                for perm_str in custom_perms:
                    try:
                        perm = Permission(perm_str)
                        if perm not in permissions:
                            permissions.append(perm)
                    except ValueError:
                        logger.warning(f"Invalid custom permission: {perm_str}")
        
        return permissions
    
    @staticmethod
    def has_permission(user: UserDB, permission: Permission) -> bool:
        """
        Check if user has a specific permission
        """
        if not user.is_active:
            return False
        
        user_permissions = PermissionChecker.get_user_permissions(user)
        return permission in user_permissions
    
    @staticmethod
    def has_any_permission(user: UserDB, permissions: List[Permission]) -> bool:
        """
        Check if user has any of the specified permissions
        """
        return any(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user: UserDB, permissions: List[Permission]) -> bool:
        """
        Check if user has all of the specified permissions
        """
        return all(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def can_access_simulation(user: UserDB, simulation_id: str, db: Session, required_permission: Permission) -> bool:
        """
        Check if user can access a specific simulation
        """
        # Check basic permission
        if not PermissionChecker.has_permission(user, required_permission):
            return False
        
        # Superusers and admins can access all simulations
        role = PermissionChecker.get_user_role(user)
        if role in [Role.SUPERUSER, Role.ADMIN]:
            return True
        
        # Check if user owns the simulation
        simulation = SimulationSessionCRUD.get(db, simulation_id)
        if simulation and simulation.user_id == user.id:
            return True
        
        # Moderators can access all simulations
        if role == Role.MODERATOR:
            return True
        
        return False
    
    @staticmethod
    def can_modify_user(current_user: UserDB, target_user_id: str) -> bool:
        """
        Check if current user can modify target user
        """
        # Users can modify their own profile
        if current_user.id == target_user_id:
            return PermissionChecker.has_permission(current_user, Permission.USER_UPDATE)
        
        # Admins and superusers can modify other users
        role = PermissionChecker.get_user_role(current_user)
        if role in [Role.SUPERUSER, Role.ADMIN]:
            return True
        
        return False

def check_permissions(user: UserDB, required_permissions: List[Permission], require_all: bool = True) -> bool:
    """
    Check if user has required permissions
    """
    if require_all:
        return PermissionChecker.has_all_permissions(user, required_permissions)
    else:
        return PermissionChecker.has_any_permission(user, required_permissions)

def require_permissions(permissions: List[Permission], require_all: bool = True):
    """
    Decorator to require specific permissions for a function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find user in function arguments
            user = None
            
            # Check if 'current_user' is in kwargs
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            # Check if first argument is a User object
            elif args and isinstance(args[0], UserDB):
                user = args[0]
            
            if not user:
                raise AuthorizationError("No user found for permission check")
            
            if not check_permissions(user, permissions, require_all):
                perm_names = [perm.value for perm in permissions]
                raise AuthorizationError(f"Insufficient permissions. Required: {perm_names}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_role(required_role: Role):
    """
    Decorator to require a specific role
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find user in function arguments
            user = None
            
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            elif args and isinstance(args[0], UserDB):
                user = args[0]
            
            if not user:
                raise AuthorizationError("No user found for role check")
            
            user_role = PermissionChecker.get_user_role(user)
            
            # Define role hierarchy
            role_hierarchy = {
                Role.GUEST: 0,
                Role.USER: 1,
                Role.MODERATOR: 2,
                Role.ADMIN: 3,
                Role.SUPERUSER: 4
            }
            
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                raise AuthorizationError(f"Insufficient role. Required: {required_role.value}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_ownership_or_admin(resource_user_id_key: str = "user_id"):
    """
    Decorator to require resource ownership or admin privileges
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise AuthorizationError("No user found for ownership check")
            
            # Check if user is admin or superuser
            role = PermissionChecker.get_user_role(user)
            if role in [Role.ADMIN, Role.SUPERUSER]:
                return func(*args, **kwargs)
            
            # Check ownership
            resource_user_id = kwargs.get(resource_user_id_key)
            if not resource_user_id:
                raise AuthorizationError(f"Resource user ID not found in {resource_user_id_key}")
            
            if user.id != resource_user_id:
                raise AuthorizationError("Access denied: insufficient privileges")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Convenience functions for common permission checks
def is_admin(user: UserDB) -> bool:
    """Check if user is admin or superuser"""
    role = PermissionChecker.get_user_role(user)
    return role in [Role.ADMIN, Role.SUPERUSER]

def is_superuser(user: UserDB) -> bool:
    """Check if user is superuser"""
    return PermissionChecker.get_user_role(user) == Role.SUPERUSER

def can_create_simulation(user: UserDB) -> bool:
    """Check if user can create simulations"""
    return PermissionChecker.has_permission(user, Permission.SIMULATION_CREATE)

def can_access_admin_panel(user: UserDB) -> bool:
    """Check if user can access admin panel"""
    return PermissionChecker.has_any_permission(user, [
        Permission.ADMIN_SYSTEM,
        Permission.ADMIN_USERS,
        Permission.ADMIN_SIMULATIONS,
        Permission.ADMIN_LOGS
    ])