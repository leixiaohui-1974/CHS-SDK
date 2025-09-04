#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精度测试框架
自动化测试各种复杂场景下的转换精度
"""

import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class TestScenario(Enum):
    """测试场景类型"""
    BASIC = "basic"  # 基础场景
    COMPLEX = "complex"  # 复杂场景
    EDGE_CASE = "edge_case"  # 边界情况
    STRESS_TEST = "stress_test"  # 压力测试
    REAL_WORLD = "real_world"  # 真实世界场景
    ADVERSARIAL = "adversarial"  # 对抗性测试

class TestCategory(Enum):
    """测试类别"""
    COMPONENT_RECOGNITION = "component_recognition"
    PARAMETER_EXTRACTION = "parameter_extraction"
    CONNECTION_INFERENCE = "connection_inference"
    UNIT_CONVERSION = "unit_conversion"
    ERROR_CORRECTION = "error_correction"
    OVERALL_ACCURACY = "overall_accuracy"

class TestResult(Enum):
    """测试结果"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"

@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    scenario: TestScenario
    category: TestCategory
    input_text: str
    expected_output: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    difficulty_level: int = 1  # 1-5
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TestExecution:
    """测试执行结果"""
    test_case_id: str
    result: TestResult
    actual_output: Dict[str, Any]
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    processing_time: float
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    executed_at: datetime = field(default_factory=datetime.now)

@dataclass
class TestSuite:
    """测试套件"""
    name: str
    description: str
    test_cases: List[TestCase]
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)

class PrecisionTestingFramework:
    """
    精度测试框架
    自动化测试各种复杂场景下的转换精度
    """
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_suites = {}
        self.test_cases = {}
        self.execution_history = []
        self.performance_baselines = {}
        
        # 初始化测试数据生成器
        self.data_generators = {
            TestCategory.COMPONENT_RECOGNITION: self._generate_component_test_data,
            TestCategory.PARAMETER_EXTRACTION: self._generate_parameter_test_data,
            TestCategory.CONNECTION_INFERENCE: self._generate_connection_test_data,
            TestCategory.UNIT_CONVERSION: self._generate_unit_conversion_test_data,
            TestCategory.ERROR_CORRECTION: self._generate_error_correction_test_data,
            TestCategory.OVERALL_ACCURACY: self._generate_overall_test_data
        }
        
        # 初始化评估器
        self.evaluators = {
            TestCategory.COMPONENT_RECOGNITION: self._evaluate_component_recognition,
            TestCategory.PARAMETER_EXTRACTION: self._evaluate_parameter_extraction,
            TestCategory.CONNECTION_INFERENCE: self._evaluate_connection_inference,
            TestCategory.UNIT_CONVERSION: self._evaluate_unit_conversion,
            TestCategory.ERROR_CORRECTION: self._evaluate_error_correction,
            TestCategory.OVERALL_ACCURACY: self._evaluate_overall_accuracy
        }
        
        # 初始化基准测试数据
        self._initialize_benchmark_data()
        
        logger.info(f"精度测试框架初始化完成，输出目录: {self.output_dir}")
    
    def _initialize_benchmark_data(self):
        """初始化基准测试数据"""
        self.benchmark_data = {
            'component_recognition': {
                'simple_cases': [
                    "主水库的容量为1000万立方米",
                    "1号泵站功率为500kW",
                    "闸门开度调节至60%",
                    "水位传感器显示85.5米"
                ],
                'complex_cases': [
                    "通过调节主干渠首部闸门和分水闸门的开度，控制各支渠的流量分配",
                    "水库-泵站-管道-阀门组成的复合供水系统运行状态良好",
                    "多级泵站串联运行，总扬程达到150米，流量保持在5.2m³/s"
                ],
                'edge_cases': [
                    "备用泵站（型号XYZ-2000）在主泵站故障时自动启动",
                    "临时设置的移动泵车，流量范围0.5-2.0m³/s",
                    "老旧闸门（建于1985年）需要人工操作"
                ]
            },
            'parameter_extraction': {
                'numerical_values': [
                    "流量150.5m³/s",
                    "水位85米",
                    "压力0.8MPa",
                    "效率92.5%",
                    "功率1200kW"
                ],
                'unit_variations': [
                    "流量150500L/s",
                    "水位8500cm",
                    "压力800kPa",
                    "功率1.2MW",
                    "容量100万m³"
                ],
                'complex_expressions': [
                    "流量从120m³/s增加到180m³/s",
                    "水位在82-88米之间波动",
                    "压力不超过1.5MPa",
                    "效率达到95%以上"
                ]
            },
            'connection_inference': {
                'direct_connections': [
                    "水库连接主干渠",
                    "泵站出水管接入配水管网",
                    "闸门控制渠道流量"
                ],
                'implicit_connections': [
                    "水库水位下降，启动补水泵站",
                    "下游需水量增加，调节上游闸门开度",
                    "管道压力异常，关闭相关阀门"
                ],
                'complex_networks': [
                    "多水源联合调度：水库A、水库B通过连通管道实现水量互补",
                    "梯级泵站系统：1级泵站→中间水池→2级泵站→高位水塔"
                ]
            }
        }
    
    def create_test_suite(self, name: str, description: str, tags: List[str] = None) -> TestSuite:
        """创建测试套件"""
        test_suite = TestSuite(
            name=name,
            description=description,
            test_cases=[],
            tags=tags or []
        )
        self.test_suites[name] = test_suite
        return test_suite
    
    def add_test_case(self, suite_name: str, test_case: TestCase):
        """添加测试用例"""
        if suite_name not in self.test_suites:
            raise ValueError(f"测试套件 '{suite_name}' 不存在")
        
        self.test_suites[suite_name].test_cases.append(test_case)
        self.test_cases[test_case.id] = test_case
    
    def generate_comprehensive_test_suite(self) -> TestSuite:
        """生成综合测试套件"""
        suite = self.create_test_suite(
            "comprehensive_precision_test",
            "综合精度测试套件，覆盖所有主要功能和场景",
            ["comprehensive", "precision", "automated"]
        )
        
        # 为每个类别生成测试用例
        for category in TestCategory:
            test_cases = self._generate_test_cases_for_category(category)
            for test_case in test_cases:
                self.add_test_case(suite.name, test_case)
        
        return suite
    
    def _generate_test_cases_for_category(self, category: TestCategory) -> List[TestCase]:
        """为指定类别生成测试用例"""
        generator = self.data_generators[category]
        return generator()
    
    def _generate_component_test_data(self) -> List[TestCase]:
        """生成组件识别测试数据"""
        test_cases = []
        
        # 基础场景
        test_cases.extend([
            TestCase(
                id="comp_basic_001",
                name="基础水库识别",
                description="识别简单的水库组件",
                scenario=TestScenario.BASIC,
                category=TestCategory.COMPONENT_RECOGNITION,
                input_text="主水库容量为5000万立方米",
                expected_output={
                    "components": [{"name": "主水库", "type": "水库", "confidence": 0.95}]
                },
                difficulty_level=1,
                tags=["水库", "基础"]
            ),
            TestCase(
                id="comp_basic_002",
                name="基础泵站识别",
                description="识别简单的泵站组件",
                scenario=TestScenario.BASIC,
                category=TestCategory.COMPONENT_RECOGNITION,
                input_text="1号泵站正常运行，功率800kW",
                expected_output={
                    "components": [{"name": "1号泵站", "type": "泵站", "confidence": 0.95}]
                },
                difficulty_level=1,
                tags=["泵站", "基础"]
            )
        ])
        
        # 复杂场景
        test_cases.extend([
            TestCase(
                id="comp_complex_001",
                name="多组件系统识别",
                description="识别包含多个组件的复杂系统",
                scenario=TestScenario.COMPLEX,
                category=TestCategory.COMPONENT_RECOGNITION,
                input_text="水库-泵站-管道-阀门-水塔组成的供水系统运行正常",
                expected_output={
                    "components": [
                        {"name": "水库", "type": "水库", "confidence": 0.90},
                        {"name": "泵站", "type": "泵站", "confidence": 0.90},
                        {"name": "管道", "type": "管道", "confidence": 0.90},
                        {"name": "阀门", "type": "阀门", "confidence": 0.90},
                        {"name": "水塔", "type": "水塔", "confidence": 0.90}
                    ]
                },
                difficulty_level=3,
                tags=["多组件", "复杂"]
            )
        ])
        
        # 边界情况
        test_cases.extend([
            TestCase(
                id="comp_edge_001",
                name="模糊组件识别",
                description="识别描述模糊的组件",
                scenario=TestScenario.EDGE_CASE,
                category=TestCategory.COMPONENT_RECOGNITION,
                input_text="那个老旧的提水设备需要维修",
                expected_output={
                    "components": [{"name": "提水设备", "type": "泵站", "confidence": 0.70}]
                },
                difficulty_level=4,
                tags=["模糊", "边界"]
            )
        ])
        
        return test_cases
    
    def _generate_parameter_test_data(self) -> List[TestCase]:
        """生成参数提取测试数据"""
        test_cases = []
        
        # 数值参数提取
        test_cases.extend([
            TestCase(
                id="param_basic_001",
                name="基础流量提取",
                description="提取简单的流量参数",
                scenario=TestScenario.BASIC,
                category=TestCategory.PARAMETER_EXTRACTION,
                input_text="当前流量为150.5m³/s",
                expected_output={
                    "parameters": [{
                        "name": "流量",
                        "value": 150.5,
                        "unit": "m³/s",
                        "confidence": 0.95
                    }]
                },
                difficulty_level=1,
                tags=["流量", "基础"]
            ),
            TestCase(
                id="param_complex_001",
                name="复杂参数表达式",
                description="提取复杂的参数表达式",
                scenario=TestScenario.COMPLEX,
                category=TestCategory.PARAMETER_EXTRACTION,
                input_text="流量从120m³/s逐步增加到180m³/s，用时30分钟",
                expected_output={
                    "parameters": [
                        {"name": "初始流量", "value": 120, "unit": "m³/s", "confidence": 0.90},
                        {"name": "最终流量", "value": 180, "unit": "m³/s", "confidence": 0.90},
                        {"name": "调节时间", "value": 30, "unit": "分钟", "confidence": 0.85}
                    ]
                },
                difficulty_level=3,
                tags=["复杂", "时间序列"]
            )
        ])
        
        return test_cases
    
    def _generate_connection_test_data(self) -> List[TestCase]:
        """生成连接推理测试数据"""
        test_cases = []
        
        test_cases.extend([
            TestCase(
                id="conn_basic_001",
                name="基础连接识别",
                description="识别简单的组件连接",
                scenario=TestScenario.BASIC,
                category=TestCategory.CONNECTION_INFERENCE,
                input_text="水库通过主干渠连接到泵站",
                expected_output={
                    "connections": [{
                        "from": "水库",
                        "to": "泵站",
                        "via": "主干渠",
                        "type": "流量连接",
                        "confidence": 0.90
                    }]
                },
                difficulty_level=1,
                tags=["连接", "基础"]
            )
        ])
        
        return test_cases
    
    def _generate_unit_conversion_test_data(self) -> List[TestCase]:
        """生成单位转换测试数据"""
        test_cases = []
        
        test_cases.extend([
            TestCase(
                id="unit_basic_001",
                name="基础单位转换",
                description="测试基础的单位转换",
                scenario=TestScenario.BASIC,
                category=TestCategory.UNIT_CONVERSION,
                input_text="流量150500L/s",
                expected_output={
                    "parameters": [{
                        "name": "流量",
                        "value": 150.5,
                        "unit": "m³/s",
                        "original_value": 150500,
                        "original_unit": "L/s",
                        "confidence": 0.98
                    }]
                },
                difficulty_level=1,
                tags=["单位转换", "基础"]
            )
        ])
        
        return test_cases
    
    def _generate_error_correction_test_data(self) -> List[TestCase]:
        """生成错误修正测试数据"""
        test_cases = []
        
        test_cases.extend([
            TestCase(
                id="error_basic_001",
                name="拼写错误修正",
                description="修正常见的拼写错误",
                scenario=TestScenario.BASIC,
                category=TestCategory.ERROR_CORRECTION,
                input_text="水库流量为150立方米每秒",
                expected_output={
                    "parameters": [{
                        "name": "流量",
                        "value": 150,
                        "unit": "m³/s",
                        "confidence": 0.90
                    }],
                    "corrections": [{
                        "type": "unit_standardization",
                        "original": "立方米每秒",
                        "corrected": "m³/s"
                    }]
                },
                difficulty_level=2,
                tags=["错误修正", "单位"]
            )
        ])
        
        return test_cases
    
    def _generate_overall_test_data(self) -> List[TestCase]:
        """生成整体准确性测试数据"""
        test_cases = []
        
        test_cases.extend([
            TestCase(
                id="overall_001",
                name="综合场景测试",
                description="测试综合场景的整体准确性",
                scenario=TestScenario.REAL_WORLD,
                category=TestCategory.OVERALL_ACCURACY,
                input_text="主水库当前水位85.2米，通过1号泵站（功率1200kW）向城市供水，流量保持在180m³/s",
                expected_output={
                    "components": [
                        {"name": "主水库", "type": "水库"},
                        {"name": "1号泵站", "type": "泵站"}
                    ],
                    "parameters": [
                        {"name": "水位", "value": 85.2, "unit": "m"},
                        {"name": "功率", "value": 1200, "unit": "kW"},
                        {"name": "流量", "value": 180, "unit": "m³/s"}
                    ],
                    "connections": [{
                        "from": "主水库",
                        "to": "城市供水",
                        "via": "1号泵站"
                    }]
                },
                difficulty_level=4,
                tags=["综合", "真实场景"]
            )
        ])
        
        return test_cases
    
    def run_test_suite(self, suite_name: str, target_system: Callable) -> Dict[str, Any]:
        """运行测试套件"""
        if suite_name not in self.test_suites:
            raise ValueError(f"测试套件 '{suite_name}' 不存在")
        
        suite = self.test_suites[suite_name]
        start_time = time.time()
        
        logger.info(f"开始运行测试套件: {suite_name}")
        
        # 执行setup
        if suite.setup_function:
            suite.setup_function()
        
        results = []
        
        try:
            for test_case in suite.test_cases:
                result = self._execute_test_case(test_case, target_system)
                results.append(result)
                self.execution_history.append(result)
        
        finally:
            # 执行teardown
            if suite.teardown_function:
                suite.teardown_function()
        
        execution_time = time.time() - start_time
        
        # 生成测试报告
        report = self._generate_test_report(suite, results, execution_time)
        
        # 保存结果
        self._save_test_results(suite_name, report)
        
        logger.info(f"测试套件 {suite_name} 执行完成，耗时 {execution_time:.2f}秒")
        
        return report
    
    def _execute_test_case(self, test_case: TestCase, target_system: Callable) -> TestExecution:
        """执行单个测试用例"""
        start_time = time.time()
        
        try:
            # 调用目标系统
            actual_output = target_system(test_case.input_text, test_case.context)
            
            # 评估结果
            evaluation = self._evaluate_test_result(test_case, actual_output)
            
            processing_time = time.time() - start_time
            
            return TestExecution(
                test_case_id=test_case.id,
                result=TestResult.PASS if evaluation['accuracy'] >= 0.8 else TestResult.FAIL,
                actual_output=actual_output,
                accuracy=evaluation['accuracy'],
                precision=evaluation['precision'],
                recall=evaluation['recall'],
                f1_score=evaluation['f1_score'],
                processing_time=processing_time,
                warnings=evaluation.get('warnings', [])
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"测试用例 {test_case.id} 执行失败: {e}")
            
            return TestExecution(
                test_case_id=test_case.id,
                result=TestResult.FAIL,
                actual_output={},
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _evaluate_test_result(self, test_case: TestCase, actual_output: Dict[str, Any]) -> Dict[str, Any]:
        """评估测试结果"""
        evaluator = self.evaluators[test_case.category]
        return evaluator(test_case.expected_output, actual_output)
    
    def _evaluate_component_recognition(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估组件识别结果"""
        expected_components = expected.get('components', [])
        actual_components = actual.get('components', [])
        
        if not expected_components:
            return {'accuracy': 1.0, 'precision': 1.0, 'recall': 1.0, 'f1_score': 1.0}
        
        # 计算匹配度
        matches = 0
        for exp_comp in expected_components:
            for act_comp in actual_components:
                if self._components_match(exp_comp, act_comp):
                    matches += 1
                    break
        
        precision = matches / len(actual_components) if actual_components else 0
        recall = matches / len(expected_components) if expected_components else 0
        accuracy = matches / max(len(expected_components), len(actual_components))
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
    
    def _evaluate_parameter_extraction(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估参数提取结果"""
        expected_params = expected.get('parameters', [])
        actual_params = actual.get('parameters', [])
        
        if not expected_params:
            return {'accuracy': 1.0, 'precision': 1.0, 'recall': 1.0, 'f1_score': 1.0}
        
        matches = 0
        for exp_param in expected_params:
            for act_param in actual_params:
                if self._parameters_match(exp_param, act_param):
                    matches += 1
                    break
        
        precision = matches / len(actual_params) if actual_params else 0
        recall = matches / len(expected_params) if expected_params else 0
        accuracy = matches / max(len(expected_params), len(actual_params))
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
    
    def _evaluate_connection_inference(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估连接推理结果"""
        expected_connections = expected.get('connections', [])
        actual_connections = actual.get('connections', [])
        
        if not expected_connections:
            return {'accuracy': 1.0, 'precision': 1.0, 'recall': 1.0, 'f1_score': 1.0}
        
        matches = 0
        for exp_conn in expected_connections:
            for act_conn in actual_connections:
                if self._connections_match(exp_conn, act_conn):
                    matches += 1
                    break
        
        precision = matches / len(actual_connections) if actual_connections else 0
        recall = matches / len(expected_connections) if expected_connections else 0
        accuracy = matches / max(len(expected_connections), len(actual_connections))
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
    
    def _evaluate_unit_conversion(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估单位转换结果"""
        return self._evaluate_parameter_extraction(expected, actual)
    
    def _evaluate_error_correction(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估错误修正结果"""
        # 综合评估参数提取和错误修正
        param_eval = self._evaluate_parameter_extraction(expected, actual)
        
        # 检查是否有修正信息
        expected_corrections = expected.get('corrections', [])
        actual_corrections = actual.get('corrections', [])
        
        correction_accuracy = 1.0
        if expected_corrections:
            correction_matches = 0
            for exp_corr in expected_corrections:
                for act_corr in actual_corrections:
                    if exp_corr.get('type') == act_corr.get('type'):
                        correction_matches += 1
                        break
            correction_accuracy = correction_matches / len(expected_corrections)
        
        # 综合评分
        overall_accuracy = (param_eval['accuracy'] + correction_accuracy) / 2
        
        return {
            'accuracy': overall_accuracy,
            'precision': param_eval['precision'],
            'recall': param_eval['recall'],
            'f1_score': param_eval['f1_score']
        }
    
    def _evaluate_overall_accuracy(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估整体准确性"""
        evaluations = []
        
        # 评估各个方面
        if 'components' in expected:
            comp_eval = self._evaluate_component_recognition(
                {'components': expected['components']},
                {'components': actual.get('components', [])}
            )
            evaluations.append(comp_eval)
        
        if 'parameters' in expected:
            param_eval = self._evaluate_parameter_extraction(
                {'parameters': expected['parameters']},
                {'parameters': actual.get('parameters', [])}
            )
            evaluations.append(param_eval)
        
        if 'connections' in expected:
            conn_eval = self._evaluate_connection_inference(
                {'connections': expected['connections']},
                {'connections': actual.get('connections', [])}
            )
            evaluations.append(conn_eval)
        
        if not evaluations:
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
        
        # 计算平均值
        avg_accuracy = np.mean([e['accuracy'] for e in evaluations])
        avg_precision = np.mean([e['precision'] for e in evaluations])
        avg_recall = np.mean([e['recall'] for e in evaluations])
        avg_f1_score = np.mean([e['f1_score'] for e in evaluations])
        
        return {
            'accuracy': avg_accuracy,
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': avg_f1_score
        }
    
    def _components_match(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """检查组件是否匹配"""
        name_match = expected.get('name', '').lower() in actual.get('name', '').lower() or \
                    actual.get('name', '').lower() in expected.get('name', '').lower()
        type_match = expected.get('type', '') == actual.get('type', '')
        
        return name_match and type_match
    
    def _parameters_match(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """检查参数是否匹配"""
        name_match = expected.get('name', '') == actual.get('name', '')
        value_match = abs(expected.get('value', 0) - actual.get('value', 0)) < 0.01
        unit_match = expected.get('unit', '') == actual.get('unit', '')
        
        return name_match and value_match and unit_match
    
    def _connections_match(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """检查连接是否匹配"""
        from_match = expected.get('from', '') == actual.get('from', '')
        to_match = expected.get('to', '') == actual.get('to', '')
        
        return from_match and to_match
    
    def _generate_test_report(self, suite: TestSuite, results: List[TestExecution], execution_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r.result == TestResult.PASS])
        failed_tests = len([r for r in results if r.result == TestResult.FAIL])
        
        avg_accuracy = np.mean([r.accuracy for r in results]) if results else 0
        avg_precision = np.mean([r.precision for r in results]) if results else 0
        avg_recall = np.mean([r.recall for r in results]) if results else 0
        avg_f1_score = np.mean([r.f1_score for r in results]) if results else 0
        avg_processing_time = np.mean([r.processing_time for r in results]) if results else 0
        
        # 按类别统计
        category_stats = {}
        for category in TestCategory:
            category_results = [r for r in results if self.test_cases[r.test_case_id].category == category]
            if category_results:
                category_stats[category.value] = {
                    'total': len(category_results),
                    'passed': len([r for r in category_results if r.result == TestResult.PASS]),
                    'avg_accuracy': np.mean([r.accuracy for r in category_results]),
                    'avg_processing_time': np.mean([r.processing_time for r in category_results])
                }
        
        # 按难度统计
        difficulty_stats = {}
        for level in range(1, 6):
            level_results = [r for r in results if self.test_cases[r.test_case_id].difficulty_level == level]
            if level_results:
                difficulty_stats[f'level_{level}'] = {
                    'total': len(level_results),
                    'passed': len([r for r in level_results if r.result == TestResult.PASS]),
                    'avg_accuracy': np.mean([r.accuracy for r in level_results])
                }
        
        report = {
            'suite_info': {
                'name': suite.name,
                'description': suite.description,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'avg_accuracy': avg_accuracy,
                'avg_precision': avg_precision,
                'avg_recall': avg_recall,
                'avg_f1_score': avg_f1_score,
                'avg_processing_time': avg_processing_time
            },
            'category_breakdown': category_stats,
            'difficulty_breakdown': difficulty_stats,
            'detailed_results': [{
                'test_case_id': r.test_case_id,
                'test_name': self.test_cases[r.test_case_id].name,
                'result': r.result.value,
                'accuracy': r.accuracy,
                'precision': r.precision,
                'recall': r.recall,
                'f1_score': r.f1_score,
                'processing_time': r.processing_time,
                'error_message': r.error_message,
                'warnings': r.warnings
            } for r in results],
            'performance_analysis': self._analyze_performance(results),
            'recommendations': self._generate_recommendations(results)
        }
        
        return report
    
    def _analyze_performance(self, results: List[TestExecution]) -> Dict[str, Any]:
        """分析性能"""
        if not results:
            return {}
        
        accuracies = [r.accuracy for r in results]
        processing_times = [r.processing_time for r in results]
        
        return {
            'accuracy_distribution': {
                'min': min(accuracies),
                'max': max(accuracies),
                'mean': np.mean(accuracies),
                'std': np.std(accuracies),
                'percentiles': {
                    '25th': np.percentile(accuracies, 25),
                    '50th': np.percentile(accuracies, 50),
                    '75th': np.percentile(accuracies, 75),
                    '95th': np.percentile(accuracies, 95)
                }
            },
            'processing_time_distribution': {
                'min': min(processing_times),
                'max': max(processing_times),
                'mean': np.mean(processing_times),
                'std': np.std(processing_times)
            },
            'correlation_analysis': {
                'accuracy_vs_time': np.corrcoef(accuracies, processing_times)[0, 1]
            }
        }
    
    def _generate_recommendations(self, results: List[TestExecution]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        avg_accuracy = np.mean([r.accuracy for r in results]) if results else 0
        avg_processing_time = np.mean([r.processing_time for r in results]) if results else 0
        
        if avg_accuracy < 0.9:
            recommendations.append("整体准确率偏低，建议优化算法精度")
        
        if avg_processing_time > 1.0:
            recommendations.append("处理时间较长，建议优化性能")
        
        failed_results = [r for r in results if r.result == TestResult.FAIL]
        if len(failed_results) > len(results) * 0.1:
            recommendations.append("失败率较高，建议检查错误处理机制")
        
        # 按类别分析
        category_issues = []
        for category in TestCategory:
            category_results = [r for r in results if self.test_cases[r.test_case_id].category == category]
            if category_results:
                category_accuracy = np.mean([r.accuracy for r in category_results])
                if category_accuracy < 0.85:
                    category_issues.append(category.value)
        
        if category_issues:
            recommendations.append(f"以下类别需要重点改进: {', '.join(category_issues)}")
        
        return recommendations
    
    def _save_test_results(self, suite_name: str, report: Dict[str, Any]):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{suite_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"测试结果已保存到: {filepath}")
    
    def generate_performance_charts(self, report: Dict[str, Any], output_file: str = None):
        """生成性能图表"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"performance_charts_{timestamp}.png"
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 准确率分布
        detailed_results = report['detailed_results']
        accuracies = [r['accuracy'] for r in detailed_results]
        
        axes[0, 0].hist(accuracies, bins=20, alpha=0.7, color='blue')
        axes[0, 0].set_title('准确率分布')
        axes[0, 0].set_xlabel('准确率')
        axes[0, 0].set_ylabel('频次')
        
        # 各类别性能
        categories = list(report['category_breakdown'].keys())
        category_accuracies = [report['category_breakdown'][cat]['avg_accuracy'] for cat in categories]
        
        axes[0, 1].bar(categories, category_accuracies, color='green', alpha=0.7)
        axes[0, 1].set_title('各类别平均准确率')
        axes[0, 1].set_ylabel('准确率')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 难度级别性能
        if 'difficulty_breakdown' in report:
            difficulties = list(report['difficulty_breakdown'].keys())
            difficulty_accuracies = [report['difficulty_breakdown'][diff]['avg_accuracy'] for diff in difficulties]
            
            axes[1, 0].bar(difficulties, difficulty_accuracies, color='orange', alpha=0.7)
            axes[1, 0].set_title('各难度级别平均准确率')
            axes[1, 0].set_ylabel('准确率')
        
        # 处理时间分布
        processing_times = [r['processing_time'] for r in detailed_results]
        
        axes[1, 1].hist(processing_times, bins=20, alpha=0.7, color='red')
        axes[1, 1].set_title('处理时间分布')
        axes[1, 1].set_xlabel('处理时间 (秒)')
        axes[1, 1].set_ylabel('频次')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"性能图表已保存到: {output_file}")
    
    def run_benchmark_test(self, target_system: Callable) -> Dict[str, Any]:
        """运行基准测试"""
        # 生成综合测试套件
        suite = self.generate_comprehensive_test_suite()
        
        # 运行测试
        report = self.run_test_suite(suite.name, target_system)
        
        # 生成图表
        self.generate_performance_charts(report)
        
        # 与基准比较
        if self.performance_baselines:
            comparison = self._compare_with_baseline(report)
            report['baseline_comparison'] = comparison
        
        return report
    
    def _compare_with_baseline(self, current_report: Dict[str, Any]) -> Dict[str, Any]:
        """与基准比较"""
        # 简化的基准比较逻辑
        baseline_accuracy = 0.85  # 假设基准准确率
        current_accuracy = current_report['summary']['avg_accuracy']
        
        improvement = current_accuracy - baseline_accuracy
        
        return {
            'baseline_accuracy': baseline_accuracy,
            'current_accuracy': current_accuracy,
            'improvement': improvement,
            'improvement_percentage': (improvement / baseline_accuracy) * 100 if baseline_accuracy > 0 else 0
        }
    
    def set_performance_baseline(self, report: Dict[str, Any]):
        """设置性能基准"""
        self.performance_baselines = {
            'accuracy': report['summary']['avg_accuracy'],
            'precision': report['summary']['avg_precision'],
            'recall': report['summary']['avg_recall'],
            'f1_score': report['summary']['avg_f1_score'],
            'processing_time': report['summary']['avg_processing_time'],
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存基准
        baseline_file = self.output_dir / "performance_baseline.json"
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(self.performance_baselines, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能基准已设置并保存到: {baseline_file}")

# 使用示例
if __name__ == "__main__":
    # 创建测试框架
    framework = PrecisionTestingFramework()
    
    # 模拟目标系统
    def mock_target_system(input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """模拟目标系统"""
        # 简化的模拟实现
        return {
            'components': [{'name': '水库', 'type': '水库', 'confidence': 0.9}],
            'parameters': [{'name': '流量', 'value': 150, 'unit': 'm³/s', 'confidence': 0.95}],
            'connections': []
        }
    
    # 运行基准测试
    report = framework.run_benchmark_test(mock_target_system)
    
    print("基准测试完成!")
    print(f"总体准确率: {report['summary']['avg_accuracy']:.3f}")
    print(f"通过率: {report['summary']['pass_rate']:.3f}")
    print(f"平均处理时间: {report['summary']['avg_processing_time']:.3f}秒")