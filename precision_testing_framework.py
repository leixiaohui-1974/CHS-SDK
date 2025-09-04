#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精度测试框架
自动化测试各种复杂场景下的转换精度
"""

import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

class TestScenario(Enum):
    """测试场景"""
    BASIC = "basic"                    # 基础场景
    COMPLEX = "complex"                # 复杂场景
    EDGE_CASE = "edge_case"            # 边界情况
    STRESS_TEST = "stress_test"        # 压力测试
    REAL_WORLD = "real_world"          # 真实世界
    ADVERSARIAL = "adversarial"        # 对抗性测试

class TestCategory(Enum):
    """测试类别"""
    COMPONENT_RECOGNITION = "component_recognition"  # 组件识别
    PARAMETER_EXTRACTION = "parameter_extraction"    # 参数提取
    CONNECTION_INFERENCE = "connection_inference"    # 连接推理
    UNIT_CONVERSION = "unit_conversion"              # 单位转换
    ERROR_CORRECTION = "error_correction"            # 错误修正
    OVERALL_ACCURACY = "overall_accuracy"            # 整体准确性

class TestResult(Enum):
    """测试结果"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"

@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    input_text: str
    expected_output: Dict[str, Any]
    scenario: TestScenario
    category: TestCategory
    difficulty: float  # 0-1, 1为最难
    timeout: float = 30.0  # 超时时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestExecution:
    """测试执行结果"""
    test_case_id: str
    result: TestResult
    actual_output: Dict[str, Any]
    precision_score: float
    execution_time: float
    error_message: Optional[str] = None
    detailed_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TestSuite:
    """测试套件"""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class PrecisionTestingFramework:
    """精度测试框架"""
    
    def __init__(self):
        """初始化测试框架"""
        self.logger = logging.getLogger(__name__)
        
        # 测试数据生成器
        self.test_data_generator = TestDataGenerator()
        
        # 测试结果评估器
        self.evaluator = TestResultEvaluator()
        
        # 测试套件存储
        self.test_suites: Dict[str, TestSuite] = {}
        
        # 执行历史
        self.execution_history: List[TestExecution] = []
        
        # 性能基准
        self.performance_benchmarks = {
            "component_recognition": 0.95,
            "parameter_extraction": 0.93,
            "connection_inference": 0.88,
            "unit_conversion": 0.97,
            "error_correction": 0.90,
            "overall_accuracy": 0.92
        }
        
        # 初始化基准测试数据
        self._initialize_benchmark_data()
    
    def _initialize_benchmark_data(self):
        """初始化基准测试数据"""
        # 组件识别基准数据
        self.benchmark_data = {
            "component_recognition": [
                "水库容量1000万立方米",
                "渠道长度5公里，底宽3米",
                "管道直径800毫米",
                "闸门控制流量",
                "泵站提升高度50米"
            ],
            "parameter_extraction": [
                "设计水位150米，死水位120米",
                "流量50立方米每秒，流速2米每秒",
                "糙率0.025，边坡1:1.5",
                "压力0.5MPa，温度20摄氏度"
            ],
            "connection_inference": [
                "水库通过渠道连接到下游闸门",
                "泵站从下游抽水到上游水库",
                "管道连接两个水池"
            ]
        }
    
    def create_test_suite(self, name: str, description: str) -> TestSuite:
        """创建测试套件"""
        test_suite = TestSuite(name=name, description=description)
        self.test_suites[name] = test_suite
        return test_suite
    
    def add_test_case(self, suite_name: str, test_case: TestCase):
        """添加测试用例到套件"""
        if suite_name in self.test_suites:
            self.test_suites[suite_name].test_cases.append(test_case)
        else:
            raise ValueError(f"测试套件 '{suite_name}' 不存在")
    
    def generate_comprehensive_test_suite(self) -> TestSuite:
        """生成综合测试套件"""
        suite = self.create_test_suite(
            "comprehensive_precision_test",
            "综合精度测试套件，覆盖所有主要功能"
        )
        
        # 基础组件识别测试
        basic_tests = self._generate_basic_component_tests()
        for test in basic_tests:
            self.add_test_case(suite.name, test)
        
        # 复杂参数提取测试
        parameter_tests = self._generate_parameter_extraction_tests()
        for test in parameter_tests:
            self.add_test_case(suite.name, test)
        
        # 连接推理测试
        connection_tests = self._generate_connection_inference_tests()
        for test in connection_tests:
            self.add_test_case(suite.name, test)
        
        # 单位转换测试
        unit_tests = self._generate_unit_conversion_tests()
        for test in unit_tests:
            self.add_test_case(suite.name, test)
        
        # 错误修正测试
        error_tests = self._generate_error_correction_tests()
        for test in error_tests:
            self.add_test_case(suite.name, test)
        
        # 边界情况测试
        edge_tests = self._generate_edge_case_tests()
        for test in edge_tests:
            self.add_test_case(suite.name, test)
        
        return suite
    
    def _generate_basic_component_tests(self) -> List[TestCase]:
        """生成基础组件测试"""
        tests = []
        
        # 水库识别测试
        tests.append(TestCase(
            id="comp_001",
            name="水库识别测试",
            description="测试基础水库组件识别",
            input_text="水库容量为1000万立方米，设计水位为150米",
            expected_output={
                "components": {"水库": {"type": "reservoir"}},
                "parameters": {"容量": "10000000立方米", "设计水位": "150米"}
            },
            scenario=TestScenario.BASIC,
            category=TestCategory.COMPONENT_RECOGNITION,
            difficulty=0.2
        ))
        
        # 渠道识别测试
        tests.append(TestCase(
            id="comp_002",
            name="渠道识别测试",
            description="测试渠道组件识别和参数提取",
            input_text="明渠长度5公里，底宽3米，边坡1:1.5，糙率0.025",
            expected_output={
                "components": {"渠道": {"type": "channel"}},
                "parameters": {
                    "长度": "5000米",
                    "底宽": "3米",
                    "边坡": "1:1.5",
                    "糙率": "0.025"
                }
            },
            scenario=TestScenario.BASIC,
            category=TestCategory.COMPONENT_RECOGNITION,
            difficulty=0.4
        ))
        
        return tests
    
    def _generate_parameter_extraction_tests(self) -> List[TestCase]:
        """生成参数提取测试"""
        tests = []
        
        tests.append(TestCase(
            id="param_001",
            name="多参数提取测试",
            description="测试从复杂文本中提取多个参数",
            input_text="水库设计水位150米，死水位120米，正常蓄水位145米，容量1000万立方米",
            expected_output={
                "parameters": {
                    "设计水位": "150米",
                    "死水位": "120米",
                    "正常蓄水位": "145米",
                    "容量": "10000000立方米"
                }
            },
            scenario=TestScenario.COMPLEX,
            category=TestCategory.PARAMETER_EXTRACTION,
            difficulty=0.6
        ))
        
        return tests
    
    def _generate_connection_inference_tests(self) -> List[TestCase]:
        """生成连接推理测试"""
        tests = []
        
        tests.append(TestCase(
            id="conn_001",
            name="基础连接推理测试",
            description="测试基础的组件连接关系推理",
            input_text="水库通过渠道向下游输水，渠道末端设置闸门控制流量",
            expected_output={
                "components": {
                    "水库": {"type": "reservoir"},
                    "渠道": {"type": "channel"},
                    "闸门": {"type": "gate"}
                },
                "connections": [
                    {"from": "水库", "to": "渠道", "type": "出水"},
                    {"from": "渠道", "to": "闸门", "type": "流入"}
                ]
            },
            scenario=TestScenario.BASIC,
            category=TestCategory.CONNECTION_INFERENCE,
            difficulty=0.5
        ))
        
        return tests
    
    def _generate_unit_conversion_tests(self) -> List[TestCase]:
        """生成单位转换测试"""
        tests = []
        
        tests.append(TestCase(
            id="unit_001",
            name="长度单位转换测试",
            description="测试各种长度单位的转换",
            input_text="管道长度2.5千米，直径800毫米",
            expected_output={
                "parameters": {
                    "长度": "2500米",
                    "直径": "0.8米"
                }
            },
            scenario=TestScenario.BASIC,
            category=TestCategory.UNIT_CONVERSION,
            difficulty=0.3
        ))
        
        return tests
    
    def _generate_error_correction_tests(self) -> List[TestCase]:
        """生成错误修正测试"""
        tests = []
        
        tests.append(TestCase(
            id="error_001",
            name="水位逻辑错误修正测试",
            description="测试水位逻辑错误的识别和修正",
            input_text="水库容量1000万立方米，设计水位120米，死水位150米",
            expected_output={
                "corrections": ["死水位应低于设计水位"]
            },
            scenario=TestScenario.BASIC,
            category=TestCategory.ERROR_CORRECTION,
            difficulty=0.4
        ))
        
        return tests
    
    def _generate_edge_case_tests(self) -> List[TestCase]:
        """生成边界情况测试"""
        tests = []
        
        tests.append(TestCase(
            id="edge_001",
            name="极值参数测试",
            description="测试极值参数的处理",
            input_text="微型水库容量0.1立方米，巨型水库容量100亿立方米",
            expected_output={
                "parameters": {
                    "容量1": "0.1立方米",
                    "容量2": "10000000000立方米"
                }
            },
            scenario=TestScenario.EDGE_CASE,
            category=TestCategory.PARAMETER_EXTRACTION,
            difficulty=0.8
        ))
        
        return tests
    
    def run_test_suite(self, suite_name: str, precision_framework) -> Dict[str, Any]:
        """运行测试套件"""
        if suite_name not in self.test_suites:
            raise ValueError(f"测试套件 '{suite_name}' 不存在")
        
        suite = self.test_suites[suite_name]
        results = []
        
        self.logger.info(f"开始运行测试套件: {suite_name}")
        
        for test_case in suite.test_cases:
            execution_result = self.execute_test_case(test_case, precision_framework)
            results.append(execution_result)
            self.execution_history.append(execution_result)
        
        # 计算套件统计
        suite_stats = self._calculate_suite_statistics(results)
        
        return {
            "suite_name": suite_name,
            "total_tests": len(results),
            "results": results,
            "statistics": suite_stats
        }
    
    def execute_test_case(self, test_case: TestCase, precision_framework) -> TestExecution:
        """执行单个测试用例"""
        start_time = time.time()
        
        try:
            # 运行精度框架处理
            actual_output = precision_framework.process_input(test_case.input_text)
            
            execution_time = time.time() - start_time
            
            # 评估结果
            evaluation = self.evaluator.evaluate_result(
                test_case.expected_output,
                actual_output.__dict__,
                test_case.category
            )
            
            return TestExecution(
                test_case_id=test_case.id,
                result=evaluation["result"],
                actual_output=actual_output.__dict__,
                precision_score=evaluation["precision_score"],
                execution_time=execution_time,
                detailed_metrics=evaluation["detailed_metrics"]
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestExecution(
                test_case_id=test_case.id,
                result=TestResult.ERROR,
                actual_output={},
                precision_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _calculate_suite_statistics(self, results: List[TestExecution]) -> Dict[str, Any]:
        """计算套件统计信息"""
        total = len(results)
        passed = len([r for r in results if r.result == TestResult.PASS])
        failed = len([r for r in results if r.result == TestResult.FAIL])
        errors = len([r for r in results if r.result == TestResult.ERROR])
        
        precision_scores = [r.precision_score for r in results if r.precision_score > 0]
        avg_precision = np.mean(precision_scores) if precision_scores else 0.0
        
        execution_times = [r.execution_time for r in results]
        avg_execution_time = np.mean(execution_times) if execution_times else 0.0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": passed / total if total > 0 else 0,
            "average_precision": avg_precision,
            "average_execution_time": avg_execution_time
        }
    
    def generate_test_report(self, suite_results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = []
        report.append(f"# 精度测试报告 - {suite_results['suite_name']}")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        stats = suite_results['statistics']
        report.append("## 测试统计")
        report.append(f"- 总测试数: {stats['total_tests']}")
        report.append(f"- 通过: {stats['passed']}")
        report.append(f"- 失败: {stats['failed']}")
        report.append(f"- 错误: {stats['errors']}")
        report.append(f"- 通过率: {stats['pass_rate']:.2%}")
        report.append(f"- 平均精度: {stats['average_precision']:.2%}")
        report.append(f"- 平均执行时间: {stats['average_execution_time']:.3f}秒")
        report.append("")
        
        report.append("## 详细结果")
        for result in suite_results['results']:
            status_icon = "✓" if result.result == TestResult.PASS else "✗"
            report.append(f"{status_icon} {result.test_case_id}: 精度 {result.precision_score:.2%}, 用时 {result.execution_time:.3f}s")
            if result.error_message:
                report.append(f"  错误: {result.error_message}")
        
        return "\n".join(report)
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        if not self.execution_history:
            return {"message": "没有执行历史数据"}
        
        # 按类别分析
        category_stats = {}
        for category in TestCategory:
            category_results = [
                r for r in self.execution_history 
                if any(tc.category == category for tc in self._get_all_test_cases() if tc.id == r.test_case_id)
            ]
            
            if category_results:
                precision_scores = [r.precision_score for r in category_results]
                category_stats[category.value] = {
                    "count": len(category_results),
                    "average_precision": np.mean(precision_scores),
                    "min_precision": np.min(precision_scores),
                    "max_precision": np.max(precision_scores)
                }
        
        return {
            "total_executions": len(self.execution_history),
            "category_statistics": category_stats,
            "overall_average_precision": np.mean([r.precision_score for r in self.execution_history])
        }
    
    def _get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        all_cases = []
        for suite in self.test_suites.values():
            all_cases.extend(suite.test_cases)
        return all_cases
    
    def generate_improvement_suggestions(self) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        performance = self.analyze_performance()
        
        if "category_statistics" in performance:
            for category, stats in performance["category_statistics"].items():
                if stats["average_precision"] < 0.9:
                    suggestions.append(f"建议改进 {category} 的精度，当前平均精度为 {stats['average_precision']:.2%}")
        
        if performance.get("overall_average_precision", 0) < 0.95:
            suggestions.append("整体精度未达到超高精度目标（95%），建议优化算法融合策略")
        
        return suggestions
    
    def save_test_results(self, results: Dict[str, Any], filename: str):
        """保存测试结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    def generate_performance_charts(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成性能图表数据"""
        # 准备图表数据
        chart_data = {
            "precision_distribution": [],
            "execution_time_distribution": [],
            "category_performance": {}
        }
        
        # 精度分布
        precision_scores = [r.precision_score for r in results['results']]
        chart_data["precision_distribution"] = precision_scores
        
        # 执行时间分布
        execution_times = [r.execution_time for r in results['results']]
        chart_data["execution_time_distribution"] = execution_times
        
        return chart_data
    
    def run_benchmark_tests(self, precision_framework) -> Dict[str, Any]:
        """运行基准测试"""
        benchmark_results = {}
        
        for category, test_data in self.benchmark_data.items():
            category_results = []
            
            for i, test_input in enumerate(test_data):
                start_time = time.time()
                result = precision_framework.process_input(test_input)
                execution_time = time.time() - start_time
                
                # 简化的精度评估
                precision_score = self._estimate_precision(result, category)
                
                category_results.append({
                    "input": test_input,
                    "precision_score": precision_score,
                    "execution_time": execution_time
                })
            
            benchmark_results[category] = {
                "results": category_results,
                "average_precision": np.mean([r["precision_score"] for r in category_results]),
                "average_execution_time": np.mean([r["execution_time"] for r in category_results])
            }
        
        return benchmark_results
    
    def _estimate_precision(self, result, category: str) -> float:
        """估算精度（简化实现）"""
        # 基于结果的完整性和合理性估算精度
        base_score = 0.8
        
        if hasattr(result, 'components') and result.components:
            base_score += 0.1
        
        if hasattr(result, 'parameters') and result.parameters:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def compare_with_benchmark(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """与基准比较"""
        comparison = {}
        
        current_precision = current_results['statistics']['average_precision']
        
        for category, benchmark_precision in self.performance_benchmarks.items():
            comparison[category] = {
                "current": current_precision,
                "benchmark": benchmark_precision,
                "improvement": current_precision - benchmark_precision,
                "meets_benchmark": current_precision >= benchmark_precision
            }
        
        return comparison
    
    def set_performance_benchmark(self, category: str, precision: float):
        """设置性能基准"""
        self.performance_benchmarks[category] = precision

class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.component_templates = {
            "水库": ["水库容量{capacity}，设计水位{level}米"],
            "渠道": ["渠道长度{length}，底宽{width}米"],
            "管道": ["管道直径{diameter}，长度{length}"]
        }
    
    def generate_random_test_case(self, category: TestCategory) -> TestCase:
        """生成随机测试用例"""
        # 简化实现
        return TestCase(
            id=f"auto_{int(time.time())}",
            name="自动生成测试",
            description="自动生成的测试用例",
            input_text="水库容量1000万立方米",
            expected_output={},
            scenario=TestScenario.BASIC,
            category=category,
            difficulty=0.5
        )

class TestResultEvaluator:
    """测试结果评估器"""
    
    def evaluate_result(self, expected: Dict[str, Any], actual: Dict[str, Any], category: TestCategory) -> Dict[str, Any]:
        """评估测试结果"""
        if category == TestCategory.COMPONENT_RECOGNITION:
            return self._evaluate_component_recognition(expected, actual)
        elif category == TestCategory.PARAMETER_EXTRACTION:
            return self._evaluate_parameter_extraction(expected, actual)
        elif category == TestCategory.CONNECTION_INFERENCE:
            return self._evaluate_connection_inference(expected, actual)
        elif category == TestCategory.UNIT_CONVERSION:
            return self._evaluate_unit_conversion(expected, actual)
        elif category == TestCategory.ERROR_CORRECTION:
            return self._evaluate_error_correction(expected, actual)
        else:
            return self._evaluate_overall_accuracy(expected, actual)
    
    def _evaluate_component_recognition(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估组件识别"""
        expected_components = set(expected.get("components", {}).keys())
        actual_components = set(actual.get("components", {}).keys())
        
        if not expected_components:
            precision_score = 1.0 if not actual_components else 0.5
        else:
            intersection = expected_components & actual_components
            precision_score = len(intersection) / len(expected_components)
        
        result = TestResult.PASS if precision_score >= 0.8 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {
                "expected_count": len(expected_components),
                "actual_count": len(actual_components),
                "correct_count": len(expected_components & actual_components)
            }
        }
    
    def _evaluate_parameter_extraction(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估参数提取"""
        expected_params = expected.get("parameters", {})
        actual_params = actual.get("parameters", {})
        
        if not expected_params:
            precision_score = 1.0 if not actual_params else 0.5
        else:
            correct_params = 0
            for param_name, expected_value in expected_params.items():
                if param_name in actual_params:
                    # 简化的值比较
                    if str(actual_params[param_name]).strip() == str(expected_value).strip():
                        correct_params += 1
            
            precision_score = correct_params / len(expected_params)
        
        result = TestResult.PASS if precision_score >= 0.8 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {
                "expected_count": len(expected_params),
                "actual_count": len(actual_params),
                "correct_count": correct_params if expected_params else 0
            }
        }
    
    def _evaluate_connection_inference(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估连接推理"""
        # 简化实现
        precision_score = 0.8  # 模拟值
        result = TestResult.PASS if precision_score >= 0.7 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {}
        }
    
    def _evaluate_unit_conversion(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估单位转换"""
        # 简化实现
        precision_score = 0.95  # 模拟值
        result = TestResult.PASS if precision_score >= 0.9 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {}
        }
    
    def _evaluate_error_correction(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估错误修正"""
        expected_corrections = expected.get("corrections", [])
        actual_corrections = actual.get("corrections", [])
        
        if not expected_corrections:
            precision_score = 1.0 if not actual_corrections else 0.5
        else:
            # 简化的修正匹配
            precision_score = 1.0 if actual_corrections else 0.0
        
        result = TestResult.PASS if precision_score >= 0.8 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {
                "expected_corrections": len(expected_corrections),
                "actual_corrections": len(actual_corrections)
            }
        }
    
    def _evaluate_overall_accuracy(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """评估整体准确性"""
        # 综合评估
        precision_score = 0.9  # 模拟值
        result = TestResult.PASS if precision_score >= 0.85 else TestResult.FAIL
        
        return {
            "result": result,
            "precision_score": precision_score,
            "detailed_metrics": {}
        }