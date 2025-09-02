# -*- coding: utf-8 -*-
"""
Semantic Search Engine for CHS-SDK Knowledge Base
语义搜索引擎模块

Provides semantic search capabilities using sentence transformers
and vector similarity search for intelligent code and documentation retrieval.
"""

import os
import json
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
from datetime import datetime

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SemanticSearchEngine:
    """
    语义搜索引擎
    
    使用预训练的句子变换器模型和FAISS向量数据库
    实现高效的语义搜索功能。
    """
    
    def __init__(self, kb_path: Path, config: Dict[str, Any]):
        """
        初始化语义搜索引擎
        
        Args:
            kb_path: 知识库存储路径
            config: 配置参数
        """
        self.kb_path = kb_path
        self.config = config
        self.logger = logging.getLogger("CHS-SDK.SemanticSearch")
        
        # 模型和索引
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        
        # 配置参数
        self.model_name = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        self.vector_dim = 384  # MiniLM-L6-v2的向量维度
        self.top_k = config.get("search_top_k", 10)
        
        # 文件路径
        self.index_file = self.kb_path / "vector_index.faiss"
        self.documents_file = self.kb_path / "documents.json"
        self.metadata_file = self.kb_path / "search_metadata.json"
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化搜索引擎
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查依赖
            if not self._check_dependencies():
                return False
            
            # 加载模型
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # 加载或创建索引
            if self.index_file.exists():
                self.logger.info("Loading existing vector index...")
                await self._load_index()
            else:
                self.logger.info("Creating new vector index...")
                await self._create_empty_index()
            
            self.is_initialized = True
            self.logger.info("Semantic search engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize semantic search engine: {str(e)}")
            return False
    
    def _check_dependencies(self) -> bool:
        """检查必要的依赖包"""
        if SentenceTransformer is None:
            self.logger.error("sentence-transformers not installed. Please install: pip install sentence-transformers")
            return False
        
        if faiss is None:
            self.logger.error("faiss not installed. Please install: pip install faiss-cpu")
            return False
        
        return True
    
    async def _load_index(self):
        """加载现有索引"""
        try:
            # 加载FAISS索引
            self.index = faiss.read_index(str(self.index_file))
            
            # 加载文档数据
            if self.documents_file.exists():
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
            
            self.logger.info(f"Loaded index with {len(self.documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to load index: {str(e)}")
            await self._create_empty_index()
    
    async def _create_empty_index(self):
        """创建空索引"""
        # 创建FAISS索引
        self.index = faiss.IndexFlatIP(self.vector_dim)  # 内积相似度
        self.documents = []
        self.metadata = []
        
        # 保存空索引
        await self._save_index()
    
    async def _save_index(self):
        """保存索引到文件"""
        try:
            # 保存FAISS索引
            faiss.write_index(self.index, str(self.index_file))
            
            # 保存文档数据
            data = {
                'documents': self.documents,
                'metadata': self.metadata,
                'last_updated': datetime.now().isoformat(),
                'total_documents': len(self.documents)
            }
            
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Index saved with {len(self.documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to save index: {str(e)}")
    
    async def add_document(self, document: Dict[str, Any]) -> bool:
        """
        添加单个文档到索引
        
        Args:
            document: 文档字典，包含 'content', 'metadata' 等字段
            
        Returns:
            bool: 添加是否成功
        """
        return await self.add_documents([document])
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        添加文档到索引
        
        Args:
            documents: 文档列表，每个文档包含 'content', 'metadata' 等字段
            
        Returns:
            bool: 添加是否成功
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 提取文档内容
            texts = [doc.get('content', '') for doc in documents]
            
            if not texts:
                return True
            
            # 生成嵌入向量
            self.logger.info(f"Generating embeddings for {len(texts)} documents...")
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # 标准化向量（用于内积相似度）
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # 添加到索引
            self.index.add(embeddings.astype(np.float32))
            
            # 保存文档和元数据
            for i, doc in enumerate(documents):
                # 保存完整的文档字典
                document_dict = {
                    'content': doc.get('content', ''),
                    'metadata': {
                        'id': len(self.metadata),
                        'file_path': doc.get('file_path', ''),
                        'doc_type': doc.get('doc_type', 'unknown'),
                        'title': doc.get('title', ''),
                        'tags': doc.get('tags', []),
                        'created_at': datetime.now().isoformat(),
                        **doc.get('metadata', {})
                    }
                }
                self.documents.append(document_dict)
                self.metadata.append(document_dict['metadata'])
            
            # 保存索引
            await self._save_index()
            
            self.logger.info(f"Successfully added {len(documents)} documents to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {str(e)}")
            return False
    
    async def search(self, 
                    query: str,
                    search_type: str = "semantic",
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 (semantic, keyword, hybrid)
            filters: 搜索过滤器
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果
        """
        if not self.is_initialized:
            await self.initialize()
        
        top_k = top_k or self.top_k
        
        try:
            if search_type == "semantic":
                return await self._semantic_search(query, filters, top_k)
            elif search_type == "keyword":
                return await self._keyword_search(query, filters, top_k)
            elif search_type == "hybrid":
                return await self._hybrid_search(query, filters, top_k)
            else:
                raise ValueError(f"Unsupported search type: {search_type}")
                
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []
    
    async def _semantic_search(self, 
                              query: str, 
                              filters: Optional[Dict[str, Any]], 
                              top_k: int) -> List[Dict[str, Any]]:
        """语义搜索"""
        if len(self.documents) == 0:
            return []
        
        # 生成查询向量
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # 搜索最相似的文档
        scores, indices = self.index.search(query_embedding.astype(np.float32), min(top_k, len(self.documents)))
        
        # 构建结果
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= len(self.documents):
                continue
                
            metadata = self.metadata[idx] if idx < len(self.metadata) else {}
            
            # 应用过滤器
            if filters and not self._apply_filters(metadata, filters):
                continue
            
            # 获取文档内容
            doc = self.documents[idx]
            content = doc.get('content', '') if isinstance(doc, dict) else str(doc)
            
            result = {
                'content': content,
                'score': float(score),
                'rank': i + 1,
                'search_type': 'semantic',
                'metadata': metadata
            }
            results.append(result)
        
        return results[:top_k]
    
    async def _keyword_search(self, 
                             query: str, 
                             filters: Optional[Dict[str, Any]], 
                             top_k: int) -> List[Dict[str, Any]]:
        """关键词搜索"""
        query_lower = query.lower()
        results = []
        
        for i, doc in enumerate(self.documents):
            # 获取文档内容
            content = doc.get('content', '') if isinstance(doc, dict) else str(doc)
            doc_lower = content.lower()
            
            # 计算关键词匹配分数
            score = 0.0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in doc_lower:
                    score += doc_lower.count(word) / len(doc_lower)
            
            if score > 0:
                metadata = self.metadata[i] if i < len(self.metadata) else {}
                
                # 应用过滤器
                if filters and not self._apply_filters(metadata, filters):
                    continue
                
                result = {
                    'content': content,
                    'score': score,
                    'search_type': 'keyword',
                    'metadata': metadata
                }
                results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 添加排名
        for i, result in enumerate(results[:top_k]):
            result['rank'] = i + 1
        
        return results[:top_k]
    
    async def _hybrid_search(self, 
                            query: str, 
                            filters: Optional[Dict[str, Any]], 
                            top_k: int) -> List[Dict[str, Any]]:
        """混合搜索（语义+关键词）"""
        # 获取语义搜索结果
        semantic_results = await self._semantic_search(query, filters, top_k * 2)
        
        # 获取关键词搜索结果
        keyword_results = await self._keyword_search(query, filters, top_k * 2)
        
        # 合并和重新排序
        combined_results = {}
        
        # 添加语义搜索结果（权重0.7）
        for result in semantic_results:
            doc_id = id(result['content'])
            combined_results[doc_id] = result.copy()
            combined_results[doc_id]['combined_score'] = result['score'] * 0.7
        
        # 添加关键词搜索结果（权重0.3）
        for result in keyword_results:
            doc_id = id(result['content'])
            if doc_id in combined_results:
                combined_results[doc_id]['combined_score'] += result['score'] * 0.3
            else:
                combined_results[doc_id] = result.copy()
                combined_results[doc_id]['combined_score'] = result['score'] * 0.3
        
        # 按组合分数排序
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # 更新排名和搜索类型
        for i, result in enumerate(final_results[:top_k]):
            result['rank'] = i + 1
            result['search_type'] = 'hybrid'
            result['score'] = result['combined_score']
            del result['combined_score']
        
        return final_results[:top_k]
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """应用搜索过滤器"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
        
        return True
    
    async def reload_index(self):
        """重新加载索引"""
        self.logger.info("Reloading search index...")
        await self._load_index()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取搜索引擎统计信息"""
        return {
            "is_initialized": self.is_initialized,
            "model_name": self.model_name,
            "vector_dimension": self.vector_dim,
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "index_file_exists": self.index_file.exists(),
            "documents_file_exists": self.documents_file.exists()
        }
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up semantic search engine...")
        
        if self.model:
            del self.model
            self.model = None
        
        if self.index:
            del self.index
            self.index = None
        
        self.documents.clear()
        self.metadata.clear()
        
        self.is_initialized = False