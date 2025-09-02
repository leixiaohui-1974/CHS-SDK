#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试推荐引擎评分计算
分析为什么推荐分数没有达到阈值
"""

import asyncio
import logging
from pathlib import Path
import sys
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.recommendation_engine import RecommendationEngine

async def debug_recommendation_scoring():
    """
    调试推荐引擎评分计算
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("DebugRecommendationScoring")
    
    try:
        logger.info("开始调试推荐引擎评分计算...")
        
        # 知识库路径
        kb_path = project_root / "knowledge_base"
        
        # 推荐引擎配置
        config = {
            "recommendation_threshold": 0.3,  # 降低阈值用于调试
            "max_recommendations": 10,
            "context_weight": 0.6,
            "popularity_weight": 0.3,
            "similarity_weight": 0.1
        }
        
        # 创建推荐引擎实例
        recommendation_engine = RecommendationEngine(kb_path, config)
        
        # 初始化推荐引擎
        await recommendation_engine.initialize()
        
        logger.info("推荐引擎初始化完成")
        
        # 检查加载的数据
        logger.info(f"智能体注册表: {len(recommendation_engine.agent_registry)} 个智能体")
        for name, info in recommendation_engine.agent_registry.items():
            logger.info(f"  - {name}: {info.get('category', 'N/A')} ({info.get('type', 'N/A')})")
        
        logger.info(f"配置模板: {len(recommendation_engine.config_templates)} 个模板")
        for name, info in recommendation_engine.config_templates.items():
            logger.info(f"  - {name}: {info.get('category', 'N/A')}")
        
        # 测试上下文
        test_contexts = [
            {
                "project_type": "flood_management",
                "scenario_type": "emergency_response",
                "scenario": "flood_control",
                "current_agents": [],
                "keywords": ["flood", "control", "emergency"]
            },
            {
                "project_type": "water_management",
                "scenario_type": "drought_management",
                "scenario": "water_allocation",
                "current_agents": [],
                "keywords": ["water", "drought", "allocation"]
            },
            {
                "project_type": "monitoring",
                "scenario_type": "real_time_monitoring",
                "scenario": "system_monitoring",
                "current_agents": [],
                "keywords": ["monitoring", "real_time", "analysis"]
            }
        ]
        
        for i, context in enumerate(test_contexts, 1):
            logger.info(f"\n=== 测试场景 {i} ===")
            logger.info(f"上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
            
            # 手动计算每个智能体的评分
            logger.info("\n智能体评分详情:")
            for agent_name, agent_info in recommendation_engine.agent_registry.items():
                score = recommendation_engine._calculate_agent_recommendation_score(
                    agent_info,
                    context.get("scenario", ""),
                    context.get("project_type", ""),
                    context.get("keywords", []),
                    context.get("current_agents", [])
                )
                
                logger.info(f"  {agent_name}: {score:.3f}")
                logger.info(f"    - 类别: {agent_info.get('category', 'N/A')}")
                logger.info(f"    - 用例: {agent_info.get('use_cases', [])}")
                logger.info(f"    - 标签: {agent_info.get('tags', [])}")
                logger.info(f"    - 流行度: {agent_info.get('popularity_score', 0.5)}")
                
                # 详细分析评分组成
                use_cases = agent_info.get("use_cases", [])
                scenario_match = any(context.get("scenario", "").lower() in use_case.lower() for use_case in use_cases)
                
                category = agent_info.get("category", "")
                project_match = context.get("project_type", "").lower() in category.lower()
                
                agent_tags = agent_info.get("tags", [])
                keywords = context.get("keywords", [])
                keyword_matches = sum(1 for keyword in keywords if any(keyword.lower() in tag.lower() for tag in agent_tags))
                
                logger.info(f"    - 场景匹配: {scenario_match}")
                logger.info(f"    - 项目类型匹配: {project_match}")
                logger.info(f"    - 关键词匹配: {keyword_matches}/{len(keywords)}")
            
            # 获取推荐结果
            logger.info("\n智能体推荐结果:")
            agent_recommendations = await recommendation_engine.get_recommendations(context, "agent")
            if agent_recommendations:
                for j, rec in enumerate(agent_recommendations, 1):
                    logger.info(f"  {j}. {rec.get('name', 'N/A')} (评分: {rec.get('score', 0):.3f})")
                    logger.info(f"     原因: {rec.get('reason', 'N/A')}")
            else:
                logger.info("  无推荐结果")
            
            # 模板推荐
            logger.info("\n模板推荐结果:")
            template_recommendations = await recommendation_engine.get_recommendations(context, "template")
            if template_recommendations:
                for j, rec in enumerate(template_recommendations, 1):
                    logger.info(f"  {j}. {rec.get('name', 'N/A')} (评分: {rec.get('score', 0):.3f})")
                    logger.info(f"     原因: {rec.get('reason', 'N/A')}")
            else:
                logger.info("  无推荐结果")
        
        # 清理资源
        await recommendation_engine.cleanup()
        logger.info("\n调试完成！")
        return True
        
    except Exception as e:
        logger.error(f"调试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_recommendation_scoring())
    if success:
        print("\n✅ 调试完成！")
    else:
        print("\n❌ 调试失败！")
        sys.exit(1)