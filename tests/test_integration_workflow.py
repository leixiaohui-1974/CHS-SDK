#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 集成测试套件

专门用于测试多智能体协同和端到端工作流，包括：
1. 完整的仿真工作流集成测试
2. 智能体间通信和协调测试
3. API与智能体集成测试
4. 实时监控集成测试
5. 错误恢复和容错测试
6. 数据流和状态管理测试
"""

import pytest
import asyncio
import json
import time
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# 导入项目模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.server import app
from api.agents.chief_modeling_agent import ChiefModelingAgent
from api.agents.validator_agent import ValidatorAgent
from api.agents.configurator_agent import ConfiguratorAgent
from api.agents.analyst_reporter_agent import AnalystAndReporterAgent
from api.agents.runner_agent import RunnerAgent
from api.services.websocket_monitor import WebSocketMonitorService


class WorkflowOrchestrator:
    """工作流编排器 - 用于集成测试"""
    
    def __init__(self):
        self.agents = {
            'chief': ChiefModelingAgent(),
            'validator': ValidatorAgent(),
            'configurator': ConfiguratorAgent(),
            'analyst': AnalystAndReporterAgent(),
            'runner': RunnerAgent()
        }
        self.monitor = WebSocketMonitorService()
        self.workflow_state = {
            'current_step': None,
            'completed_steps': [],
            'errors': [],
            'results': {}
        }
    
    async def execute_full_workflow(self, user_request: str, workspace: Path) -> Dict[str, Any]:
        """执行完整工作流"""
        try:
            # 步骤1: 任务分解
            self.workflow_state['current_step'] = 'task_decomposition'
            task_plan = await self.agents['chief'].process_user_request(user_request)
            self.workflow_state['results']['task_plan'] = task_plan
            self.workflow_state['completed_steps'].append('task_decomposition')
            
            # 步骤2: 配置生成
            self.workflow_state['current_step'] = 'configuration_generation'
            config = await self.agents['configurator'].generate_config(task_plan)
            self.workflow_state['results']['config'] = config
            self.workflow_state['completed_steps'].append('configuration_generation')
            
            # 步骤3: 配置验证
            self.workflow_state['current_step'] = 'configuration_validation'
            validation = await self.agents['validator'].validate_config(config)
            self.workflow_state['results']['validation'] = validation
            
            if not validation.get('valid', False):
                raise ValueError(f"配置验证失败: {validation.get('errors', [])}")
            
            self.workflow_state['completed_steps'].append('configuration_validation')
            
            # 步骤4: 仿真执行
            self.workflow_state['current_step'] = 'simulation_execution'
            simulation_result = await self.agents['runner'].run_simulation(config)
            self.workflow_state['results']['simulation'] = simulation_result
            
            if simulation_result.get('status') != 'completed':
                raise RuntimeError(f"仿真执行失败: {simulation_result.get('error', 'Unknown error')}")
            
            self.workflow_state['completed_steps'].append('simulation_execution')
            
            # 步骤5: 结果分析
            self.workflow_state['current_step'] = 'result_analysis'
            analysis = await self.agents['analyst'].analyze_results(simulation_result['results'])
            self.workflow_state['results']['analysis'] = analysis
            self.workflow_state['completed_steps'].append('result_analysis')
            
            # 步骤6: 报告生成
            self.workflow_state['current_step'] = 'report_generation'
            report = await self.agents['analyst'].generate_report(analysis, 'comprehensive')
            self.workflow_state['results']['report'] = report
            self.workflow_state['completed_steps'].append('report_generation')
            
            self.workflow_state['current_step'] = 'completed'
            
            return {
                'status': 'success',
                'workflow_state': self.workflow_state,
                'final_results': {
                    'task_plan': task_plan,
                    'config': config,
                    'validation': validation,
                    'simulation': simulation_result,
                    'analysis': analysis,
                    'report': report
                }
            }
            
        except Exception as e:
            self.workflow_state['errors'].append({
                'step': self.workflow_state['current_step'],
                'error': str(e),
                'timestamp': time.time()
            })
            
            return {
                'status': 'error',
                'workflow_state': self.workflow_state,
                'error': str(e)
            }
    
    async def execute_partial_workflow(self, start_step: str, end_step: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行部分工作流"""
        steps = ['task_decomposition', 'configuration_generation', 'configuration_validation', 
                'simulation_execution', 'result_analysis', 'report_generation']
        
        start_idx = steps.index(start_step)
        end_idx = steps.index(end_step)
        
        if start_idx > end_idx:
            raise ValueError("起始步骤不能在结束步骤之后")
        
        # 设置初始数据
        self.workflow_state['results'].update(initial_data)
        
        for i in range(start_idx, end_idx + 1):
            step = steps[i]
            self.workflow_state['current_step'] = step
            
            try:
                if step == 'task_decomposition':
                    if 'user_request' not in initial_data:
                        raise ValueError("缺少用户请求")
                    result = await self.agents['chief'].process_user_request(initial_data['user_request'])
                    self.workflow_state['results']['task_plan'] = result
                
                elif step == 'configuration_generation':
                    if 'task_plan' not in self.workflow_state['results']:
                        raise ValueError("缺少任务计划")
                    result = await self.agents['configurator'].generate_config(self.workflow_state['results']['task_plan'])
                    self.workflow_state['results']['config'] = result
                
                elif step == 'configuration_validation':
                    if 'config' not in self.workflow_state['results']:
                        raise ValueError("缺少配置")
                    result = await self.agents['validator'].validate_config(self.workflow_state['results']['config'])
                    self.workflow_state['results']['validation'] = result
                
                elif step == 'simulation_execution':
                    if 'config' not in self.workflow_state['results']:
                        raise ValueError("缺少配置")
                    result = await self.agents['runner'].run_simulation(self.workflow_state['results']['config'])
                    self.workflow_state['results']['simulation'] = result
                
                elif step == 'result_analysis':
                    if 'simulation' not in self.workflow_state['results']:
                        raise ValueError("缺少仿真结果")
                    result = await self.agents['analyst'].analyze_results(self.workflow_state['results']['simulation']['results'])
                    self.workflow_state['results']['analysis'] = result
                
                elif step == 'report_generation':
                    if 'analysis' not in self.workflow_state['results']:
                        raise ValueError("缺少分析结果")
                    result = await self.agents['analyst'].generate_report(self.workflow_state['results']['analysis'], 'comprehensive')
                    self.workflow_state['results']['report'] = result
                
                self.workflow_state['completed_steps'].append(step)
                
            except Exception as e:
                self.workflow_state['errors'].append({
                    'step': step,
                    'error': str(e),
                    'timestamp': time.time()
                })
                return {
                    'status': 'error',
                    'workflow_state': self.workflow_state,
                    'error': str(e)
                }
        
        return {
            'status': 'success',
            'workflow_state': self.workflow_state
        }


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    @pytest.fixture(scope="class")
    def temp_workspace(self):
        """临时工作空间"""
        temp_dir = tempfile.mkdtemp(prefix="chs_integration_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture(scope="class")
    def orchestrator(self):
        """工作流编排器"""
        return WorkflowOrchestrator()
    
    @pytest.mark.asyncio
    async def test_complete_watertank_workflow(self, orchestrator, temp_workspace):
        """测试完整的水箱控制工作流"""
        user_request = "创建一个水箱液位控制仿真，目标液位750L，初始液位500L，仿真时间100秒"
        
        # 模拟各个智能体的响应
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
             patch.object(orchestrator.agents['configurator'], 'generate_config') as mock_config, \
             patch.object(orchestrator.agents['validator'], 'validate_config') as mock_validate, \
             patch.object(orchestrator.agents['runner'], 'run_simulation') as mock_run, \
             patch.object(orchestrator.agents['analyst'], 'analyze_results') as mock_analyze, \
             patch.object(orchestrator.agents['analyst'], 'generate_report') as mock_report:
            
            # 设置模拟响应
            mock_chief.return_value = {
                'scenario_type': 'watertank_control',
                'objectives': ['liquid_level_control'],
                'parameters': {'target_level': 750, 'initial_level': 500},
                'tasks': ['setup_tank', 'configure_controller', 'run_simulation']
            }
            
            mock_config.return_value = {
                'scenario_name': 'watertank_control',
                'components': {
                    'tank': {
                        'type': 'WaterTank',
                        'parameters': {
                            'capacity': 1000.0,
                            'initial_level': 500.0,
                            'inflow_rate': 10.0,
                            'outflow_rate': 8.0
                        }
                    },
                    'controller': {
                        'type': 'PIDController',
                        'parameters': {
                            'kp': 1.0,
                            'ki': 0.1,
                            'kd': 0.01,
                            'setpoint': 750.0
                        }
                    }
                },
                'simulation': {
                    'duration': 100.0,
                    'time_step': 0.1,
                    'output_interval': 1.0
                }
            }
            
            mock_validate.return_value = {
                'valid': True,
                'warnings': [],
                'suggestions': ['Consider adding safety limits']
            }
            
            # 生成模拟仿真数据
            time_points = np.arange(0, 101, 1)
            level_data = 500 + (750 - 500) * (1 - np.exp(-time_points / 30))
            
            mock_run.return_value = {
                'status': 'completed',
                'duration': 100.0,
                'time_steps': 1000,
                'results': {
                    'time': time_points.tolist(),
                    'tank_level': level_data.tolist(),
                    'controller_output': [1.0 - i/100 for i in range(101)],
                    'inflow_rate': [10.0] * 101,
                    'outflow_rate': [8.0] * 101
                }
            }
            
            mock_analyze.return_value = {
                'summary': '水箱液位控制仿真成功完成',
                'metrics': {
                    'final_level': 749.8,
                    'settling_time': 85.2,
                    'overshoot': 2.1,
                    'steady_state_error': 0.2
                },
                'performance': 'excellent'
            }
            
            mock_report.return_value = {
                'title': '水箱液位控制仿真报告',
                'sections': {
                    'executive_summary': '仿真成功达到控制目标',
                    'methodology': '使用PID控制器进行液位控制',
                    'results': '系统在85.2秒内稳定到目标液位',
                    'conclusions': '控制系统性能优秀'
                },
                'format': 'comprehensive'
            }
            
            # 执行完整工作流
            result = await orchestrator.execute_full_workflow(user_request, temp_workspace)
            
            # 验证结果
            assert result['status'] == 'success'
            assert 'final_results' in result
            assert len(result['workflow_state']['completed_steps']) == 6
            assert result['workflow_state']['current_step'] == 'completed'
            assert len(result['workflow_state']['errors']) == 0
            
            # 验证各步骤结果
            final_results = result['final_results']
            assert final_results['task_plan']['scenario_type'] == 'watertank_control'
            assert final_results['config']['scenario_name'] == 'watertank_control'
            assert final_results['validation']['valid'] is True
            assert final_results['simulation']['status'] == 'completed'
            assert final_results['analysis']['performance'] == 'excellent'
            assert 'title' in final_results['report']
            
            print("完整水箱工作流测试通过")
            print(f"完成步骤: {result['workflow_state']['completed_steps']}")
            print(f"最终液位: {final_results['analysis']['metrics']['final_level']}L")
    
    @pytest.mark.asyncio
    async def test_multi_scenario_workflow(self, orchestrator, temp_workspace):
        """测试多场景工作流"""
        scenarios = [
            "创建渠道水流仿真，长度1000米，宽度10米",
            "设计多智能体协同控制系统，包含3个局部控制器",
            "建立水库调度优化模型，考虑发电和防洪"
        ]
        
        results = []
        
        for i, scenario in enumerate(scenarios):
            # 为每个场景创建新的编排器实例
            scenario_orchestrator = WorkflowOrchestrator()
            
            with patch.object(scenario_orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
                 patch.object(scenario_orchestrator.agents['configurator'], 'generate_config') as mock_config, \
                 patch.object(scenario_orchestrator.agents['validator'], 'validate_config') as mock_validate, \
                 patch.object(scenario_orchestrator.agents['runner'], 'run_simulation') as mock_run, \
                 patch.object(scenario_orchestrator.agents['analyst'], 'analyze_results') as mock_analyze, \
                 patch.object(scenario_orchestrator.agents['analyst'], 'generate_report') as mock_report:
                
                # 设置场景特定的模拟响应
                if i == 0:  # 渠道仿真
                    mock_chief.return_value = {'scenario_type': 'canal_flow', 'tasks': ['setup_canal']}
                    mock_config.return_value = {'scenario_name': f'canal_sim_{i}', 'components': {'canal': {}}}
                elif i == 1:  # 多智能体
                    mock_chief.return_value = {'scenario_type': 'multi_agent', 'tasks': ['setup_agents']}
                    mock_config.return_value = {'scenario_name': f'agent_sim_{i}', 'agents': {'coordinator': {}}}
                else:  # 水库调度
                    mock_chief.return_value = {'scenario_type': 'reservoir_optimization', 'tasks': ['setup_reservoir']}
                    mock_config.return_value = {'scenario_name': f'reservoir_sim_{i}', 'components': {'reservoir': {}}}
                
                mock_validate.return_value = {'valid': True, 'warnings': []}
                mock_run.return_value = {
                    'status': 'completed',
                    'results': {'time': [0, 1, 2], 'values': [1.0, 2.0, 3.0]}
                }
                mock_analyze.return_value = {'summary': f'场景{i+1}分析完成', 'metrics': {}}
                mock_report.return_value = {'title': f'场景{i+1}报告'}
                
                # 执行工作流
                result = await scenario_orchestrator.execute_full_workflow(scenario, temp_workspace)
                results.append(result)
        
        # 验证所有场景都成功完成
        for i, result in enumerate(results):
            assert result['status'] == 'success', f"场景{i+1}执行失败"
            assert len(result['workflow_state']['completed_steps']) == 6
            assert len(result['workflow_state']['errors']) == 0
        
        print(f"多场景工作流测试通过，成功执行{len(scenarios)}个场景")
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, orchestrator, temp_workspace):
        """测试工作流错误恢复"""
        user_request = "创建一个有问题的仿真配置"
        
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
             patch.object(orchestrator.agents['configurator'], 'generate_config') as mock_config, \
             patch.object(orchestrator.agents['validator'], 'validate_config') as mock_validate:
            
            # 设置正常的任务分解
            mock_chief.return_value = {
                'scenario_type': 'test_scenario',
                'tasks': ['setup_test']
            }
            
            # 设置正常的配置生成
            mock_config.return_value = {
                'scenario_name': 'error_test',
                'components': {'test_component': {}}
            }
            
            # 设置验证失败
            mock_validate.return_value = {
                'valid': False,
                'errors': ['Invalid component configuration', 'Missing required parameters']
            }
            
            # 执行工作流（应该在验证步骤失败）
            result = await orchestrator.execute_full_workflow(user_request, temp_workspace)
            
            # 验证错误处理
            assert result['status'] == 'error'
            assert len(result['workflow_state']['errors']) == 1
            assert result['workflow_state']['errors'][0]['step'] == 'configuration_validation'
            assert 'Invalid component configuration' in result['workflow_state']['errors'][0]['error']
            
            # 验证部分步骤完成
            completed_steps = result['workflow_state']['completed_steps']
            assert 'task_decomposition' in completed_steps
            assert 'configuration_generation' in completed_steps
            assert 'configuration_validation' not in completed_steps
            
            print("工作流错误恢复测试通过")
            print(f"错误信息: {result['workflow_state']['errors'][0]['error']}")
    
    @pytest.mark.asyncio
    async def test_partial_workflow_execution(self, orchestrator, temp_workspace):
        """测试部分工作流执行"""
        # 准备初始数据
        initial_data = {
            'task_plan': {
                'scenario_type': 'partial_test',
                'tasks': ['test_task']
            },
            'config': {
                'scenario_name': 'partial_test',
                'components': {'test': {}}
            }
        }
        
        with patch.object(orchestrator.agents['validator'], 'validate_config') as mock_validate, \
             patch.object(orchestrator.agents['runner'], 'run_simulation') as mock_run:
            
            mock_validate.return_value = {'valid': True, 'warnings': []}
            mock_run.return_value = {
                'status': 'completed',
                'results': {'time': [0, 1], 'values': [1.0, 2.0]}
            }
            
            # 执行从验证到仿真的部分工作流
            result = await orchestrator.execute_partial_workflow(
                'configuration_validation', 
                'simulation_execution', 
                initial_data
            )
            
            # 验证结果
            assert result['status'] == 'success'
            completed_steps = result['workflow_state']['completed_steps']
            assert 'configuration_validation' in completed_steps
            assert 'simulation_execution' in completed_steps
            assert 'result_analysis' not in completed_steps
            
            # 验证数据传递
            assert 'validation' in result['workflow_state']['results']
            assert 'simulation' in result['workflow_state']['results']
            
            print("部分工作流执行测试通过")
            print(f"执行步骤: {completed_steps}")


class TestAgentCommunication:
    """智能体通信测试"""
    
    @pytest.mark.asyncio
    async def test_agent_message_passing(self):
        """测试智能体消息传递"""
        chief = ChiefModelingAgent()
        configurator = ConfiguratorAgent()
        validator = ValidatorAgent()
        
        # 模拟消息传递链
        with patch.object(chief, 'process_user_request') as mock_chief, \
             patch.object(configurator, 'generate_config') as mock_config, \
             patch.object(validator, 'validate_config') as mock_validate:
            
            # 设置消息传递
            task_plan = {
                'scenario_type': 'communication_test',
                'requirements': ['req1', 'req2'],
                'constraints': ['constraint1']
            }
            mock_chief.return_value = task_plan
            
            config = {
                'scenario_name': 'comm_test',
                'based_on': task_plan,
                'components': {'comp1': {}}
            }
            mock_config.return_value = config
            
            validation = {
                'valid': True,
                'config_reviewed': config,
                'recommendations': ['rec1']
            }
            mock_validate.return_value = validation
            
            # 执行消息传递链
            user_request = "测试智能体通信"
            
            step1_result = await chief.process_user_request(user_request)
            step2_result = await configurator.generate_config(step1_result)
            step3_result = await validator.validate_config(step2_result)
            
            # 验证消息传递
            assert step1_result == task_plan
            assert step2_result == config
            assert step3_result == validation
            
            # 验证调用参数
            mock_chief.assert_called_once_with(user_request)
            mock_config.assert_called_once_with(task_plan)
            mock_validate.assert_called_once_with(config)
            
            print("智能体消息传递测试通过")
    
    @pytest.mark.asyncio
    async def test_agent_error_propagation(self):
        """测试智能体错误传播"""
        chief = ChiefModelingAgent()
        configurator = ConfiguratorAgent()
        
        with patch.object(chief, 'process_user_request') as mock_chief, \
             patch.object(configurator, 'generate_config') as mock_config:
            
            # Chief正常返回
            mock_chief.return_value = {'scenario_type': 'error_test'}
            
            # Configurator抛出异常
            mock_config.side_effect = ValueError("配置生成失败")
            
            # 测试错误传播
            try:
                task_plan = await chief.process_user_request("测试错误传播")
                config = await configurator.generate_config(task_plan)
                assert False, "应该抛出异常"
            except ValueError as e:
                assert str(e) == "配置生成失败"
                print("智能体错误传播测试通过")
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self):
        """测试并发智能体操作"""
        # 创建多个智能体实例
        agents = {
            f'chief_{i}': ChiefModelingAgent() for i in range(5)
        }
        
        async def process_request(agent_id: str, request: str):
            agent = agents[agent_id]
            with patch.object(agent, 'process_user_request') as mock_process:
                mock_process.return_value = {
                    'agent_id': agent_id,
                    'request': request,
                    'timestamp': time.time()
                }
                
                result = await agent.process_user_request(request)
                return result
        
        # 并发执行多个请求
        requests = [f"请求_{i}" for i in range(5)]
        tasks = [
            process_request(f'chief_{i}', requests[i]) 
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证并发执行结果
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result['agent_id'] == f'chief_{i}'
            assert result['request'] == f'请求_{i}'
        
        print("并发智能体操作测试通过")


class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    def test_api_agent_integration(self, client):
        """测试API与智能体集成"""
        # 测试场景创建API
        scenario_data = {
            "scenario_name": "api_integration_test",
            "description": "API集成测试场景",
            "components": {
                "test_component": {
                    "type": "TestComponent",
                    "parameters": {"param1": 1.0}
                }
            }
        }
        
        response = client.post("/api/scenarios/", json=scenario_data)
        assert response.status_code in [200, 201]
        
        # 测试配置验证API
        response = client.post("/api/validator/validate", json=scenario_data)
        assert response.status_code == 200
        validation_result = response.json()
        assert "valid" in validation_result
        
        # 测试仿真执行API
        response = client.post("/api/simulations/run", json=scenario_data)
        assert response.status_code in [200, 202]
        
        print("API智能体集成测试通过")
    
    def test_api_workflow_coordination(self, client):
        """测试API工作流协调"""
        # 创建工作流请求
        workflow_request = {
            "user_request": "创建测试仿真",
            "workflow_type": "full",
            "options": {
                "auto_validate": True,
                "auto_run": True,
                "generate_report": True
            }
        }
        
        # 启动工作流
        response = client.post("/api/workflow/start", json=workflow_request)
        assert response.status_code in [200, 202]
        
        # 检查工作流状态
        response = client.get("/api/workflow/status")
        assert response.status_code == 200
        
        # 获取工作流结果
        response = client.get("/api/workflow/results")
        assert response.status_code in [200, 404]  # 可能还没有结果
        
        print("API工作流协调测试通过")
    
    @pytest.mark.asyncio
    async def test_websocket_api_integration(self):
        """测试WebSocket API集成"""
        monitor = WebSocketMonitorService()
        
        # 模拟WebSocket连接
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        
        # 连接到监控服务
        await monitor.connect(mock_websocket)
        
        # 模拟API触发的事件
        api_events = [
            {"type": "scenario_created", "data": {"id": "test_scenario"}},
            {"type": "simulation_started", "data": {"id": "test_sim"}},
            {"type": "simulation_progress", "data": {"progress": 50}},
            {"type": "simulation_completed", "data": {"status": "success"}}
        ]
        
        # 广播事件
        for event in api_events:
            await monitor.broadcast(event)
        
        # 验证WebSocket调用
        assert mock_websocket.send.call_count == len(api_events)
        
        # 断开连接
        await monitor.disconnect(mock_websocket)
        
        print("WebSocket API集成测试通过")


class TestDataFlowAndState:
    """数据流和状态管理测试"""
    
    @pytest.mark.asyncio
    async def test_data_persistence_across_workflow(self):
        """测试工作流中的数据持久化"""
        orchestrator = WorkflowOrchestrator()
        
        # 模拟数据在工作流中的传递
        initial_data = {
            'user_request': '测试数据持久化',
            'metadata': {
                'user_id': 'test_user',
                'session_id': 'test_session',
                'timestamp': time.time()
            }
        }
        
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
             patch.object(orchestrator.agents['configurator'], 'generate_config') as mock_config:
            
            # 设置返回值，包含原始元数据
            mock_chief.return_value = {
                'scenario_type': 'data_persistence_test',
                'metadata': initial_data['metadata'],
                'tasks': ['test_task']
            }
            
            mock_config.return_value = {
                'scenario_name': 'persistence_test',
                'metadata': initial_data['metadata'],
                'components': {'test': {}}
            }
            
            # 执行部分工作流
            result = await orchestrator.execute_partial_workflow(
                'task_decomposition',
                'configuration_generation',
                initial_data
            )
            
            # 验证数据持久化
            assert result['status'] == 'success'
            
            # 检查元数据在各步骤中的保持
            task_plan = result['workflow_state']['results']['task_plan']
            config = result['workflow_state']['results']['config']
            
            assert task_plan['metadata']['user_id'] == 'test_user'
            assert config['metadata']['session_id'] == 'test_session'
            
            print("数据持久化测试通过")
    
    @pytest.mark.asyncio
    async def test_state_transitions(self):
        """测试状态转换"""
        orchestrator = WorkflowOrchestrator()
        
        # 验证初始状态
        assert orchestrator.workflow_state['current_step'] is None
        assert len(orchestrator.workflow_state['completed_steps']) == 0
        assert len(orchestrator.workflow_state['errors']) == 0
        
        # 模拟状态转换
        test_data = {'user_request': '测试状态转换'}
        
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief:
            mock_chief.return_value = {'scenario_type': 'state_test'}
            
            # 执行单步
            result = await orchestrator.execute_partial_workflow(
                'task_decomposition',
                'task_decomposition',
                test_data
            )
            
            # 验证状态变化
            assert result['status'] == 'success'
            assert orchestrator.workflow_state['current_step'] == 'task_decomposition'
            assert 'task_decomposition' in orchestrator.workflow_state['completed_steps']
            assert len(orchestrator.workflow_state['errors']) == 0
            
            print("状态转换测试通过")
    
    def test_large_data_handling(self):
        """测试大数据处理"""
        # 创建大型数据集
        large_dataset = {
            'time_series': {
                'time': list(range(100000)),
                'values': [np.sin(i * 0.01) + np.random.normal(0, 0.1) for i in range(100000)],
                'metadata': {f'meta_{i}': f'value_{i}' for i in range(1000)}
            },
            'parameters': {f'param_{i}': np.random.random() for i in range(10000)}
        }
        
        # 测试数据序列化/反序列化
        start_time = time.time()
        serialized = json.dumps(large_dataset, default=str)
        serialization_time = time.time() - start_time
        
        start_time = time.time()
        deserialized = json.loads(serialized)
        deserialization_time = time.time() - start_time
        
        # 验证数据完整性
        assert len(deserialized['time_series']['time']) == 100000
        assert len(deserialized['parameters']) == 10000
        
        # 性能断言
        assert serialization_time < 10.0, f"序列化时间过长: {serialization_time:.2f}s"
        assert deserialization_time < 5.0, f"反序列化时间过长: {deserialization_time:.2f}s"
        
        print(f"大数据处理测试通过")
        print(f"序列化时间: {serialization_time:.2f}s")
        print(f"反序列化时间: {deserialization_time:.2f}s")
        print(f"数据大小: {len(serialized) / 1024 / 1024:.1f}MB")


class TestFaultTolerance:
    """容错测试"""
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self):
        """测试智能体故障恢复"""
        orchestrator = WorkflowOrchestrator()
        
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
             patch.object(orchestrator.agents['configurator'], 'generate_config') as mock_config:
            
            # 第一次调用失败
            mock_chief.side_effect = [ConnectionError("网络连接失败"), {'scenario_type': 'recovery_test'}]
            mock_config.return_value = {'scenario_name': 'recovery_test'}
            
            # 第一次尝试（失败）
            result1 = await orchestrator.execute_partial_workflow(
                'task_decomposition',
                'task_decomposition',
                {'user_request': '测试故障恢复'}
            )
            
            assert result1['status'] == 'error'
            assert 'network' in result1['error'].lower() or 'connection' in result1['error'].lower()
            
            # 重置状态并重试
            orchestrator.workflow_state = {
                'current_step': None,
                'completed_steps': [],
                'errors': [],
                'results': {}
            }
            
            # 第二次尝试（成功）
            result2 = await orchestrator.execute_partial_workflow(
                'task_decomposition',
                'configuration_generation',
                {'user_request': '测试故障恢复'}
            )
            
            assert result2['status'] == 'success'
            assert len(result2['workflow_state']['completed_steps']) == 2
            
            print("智能体故障恢复测试通过")
    
    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """测试部分失败处理"""
        orchestrator = WorkflowOrchestrator()
        
        with patch.object(orchestrator.agents['chief'], 'process_user_request') as mock_chief, \
             patch.object(orchestrator.agents['configurator'], 'generate_config') as mock_config, \
             patch.object(orchestrator.agents['validator'], 'validate_config') as mock_validate:
            
            # 前两步成功
            mock_chief.return_value = {'scenario_type': 'partial_failure_test'}
            mock_config.return_value = {'scenario_name': 'partial_failure_test'}
            
            # 验证步骤失败
            mock_validate.side_effect = ValueError("验证失败")
            
            # 执行工作流
            result = await orchestrator.execute_partial_workflow(
                'task_decomposition',
                'configuration_validation',
                {'user_request': '测试部分失败'}
            )
            
            # 验证部分成功
            assert result['status'] == 'error'
            assert len(result['workflow_state']['completed_steps']) == 2  # 前两步成功
            assert len(result['workflow_state']['errors']) == 1
            assert result['workflow_state']['errors'][0]['step'] == 'configuration_validation'
            
            # 验证可以从失败点继续
            assert 'task_plan' in result['workflow_state']['results']
            assert 'config' in result['workflow_state']['results']
            
            print("部分失败处理测试通过")
    
    def test_resource_exhaustion_handling(self):
        """测试资源耗尽处理"""
        import psutil
        
        # 模拟内存不足情况
        def memory_intensive_operation():
            try:
                # 尝试分配大量内存
                large_data = []
                for i in range(1000):
                    chunk = [0] * 1000000  # 每块约4MB
                    large_data.append(chunk)
                    
                    # 检查内存使用
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    
                    if memory_mb > 1000:  # 超过1GB时停止
                        break
                
                return len(large_data)
                
            except MemoryError:
                return -1
            finally:
                # 清理内存
                if 'large_data' in locals():
                    del large_data
                import gc
                gc.collect()
        
        # 执行内存密集型操作
        result = memory_intensive_operation()
        
        # 验证系统能够处理资源限制
        assert result != -1, "系统应该能够优雅处理内存限制"
        
        print(f"资源耗尽处理测试通过，分配了{result}个内存块")


if __name__ == "__main__":
    # 运行集成测试
    pytest.main(["-v", __file__, "--tb=short"])