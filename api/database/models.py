from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import enum
import uuid

from .database import Base
from ..models.simulation_models import SimulationStatus, ComponentType

class SimulationSessionDB(Base):
    """
    Database model for simulation sessions
    """
    __tablename__ = "simulation_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(SimulationStatus), default=SimulationStatus.CREATED, nullable=False)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Store simulation configuration as JSON
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Simulation parameters
    time_step = Column(Float, default=1.0, nullable=False)
    total_steps = Column(Integer, default=1000, nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    
    # User information
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    components = relationship("ComponentConfigDB", back_populates="session", cascade="all, delete-orphan")
    results = relationship("SimulationResultDB", back_populates="session", cascade="all, delete-orphan")
    events = relationship("SimulationEventDB", back_populates="session", cascade="all, delete-orphan")
    user = relationship("UserDB", back_populates="sessions")
    
    def __repr__(self):
        return f"<SimulationSession(id={self.id}, name={self.name}, status={self.status})>"

class ComponentConfigDB(Base):
    """
    Database model for component configurations
    """
    __tablename__ = "component_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("simulation_sessions.id"), nullable=False)
    
    # Component information
    component_id = Column(String, nullable=False)  # Unique within session
    component_type = Column(Enum(ComponentType), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Configuration data
    config = Column(JSON, nullable=False)  # Component-specific configuration
    position = Column(JSON, nullable=True)  # Position in UI (x, y coordinates)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("SimulationSessionDB", back_populates="components")
    
    def __repr__(self):
        return f"<ComponentConfig(id={self.id}, type={self.component_type}, name={self.name})>"

class SimulationResultDB(Base):
    """
    Database model for simulation results
    """
    __tablename__ = "simulation_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("simulation_sessions.id"), nullable=False)
    
    # Time information
    simulation_time = Column(Float, nullable=False)  # Simulation time
    step_number = Column(Integer, nullable=False)  # Step number
    
    # Component data
    component_id = Column(String, nullable=False)  # Component that generated this result
    component_type = Column(Enum(ComponentType), nullable=False)
    
    # Result data
    data = Column(JSON, nullable=False)  # Component state and output data
    metrics = Column(JSON, nullable=True)  # Performance metrics
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    session = relationship("SimulationSessionDB", back_populates="results")
    
    def __repr__(self):
        return f"<SimulationResult(id={self.id}, step={self.step_number}, component={self.component_id})>"

class SimulationEventDB(Base):
    """
    Database model for simulation events and logs
    """
    __tablename__ = "simulation_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("simulation_sessions.id"), nullable=False)
    
    # Event information
    event_type = Column(String(100), nullable=False)  # e.g., 'error', 'warning', 'info', 'control'
    level = Column(String(20), default="info", nullable=False)  # log level
    message = Column(Text, nullable=False)
    
    # Context
    component_id = Column(String, nullable=True)  # Related component
    simulation_time = Column(Float, nullable=True)  # When in simulation this occurred
    step_number = Column(Integer, nullable=True)  # Step number when this occurred
    
    # Additional data
    data = Column(JSON, nullable=True)  # Additional event data
    stack_trace = Column(Text, nullable=True)  # For errors
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    session = relationship("SimulationSessionDB", back_populates="events")
    
    def __repr__(self):
        return f"<SimulationEvent(id={self.id}, type={self.event_type}, level={self.level})>"

class UserDB(Base):
    """
    Database model for users
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Preferences
    preferences = Column(JSON, nullable=True)  # User preferences as JSON
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sessions = relationship("SimulationSessionDB", back_populates="user")
    tokens = relationship("SessionTokenDB", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

class SessionTokenDB(Base):
    """
    Database model for session tokens
    """
    __tablename__ = "session_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Token information
    token = Column(String(255), unique=True, nullable=False)
    token_type = Column(String(50), default="access", nullable=False)  # access, refresh
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Client information
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("UserDB", back_populates="tokens")
    
    def __repr__(self):
        return f"<SessionToken(id={self.id}, user_id={self.user_id}, type={self.token_type})>"

class SimulationSnapshotDB(Base):
    """
    Database model for simulation snapshots
    """
    __tablename__ = "simulation_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("simulation_sessions.id"), nullable=False)
    
    # Snapshot information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Snapshot data
    simulation_time = Column(Float, nullable=False)
    step_number = Column(Integer, nullable=False)
    state_data = Column(JSON, nullable=False)  # Complete simulation state
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    checksum = Column(String(64), nullable=True)  # SHA-256 checksum
    
    # Relationships
    session = relationship("SimulationSessionDB")
    
    def __repr__(self):
        return f"<SimulationSnapshot(id={self.id}, name={self.name}, step={self.step_number})>"

# Create indexes for better performance
from sqlalchemy import Index

# Indexes for simulation_sessions
Index('idx_simulation_sessions_status', SimulationSessionDB.status)
Index('idx_simulation_sessions_user_id', SimulationSessionDB.user_id)
Index('idx_simulation_sessions_created_at', SimulationSessionDB.created_at)

# Indexes for simulation_results
Index('idx_simulation_results_session_step', SimulationResultDB.session_id, SimulationResultDB.step_number)
Index('idx_simulation_results_component', SimulationResultDB.component_id)
Index('idx_simulation_results_time', SimulationResultDB.simulation_time)

# Indexes for simulation_events
Index('idx_simulation_events_session_time', SimulationEventDB.session_id, SimulationEventDB.created_at)
Index('idx_simulation_events_type_level', SimulationEventDB.event_type, SimulationEventDB.level)

# Indexes for users
Index('idx_users_username', UserDB.username)
Index('idx_users_email', UserDB.email)
Index('idx_users_active', UserDB.is_active)

# Indexes for session_tokens
Index('idx_session_tokens_token', SessionTokenDB.token)
Index('idx_session_tokens_user_expires', SessionTokenDB.user_id, SessionTokenDB.expires_at)
Index('idx_session_tokens_revoked', SessionTokenDB.is_revoked)