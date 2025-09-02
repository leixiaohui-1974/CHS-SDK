#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 知识库使用演示

这个脚本演示了如何使用CHS-SDK知识库进行各种类型的搜索和查询。
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def demo_basic_search():
    """演示基本搜索功能"""
    print("=" * 60)
    print("CHS-SDK 知识库使用演示")
    print("=" * 60)
    
    try:
        # 初始化知识库
        print("\n1. 初始化知识库...")
        kb = KnowledgeBase(str(project_root))
        await kb.initialize()
        
        # 获取知识库统计信息
        stats = kb.get_statistics()
        print(f"   知识库已初始化: {stats['is_initialized']}")
        
        # 演示语义搜索
        print("\n2. 语义搜索演示")
        print("-" * 30)
        query = "如何配置水利仿真参数"
        print(f"查询: {query}")
        
        results = await kb.search(query, search_type="semantic", top_k=3)
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            file_path = metadata.get('file_path', 'N/A')
            print(f"  标题: {title}")
            print(f"  文件: {file_path}")
            print(f"  相关度: {result.get('score', 0):.3f}")
            content = result.get('content', '')
            print(f"  内容摘要: {content[:150]}..." if len(content) > 150 else f"  内容: {content}")
        
        # 演示关键词搜索
        print("\n\n3. 关键词搜索演示")
        print("-" * 30)
        query = "agent"
        print(f"查询: {query}")
        
        results = await kb.search(query, search_type="keyword", top_k=3)
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            file_path = metadata.get('file_path', 'N/A')
            print(f"  标题: {title}")
            print(f"  文件: {file_path}")
            print(f"  相关度: {result.get('score', 0):.3f}")
            content = result.get('content', '')
            print(f"  内容摘要: {content[:150]}..." if len(content) > 150 else f"  内容: {content}")
        
        # 演示混合搜索
        print("\n\n4. 混合搜索演示")
        print("-" * 30)
        query = "智能体配置"
        print(f"查询: {query}")
        
        results = await kb.search(query, search_type="hybrid", top_k=3)
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            file_path = metadata.get('file_path', 'N/A')
            print(f"  标题: {title}")
            print(f"  文件: {file_path}")
            print(f"  相关度: {result.get('score', 0):.3f}")
            content = result.get('content', '')
            print(f"  内容摘要: {content[:150]}..." if len(content) > 150 else f"  内容: {content}")
        
        # 演示推荐功能
        print("\n\n5. 推荐功能演示")
        print("-" * 30)
        query = "水位控制算法"
        print(f"基于查询获取推荐: {query}")
        
        recommendations = await kb.get_recommendations({"query": query}, "agent")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n推荐 {i}:")
                metadata = rec.get('metadata', {})
                title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                file_path = metadata.get('file_path', 'N/A')
                print(f"  标题: {title}")
                print(f"  文件: {file_path}")
                print(f"  相关度: {rec.get('score', 0):.3f}")
        else:
            print("  暂无推荐结果")
        
        # 演示按类型搜索
        print("\n\n6. 按类型搜索演示")
        print("-" * 30)
        
        # 搜索类定义
        print("\n按文档类型搜索:")
        class_results = await kb.search("class", search_type="keyword", filters={"doc_type": "class_definition"}, top_k=2)
        for i, result in enumerate(class_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            print(f"  类定义 {i}: {title} (相关度: {result.get('score', 0):.3f})")
        
        # 搜索智能体定义
        agent_results = await kb.search("agent", search_type="keyword", filters={"doc_type": "agent_definition"}, top_k=2)
        for i, result in enumerate(agent_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            print(f"  智能体 {i}: {title} (相关度: {result.get('score', 0):.3f})")
        
        # 搜索配置文件
        config_results = await kb.search("config", search_type="keyword", filters={"doc_type": "agent_configuration"}, top_k=2)
        for i, result in enumerate(config_results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
            print(f"  配置 {i}: {title} (相关度: {result.get('score', 0):.3f})")
        
        print("\n\n=" * 60)
        print("演示完成！")
        print("\n使用提示:")
        print("- 语义搜索适合概念性查询")
        print("- 关键词搜索适合精确匹配")
        print("- 混合搜索结合两者优势")
        print("- 按类型搜索可以缩小范围")
        print("- 推荐功能基于相似性分析")
        print("=" * 60)
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("\n可能的解决方案:")
        print("1. 确保知识库已正确构建: python build_complete_knowledge_base.py")
        print("2. 检查依赖是否安装完整: pip install -r requirements.txt")
        print("3. 查看详细错误信息，检查配置文件")
    
    finally:
        # 清理资源
        try:
            await kb.cleanup()
        except:
            pass

async def interactive_search():
    """交互式搜索演示"""
    print("\n" + "=" * 60)
    print("交互式搜索模式")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60)
    
    try:
        kb = KnowledgeBase(str(project_root))
        await kb.initialize()
        
        while True:
            query = input("\n请输入搜索查询: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                break
            
            if not query:
                continue
            
            print("\n选择搜索类型:")
            print("1. 语义搜索 (semantic)")
            print("2. 关键词搜索 (keyword)")
            print("3. 混合搜索 (hybrid)")
            
            choice = input("请选择 (1-3, 默认为3): ").strip()
            
            search_type_map = {
                '1': 'semantic',
                '2': 'keyword',
                '3': 'hybrid'
            }
            
            search_type = search_type_map.get(choice, 'hybrid')
            
            print(f"\n正在执行{search_type}搜索...")
            
            results = await kb.search(query, search_type=search_type, top_k=5)
            
            if results:
                print(f"\n找到 {len(results)} 个结果:")
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                    file_path = metadata.get('file_path', 'N/A')
                    print(f"\n{i}. {title}")
                    print(f"   文件: {file_path}")
                    print(f"   相关度: {result.get('score', 0):.3f}")
                    content = result.get('content', '')
                    print(f"   摘要: {content[:200]}..." if len(content) > 200 else f"   内容: {content}")
            else:
                print("\n未找到相关结果，请尝试其他查询词。")
    
    except Exception as e:
        print(f"交互式搜索出现错误: {e}")
    
    finally:
        try:
            await kb.cleanup()
        except:
            pass
        print("\n感谢使用CHS-SDK知识库！")

async def main():
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_search()
    else:
        await demo_basic_search()
        
        # 询问是否进入交互模式
        response = input("\n是否进入交互式搜索模式？(y/n): ").strip().lower()
        if response in ['y', 'yes', '是']:
            await interactive_search()

if __name__ == "__main__":
    asyncio.run(main())