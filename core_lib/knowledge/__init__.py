# CHS-SDK Knowledge Base Enhancement System
# 知识库增强检索系统

from .knowledge_base import KnowledgeBase
from .semantic_search import SemanticSearchEngine
from .recommendation_engine import RecommendationEngine
from .knowledge_indexer import KnowledgeIndexer
from .knowledge_api import KnowledgeAPIInterface

__all__ = [
    'KnowledgeBase',
    'SemanticSearchEngine', 
    'RecommendationEngine',
    'KnowledgeIndexer',
    'KnowledgeAPIInterface'
]

__version__ = '1.0.0'
__author__ = 'CHS-SDK Team'
__description__ = 'Knowledge base enhancement system for CHS-SDK with semantic search and intelligent recommendations'