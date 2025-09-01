from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from database.database import get_db
from database.models import UserDB, SessionTokenDB
from database.crud import UserCRUD, SessionTokenCRUD
from auth import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenRefresh,
    PasswordReset,
    PasswordResetConfirm,
    UserPreferences,
    UserStats,
    TokenManager,
    UserAuthenticator,
    get_current_user,
    get_current_active_user,
    require_admin,
    require_user_management,
    auth_rate_limiter,
    Permission,
    PermissionChecker
)
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize managers
token_manager = TokenManager()
user_authenticator = UserAuthenticator()
user_crud = UserCRUD()
session_crud = SessionTokenCRUD()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(auth_rate_limiter)
):
    """
    Register a new user
    """
    try:
        # Check if username already exists
        existing_user = user_crud.get_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = user_crud.get_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = user_authenticator.create_user(db, user_data)
        
        logger.info(f"New user registered: {user.username} ({user.email})")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: bool = Depends(auth_rate_limiter)
):
    """
    User login
    """
    try:
        # Authenticate user
        user = user_authenticator.authenticate_user(
            db, user_credentials.username, user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create tokens
        access_token = token_manager.create_access_token(user)
        refresh_token = token_manager.create_refresh_token(user) if user_credentials.remember_me else None
        
        # Update last login
        user_crud.update_last_login(db, user.id)
        
        # Create session token record
        if refresh_token:
            session_data = {
                "user_id": user.id,
                "token": refresh_token,
                "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
            session_crud.create(db, session_data)
        
        # Set secure cookie for refresh token
        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="lax"
            )
        
        logger.info(f"User logged in: {user.username}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token
    """
    try:
        # Verify refresh token
        token_payload = token_manager.verify_refresh_token(token_data.refresh_token)
        if not token_payload or not token_payload.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = user_crud.get(db, token_payload.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Check if refresh token exists in database
        session_token = session_crud.get_by_token(db, token_data.refresh_token)
        if not session_token or session_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or invalid"
            )
        
        # Create new access token
        new_access_token = token_manager.create_access_token(user)
        
        logger.info(f"Token refreshed for user: {user.username}")
        
        return Token(
            access_token=new_access_token,
            refresh_token=token_data.refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    User logout
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Remove session token from database
            session_token = session_crud.get_by_token(db, refresh_token)
            if session_token:
                session_crud.delete(db, session_token.id)
        
        # Clear refresh token cookie
        response.delete_cookie("refresh_token")
        
        logger.info(f"User logged out: {current_user.username}")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information
    """
    try:
        # Check if username is being changed and if it's available
        if user_update.username and user_update.username != current_user.username:
            existing_user = user_crud.get_by_username(db, user_update.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check if email is being changed and if it's available
        if user_update.email and user_update.email != current_user.email:
            existing_email = user_crud.get_by_email(db, user_update.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Update user
        updated_user = user_crud.update(db, current_user.id, user_update.dict(exclude_unset=True))
        
        logger.info(f"User updated: {updated_user.username}")
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.put("/me/password")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user password
    """
    try:
        # Verify current password
        if not user_authenticator.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        hashed_password = user_authenticator.hash_password(password_data.new_password)
        user_crud.update(db, current_user.id, {"hashed_password": hashed_password})
        
        # Invalidate all existing sessions
        session_crud.delete_by_user_id(db, current_user.id)
        
        logger.info(f"Password changed for user: {current_user.username}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.put("/me/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences
    """
    try:
        # Update preferences
        updated_user = user_crud.update(db, current_user.id, {
            "preferences": preferences.dict(exclude_unset=True)
        })
        
        logger.info(f"Preferences updated for user: {updated_user.username}")
        
        return UserResponse.from_orm(updated_user)
        
    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preferences update failed"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDB = Depends(require_user_management()),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only)
    """
    try:
        users = user_crud.get_multi(db, skip=skip, limit=limit)
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserDB = Depends(require_user_management()),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    try:
        user = user_crud.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserDB = Depends(require_user_management()),
    db: Session = Depends(get_db)
):
    """
    Update user by ID (admin only)
    """
    try:
        user = user_crud.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if username is being changed and if it's available
        if user_update.username and user_update.username != user.username:
            existing_user = user_crud.get_by_username(db, user_update.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check if email is being changed and if it's available
        if user_update.email and user_update.email != user.email:
            existing_email = user_crud.get_by_email(db, user_update.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Update user
        updated_user = user_crud.update(db, user_id, user_update.dict(exclude_unset=True))
        
        logger.info(f"User {user_id} updated by admin {current_user.username}")
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserDB = Depends(require_user_management()),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID (admin only)
    """
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user = user_crud.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user
        user_crud.delete(db, user_id)
        
        # Delete all user sessions
        session_crud.delete_by_user_id(db, user_id)
        
        logger.info(f"User {user_id} deleted by admin {current_user.username}")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: UserDB = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Get user statistics (admin only)
    """
    try:
        stats = user_crud.get_user_stats(db)
        return stats
        
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.post("/verify-token")
async def verify_token(
    current_user: UserDB = Depends(get_current_user)
):
    """
    Verify if token is valid
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "role": PermissionChecker.get_user_role(current_user).value,
        "permissions": [perm.value for perm in PermissionChecker.get_user_permissions(current_user)]
    }