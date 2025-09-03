#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库集成模块

为LLM代理提供知识库访问和利用功能，包括历史案例、最佳实践、技术文档等。

主要功能：
- 知识库查询和检索
- 上下文增强
- 案例推荐
- 最佳实践建议
- 知识图谱构建
- 智能问答
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# 导入CHS-SDK知识库
try:
    from core_lib.knowledge_base.knowledge_base import KnowledgeBase
except ImportError:
    KnowledgeBase = None
    logging.warning("KnowledgeBase not available")

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """知识项"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source: str
    confidence: float = 1.0
    created_at: str = None
    updated_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CaseStudy:
    """案例研究"""
    id: str
    title: str
    description: str
    problem: str
    solution: str
    results: str
    lessons_learned: List[str]
    applicable_scenarios: List[str]
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    tags: List[str]
    difficulty_level: str = "medium"  # easy, medium, hard
    success_rate: float = 1.0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class BestPractice:
    """最佳实践"""
    id: str
    title: str
    description: str
    domain: str  # 领域：水库控制、洪水管理、系统优化等
    practice_type: str  # 类型：设计、运维、故障处理等
    steps: List[str]
    benefits: List[str]
    prerequisites: List[str]
    risks: List[str]
    success_criteria: List[str]
    related_cases: List[str]
    confidence_score: float = 1.0
    usage_count: int = 0
    last_used: str = None
    
    def __post_init__(self):
        if self.last_used is None:
            self.last_used = datetime.now().isoformat()

@dataclass
class QueryResult:
    """查询结果"""
    items: List[KnowledgeItem]
    relevance_scores: List[float]
    total_count: int
    query_time: float
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class KnowledgeIntegration:
    """
    知识库集成系统
    
    为LLM代理提供智能知识访问和利用功能
    """
    
    def __init__(self, knowledge_base_path: str = None, cache_dir: str = None):
        """
        初始化知识库集成系统
        
        Args:
            knowledge_base_path: 知识库路径
            cache_dir: 缓存目录
        """
        self.knowledge_base_path = Path(knowledge_base_path) if knowledge_base_path else self._get_default_kb_path()
        self.cache_dir = Path(cache_dir) if cache_dir else Path("cache/knowledge")
        
        # 确保目录存在
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化知识库
        self.kb = None
        if KnowledgeBase:
            try:
                self.kb = KnowledgeBase(str(self.knowledge_base_path))
                logger.info("KnowledgeBase initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize KnowledgeBase: {e}")
        
        # 内存知识存储
        self.knowledge_items: Dict[str, KnowledgeItem] = {}
        self.case_studies: Dict[str, CaseStudy] = {}
        self.best_practices: Dict[str, BestPractice] = {}
        
        # TF-IDF向量化器
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.document_ids = []
        
        # 加载现有知识
        self._load_knowledge_data()
        self._build_search_index()
        
        logger.info(f"Knowledge integration system initialized. Items: {len(self.knowledge_items)}, Cases: {len(self.case_studies)}, Practices: {len(self.best_practices)}")
    
    def _get_default_kb_path(self) -> Path:
        """获取默认知识库路径"""
        current_dir = Path(__file__).parent
        return current_dir.parent.parent / "knowledge_base"
    
    def _load_knowledge_data(self):
        """加载知识数据"""
        try:
            # 加载知识项
            knowledge_file = self.cache_dir / "knowledge_items.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = KnowledgeItem(**item_data)
                        self.knowledge_items[item.id] = item
            
            # 加载案例研究
            cases_file = self.cache_dir / "case_studies.json"
            if cases_file.exists():
                with open(cases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for case_data in data:
                        case = CaseStudy(**case_data)
                        self.case_studies[case.id] = case
            
            # 加载最佳实践
            practices_file = self.cache_dir / "best_practices.json"
            if practices_file.exists():
                with open(practices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for practice_data in data:
                        practice = BestPractice(**practice_data)
                        self.best_practices[practice.id] = practice
            
            # 如果没有数据，初始化一些示例
            if not self.knowledge_items and not self.case_studies and not self.best_practices:
                self._initialize_sample_knowledge()
                
        except Exception as e:
            logger.error(f"Failed to load knowledge data: {e}")
            self._initialize_sample_knowledge()
    
    def _initialize_sample_knowledge(self):
        """初始化示例知识"""
        # 示例知识项
        sample_items = [
            KnowledgeItem(
                id="water_level_control_basics",
                title="水位控制基础原理",
                content="水位控制是水库管理的核心技术，通过调节闸门开度来控制水位高度。基本原理包括PID控制、模糊控制等方法。",
                category="基础理论",
                tags=["水位控制", "PID", "模糊控制"],
                source="技术手册"
            ),
            KnowledgeItem(
                id="flood_management_strategies",
                title="洪水管理策略",
                content="洪水管理包括预防、监测、响应和恢复四个阶段。关键是建立有效的预警系统和应急响应机制。",
                category="应急管理",
                tags=["洪水管理", "预警系统", "应急响应"],
                source="应急手册"
            ),
            KnowledgeItem(
                id="system_optimization_methods",
                title="系统优化方法",
                content="水利系统优化可采用遗传算法、粒子群优化、模拟退火等智能优化算法，以提高系统性能和效率。",
                category="优化技术",
                tags=["系统优化", "遗传算法", "粒子群优化"],
                source="研究论文"
            )
        ]
        
        for item in sample_items:
            self.knowledge_items[item.id] = item
        
        # 示例案例研究
        sample_cases = [
            CaseStudy(
                id="reservoir_flood_control_case",
                title="某水库洪水控制案例",
                description="2023年汛期某大型水库成功应对特大洪水的案例分析",
                problem="面临50年一遇特大洪水，需要在保证大坝安全的前提下最大化下游防洪效益",
                solution="采用智能调度算法，结合实时气象预报，动态调整泄洪策略",
                results="成功削峰40%，下游未发生洪涝灾害，大坝安全运行",
                lessons_learned=["实时数据的重要性", "多目标优化的必要性", "应急预案的完善"],
                applicable_scenarios=["大型水库", "洪水调度", "多目标优化"],
                parameters={"水库容量": "10亿立方米", "最大泄洪量": "8000立方米/秒"},
                performance_metrics={"削峰率": 0.4, "安全系数": 1.2, "经济效益": 5000000},
                tags=["洪水控制", "智能调度", "多目标优化"],
                difficulty_level="hard",
                success_rate=0.95
            )
        ]
        
        for case in sample_cases:
            self.case_studies[case.id] = case
        
        # 示例最佳实践
        sample_practices = [
            BestPractice(
                id="pid_tuning_best_practice",
                title="PID控制器参数调优最佳实践",
                description="水位控制系统中PID控制器参数调优的标准流程和注意事项",
                domain="水位控制",
                practice_type="参数调优",
                steps=[
                    "分析系统特性和响应时间",
                    "设定初始PID参数",
                    "进行阶跃响应测试",
                    "根据响应曲线调整参数",
                    "验证控制性能和稳定性"
                ],
                benefits=["提高控制精度", "减少超调", "增强系统稳定性"],
                prerequisites=["了解系统动态特性", "具备PID理论基础"],
                risks=["参数设置不当可能导致系统不稳定"],
                success_criteria=["稳态误差<2%", "超调量<10%", "调节时间<30秒"],
                related_cases=["reservoir_flood_control_case"],
                confidence_score=0.9
            )
        ]
        
        for practice in sample_practices:
            self.best_practices[practice.id] = practice
        
        # 保存示例数据
        self._save_knowledge_data()
    
    def _build_search_index(self):
        """构建搜索索引"""
        try:
            documents = []
            doc_ids = []
            
            # 添加知识项
            for item in self.knowledge_items.values():
                text = f"{item.title} {item.content} {' '.join(item.tags)}"
                documents.append(text)
                doc_ids.append(f"item_{item.id}")
            
            # 添加案例研究
            for case in self.case_studies.values():
                text = f"{case.title} {case.description} {case.problem} {case.solution} {' '.join(case.tags)}"
                documents.append(text)
                doc_ids.append(f"case_{case.id}")
            
            # 添加最佳实践
            for practice in self.best_practices.values():
                text = f"{practice.title} {practice.description} {' '.join(practice.steps)}"
                documents.append(text)
                doc_ids.append(f"practice_{practice.id}")
            
            if documents:
                self.tfidf_matrix = self.vectorizer.fit_transform(documents)
                self.document_ids = doc_ids
                
                # 保存索引
                index_file = self.cache_dir / "search_index.pkl"
                with open(index_file, 'wb') as f:
                    pickle.dump({
                        'vectorizer': self.vectorizer,
                        'tfidf_matrix': self.tfidf_matrix,
                        'document_ids': self.document_ids
                    }, f)
                
                logger.info(f"Search index built with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build search index: {e}")
    
    def search_knowledge(self, query: str, limit: int = 10, min_score: float = 0.1) -> QueryResult:
        """
        搜索知识库
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            min_score: 最小相关性分数
        
        Returns:
            查询结果
        """
        start_time = datetime.now()
        
        try:
            # 使用CHS-SDK知识库搜索
            if self.kb:
                try:
                    kb_results = self.kb.search(query, limit=limit)
                    # 转换为KnowledgeItem格式
                    items = []
                    scores = []
                    for result in kb_results:
                        item = KnowledgeItem(
                            id=result.get('id', 'kb_' + str(len(items))),
                            title=result.get('title', 'Knowledge Base Result'),
                            content=result.get('content', ''),
                            category=result.get('category', 'Knowledge Base'),
                            tags=result.get('tags', []),
                            source='Knowledge Base',
                            confidence=result.get('score', 0.5)
                        )
                        items.append(item)
                        scores.append(result.get('score', 0.5))
                    
                    query_time = (datetime.now() - start_time).total_seconds()
                    return QueryResult(
                        items=items[:limit],
                        relevance_scores=scores[:limit],
                        total_count=len(items),
                        query_time=query_time
                    )
                except Exception as e:
                    logger.warning(f"Knowledge base search failed: {e}")
            
            # 使用内置搜索
            if self.tfidf_matrix is None:
                return QueryResult(items=[], relevance_scores=[], total_count=0, query_time=0)
            
            # TF-IDF搜索
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # 获取相关结果
            relevant_indices = np.where(similarities >= min_score)[0]
            sorted_indices = relevant_indices[np.argsort(similarities[relevant_indices])[::-1]]
            
            items = []
            scores = []
            
            for idx in sorted_indices[:limit]:
                doc_id = self.document_ids[idx]
                score = similarities[idx]
                
                if doc_id.startswith('item_'):
                    item_id = doc_id[5:]
                    if item_id in self.knowledge_items:
                        items.append(self.knowledge_items[item_id])
                        scores.append(score)
                elif doc_id.startswith('case_'):
                    case_id = doc_id[5:]
                    if case_id in self.case_studies:
                        case = self.case_studies[case_id]
                        item = KnowledgeItem(
                            id=case.id,
                            title=case.title,
                            content=case.description,
                            category="案例研究",
                            tags=case.tags,
                            source="案例库",
                            confidence=score
                        )
                        items.append(item)
                        scores.append(score)
                elif doc_id.startswith('practice_'):
                    practice_id = doc_id[9:]
                    if practice_id in self.best_practices:
                        practice = self.best_practices[practice_id]
                        item = KnowledgeItem(
                            id=practice.id,
                            title=practice.title,
                            content=practice.description,
                            category="最佳实践",
                            tags=[practice.domain, practice.practice_type],
                            source="实践库",
                            confidence=score
                        )
                        items.append(item)
                        scores.append(score)
            
            query_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                items=items,
                relevance_scores=scores,
                total_count=len(items),
                query_time=query_time,
                suggestions=self._generate_suggestions(query, items)
            )
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return QueryResult(items=[], relevance_scores=[], total_count=0, query_time=0)
    
    def get_relevant_cases(self, problem_description: str, limit: int = 5) -> List[CaseStudy]:
        """
        获取相关案例
        
        Args:
            problem_description: 问题描述
            limit: 返回案例数量限制
        
        Returns:
            相关案例列表
        """
        try:
            # 搜索相关案例
            results = self.search_knowledge(problem_description, limit=limit * 2)
            
            cases = []
            for item in results.items:
                if item.id in self.case_studies:
                    cases.append(self.case_studies[item.id])
                    if len(cases) >= limit:
                        break
            
            return cases
            
        except Exception as e:
            logger.error(f"Failed to get relevant cases: {e}")
            return []
    
    def get_best_practices(self, domain: str = None, practice_type: str = None, limit: int = 10) -> List[BestPractice]:
        """
        获取最佳实践
        
        Args:
            domain: 领域过滤
            practice_type: 实践类型过滤
            limit: 返回数量限制
        
        Returns:
            最佳实践列表
        """
        try:
            practices = list(self.best_practices.values())
            
            # 过滤
            if domain:
                practices = [p for p in practices if p.domain == domain]
            if practice_type:
                practices = [p for p in practices if p.practice_type == practice_type]
            
            # 按置信度和使用次数排序
            practices.sort(key=lambda x: (x.confidence_score, x.usage_count), reverse=True)
            
            return practices[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get best practices: {e}")
            return []
    
    def enhance_context(self, user_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强上下文信息
        
        Args:
            user_prompt: 用户提示
            context: 原始上下文
        
        Returns:
            增强后的上下文
        """
        try:
            enhanced_context = context.copy()
            
            # 搜索相关知识
            knowledge_results = self.search_knowledge(user_prompt, limit=5)
            if knowledge_results.items:
                enhanced_context['relevant_knowledge'] = [
                    {
                        'title': item.title,
                        'content': item.content,
                        'category': item.category,
                        'confidence': item.confidence
                    }
                    for item in knowledge_results.items
                ]
            
            # 获取相关案例
            relevant_cases = self.get_relevant_cases(user_prompt, limit=3)
            if relevant_cases:
                enhanced_context['relevant_cases'] = [
                    {
                        'title': case.title,
                        'problem': case.problem,
                        'solution': case.solution,
                        'lessons_learned': case.lessons_learned
                    }
                    for case in relevant_cases
                ]
            
            # 获取最佳实践
            best_practices = self.get_best_practices(limit=3)
            if best_practices:
                enhanced_context['best_practices'] = [
                    {
                        'title': practice.title,
                        'description': practice.description,
                        'steps': practice.steps,
                        'benefits': practice.benefits
                    }
                    for practice in best_practices
                ]
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Failed to enhance context: {e}")
            return context
    
    def add_knowledge_item(self, item: KnowledgeItem):
        """添加知识项"""
        self.knowledge_items[item.id] = item
        self._rebuild_search_index()
        self._save_knowledge_data()
    
    def add_case_study(self, case: CaseStudy):
        """添加案例研究"""
        self.case_studies[case.id] = case
        self._rebuild_search_index()
        self._save_knowledge_data()
    
    def add_best_practice(self, practice: BestPractice):
        """添加最佳实践"""
        self.best_practices[practice.id] = practice
        self._rebuild_search_index()
        self._save_knowledge_data()
    
    def _rebuild_search_index(self):
        """重建搜索索引"""
        self._build_search_index()
    
    def _save_knowledge_data(self):
        """保存知识数据"""
        try:
            # 保存知识项
            knowledge_file = self.cache_dir / "knowledge_items.json"
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                data = [asdict(item) for item in self.knowledge_items.values()]
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存案例研究
            cases_file = self.cache_dir / "case_studies.json"
            with open(cases_file, 'w', encoding='utf-8') as f:
                data = [asdict(case) for case in self.case_studies.values()]
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存最佳实践
            practices_file = self.cache_dir / "best_practices.json"
            with open(practices_file, 'w', encoding='utf-8') as f:
                data = [asdict(practice) for practice in self.best_practices.values()]
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save knowledge data: {e}")
    
    def _generate_suggestions(self, query: str, results: List[KnowledgeItem]) -> List[str]:
        """生成搜索建议"""
        suggestions = []
        
        # 基于结果生成建议
        categories = set(item.category for item in results)
        for category in categories:
            suggestions.append(f"查看更多{category}相关内容")
        
        # 基于标签生成建议
        all_tags = []
        for item in results:
            all_tags.extend(item.tags)
        
        from collections import Counter
        common_tags = Counter(all_tags).most_common(3)
        for tag, _ in common_tags:
            if tag.lower() not in query.lower():
                suggestions.append(f"搜索'{tag}'相关内容")
        
        return suggestions[:5]

# 工厂函数
def create_knowledge_integration(knowledge_base_path: str = None) -> KnowledgeIntegration:
    """创建知识库集成实例"""
    return KnowledgeIntegration(knowledge_base_path)

# 使用示例
if __name__ == "__main__":
    # 创建知识库集成系统
    ki = create_knowledge_integration()
    
    # 搜索知识
    results = ki.search_knowledge("水位控制PID参数调优")
    print(f"Found {len(results.items)} relevant items")
    
    for item in results.items:
        print(f"- {item.title} (confidence: {item.confidence:.2f})")
    
    # 获取相关案例
    cases = ki.get_relevant_cases("洪水控制优化")
    print(f"\nFound {len(cases)} relevant cases")
    
    for case in cases:
        print(f"- {case.title}")
    
    # 获取最佳实践
    practices = ki.get_best_practices(domain="水位控制")
    print(f"\nFound {len(practices)} best practices")
    
    for practice in practices:
        print(f"- {practice.title}")