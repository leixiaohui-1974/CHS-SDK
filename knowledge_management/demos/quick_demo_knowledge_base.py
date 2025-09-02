#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 知识库快速演示

这个脚本快速演示CHS-SDK知识库的主要功能，无需用户交互。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def quick_demo():
    """快速演示知识库功能"""
    print("=" * 60)
    print("CHS-SDK 知识库快速演示")
    print("=" * 60)
    
    kb = None
    try:
        # 1. 初始化知识库
        print("\n📚 正在初始化知识库...")
        kb = KnowledgeBase(str(project_root))
        await kb.initialize()
        
        # 获取统计信息
        stats = kb.get_statistics()
        print(f"✅ 知识库初始化完成: {stats['is_initialized']}")
        
        # 2. 语义搜索演示
        print("\n🔍 语义搜索演示")
        print("-" * 30)
        
        queries = [
            "如何配置水利仿真参数",
            "智能体的定义和使用",
            "API接口文档"
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            results = await kb.search(query, search_type="semantic", top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                    score = result.get('score', 0)
                    file_path = metadata.get('file_path', 'N/A')
                    print(f"  {i}. {title} (相关度: {score:.3f})")
                    print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
            else:
                print("  未找到相关结果")
        
        # 3. 关键词搜索演示
        print("\n\n🔎 关键词搜索演示")
        print("-" * 30)
        
        keywords = ["agent", "config", "simulation"]
        
        for keyword in keywords:
            print(f"\n关键词: {keyword}")
            results = await kb.search(keyword, search_type="keyword", top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                    score = result.get('score', 0)
                    file_path = metadata.get('file_path', 'N/A')
                    print(f"  {i}. {title} (相关度: {score:.3f})")
                    print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
            else:
                print("  未找到相关结果")
        
        # 4. 混合搜索演示
        print("\n\n🔀 混合搜索演示")
        print("-" * 30)
        
        hybrid_queries = ["水位控制算法", "配置文件模板"]
        
        for query in hybrid_queries:
            print(f"\n查询: {query}")
            results = await kb.search(query, search_type="hybrid", top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                    score = result.get('score', 0)
                    file_path = metadata.get('file_path', 'N/A')
                    print(f"  {i}. {title} (相关度: {score:.3f})")
                    print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
            else:
                print("  未找到相关结果")
        
        # 5. 推荐功能演示
        print("\n\n💡 推荐功能演示")
        print("-" * 30)
        
        context = {"query": "智能体开发", "current_file": "agent.py"}
        print(f"上下文: {context}")
        
        recommendations = await kb.get_recommendations(context, "agent")
        
        if recommendations:
            print(f"找到 {len(recommendations)} 个推荐:")
            for i, rec in enumerate(recommendations[:3], 1):
                metadata = rec.get('metadata', {})
                title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                score = rec.get('score', 0)
                file_path = metadata.get('file_path', 'N/A')
                print(f"  {i}. {title} (相关度: {score:.3f})")
                print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
        else:
            print("  暂无推荐结果")
        
        # 6. 按类型过滤搜索演示
        print("\n\n📁 按类型过滤搜索演示")
        print("-" * 30)
        
        filter_tests = [
            ("class", {"doc_type": "class_definition"}, "类定义"),
            ("agent", {"doc_type": "agent_definition"}, "智能体定义"),
            ("config", {"doc_type": "agent_configuration"}, "智能体配置"),
            ("function", {"doc_type": "function_definition"}, "函数定义"),
            ("guide", {"doc_type": "markdown_documentation"}, "文档文件")
        ]
        
        for query, filters, desc in filter_tests:
            print(f"\n搜索{desc}中的'{query}':")
            results = await kb.search(query, search_type="keyword", filters=filters, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                    score = result.get('score', 0)
                    file_path = metadata.get('file_path', 'N/A')
                    print(f"  {i}. {title} (相关度: {score:.3f})")
                    print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
            else:
                print(f"  未找到包含'{query}'的{desc}")
        
        print("\n\n=" * 60)
        print("🎉 演示完成！")
        print("\n💡 使用提示:")
        print("• 语义搜索 - 理解查询意图，适合概念性问题")
        print("• 关键词搜索 - 精确匹配，适合查找特定术语")
        print("• 混合搜索 - 结合两者优势，推荐日常使用")
        print("• 类型过滤 - 缩小搜索范围，提高结果精度")
        print("• 智能推荐 - 基于上下文的相关内容推荐")
        print("\n📖 详细使用方法请参考: knowledge_base_usage_guide.md")
        print("🔧 交互式演示请运行: python demo_knowledge_base_usage.py --interactive")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 确保知识库已构建: python build_complete_knowledge_base.py")
        print("2. 检查依赖安装: pip install -r requirements.txt")
        print("3. 查看详细日志获取更多信息")
        
    finally:
        # 清理资源
        if kb:
            try:
                await kb.cleanup()
                print("\n🧹 资源清理完成")
            except Exception as e:
                print(f"\n⚠️  资源清理时出现警告: {e}")

if __name__ == "__main__":
    asyncio.run(quick_demo())