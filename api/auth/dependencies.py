from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from database.database import get_db
from database.models import UserDB
from database.crud import UserCRUD
from .authentication import TokenManager, AuthenticationError
from .authorization import Permission, PermissionChecker, AuthorizationError
from .models import TokenData, UserResponse

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)

class AuthDependencies:
    """
    Authentication and authorization dependencies for FastAPI
    """
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.user_crud = UserCRUD()
    
    async def get_current_user_optional(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[UserDB]:
        """
        Get current user from token (optional - returns None if no valid token)
        """
        if not credentials:
            return None
        
        try:
            token_data = self.token_manager.verify_access_token(credentials.credentials)
            if not token_data or not token_data.user_id:
                return None
            
            user = self.user_crud.get(db, token_data.user_id)
            if not user:
                return None
            
            # Log user activity
            logger.info(f"User {user.username} accessed {request.url.path}")
            
            return user
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user_optional: {e}")
            return None
    
    async def get_current_user(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> UserDB:
        """
        Get current user from token (required)
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            token_data = self.token_manager.verify_access_token(credentials.credentials)
            if not token_data or not token_data.user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = self.user_crud.get(db, token_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Log user activity
            logger.info(f"User {user.username} accessed {request.url.path}")
            
            return user
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_current_active_user(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> UserDB:
        """
        Get current active user
        """
        current_user = await self.get_current_user(request, credentials, db)
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
    
    def require_permissions(self, permissions: List[Permission], require_all: bool = True):
        """
        Dependency factory for requiring specific permissions
        """
        async def permission_dependency(
            request: Request,
            credentials: HTTPAuthorizationCredentials = Depends(security),
            db: Session = Depends(get_db)
        ) -> UserDB:
            current_user = await self.get_current_active_user(request, credentials, db)
            try:
                if require_all:
                    has_permission = PermissionChecker.has_all_permissions(current_user, permissions)
                else:
                    has_permission = PermissionChecker.has_any_permission(current_user, permissions)
                
                if not has_permission:
                    perm_names = [perm.value for perm in permissions]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {perm_names}"
                    )
                
                return current_user
                
            except AuthorizationError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
        
        return permission_dependency
    
    def require_role(self, required_role: str):
        """
        Dependency factory for requiring specific role
        """
        async def role_dependency(
            current_user: UserDB = Depends(auth_deps.get_current_active_user)
        ) -> UserDB:
            user_role = PermissionChecker.get_user_role(current_user)
            
            # Define role hierarchy
            role_hierarchy = {
                "guest": 0,
                "user": 1,
                "moderator": 2,
                "admin": 3,
                "superuser": 4
            }
            
            if role_hierarchy.get(user_role.value, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {required_role}"
                )
            
            return current_user
        
        return role_dependency
    
    def require_simulation_access(self, required_permission: Permission):
        """
        Dependency factory for requiring simulation access
        """
        async def simulation_access_dependency(
            simulation_id: str,
            current_user: UserDB = Depends(auth_deps.get_current_active_user),
            db: Session = Depends(get_db)
        ) -> UserDB:
            can_access = PermissionChecker.can_access_simulation(
                current_user, simulation_id, db, required_permission
            )
            
            if not can_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to simulation"
                )
            
            return current_user
        
        return simulation_access_dependency
    
    def require_user_access(self):
        """
        Dependency factory for requiring user access (self or admin)
        """
        async def user_access_dependency(
            user_id: str,
            current_user: UserDB = Depends(auth_deps.get_current_active_user)
        ) -> UserDB:
            can_modify = PermissionChecker.can_modify_user(current_user, user_id)
            
            if not can_modify:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to user data"
                )
            
            return current_user
        
        return user_access_dependency

# Global instance
auth_deps = AuthDependencies()

# Convenience dependency functions
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[UserDB]:
    """Get current user (optional)"""
    return await auth_deps.get_current_user_optional(request, credentials, db)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserDB:
    """Get current user (required)"""
    return await auth_deps.get_current_user(request, credentials, db)

async def get_current_active_user(
    current_user: UserDB = Depends(get_current_user)
) -> UserDB:
    """Get current active user"""
    return await auth_deps.get_current_active_user(current_user)

# Permission-based dependencies
def require_admin():
    """Require admin role"""
    return auth_deps.require_role("admin")

def require_moderator():
    """Require moderator role or higher"""
    return auth_deps.require_role("moderator")

def require_user_management():
    """Require user management permissions"""
    return auth_deps.require_permissions([
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE
    ], require_all=False)

def require_simulation_management():
    """Require simulation management permissions"""
    return auth_deps.require_permissions([
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_UPDATE,
        Permission.SIMULATION_DELETE,
        Permission.SIMULATION_CONTROL
    ], require_all=False)

def require_simulation_read():
    """Require simulation read permission"""
    return auth_deps.require_permissions([Permission.SIMULATION_READ])

def require_simulation_write():
    """Require simulation write permissions"""
    return auth_deps.require_permissions([
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_UPDATE
    ], require_all=False)

def require_data_access():
    """Require data access permissions"""
    return auth_deps.require_permissions([
        Permission.DATA_READ,
        Permission.DATA_WRITE
    ], require_all=False)

def require_websocket_access():
    """Require WebSocket access permissions"""
    return auth_deps.require_permissions([
        Permission.WEBSOCKET_CONNECT,
        Permission.WEBSOCKET_SUBSCRIBE
    ], require_all=False)

# Rate limiting and security dependencies
class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis
    
    async def __call__(self, request: Request) -> bool:
        client_ip = request.client.host
        current_time = int(request.state.current_time.timestamp()) if hasattr(request.state, 'current_time') else int(__import__('time').time())
        window_start = current_time - (current_time % self.window_seconds)
        
        key = f"{client_ip}:{window_start}"
        
        if key not in self.requests:
            self.requests[key] = 0
        
        self.requests[key] += 1
        
        if self.requests[key] > self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return True

# Rate limiting instances
api_rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)  # 1000 requests per hour
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=300)    # 10 auth requests per 5 minutes
websocket_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 WS connections per minute

# Global auth dependencies instance
auth_deps = AuthDependencies()