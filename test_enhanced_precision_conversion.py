#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成精度增强的双向转换测试

集成新开发的精度增强模块，测试改进后的转换精度：
1. 使用精度增强框架优化转换结果
2. 对比增强前后的转换精度
3. 分析各项改进指标的效果
4. 生成详细的改进报告

作者: CHS-SDK Team
创建时间: 2024
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigInfo
from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.enhanced_language_to_config_converter import EnhancedLanguageToConfigConverter
from precision_enhancement_module import PrecisionEnhancementFramework

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_precision_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class EnhancedTestResult:
    """增强测试结果数据类"""
    config_path: str
    config_type: str
    
    # 基础转换结果
    original_to_language_success: bool
    language_to_config_success: bool
    roundtrip_success: bool
    
    # 转换时间
    original_to_language_time: float
    language_to_config_time: float
    enhancement_time: float
    
    # 精度指标
    baseline_similarity: float  # 基础相似度
    enhanced_similarity: float  # 增强后相似度
    improvement_score: float    # 改进分数
    
    # 详细相似度
    baseline_detailed_similarity: Dict[str, float]
    enhanced_detailed_similarity: Dict[str, float]
    
    # 增强信息
    applied_enhancements: List[str]
    enhancement_metrics: Dict[str, float]
    
    # 其他信息
    strategy_used: str
    confidence_score: float
    errors: List[str]
    warnings: List[str]


class EnhancedPrecisionTester:
    """增强精度测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = UnifiedConfigManager()
        self.config_to_language = ConfigToLanguageConverter()
        self.language_to_config = EnhancedLanguageToConfigConverter()
        self.enhancement_framework = PrecisionEnhancementFramework()
        
        self.test_results = []
        
    def find_config_files(self, base_dir: str = "examples") -> List[ConfigInfo]:
        """查找统一配置文件"""
        config_files = []
        base_path = Path(base_dir)
        
        if not base_path.exists():
            self.logger.error(f"目录不存在: {base_dir}")
            return config_files
        
        # 查找统一配置文件（yml格式）
        for yaml_file in base_path.rglob("*.yml"):
            # 跳过非配置文件
            if yaml_file.name in ['scenarios.yml', 'topology.yml']:
                continue
            # 跳过输出和结果目录
            if any(skip_dir in str(yaml_file) for skip_dir in ['output', 'results', 'logs', 'temp', 'cache']):
                continue
            # 只选择统一配置文件
            if any(config_name in yaml_file.name.lower() for config_name in ['unified_config', 'universal_config']):
                try:
                    # 验证是否为统一配置文件格式
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 检查是否包含统一配置的关键字段
                        if any(keyword in content for keyword in ['components:', 'simulation:', 'metadata:']):
                            # 直接创建ConfigInfo对象
                            from core_lib.config.unified_config_manager import ConfigType
                            config_info = ConfigInfo(
                                config_type=ConfigType.UNIFIED_SINGLE,
                                config_path=yaml_file,
                                config_files={'main': yaml_file},
                                metadata={},
                                description=f"统一配置文件: {yaml_file.name}"
                            )
                            config_files.append(config_info)
                        else:
                            self.logger.debug(f"跳过非统一配置文件: {yaml_file}")
                except Exception as e:
                    self.logger.warning(f"无法处理配置文件 {yaml_file}: {e}")
        
        self.logger.info(f"找到 {len(config_files)} 个统一配置文件")
        return config_files
    
    def _convert_config_to_language(self, config_path: str) -> Tuple[bool, str, float, str, float]:
        """配置文件转自然语言"""
        try:
            start_time = time.time()
            result = self.config_to_language.convert_config_to_language(config_path)
            conversion_time = time.time() - start_time
            
            if result and hasattr(result, 'summary'):
                # 组合完整描述
                description_parts = []
                if hasattr(result, 'summary') and result.summary:
                    description_parts.append(result.summary)
                if hasattr(result, 'modeling_description') and result.modeling_description:
                    description_parts.append(result.modeling_description)
                if hasattr(result, 'scenario_description') and result.scenario_description:
                    description_parts.append(result.scenario_description)
                if hasattr(result, 'analysis_description') and result.analysis_description:
                    description_parts.append(result.analysis_description)
                
                description = "\n\n".join(description_parts)
                return True, description, conversion_time, "success", 1.0
            else:
                return False, "", conversion_time, "转换结果为空", 0.0
                
        except Exception as e:
            self.logger.error(f"配置到语言转换失败: {e}")
            return False, "", 0.0, str(e), 0.0
    
    def _convert_language_to_config(self, description: str, config_type, output_dir: str) -> Tuple[bool, float, Dict[str, Any]]:
        """自然语言转配置文件"""
        try:
            start_time = time.time()
            
            # 处理配置类型
            if isinstance(config_type, str):
                from core_lib.config.unified_config_manager import ConfigType
                config_type = ConfigType.UNIFIED_SINGLE
            elif hasattr(config_type, 'name') and config_type.name == 'UNIVERSAL_CONFIG':
                from core_lib.config.unified_config_manager import ConfigType
                config_type = ConfigType.UNIFIED_SINGLE
            
            result = self.language_to_config.convert_language_to_config(
                description, config_type, output_dir
            )
            
            conversion_time = time.time() - start_time
            
            if result and hasattr(result, 'config_data'):
                return True, conversion_time, result.config_data
            else:
                return False, conversion_time, {}
                
        except Exception as e:
            self.logger.error(f"语言到配置转换失败: {e}")
            return False, 0.0, {}
    
    def calculate_enhanced_similarity(self, original_config: Dict, converted_config: Dict) -> Tuple[float, Dict[str, float]]:
        """计算增强相似度"""
        detailed_scores = {}
        total_score = 0.0
        
        # 权重配置
        weights = {
            'components': 0.25,
            'topology': 0.20,
            'simulation': 0.15,
            'scenarios': 0.10,
            'debug': 0.05,
            'logging': 0.05,
            'agents': 0.10,
            'controllers': 0.05,
            'disturbances': 0.03,
            'analysis': 0.02
        }
        
        # 1. 组件相似度
        detailed_scores['components'] = self._calculate_components_similarity(original_config, converted_config)
        
        # 2. 拓扑相似度 - 增强版
        detailed_scores['topology'] = self._calculate_enhanced_topology_similarity(original_config, converted_config)
        
        # 3. 仿真相似度 - 增强版
        detailed_scores['simulation'] = self._calculate_enhanced_simulation_similarity(original_config, converted_config)
        
        # 4. 其他相似度
        detailed_scores['scenarios'] = self._calculate_scenarios_similarity(original_config, converted_config)
        detailed_scores['debug'] = self._calculate_debug_similarity(original_config, converted_config)
        detailed_scores['logging'] = self._calculate_logging_similarity(original_config, converted_config)
        detailed_scores['agents'] = self._calculate_agents_similarity(original_config, converted_config)
        detailed_scores['controllers'] = self._calculate_controllers_similarity(original_config, converted_config)
        detailed_scores['disturbances'] = self._calculate_disturbances_similarity(original_config, converted_config)
        detailed_scores['analysis'] = self._calculate_analysis_similarity(original_config, converted_config)
        
        # 计算加权总分
        for component, score in detailed_scores.items():
            weight = weights.get(component, 0.0)
            total_score += score * weight
        
        return total_score, detailed_scores
    
    def _calculate_enhanced_topology_similarity(self, original: Dict, converted: Dict) -> float:
        """计算增强拓扑相似度"""
        orig_topology = self._get_nested_value(original, ['topology']) or []
        conv_topology = self._get_nested_value(converted, ['topology']) or []
        
        # 标准化拓扑格式
        orig_connections = self._normalize_connections(orig_topology)
        conv_connections = self._normalize_connections(conv_topology)
        
        if not orig_connections and not conv_connections:
            return 1.0
        if not orig_connections or not conv_connections:
            return 0.0
        
        # 连接数量相似度
        count_diff = abs(len(orig_connections) - len(conv_connections))
        max_count = max(len(orig_connections), len(conv_connections))
        count_similarity = 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
        
        # 连接内容相似度
        content_similarity = 0.0
        if orig_connections and conv_connections:
            matched_connections = 0
            for orig_conn in orig_connections:
                for conv_conn in conv_connections:
                    if self._connections_similar(orig_conn, conv_conn):
                        matched_connections += 1
                        break
            content_similarity = matched_connections / len(orig_connections)
        
        # 综合相似度
        return (count_similarity * 0.4 + content_similarity * 0.6)
    
    def _normalize_connections(self, topology) -> List[Dict[str, str]]:
        """标准化连接格式"""
        connections = []
        
        if isinstance(topology, dict):
            if 'connections' in topology:
                topology = topology['connections']
            else:
                topology = list(topology.values())
        
        if isinstance(topology, list):
            for conn in topology:
                if isinstance(conn, dict):
                    connections.append({
                        'from': conn.get('from', conn.get('source', '')),
                        'to': conn.get('to', conn.get('target', '')),
                        'type': conn.get('type', 'flow')
                    })
        
        return connections
    
    def _connections_similar(self, conn1: Dict, conn2: Dict) -> bool:
        """判断两个连接是否相似"""
        return (conn1.get('from') == conn2.get('from') and 
                conn1.get('to') == conn2.get('to')) or \
               (conn1.get('from') == conn2.get('to') and 
                conn1.get('to') == conn2.get('from'))
    
    def _calculate_enhanced_simulation_similarity(self, original: Dict, converted: Dict) -> float:
        """计算增强仿真相似度"""
        orig_sim = self._get_nested_value(original, ['simulation']) or {}
        conv_sim = self._get_nested_value(converted, ['simulation']) or {}
        
        if not orig_sim and not conv_sim:
            return 1.0
        if not orig_sim or not conv_sim:
            return 0.0
        
        # 关键参数映射
        param_mappings = {
            'duration': ['duration', 'end_time', 'total_time'],
            'dt': ['dt', 'time_step', 'timestep'],
            'solver': ['solver', 'method', 'algorithm'],
            'name': ['name', 'title', 'description']
        }
        
        matches = 0
        total = 0
        
        for standard_param, aliases in param_mappings.items():
            orig_val = None
            conv_val = None
            
            # 查找原始值
            for alias in aliases:
                if orig_val is None:
                    orig_val = self._get_nested_value(orig_sim, [alias])
                if conv_val is None:
                    conv_val = self._get_nested_value(conv_sim, [alias])
            
            if orig_val is not None or conv_val is not None:
                total += 1
                if self._values_similar(orig_val, conv_val):
                    matches += 1
        
        return matches / total if total > 0 else 1.0
    
    def _calculate_components_similarity(self, original: Dict, converted: Dict) -> float:
        """计算组件相似度"""
        orig_components = self._extract_components_list(original)
        conv_components = self._extract_components_list(converted)
        
        if not orig_components and not conv_components:
            return 1.0
        if not orig_components or not conv_components:
            return 0.0
        
        # 组件数量相似度
        count_diff = abs(len(orig_components) - len(conv_components))
        max_count = max(len(orig_components), len(conv_components))
        count_similarity = 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
        
        # 组件类型相似度
        orig_types = {comp.get('type', '') for comp in orig_components}
        conv_types = {comp.get('type', '') for comp in conv_components}
        
        if orig_types and conv_types:
            type_intersection = len(orig_types & conv_types)
            type_union = len(orig_types | conv_types)
            type_similarity = type_intersection / type_union if type_union > 0 else 0.0
        else:
            type_similarity = 0.0
        
        return (count_similarity * 0.5 + type_similarity * 0.5)
    
    def _extract_components_list(self, config: Dict) -> List[Dict]:
        """提取组件列表"""
        components = config.get('components', {})
        
        if isinstance(components, dict):
            if 'components' in components:
                return components['components']
            else:
                return list(components.values())
        elif isinstance(components, list):
            return components
        else:
            return []
    
    def _calculate_scenarios_similarity(self, original: Dict, converted: Dict) -> float:
        """计算情景相似度"""
        orig_scenarios = original.get('scenarios', [])
        conv_scenarios = converted.get('scenarios', [])
        
        if not orig_scenarios and not conv_scenarios:
            return 1.0
        if not orig_scenarios or not conv_scenarios:
            return 0.0
        
        count_diff = abs(len(orig_scenarios) - len(conv_scenarios))
        max_count = max(len(orig_scenarios), len(conv_scenarios))
        return 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
    
    def _calculate_debug_similarity(self, original: Dict, converted: Dict) -> float:
        """计算调试相似度"""
        orig_debug = original.get('debug', {})
        conv_debug = converted.get('debug', {})
        
        if not orig_debug and not conv_debug:
            return 1.0
        if not orig_debug or not conv_debug:
            return 0.0
        
        return 0.5  # 简化计算
    
    def _calculate_logging_similarity(self, original: Dict, converted: Dict) -> float:
        """计算日志相似度"""
        orig_logging = original.get('logging', {})
        conv_logging = converted.get('logging', {})
        
        if not orig_logging and not conv_logging:
            return 1.0
        if not orig_logging or not conv_logging:
            return 0.0
        
        return 0.5  # 简化计算
    
    def _calculate_agents_similarity(self, original: Dict, converted: Dict) -> float:
        """计算智能体相似度"""
        orig_agents = original.get('agents', [])
        conv_agents = converted.get('agents', [])
        
        if not orig_agents and not conv_agents:
            return 1.0
        if not orig_agents or not conv_agents:
            return 0.0
        
        count_diff = abs(len(orig_agents) - len(conv_agents))
        max_count = max(len(orig_agents), len(conv_agents))
        return 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
    
    def _calculate_controllers_similarity(self, original: Dict, converted: Dict) -> float:
        """计算控制器相似度"""
        orig_controllers = original.get('controllers', [])
        conv_controllers = converted.get('controllers', [])
        
        if not orig_controllers and not conv_controllers:
            return 1.0
        if not orig_controllers or not conv_controllers:
            return 0.0
        
        count_diff = abs(len(orig_controllers) - len(conv_controllers))
        max_count = max(len(orig_controllers), len(conv_controllers))
        return 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
    
    def _calculate_disturbances_similarity(self, original: Dict, converted: Dict) -> float:
        """计算扰动相似度"""
        orig_disturbances = original.get('disturbances', [])
        conv_disturbances = converted.get('disturbances', [])
        
        if not orig_disturbances and not conv_disturbances:
            return 1.0
        if not orig_disturbances or not conv_disturbances:
            return 0.0
        
        count_diff = abs(len(orig_disturbances) - len(conv_disturbances))
        max_count = max(len(orig_disturbances), len(conv_disturbances))
        return 1.0 - (count_diff / max_count) if max_count > 0 else 1.0
    
    def _calculate_analysis_similarity(self, original: Dict, converted: Dict) -> float:
        """计算分析相似度"""
        orig_analysis = original.get('analysis', {})
        conv_analysis = converted.get('analysis', {})
        
        if not orig_analysis and not conv_analysis:
            return 1.0
        if not orig_analysis or not conv_analysis:
            return 0.0
        
        return 0.5  # 简化计算
    
    def _get_nested_value(self, data: Dict, keys: List[str]) -> Any:
        """获取嵌套值"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _values_similar(self, val1: Any, val2: Any, tolerance: float = 0.1) -> bool:
        """判断值是否相似"""
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val1 == 0 and val2 == 0:
                return True
            if val1 == 0 or val2 == 0:
                return abs(val1 - val2) < tolerance
            return abs(val1 - val2) / max(abs(val1), abs(val2)) < tolerance
        
        return str(val1).lower() == str(val2).lower()
    
    def test_single_config(self, config_info: ConfigInfo) -> EnhancedTestResult:
        """测试单个配置文件"""
        config_path = str(config_info.config_path)
        config_type = config_info.config_type
        errors = []
        warnings = []
        
        self.logger.info(f"测试配置文件: {config_path}")
        
        # 1. 配置到语言转换
        to_lang_success, description, to_lang_time, to_lang_error, confidence = self._convert_config_to_language(config_path)
        
        if not to_lang_success:
            errors.append(f"配置到语言转换失败: {to_lang_error}")
            return EnhancedTestResult(
                config_path=config_path,
                config_type=str(config_type),
                original_to_language_success=False,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=to_lang_time,
                language_to_config_time=0.0,
                enhancement_time=0.0,
                baseline_similarity=0.0,
                enhanced_similarity=0.0,
                improvement_score=0.0,
                baseline_detailed_similarity={},
                enhanced_detailed_similarity={},
                applied_enhancements=[],
                enhancement_metrics={},
                strategy_used="N/A",
                confidence_score=0.0,
                errors=errors,
                warnings=warnings
            )
        
        # 2. 语言到配置转换
        output_dir = f"test_output/{Path(config_path).stem}"
        os.makedirs(output_dir, exist_ok=True)
        
        to_config_success, to_config_time, converted_config = self._convert_language_to_config(description, config_type, output_dir)
        
        if not to_config_success:
            errors.append("语言到配置转换失败")
            return EnhancedTestResult(
                config_path=config_path,
                config_type=str(config_type),
                original_to_language_success=True,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=to_lang_time,
                language_to_config_time=to_config_time,
                enhancement_time=0.0,
                baseline_similarity=0.0,
                enhanced_similarity=0.0,
                improvement_score=0.0,
                baseline_detailed_similarity={},
                enhanced_detailed_similarity={},
                applied_enhancements=[],
                enhancement_metrics={},
                strategy_used="N/A",
                confidence_score=confidence,
                errors=errors,
                warnings=warnings
            )
        
        # 3. 加载原始配置
        try:
            original_config = self.config_manager.load_config(config_info)
            if hasattr(original_config, 'config_data'):
                original_config = original_config.config_data
        except Exception as e:
            errors.append(f"加载原始配置失败: {e}")
            original_config = {}
        
        # 4. 计算基础相似度（原始配置 vs 往返转换后配置）
        baseline_similarity, baseline_detailed = self.calculate_enhanced_similarity(original_config, converted_config)
        
        # 5. 应用精度增强
        enhancement_start = time.time()
        enhancement_result = self.enhancement_framework.enhance_conversion_precision(converted_config, description)
        enhanced_config = enhancement_result.enhanced_config
        
        # 6. 对增强后的配置进行往返转换测试
        enhanced_roundtrip_success = False
        enhanced_roundtrip_config = None
        
        try:
            # 将增强后的配置保存为临时文件
            import yaml
            temp_enhanced_path = os.path.join(output_dir, "universal_config.yml")
            with open(temp_enhanced_path, 'w', encoding='utf-8') as f:
                yaml.dump(enhanced_config, f, default_flow_style=False, allow_unicode=True)
            
            # 对增强后的配置进行配置到语言转换
            enhanced_to_lang_success, enhanced_description, enhanced_to_lang_time, _, _ = self._convert_config_to_language(temp_enhanced_path)
            
            if enhanced_to_lang_success:
                # 对增强后的描述进行语言到配置转换
                enhanced_roundtrip_success, enhanced_roundtrip_time, enhanced_roundtrip_config = self._convert_language_to_config(
                    enhanced_description, config_type, output_dir
                )
            
            # 清理临时文件
            if os.path.exists(temp_enhanced_path):
                os.remove(temp_enhanced_path)
                
        except Exception as e:
            self.logger.warning(f"增强后往返转换测试失败: {e}")
            enhanced_roundtrip_success = False
        
        # 计算增强后的相似度
        if enhanced_roundtrip_success and enhanced_roundtrip_config is not None:
            # 如果增强后往返转换成功，比较原始配置与增强后往返转换的配置
            enhanced_similarity, enhanced_detailed = self.calculate_enhanced_similarity(original_config, enhanced_roundtrip_config)
            self.logger.info(f"增强后往返转换成功，相似度: {enhanced_similarity:.4f}")
        else:
            # 如果增强后往返转换失败，使用基础往返转换的相似度作为增强相似度
            # 这样可以确保改进分数反映的是增强对往返转换精度的实际影响
            enhanced_similarity, enhanced_detailed = baseline_similarity, baseline_detailed
            self.logger.warning(f"增强后往返转换失败，使用基础相似度: {enhanced_similarity:.4f}")
        
        enhancement_time = time.time() - enhancement_start
        
        # 7. 计算改进分数
        improvement_score = enhanced_similarity - baseline_similarity
        
        # 8. 判断往返转换成功
        roundtrip_success = to_lang_success and to_config_success and enhanced_similarity > 0.3
        
        return EnhancedTestResult(
            config_path=config_path,
            config_type=str(config_type),
            original_to_language_success=to_lang_success,
            language_to_config_success=to_config_success,
            roundtrip_success=roundtrip_success,
            original_to_language_time=to_lang_time,
            language_to_config_time=to_config_time,
            enhancement_time=enhancement_time,
            baseline_similarity=baseline_similarity,
            enhanced_similarity=enhanced_similarity,
            improvement_score=improvement_score,
            baseline_detailed_similarity=baseline_detailed,
            enhanced_detailed_similarity=enhanced_detailed,
            applied_enhancements=enhancement_result.applied_enhancements,
            enhancement_metrics=enhancement_result.metrics,
            strategy_used="hybrid",
            confidence_score=confidence,
            errors=errors,
            warnings=warnings + enhancement_result.warnings
        )
    
    def run_enhanced_precision_tests(self) -> Dict[str, Any]:
        """运行增强精度测试"""
        self.logger.info("开始增强精度测试")
        
        # 查找配置文件
        config_files = self.find_config_files()
        
        if not config_files:
            self.logger.error("未找到任何配置文件")
            return {}
        
        # 测试每个配置文件
        for config_info in config_files:
            try:
                result = self.test_single_config(config_info)
                self.test_results.append(result)
                
                # 输出进度
                self.logger.info(f"完成测试: {config_info.config_path} - 基础相似度: {result.baseline_similarity:.3f}, 增强相似度: {result.enhanced_similarity:.3f}, 改进: {result.improvement_score:.3f}")
                
            except Exception as e:
                self.logger.error(f"测试配置文件失败 {config_info.config_path}: {e}")
        
        # 生成测试报告
        return self.generate_enhanced_report()
    
    def generate_enhanced_report(self) -> Dict[str, Any]:
        """生成增强测试报告"""
        if not self.test_results:
            return {}
        
        # 统计基础指标
        total_tests = len(self.test_results)
        successful_to_language = sum(1 for r in self.test_results if r.original_to_language_success)
        successful_to_config = sum(1 for r in self.test_results if r.language_to_config_success)
        successful_roundtrip = sum(1 for r in self.test_results if r.roundtrip_success)
        
        # 计算平均相似度
        baseline_similarities = [r.baseline_similarity for r in self.test_results if r.roundtrip_success]
        enhanced_similarities = [r.enhanced_similarity for r in self.test_results if r.roundtrip_success]
        improvements = [r.improvement_score for r in self.test_results if r.roundtrip_success]
        
        avg_baseline_similarity = sum(baseline_similarities) / len(baseline_similarities) if baseline_similarities else 0.0
        avg_enhanced_similarity = sum(enhanced_similarities) / len(enhanced_similarities) if enhanced_similarities else 0.0
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        
        # 统计增强效果
        positive_improvements = sum(1 for imp in improvements if imp > 0)
        significant_improvements = sum(1 for imp in improvements if imp > 0.1)
        
        # 详细相似度统计
        baseline_detailed_stats = defaultdict(list)
        enhanced_detailed_stats = defaultdict(list)
        
        for result in self.test_results:
            if result.roundtrip_success:
                for component, score in result.baseline_detailed_similarity.items():
                    baseline_detailed_stats[component].append(score)
                for component, score in result.enhanced_detailed_similarity.items():
                    enhanced_detailed_stats[component].append(score)
        
        # 计算各组件平均相似度
        baseline_component_averages = {}
        enhanced_component_averages = {}
        component_improvements = {}
        
        for component in baseline_detailed_stats:
            baseline_avg = sum(baseline_detailed_stats[component]) / len(baseline_detailed_stats[component])
            enhanced_avg = sum(enhanced_detailed_stats[component]) / len(enhanced_detailed_stats[component])
            
            baseline_component_averages[component] = baseline_avg
            enhanced_component_averages[component] = enhanced_avg
            component_improvements[component] = enhanced_avg - baseline_avg
        
        # 统计增强技术使用情况
        enhancement_usage = defaultdict(int)
        for result in self.test_results:
            for enhancement in result.applied_enhancements:
                enhancement_usage[enhancement] += 1
        
        # 生成报告
        report = {
            "测试概览": {
                "总测试数": total_tests,
                "配置到语言成功率": f"{successful_to_language / total_tests * 100:.2f}%" if total_tests > 0 else "0.00%",
                "语言到配置成功率": f"{successful_to_config / total_tests * 100:.2f}%" if total_tests > 0 else "0.00%",
                "往返转换成功率": f"{successful_roundtrip / total_tests * 100:.2f}%" if total_tests > 0 else "0.00%",
                "测试时间": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "精度对比": {
                "基础平均相似度": f"{avg_baseline_similarity:.4f}",
                "增强平均相似度": f"{avg_enhanced_similarity:.4f}",
                "平均改进幅度": f"{avg_improvement:.4f}",
                "改进成功率": f"{positive_improvements / len(improvements) * 100:.2f}%" if improvements else "0.00%",
                "显著改进率": f"{significant_improvements / len(improvements) * 100:.2f}%" if improvements else "0.00%"
            },
            "组件相似度对比": {
                "基础相似度": baseline_component_averages,
                "增强相似度": enhanced_component_averages,
                "改进幅度": component_improvements
            },
            "增强技术使用统计": dict(enhancement_usage),
            "详细结果": []
        }
        
        # 添加详细结果
        for result in self.test_results:
            detail = {
                "配置文件": result.config_path,
                "配置类型": result.config_type,
                "往返转换成功": result.roundtrip_success,
                "基础相似度": result.baseline_similarity,
                "增强相似度": result.enhanced_similarity,
                "改进分数": result.improvement_score,
                "基础详细相似度": result.baseline_detailed_similarity,
                "增强详细相似度": result.enhanced_detailed_similarity,
                "应用的增强技术": result.applied_enhancements,
                "增强指标": result.enhancement_metrics,
                "转换时间": {
                    "配置到语言": f"{result.original_to_language_time:.3f}秒",
                    "语言到配置": f"{result.language_to_config_time:.3f}秒",
                    "精度增强": f"{result.enhancement_time:.3f}秒"
                },
                "置信度": result.confidence_score,
                "错误信息": result.errors,
                "警告信息": result.warnings
            }
            report["详细结果"].append(detail)
        
        # 保存报告
        report_file = "enhanced_precision_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"增强精度测试报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    tester = EnhancedPrecisionTester()
    
    # 运行增强精度测试
    report = tester.run_enhanced_precision_tests()
    
    if report:
        print("\n=== 增强精度测试报告 ===")
        print(f"总测试数: {report['测试概览']['总测试数']}")
        print(f"往返转换成功率: {report['测试概览']['往返转换成功率']}")
        print(f"基础平均相似度: {report['精度对比']['基础平均相似度']}")
        print(f"增强平均相似度: {report['精度对比']['增强平均相似度']}")
        print(f"平均改进幅度: {report['精度对比']['平均改进幅度']}")
        print(f"改进成功率: {report['精度对比']['改进成功率']}")
        print(f"显著改进率: {report['精度对比']['显著改进率']}")
        
        print("\n=== 组件改进效果 ===")
        for component, improvement in report['组件相似度对比']['改进幅度'].items():
            print(f"{component}: {improvement:+.4f}")
        
        print("\n=== 增强技术使用统计 ===")
        for technique, count in report['增强技术使用统计'].items():
            print(f"{technique}: {count}次")
    else:
        print("测试失败，未生成报告")


if __name__ == "__main__":
    main()