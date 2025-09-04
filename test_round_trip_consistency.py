#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
往返转换一致性测试

测试配置文件 -> 自然语言 -> 配置文件的往返转换一致性
验证信息是否丢失，连接关系是否正确保持

作者: CHS-SDK Team
创建时间: 2024
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime
import difflib

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.language_to_config_converter import LanguageToConfigConverter
from core_lib.config.unified_config_manager import ConfigType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RoundTripTester:
    """往返转换测试器"""
    
    def __init__(self):
        self.config_to_lang = ConfigToLanguageConverter()
        self.lang_to_config = LanguageToConfigConverter()
        self.test_results = []
        
    def test_round_trip_consistency(self, config_path: str, config_type: ConfigType = None) -> Dict[str, Any]:
        """测试单个配置文件的往返转换一致性"""
        logger.info(f"测试配置文件: {config_path}")
        
        try:
            # 步骤1: 配置文件 -> 自然语言
            logger.info("步骤1: 配置文件转换为自然语言")
            nl_description = self.config_to_lang.convert_config_to_language(config_path)
            
            # 步骤2: 自然语言 -> 配置文件
            logger.info("步骤2: 自然语言转换为配置文件")
            
            # 构建完整的自然语言描述
            full_description = f"""
{nl_description.summary}

{nl_description.modeling_description}

{nl_description.scenario_description}

{nl_description.query_description}

{nl_description.analysis_description}
"""
            
            # 确定配置类型
            if config_type is None:
                if 'unified_config' in str(config_path):
                    config_type = ConfigType.UNIFIED_SINGLE
                elif 'universal_config' in str(config_path):
                    config_type = ConfigType.UNIVERSAL_CONFIG
                else:
                    config_type = ConfigType.TRADITIONAL_MULTI
            
            # 生成新配置
            output_dir = Path("test_output") / "round_trip_test" / Path(config_path).stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            regenerated_config = self.lang_to_config.convert_language_to_config(
                full_description, config_type, output_dir
            )
            
            # 步骤3: 比较原始配置和重新生成的配置
            logger.info("步骤3: 比较配置一致性")
            consistency_result = self._compare_configs(config_path, regenerated_config, output_dir)
            
            # 保存自然语言描述
            nl_file = output_dir / "natural_language_description.md"
            with open(nl_file, 'w', encoding='utf-8') as f:
                f.write(f"# 配置文件自然语言描述\n\n")
                f.write(f"原始配置: {config_path}\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## 总结\n{nl_description.summary}\n\n")
                f.write(f"## 建模描述\n{nl_description.modeling_description}\n\n")
                f.write(f"## 情景描述\n{nl_description.scenario_description}\n\n")
                f.write(f"## 查询描述\n{nl_description.query_description}\n\n")
                f.write(f"## 分析描述\n{nl_description.analysis_description}\n\n")
            
            result = {
                'config_path': str(config_path),
                'config_type': config_type.value,
                'success': True,
                'natural_language_file': str(nl_file),
                'regenerated_config_dir': str(output_dir),
                'consistency': consistency_result,
                'technical_details': nl_description.technical_details
            }
            
            logger.info(f"测试完成: {config_path}")
            return result
            
        except Exception as e:
            logger.error(f"测试失败 {config_path}: {str(e)}")
            return {
                'config_path': str(config_path),
                'config_type': config_type.value if config_type else 'unknown',
                'success': False,
                'error': str(e),
                'consistency': {'overall_score': 0.0, 'issues': [str(e)]}
            }
    
    def _compare_configs(self, original_path: str, regenerated_config: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """比较原始配置和重新生成的配置"""
        
        # 加载原始配置
        original_config = self._load_original_config(original_path)
        
        # 保存比较结果
        comparison_file = output_dir / "config_comparison.json"
        
        # 比较各个部分
        comparison_result = {
            'overall_score': 0.0,
            'components_score': 0.0,
            'topology_score': 0.0,
            'simulation_score': 0.0,
            'agents_score': 0.0,
            'issues': [],
            'improvements': []
        }
        
        try:
            # 提取重新生成配置的各部分
            regen_components = regenerated_config.get('components.yml', regenerated_config.get('components', {}))
            regen_topology = regenerated_config.get('topology.yml', regenerated_config.get('topology', {}))
            regen_simulation = regenerated_config.get('config.yml', regenerated_config.get('simulation', {}))
            if 'simulation' in regen_simulation:
                regen_simulation = regen_simulation['simulation']
            regen_agents = regenerated_config.get('agents.yml', regenerated_config.get('agents', {}))
            
            # 比较组件
            comp_result = self._compare_components(
                original_config.get('components', {}),
                regen_components
            )
            comparison_result['components_score'] = comp_result['score']
            comparison_result['issues'].extend(comp_result['issues'])
            comparison_result['improvements'].extend(comp_result['improvements'])
            
            # 比较拓扑连接
            topo_result = self._compare_topology(
                original_config.get('topology', {}),
                regen_topology
            )
            comparison_result['topology_score'] = topo_result['score']
            comparison_result['issues'].extend(topo_result['issues'])
            comparison_result['improvements'].extend(topo_result['improvements'])
            
            # 比较仿真配置（处理不同的配置结构）
            orig_simulation = original_config.get('simulation', {})
            if not orig_simulation:
                # 尝试从config字段获取
                config_data = original_config.get('config', {})
                if isinstance(config_data, dict):
                    orig_simulation = config_data.get('simulation', {})
            if not orig_simulation:
                # 尝试从unified_config字段获取
                unified_data = original_config.get('unified_config', {})
                if isinstance(unified_data, dict):
                    orig_simulation = unified_data.get('simulation', {})
            if not orig_simulation:
                # 尝试从universal_config字段获取
                universal_data = original_config.get('universal_config', {})
                if isinstance(universal_data, dict):
                    orig_simulation = universal_data.get('simulation', {})
            
            sim_result = self._compare_simulation(
                orig_simulation,
                regen_simulation
            )
            comparison_result['simulation_score'] = sim_result['score']
            comparison_result['issues'].extend(sim_result['issues'])
            comparison_result['improvements'].extend(sim_result['improvements'])
            
            # 比较智能体
            agent_result = self._compare_agents(
                original_config.get('agents', {}),
                regen_agents
            )
            comparison_result['agents_score'] = agent_result['score']
            comparison_result['issues'].extend(agent_result['issues'])
            comparison_result['improvements'].extend(agent_result['improvements'])
            
            # 计算总体得分
            scores = [comparison_result['components_score'], comparison_result['topology_score'], 
                     comparison_result['simulation_score'], comparison_result['agents_score']]
            comparison_result['overall_score'] = sum(scores) / len(scores)
            
            # 保存详细比较结果
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'original_config': original_config,
                    'regenerated_config': regenerated_config,
                    'comparison_result': comparison_result
                }, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            comparison_result['issues'].append(f"配置比较失败: {str(e)}")
            comparison_result['overall_score'] = 0.0
        
        return comparison_result
    
    def _load_original_config(self, config_path: str) -> Dict[str, Any]:
        """加载原始配置文件"""
        config_path = Path(config_path)
        
        if config_path.is_file():
            # 单文件配置
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        elif config_path.is_dir():
            # 多文件配置
            config = {}
            for file_path in config_path.glob('*.yml'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                    config[file_path.stem] = file_config
            return config
        else:
            return {}
    
    def _compare_components(self, original: Dict[str, Any], regenerated: Dict[str, Any]) -> Dict[str, Any]:
        """比较组件配置"""
        result = {'score': 0.0, 'issues': [], 'improvements': []}
        
        try:
            orig_components = self._normalize_components(original)
            regen_components = self._normalize_components(regenerated)
            
            if not orig_components and not regen_components:
                result['score'] = 1.0
                return result
            
            if not orig_components:
                result['issues'].append("原始配置中没有组件定义")
                return result
            
            if not regen_components:
                result['issues'].append("重新生成的配置中没有组件定义")
                return result
            
            # 比较组件数量
            orig_count = len(orig_components)
            regen_count = len(regen_components)
            
            if orig_count != regen_count:
                result['issues'].append(f"组件数量不匹配: 原始{orig_count}个, 重新生成{regen_count}个")
            
            # 比较组件类型（考虑类型映射关系）
            orig_types = set(comp.get('type', comp.get('class', '')) for comp in orig_components.values())
            regen_types = set(comp.get('type', comp.get('class', '')) for comp in regen_components.values())
            
            # 标准化类型名称（处理等价类型）
            type_mapping = {
                'RiverChannel': 'Channel',
                'UnifiedCanal': 'Canal',
                'IntegralDelayCanal': 'Canal',
                'PumpStation': 'Pump',
                'ValveStation': 'Valve',
                'TurbineStation': 'ControlledSystem',
                'WaterTurbine': 'ControlledSystem'
            }
            
            def normalize_type(type_name):
                return type_mapping.get(type_name, type_name)
            
            normalized_orig_types = set(normalize_type(t) for t in orig_types)
            normalized_regen_types = set(normalize_type(t) for t in regen_types)
            
            missing_types = normalized_orig_types - normalized_regen_types
            extra_types = normalized_regen_types - normalized_orig_types
            
            if missing_types:
                result['issues'].append(f"缺失的组件类型: {missing_types}")
            if extra_types:
                result['improvements'].append(f"新增的组件类型: {extra_types}")
            
            # 计算得分
            type_score = len(normalized_orig_types & normalized_regen_types) / max(len(normalized_orig_types), 1)
            count_score = 1.0 - abs(orig_count - regen_count) / max(orig_count, regen_count, 1)
            result['score'] = (type_score + count_score) / 2
            
        except Exception as e:
            result['issues'].append(f"组件比较失败: {str(e)}")
        
        return result
    
    def _compare_topology(self, original: Dict[str, Any], regenerated: Dict[str, Any]) -> Dict[str, Any]:
        """比较拓扑连接"""
        result = {'score': 0.0, 'issues': [], 'improvements': []}
        
        try:
            orig_connections = self._normalize_connections(original)
            regen_connections = self._normalize_connections(regenerated)
            
            if not orig_connections and not regen_connections:
                result['score'] = 1.0
                return result
            
            if not orig_connections:
                result['issues'].append("原始配置中没有连接定义")
                if regen_connections:
                    result['improvements'].append(f"重新生成的配置中添加了{len(regen_connections)}个连接")
                return result
            
            if not regen_connections:
                result['issues'].append("重新生成的配置中没有连接定义")
                return result
            
            # 比较连接数量
            orig_count = len(orig_connections)
            regen_count = len(regen_connections)
            
            if orig_count != regen_count:
                result['issues'].append(f"连接数量不匹配: 原始{orig_count}个, 重新生成{regen_count}个")
            
            # 比较具体连接
            orig_pairs = set((conn.get('upstream', conn.get('from', '')), 
                            conn.get('downstream', conn.get('to', ''))) for conn in orig_connections)
            regen_pairs = set((conn.get('upstream', conn.get('from', '')), 
                             conn.get('downstream', conn.get('to', ''))) for conn in regen_connections)
            
            missing_connections = orig_pairs - regen_pairs
            extra_connections = regen_pairs - orig_pairs
            
            if missing_connections:
                result['issues'].append(f"缺失的连接: {missing_connections}")
            if extra_connections:
                result['improvements'].append(f"新增的连接: {extra_connections}")
            
            # 计算得分
            if orig_pairs:
                connection_score = len(orig_pairs & regen_pairs) / len(orig_pairs)
            else:
                connection_score = 1.0 if not regen_pairs else 0.5
            
            count_score = 1.0 - abs(orig_count - regen_count) / max(orig_count, regen_count, 1)
            result['score'] = (connection_score + count_score) / 2
            
        except Exception as e:
            result['issues'].append(f"拓扑比较失败: {str(e)}")
        
        return result
    
    def _compare_simulation(self, original: Dict[str, Any], regenerated: Dict[str, Any]) -> Dict[str, Any]:
        """比较仿真配置"""
        result = {'score': 0.0, 'issues': [], 'improvements': []}
        
        try:
            # 比较关键参数（处理参数名映射）
            param_mappings = [
                (['duration'], ['duration']),
                (['dt', 'time_step'], ['dt', 'time_step']),
                (['name'], ['name'])
            ]
            
            score_sum = 0
            valid_params = 0
            
            for orig_names, regen_names in param_mappings:
                # 从原始配置中获取参数值
                orig_val = None
                for name in orig_names:
                    if name in original:
                        orig_val = original[name]
                        break
                
                # 从重新生成配置中获取参数值
                regen_val = None
                for name in regen_names:
                    if name in regenerated:
                        regen_val = regenerated[name]
                        break
                
                if orig_val is not None:
                    valid_params += 1
                    if orig_val == regen_val:
                        score_sum += 1.0
                    elif isinstance(orig_val, (int, float)) and isinstance(regen_val, (int, float)):
                        # 数值参数允许一定误差
                        error_rate = abs(orig_val - regen_val) / max(abs(orig_val), 1)
                        if error_rate < 0.1:  # 10%误差内
                            score_sum += 0.8
                        elif error_rate < 0.5:  # 50%误差内
                            score_sum += 0.5
                        result['issues'].append(f"仿真参数不匹配: 原始{orig_val}, 重新生成{regen_val}")
                    else:
                        result['issues'].append(f"仿真参数不匹配: 原始{orig_val}, 重新生成{regen_val}")
            
            result['score'] = score_sum / max(valid_params, 1)
            
        except Exception as e:
            result['issues'].append(f"仿真配置比较失败: {str(e)}")
        
        return result
    
    def _compare_agents(self, original: Dict[str, Any], regenerated: Dict[str, Any]) -> Dict[str, Any]:
        """比较智能体配置"""
        result = {'score': 0.0, 'issues': [], 'improvements': []}
        
        try:
            orig_agents = self._normalize_agents(original)
            regen_agents = self._normalize_agents(regenerated)
            
            if not orig_agents and not regen_agents:
                result['score'] = 1.0
                return result
            
            orig_count = len(orig_agents)
            regen_count = len(regen_agents)
            
            if orig_count != regen_count:
                result['issues'].append(f"智能体数量不匹配: 原始{orig_count}个, 重新生成{regen_count}个")
            
            # 比较智能体类型
            if orig_agents:
                orig_types = set(agent.get('type', agent.get('class', '')) for agent in orig_agents.values())
                regen_types = set(agent.get('type', agent.get('class', '')) for agent in regen_agents.values())
                
                if orig_types:
                    type_score = len(orig_types & regen_types) / len(orig_types)
                else:
                    type_score = 1.0 if not regen_types else 0.5
            else:
                type_score = 1.0 if not regen_agents else 0.5
            
            count_score = 1.0 - abs(orig_count - regen_count) / max(orig_count, regen_count, 1)
            result['score'] = (type_score + count_score) / 2
            
        except Exception as e:
            result['issues'].append(f"智能体比较失败: {str(e)}")
        
        return result
    
    def _normalize_components(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """标准化组件格式"""
        if not components:
            return {}
        
        # 处理嵌套的components字段
        if 'components' in components:
            comp_data = components['components']
            if isinstance(comp_data, dict):
                return comp_data
            elif isinstance(comp_data, list):
                # 将列表转换为字典格式
                result = {}
                for i, comp in enumerate(comp_data):
                    if isinstance(comp, dict):
                        comp_name = comp.get('name', comp.get('id', f'component_{i}'))
                        result[comp_name] = comp
                return result
        
        # 如果components本身就是列表
        if isinstance(components, list):
            result = {}
            for i, comp in enumerate(components):
                if isinstance(comp, dict):
                    comp_name = comp.get('name', comp.get('id', f'component_{i}'))
                    result[comp_name] = comp
            return result
        
        return components
    
    def _normalize_connections(self, topology: Dict[str, Any]) -> List[Dict[str, Any]]:
        """标准化连接格式"""
        if not topology:
            return []
        
        if 'connections' in topology:
            return topology['connections']
        if 'topology' in topology:
            return topology['topology']
        return []
    
    def _normalize_agents(self, agents: Dict[str, Any]) -> Dict[str, Any]:
        """标准化智能体格式"""
        if not agents:
            return {}
        
        # 处理嵌套的agents字段
        if 'agents' in agents:
            agent_data = agents['agents']
            if isinstance(agent_data, dict):
                return agent_data
            elif isinstance(agent_data, list):
                # 将列表转换为字典格式
                result = {}
                for i, agent in enumerate(agent_data):
                    if isinstance(agent, dict):
                        agent_name = agent.get('name', agent.get('id', f'agent_{i}'))
                        result[agent_name] = agent
                return result
        
        # 如果agents本身就是列表
        if isinstance(agents, list):
            result = {}
            for i, agent in enumerate(agents):
                if isinstance(agent, dict):
                    agent_name = agent.get('name', agent.get('id', f'agent_{i}'))
                    result[agent_name] = agent
            return result
        
        return agents
    
    def test_multiple_configs(self, config_paths: List[str]) -> Dict[str, Any]:
        """测试多个配置文件的往返转换"""
        logger.info(f"开始测试{len(config_paths)}个配置文件的往返转换一致性")
        
        all_results = []
        summary = {
            'total_tests': len(config_paths),
            'successful_tests': 0,
            'failed_tests': 0,
            'average_consistency_score': 0.0,
            'best_score': 0.0,
            'worst_score': 1.0,
            'common_issues': [],
            'test_results': []
        }
        
        for config_path in config_paths:
            result = self.test_round_trip_consistency(config_path)
            all_results.append(result)
            
            if result['success']:
                summary['successful_tests'] += 1
                score = result['consistency']['overall_score']
                summary['best_score'] = max(summary['best_score'], score)
                summary['worst_score'] = min(summary['worst_score'], score)
            else:
                summary['failed_tests'] += 1
        
        # 计算平均得分
        successful_results = [r for r in all_results if r['success']]
        if successful_results:
            scores = [r['consistency']['overall_score'] for r in successful_results]
            summary['average_consistency_score'] = sum(scores) / len(scores)
        
        # 收集常见问题
        all_issues = []
        for result in successful_results:
            all_issues.extend(result['consistency']['issues'])
        
        # 统计问题频率
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # 获取最常见的问题
        summary['common_issues'] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        summary['test_results'] = all_results
        
        # 保存总结报告
        report_file = Path("test_output") / "round_trip_test" / "summary_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"往返转换测试完成，成功{summary['successful_tests']}个，失败{summary['failed_tests']}个")
        logger.info(f"平均一致性得分: {summary['average_consistency_score']:.2f}")
        
        return summary

def find_example_configs() -> List[str]:
    """查找示例配置文件"""
    config_paths = []
    
    # 查找examples目录下的配置文件
    examples_dir = Path("examples")
    if examples_dir.exists():
        # 查找统一配置文件
        for unified_config in examples_dir.rglob("unified_config.yml"):
            config_paths.append(str(unified_config))
        
        # 查找通用配置文件
        for universal_config in examples_dir.rglob("universal_config.yml"):
            config_paths.append(str(universal_config))
        
        # 查找传统多配置文件目录
        for config_dir in examples_dir.rglob("*"):
            if config_dir.is_dir() and (config_dir / "config.yml").exists():
                config_paths.append(str(config_dir))
    
    # 查找demo_output目录下的配置文件
    demo_dir = Path("demo_output")
    if demo_dir.exists():
        for config_file in demo_dir.rglob("*.yml"):
            if config_file.name in ["unified_config.yml", "universal_config.yml"]:
                config_paths.append(str(config_file))
    
    # 查找test_output目录下的配置文件
    test_dir = Path("test_output")
    if test_dir.exists():
        for config_file in test_dir.rglob("*.yml"):
            if config_file.name in ["unified_config.yml", "universal_config.yml"]:
                config_paths.append(str(config_file))
    
    return list(set(config_paths))  # 去重

def main():
    """主函数"""
    print("=== CHS-SDK 往返转换一致性测试 ===")
    
    # 查找所有示例配置文件
    config_paths = find_example_configs()
    
    if not config_paths:
        print("未找到任何配置文件进行测试")
        return
    
    print(f"找到 {len(config_paths)} 个配置文件:")
    for i, path in enumerate(config_paths, 1):
        print(f"  {i}. {path}")
    
    # 创建测试器
    tester = RoundTripTester()
    
    # 执行测试
    print("\n开始执行往返转换测试...")
    summary = tester.test_multiple_configs(config_paths)
    
    # 打印结果
    print("\n=== 测试结果总结 ===")
    print(f"总测试数: {summary['total_tests']}")
    print(f"成功测试: {summary['successful_tests']}")
    print(f"失败测试: {summary['failed_tests']}")
    print(f"平均一致性得分: {summary['average_consistency_score']:.2f}")
    print(f"最高得分: {summary['best_score']:.2f}")
    print(f"最低得分: {summary['worst_score']:.2f}")
    
    if summary['common_issues']:
        print("\n常见问题:")
        for issue, count in summary['common_issues']:
            print(f"  - {issue} (出现{count}次)")
    
    print(f"\n详细报告已保存到: test_output/round_trip_test/summary_report.json")
    
    # 如果测试成功，生成所有示例的自然语言描述合并报告
    if summary['successful_tests'] > 0:
        print("\n生成所有示例的自然语言描述合并报告...")
        generate_combined_nl_report(summary['test_results'])

def generate_combined_nl_report(test_results: List[Dict[str, Any]]):
    """生成所有示例的自然语言描述合并报告"""
    
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "all_examples_natural_language.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# CHS-SDK 所有示例配置文件的自然语言描述\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"本报告包含了 {len([r for r in test_results if r['success']])} 个成功转换的配置文件的自然语言描述。\n\n")
        
        f.write("## 目录\n\n")
        
        # 生成目录
        successful_results = [r for r in test_results if r['success']]
        for i, result in enumerate(successful_results, 1):
            config_name = Path(result['config_path']).stem
            f.write(f"{i}. [{config_name}](#{config_name.lower().replace('_', '-')})\n")
        
        f.write("\n---\n\n")
        
        # 生成每个配置的详细描述
        for i, result in enumerate(successful_results, 1):
            config_name = Path(result['config_path']).stem
            config_path = result['config_path']
            
            f.write(f"## {i}. {config_name}\n\n")
            f.write(f"**配置路径:** `{config_path}`\n\n")
            f.write(f"**配置类型:** {result['config_type']}\n\n")
            f.write(f"**一致性得分:** {result['consistency']['overall_score']:.2f}\n\n")
            
            # 读取自然语言描述文件
            nl_file = Path(result['natural_language_file'])
            if nl_file.exists():
                with open(nl_file, 'r', encoding='utf-8') as nl_f:
                    nl_content = nl_f.read()
                    # 移除文件头部信息，只保留主要内容
                    lines = nl_content.split('\n')
                    content_start = 0
                    for j, line in enumerate(lines):
                        if line.startswith('## 总结') or line.startswith('## 建模描述'):
                            content_start = j
                            break
                    
                    if content_start > 0:
                        f.write('\n'.join(lines[content_start:]))
                    else:
                        f.write(nl_content)
            
            f.write("\n\n---\n\n")
        
        # 添加统计信息
        f.write("## 统计信息\n\n")
        
        # 统计配置类型
        config_types = {}
        for result in successful_results:
            config_type = result['config_type']
            config_types[config_type] = config_types.get(config_type, 0) + 1
        
        f.write("### 配置类型分布\n\n")
        for config_type, count in config_types.items():
            f.write(f"- {config_type}: {count} 个\n")
        
        # 统计一致性得分
        scores = [r['consistency']['overall_score'] for r in successful_results]
        f.write(f"\n### 一致性得分统计\n\n")
        f.write(f"- 平均得分: {sum(scores)/len(scores):.2f}\n")
        f.write(f"- 最高得分: {max(scores):.2f}\n")
        f.write(f"- 最低得分: {min(scores):.2f}\n")
        
        # 统计组件类型
        all_components = []
        for result in successful_results:
            tech_details = result.get('technical_details', {})
            if 'components_count' in tech_details:
                all_components.append(tech_details['components_count'])
        
        if all_components:
            f.write(f"\n### 组件统计\n\n")
            f.write(f"- 总配置数: {len(all_components)}\n")
            f.write(f"- 平均组件数: {sum(all_components)/len(all_components):.1f}\n")
            f.write(f"- 最多组件数: {max(all_components)}\n")
            f.write(f"- 最少组件数: {min(all_components)}\n")
    
    print(f"合并报告已保存到: {report_file}")

if __name__ == '__main__':
    main()