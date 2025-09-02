# -*- coding: utf-8 -*-
"""
CHS-SDK Knowledge Base Core Module
知识库核心管理模块

This module provides the main KnowledgeBase class that coordinates
all knowledge management operations including indexing, searching,
and recommendations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime

from .semantic_search import SemanticSearchEngine
from .recommendation_engine import RecommendationEngine
from .knowledge_indexer import KnowledgeIndexer
from .auto_learning import AutoLearningSystem


class KnowledgeBase:
    """
    CHS-SDK知识库核心管理类
    
    负责协调语义搜索、智能推荐、知识索引等功能，
    为大模型和IDE插件提供统一的知识库访问接口。
    """
    
    def __init__(self, 
                 project_root: str,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化知识库
        
        Args:
            project_root: CHS-SDK项目根目录
            config: 知识库配置参数
        """
        self.project_root = Path(project_root)
        self.config = config or self._load_default_config()
        
        # 初始化日志
        self.logger = self._setup_logger()
        
        # 知识库存储路径
        self.kb_path = self.project_root / "knowledge_base"
        self.kb_path.mkdir(exist_ok=True)
        
        # 初始化各个组件
        self.search_engine = SemanticSearchEngine(self.kb_path, self.config)
        self.indexer = KnowledgeIndexer(self.project_root, self.config, self.search_engine)
        self.recommendation_engine = RecommendationEngine(self.kb_path, self.config)
        
        # 自动学习系统
        self.auto_learner: Optional[AutoLearningSystem] = None
        self._auto_learning_enabled = self.config.get('auto_learning', {}).get('enabled', False)
        
        # 知识库状态
        self.is_initialized = False
        self.last_update = None
        
        self.logger.info(f"Knowledge base initialized for project: {project_root}")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "vector_db_type": "faiss",
            "index_batch_size": 100,
            "search_top_k": 10,
            "recommendation_threshold": 0.7,
            "auto_update_interval": 3600,  # 1小时
            "supported_file_types": [".py", ".yml", ".yaml", ".md", ".txt"],
            "exclude_dirs": ["__pycache__", ".git", "node_modules", "venv"],
            "agent_registry_path": "core_lib",
            "config_templates_path": "scenarios/templates",
            "documentation_path": "docs"
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("CHS-SDK.KnowledgeBase")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self, force_rebuild: bool = False) -> bool:
        """
        初始化知识库，构建索引
        
        Args:
            force_rebuild: 是否强制重建索引
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("Starting knowledge base initialization...")
            
            # 检查是否需要重建索引
            if force_rebuild or not self._is_index_valid():
                self.logger.info("Building knowledge index...")
                await self.indexer.build_index()
                
                self.logger.info("Initializing search engine...")
                await self.search_engine.initialize()
                
                self.logger.info("Initializing recommendation engine...")
                await self.recommendation_engine.initialize()
                
                # 初始化自动学习系统
                if self._auto_learning_enabled:
                    await self._initialize_auto_learning()
            
            self.is_initialized = True
            self.last_update = datetime.now()
            
            self.logger.info("Knowledge base initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge base: {str(e)}")
            return False
    
    def _is_index_valid(self) -> bool:
        """检查索引是否有效"""
        index_file = self.kb_path / "vector_index.faiss"
        metadata_file = self.kb_path / "index_metadata.json"
        
        if not (index_file.exists() and metadata_file.exists()):
            return False
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 检查索引版本和最后更新时间
            last_indexed = datetime.fromisoformat(metadata.get('last_indexed', '1970-01-01'))
            
            # 如果索引超过配置的更新间隔，则认为无效
            update_interval = self.config.get('auto_update_interval', 3600)
            if (datetime.now() - last_indexed).total_seconds() > update_interval:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def search(self, 
                    query: str, 
                    search_type: str = "semantic",
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 (semantic, keyword, hybrid)
            filters: 搜索过滤器
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.is_initialized:
            await self.initialize()
        
        top_k = top_k or self.config.get('search_top_k', 10)
        
        try:
            results = await self.search_engine.search(
                query=query,
                search_type=search_type,
                filters=filters,
                top_k=top_k
            )
            
            self.logger.debug(f"Search completed: {len(results)} results for query '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []
    
    async def get_recommendations(self, 
                                 context: Dict[str, Any],
                                 recommendation_type: str = "agent") -> List[Dict[str, Any]]:
        """
        获取智能推荐
        
        Args:
            context: 当前开发上下文
            recommendation_type: 推荐类型 (agent, config, template)
            
        Returns:
            List[Dict]: 推荐结果列表
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            recommendations = await self.recommendation_engine.get_recommendations(
                context=context,
                recommendation_type=recommendation_type
            )
            
            self.logger.debug(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation failed: {str(e)}")
            return []
    
    async def update_index(self, incremental: bool = True) -> bool:
        """
        更新知识库索引
        
        Args:
            incremental: 是否增量更新
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info(f"Starting {'incremental' if incremental else 'full'} index update...")
            
            success = await self.indexer.update_index(incremental=incremental)
            
            if success:
                # 重新初始化搜索引擎和推荐引擎
                await self.search_engine.reload_index()
                await self.recommendation_engine.reload_index()
                
                self.last_update = datetime.now()
                self.logger.info("Index update completed successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Index update failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            "is_initialized": self.is_initialized,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "project_root": str(self.project_root),
            "knowledge_base_path": str(self.kb_path)
        }
        
        if self.is_initialized:
            stats.update({
                "search_engine_stats": self.search_engine.get_statistics(),
                "recommendation_engine_stats": self.recommendation_engine.get_statistics(),
                "indexer_stats": self.indexer.get_statistics()
            })
        
        return stats
    
    async def _initialize_auto_learning(self):
        """初始化自动学习系统"""
        try:
            self.logger.info("Initializing auto learning system...")
            self.auto_learner = AutoLearningSystem(
                project_root=self.project_root,
                knowledge_base=self,
                config=self.config.get('auto_learning', {})
            )
            await self.auto_learner.start_monitoring()
            self.logger.info("Auto learning system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize auto learning system: {str(e)}")
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up knowledge base resources...")
        
        # 停止自动学习系统
        if self.auto_learner:
            await self.auto_learner.stop_monitoring()
            self.auto_learner = None
        
        if hasattr(self.search_engine, 'cleanup'):
            await self.search_engine.cleanup()
        
        if hasattr(self.recommendation_engine, 'cleanup'):
            await self.recommendation_engine.cleanup()
        
        if hasattr(self.indexer, 'cleanup'):
            await self.indexer.cleanup()
        
        self.logger.info("Knowledge base cleanup completed")