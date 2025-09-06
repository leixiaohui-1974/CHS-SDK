#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台数据库模型
提供独立的数据库模型定义，不依赖api模块
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class SimulationResult(Base):
    """仿真结果模型"""
    __tablename__ = "simulation_results"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True)
    simulation_id = Column(String(36), nullable=True)
    result_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "simulation_id": self.simulation_id,
            "result_data": json.loads(self.result_data) if self.result_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class BatchSimulation(Base):
    """批量仿真模型"""
    __tablename__ = "batch_simulations"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="normal")
    total_simulations = Column(Integer, default=0)
    completed_simulations = Column(Integer, default=0)
    failed_simulations = Column(Integer, default=0)
    parallel_count = Column(Integer, default=4)
    timeout_minutes = Column(Integer, default=60)
    auto_retry = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    simulation_requests = Column(Text, nullable=True)  # JSON字符串
    notification_webhook = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    tasks = relationship("BatchSimulationTask", back_populates="batch", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "status": self.status,
            "priority": self.priority,
            "total_simulations": self.total_simulations,
            "completed_simulations": self.completed_simulations,
            "failed_simulations": self.failed_simulations,
            "parallel_count": self.parallel_count,
            "timeout_minutes": self.timeout_minutes,
            "auto_retry": self.auto_retry,
            "max_retries": self.max_retries,
            "simulation_requests": json.loads(self.simulation_requests) if self.simulation_requests else None,
            "notification_webhook": self.notification_webhook,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class BatchSimulationTask(Base):
    """批量仿真任务模型"""
    __tablename__ = "batch_simulation_tasks"
    
    id = Column(String(36), primary_key=True)
    batch_id = Column(String(36), ForeignKey("batch_simulations.id"), nullable=False)
    task_index = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    simulation_request = Column(Text, nullable=True)  # JSON字符串
    result_id = Column(String(36), nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    batch = relationship("BatchSimulation", back_populates="tasks")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "task_index": self.task_index,
            "status": self.status,
            "simulation_request": json.loads(self.simulation_request) if self.simulation_request else None,
            "result_id": self.result_id,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SimulationTemplate(Base):
    """仿真模板模型"""
    __tablename__ = "simulation_templates"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0.0")
    author = Column(String(100), nullable=False)
    status = Column(String(50), default="draft")
    tags = Column(Text, nullable=True)  # JSON字符串
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    template_data = Column(Text, nullable=True)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "status": self.status,
            "tags": json.loads(self.tags) if self.tags else [],
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "template_data": json.loads(self.template_data) if self.template_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class BatchTemplate(Base):
    """批量仿真模板模型"""
    __tablename__ = "batch_templates"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parameter_template = Column(Text, nullable=True)  # JSON字符串
    default_settings = Column(Text, nullable=True)  # JSON字符串
    created_by = Column(String(36), nullable=False)
    is_public = Column(Boolean, default=False)
    tags = Column(Text, nullable=True)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameter_template": json.loads(self.parameter_template) if self.parameter_template else None,
            "default_settings": json.loads(self.default_settings) if self.default_settings else None,
            "created_by": self.created_by,
            "is_public": self.is_public,
            "tags": json.loads(self.tags) if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ResultComparison(Base):
    """结果对比模型"""
    __tablename__ = "result_comparisons"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True)
    comparison_type = Column(String(50), nullable=False)
    result_ids = Column(Text, nullable=True)  # JSON字符串
    metrics = Column(Text, nullable=True)  # JSON字符串
    summary = Column(Text, nullable=True)
    confidence_level = Column(Float, default=0.95)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "comparison_type": self.comparison_type,
            "result_ids": json.loads(self.result_ids) if self.result_ids else None,
            "metrics": json.loads(self.metrics) if self.metrics else None,
            "summary": self.summary,
            "confidence_level": self.confidence_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ExportRecord(Base):
    """导出记录模型"""
    __tablename__ = "export_records"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True)
    result_ids = Column(Text, nullable=True)  # JSON字符串
    format = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "result_ids": json.loads(self.result_ids) if self.result_ids else None,
            "format": self.format,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
