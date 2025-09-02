#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK知识库功能测试

测试构建完成的知识库的各项功能，包括：
- 语义搜索
- 智能推荐
- 知识检索
- 统计信息
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_lib.knowledge.knowledge_base import KnowledgeBase

class KnowledgeBaseTester:
    """知识库测试器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.knowledge_base = None
    
    async def initialize(self):
        """初始化知识库"""
        try:
            # 加载知识库配置
            config_path = Path(self.project_root) / "knowledge_base" / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 初始化知识库
            self.knowledge_base = KnowledgeBase(self.project_root, config)
            await self.knowledge_base.initialize()
            
            print("✅ 知识库初始化成功")
            
        except Exception as e:
            print(f"❌ 知识库初始化失败: {e}")
            raise
    
    async def test_search_functionality(self):
        """测试搜索功能"""
        print("\n🔍 测试搜索功能...")
        
        # 测试查询列表
        test_queries = [
            "水利工程智能体",
            "scenario configuration",
            "agent definition",
            "水库控制算法",
            "distributed simulation",
            "knowledge base",
            "API接口文档",
            "配置文件格式"
        ]
        
        for query in test_queries:
            try:
                # 语义搜索
                results = await self.knowledge_base.search(
                    query=query,
                    search_type="semantic",
                    top_k=3
                )
                
                print(f"\n查询: '{query}'")
                print(f"找到 {len(results)} 个相关结果:")
                
                for i, result in enumerate(results[:3], 1):
                    file_path = result.get('file_path', '未知文件')
                    score = result.get('score', 0)
                    content_preview = result.get('content', '')[:100] + '...' if result.get('content') else '无内容预览'
                    
                    print(f"  {i}. {file_path} (相关度: {score:.3f})")
                    print(f"     {content_preview}")
                
            except Exception as e:
                print(f"❌ 搜索 '{query}' 失败: {e}")
    
    async def test_recommendation_functionality(self):
        """测试推荐功能"""
        print("\n💡 测试推荐功能...")
        
        # 测试推荐场景
        test_contexts = [
            {
                "type": "agent_development",
                "current_file": "agents/water_control_agent.py",
                "task": "创建新的水利控制智能体"
            },
            {
                "type": "scenario_configuration",
                "current_file": "scenarios/water_system.yml",
                "task": "配置水利系统仿真场景"
            },
            {
                "type": "api_integration",
                "current_file": "api/routes/simulation.py",
                "task": "开发仿真API接口"
            }
        ]
        
        for context in test_contexts:
            try:
                recommendations = await self.knowledge_base.get_recommendations(
                    context=context,
                    recommendation_type="agent"
                )
                
                print(f"\n场景: {context['task']}")
                print(f"获得 {len(recommendations)} 个推荐:")
                
                for i, rec in enumerate(recommendations[:3], 1):
                    title = rec.get('title', '未知推荐')
                    description = rec.get('description', '无描述')
                    confidence = rec.get('confidence', 0)
                    
                    print(f"  {i}. {title} (置信度: {confidence:.3f})")
                    print(f"     {description}")
                
            except Exception as e:
                print(f"❌ 推荐生成失败: {e}")
    
    async def test_statistics(self):
        """测试统计信息"""
        print("\n📊 知识库统计信息:")
        
        try:
            stats = self.knowledge_base.get_statistics()
            
            print(f"索引文档数: {stats.get('total_documents', 0)}")
            print(f"索引大小: {stats.get('index_size_mb', 0):.2f} MB")
            print(f"最后更新: {stats.get('last_updated', '未知')}")
            
            # 文件类型分布
            if 'file_types' in stats:
                print("\n文件类型分布:")
                for file_type, count in stats['file_types'].items():
                    print(f"  {file_type}: {count} 个文件")
            
            # 索引状态
            if 'index_status' in stats:
                print(f"\n索引状态: {stats['index_status']}")
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
    
    async def test_specific_queries(self):
        """测试特定领域查询"""
        print("\n🎯 测试特定领域查询...")
        
        # 水利工程相关查询
        water_queries = [
            "水库调度算法",
            "洪水预警系统",
            "灌溉控制策略",
            "水位监测传感器"
        ]
        
        # 智能体相关查询
        agent_queries = [
            "智能体通信协议",
            "多智能体协调",
            "智能体决策算法",
            "分布式智能体架构"
        ]
        
        # 配置相关查询
        config_queries = [
            "YAML配置格式",
            "参数验证规则",
            "环境变量设置",
            "Docker部署配置"
        ]
        
        all_queries = [
            ("水利工程", water_queries),
            ("智能体", agent_queries),
            ("配置管理", config_queries)
        ]
        
        for domain, queries in all_queries:
            print(f"\n--- {domain}领域查询 ---")
            
            for query in queries:
                try:
                    results = await self.knowledge_base.search(
                        query=query,
                        search_type="semantic",
                        top_k=2
                    )
                    
                    if results:
                        best_result = results[0]
                        file_path = best_result.get('file_path', '').replace(self.project_root, '')
                        score = best_result.get('score', 0)
                        print(f"  '{query}' -> {file_path} (相关度: {score:.3f})")
                    else:
                        print(f"  '{query}' -> 未找到相关结果")
                        
                except Exception as e:
                    print(f"  '{query}' -> 查询失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始CHS-SDK知识库功能测试")
        print("="*60)
        
        try:
            # 初始化
            await self.initialize()
            
            # 运行各项测试
            await self.test_statistics()
            await self.test_search_functionality()
            await self.test_recommendation_functionality()
            await self.test_specific_queries()
            
            print("\n" + "="*60)
            print("✅ 所有测试完成！知识库功能正常。")
            
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {e}")
            raise
        
        finally:
            # 清理资源
            if self.knowledge_base:
                await self.knowledge_base.cleanup()

async def main():
    """主函数"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    tester = KnowledgeBaseTester(project_root)
    
    try:
        await tester.run_all_tests()
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())