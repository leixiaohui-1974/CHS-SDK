#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 知识库交互式测试工具
提供实时搜索体验和功能演示
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.knowledge.knowledge_base import KnowledgeBase
    from core_lib.knowledge.recommendation_engine import RecommendationEngine
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在CHS-SDK项目根目录下运行此脚本")
    sys.exit(1)

class InteractiveKnowledgeTest:
    """交互式知识库测试工具"""
    
    def __init__(self):
        self.kb = None
        self.recommendation_engine = None
        self.search_history = []
        
    async def initialize(self):
        """初始化知识库"""
        print("🚀 正在初始化CHS-SDK知识库...")
        try:
            self.kb = KnowledgeBase(project_root=project_root)
            await self.kb.initialize()
            
            # 获取统计信息
            try:
                stats = self.kb.get_statistics() if hasattr(self.kb, 'get_statistics') else {}
                # 提取关键统计信息
                search_stats = stats.get('search_engine_stats', {})
                total_docs = search_stats.get('total_documents', 'N/A')
                index_size = search_stats.get('index_size', 'N/A')
                last_updated = stats.get('last_update', 'N/A')
                stats = {'total_documents': total_docs, 'index_size': index_size, 'last_updated': last_updated}
            except:
                stats = {'total_documents': 'N/A', 'index_size': 'N/A', 'last_updated': 'N/A'}
                
            print(f"✅ 知识库初始化成功!")
            print(f"📊 统计信息:")
            print(f"   - 总文档数: {stats.get('total_documents', 'N/A')}")
            print(f"   - 索引大小: {stats.get('index_size', 'N/A')}")
            print(f"   - 最后更新: {stats.get('last_updated', 'N/A')}")
            
            # 初始化推荐引擎
            try:
                # 创建推荐引擎配置
                rec_config = {
                    "recommendation_threshold": 0.7,
                    "max_recommendations": 5,
                    "context_weight": 0.6,
                    "popularity_weight": 0.3,
                    "similarity_weight": 0.1
                }
                kb_path = project_root / "knowledge_base"
                self.recommendation_engine = RecommendationEngine(kb_path, rec_config)
                print("🎯 推荐引擎已就绪")
            except Exception as e:
                print(f"⚠️ 推荐引擎初始化失败: {e}")
                self.recommendation_engine = None
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        return True
    
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🔍 CHS-SDK 知识库交互式测试工具")
        print("="*60)
        print("1. 语义搜索 (Semantic Search)")
        print("2. 关键词搜索 (Keyword Search)")
        print("3. 混合搜索 (Hybrid Search)")
        print("4. 过滤器搜索 (Filtered Search)")
        print("5. 智能推荐 (Smart Recommendations)")
        print("6. 搜索历史 (Search History)")
        print("7. 知识库统计 (Statistics)")
        print("8. 性能测试 (Performance Test)")
        print("9. 帮助信息 (Help)")
        print("0. 退出 (Exit)")
        print("-"*60)
    
    async def perform_search(self, search_type: str, query: str, **kwargs):
        """执行搜索并记录历史"""
        start_time = time.time()
        
        try:
            # 将 limit 参数转换为 top_k
            if 'limit' in kwargs:
                kwargs['top_k'] = kwargs.pop('limit')
            
            results = await self.kb.search(query, search_type=search_type, **kwargs)
            
            search_time = time.time() - start_time
            
            # 记录搜索历史
            self.search_history.append({
                'query': query,
                'type': search_type,
                'results_count': len(results),
                'search_time': search_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            return results, search_time
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return [], 0
    
    def display_results(self, results: List[Dict[str, Any]], search_time: float, query: str):
        """显示搜索结果"""
        print(f"\n🔍 搜索查询: '{query}'")
        print(f"⏱️  搜索耗时: {search_time:.3f}秒")
        print(f"📄 找到 {len(results)} 个结果\n")
        
        if not results:
            print("❌ 没有找到相关结果")
            return
        
        for i, result in enumerate(results[:5], 1):  # 只显示前5个结果
            print(f"📋 结果 {i}:")
            
            # 从metadata中提取信息
            metadata = result.get('metadata', {})
            title = metadata.get('title', result.get('title', 'N/A'))
            doc_type = metadata.get('doc_type', result.get('doc_type', 'N/A'))
            file_path = metadata.get('file_path', result.get('file_path', 'N/A'))
            tags = metadata.get('tags', result.get('tags', []))
            
            print(f"   标题: {title}")
            print(f"   类型: {doc_type}")
            print(f"   路径: {file_path}")
            print(f"   相似度: {result.get('score', 0):.3f}")
            
            # 显示内容预览
            content = result.get('content', '')
            preview = content[:200] + '...' if len(content) > 200 else content
            print(f"   预览: {preview}")
            print(f"   标签: {', '.join(tags)}")
            print("-" * 50)
    
    async def semantic_search_test(self):
        """语义搜索测试"""
        print("\n🧠 语义搜索模式")
        print("提示: 使用自然语言描述您要查找的内容")
        
        while True:
            query = input("\n请输入搜索查询 (输入 'back' 返回主菜单): ").strip()
            if query.lower() == 'back':
                break
            if not query:
                continue
                
            # 可选参数
            try:
                limit = int(input("结果数量限制 (默认5): ") or "5")
            except ValueError:
                limit = 5
                
            results, search_time = await self.perform_search("semantic", query, top_k=limit)
            self.display_results(results, search_time, query)
    
    async def keyword_search_test(self):
        """关键词搜索测试"""
        print("\n🔤 关键词搜索模式")
        print("提示: 使用具体的关键词或短语")
        
        while True:
            query = input("\n请输入关键词 (输入 'back' 返回主菜单): ").strip()
            if query.lower() == 'back':
                break
            if not query:
                continue
                
            results, search_time = await self.perform_search("keyword", query)
            self.display_results(results, search_time, query)
    
    async def hybrid_search_test(self):
        """混合搜索测试"""
        print("\n🔀 混合搜索模式")
        print("提示: 结合语义理解和关键词匹配的最佳效果")
        
        while True:
            query = input("\n请输入搜索查询 (输入 'back' 返回主菜单): ").strip()
            if query.lower() == 'back':
                break
            if not query:
                continue
                
            results, search_time = await self.perform_search("hybrid", query)
            self.display_results(results, search_time, query)
    
    async def filtered_search_test(self):
        """过滤器搜索测试"""
        print("\n🎯 过滤器搜索模式")
        print("可用过滤器: doc_type, file_path, tags")
        
        while True:
            query = input("\n请输入搜索查询 (输入 'back' 返回主菜单): ").strip()
            if query.lower() == 'back':
                break
            if not query:
                continue
            
            # 设置过滤器
            filters = {}
            doc_type = input("文档类型过滤 (python/markdown/yaml/text, 可选): ").strip()
            if doc_type:
                filters['doc_type'] = doc_type
                
            file_path = input("文件路径过滤 (包含特定路径, 可选): ").strip()
            if file_path:
                filters['file_path'] = file_path
                
            tags = input("标签过滤 (逗号分隔, 可选): ").strip()
            if tags:
                filters['tags'] = [tag.strip() for tag in tags.split(',')]
            
            results, search_time = await self.perform_search("hybrid", query, filters=filters)
            self.display_results(results, search_time, query)
    
    async def recommendation_test(self):
        """智能推荐测试"""
        if not self.recommendation_engine:
            print("\n❌ 推荐引擎不可用")
            return
            
        print("\n🎯 智能推荐系统")
        print("1. 智能体推荐")
        print("2. 配置推荐")
        print("3. 模板推荐")
        
        choice = input("请选择推荐类型 (1-3): ").strip()
        
        if choice == "1":
            scenario = input("请输入场景描述 (如: 洪水控制): ").strip()
            keywords = input("请输入关键词 (逗号分隔): ").strip()
            if scenario or keywords:
                try:
                    context = {
                        "scenario": scenario,
                        "keywords": keywords.split(',') if keywords else [],
                        "project_type": "water_management",
                        "current_agents": []
                    }
                    recommendations = await self.recommendation_engine.get_recommendations(context, "agent")
                    print(f"\n🤖 智能体推荐:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        print(f"{i}. {rec.get('name', 'N/A')} (评分: {rec.get('score', 0):.3f})")
                        print(f"   描述: {rec.get('metadata', {}).get('description', 'N/A')}")
                        print(f"   推荐理由: {rec.get('reason', 'N/A')}")
                        print("-" * 50)
                except Exception as e:
                    print(f"❌ 推荐失败: {e}")
        
        elif choice == "2":
            scenario = input("请输入场景描述: ").strip()
            if scenario:
                try:
                    context = {
                        "scenario": scenario,
                        "project_type": "water_management",
                        "keywords": [scenario]
                    }
                    recommendations = await self.recommendation_engine.get_recommendations(context, "config")
                    print(f"\n⚙️ 配置推荐:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        print(f"{i}. {rec.get('name', 'N/A')} (评分: {rec.get('score', 0):.3f})")
                        print(f"   推荐理由: {rec.get('reason', 'N/A')}")
                        print("-" * 50)
                except Exception as e:
                    print(f"❌ 推荐失败: {e}")
        
        elif choice == "3":
            scenario = input("请输入场景描述: ").strip()
            if scenario:
                try:
                    context = {
                        "scenario": scenario,
                        "project_type": "water_management",
                        "keywords": [scenario]
                    }
                    recommendations = await self.recommendation_engine.get_recommendations(context, "template")
                    print(f"\n📋 模板推荐:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        print(f"{i}. {rec.get('name', 'N/A')} (评分: {rec.get('score', 0):.3f})")
                        print(f"   描述: {rec.get('metadata', {}).get('description', 'N/A')}")
                        print(f"   推荐理由: {rec.get('reason', 'N/A')}")
                        print("-" * 50)
                except Exception as e:
                    print(f"❌ 推荐失败: {e}")
    
    def show_search_history(self):
        """显示搜索历史"""
        print("\n📚 搜索历史")
        if not self.search_history:
            print("暂无搜索历史")
            return
        
        print(f"总共 {len(self.search_history)} 次搜索:")
        for i, record in enumerate(self.search_history[-10:], 1):  # 显示最近10次
            print(f"{i}. [{record['timestamp']}] {record['type']} - '{record['query']}'")
            print(f"   结果: {record['results_count']} 个, 耗时: {record['search_time']:.3f}秒")
    
    async def show_statistics(self):
        """显示知识库统计信息"""
        print("\n📊 知识库统计信息")
        try:
            if hasattr(self.kb, 'get_statistics'):
                stats = self.kb.get_statistics()
                # 提取关键统计信息
                search_stats = stats.get('search_engine_stats', {})
                total_docs = search_stats.get('total_documents', 'N/A')
                index_size = search_stats.get('index_size', 'N/A')
                last_updated = stats.get('last_update', 'N/A')
                stats = {'total_documents': total_docs, 'index_size': index_size, 'last_updated': last_updated}
            else:
                stats = {'total_documents': 'N/A', 'index_size': 'N/A', 'last_updated': 'N/A'}
                
            print(f"总文档数: {stats.get('total_documents', 'N/A')}")
            print(f"索引大小: {stats.get('index_size', 'N/A')}")
            print(f"最后更新: {stats.get('last_updated', 'N/A')}")
            
            # 搜索统计
            if self.search_history:
                total_searches = len(self.search_history)
                avg_time = sum(r['search_time'] for r in self.search_history) / total_searches
                print(f"\n🔍 搜索统计:")
                print(f"总搜索次数: {total_searches}")
                print(f"平均搜索时间: {avg_time:.3f}秒")
                
                # 按类型统计
                type_counts = {}
                for record in self.search_history:
                    type_counts[record['type']] = type_counts.get(record['type'], 0) + 1
                
                print("搜索类型分布:")
                for search_type, count in type_counts.items():
                    print(f"  {search_type}: {count} 次")
                    
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
    
    async def performance_test(self):
        """性能测试"""
        print("\n⚡ 性能测试")
        test_queries = [
            "水位控制",
            "agent configuration",
            "洪水预警系统",
            "API documentation",
            "智能体架构"
        ]
        
        print("正在执行性能测试...")
        results = {}
        
        for search_type in ["semantic", "keyword", "hybrid"]:
            print(f"\n测试 {search_type} 搜索:")
            times = []
            
            for query in test_queries:
                _, search_time = await self.perform_search(search_type, query, top_k=5)
                times.append(search_time)
                print(f"  '{query}': {search_time:.3f}秒")
            
            avg_time = sum(times) / len(times)
            results[search_type] = {
                'avg_time': avg_time,
                'min_time': min(times),
                'max_time': max(times)
            }
        
        print("\n📊 性能测试结果:")
        for search_type, stats in results.items():
            print(f"{search_type}:")
            print(f"  平均: {stats['avg_time']:.3f}秒")
            print(f"  最快: {stats['min_time']:.3f}秒")
            print(f"  最慢: {stats['max_time']:.3f}秒")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n❓ 帮助信息")
        print("="*50)
        print("🧠 语义搜索: 使用AI理解查询意图，适合自然语言查询")
        print("🔤 关键词搜索: 精确匹配关键词，适合已知术语查询")
        print("🔀 混合搜索: 结合语义和关键词，提供最佳搜索效果")
        print("🎯 过滤器搜索: 在搜索基础上添加条件过滤")
        print("🎯 智能推荐: 基于上下文提供相关内容推荐")
        print("\n💡 搜索技巧:")
        print("- 语义搜索: '如何配置水位控制系统'")
        print("- 关键词搜索: 'WaterLevelAgent'")
        print("- 混合搜索: '智能体配置文件'")
        print("- 使用过滤器缩小搜索范围")
        print("- 查看搜索历史了解使用模式")
    
    async def run(self):
        """运行交互式测试"""
        if not await self.initialize():
            return
        
        print("\n🎉 欢迎使用CHS-SDK知识库交互式测试工具!")
        print("您可以实时体验各种搜索功能和智能推荐")
        
        while True:
            self.display_menu()
            choice = input("请选择功能 (0-9): ").strip()
            
            if choice == "0":
                print("\n👋 感谢使用! 再见!")
                break
            elif choice == "1":
                await self.semantic_search_test()
            elif choice == "2":
                await self.keyword_search_test()
            elif choice == "3":
                await self.hybrid_search_test()
            elif choice == "4":
                await self.filtered_search_test()
            elif choice == "5":
                await self.recommendation_test()
            elif choice == "6":
                self.show_search_history()
            elif choice == "7":
                await self.show_statistics()
            elif choice == "8":
                await self.performance_test()
            elif choice == "9":
                self.show_help()
            else:
                print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    tester = InteractiveKnowledgeTest()
    asyncio.run(tester.run())