#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版双向转换精度测试
全面覆盖配置文件中的情景设置、调试、日志等内容
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.config.unified_config_manager import UnifiedConfigManager
from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.enhanced_language_to_config_converter import EnhancedLanguageToConfigConverter

@dataclass
class EnhancedConversionTestResult:
    """增强版转换测试结果"""
    config_path: str
    config_type: str
    original_to_language_success: bool
    language_to_config_success: bool
    roundtrip_success: bool
    original_to_language_time: float
    language_to_config_time: float
    similarity_score: float
    detailed_similarity: Dict[str, float]  # 详细相似度分析
    strategy_used: str
    confidence_score: float
    coverage_analysis: Dict[str, bool]  # 覆盖度分析
    errors: List[str]
    warnings: List[str]

class EnhancedBidirectionalConversionTester:
    """增强版双向转换测试器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.config_manager = UnifiedConfigManager()
        self.config_to_lang_converter = ConfigToLanguageConverter()
        self.lang_to_config_converter = EnhancedLanguageToConfigConverter()
        self.test_strategies = ['rule', 'llm', 'hybrid']
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('EnhancedBidirectionalConversionTester')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def find_all_config_files(self, examples_dir: str = "examples") -> List[Tuple[str, str]]:
        """查找所有配置文件"""
        config_files = []
        examples_path = Path(examples_dir)
        
        if not examples_path.exists():
            self.logger.error(f"示例目录不存在: {examples_dir}")
            return []
        
        for root, dirs, files in os.walk(examples_path):
            root_path = Path(root)
            
            # 检查是否包含配置文件
            has_config = any(
                f.endswith(('.yml', '.yaml', '.json')) and 
                f in ['config.yml', 'config.yaml', 'simulation.yml', 'simulation.yaml', 'config.json']
                for f in files
            )
            
            if has_config:
                try:
                    config_type = self.config_manager.detect_config_type(str(root_path))
                    config_files.append((str(root_path), config_type))
                except Exception as e:
                    self.logger.warning(f"无法检测配置类型: {root_path}, 错误: {e}")
        
        self.logger.info(f"找到 {len(config_files)} 个配置文件")
        return config_files
    
    def test_config_to_language(self, config_path: str) -> Tuple[bool, str, float, List[str]]:
        """测试配置文件到自然语言的转换"""
        errors = []
        start_time = time.time()
        
        try:
            # 转换为自然语言
            description_obj = self.config_to_lang_converter.convert_config_to_language(config_path)
            
            # 提取完整描述
            description = f"{description_obj.modeling_description}\n\n{description_obj.scenario_description}\n\n{description_obj.query_description}\n\n{description_obj.analysis_description}"
            
            conversion_time = time.time() - start_time
            
            if description and len(description.strip()) > 50:
                return True, description, conversion_time, errors
            else:
                errors.append("生成的描述过短或为空")
                return False, "", conversion_time, errors
                
        except Exception as e:
            errors.append(f"配置到语言转换失败: {str(e)}")
            self.logger.error(f"配置到语言转换失败: {e}")
            return False, "", time.time() - start_time, errors
    
    def test_language_to_config(self, description: str, strategy: str) -> Tuple[bool, Dict[str, Any], float, float, List[str]]:
        """测试自然语言到配置文件的转换"""
        errors = []
        start_time = time.time()
        
        try:
            result = self.lang_to_config_converter.convert_language_to_config(
                description, strategy=strategy
            )
            
            conversion_time = time.time() - start_time
            
            if result.config_data and result.confidence_score > 0.1:
                return True, result.config_data, conversion_time, result.confidence_score, result.validation_errors
            else:
                errors.extend(result.validation_errors)
                errors.append(f"转换失败或置信度过低: {result.confidence_score}")
                return False, {}, conversion_time, result.confidence_score, errors
                
        except Exception as e:
            errors.append(f"语言到配置转换失败: {str(e)}")
            self.logger.error(f"语言到配置转换失败: {e}")
            return False, {}, time.time() - start_time, 0.0, errors
    
    def calculate_enhanced_similarity(self, original_config: Dict[str, Any], generated_config: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """计算增强版配置文件相似度
        
        Returns:
            Tuple[float, Dict[str, float]]: 总相似度和详细相似度分析
        """
        detailed_similarity = {
            'components': 0.0,
            'topology': 0.0,
            'simulation': 0.0,
            'scenarios': 0.0,
            'debug': 0.0,
            'logging': 0.0,
            'agents': 0.0,
            'controllers': 0.0,
            'disturbances': 0.0,
            'analysis': 0.0
        }
        
        try:
            # 1. 组件相似度 (权重: 25%)
            detailed_similarity['components'] = self._calculate_components_similarity(
                original_config, generated_config
            )
            
            # 2. 拓扑相似度 (权重: 20%)
            detailed_similarity['topology'] = self._calculate_topology_similarity(
                original_config, generated_config
            )
            
            # 3. 仿真配置相似度 (权重: 15%)
            detailed_similarity['simulation'] = self._calculate_simulation_similarity(
                original_config, generated_config
            )
            
            # 4. 情景设置相似度 (权重: 10%)
            detailed_similarity['scenarios'] = self._calculate_scenarios_similarity(
                original_config, generated_config
            )
            
            # 5. 调试配置相似度 (权重: 5%)
            detailed_similarity['debug'] = self._calculate_debug_similarity(
                original_config, generated_config
            )
            
            # 6. 日志配置相似度 (权重: 5%)
            detailed_similarity['logging'] = self._calculate_logging_similarity(
                original_config, generated_config
            )
            
            # 7. 智能体配置相似度 (权重: 10%)
            detailed_similarity['agents'] = self._calculate_agents_similarity(
                original_config, generated_config
            )
            
            # 8. 控制器配置相似度 (权重: 5%)
            detailed_similarity['controllers'] = self._calculate_controllers_similarity(
                original_config, generated_config
            )
            
            # 9. 扰动配置相似度 (权重: 3%)
            detailed_similarity['disturbances'] = self._calculate_disturbances_similarity(
                original_config, generated_config
            )
            
            # 10. 分析配置相似度 (权重: 2%)
            detailed_similarity['analysis'] = self._calculate_analysis_similarity(
                original_config, generated_config
            )
            
            # 计算加权总相似度
            weights = {
                'components': 0.25,
                'topology': 0.20,
                'simulation': 0.15,
                'scenarios': 0.10,
                'agents': 0.10,
                'debug': 0.05,
                'logging': 0.05,
                'controllers': 0.05,
                'disturbances': 0.03,
                'analysis': 0.02
            }
            
            total_similarity = sum(
                detailed_similarity[key] * weights[key] 
                for key in weights.keys()
            )
            
            return total_similarity, detailed_similarity
            
        except Exception as e:
            self.logger.error(f"增强相似度计算失败: {e}")
            return 0.0, detailed_similarity
    
    def _calculate_components_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算组件相似度"""
        try:
            orig_components = self._extract_components(orig)
            gen_components = self._extract_components(gen)
            
            if not orig_components and not gen_components:
                return 1.0
            if not orig_components or not gen_components:
                return 0.0
            
            # 比较组件数量
            count_similarity = min(len(gen_components), len(orig_components)) / max(len(orig_components), 1)
            
            # 比较组件类型
            orig_types = set(comp.get('type', '') for comp in orig_components if isinstance(comp, dict))
            gen_types = set(comp.get('type', '') for comp in gen_components if isinstance(comp, dict))
            
            type_similarity = len(orig_types & gen_types) / max(len(orig_types), 1) if orig_types else 0.0
            
            return (count_similarity * 0.6 + type_similarity * 0.4)
            
        except Exception:
            return 0.0
    
    def _calculate_topology_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算拓扑相似度"""
        try:
            orig_topology = self._extract_topology(orig)
            gen_topology = self._extract_topology(gen)
            
            if not orig_topology and not gen_topology:
                return 1.0
            if not orig_topology or not gen_topology:
                return 0.0
            
            return min(len(gen_topology), len(orig_topology)) / max(len(orig_topology), 1)
            
        except Exception:
            return 0.0
    
    def _calculate_simulation_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算仿真配置相似度"""
        try:
            orig_sim = orig.get('simulation', {})
            gen_sim = gen.get('simulation', {})
            
            if not orig_sim and not gen_sim:
                return 1.0
            if not orig_sim or not gen_sim:
                return 0.0
            
            # 检查关键仿真参数
            key_params = ['duration', 'time_step', 'start_time', 'end_time', 'solver']
            matches = sum(1 for param in key_params if 
                         orig_sim.get(param) == gen_sim.get(param) and 
                         orig_sim.get(param) is not None)
            
            return matches / len(key_params)
            
        except Exception:
            return 0.0
    
    def _calculate_scenarios_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算情景设置相似度"""
        try:
            orig_scenarios = orig.get('scenarios', orig.get('scenario', {}))
            gen_scenarios = gen.get('scenarios', gen.get('scenario', {}))
            
            if not orig_scenarios and not gen_scenarios:
                return 1.0
            if not orig_scenarios or not gen_scenarios:
                return 0.0
            
            # 比较情景类型和参数
            if isinstance(orig_scenarios, dict) and isinstance(gen_scenarios, dict):
                common_keys = set(orig_scenarios.keys()) & set(gen_scenarios.keys())
                total_keys = set(orig_scenarios.keys()) | set(gen_scenarios.keys())
                return len(common_keys) / max(len(total_keys), 1)
            
            return 0.5  # 部分匹配
            
        except Exception:
            return 0.0
    
    def _calculate_debug_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算调试配置相似度"""
        try:
            orig_debug = orig.get('debug', orig.get('debugging', {}))
            gen_debug = gen.get('debug', gen.get('debugging', {}))
            
            if not orig_debug and not gen_debug:
                return 1.0
            if not orig_debug or not gen_debug:
                return 0.0
            
            # 检查调试选项
            debug_options = ['enabled', 'level', 'output_file', 'console_output', 'detailed_logs']
            matches = sum(1 for option in debug_options if 
                         orig_debug.get(option) == gen_debug.get(option))
            
            return matches / len(debug_options)
            
        except Exception:
            return 0.0
    
    def _calculate_logging_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算日志配置相似度"""
        try:
            orig_logging = orig.get('logging', orig.get('log', {}))
            gen_logging = gen.get('logging', gen.get('log', {}))
            
            if not orig_logging and not gen_logging:
                return 1.0
            if not orig_logging or not gen_logging:
                return 0.0
            
            # 检查日志选项
            log_options = ['level', 'file', 'format', 'rotation', 'max_size']
            matches = sum(1 for option in log_options if 
                         orig_logging.get(option) == gen_logging.get(option))
            
            return matches / len(log_options)
            
        except Exception:
            return 0.0
    
    def _calculate_agents_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算智能体配置相似度"""
        try:
            orig_agents = orig.get('agents', orig.get('agent_config', []))
            gen_agents = gen.get('agents', gen.get('agent_config', []))
            
            if not orig_agents and not gen_agents:
                return 1.0
            if not orig_agents or not gen_agents:
                return 0.0
            
            # 转换为列表格式
            if isinstance(orig_agents, dict):
                orig_agents = list(orig_agents.values())
            if isinstance(gen_agents, dict):
                gen_agents = list(gen_agents.values())
            
            if not isinstance(orig_agents, list) or not isinstance(gen_agents, list):
                return 0.0
            
            # 比较智能体数量和类型
            count_similarity = min(len(gen_agents), len(orig_agents)) / max(len(orig_agents), 1)
            
            orig_types = set(agent.get('type', '') for agent in orig_agents if isinstance(agent, dict))
            gen_types = set(agent.get('type', '') for agent in gen_agents if isinstance(agent, dict))
            
            type_similarity = len(orig_types & gen_types) / max(len(orig_types), 1) if orig_types else 0.0
            
            return (count_similarity * 0.7 + type_similarity * 0.3)
            
        except Exception:
            return 0.0
    
    def _calculate_controllers_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算控制器配置相似度"""
        try:
            orig_controllers = orig.get('controllers', orig.get('control', {}))
            gen_controllers = gen.get('controllers', gen.get('control', {}))
            
            if not orig_controllers and not gen_controllers:
                return 1.0
            if not orig_controllers or not gen_controllers:
                return 0.0
            
            # 比较控制器类型
            if isinstance(orig_controllers, dict) and isinstance(gen_controllers, dict):
                common_keys = set(orig_controllers.keys()) & set(gen_controllers.keys())
                total_keys = set(orig_controllers.keys()) | set(gen_controllers.keys())
                return len(common_keys) / max(len(total_keys), 1)
            
            return 0.5
            
        except Exception:
            return 0.0
    
    def _calculate_disturbances_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算扰动配置相似度"""
        try:
            orig_dist = orig.get('disturbances', orig.get('disturbance', []))
            gen_dist = gen.get('disturbances', gen.get('disturbance', []))
            
            if not orig_dist and not gen_dist:
                return 1.0
            if not orig_dist or not gen_dist:
                return 0.0
            
            # 转换为列表格式
            if isinstance(orig_dist, dict):
                orig_dist = list(orig_dist.values())
            if isinstance(gen_dist, dict):
                gen_dist = list(gen_dist.values())
            
            if isinstance(orig_dist, list) and isinstance(gen_dist, list):
                return min(len(gen_dist), len(orig_dist)) / max(len(orig_dist), 1)
            
            return 0.5
            
        except Exception:
            return 0.0
    
    def _calculate_analysis_similarity(self, orig: Dict[str, Any], gen: Dict[str, Any]) -> float:
        """计算分析配置相似度"""
        try:
            orig_analysis = orig.get('analysis', orig.get('analytics', {}))
            gen_analysis = gen.get('analysis', gen.get('analytics', {}))
            
            if not orig_analysis and not gen_analysis:
                return 1.0
            if not orig_analysis or not gen_analysis:
                return 0.0
            
            if isinstance(orig_analysis, dict) and isinstance(gen_analysis, dict):
                common_keys = set(orig_analysis.keys()) & set(gen_analysis.keys())
                total_keys = set(orig_analysis.keys()) | set(gen_analysis.keys())
                return len(common_keys) / max(len(total_keys), 1)
            
            return 0.5
            
        except Exception:
            return 0.0
    
    def _extract_components(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取组件列表"""
        components = config.get('components', {})
        
        if isinstance(components, dict):
            if 'components' in components:
                return components['components'] if isinstance(components['components'], list) else []
            else:
                return list(components.values()) if components else []
        elif isinstance(components, list):
            return components
        else:
            return []
    
    def _extract_topology(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取拓扑连接列表"""
        topology = config.get('topology', {})
        
        if isinstance(topology, dict):
            return topology.get('connections', [])
        elif isinstance(topology, list):
            return topology
        else:
            return []
    
    def analyze_coverage(self, original_config: Dict[str, Any], generated_config: Dict[str, Any]) -> Dict[str, bool]:
        """分析配置覆盖度"""
        coverage = {
            'has_components': False,
            'has_topology': False,
            'has_simulation': False,
            'has_scenarios': False,
            'has_debug': False,
            'has_logging': False,
            'has_agents': False,
            'has_controllers': False,
            'has_disturbances': False,
            'has_analysis': False
        }
        
        try:
            # 检查原始配置中存在的项目是否在生成配置中也存在
            if original_config.get('components'):
                coverage['has_components'] = bool(generated_config.get('components'))
            
            if original_config.get('topology'):
                coverage['has_topology'] = bool(generated_config.get('topology'))
            
            if original_config.get('simulation'):
                coverage['has_simulation'] = bool(generated_config.get('simulation'))
            
            if original_config.get('scenarios') or original_config.get('scenario'):
                coverage['has_scenarios'] = bool(generated_config.get('scenarios') or generated_config.get('scenario'))
            
            if original_config.get('debug') or original_config.get('debugging'):
                coverage['has_debug'] = bool(generated_config.get('debug') or generated_config.get('debugging'))
            
            if original_config.get('logging') or original_config.get('log'):
                coverage['has_logging'] = bool(generated_config.get('logging') or generated_config.get('log'))
            
            if original_config.get('agents') or original_config.get('agent_config'):
                coverage['has_agents'] = bool(generated_config.get('agents') or generated_config.get('agent_config'))
            
            if original_config.get('controllers') or original_config.get('control'):
                coverage['has_controllers'] = bool(generated_config.get('controllers') or generated_config.get('control'))
            
            if original_config.get('disturbances') or original_config.get('disturbance'):
                coverage['has_disturbances'] = bool(generated_config.get('disturbances') or generated_config.get('disturbance'))
            
            if original_config.get('analysis') or original_config.get('analytics'):
                coverage['has_analysis'] = bool(generated_config.get('analysis') or generated_config.get('analytics'))
            
        except Exception as e:
            self.logger.error(f"覆盖度分析失败: {e}")
        
        return coverage
    
    def test_single_config(self, config_path: str, config_type: str) -> EnhancedConversionTestResult:
        """测试单个配置文件的双向转换"""
        self.logger.info(f"测试配置文件: {config_path}")
        
        errors = []
        warnings = []
        
        # 1. 配置文件 -> 自然语言
        lang_success, description, lang_time, lang_errors = self.test_config_to_language(config_path)
        errors.extend(lang_errors)
        
        if not lang_success:
            return EnhancedConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=False,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=lang_time,
                language_to_config_time=0.0,
                similarity_score=0.0,
                detailed_similarity={},
                strategy_used='N/A',
                confidence_score=0.0,
                coverage_analysis={},
                errors=errors,
                warnings=warnings
            )
        
        # 2. 自然语言 -> 配置文件 (测试不同策略)
        best_result = None
        best_similarity = 0.0
        
        for strategy in self.test_strategies:
            config_success, generated_config, config_time, confidence, config_errors = self.test_language_to_config(description, strategy)
            
            if config_success:
                # 加载原始配置进行比较
                try:
                    original_config = self.config_manager.load_config(
                        self.config_manager.detect_config_type(config_path)
                    )
                    similarity, detailed_similarity = self.calculate_enhanced_similarity(original_config, generated_config)
                    coverage_analysis = self.analyze_coverage(original_config, generated_config)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_result = {
                            'strategy': strategy,
                            'config_success': config_success,
                            'config_time': config_time,
                            'confidence': confidence,
                            'similarity': similarity,
                            'detailed_similarity': detailed_similarity,
                            'coverage_analysis': coverage_analysis,
                            'config_errors': config_errors
                        }
                        
                except Exception as e:
                    warnings.append(f"加载原始配置失败 ({strategy}): {str(e)}")
            else:
                warnings.append(f"策略 {strategy} 转换失败: {config_errors}")
        
        # 构建最终结果
        if best_result:
            return EnhancedConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=lang_success,
                language_to_config_success=best_result['config_success'],
                roundtrip_success=lang_success and best_result['config_success'] and best_result['similarity'] > 0.15,
                original_to_language_time=lang_time,
                language_to_config_time=best_result['config_time'],
                similarity_score=best_result['similarity'],
                detailed_similarity=best_result['detailed_similarity'],
                strategy_used=best_result['strategy'],
                confidence_score=best_result['confidence'],
                coverage_analysis=best_result['coverage_analysis'],
                errors=errors + best_result['config_errors'],
                warnings=warnings
            )
        else:
            return EnhancedConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=lang_success,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=lang_time,
                language_to_config_time=0.0,
                similarity_score=0.0,
                detailed_similarity={},
                strategy_used='N/A',
                confidence_score=0.0,
                coverage_analysis={},
                errors=errors,
                warnings=warnings
            )
    
    def run_comprehensive_test(self, examples_dir: str = "examples") -> Dict[str, Any]:
        """运行全面的双向转换测试"""
        self.logger.info("开始增强版双向转换精度测试")
        
        # 查找所有配置文件
        config_files = self.find_all_config_files(examples_dir)
        
        if not config_files:
            self.logger.error("未找到任何配置文件")
            return {}
        
        results = []
        total_tests = len(config_files)
        
        for i, (config_path, config_type) in enumerate(config_files, 1):
            self.logger.info(f"进度: {i}/{total_tests} - 测试 {config_path}")
            
            try:
                result = self.test_single_config(config_path, config_type)
                results.append(result)
                
                # 输出进度信息
                status = "成功" if result.roundtrip_success else "失败"
                self.logger.info(f"完成测试: {config_path} - 往返{status}: {result.roundtrip_success}")
                
            except Exception as e:
                self.logger.error(f"测试失败: {config_path}, 错误: {e}")
                # 创建失败结果
                failed_result = EnhancedConversionTestResult(
                    config_path=config_path,
                    config_type=config_type,
                    original_to_language_success=False,
                    language_to_config_success=False,
                    roundtrip_success=False,
                    original_to_language_time=0.0,
                    language_to_config_time=0.0,
                    similarity_score=0.0,
                    detailed_similarity={},
                    strategy_used='N/A',
                    confidence_score=0.0,
                    coverage_analysis={},
                    errors=[f"测试异常: {str(e)}"],
                    warnings=[]
                )
                results.append(failed_result)
        
        # 生成统计报告
        report = self.generate_enhanced_report(results)
        
        # 保存详细报告
        report_file = "enhanced_bidirectional_conversion_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"测试报告已保存到: {report_file}")
        
        # 输出摘要
        summary = report['summary']
        print(f"\n增强版测试摘要:")
        print(f"总测试数: {summary['total_tests']}")
        print(f"配置->语言成功率: {summary['config_to_language_success_rate']:.2%}")
        print(f"语言->配置成功率: {summary['language_to_config_success_rate']:.2%}")
        print(f"往返转换成功率: {summary['roundtrip_success_rate']:.2%}")
        print(f"平均相似度: {summary['average_similarity']:.2f}")
        print(f"平均置信度: {summary['average_confidence']:.2f}")
        print(f"平均覆盖度: {summary['average_coverage_rate']:.2%}")
        
        return report
    
    def generate_enhanced_report(self, results: List[EnhancedConversionTestResult]) -> Dict[str, Any]:
        """生成增强版测试报告"""
        total_tests = len(results)
        
        if total_tests == 0:
            return {"error": "没有测试结果"}
        
        # 基础统计
        config_to_lang_success = sum(1 for r in results if r.original_to_language_success)
        lang_to_config_success = sum(1 for r in results if r.language_to_config_success)
        roundtrip_success = sum(1 for r in results if r.roundtrip_success)
        
        # 相似度和置信度统计
        similarities = [r.similarity_score for r in results if r.similarity_score > 0]
        confidences = [r.confidence_score for r in results if r.confidence_score > 0]
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 覆盖度统计
        coverage_rates = []
        for result in results:
            if result.coverage_analysis:
                coverage_rate = sum(result.coverage_analysis.values()) / len(result.coverage_analysis)
                coverage_rates.append(coverage_rate)
        
        avg_coverage_rate = sum(coverage_rates) / len(coverage_rates) if coverage_rates else 0.0
        
        # 详细相似度统计
        detailed_similarity_stats = {}
        similarity_categories = ['components', 'topology', 'simulation', 'scenarios', 'debug', 'logging', 'agents', 'controllers', 'disturbances', 'analysis']
        
        for category in similarity_categories:
            category_scores = [r.detailed_similarity.get(category, 0.0) for r in results if r.detailed_similarity]
            detailed_similarity_stats[category] = {
                'average': sum(category_scores) / len(category_scores) if category_scores else 0.0,
                'max': max(category_scores) if category_scores else 0.0,
                'min': min(category_scores) if category_scores else 0.0
            }
        
        # 按配置类型统计
        by_config_type = {}
        for result in results:
            config_type = str(result.config_type)  # 转换为字符串
            if config_type not in by_config_type:
                by_config_type[config_type] = {
                    'total': 0,
                    'lang_success': 0,
                    'config_success': 0,
                    'roundtrip_success': 0,
                    'similarities': [],
                    'coverage_rates': []
                }
            
            stats = by_config_type[config_type]
            stats['total'] += 1
            if result.original_to_language_success:
                stats['lang_success'] += 1
            if result.language_to_config_success:
                stats['config_success'] += 1
            if result.roundtrip_success:
                stats['roundtrip_success'] += 1
            if result.similarity_score > 0:
                stats['similarities'].append(result.similarity_score)
            if result.coverage_analysis:
                coverage_rate = sum(result.coverage_analysis.values()) / len(result.coverage_analysis)
                stats['coverage_rates'].append(coverage_rate)
        
        # 计算每种配置类型的平均值
        for config_type, stats in by_config_type.items():
            stats['avg_similarity'] = sum(stats['similarities']) / len(stats['similarities']) if stats['similarities'] else 0.0
            stats['avg_coverage_rate'] = sum(stats['coverage_rates']) / len(stats['coverage_rates']) if stats['coverage_rates'] else 0.0
            del stats['similarities']
            del stats['coverage_rates']
        
        # 按策略统计
        by_strategy = {}
        for result in results:
            strategy = result.strategy_used
            if strategy not in by_strategy:
                by_strategy[strategy] = {
                    'count': 0,
                    'success': 0,
                    'confidences': [],
                    'similarities': []
                }
            
            stats = by_strategy[strategy]
            stats['count'] += 1
            if result.language_to_config_success:
                stats['success'] += 1
            if result.confidence_score > 0:
                stats['confidences'].append(result.confidence_score)
            if result.similarity_score > 0:
                stats['similarities'].append(result.similarity_score)
        
        # 计算每种策略的平均值
        for strategy, stats in by_strategy.items():
            stats['avg_confidence'] = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0.0
            stats['avg_similarity'] = sum(stats['similarities']) / len(stats['similarities']) if stats['similarities'] else 0.0
            del stats['confidences']
            del stats['similarities']
        
        return {
            'summary': {
                'total_tests': total_tests,
                'config_to_language_success_rate': config_to_lang_success / total_tests,
                'language_to_config_success_rate': lang_to_config_success / total_tests,
                'roundtrip_success_rate': roundtrip_success / total_tests,
                'average_similarity': avg_similarity,
                'average_confidence': avg_confidence,
                'average_coverage_rate': avg_coverage_rate
            },
            'detailed_similarity_stats': detailed_similarity_stats,
            'by_config_type': by_config_type,
            'by_strategy': by_strategy,
            'detailed_results': [asdict(result) for result in results]
        }

def main():
    """主函数"""
    tester = EnhancedBidirectionalConversionTester()
    report = tester.run_comprehensive_test()
    
    print("\n详细报告已保存到: enhanced_bidirectional_conversion_test_report.json")
    
    return report

if __name__ == "__main__":
    main()