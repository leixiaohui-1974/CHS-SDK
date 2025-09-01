from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging

from .models import (
    SimulationSessionDB,
    ComponentConfigDB,
    SimulationResultDB,
    SimulationEventDB,
    UserDB,
    SessionTokenDB,
    SimulationSnapshotDB
)
from models.simulation_models import SimulationStatus, ComponentType

logger = logging.getLogger(__name__)

# Simulation Session CRUD
class SimulationSessionCRUD:
    @staticmethod
    def create(db: Session, session_data: Dict[str, Any]) -> SimulationSessionDB:
        """Create a new simulation session"""
        db_session = SimulationSessionDB(**session_data)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        logger.info(f"Created simulation session: {db_session.id}")
        return db_session
    
    @staticmethod
    def get(db: Session, session_id: str) -> Optional[SimulationSessionDB]:
        """Get simulation session by ID"""
        return db.query(SimulationSessionDB).filter(SimulationSessionDB.id == session_id).first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[SimulationSessionDB]:
        """Get simulation sessions by user ID"""
        return db.query(SimulationSessionDB).filter(
            SimulationSessionDB.user_id == user_id
        ).order_by(desc(SimulationSessionDB.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[SimulationSessionDB]:
        """Get all simulation sessions"""
        return db.query(SimulationSessionDB).order_by(
            desc(SimulationSessionDB.created_at)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_status(db: Session, status: SimulationStatus, skip: int = 0, limit: int = 100) -> List[SimulationSessionDB]:
        """Get simulation sessions by status"""
        return db.query(SimulationSessionDB).filter(
            SimulationSessionDB.status == status
        ).order_by(desc(SimulationSessionDB.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, session_id: str, update_data: Dict[str, Any]) -> Optional[SimulationSessionDB]:
        """Update simulation session"""
        db_session = db.query(SimulationSessionDB).filter(SimulationSessionDB.id == session_id).first()
        if db_session:
            for key, value in update_data.items():
                setattr(db_session, key, value)
            db.commit()
            db.refresh(db_session)
            logger.info(f"Updated simulation session: {session_id}")
        return db_session
    
    @staticmethod
    def delete(db: Session, session_id: str) -> bool:
        """Delete simulation session"""
        db_session = db.query(SimulationSessionDB).filter(SimulationSessionDB.id == session_id).first()
        if db_session:
            db.delete(db_session)
            db.commit()
            logger.info(f"Deleted simulation session: {session_id}")
            return True
        return False
    
    @staticmethod
    def count_by_user(db: Session, user_id: str) -> int:
        """Count simulation sessions by user"""
        return db.query(SimulationSessionDB).filter(SimulationSessionDB.user_id == user_id).count()
    
    @staticmethod
    def get_active_sessions(db: Session) -> List[SimulationSessionDB]:
        """Get all active simulation sessions"""
        active_statuses = [SimulationStatus.RUNNING, SimulationStatus.PAUSED]
        return db.query(SimulationSessionDB).filter(
            SimulationSessionDB.status.in_(active_statuses)
        ).all()

# Component Configuration CRUD
class ComponentConfigCRUD:
    @staticmethod
    def create(db: Session, config_data: Dict[str, Any]) -> ComponentConfigDB:
        """Create a new component configuration"""
        db_config = ComponentConfigDB(**config_data)
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config
    
    @staticmethod
    def get_by_session(db: Session, session_id: str) -> List[ComponentConfigDB]:
        """Get all component configurations for a session"""
        return db.query(ComponentConfigDB).filter(
            ComponentConfigDB.session_id == session_id
        ).all()
    
    @staticmethod
    def get_by_component_id(db: Session, session_id: str, component_id: str) -> Optional[ComponentConfigDB]:
        """Get component configuration by component ID within a session"""
        return db.query(ComponentConfigDB).filter(
            and_(
                ComponentConfigDB.session_id == session_id,
                ComponentConfigDB.component_id == component_id
            )
        ).first()
    
    @staticmethod
    def update(db: Session, config_id: str, update_data: Dict[str, Any]) -> Optional[ComponentConfigDB]:
        """Update component configuration"""
        db_config = db.query(ComponentConfigDB).filter(ComponentConfigDB.id == config_id).first()
        if db_config:
            for key, value in update_data.items():
                setattr(db_config, key, value)
            db.commit()
            db.refresh(db_config)
        return db_config
    
    @staticmethod
    def delete(db: Session, config_id: str) -> bool:
        """Delete component configuration"""
        db_config = db.query(ComponentConfigDB).filter(ComponentConfigDB.id == config_id).first()
        if db_config:
            db.delete(db_config)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_by_session(db: Session, session_id: str) -> int:
        """Delete all component configurations for a session"""
        count = db.query(ComponentConfigDB).filter(
            ComponentConfigDB.session_id == session_id
        ).count()
        db.query(ComponentConfigDB).filter(
            ComponentConfigDB.session_id == session_id
        ).delete()
        db.commit()
        return count

# Simulation Result CRUD
class SimulationResultCRUD:
    @staticmethod
    def create(db: Session, result_data: Dict[str, Any]) -> SimulationResultDB:
        """Create a new simulation result"""
        db_result = SimulationResultDB(**result_data)
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    
    @staticmethod
    def create_batch(db: Session, results_data: List[Dict[str, Any]]) -> List[SimulationResultDB]:
        """Create multiple simulation results in batch"""
        db_results = [SimulationResultDB(**data) for data in results_data]
        db.add_all(db_results)
        db.commit()
        for result in db_results:
            db.refresh(result)
        return db_results
    
    @staticmethod
    def get_by_session(db: Session, session_id: str, skip: int = 0, limit: int = 1000) -> List[SimulationResultDB]:
        """Get simulation results by session"""
        return db.query(SimulationResultDB).filter(
            SimulationResultDB.session_id == session_id
        ).order_by(asc(SimulationResultDB.step_number)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_component(db: Session, session_id: str, component_id: str, skip: int = 0, limit: int = 1000) -> List[SimulationResultDB]:
        """Get simulation results by component"""
        return db.query(SimulationResultDB).filter(
            and_(
                SimulationResultDB.session_id == session_id,
                SimulationResultDB.component_id == component_id
            )
        ).order_by(asc(SimulationResultDB.step_number)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_time_range(db: Session, session_id: str, start_time: float, end_time: float) -> List[SimulationResultDB]:
        """Get simulation results by time range"""
        return db.query(SimulationResultDB).filter(
            and_(
                SimulationResultDB.session_id == session_id,
                SimulationResultDB.simulation_time >= start_time,
                SimulationResultDB.simulation_time <= end_time
            )
        ).order_by(asc(SimulationResultDB.simulation_time)).all()
    
    @staticmethod
    def get_latest_by_session(db: Session, session_id: str, limit: int = 100) -> List[SimulationResultDB]:
        """Get latest simulation results by session"""
        return db.query(SimulationResultDB).filter(
            SimulationResultDB.session_id == session_id
        ).order_by(desc(SimulationResultDB.step_number)).limit(limit).all()
    
    @staticmethod
    def delete_by_session(db: Session, session_id: str) -> int:
        """Delete all simulation results for a session"""
        count = db.query(SimulationResultDB).filter(
            SimulationResultDB.session_id == session_id
        ).count()
        db.query(SimulationResultDB).filter(
            SimulationResultDB.session_id == session_id
        ).delete()
        db.commit()
        return count
    
    @staticmethod
    def count_by_session(db: Session, session_id: str) -> int:
        """Count simulation results by session"""
        return db.query(SimulationResultDB).filter(
            SimulationResultDB.session_id == session_id
        ).count()

# Simulation Event CRUD
class SimulationEventCRUD:
    @staticmethod
    def create(db: Session, event_data: Dict[str, Any]) -> SimulationEventDB:
        """Create a new simulation event"""
        db_event = SimulationEventDB(**event_data)
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    
    @staticmethod
    def get_by_session(db: Session, session_id: str, skip: int = 0, limit: int = 100) -> List[SimulationEventDB]:
        """Get simulation events by session"""
        return db.query(SimulationEventDB).filter(
            SimulationEventDB.session_id == session_id
        ).order_by(desc(SimulationEventDB.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_level(db: Session, session_id: str, level: str, skip: int = 0, limit: int = 100) -> List[SimulationEventDB]:
        """Get simulation events by level"""
        return db.query(SimulationEventDB).filter(
            and_(
                SimulationEventDB.session_id == session_id,
                SimulationEventDB.level == level
            )
        ).order_by(desc(SimulationEventDB.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_errors(db: Session, session_id: str, skip: int = 0, limit: int = 100) -> List[SimulationEventDB]:
        """Get error events for a session"""
        return db.query(SimulationEventDB).filter(
            and_(
                SimulationEventDB.session_id == session_id,
                SimulationEventDB.level == "error"
            )
        ).order_by(desc(SimulationEventDB.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_by_session(db: Session, session_id: str) -> int:
        """Delete all simulation events for a session"""
        count = db.query(SimulationEventDB).filter(
            SimulationEventDB.session_id == session_id
        ).count()
        db.query(SimulationEventDB).filter(
            SimulationEventDB.session_id == session_id
        ).delete()
        db.commit()
        return count

# User CRUD
class UserCRUD:
    @staticmethod
    def create(db: Session, user_data: Dict[str, Any]) -> UserDB:
        """Create a new user"""
        db_user = UserDB(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created user: {db_user.username}")
        return db_user
    
    @staticmethod
    def get(db: Session, user_id: str) -> Optional[UserDB]:
        """Get user by ID"""
        return db.query(UserDB).filter(UserDB.id == user_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserDB]:
        """Get user by username"""
        return db.query(UserDB).filter(UserDB.username == username).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserDB]:
        """Get user by email"""
        return db.query(UserDB).filter(UserDB.email == email).first()
    
    @staticmethod
    def update(db: Session, user_id: str, update_data: Dict[str, Any]) -> Optional[UserDB]:
        """Update user"""
        db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if db_user:
            for key, value in update_data.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            logger.info(f"Updated user: {user_id}")
        return db_user
    
    @staticmethod
    def update_last_login(db: Session, user_id: str) -> Optional[UserDB]:
        """Update user's last login time"""
        return UserCRUD.update(db, user_id, {"last_login": datetime.utcnow()})
    
    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Delete user"""
        db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
        return False

# Session Token CRUD
class SessionTokenCRUD:
    @staticmethod
    def create(db: Session, token_data: Dict[str, Any]) -> SessionTokenDB:
        """Create a new session token"""
        db_token = SessionTokenDB(**token_data)
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token
    
    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[SessionTokenDB]:
        """Get session token by token value"""
        return db.query(SessionTokenDB).filter(
            and_(
                SessionTokenDB.token == token,
                SessionTokenDB.is_revoked == False,
                SessionTokenDB.expires_at > datetime.utcnow()
            )
        ).first()
    
    @staticmethod
    def revoke_token(db: Session, token: str) -> bool:
        """Revoke a session token"""
        db_token = db.query(SessionTokenDB).filter(SessionTokenDB.token == token).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def revoke_user_tokens(db: Session, user_id: str, token_type: Optional[str] = None) -> int:
        """Revoke all tokens for a user"""
        query = db.query(SessionTokenDB).filter(SessionTokenDB.user_id == user_id)
        if token_type:
            query = query.filter(SessionTokenDB.token_type == token_type)
        
        count = query.count()
        query.update({"is_revoked": True})
        db.commit()
        return count
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Clean up expired tokens"""
        count = db.query(SessionTokenDB).filter(
            SessionTokenDB.expires_at < datetime.utcnow()
        ).count()
        
        db.query(SessionTokenDB).filter(
            SessionTokenDB.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        
        logger.info(f"Cleaned up {count} expired tokens")
        return count

# Simulation Snapshot CRUD
class SimulationSnapshotCRUD:
    @staticmethod
    def create(db: Session, snapshot_data: Dict[str, Any]) -> SimulationSnapshotDB:
        """Create a new simulation snapshot"""
        db_snapshot = SimulationSnapshotDB(**snapshot_data)
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        return db_snapshot
    
    @staticmethod
    def get_by_session(db: Session, session_id: str) -> List[SimulationSnapshotDB]:
        """Get all snapshots for a session"""
        return db.query(SimulationSnapshotDB).filter(
            SimulationSnapshotDB.session_id == session_id
        ).order_by(desc(SimulationSnapshotDB.created_at)).all()
    
    @staticmethod
    def delete(db: Session, snapshot_id: str) -> bool:
        """Delete a simulation snapshot"""
        db_snapshot = db.query(SimulationSnapshotDB).filter(
            SimulationSnapshotDB.id == snapshot_id
        ).first()
        if db_snapshot:
            db.delete(db_snapshot)
            db.commit()
            return True
        return False

# Export all CRUD classes
__all__ = [
    "SimulationSessionCRUD",
    "ComponentConfigCRUD",
    "SimulationResultCRUD",
    "SimulationEventCRUD",
    "UserCRUD",
    "SessionTokenCRUD",
    "SimulationSnapshotCRUD"
]