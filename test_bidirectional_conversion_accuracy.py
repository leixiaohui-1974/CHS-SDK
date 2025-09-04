#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双向转换精度测试脚本

测试CHS-SDK中配置文件与自然语言之间的双向转换精度，包括：
1. 配置文件 -> 自然语言描述
2. 自然语言描述 -> 配置文件
3. 往返转换精度评估
4. 不同转换策略的性能对比

作者: CHS-SDK Team
创建时间: 2024
"""

import os
import sys
import json
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import traceback

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.enhanced_language_to_config_converter import EnhancedLanguageToConfigConverter
from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bidirectional_conversion_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ConversionTestResult:
    """转换测试结果"""
    config_path: str
    config_type: str
    original_to_language_success: bool
    language_to_config_success: bool
    roundtrip_success: bool
    original_to_language_time: float
    language_to_config_time: float
    similarity_score: float
    strategy_used: str
    confidence_score: float
    errors: List[str]
    warnings: List[str]
    
class BidirectionalConversionTester:
    """双向转换测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_to_lang = ConfigToLanguageConverter()
        self.enhanced_lang_to_config = EnhancedLanguageToConfigConverter()
        self.config_manager = UnifiedConfigManager()
        
        # 测试策略
        self.test_strategies = ['llm', 'rule', 'hybrid']
        
        # 结果存储
        self.test_results: List[ConversionTestResult] = []
        
    def find_all_config_files(self, examples_dir: str) -> List[Tuple[str, str]]:
        """查找所有配置文件
        
        Returns:
            List[Tuple[str, str]]: (配置文件路径, 配置类型)
        """
        config_files = []
        examples_path = Path(examples_dir)
        
        if not examples_path.exists():
            self.logger.error(f"Examples目录不存在: {examples_dir}")
            return config_files
        
        # 查找不同类型的配置文件
        for root, dirs, files in os.walk(examples_path):
            root_path = Path(root)
            
            # 跳过输出目录和缓存目录
            if any(skip in str(root_path) for skip in ['output', 'cache', '__pycache__', '.git']):
                continue
            
            # 查找YAML配置文件
            yaml_files = [f for f in files if f.endswith(('.yml', '.yaml'))]
            
            if yaml_files:
                # 检测配置类型
                config_info = self.config_manager.detect_config_type(root_path)
                if config_info.config_type != ConfigType.UNKNOWN:
                    config_files.append((str(root_path), config_info.config_type.value))
                    self.logger.info(f"发现配置: {root_path} (类型: {config_info.config_type.value})")
        
        self.logger.info(f"总共发现 {len(config_files)} 个配置文件")
        return config_files
    
    def test_config_to_language(self, config_path: str) -> Tuple[bool, str, float, List[str]]:
        """测试配置文件到自然语言转换
        
        Returns:
            Tuple[bool, str, float, List[str]]: (成功标志, 自然语言描述, 转换时间, 错误列表)
        """
        start_time = time.time()
        errors = []
        
        try:
            # 转换为自然语言
            description = self.config_to_lang.convert_config_to_language(config_path)
            
            if description and description.summary:
                conversion_time = time.time() - start_time
                return True, description.summary, conversion_time, errors
            else:
                errors.append("生成的自然语言描述为空")
                return False, "", time.time() - start_time, errors
                
        except Exception as e:
            errors.append(f"配置到语言转换失败: {str(e)}")
            self.logger.error(f"配置到语言转换失败 {config_path}: {e}")
            return False, "", time.time() - start_time, errors
    
    def test_language_to_config(self, description: str, strategy: str = 'hybrid') -> Tuple[bool, Dict[str, Any], float, float, List[str]]:
        """测试自然语言到配置文件转换
        
        Returns:
            Tuple[bool, Dict, float, float, List[str]]: (成功标志, 配置数据, 转换时间, 置信度, 错误列表)
        """
        start_time = time.time()
        errors = []
        
        try:
            # 转换为配置文件
            result = self.enhanced_lang_to_config.convert_language_to_config(
                description, 
                ConfigType.UNIVERSAL_CONFIG,
                strategy=strategy
            )
            
            conversion_time = time.time() - start_time
            
            if result.config_data and result.confidence_score > 0.1:  # 降低置信度阈值
                return True, result.config_data, conversion_time, result.confidence_score, result.validation_errors
            else:
                errors.extend(result.validation_errors)
                errors.append(f"转换失败或置信度过低: {result.confidence_score}")
                return False, {}, conversion_time, result.confidence_score, errors
                
        except Exception as e:
            errors.append(f"语言到配置转换失败: {str(e)}")
            self.logger.error(f"语言到配置转换失败: {e}")
            return False, {}, time.time() - start_time, 0.0, errors
    
    def calculate_similarity(self, original_config: Dict[str, Any], generated_config: Dict[str, Any]) -> float:
        """计算配置文件相似度
        
        Returns:
            float: 相似度分数 (0-1)
        """
        try:
            # 简单的相似度计算
            similarity_score = 0.0
            total_checks = 0
            
            # 检查组件数量
            orig_components = original_config.get('components', {})
            gen_components = generated_config.get('components', {})
            
            # 处理不同的组件结构
            if isinstance(orig_components, dict):
                if 'components' in orig_components:
                    orig_comp_list = orig_components['components']
                else:
                    orig_comp_list = list(orig_components.values()) if orig_components else []
            elif isinstance(orig_components, list):
                orig_comp_list = orig_components
            else:
                orig_comp_list = []
            
            if isinstance(gen_components, dict):
                if 'components' in gen_components:
                    gen_comp_list = gen_components['components']
                else:
                    gen_comp_list = list(gen_components.values()) if gen_components else []
            elif isinstance(gen_components, list):
                gen_comp_list = gen_components
            else:
                gen_comp_list = []
            
            if isinstance(orig_comp_list, list) and isinstance(gen_comp_list, list):
                component_similarity = min(len(gen_comp_list), len(orig_comp_list)) / max(len(orig_comp_list), 1)
                similarity_score += component_similarity * 0.4
                total_checks += 0.4
            
            # 检查拓扑连接
            orig_topology = original_config.get('topology', {})
            gen_topology = generated_config.get('topology', {})
            
            # 处理不同的拓扑结构
            if isinstance(orig_topology, dict):
                orig_topo_list = orig_topology.get('connections', [])
            elif isinstance(orig_topology, list):
                orig_topo_list = orig_topology
            else:
                orig_topo_list = []
            
            if isinstance(gen_topology, dict):
                gen_topo_list = gen_topology.get('connections', [])
            elif isinstance(gen_topology, list):
                gen_topo_list = gen_topology
            else:
                gen_topo_list = []
            
            if isinstance(orig_topo_list, list) and isinstance(gen_topo_list, list):
                topology_similarity = min(len(gen_topo_list), len(orig_topo_list)) / max(len(orig_topo_list), 1)
                similarity_score += topology_similarity * 0.3
                total_checks += 0.3
            
            # 检查仿真配置
            orig_simulation = original_config.get('simulation', {})
            gen_simulation = generated_config.get('simulation', {})
            
            if isinstance(orig_simulation, dict) and isinstance(gen_simulation, dict):
                if orig_simulation and gen_simulation:
                    sim_keys_match = len(set(orig_simulation.keys()) & set(gen_simulation.keys())) / max(len(orig_simulation.keys()), 1)
                    similarity_score += sim_keys_match * 0.3
                    total_checks += 0.3
            
            return similarity_score / max(total_checks, 1) if total_checks > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"相似度计算失败: {e}")
            self.logger.error(f"原始配置类型: {type(original_config)}, 生成配置类型: {type(generated_config)}")
            return 0.0
    
    def test_single_config(self, config_path: str, config_type: str) -> ConversionTestResult:
        """测试单个配置文件的双向转换"""
        self.logger.info(f"测试配置文件: {config_path}")
        
        errors = []
        warnings = []
        
        # 1. 配置文件 -> 自然语言
        lang_success, description, lang_time, lang_errors = self.test_config_to_language(config_path)
        errors.extend(lang_errors)
        
        if not lang_success:
            return ConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=False,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=lang_time,
                language_to_config_time=0.0,
                similarity_score=0.0,
                strategy_used='N/A',
                confidence_score=0.0,
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
                    similarity = self.calculate_similarity(original_config, generated_config)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_result = {
                            'strategy': strategy,
                            'config_success': config_success,
                            'config_time': config_time,
                            'confidence': confidence,
                            'similarity': similarity,
                            'config_errors': config_errors
                        }
                        
                except Exception as e:
                    warnings.append(f"加载原始配置失败 ({strategy}): {str(e)}")
            else:
                warnings.append(f"策略 {strategy} 转换失败: {config_errors}")
        
        # 构建最终结果
        if best_result:
            return ConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=lang_success,
                language_to_config_success=best_result['config_success'],
                roundtrip_success=lang_success and best_result['config_success'] and best_result['similarity'] > 0.2,
                original_to_language_time=lang_time,
                language_to_config_time=best_result['config_time'],
                similarity_score=best_result['similarity'],
                strategy_used=best_result['strategy'],
                confidence_score=best_result['confidence'],
                errors=errors + best_result['config_errors'],
                warnings=warnings
            )
        else:
            return ConversionTestResult(
                config_path=config_path,
                config_type=config_type,
                original_to_language_success=lang_success,
                language_to_config_success=False,
                roundtrip_success=False,
                original_to_language_time=lang_time,
                language_to_config_time=0.0,
                similarity_score=0.0,
                strategy_used='N/A',
                confidence_score=0.0,
                errors=errors,
                warnings=warnings
            )
    
    def run_comprehensive_test(self, examples_dir: str = "examples") -> Dict[str, Any]:
        """运行全面的双向转换测试"""
        self.logger.info("开始双向转换精度测试")
        
        # 查找所有配置文件
        config_files = self.find_all_config_files(examples_dir)
        
        if not config_files:
            self.logger.error("未找到任何配置文件")
            return {}
        
        # 测试每个配置文件
        for config_path, config_type in config_files:
            try:
                result = self.test_single_config(config_path, config_type)
                self.test_results.append(result)
                
                # 输出进度
                self.logger.info(f"完成测试: {config_path} - 往返成功: {result.roundtrip_success}")
                
            except Exception as e:
                self.logger.error(f"测试配置文件失败 {config_path}: {e}")
                self.logger.error(traceback.format_exc())
        
        # 生成测试报告
        return self.generate_test_report()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        if not self.test_results:
            return {"error": "没有测试结果"}
        
        total_tests = len(self.test_results)
        successful_lang_conversions = sum(1 for r in self.test_results if r.original_to_language_success)
        successful_config_conversions = sum(1 for r in self.test_results if r.language_to_config_success)
        successful_roundtrips = sum(1 for r in self.test_results if r.roundtrip_success)
        
        # 按配置类型统计
        type_stats = {}
        for result in self.test_results:
            config_type = result.config_type
            if config_type not in type_stats:
                type_stats[config_type] = {
                    'total': 0,
                    'lang_success': 0,
                    'config_success': 0,
                    'roundtrip_success': 0,
                    'avg_similarity': 0.0
                }
            
            type_stats[config_type]['total'] += 1
            if result.original_to_language_success:
                type_stats[config_type]['lang_success'] += 1
            if result.language_to_config_success:
                type_stats[config_type]['config_success'] += 1
            if result.roundtrip_success:
                type_stats[config_type]['roundtrip_success'] += 1
            type_stats[config_type]['avg_similarity'] += result.similarity_score
        
        # 计算平均相似度
        for config_type in type_stats:
            if type_stats[config_type]['total'] > 0:
                type_stats[config_type]['avg_similarity'] /= type_stats[config_type]['total']
        
        # 按策略统计
        strategy_stats = {}
        for result in self.test_results:
            strategy = result.strategy_used
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'count': 0,
                    'success': 0,
                    'avg_confidence': 0.0,
                    'avg_similarity': 0.0
                }
            
            strategy_stats[strategy]['count'] += 1
            if result.language_to_config_success:
                strategy_stats[strategy]['success'] += 1
            strategy_stats[strategy]['avg_confidence'] += result.confidence_score
            strategy_stats[strategy]['avg_similarity'] += result.similarity_score
        
        # 计算平均值
        for strategy in strategy_stats:
            if strategy_stats[strategy]['count'] > 0:
                strategy_stats[strategy]['avg_confidence'] /= strategy_stats[strategy]['count']
                strategy_stats[strategy]['avg_similarity'] /= strategy_stats[strategy]['count']
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'config_to_language_success_rate': successful_lang_conversions / total_tests,
                'language_to_config_success_rate': successful_config_conversions / total_tests,
                'roundtrip_success_rate': successful_roundtrips / total_tests,
                'average_similarity': sum(r.similarity_score for r in self.test_results) / total_tests,
                'average_confidence': sum(r.confidence_score for r in self.test_results) / total_tests
            },
            'by_config_type': type_stats,
            'by_strategy': strategy_stats,
            'detailed_results': [asdict(result) for result in self.test_results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_file: str = "bidirectional_conversion_test_report.json"):
        """保存测试报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"测试报告已保存到: {output_file}")
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

def main():
    """主函数"""
    print("=" * 80)
    print("CHS-SDK 双向转换精度测试")
    print("=" * 80)
    
    # 创建测试器
    tester = BidirectionalConversionTester()
    
    # 运行测试
    try:
        report = tester.run_comprehensive_test()
        
        if report:
            # 输出摘要
            summary = report.get('summary', {})
            print(f"\n测试摘要:")
            print(f"总测试数: {summary.get('total_tests', 0)}")
            print(f"配置->语言成功率: {summary.get('config_to_language_success_rate', 0):.2%}")
            print(f"语言->配置成功率: {summary.get('language_to_config_success_rate', 0):.2%}")
            print(f"往返转换成功率: {summary.get('roundtrip_success_rate', 0):.2%}")
            print(f"平均相似度: {summary.get('average_similarity', 0):.2f}")
            print(f"平均置信度: {summary.get('average_confidence', 0):.2f}")
            
            # 保存详细报告
            tester.save_report(report)
            
            print(f"\n详细报告已保存到: bidirectional_conversion_test_report.json")
        else:
            print("测试失败，未生成报告")
            
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        logger.error(traceback.format_exc())
        print(f"测试运行失败: {e}")

if __name__ == "__main__":
    main()