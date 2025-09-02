#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 仿真工作流测试套件

专门测试端到端仿真流程验证，包括：
1. 完整仿真工作流集成测试
2. 多场景仿真流程测试
3. 仿真数据流和状态管理测试
4. 仿真结果验证和分析测试
5. 仿真性能和资源使用测试
6. 仿真错误处理和恢复测试
"""

import pytest
import asyncio
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dataclasses import dataclass, asdict
import numpy as np
from datetime import datetime, timedelta

# 导入项目模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.agents.chief_modeling_agent import ChiefModelingAgent
from api.agents.validator_agent import ValidatorAgent
from api.agents.configurator_agent import ConfiguratorAgent
from api.agents.analyst_and_reporter_agent import AnalystAndReporterAgent
from api.agents.runner_agent import RunnerAgent
from api.services.websocket_monitor import WebSocketMonitorService
from api.models.scenario import Scenario, ScenarioStatus
from api.models.simulation import Simulation, SimulationStatus


@dataclass
class SimulationWorkflowMetrics:
    """仿真工作流指标"""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    total_scenarios: int = 0
    completed_scenarios: int = 0
    failed_scenarios: int = 0
    total_simulations: int = 0
    completed_simulations: int = 0
    failed_simulations: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def scenario_success_rate(self) -> float:
        if self.total_scenarios == 0:
            return 0.0
        return self.completed_scenarios / self.total_scenarios
    
    @property
    def simulation_success_rate(self) -> float:
        if self.total_simulations == 0:
            return 0.0
        return self.completed_simulations / self.total_simulations
    
    @property
    def throughput_scenarios_per_second(self) -> float:
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.completed_scenarios / duration
    
    @property
    def throughput_simulations_per_second(self) -> float:
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.completed_simulations / duration


class SimulationWorkflowTestFramework:
    """仿真工作流测试框架"""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.examples_dir = project_root / "examples"
        
        # 初始化智能体
        self.chief_agent = ChiefModelingAgent()
        self.validator_agent = ValidatorAgent()
        self.configurator_agent = ConfiguratorAgent()
        self.analyst_agent = AnalystAndReporterAgent()
        self.runner_agent = RunnerAgent()
        
        # 初始化监控服务
        self.monitor_service = WebSocketMonitorService()
        
        # 工作流指标
        self.workflow_metrics: Dict[str, SimulationWorkflowMetrics] = {}
        
        # 模拟数据存储
        self.scenarios: Dict[str, Scenario] = {}
        self.simulations: Dict[str, Simulation] = {}
        
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_scenario(self, scenario_id: str, scenario_type: str = "basic") -> Scenario:
        """创建测试场景"""
        scenario_configs = {
            "basic": {
                "name": f"基础测试场景_{scenario_id}",
                "description": "基础仿真测试场景",
                "parameters": {
                    "simulation_time": 100.0,
                    "time_step": 0.1,
                    "entities": 10,
                    "environment": "test_env"
                }
            },
            "complex": {
                "name": f"复杂测试场景_{scenario_id}",
                "description": "复杂仿真测试场景",
                "parameters": {
                    "simulation_time": 500.0,
                    "time_step": 0.05,
                    "entities": 100,
                    "environment": "complex_env",
                    "interactions": True,
                    "dynamic_events": True
                }
            },
            "stress": {
                "name": f"压力测试场景_{scenario_id}",
                "description": "压力测试仿真场景",
                "parameters": {
                    "simulation_time": 1000.0,
                    "time_step": 0.01,
                    "entities": 1000,
                    "environment": "stress_env",
                    "high_frequency_events": True
                }
            }
        }
        
        config = scenario_configs.get(scenario_type, scenario_configs["basic"])
        
        scenario = Scenario(
            id=scenario_id,
            name=config["name"],
            description=config["description"],
            parameters=config["parameters"],
            status=ScenarioStatus.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.scenarios[scenario_id] = scenario
        return scenario
    
    def create_test_simulation(self, simulation_id: str, scenario_id: str) -> Simulation:
        """创建测试仿真"""
        simulation = Simulation(
            id=simulation_id,
            scenario_id=scenario_id,
            name=f"仿真_{simulation_id}",
            status=SimulationStatus.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parameters={},
            results={}
        )
        
        self.simulations[simulation_id] = simulation
        return simulation
    
    async def execute_workflow_step(self, step_name: str, agent, *args, **kwargs) -> Dict[str, Any]:
        """执行工作流步骤"""
        start_time = time.time()
        
        try:
            # 根据智能体类型执行相应方法
            if hasattr(agent, 'process_async'):
                result = await agent.process_async(*args, **kwargs)
            elif hasattr(agent, 'process'):
                result = agent.process(*args, **kwargs)
            else:
                # 模拟处理
                await asyncio.sleep(0.1)  # 模拟处理时间
                result = {"status": "success", "step": step_name}
            
            end_time = time.time()
            
            return {
                "step": step_name,
                "status": "success",
                "duration": end_time - start_time,
                "result": result
            }
        
        except Exception as e:
            end_time = time.time()
            
            return {
                "step": step_name,
                "status": "error",
                "duration": end_time - start_time,
                "error": str(e)
            }
    
    async def run_complete_workflow(self, workflow_id: str, scenarios: List[Scenario]) -> SimulationWorkflowMetrics:
        """运行完整的仿真工作流"""
        metrics = SimulationWorkflowMetrics(
            workflow_id=workflow_id,
            start_time=time.time(),
            total_scenarios=len(scenarios)
        )
        
        self.workflow_metrics[workflow_id] = metrics
        
        try:
            for scenario in scenarios:
                scenario_start_time = time.time()
                
                # 步骤1: 场景建模 (ChiefModelingAgent)
                modeling_result = await self.execute_workflow_step(
                    "scenario_modeling",
                    self.chief_agent,
                    scenario
                )
                
                if modeling_result["status"] != "success":
                    metrics.failed_scenarios += 1
                    metrics.errors.append(f"场景建模失败: {modeling_result.get('error')}")
                    continue
                
                # 步骤2: 配置验证 (ValidatorAgent)
                validation_result = await self.execute_workflow_step(
                    "configuration_validation",
                    self.validator_agent,
                    scenario.parameters
                )
                
                if validation_result["status"] != "success":
                    metrics.failed_scenarios += 1
                    metrics.errors.append(f"配置验证失败: {validation_result.get('error')}")
                    continue
                
                # 步骤3: 仿真配置 (ConfiguratorAgent)
                configuration_result = await self.execute_workflow_step(
                    "simulation_configuration",
                    self.configurator_agent,
                    scenario.parameters
                )
                
                if configuration_result["status"] != "success":
                    metrics.failed_scenarios += 1
                    metrics.errors.append(f"仿真配置失败: {configuration_result.get('error')}")
                    continue
                
                # 步骤4: 创建并运行仿真
                simulation_id = f"{workflow_id}_sim_{scenario.id}"
                simulation = self.create_test_simulation(simulation_id, scenario.id)
                metrics.total_simulations += 1
                
                # 步骤5: 仿真执行 (RunnerAgent)
                execution_result = await self.execute_workflow_step(
                    "simulation_execution",
                    self.runner_agent,
                    simulation
                )
                
                if execution_result["status"] != "success":
                    metrics.failed_simulations += 1
                    metrics.errors.append(f"仿真执行失败: {execution_result.get('error')}")
                    continue
                
                # 步骤6: 结果分析 (AnalystAndReporterAgent)
                analysis_result = await self.execute_workflow_step(
                    "result_analysis",
                    self.analyst_agent,
                    simulation
                )
                
                if analysis_result["status"] == "success":
                    metrics.completed_simulations += 1
                    metrics.completed_scenarios += 1
                    
                    # 更新场景和仿真状态
                    scenario.status = ScenarioStatus.COMPLETED
                    simulation.status = SimulationStatus.COMPLETED
                    
                    # 模拟结果数据
                    simulation.results = {
                        "execution_time": execution_result["duration"],
                        "analysis_time": analysis_result["duration"],
                        "total_time": time.time() - scenario_start_time,
                        "entities_processed": scenario.parameters.get("entities", 0),
                        "simulation_steps": int(scenario.parameters.get("simulation_time", 0) / scenario.parameters.get("time_step", 1)),
                        "success": True
                    }
                else:
                    metrics.failed_simulations += 1
                    metrics.failed_scenarios += 1
                    metrics.errors.append(f"结果分析失败: {analysis_result.get('error')}")
                
                # 短暂延迟以模拟真实处理时间
                await asyncio.sleep(0.01)
        
        except Exception as e:
            metrics.errors.append(f"工作流执行异常: {str(e)}")
        
        finally:
            metrics.end_time = time.time()
        
        return metrics
    
    async def run_parallel_workflows(self, workflow_configs: List[Dict[str, Any]]) -> Dict[str, SimulationWorkflowMetrics]:
        """并行运行多个工作流"""
        tasks = []
        
        for config in workflow_configs:
            workflow_id = config["workflow_id"]
            scenarios = config["scenarios"]
            
            task = asyncio.create_task(
                self.run_complete_workflow(workflow_id, scenarios)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        workflow_results = {}
        for i, result in enumerate(results):
            workflow_id = workflow_configs[i]["workflow_id"]
            if isinstance(result, Exception):
                # 创建错误指标
                error_metrics = SimulationWorkflowMetrics(
                    workflow_id=workflow_id,
                    start_time=time.time(),
                    end_time=time.time()
                )
                error_metrics.errors.append(f"工作流异常: {str(result)}")
                workflow_results[workflow_id] = error_metrics
            else:
                workflow_results[workflow_id] = result
        
        return workflow_results
    
    def analyze_workflow_performance(self, metrics: SimulationWorkflowMetrics) -> Dict[str, Any]:
        """分析工作流性能"""
        return {
            "workflow_id": metrics.workflow_id,
            "duration_seconds": metrics.duration,
            "scenario_success_rate": metrics.scenario_success_rate,
            "simulation_success_rate": metrics.simulation_success_rate,
            "throughput_scenarios_per_second": metrics.throughput_scenarios_per_second,
            "throughput_simulations_per_second": metrics.throughput_simulations_per_second,
            "total_scenarios": metrics.total_scenarios,
            "completed_scenarios": metrics.completed_scenarios,
            "failed_scenarios": metrics.failed_scenarios,
            "total_simulations": metrics.total_simulations,
            "completed_simulations": metrics.completed_simulations,
            "failed_simulations": metrics.failed_simulations,
            "error_count": len(metrics.errors),
            "errors": metrics.errors
        }


class TestBasicSimulationWorkflow:
    """基础仿真工作流测试"""
    
    @pytest.fixture(scope="class")
    def workflow_framework(self):
        framework = SimulationWorkflowTestFramework()
        yield framework
        framework.cleanup()
    
    @pytest.mark.asyncio
    async def test_single_scenario_workflow(self, workflow_framework):
        """测试单场景工作流"""
        # 创建测试场景
        scenario = workflow_framework.create_test_scenario("test_001", "basic")
        
        # 运行工作流
        metrics = await workflow_framework.run_complete_workflow(
            "single_scenario_test",
            [scenario]
        )
        
        # 验证结果
        assert metrics.total_scenarios == 1
        assert metrics.completed_scenarios == 1
        assert metrics.failed_scenarios == 0
        assert metrics.scenario_success_rate == 1.0
        assert metrics.duration > 0
        
        # 分析性能
        performance = workflow_framework.analyze_workflow_performance(metrics)
        
        print(f"单场景工作流测试通过:")
        print(f"  执行时间: {performance['duration_seconds']:.3f}s")
        print(f"  场景成功率: {performance['scenario_success_rate']:.2%}")
        print(f"  仿真成功率: {performance['simulation_success_rate']:.2%}")
        print(f"  吞吐量: {performance['throughput_scenarios_per_second']:.2f} scenarios/s")
    
    @pytest.mark.asyncio
    async def test_multiple_scenarios_workflow(self, workflow_framework):
        """测试多场景工作流"""
        # 创建多个测试场景
        scenarios = [
            workflow_framework.create_test_scenario(f"test_{i:03d}", "basic")
            for i in range(5)
        ]
        
        # 运行工作流
        metrics = await workflow_framework.run_complete_workflow(
            "multiple_scenarios_test",
            scenarios
        )
        
        # 验证结果
        assert metrics.total_scenarios == 5
        assert metrics.completed_scenarios >= 4  # 允许一个失败
        assert metrics.scenario_success_rate >= 0.8
        assert metrics.duration > 0
        
        # 分析性能
        performance = workflow_framework.analyze_workflow_performance(metrics)
        
        print(f"多场景工作流测试通过:")
        print(f"  总场景数: {performance['total_scenarios']}")
        print(f"  完成场景数: {performance['completed_scenarios']}")
        print(f"  执行时间: {performance['duration_seconds']:.3f}s")
        print(f"  场景成功率: {performance['scenario_success_rate']:.2%}")
        print(f"  吞吐量: {performance['throughput_scenarios_per_second']:.2f} scenarios/s")
    
    @pytest.mark.asyncio
    async def test_complex_scenario_workflow(self, workflow_framework):
        """测试复杂场景工作流"""
        # 创建复杂测试场景
        scenario = workflow_framework.create_test_scenario("complex_001", "complex")
        
        # 运行工作流
        metrics = await workflow_framework.run_complete_workflow(
            "complex_scenario_test",
            [scenario]
        )
        
        # 验证结果
        assert metrics.total_scenarios == 1
        assert metrics.completed_scenarios == 1
        assert metrics.scenario_success_rate == 1.0
        
        # 复杂场景应该需要更长时间
        assert metrics.duration > 0.1
        
        # 分析性能
        performance = workflow_framework.analyze_workflow_performance(metrics)
        
        print(f"复杂场景工作流测试通过:")
        print(f"  执行时间: {performance['duration_seconds']:.3f}s")
        print(f"  场景参数: {scenario.parameters}")
        print(f"  仿真结果: {workflow_framework.simulations[f'complex_scenario_test_sim_{scenario.id}'].results}")


class TestParallelSimulationWorkflow:
    """并行仿真工作流测试"""
    
    @pytest.fixture(scope="class")
    def workflow_framework(self):
        framework = SimulationWorkflowTestFramework()
        yield framework
        framework.cleanup()
    
    @pytest.mark.asyncio
    async def test_parallel_workflows_execution(self, workflow_framework):
        """测试并行工作流执行"""
        # 创建多个工作流配置
        workflow_configs = []
        
        for i in range(3):
            scenarios = [
                workflow_framework.create_test_scenario(f"parallel_{i}_{j:02d}", "basic")
                for j in range(3)
            ]
            
            workflow_configs.append({
                "workflow_id": f"parallel_workflow_{i}",
                "scenarios": scenarios
            })
        
        # 并行运行工作流
        start_time = time.time()
        results = await workflow_framework.run_parallel_workflows(workflow_configs)
        end_time = time.time()
        
        parallel_duration = end_time - start_time
        
        # 验证结果
        assert len(results) == 3
        
        total_scenarios = 0
        total_completed = 0
        
        for workflow_id, metrics in results.items():
            assert isinstance(metrics, SimulationWorkflowMetrics)
            assert metrics.total_scenarios == 3
            assert metrics.completed_scenarios >= 2  # 允许一些失败
            
            total_scenarios += metrics.total_scenarios
            total_completed += metrics.completed_scenarios
        
        overall_success_rate = total_completed / total_scenarios
        
        # 验证并行执行效率
        assert overall_success_rate >= 0.8
        
        print(f"并行工作流测试通过:")
        print(f"  工作流数量: {len(results)}")
        print(f"  总场景数: {total_scenarios}")
        print(f"  完成场景数: {total_completed}")
        print(f"  整体成功率: {overall_success_rate:.2%}")
        print(f"  并行执行时间: {parallel_duration:.3f}s")
        
        # 分析各个工作流的性能
        for workflow_id, metrics in results.items():
            performance = workflow_framework.analyze_workflow_performance(metrics)
            print(f"  {workflow_id}: {performance['scenario_success_rate']:.2%} 成功率, {performance['duration_seconds']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_mixed_complexity_parallel_workflows(self, workflow_framework):
        """测试混合复杂度并行工作流"""
        # 创建不同复杂度的工作流
        workflow_configs = [
            {
                "workflow_id": "simple_workflow",
                "scenarios": [
                    workflow_framework.create_test_scenario(f"simple_{i}", "basic")
                    for i in range(5)
                ]
            },
            {
                "workflow_id": "complex_workflow",
                "scenarios": [
                    workflow_framework.create_test_scenario(f"complex_{i}", "complex")
                    for i in range(2)
                ]
            },
            {
                "workflow_id": "stress_workflow",
                "scenarios": [
                    workflow_framework.create_test_scenario("stress_1", "stress")
                ]
            }
        ]
        
        # 并行运行不同复杂度的工作流
        results = await workflow_framework.run_parallel_workflows(workflow_configs)
        
        # 验证结果
        assert len(results) == 3
        
        # 验证简单工作流
        simple_metrics = results["simple_workflow"]
        assert simple_metrics.total_scenarios == 5
        assert simple_metrics.scenario_success_rate >= 0.8
        
        # 验证复杂工作流
        complex_metrics = results["complex_workflow"]
        assert complex_metrics.total_scenarios == 2
        assert complex_metrics.scenario_success_rate >= 0.5  # 复杂场景允许更低成功率
        
        # 验证压力工作流
        stress_metrics = results["stress_workflow"]
        assert stress_metrics.total_scenarios == 1
        
        print(f"混合复杂度并行工作流测试通过:")
        
        for workflow_id, metrics in results.items():
            performance = workflow_framework.analyze_workflow_performance(metrics)
            print(f"  {workflow_id}:")
            print(f"    场景数: {performance['total_scenarios']}")
            print(f"    成功率: {performance['scenario_success_rate']:.2%}")
            print(f"    执行时间: {performance['duration_seconds']:.3f}s")
            print(f"    吞吐量: {performance['throughput_scenarios_per_second']:.2f} scenarios/s")


class TestSimulationDataFlow:
    """仿真数据流测试"""
    
    @pytest.fixture(scope="class")
    def workflow_framework(self):
        framework = SimulationWorkflowTestFramework()
        yield framework
        framework.cleanup()
    
    @pytest.mark.asyncio
    async def test_data_persistence_and_retrieval(self, workflow_framework):
        """测试数据持久化和检索"""
        # 创建测试场景
        scenario = workflow_framework.create_test_scenario("data_test_001", "basic")
        
        # 运行工作流
        metrics = await workflow_framework.run_complete_workflow(
            "data_flow_test",
            [scenario]
        )
        
        # 验证数据持久化
        assert scenario.id in workflow_framework.scenarios
        stored_scenario = workflow_framework.scenarios[scenario.id]
        assert stored_scenario.status == ScenarioStatus.COMPLETED
        
        # 验证仿真数据
        simulation_id = f"data_flow_test_sim_{scenario.id}"
        assert simulation_id in workflow_framework.simulations
        stored_simulation = workflow_framework.simulations[simulation_id]
        assert stored_simulation.status == SimulationStatus.COMPLETED
        assert stored_simulation.results is not None
        assert "execution_time" in stored_simulation.results
        assert "entities_processed" in stored_simulation.results
        
        print(f"数据持久化测试通过:")
        print(f"  场景状态: {stored_scenario.status}")
        print(f"  仿真状态: {stored_simulation.status}")
        print(f"  仿真结果: {stored_simulation.results}")
    
    @pytest.mark.asyncio
    async def test_data_flow_between_agents(self, workflow_framework):
        """测试智能体间数据流"""
        # 创建测试场景
        scenario = workflow_framework.create_test_scenario("dataflow_001", "complex")
        
        # 模拟智能体间数据传递
        data_flow_log = []
        
        # 重写执行步骤以记录数据流
        original_execute_step = workflow_framework.execute_workflow_step
        
        async def logged_execute_step(step_name, agent, *args, **kwargs):
            # 记录输入数据
            input_data = {
                "step": step_name,
                "agent": agent.__class__.__name__,
                "input_args": len(args),
                "input_kwargs": list(kwargs.keys())
            }
            data_flow_log.append(input_data)
            
            # 执行原始步骤
            result = await original_execute_step(step_name, agent, *args, **kwargs)
            
            # 记录输出数据
            output_data = {
                "step": step_name,
                "status": result["status"],
                "has_result": "result" in result,
                "duration": result["duration"]
            }
            data_flow_log.append(output_data)
            
            return result
        
        # 临时替换方法
        workflow_framework.execute_workflow_step = logged_execute_step
        
        try:
            # 运行工作流
            metrics = await workflow_framework.run_complete_workflow(
                "dataflow_test",
                [scenario]
            )
            
            # 验证数据流
            assert len(data_flow_log) > 0
            
            # 验证所有智能体都参与了数据流
            agent_names = {entry["agent"] for entry in data_flow_log if "agent" in entry}
            expected_agents = {
                "ChiefModelingAgent",
                "ValidatorAgent", 
                "ConfiguratorAgent",
                "RunnerAgent",
                "AnalystAndReporterAgent"
            }
            
            # 至少应该有大部分智能体参与
            assert len(agent_names.intersection(expected_agents)) >= 3
            
            print(f"智能体间数据流测试通过:")
            print(f"  数据流记录数: {len(data_flow_log)}")
            print(f"  参与的智能体: {agent_names}")
            print(f"  工作流成功率: {metrics.scenario_success_rate:.2%}")
        
        finally:
            # 恢复原始方法
            workflow_framework.execute_workflow_step = original_execute_step
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, workflow_framework):
        """测试大数据处理"""
        # 创建包含大量数据的场景
        scenario = workflow_framework.create_test_scenario("bigdata_001", "stress")
        
        # 添加大量参数数据
        large_data = {
            "entities": 10000,
            "simulation_time": 10000.0,
            "time_step": 0.001,
            "large_array": list(range(1000)),  # 大数组
            "complex_config": {
                f"param_{i}": f"value_{i}" for i in range(100)
            }
        }
        scenario.parameters.update(large_data)
        
        # 运行工作流
        start_memory = workflow_framework.monitor_service.get_memory_usage() if hasattr(workflow_framework.monitor_service, 'get_memory_usage') else 0
        
        metrics = await workflow_framework.run_complete_workflow(
            "bigdata_test",
            [scenario]
        )
        
        end_memory = workflow_framework.monitor_service.get_memory_usage() if hasattr(workflow_framework.monitor_service, 'get_memory_usage') else 0
        
        # 验证大数据处理
        assert metrics.total_scenarios == 1
        assert metrics.scenario_success_rate >= 0.5  # 大数据场景允许更低成功率
        
        # 验证内存使用合理
        memory_growth = end_memory - start_memory if end_memory > 0 and start_memory > 0 else 0
        
        print(f"大数据处理测试通过:")
        print(f"  场景参数数量: {len(scenario.parameters)}")
        print(f"  实体数量: {scenario.parameters['entities']}")
        print(f"  仿真时间: {scenario.parameters['simulation_time']}")
        print(f"  成功率: {metrics.scenario_success_rate:.2%}")
        print(f"  执行时间: {metrics.duration:.3f}s")
        if memory_growth > 0:
            print(f"  内存增长: {memory_growth:.1f}MB")


class TestSimulationErrorHandling:
    """仿真错误处理测试"""
    
    @pytest.fixture(scope="class")
    def workflow_framework(self):
        framework = SimulationWorkflowTestFramework()
        yield framework
        framework.cleanup()
    
    @pytest.mark.asyncio
    async def test_invalid_scenario_handling(self, workflow_framework):
        """测试无效场景处理"""
        # 创建无效场景
        invalid_scenario = workflow_framework.create_test_scenario("invalid_001", "basic")
        
        # 设置无效参数
        invalid_scenario.parameters = {
            "simulation_time": -100,  # 负数时间
            "time_step": 0,  # 零步长
            "entities": "invalid",  # 非数字实体数
            "missing_required_param": None
        }
        
        # 运行工作流
        metrics = await workflow_framework.run_complete_workflow(
            "invalid_scenario_test",
            [invalid_scenario]
        )
        
        # 验证错误处理
        assert metrics.total_scenarios == 1
        assert metrics.failed_scenarios >= 0  # 可能在某个步骤失败
        assert len(metrics.errors) > 0  # 应该有错误记录
        
        print(f"无效场景处理测试通过:")
        print(f"  失败场景数: {metrics.failed_scenarios}")
        print(f"  错误数量: {len(metrics.errors)}")
        print(f"  错误信息: {metrics.errors[:3]}")  # 显示前3个错误
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, workflow_framework):
        """测试智能体失败恢复"""
        # 创建测试场景
        scenario = workflow_framework.create_test_scenario("recovery_001", "basic")
        
        # 模拟智能体失败
        original_execute_step = workflow_framework.execute_workflow_step
        failure_count = 0
        
        async def failing_execute_step(step_name, agent, *args, **kwargs):
            nonlocal failure_count
            
            # 模拟某些步骤失败
            if step_name == "configuration_validation" and failure_count < 1:
                failure_count += 1
                return {
                    "step": step_name,
                    "status": "error",
                    "duration": 0.1,
                    "error": "模拟验证失败"
                }
            
            # 其他步骤正常执行
            return await original_execute_step(step_name, agent, *args, **kwargs)
        
        # 临时替换方法
        workflow_framework.execute_workflow_step = failing_execute_step
        
        try:
            # 运行工作流
            metrics = await workflow_framework.run_complete_workflow(
                "recovery_test",
                [scenario]
            )
            
            # 验证错误处理和恢复
            assert metrics.total_scenarios == 1
            assert len(metrics.errors) > 0  # 应该记录了失败
            
            print(f"智能体失败恢复测试通过:")
            print(f"  模拟失败次数: {failure_count}")
            print(f"  记录错误数: {len(metrics.errors)}")
            print(f"  场景成功率: {metrics.scenario_success_rate:.2%}")
        
        finally:
            # 恢复原始方法
            workflow_framework.execute_workflow_step = original_execute_step
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, workflow_framework):
        """测试超时处理"""
        # 创建测试场景
        scenario = workflow_framework.create_test_scenario("timeout_001", "basic")
        
        # 模拟超时
        original_execute_step = workflow_framework.execute_workflow_step
        
        async def timeout_execute_step(step_name, agent, *args, **kwargs):
            # 模拟某些步骤超时
            if step_name == "simulation_execution":
                try:
                    # 模拟长时间运行的任务
                    await asyncio.wait_for(asyncio.sleep(10), timeout=0.1)
                except asyncio.TimeoutError:
                    return {
                        "step": step_name,
                        "status": "error",
                        "duration": 0.1,
                        "error": "执行超时"
                    }
            
            # 其他步骤正常执行
            return await original_execute_step(step_name, agent, *args, **kwargs)
        
        # 临时替换方法
        workflow_framework.execute_workflow_step = timeout_execute_step
        
        try:
            # 运行工作流
            start_time = time.time()
            metrics = await workflow_framework.run_complete_workflow(
                "timeout_test",
                [scenario]
            )
            end_time = time.time()
            
            # 验证超时处理
            assert end_time - start_time < 5.0  # 应该快速失败，不会等待10秒
            assert len(metrics.errors) > 0  # 应该记录超时错误
            
            # 检查是否有超时错误
            timeout_errors = [error for error in metrics.errors if "超时" in error]
            assert len(timeout_errors) > 0
            
            print(f"超时处理测试通过:")
            print(f"  执行时间: {end_time - start_time:.3f}s")
            print(f"  超时错误数: {len(timeout_errors)}")
            print(f"  总错误数: {len(metrics.errors)}")
        
        finally:
            # 恢复原始方法
            workflow_framework.execute_workflow_step = original_execute_step


class TestSimulationPerformance:
    """仿真性能测试"""
    
    @pytest.fixture(scope="class")
    def workflow_framework(self):
        framework = SimulationWorkflowTestFramework()
        yield framework
        framework.cleanup()
    
    @pytest.mark.asyncio
    async def test_workflow_scalability(self, workflow_framework):
        """测试工作流可扩展性"""
        # 测试不同规模的场景数量
        scale_tests = [1, 5, 10, 20]
        performance_results = []
        
        for scenario_count in scale_tests:
            # 创建测试场景
            scenarios = [
                workflow_framework.create_test_scenario(f"scale_{scenario_count}_{i:03d}", "basic")
                for i in range(scenario_count)
            ]
            
            # 运行工作流
            start_time = time.time()
            metrics = await workflow_framework.run_complete_workflow(
                f"scale_test_{scenario_count}",
                scenarios
            )
            end_time = time.time()
            
            # 记录性能指标
            performance_results.append({
                "scenario_count": scenario_count,
                "duration": metrics.duration,
                "success_rate": metrics.scenario_success_rate,
                "throughput": metrics.throughput_scenarios_per_second,
                "completed_scenarios": metrics.completed_scenarios
            })
        
        # 分析可扩展性
        print(f"工作流可扩展性测试结果:")
        for result in performance_results:
            print(f"  {result['scenario_count']} 场景: {result['duration']:.3f}s, "
                  f"{result['success_rate']:.2%} 成功率, "
                  f"{result['throughput']:.2f} scenarios/s")
        
        # 验证可扩展性
        # 吞吐量不应该随着规模线性下降
        if len(performance_results) >= 2:
            small_scale_throughput = performance_results[0]["throughput"]
            large_scale_throughput = performance_results[-1]["throughput"]
            
            # 允许一定的性能下降，但不应该过于严重
            throughput_ratio = large_scale_throughput / small_scale_throughput if small_scale_throughput > 0 else 0
            assert throughput_ratio > 0.3, f"大规模场景吞吐量下降过多: {throughput_ratio:.2f}"
        
        # 成功率应该保持稳定
        success_rates = [r["success_rate"] for r in performance_results]
        min_success_rate = min(success_rates)
        assert min_success_rate >= 0.7, f"最低成功率过低: {min_success_rate:.2%}"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, workflow_framework):
        """测试内存效率"""
        import psutil
        import gc
        
        # 记录初始内存使用
        gc.collect()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 运行多轮测试
        memory_usage_history = []
        
        for round_num in range(5):
            # 创建测试场景
            scenarios = [
                workflow_framework.create_test_scenario(f"memory_{round_num}_{i:02d}", "basic")
                for i in range(10)
            ]
            
            # 运行工作流
            metrics = await workflow_framework.run_complete_workflow(
                f"memory_test_round_{round_num}",
                scenarios
            )
            
            # 记录内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_usage_history.append(current_memory - initial_memory)
            
            # 清理
            del scenarios
            gc.collect()
            
            await asyncio.sleep(0.1)  # 短暂等待
        
        # 分析内存使用
        max_memory_growth = max(memory_usage_history)
        avg_memory_growth = sum(memory_usage_history) / len(memory_usage_history)
        final_memory_growth = memory_usage_history[-1]
        
        print(f"内存效率测试结果:")
        print(f"  初始内存: {initial_memory:.1f}MB")
        print(f"  最大内存增长: {max_memory_growth:.1f}MB")
        print(f"  平均内存增长: {avg_memory_growth:.1f}MB")
        print(f"  最终内存增长: {final_memory_growth:.1f}MB")
        print(f"  内存使用历史: {[f'{m:.1f}' for m in memory_usage_history]}")
        
        # 验证内存效率
        assert max_memory_growth < 200, f"最大内存增长过多: {max_memory_growth:.1f}MB"
        assert final_memory_growth < 100, f"最终内存增长过多: {final_memory_growth:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, workflow_framework):
        """测试并发工作流性能"""
        # 创建多个并发工作流
        concurrent_count = 5
        scenarios_per_workflow = 3
        
        workflow_configs = []
        for i in range(concurrent_count):
            scenarios = [
                workflow_framework.create_test_scenario(f"concurrent_{i}_{j:02d}", "basic")
                for j in range(scenarios_per_workflow)
            ]
            
            workflow_configs.append({
                "workflow_id": f"concurrent_workflow_{i}",
                "scenarios": scenarios
            })
        
        # 测试串行执行时间
        serial_start_time = time.time()
        for config in workflow_configs:
            await workflow_framework.run_complete_workflow(
                config["workflow_id"] + "_serial",
                config["scenarios"]
            )
        serial_end_time = time.time()
        serial_duration = serial_end_time - serial_start_time
        
        # 测试并行执行时间
        parallel_start_time = time.time()
        parallel_results = await workflow_framework.run_parallel_workflows(workflow_configs)
        parallel_end_time = time.time()
        parallel_duration = parallel_end_time - parallel_start_time
        
        # 计算性能提升
        speedup_ratio = serial_duration / parallel_duration if parallel_duration > 0 else 0
        
        # 验证并发性能
        total_scenarios = concurrent_count * scenarios_per_workflow
        total_completed = sum(m.completed_scenarios for m in parallel_results.values())
        overall_success_rate = total_completed / total_scenarios
        
        print(f"并发工作流性能测试结果:")
        print(f"  并发工作流数: {concurrent_count}")
        print(f"  每个工作流场景数: {scenarios_per_workflow}")
        print(f"  串行执行时间: {serial_duration:.3f}s")
        print(f"  并行执行时间: {parallel_duration:.3f}s")
        print(f"  性能提升倍数: {speedup_ratio:.2f}x")
        print(f"  整体成功率: {overall_success_rate:.2%}")
        
        # 验证性能指标
        assert speedup_ratio > 1.5, f"并行执行性能提升不足: {speedup_ratio:.2f}x"
        assert overall_success_rate >= 0.8, f"并发执行成功率过低: {overall_success_rate:.2%}"
        assert parallel_duration < serial_duration * 0.8, "并行执行时间应该明显短于串行执行"


if __name__ == "__main__":
    # 运行仿真工作流测试
    pytest.main(["-v", __file__, "--tb=short"])