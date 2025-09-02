#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复推荐引擎数据问题
强制重新初始化推荐引擎并生成默认数据
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.recommendation_engine import RecommendationEngine

async def fix_recommendation_engine():
    """
    修复推荐引擎数据问题
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("FixRecommendationEngine")
    
    try:
        logger.info("开始修复推荐引擎...")
        
        # 知识库路径
        kb_path = project_root / "knowledge_base"
        
        # 推荐引擎配置
        config = {
            "recommendation_threshold": 0.7,
            "max_recommendations": 5,
            "context_weight": 0.6,
            "popularity_weight": 0.3,
            "similarity_weight": 0.1
        }
        
        # 创建推荐引擎实例
        recommendation_engine = RecommendationEngine(kb_path, config)
        
        logger.info("检查现有数据文件...")
        
        # 检查数据文件状态
        agent_registry_file = kb_path / "agent_registry.json"
        config_templates_file = kb_path / "config_templates.json"
        usage_history_file = kb_path / "usage_history.json"
        
        logger.info(f"智能体注册表文件存在: {agent_registry_file.exists()}")
        logger.info(f"配置模板文件存在: {config_templates_file.exists()}")
        logger.info(f"使用历史文件存在: {usage_history_file.exists()}")
        
        # 强制重新创建默认数据
        logger.info("强制重新创建默认智能体注册表...")
        await recommendation_engine._create_default_agent_registry()
        
        logger.info("强制重新创建默认配置模板...")
        await recommendation_engine._create_default_templates()
        
        # 初始化推荐引擎
        logger.info("初始化推荐引擎...")
        success = await recommendation_engine.initialize()
        
        if success:
            logger.info("推荐引擎初始化成功！")
            
            # 获取统计信息
            stats = recommendation_engine.get_statistics()
            logger.info("推荐引擎统计信息:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            # 测试推荐功能
            logger.info("\n测试推荐功能...")
            
            # 测试推荐功能
            context = {
                "project_type": "flood_management",
                "scenario_type": "emergency_response",
                "current_agents": []
            }
            
            recommendations = await recommendation_engine.get_recommendations(context)
            logger.info(f"推荐结果: {len(recommendations)} 个推荐")
            for i, rec in enumerate(recommendations[:5], 1):
                logger.info(f"  {i}. {rec.get('name', 'N/A')} (类型: {rec.get('type', 'N/A')}, 评分: {rec.get('score', 0):.2f})")
            
            # 记录一些使用历史
            logger.info("添加测试使用历史...")
            await recommendation_engine.record_usage(
                "FloodControlAgent", 
                "agent", 
                {"scenario": "flood_prevention", "success": True}
            )
            await recommendation_engine.record_usage(
                "flood_control_scenario", 
                "template", 
                {"scenario": "emergency_response", "success": True}
            )
            
            # 再次获取统计信息
            stats = recommendation_engine.get_statistics()
            logger.info("\n更新后的推荐引擎统计信息:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
        else:
            logger.error("推荐引擎初始化失败！")
            return False
        
        # 清理资源
        await recommendation_engine.cleanup()
        logger.info("推荐引擎修复完成！")
        return True
        
    except Exception as e:
        logger.error(f"修复推荐引擎时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_recommendation_engine())
    if success:
        print("\n✅ 推荐引擎修复成功！")
    else:
        print("\n❌ 推荐引擎修复失败！")
        sys.exit(1)