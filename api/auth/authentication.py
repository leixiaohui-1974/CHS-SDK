from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import logging

from ..config import settings
from ..database.crud import UserCRUD, SessionTokenCRUD
from ..database.models import UserDB
from .password import verify_password
from .models import TokenData

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class TokenManager:
    """
    JWT Token management
    """
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
            logger.info(f"Created access token for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise AuthenticationError("Failed to create access token")
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
        
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
            logger.info(f"Created refresh token for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise AuthenticationError("Failed to create refresh token")
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                raise AuthenticationError("Invalid token: missing subject")
            
            token_data = TokenData(
                username=username,
                user_id=payload.get("user_id"),
                token_type=payload.get("type", "access"),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0))
            )
            
            # Check if token is expired
            if token_data.expires_at < datetime.utcnow():
                raise AuthenticationError("Token has expired")
            
            return token_data
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError("Token verification failed")
    
    @staticmethod
    def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        """
        try:
            token_data = TokenManager.verify_token(refresh_token)
            
            if token_data.token_type != "refresh":
                raise AuthenticationError("Invalid token type for refresh")
            
            # Get user from database
            user = UserCRUD.get_by_username(db, token_data.username)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Create new access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = TokenManager.create_access_token(
                data={"sub": user.username, "user_id": user.id},
                expires_delta=access_token_expires
            )
            
            # Create new refresh token
            refresh_token_expires = timedelta(days=7)
            new_refresh_token = TokenManager.create_refresh_token(
                data={"sub": user.username, "user_id": user.id},
                expires_delta=refresh_token_expires
            )
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise AuthenticationError("Token refresh failed")

class UserAuthenticator:
    """
    User authentication logic
    """
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
        """
        Authenticate user with username and password
        """
        try:
            # Get user by username or email
            user = UserCRUD.get_by_username(db, username)
            if not user:
                user = UserCRUD.get_by_email(db, username)
            
            if not user:
                logger.warning(f"Authentication failed: user not found - {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: user inactive - {username}")
                return None
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password - {username}")
                return None
            
            # Update last login
            UserCRUD.update_last_login(db, user.id)
            
            logger.info(f"User authenticated successfully: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return None
    
    @staticmethod
    def login_user(db: Session, username: str, password: str, client_ip: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Login user and create tokens
        """
        user = UserAuthenticator.authenticate_user(db, username, password)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = TokenManager.create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=7)
        refresh_token = TokenManager.create_refresh_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=refresh_token_expires
        )
        
        # Store refresh token in database
        try:
            SessionTokenCRUD.create(db, {
                "user_id": user.id,
                "token": refresh_token,
                "token_type": "refresh",
                "expires_at": datetime.utcnow() + refresh_token_expires,
                "client_ip": client_ip,
                "user_agent": user_agent
            })
        except Exception as e:
            logger.warning(f"Failed to store refresh token: {e}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_superuser": user.is_superuser
            }
        }
    
    @staticmethod
    def logout_user(db: Session, user_id: str, token: Optional[str] = None) -> bool:
        """
        Logout user and revoke tokens
        """
        try:
            if token:
                # Revoke specific token
                SessionTokenCRUD.revoke_token(db, token)
            else:
                # Revoke all user tokens
                SessionTokenCRUD.revoke_user_tokens(db, user_id)
            
            logger.info(f"User logged out: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Logout error for user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[UserDB]:
        """
        Get user from JWT token
        """
        try:
            token_data = TokenManager.verify_token(token)
            user = UserCRUD.get_by_username(db, token_data.username)
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except AuthenticationError:
            return None
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            return None

# Convenience functions
def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
    """Authenticate user with username and password"""
    return UserAuthenticator.authenticate_user(db, username, password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    return TokenManager.create_access_token(data, expires_delta)

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token"""
    return TokenManager.verify_token(token)

def login_user(db: Session, username: str, password: str, client_ip: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
    """Login user and create tokens"""
    return UserAuthenticator.login_user(db, username, password, client_ip, user_agent)

def logout_user(db: Session, user_id: str, token: Optional[str] = None) -> bool:
    """Logout user and revoke tokens"""
    return UserAuthenticator.logout_user(db, user_id, token)

def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, str]:
    """Refresh access token using refresh token"""
    return TokenManager.refresh_access_token(refresh_token, db)

def get_user_from_token(db: Session, token: str) -> Optional[UserDB]:
    """Get user from JWT token"""
    return UserAuthenticator.get_user_from_token(db, token)