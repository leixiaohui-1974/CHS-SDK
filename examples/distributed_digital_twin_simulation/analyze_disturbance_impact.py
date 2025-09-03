#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扰动影响分析脚本
分析不同扰动场景对系统性能的影响
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DisturbanceImpactAnalyzer:
    """扰动影响分析器"""
    
    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        self.baseline_data = None
        self.disturbance_data = {}
        
    def load_results(self):
        """加载仿真结果"""
        logger.info(f"从目录加载结果: {self.results_dir}")
        
        # 加载基准数据
        baseline_file = os.path.join(self.results_dir, "baseline_results.json")
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r', encoding='utf-8') as f:
                self.baseline_data = json.load(f)
            logger.info("基准数据加载完成")
        
        # 加载扰动场景数据
        for filename in os.listdir(self.results_dir):
            if filename.endswith('_results.json') and filename != 'baseline_results.json':
                scenario_name = filename.replace('_results.json', '')
                filepath = os.path.join(self.results_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.disturbance_data[scenario_name] = json.load(f)
                
                logger.info(f"加载扰动场景: {scenario_name}")
    
    def calculate_performance_degradation(self) -> Dict[str, Dict[str, float]]:
        """计算性能退化指标"""
        if not self.baseline_data:
            logger.error("未找到基准数据")
            return {}
        
        degradation_results = {}
        
        for scenario_name, scenario_data in self.disturbance_data.items():
            degradation = {}
            
            # 水位稳定性分析
            if 'water_level_stats' in scenario_data and 'water_level_stats' in self.baseline_data:
                baseline_std = self.baseline_data['water_level_stats']['std']
                scenario_std = scenario_data['water_level_stats']['std']
                degradation['water_level_stability_degradation'] = (scenario_std - baseline_std) / baseline_std * 100
                
                baseline_range = self.baseline_data['water_level_stats']['max'] - self.baseline_data['water_level_stats']['min']
                scenario_range = scenario_data['water_level_stats']['max'] - scenario_data['water_level_stats']['min']
                degradation['water_level_range_increase'] = (scenario_range - baseline_range) / baseline_range * 100
            
            # 流量稳定性分析
            if 'flow_rate_stats' in scenario_data and 'flow_rate_stats' in self.baseline_data:
                baseline_flow_std = self.baseline_data['flow_rate_stats']['std']
                scenario_flow_std = scenario_data['flow_rate_stats']['std']
                if baseline_flow_std > 0:
                    degradation['flow_rate_stability_degradation'] = (scenario_flow_std - baseline_flow_std) / baseline_flow_std * 100
                else:
                    degradation['flow_rate_stability_degradation'] = 0
            
            # 控制精度分析
            if 'gate_opening_stats' in scenario_data and 'gate_opening_stats' in self.baseline_data:
                baseline_gate_std = self.baseline_data['gate_opening_stats']['std']
                scenario_gate_std = scenario_data['gate_opening_stats']['std']
                degradation['control_precision_degradation'] = (scenario_gate_std - baseline_gate_std) / baseline_gate_std * 100
            
            # 系统稳定性分析
            if 'system_stability' in scenario_data and 'system_stability' in self.baseline_data:
                baseline_variance = self.baseline_data['system_stability']['water_level_variance']
                scenario_variance = scenario_data['system_stability']['water_level_variance']
                degradation['system_variance_increase'] = (scenario_variance - baseline_variance) / baseline_variance * 100
            
            degradation_results[scenario_name] = degradation
        
        return degradation_results
    
    def classify_disturbance_severity(self, degradation_results: Dict[str, Dict[str, float]]) -> Dict[str, str]:
        """分类扰动严重程度"""
        severity_classification = {}
        
        for scenario_name, degradation in degradation_results.items():
            # 计算综合影响分数
            impact_score = 0
            metric_count = 0
            
            for metric, value in degradation.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    impact_score += abs(value)
                    metric_count += 1
            
            if metric_count > 0:
                avg_impact = impact_score / metric_count
            else:
                avg_impact = 0
            
            # 分类严重程度
            if avg_impact < 5:
                severity = "轻微"
            elif avg_impact < 15:
                severity = "中等"
            elif avg_impact < 30:
                severity = "严重"
            else:
                severity = "极严重"
            
            severity_classification[scenario_name] = severity
        
        return severity_classification
    
    def generate_visualization(self, degradation_results: Dict[str, Dict[str, float]], output_dir: str):
        """生成可视化图表"""
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文显示
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 水位稳定性对比图
        scenarios = list(degradation_results.keys())
        water_level_degradation = [degradation_results[s].get('water_level_stability_degradation', 0) for s in scenarios]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(scenarios)), water_level_degradation, color=['red' if x > 10 else 'orange' if x > 5 else 'green' for x in water_level_degradation])
        plt.xlabel('扰动场景')
        plt.ylabel('水位稳定性退化 (%)')
        plt.title('各扰动场景水位稳定性影响对比')
        plt.xticks(range(len(scenarios)), scenarios, rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'water_level_stability_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 综合影响雷达图
        metrics = ['water_level_stability_degradation', 'flow_rate_stability_degradation', 
                  'control_precision_degradation', 'system_variance_increase']
        metric_labels = ['水位稳定性', '流量稳定性', '控制精度', '系统方差']
        
        # 选择几个代表性场景
        representative_scenarios = scenarios[:5] if len(scenarios) > 5 else scenarios
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        for scenario in representative_scenarios:
            values = [abs(degradation_results[scenario].get(metric, 0)) for metric in metrics]
            values += values[:1]  # 闭合图形
            
            ax.plot(angles, values, 'o-', linewidth=2, label=scenario)
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, max([max([abs(degradation_results[s].get(m, 0)) for m in metrics]) for s in representative_scenarios]) * 1.1)
        ax.set_title('扰动场景综合影响雷达图', size=16, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'comprehensive_impact_radar.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"可视化图表已保存到: {output_dir}")
    
    def generate_analysis_report(self, degradation_results: Dict[str, Dict[str, float]], 
                               severity_classification: Dict[str, str], output_file: str):
        """生成分析报告"""
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "baseline_scenario": self.baseline_data['scenario_name'] if self.baseline_data else None,
            "analyzed_scenarios": list(self.disturbance_data.keys()),
            "performance_degradation": degradation_results,
            "severity_classification": severity_classification,
            "summary": {
                "total_scenarios": len(self.disturbance_data),
                "severe_scenarios": [s for s, sev in severity_classification.items() if sev in ['严重', '极严重']],
                "moderate_scenarios": [s for s, sev in severity_classification.items() if sev == '中等'],
                "mild_scenarios": [s for s, sev in severity_classification.items() if sev == '轻微']
            },
            "recommendations": self.generate_recommendations(degradation_results, severity_classification)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析报告已保存: {output_file}")
        return report
    
    def generate_recommendations(self, degradation_results: Dict[str, Dict[str, float]], 
                               severity_classification: Dict[str, str]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 针对严重扰动的建议
        severe_scenarios = [s for s, sev in severity_classification.items() if sev in ['严重', '极严重']]
        
        if severe_scenarios:
            recommendations.append(f"发现 {len(severe_scenarios)} 个严重扰动场景: {', '.join(severe_scenarios)}")
            recommendations.append("建议优先处理这些场景，增强系统鲁棒性")
        
        # 针对水位稳定性问题的建议
        water_level_issues = [s for s, deg in degradation_results.items() 
                             if deg.get('water_level_stability_degradation', 0) > 15]
        if water_level_issues:
            recommendations.append(f"水位稳定性问题场景: {', '.join(water_level_issues)}")
            recommendations.append("建议优化水位控制算法，增加预测控制策略")
        
        # 针对控制精度问题的建议
        control_issues = [s for s, deg in degradation_results.items() 
                         if deg.get('control_precision_degradation', 0) > 20]
        if control_issues:
            recommendations.append(f"控制精度问题场景: {', '.join(control_issues)}")
            recommendations.append("建议改进执行器控制策略，增加故障检测与容错机制")
        
        # 针对组合扰动的建议
        combined_scenarios = [s for s in degradation_results.keys() if '_' in s and len(s.split('_')) > 2]
        if combined_scenarios:
            recommendations.append(f"组合扰动场景: {', '.join(combined_scenarios)}")
            recommendations.append("建议设计多层次防护策略，应对复合扰动")
        
        if not recommendations:
            recommendations.append("系统整体表现良好，建议继续监控关键性能指标")
        
        return recommendations

def main():
    """主函数"""
    # 获取最新的结果目录
    base_dir = "disturbance_scenarios/analysis_results"
    
    # 查找最新的会话目录
    session_dirs = [d for d in os.listdir(base_dir) if d.startswith('session_')]
    if not session_dirs:
        logger.error("未找到仿真结果目录")
        return
    
    latest_session = sorted(session_dirs)[-1]
    results_dir = os.path.join(base_dir, latest_session)
    
    logger.info(f"分析目录: {results_dir}")
    
    # 创建分析器
    analyzer = DisturbanceImpactAnalyzer(results_dir)
    
    # 加载结果
    analyzer.load_results()
    
    # 计算性能退化
    degradation_results = analyzer.calculate_performance_degradation()
    
    # 分类严重程度
    severity_classification = analyzer.classify_disturbance_severity(degradation_results)
    
    # 生成可视化
    visualization_dir = os.path.join(results_dir, "visualizations")
    analyzer.generate_visualization(degradation_results, visualization_dir)
    
    # 生成分析报告
    report_file = os.path.join(results_dir, "impact_analysis_report.json")
    report = analyzer.generate_analysis_report(degradation_results, severity_classification, report_file)
    
    # 打印摘要
    logger.info("=== 扰动影响分析摘要 ===")
    logger.info(f"分析场景数: {report['summary']['total_scenarios']}")
    logger.info(f"严重场景: {len(report['summary']['severe_scenarios'])}")
    logger.info(f"中等场景: {len(report['summary']['moderate_scenarios'])}")
    logger.info(f"轻微场景: {len(report['summary']['mild_scenarios'])}")
    
    logger.info("\n=== 优化建议 ===")
    for i, rec in enumerate(report['recommendations'], 1):
        logger.info(f"{i}. {rec}")

if __name__ == "__main__":
    main()