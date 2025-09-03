#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型LLM结果分析代理演示

这个脚本演示了如何使用增强的LLM结果分析代理，包括：
1. 智能数据分析
2. 知识库集成
3. 自动报告生成
4. 多格式输出
5. 案例推荐和最佳实践

作者: CHS-SDK团队
日期: 2024年1月
"""

import asyncio
import sys
from pathlib import Path
import logging
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.llm_integration_agents.enhanced_llm_result_analysis_agent import (
        EnhancedLLMResultAnalysisAgent, ReportConfig
    )
    from core_lib.knowledge.knowledge_base import KnowledgeBase
    from core_lib.llm_services.llm_service import call_tongyi_qianwen_api
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在CHS-SDK项目根目录下运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedAnalysisDemo:
    """
    增强型分析演示类
    """
    
    def __init__(self):
        self.project_root = project_root
        self.output_dir = self.project_root / "examples" / "llm_integration" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.enhanced_agent = None
        self.knowledge_base = None
        
    async def initialize_components(self):
        """
        初始化所有组件
        """
        try:
            logger.info("正在初始化增强型分析代理...")
            self.enhanced_agent = EnhancedLLMResultAnalysisAgent(str(self.project_root))
            
            logger.info("正在初始化知识库...")
            # 创建示例数据
            sample_data = {
                "simulation_results": {
                    "water_level": [1.2, 1.5, 1.8, 2.1, 1.9, 1.6],
                    "flow_rate": [10.5, 12.3, 15.2, 18.7, 16.4, 13.8],
                    "pressure": [0.8, 0.9, 1.1, 1.3, 1.2, 1.0],
                    "timestamps": ["2024-01-01 00:00", "2024-01-01 01:00", 
                                  "2024-01-01 02:00", "2024-01-01 03:00",
                                  "2024-01-01 04:00", "2024-01-01 05:00"]
                },
                "performance_metrics": {
                    "efficiency": 0.85,
                    "stability": 0.92,
                    "response_time": 2.3
                }
            }
            
            logger.info("组件初始化完成")
            return sample_data
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    async def run_basic_analysis_demo(self):
        """
        运行基础分析演示
        """
        logger.info("\n=== 基础分析演示 ===")
        
        # 准备分析上下文
        context = {
            "scenario_type": "reservoir_control",
            "analysis_focus": "dispatch_optimization",
            "data_source": "simulation",
            "data_file": str(self.project_root / "examples" / "llm_integration" / "test_data.csv"),
            "scenario_config": str(self.project_root / "examples" / "llm_integration" / "scenario_config.yml"),
            "problem_description": "水库调度策略优化：在保证防洪安全的前提下，最大化发电效益和供水保障",
            "modeling_approach": "多目标优化控制(MPC)",
            "key_metrics": ["flood_risk", "power_generation", "efficiency", "water_level"]
        }
        
        # 配置报告
        config = ReportConfig(
            format="html",
            include_charts=True,
            include_llm_insights=True,
            template_name="standard"
        )
        
        try:
            # 运行分析
            results = await self.enhanced_agent.run(
                user_prompt="分析水位控制系统的性能表现，识别优化机会",
                context=context,
                config=config
            )
            
            self._display_basic_results(results)
            return results
            
        except Exception as e:
            logger.error(f"基础分析失败: {e}")
            return None
    
    async def run_comprehensive_demo(self):
        """
        运行综合分析演示
        """
        logger.info("\n=== 综合分析演示 ===")
        
        # 准备复杂分析上下文
        context = {
            "scenario_type": "flood_control",
            "analysis_focus": "risk_assessment",
            "data_source": "historical_simulation",
            "time_range": "2024-01-01 to 2024-01-07",
            "critical_parameters": ["water_level", "flow_rate", "gate_position"],
            "data_file": str(self.project_root / "examples" / "llm_integration" / "test_data.csv"),
            "scenario_config": str(self.project_root / "examples" / "llm_integration" / "scenario_config.yml"),
            "problem_description": "洪水控制系统风险评估：基于历史数据的综合安全性分析",
            "modeling_approach": "风险评估模型与预警系统",
            "key_metrics": ["flood_risk", "safety_margin", "response_time", "water_level", "flow_rate"],
            "analysis_depth": "comprehensive",
            "include_sensitivity": True,
            "include_recommendations": True
        }
        
        # 配置详细报告
        config = ReportConfig(
            format="html",
            include_charts=True,
            include_raw_data=True,
            include_llm_insights=True,
            include_knowledge_base=True,
            template_name="detailed"
        )
        
        try:
            # 运行综合分析
            results = await self.enhanced_agent.run(
                user_prompt="""进行洪水控制系统的全面风险评估，包括：
                1. 历史数据趋势分析
                2. 异常模式识别
                3. 风险等级评估
                4. 优化建议
                5. 应急预案建议""",
                context=context,
                config=config
            )
            
            self._display_comprehensive_results(results)
            return results
            
        except Exception as e:
            logger.error(f"综合分析失败: {e}")
            return None
    
    def _display_basic_results(self, results: Dict[str, Any]):
        """
        显示基础分析结果
        """
        if not results:
            logger.warning("没有分析结果可显示")
            return
            
        print("\n" + "="*50)
        print("基础分析结果摘要")
        print("="*50)
        
        # 显示基础分析
        if 'base_analysis' in results:
            base = results['base_analysis']
            print(f"\n📊 数据概览:")
            print(f"   - 数据点数量: {base.get('data_points', 'N/A')}")
            print(f"   - 分析维度: {base.get('dimensions', 'N/A')}")
            
        # 显示增强洞察
        if 'enhanced_insights' in results:
            insights = results['enhanced_insights']
            print(f"\n🔍 关键洞察 ({len(insights)} 项):")
            for i, insight in enumerate(insights[:3], 1):
                print(f"   {i}. {insight.get('title', 'N/A')} (置信度: {insight.get('confidence', 0):.2f})")
                print(f"      {insight.get('description', 'N/A')[:100]}...")
        
        # 显示报告路径
        if 'report_path' in results:
            print(f"\n📄 详细报告: {results['report_path']}")
            
        print("\n" + "="*50)
    
    def _display_comprehensive_results(self, results: Dict[str, Any]):
        """
        显示综合分析结果
        """
        if not results:
            logger.warning("没有分析结果可显示")
            return
            
        print("\n" + "="*60)
        print("综合分析结果详情")
        print("="*60)
        
        # 显示执行摘要
        if 'executive_summary' in results:
            print(f"\n📋 执行摘要:")
            print(f"   {results['executive_summary'][:200]}...")
        
        # 显示增强洞察
        if 'enhanced_insights' in results:
            insights = results['enhanced_insights']
            print(f"\n🔍 深度洞察 ({len(insights)} 项):")
            for insight in insights:
                print(f"   • {insight.get('title', 'N/A')} [{insight.get('category', 'N/A')}]")
                print(f"     置信度: {insight.get('confidence', 0):.2f}")
                print(f"     描述: {insight.get('description', 'N/A')[:150]}...")
                if insight.get('recommendations'):
                    print(f"     建议: {', '.join(insight['recommendations'][:2])}")
                print()
        
        # 显示知识库洞察
        if 'knowledge_insights' in results:
            kb_insights = results['knowledge_insights']
            print(f"\n📚 知识库洞察:")
            print(f"   - 相关文档: {kb_insights.get('relevant_docs', 0)} 个")
            print(f"   - 历史案例: {len(results.get('relevant_cases', []))} 个")
            print(f"   - 最佳实践: {len(results.get('best_practices', []))} 个")
        
        # 显示可视化
        if 'visualizations' in results:
            viz = results['visualizations']
            print(f"\n📈 生成的可视化:")
            for viz_type, path in viz.items():
                print(f"   - {viz_type}: {path}")
        
        # 显示报告路径
        if 'report_path' in results:
            print(f"\n📄 完整报告: {results['report_path']}")
            print(f"   建议使用浏览器打开查看完整的交互式报告")
            
        print("\n" + "="*60)
    
    async def run_demo(self):
        """
        运行完整演示
        """
        try:
            print("🚀 启动增强型LLM结果分析演示")
            print("=" * 50)
            
            # 初始化组件
            sample_data = await self.initialize_components()
            
            # 运行基础演示
            basic_results = await self.run_basic_analysis_demo()
            
            # 运行综合演示
            comprehensive_results = await self.run_comprehensive_demo()
            
            # 总结
            print("\n🎉 演示完成!")
            print("\n📊 演示总结:")
            print(f"   - 基础分析: {'✅ 成功' if basic_results else '❌ 失败'}")
            print(f"   - 综合分析: {'✅ 成功' if comprehensive_results else '❌ 失败'}")
            print(f"   - 输出目录: {self.output_dir}")
            
            return {
                "basic_results": basic_results,
                "comprehensive_results": comprehensive_results,
                "output_directory": str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"演示运行失败: {e}")
            raise


async def main():
    """
    主函数
    """
    try:
        demo = EnhancedAnalysisDemo()
        results = await demo.run_demo()
        
        print("\n✨ 增强型LLM结果分析演示成功完成!")
        print("\n🔗 相关链接:")
        print("   - 查看生成的报告文件")
        print("   - 检查输出目录中的可视化图表")
        print("   - 参考 ENHANCED_FEATURES.md 了解更多功能")
        
        return results
        
    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 演示失败: {e}")
        print("\n🔧 故障排除建议:")
        print("   1. 检查所有依赖是否正确安装")
        print("   2. 确认项目路径设置正确")
        print("   3. 查看日志文件获取详细错误信息")
        return None


if __name__ == "__main__":
    asyncio.run(main())