#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台数据库管理器
提供独立的数据库访问功能，不依赖api模块
"""

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .models import Base

# 配置日志
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            database_url: 数据库连接URL，如果为None则使用默认配置
        """
        if database_url is None:
            # 默认使用SQLite数据库
            db_path = os.path.join(os.getcwd(), "simulation.db")
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        
        # 创建数据库引擎
        if "sqlite" in database_url:
            self.engine = create_engine(
                database_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False
            )
        else:
            self.engine = create_engine(database_url, echo=False)
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"数据库管理器初始化完成，连接: {database_url}")
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {str(e)}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """直接获取数据库会话（需要手动关闭）"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        try:
            self.engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")

# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None

def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """
    初始化全局数据库管理器
    
    Args:
        database_url: 数据库连接URL
        
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
        _db_manager.create_tables()
    return _db_manager

def get_database_manager() -> DatabaseManager:
    """
    获取全局数据库管理器
    
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = init_database()
    return _db_manager

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话生成器
    兼容原有的get_db()函数接口
    
    Yields:
        Session: 数据库会话
    """
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session

def close_database():
    """关闭全局数据库连接"""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close()
        _db_manager = None
