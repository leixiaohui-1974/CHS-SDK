from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User roles"""
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"

class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    role: UserRole = Field(UserRole.USER, description="User role")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.isalnum() and '_' not in v and '-' not in v:
                raise ValueError('Username must contain only alphanumeric characters, underscores, and hyphens')
            return v.lower()
        return v

class UserPasswordUpdate(BaseModel):
    """User password update model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    preferences: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """User login model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(False, description="Remember login")

class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    token_type: Optional[TokenType] = None
    expires_at: Optional[datetime] = None

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

class TokenRefresh(BaseModel):
    """Token refresh model"""
    refresh_token: str = Field(..., description="Refresh token")

class PasswordReset(BaseModel):
    """Password reset request model"""
    email: EmailStr = Field(..., description="Email address")

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserPreferences(BaseModel):
    """User preferences model"""
    theme: Optional[str] = Field("light", description="UI theme")
    language: Optional[str] = Field("en", description="Language preference")
    timezone: Optional[str] = Field("UTC", description="Timezone")
    notifications: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {
            "email": True,
            "push": True,
            "simulation_updates": True,
            "system_alerts": True
        },
        description="Notification preferences"
    )
    dashboard_layout: Optional[Dict[str, Any]] = Field(None, description="Dashboard layout configuration")
    simulation_defaults: Optional[Dict[str, Any]] = Field(None, description="Default simulation settings")
    custom_permissions: Optional[List[str]] = Field(None, description="Custom permissions")
    role: Optional[UserRole] = Field(None, description="User role override")

class UserSession(BaseModel):
    """User session model"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True

class LoginAttempt(BaseModel):
    """Login attempt model"""
    username: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    attempted_at: datetime
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserActivity(BaseModel):
    """User activity model"""
    user_id: str
    activity_type: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PermissionCheck(BaseModel):
    """Permission check request model"""
    user_id: str
    permissions: List[str]
    require_all: bool = True
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None

class PermissionResponse(BaseModel):
    """Permission check response model"""
    has_permission: bool
    missing_permissions: Optional[List[str]] = None
    user_role: UserRole
    user_permissions: List[str]

class RoleUpdate(BaseModel):
    """Role update model"""
    user_id: str
    new_role: UserRole
    reason: Optional[str] = None

class BulkUserOperation(BaseModel):
    """Bulk user operation model"""
    user_ids: List[str]
    operation: str  # activate, deactivate, delete, update_role
    parameters: Optional[Dict[str, Any]] = None

class UserStats(BaseModel):
    """User statistics model"""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: Dict[UserRole, int]
    recent_registrations: int
    recent_logins: int
    
class SecurityEvent(BaseModel):
    """Security event model"""
    event_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    description: str
    severity: str  # low, medium, high, critical
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True