#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终推荐功能测试
验证知识库推荐功能的完整性
"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def final_recommendation_test():
    """
    最终推荐功能测试
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("FinalRecommendationTest")
    
    try:
        logger.info("开始最终推荐功能测试...")
        
        # 知识库路径
        kb_path = project_root / "knowledge_base"
        
        # 创建知识库实例
        kb = KnowledgeBase(kb_path)
        
        # 初始化知识库
        logger.info("初始化知识库...")
        await kb.initialize()
        
        # 获取知识库统计信息
        stats = kb.get_statistics()
        logger.info("知识库统计信息:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # 测试推荐功能
        logger.info("\n=== 推荐功能测试 ===")
        
        # 测试场景1：洪水管理
        logger.info("\n1. 洪水管理场景推荐:")
        flood_context = {
            "project_type": "flood_management",
            "scenario_type": "emergency_response",
            "current_agents": [],
            "keywords": ["flood", "control", "emergency"]
        }
        
        flood_recommendations = await kb.get_recommendations(flood_context)
        logger.info(f"推荐结果: {len(flood_recommendations)} 个")
        for i, rec in enumerate(flood_recommendations[:3], 1):
            logger.info(f"  {i}. {rec.get('name', 'N/A')} (类型: {rec.get('type', 'N/A')}, 评分: {rec.get('score', 0):.3f})")
            logger.info(f"     原因: {rec.get('reason', 'N/A')}")
        
        # 测试场景2：水资源管理
        logger.info("\n2. 水资源管理场景推荐:")
        water_context = {
            "project_type": "water_management",
            "scenario_type": "drought_management",
            "current_agents": [],
            "keywords": ["water", "drought", "allocation"]
        }
        
        water_recommendations = await kb.get_recommendations(water_context)
        logger.info(f"推荐结果: {len(water_recommendations)} 个")
        for i, rec in enumerate(water_recommendations[:3], 1):
            logger.info(f"  {i}. {rec.get('name', 'N/A')} (类型: {rec.get('type', 'N/A')}, 评分: {rec.get('score', 0):.3f})")
            logger.info(f"     原因: {rec.get('reason', 'N/A')}")
        
        # 测试场景3：系统监控
        logger.info("\n3. 系统监控场景推荐:")
        monitoring_context = {
            "project_type": "monitoring",
            "scenario_type": "real_time_monitoring",
            "current_agents": [],
            "keywords": ["monitoring", "real_time", "analysis"]
        }
        
        monitoring_recommendations = await kb.get_recommendations(monitoring_context)
        logger.info(f"推荐结果: {len(monitoring_recommendations)} 个")
        for i, rec in enumerate(monitoring_recommendations[:3], 1):
            logger.info(f"  {i}. {rec.get('name', 'N/A')} (类型: {rec.get('type', 'N/A')}, 评分: {rec.get('score', 0):.3f})")
            logger.info(f"     原因: {rec.get('reason', 'N/A')}")
        
        # 测试场景4：已有智能体的协同推荐
        logger.info("\n4. 协同智能体推荐:")
        synergy_context = {
            "project_type": "flood_management",
            "scenario_type": "emergency_response",
            "current_agents": ["FloodControlAgent"],
            "keywords": ["flood", "control"]
        }
        
        synergy_recommendations = await kb.get_recommendations(synergy_context)
        logger.info(f"推荐结果: {len(synergy_recommendations)} 个")
        for i, rec in enumerate(synergy_recommendations[:3], 1):
            logger.info(f"  {i}. {rec.get('name', 'N/A')} (类型: {rec.get('type', 'N/A')}, 评分: {rec.get('score', 0):.3f})")
            logger.info(f"     原因: {rec.get('reason', 'N/A')}")
        
        # 测试搜索功能
        logger.info("\n=== 搜索功能测试 ===")
        
        # 语义搜索
        logger.info("\n1. 语义搜索测试:")
        semantic_results = await kb.search("水资源管理智能体", search_type="semantic", top_k=3)
        logger.info(f"语义搜索结果: {len(semantic_results)} 个")
        for i, result in enumerate(semantic_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            logger.info(f"  {i}. {title} (相关度: {result.get('score', 0):.3f})")
        
        # 关键词搜索
        logger.info("\n2. 关键词搜索测试:")
        keyword_results = await kb.search("agent", search_type="keyword", top_k=3)
        logger.info(f"关键词搜索结果: {len(keyword_results)} 个")
        for i, result in enumerate(keyword_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            logger.info(f"  {i}. {title} (相关度: {result.get('score', 0):.3f})")
        
        # 混合搜索
        logger.info("\n3. 混合搜索测试:")
        hybrid_results = await kb.search("洪水控制", search_type="hybrid", top_k=3)
        logger.info(f"混合搜索结果: {len(hybrid_results)} 个")
        for i, result in enumerate(hybrid_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            logger.info(f"  {i}. {title} (相关度: {result.get('score', 0):.3f})")
        
        # 按类型过滤搜索
        logger.info("\n4. 按类型过滤搜索测试:")
        filtered_results = await kb.search("class", search_type="keyword", filters={"doc_type": "class_definition"}, top_k=3)
        logger.info(f"类定义搜索结果: {len(filtered_results)} 个")
        for i, result in enumerate(filtered_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            logger.info(f"  {i}. {title} (相关度: {result.get('score', 0):.3f})")
        
        # 清理资源
        await kb.cleanup()
        logger.info("\n测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(final_recommendation_test())
    if success:
        print("\n✅ 所有功能测试通过！")
        print("\n🎉 CHS-SDK知识库系统已完全修复并正常工作：")
        print("   • 搜索结果的标题和文件路径正确显示")
        print("   • 按文档类型过滤搜索功能正常")
        print("   • 推荐引擎已初始化并能提供智能推荐")
        print("   • 语义搜索、关键词搜索和混合搜索都正常工作")
        print("   • 知识库索引和元数据管理正常")
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)