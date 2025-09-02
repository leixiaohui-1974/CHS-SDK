# -*- coding: utf-8 -*-
"""
Knowledge API Interface for CHS-SDK Knowledge Base
知识库API接口模块

Provides unified API interface for knowledge base access,
designed for LLM integration and IDE plugin consumption.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .knowledge_base import KnowledgeBase
from .semantic_search import SemanticSearchEngine
from .recommendation_engine import RecommendationEngine
from .knowledge_indexer import KnowledgeIndexer


# API数据模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("semantic", description="搜索类型: semantic, keyword, hybrid")
    max_results: int = Field(10, description="最大结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="搜索过滤器")
    context: Optional[Dict[str, Any]] = Field(None, description="搜索上下文")


class SearchResult(BaseModel):
    """搜索结果模型"""
    content: str = Field(..., description="文档内容")
    title: str = Field(..., description="文档标题")
    doc_type: str = Field(..., description="文档类型")
    file_path: str = Field(..., description="文件路径")
    score: float = Field(..., description="相关性分数")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    context: Dict[str, Any] = Field(..., description="当前上下文")
    recommendation_type: str = Field("agent", description="推荐类型: agent, config, template")
    max_results: int = Field(5, description="最大推荐数量")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好")


class RecommendationResult(BaseModel):
    """推荐结果模型"""
    item_id: str = Field(..., description="项目ID")
    item_type: str = Field(..., description="项目类型")
    title: str = Field(..., description="项目标题")
    description: str = Field(..., description="项目描述")
    confidence: float = Field(..., description="推荐置信度")
    reason: str = Field(..., description="推荐理由")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class IndexStatus(BaseModel):
    """索引状态模型"""
    is_ready: bool = Field(..., description="索引是否就绪")
    last_updated: Optional[str] = Field(None, description="最后更新时间")
    total_documents: int = Field(0, description="文档总数")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计信息")


class KnowledgeAPIInterface:
    """
    知识库API接口
    
    为大模型和IDE插件提供统一的知识库访问接口，
    支持语义搜索、智能推荐和知识库管理功能。
    """
    
    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        初始化知识库API接口
        
        Args:
            project_root: 项目根目录
            config: 配置参数
        """
        self.project_root = Path(project_root)
        self.config = config
        self.logger = logging.getLogger("CHS-SDK.KnowledgeAPI")
        
        # API配置
        self.host = config.get("api_host", "localhost")
        self.port = config.get("api_port", 8080)
        self.enable_cors = config.get("enable_cors", True)
        self.cors_origins = config.get("cors_origins", ["*"])
        
        # 初始化核心组件
        self.knowledge_base = None
        self.search_engine = None
        self.recommendation_engine = None
        self.indexer = None
        
        # FastAPI应用
        self.app = FastAPI(
            title="CHS-SDK Knowledge Base API",
            description="Knowledge base API for CHS-SDK intelligent agents and IDE integration",
            version="1.0.0"
        )
        
        # 配置CORS
        if self.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # 注册路由
        self._register_routes()
        
        # 服务器实例
        self.server = None
        self.is_running = False
    
    async def initialize(self) -> bool:
        """
        初始化知识库组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("Initializing knowledge base components...")
            
            # 初始化知识库
            self.knowledge_base = KnowledgeBase(self.project_root, self.config)
            await self.knowledge_base.initialize()
            
            # 获取组件引用
            self.search_engine = self.knowledge_base.search_engine
            self.recommendation_engine = self.knowledge_base.recommendation_engine
            self.indexer = self.knowledge_base.indexer
            
            self.logger.info("Knowledge base API interface initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge base API: {str(e)}")
            return False
    
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @self.app.get("/status", response_model=IndexStatus)
        async def get_index_status():
            """获取索引状态"""
            if not self.knowledge_base:
                raise HTTPException(status_code=503, detail="Knowledge base not initialized")
            
            try:
                stats = self.indexer.get_statistics() if self.indexer else {}
                
                return IndexStatus(
                    is_ready=self.knowledge_base.is_ready,
                    last_updated=stats.get('last_indexed'),
                    total_documents=stats.get('total_documents', 0),
                    statistics=stats
                )
            except Exception as e:
                self.logger.error(f"Failed to get index status: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to get index status")
        
        @self.app.post("/search", response_model=List[SearchResult])
        async def search_knowledge(request: SearchRequest):
            """搜索知识库"""
            if not self.knowledge_base or not self.knowledge_base.is_ready:
                raise HTTPException(status_code=503, detail="Knowledge base not ready")
            
            try:
                # 执行搜索
                if request.search_type == "semantic":
                    results = await self.search_engine.semantic_search(
                        query=request.query,
                        top_k=request.max_results,
                        filters=request.filters
                    )
                elif request.search_type == "keyword":
                    results = await self.search_engine.keyword_search(
                        query=request.query,
                        top_k=request.max_results,
                        filters=request.filters
                    )
                elif request.search_type == "hybrid":
                    results = await self.search_engine.hybrid_search(
                        query=request.query,
                        top_k=request.max_results,
                        filters=request.filters
                    )
                else:
                    raise HTTPException(status_code=400, detail="Invalid search type")
                
                # 转换为API响应格式
                search_results = []
                for result in results:
                    search_results.append(SearchResult(
                        content=result['content'],
                        title=result['title'],
                        doc_type=result['doc_type'],
                        file_path=result['file_path'],
                        score=result['score'],
                        tags=result.get('tags', []),
                        metadata=result.get('metadata', {})
                    ))
                
                return search_results
                
            except Exception as e:
                self.logger.error(f"Search failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Search failed")
        
        @self.app.post("/recommend", response_model=List[RecommendationResult])
        async def get_recommendations(request: RecommendationRequest):
            """获取智能推荐"""
            if not self.knowledge_base or not self.knowledge_base.is_ready:
                raise HTTPException(status_code=503, detail="Knowledge base not ready")
            
            try:
                # 执行推荐
                if request.recommendation_type == "agent":
                    recommendations = await self.recommendation_engine.recommend_agents(
                        context=request.context,
                        max_recommendations=request.max_results
                    )
                elif request.recommendation_type == "config":
                    recommendations = await self.recommendation_engine.recommend_configurations(
                        context=request.context,
                        max_recommendations=request.max_results
                    )
                elif request.recommendation_type == "template":
                    recommendations = await self.recommendation_engine.recommend_templates(
                        context=request.context,
                        max_recommendations=request.max_results
                    )
                else:
                    raise HTTPException(status_code=400, detail="Invalid recommendation type")
                
                # 转换为API响应格式
                recommendation_results = []
                for rec in recommendations:
                    recommendation_results.append(RecommendationResult(
                        item_id=rec['item_id'],
                        item_type=rec['item_type'],
                        title=rec['title'],
                        description=rec['description'],
                        confidence=rec['confidence'],
                        reason=rec['reason'],
                        metadata=rec.get('metadata', {})
                    ))
                
                return recommendation_results
                
            except Exception as e:
                self.logger.error(f"Recommendation failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Recommendation failed")
        
        @self.app.post("/index/rebuild")
        async def rebuild_index(force: bool = Query(False, description="是否强制重建")):
            """重建知识库索引"""
            if not self.knowledge_base:
                raise HTTPException(status_code=503, detail="Knowledge base not initialized")
            
            try:
                success = await self.indexer.build_index(force_rebuild=force)
                if success:
                    return {"status": "success", "message": "Index rebuild completed"}
                else:
                    raise HTTPException(status_code=500, detail="Index rebuild failed")
            except Exception as e:
                self.logger.error(f"Index rebuild failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Index rebuild failed")
        
        @self.app.post("/index/update")
        async def update_index():
            """增量更新知识库索引"""
            if not self.knowledge_base:
                raise HTTPException(status_code=503, detail="Knowledge base not initialized")
            
            try:
                success = await self.indexer.update_index(incremental=True)
                if success:
                    return {"status": "success", "message": "Index update completed"}
                else:
                    raise HTTPException(status_code=500, detail="Index update failed")
            except Exception as e:
                self.logger.error(f"Index update failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Index update failed")
        
        @self.app.get("/agents")
        async def list_agents():
            """列出所有智能体"""
            if not self.knowledge_base or not self.knowledge_base.is_ready:
                raise HTTPException(status_code=503, detail="Knowledge base not ready")
            
            try:
                # 搜索所有智能体定义
                results = await self.search_engine.semantic_search(
                    query="agent definition",
                    top_k=100,
                    filters={'doc_type': 'agent_definition'}
                )
                
                agents = []
                for result in results:
                    metadata = result.get('metadata', {})
                    agents.append({
                        'name': metadata.get('class_name', 'Unknown'),
                        'file_path': result['file_path'],
                        'description': result['content'][:200] + '...' if len(result['content']) > 200 else result['content'],
                        'base_classes': metadata.get('base_classes', []),
                        'init_params': metadata.get('init_params', [])
                    })
                
                return {'agents': agents, 'total': len(agents)}
                
            except Exception as e:
                self.logger.error(f"Failed to list agents: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to list agents")
        
        @self.app.get("/configurations")
        async def list_configurations():
            """列出所有配置"""
            if not self.knowledge_base or not self.knowledge_base.is_ready:
                raise HTTPException(status_code=503, detail="Knowledge base not ready")
            
            try:
                # 搜索所有配置文件
                results = await self.search_engine.semantic_search(
                    query="configuration",
                    top_k=100,
                    filters={'tags': 'configuration'}
                )
                
                configs = []
                for result in results:
                    metadata = result.get('metadata', {})
                    configs.append({
                        'name': metadata.get('config_name', 'Unknown'),
                        'file_path': result['file_path'],
                        'type': result['doc_type'],
                        'description': result['content'][:200] + '...' if len(result['content']) > 200 else result['content'],
                        'structure': metadata.get('config_structure', {})
                    })
                
                return {'configurations': configs, 'total': len(configs)}
                
            except Exception as e:
                self.logger.error(f"Failed to list configurations: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to list configurations")
        
        @self.app.get("/documentation")
        async def list_documentation():
            """列出所有文档"""
            if not self.knowledge_base or not self.knowledge_base.is_ready:
                raise HTTPException(status_code=503, detail="Knowledge base not ready")
            
            try:
                # 搜索所有文档
                results = await self.search_engine.semantic_search(
                    query="documentation",
                    top_k=100,
                    filters={'doc_type': 'documentation'}
                )
                
                docs = []
                for result in results:
                    metadata = result.get('metadata', {})
                    docs.append({
                        'title': result['title'],
                        'file_path': result['file_path'],
                        'type': metadata.get('file_type', 'unknown'),
                        'section_level': metadata.get('section_level', 0),
                        'content_preview': result['content'][:300] + '...' if len(result['content']) > 300 else result['content']
                    })
                
                return {'documentation': docs, 'total': len(docs)}
                
            except Exception as e:
                self.logger.error(f"Failed to list documentation: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to list documentation")
        
        @self.app.post("/usage/record")
        async def record_usage(usage_data: Dict[str, Any] = Body(...)):
            """记录使用情况"""
            if not self.recommendation_engine:
                raise HTTPException(status_code=503, detail="Recommendation engine not available")
            
            try:
                await self.recommendation_engine.record_usage(
                    item_id=usage_data.get('item_id'),
                    item_type=usage_data.get('item_type'),
                    context=usage_data.get('context', {}),
                    success=usage_data.get('success', True)
                )
                
                return {"status": "success", "message": "Usage recorded"}
                
            except Exception as e:
                self.logger.error(f"Failed to record usage: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to record usage")
    
    async def start_server(self) -> bool:
        """
        启动API服务器
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.is_running:
                self.logger.warning("API server is already running")
                return True
            
            self.logger.info(f"Starting knowledge base API server on {self.host}:{self.port}...")
            
            # 初始化知识库组件
            if not await self.initialize():
                return False
            
            # 配置服务器
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            
            self.server = uvicorn.Server(config)
            
            # 在后台启动服务器
            self.is_running = True
            await self.server.serve()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {str(e)}")
            self.is_running = False
            return False
    
    async def stop_server(self):
        """停止API服务器"""
        if self.server and self.is_running:
            self.logger.info("Stopping knowledge base API server...")
            self.server.should_exit = True
            self.is_running = False
            
            # 清理知识库组件
            if self.knowledge_base:
                await self.knowledge_base.cleanup()
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            'title': 'CHS-SDK Knowledge Base API',
            'version': '1.0.0',
            'host': self.host,
            'port': self.port,
            'is_running': self.is_running,
            'endpoints': {
                'health': '/health',
                'status': '/status',
                'search': '/search',
                'recommend': '/recommend',
                'rebuild_index': '/index/rebuild',
                'update_index': '/index/update',
                'list_agents': '/agents',
                'list_configurations': '/configurations',
                'list_documentation': '/documentation',
                'record_usage': '/usage/record'
            },
            'documentation': f'http://{self.host}:{self.port}/docs'
        }


# 便捷函数
async def create_knowledge_api(project_root: Path, config: Dict[str, Any]) -> KnowledgeAPIInterface:
    """
    创建知识库API接口实例
    
    Args:
        project_root: 项目根目录
        config: 配置参数
        
    Returns:
        KnowledgeAPIInterface: API接口实例
    """
    api = KnowledgeAPIInterface(project_root, config)
    return api


async def start_knowledge_api_server(project_root: Path, config: Dict[str, Any]) -> KnowledgeAPIInterface:
    """
    启动知识库API服务器
    
    Args:
        project_root: 项目根目录
        config: 配置参数
        
    Returns:
        KnowledgeAPIInterface: API接口实例
    """
    api = await create_knowledge_api(project_root, config)
    
    # 启动服务器（在后台运行）
    asyncio.create_task(api.start_server())
    
    return api


if __name__ == "__main__":
    # 示例用法
    import sys
    from pathlib import Path
    
    # 配置
    project_root = Path("e:/OneDrive/Documents/GitHub/CHS-SDK")
    config = {
        "api_host": "localhost",
        "api_port": 8080,
        "enable_cors": True,
        "cors_origins": ["*"],
        "vector_db_path": "knowledge_base/vectors",
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "supported_file_types": [".py", ".yml", ".yaml", ".md", ".txt"],
        "exclude_dirs": ["__pycache__", ".git", "node_modules", "venv"]
    }
    
    async def main():
        api = await create_knowledge_api(project_root, config)
        await api.start_server()
    
    # 运行服务器
    asyncio.run(main())