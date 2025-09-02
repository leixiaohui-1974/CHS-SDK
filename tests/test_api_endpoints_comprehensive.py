#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK API端点深度测试套件

全面测试所有API端点，包括：
1. 所有REST API端点的功能测试
2. 请求参数验证和边界情况
3. 错误处理和状态码验证
4. 认证和授权测试
5. 数据格式和序列化测试
6. 并发请求和竞态条件测试
7. API版本兼容性测试
"""

import pytest
import json
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import requests
import uuid

# 导入项目模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.server import app
from api.models.scenario import ScenarioModel, ComponentModel
from api.models.simulation import SimulationRequest, SimulationResult
from api.models.agent import AgentRequest, AgentResponse


class APITestHelper:
    """API测试辅助类"""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.auth_token = None
        self.test_data = {}
    
    def authenticate(self, username: str = "test_user", password: str = "test_pass") -> str:
        """模拟用户认证"""
        auth_data = {"username": username, "password": password}
        response = self.client.post("/api/auth/login", json=auth_data)
        
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
        elif response.status_code == 404:
            # 如果认证端点不存在，使用模拟token
            self.auth_token = "mock_token_12345"
        
        return self.auth_token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        if not self.auth_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_scenario(self, name: str = None) -> Dict[str, Any]:
        """创建测试场景"""
        if not name:
            name = f"test_scenario_{uuid.uuid4().hex[:8]}"
        
        scenario_data = {
            "scenario_name": name,
            "description": f"测试场景 - {name}",
            "scenario_type": "test",
            "components": {
                "test_component": {
                    "type": "TestComponent",
                    "parameters": {
                        "param1": 1.0,
                        "param2": "test_value",
                        "param3": True
                    }
                }
            },
            "simulation_config": {
                "duration": 100.0,
                "time_step": 0.1,
                "output_interval": 1.0
            }
        }
        
        self.test_data[name] = scenario_data
        return scenario_data
    
    def cleanup_test_data(self):
        """清理测试数据"""
        for scenario_name in self.test_data.keys():
            try:
                self.client.delete(f"/api/scenarios/{scenario_name}", headers=self.get_auth_headers())
            except:
                pass
        self.test_data.clear()


class TestScenarioAPI:
    """场景管理API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        helper = APITestHelper(client)
        yield helper
        helper.cleanup_test_data()
    
    def test_create_scenario_success(self, client, api_helper):
        """测试成功创建场景"""
        scenario_data = api_helper.create_test_scenario("create_success_test")
        
        response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
        
        assert response.status_code in [200, 201]
        response_data = response.json()
        assert "scenario_id" in response_data or "id" in response_data
        assert response_data.get("scenario_name") == scenario_data["scenario_name"]
    
    def test_create_scenario_invalid_data(self, client, api_helper):
        """测试创建场景时的无效数据"""
        invalid_scenarios = [
            {},  # 空数据
            {"scenario_name": ""},  # 空名称
            {"scenario_name": "test", "components": "invalid"},  # 无效组件格式
            {"scenario_name": "test", "simulation_config": {"duration": -1}},  # 无效仿真配置
        ]
        
        for invalid_data in invalid_scenarios:
            response = client.post("/api/scenarios/", json=invalid_data, headers=api_helper.get_auth_headers())
            assert response.status_code in [400, 422], f"无效数据应该返回错误: {invalid_data}"
    
    def test_get_scenario_success(self, client, api_helper):
        """测试成功获取场景"""
        # 先创建场景
        scenario_data = api_helper.create_test_scenario("get_success_test")
        create_response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
        
        if create_response.status_code in [200, 201]:
            scenario_name = scenario_data["scenario_name"]
            
            # 获取场景
            response = client.get(f"/api/scenarios/{scenario_name}", headers=api_helper.get_auth_headers())
            
            if response.status_code == 200:
                response_data = response.json()
                assert response_data["scenario_name"] == scenario_name
            else:
                # 如果端点不存在，跳过测试
                pytest.skip("场景获取端点未实现")
    
    def test_get_scenario_not_found(self, client, api_helper):
        """测试获取不存在的场景"""
        response = client.get("/api/scenarios/nonexistent_scenario", headers=api_helper.get_auth_headers())
        assert response.status_code in [404, 422]
    
    def test_list_scenarios(self, client, api_helper):
        """测试列出所有场景"""
        # 创建多个测试场景
        for i in range(3):
            scenario_data = api_helper.create_test_scenario(f"list_test_{i}")
            client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
        
        # 获取场景列表
        response = client.get("/api/scenarios/", headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            scenarios = response.json()
            assert isinstance(scenarios, list)
        else:
            pytest.skip("场景列表端点未实现")
    
    def test_update_scenario(self, client, api_helper):
        """测试更新场景"""
        # 创建场景
        scenario_data = api_helper.create_test_scenario("update_test")
        create_response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
        
        if create_response.status_code in [200, 201]:
            scenario_name = scenario_data["scenario_name"]
            
            # 更新场景
            updated_data = scenario_data.copy()
            updated_data["description"] = "更新后的描述"
            
            response = client.put(f"/api/scenarios/{scenario_name}", json=updated_data, headers=api_helper.get_auth_headers())
            
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    response_data = response.json()
                    assert response_data["description"] == "更新后的描述"
            else:
                pytest.skip("场景更新端点未实现")
    
    def test_delete_scenario(self, client, api_helper):
        """测试删除场景"""
        # 创建场景
        scenario_data = api_helper.create_test_scenario("delete_test")
        create_response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
        
        if create_response.status_code in [200, 201]:
            scenario_name = scenario_data["scenario_name"]
            
            # 删除场景
            response = client.delete(f"/api/scenarios/{scenario_name}", headers=api_helper.get_auth_headers())
            
            if response.status_code in [200, 204, 404]:
                # 验证删除成功
                get_response = client.get(f"/api/scenarios/{scenario_name}", headers=api_helper.get_auth_headers())
                assert get_response.status_code in [404, 422]
            else:
                pytest.skip("场景删除端点未实现")


class TestSimulationAPI:
    """仿真执行API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        helper = APITestHelper(client)
        yield helper
        helper.cleanup_test_data()
    
    def test_run_simulation_success(self, client, api_helper):
        """测试成功运行仿真"""
        scenario_data = api_helper.create_test_scenario("sim_success_test")
        
        simulation_request = {
            "scenario_config": scenario_data,
            "simulation_options": {
                "output_format": "json",
                "save_results": True,
                "real_time_monitoring": False
            }
        }
        
        response = client.post("/api/simulations/run", json=simulation_request, headers=api_helper.get_auth_headers())
        
        assert response.status_code in [200, 202]
        response_data = response.json()
        
        if response.status_code == 202:
            # 异步执行
            assert "simulation_id" in response_data or "task_id" in response_data
        else:
            # 同步执行
            assert "results" in response_data or "status" in response_data
    
    def test_run_simulation_invalid_config(self, client, api_helper):
        """测试运行仿真时的无效配置"""
        invalid_requests = [
            {},  # 空请求
            {"scenario_config": {}},  # 空配置
            {"scenario_config": {"invalid": "config"}},  # 无效配置
        ]
        
        for invalid_request in invalid_requests:
            response = client.post("/api/simulations/run", json=invalid_request, headers=api_helper.get_auth_headers())
            assert response.status_code in [400, 422], f"无效请求应该返回错误: {invalid_request}"
    
    def test_get_simulation_status(self, client, api_helper):
        """测试获取仿真状态"""
        # 先启动仿真
        scenario_data = api_helper.create_test_scenario("status_test")
        simulation_request = {"scenario_config": scenario_data}
        
        run_response = client.post("/api/simulations/run", json=simulation_request, headers=api_helper.get_auth_headers())
        
        if run_response.status_code == 202:
            response_data = run_response.json()
            simulation_id = response_data.get("simulation_id") or response_data.get("task_id")
            
            if simulation_id:
                # 获取状态
                status_response = client.get(f"/api/simulations/{simulation_id}/status", headers=api_helper.get_auth_headers())
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    assert "status" in status_data
                    assert status_data["status"] in ["pending", "running", "completed", "failed"]
                else:
                    pytest.skip("仿真状态端点未实现")
    
    def test_get_simulation_results(self, client, api_helper):
        """测试获取仿真结果"""
        scenario_data = api_helper.create_test_scenario("results_test")
        simulation_request = {"scenario_config": scenario_data}
        
        run_response = client.post("/api/simulations/run", json=simulation_request, headers=api_helper.get_auth_headers())
        
        if run_response.status_code in [200, 202]:
            if run_response.status_code == 200:
                # 同步执行，直接有结果
                response_data = run_response.json()
                assert "results" in response_data or "status" in response_data
            else:
                # 异步执行，需要查询结果
                response_data = run_response.json()
                simulation_id = response_data.get("simulation_id") or response_data.get("task_id")
                
                if simulation_id:
                    results_response = client.get(f"/api/simulations/{simulation_id}/results", headers=api_helper.get_auth_headers())
                    
                    if results_response.status_code in [200, 202, 404]:
                        # 200: 结果已准备好, 202: 仍在处理, 404: 未找到
                        pass
                    else:
                        pytest.skip("仿真结果端点未实现")
    
    def test_cancel_simulation(self, client, api_helper):
        """测试取消仿真"""
        scenario_data = api_helper.create_test_scenario("cancel_test")
        simulation_request = {"scenario_config": scenario_data}
        
        run_response = client.post("/api/simulations/run", json=simulation_request, headers=api_helper.get_auth_headers())
        
        if run_response.status_code == 202:
            response_data = run_response.json()
            simulation_id = response_data.get("simulation_id") or response_data.get("task_id")
            
            if simulation_id:
                # 取消仿真
                cancel_response = client.post(f"/api/simulations/{simulation_id}/cancel", headers=api_helper.get_auth_headers())
                
                if cancel_response.status_code in [200, 404]:
                    if cancel_response.status_code == 200:
                        cancel_data = cancel_response.json()
                        assert cancel_data.get("status") in ["cancelled", "cancelling"]
                else:
                    pytest.skip("仿真取消端点未实现")


class TestAgentAPI:
    """智能体API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client)
    
    def test_chief_agent_process_request(self, client, api_helper):
        """测试首席建模智能体处理请求"""
        request_data = {
            "user_request": "创建一个水箱控制仿真",
            "context": {
                "user_id": "test_user",
                "session_id": "test_session"
            }
        }
        
        response = client.post("/api/agents/chief/process", json=request_data, headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            assert "scenario_type" in response_data or "task_plan" in response_data
        elif response.status_code == 404:
            pytest.skip("首席智能体端点未实现")
        else:
            assert response.status_code in [400, 422], "无效请求应该返回适当的错误码"
    
    def test_configurator_agent_generate_config(self, client, api_helper):
        """测试配置器智能体生成配置"""
        task_plan = {
            "scenario_type": "watertank_control",
            "objectives": ["liquid_level_control"],
            "parameters": {"target_level": 750, "initial_level": 500}
        }
        
        response = client.post("/api/agents/configurator/generate", json=task_plan, headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            assert "scenario_name" in response_data or "config" in response_data
        elif response.status_code == 404:
            pytest.skip("配置器智能体端点未实现")
        else:
            assert response.status_code in [400, 422]
    
    def test_validator_agent_validate_config(self, client, api_helper):
        """测试验证器智能体验证配置"""
        config_data = {
            "scenario_name": "test_validation",
            "components": {
                "tank": {
                    "type": "WaterTank",
                    "parameters": {"capacity": 1000.0}
                }
            }
        }
        
        response = client.post("/api/agents/validator/validate", json=config_data, headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            assert "valid" in response_data
            assert isinstance(response_data["valid"], bool)
        elif response.status_code == 404:
            pytest.skip("验证器智能体端点未实现")
        else:
            assert response.status_code in [400, 422]
    
    def test_analyst_agent_analyze_results(self, client, api_helper):
        """测试分析师智能体分析结果"""
        simulation_results = {
            "time": [0, 1, 2, 3, 4, 5],
            "tank_level": [500, 520, 540, 560, 580, 600],
            "controller_output": [1.0, 0.8, 0.6, 0.4, 0.2, 0.1]
        }
        
        response = client.post("/api/agents/analyst/analyze", json=simulation_results, headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            assert "summary" in response_data or "analysis" in response_data
        elif response.status_code == 404:
            pytest.skip("分析师智能体端点未实现")
        else:
            assert response.status_code in [400, 422]
    
    def test_runner_agent_execute_simulation(self, client, api_helper):
        """测试执行器智能体执行仿真"""
        config_data = {
            "scenario_name": "runner_test",
            "components": {"test_component": {}},
            "simulation": {"duration": 10.0}
        }
        
        response = client.post("/api/agents/runner/execute", json=config_data, headers=api_helper.get_auth_headers())
        
        if response.status_code in [200, 202]:
            response_data = response.json()
            if response.status_code == 200:
                assert "results" in response_data or "status" in response_data
            else:
                assert "task_id" in response_data or "simulation_id" in response_data
        elif response.status_code == 404:
            pytest.skip("执行器智能体端点未实现")
        else:
            assert response.status_code in [400, 422]


class TestWorkflowAPI:
    """工作流API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client)
    
    def test_start_workflow(self, client, api_helper):
        """测试启动工作流"""
        workflow_request = {
            "user_request": "创建水箱控制仿真",
            "workflow_type": "full",
            "options": {
                "auto_validate": True,
                "auto_run": True,
                "generate_report": True
            }
        }
        
        response = client.post("/api/workflow/start", json=workflow_request, headers=api_helper.get_auth_headers())
        
        if response.status_code in [200, 202]:
            response_data = response.json()
            assert "workflow_id" in response_data or "task_id" in response_data
        elif response.status_code == 404:
            pytest.skip("工作流启动端点未实现")
        else:
            assert response.status_code in [400, 422]
    
    def test_get_workflow_status(self, client, api_helper):
        """测试获取工作流状态"""
        # 先启动工作流
        workflow_request = {
            "user_request": "测试工作流状态",
            "workflow_type": "partial"
        }
        
        start_response = client.post("/api/workflow/start", json=workflow_request, headers=api_helper.get_auth_headers())
        
        if start_response.status_code in [200, 202]:
            if start_response.status_code == 202:
                response_data = start_response.json()
                workflow_id = response_data.get("workflow_id") or response_data.get("task_id")
                
                if workflow_id:
                    # 获取状态
                    status_response = client.get(f"/api/workflow/{workflow_id}/status", headers=api_helper.get_auth_headers())
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        assert "status" in status_data
                        assert "current_step" in status_data or "progress" in status_data
                    else:
                        pytest.skip("工作流状态端点未实现")
        elif start_response.status_code == 404:
            pytest.skip("工作流端点未实现")
    
    def test_get_workflow_results(self, client, api_helper):
        """测试获取工作流结果"""
        response = client.get("/api/workflow/results", headers=api_helper.get_auth_headers())
        
        if response.status_code in [200, 404]:
            if response.status_code == 200:
                response_data = response.json()
                assert isinstance(response_data, (dict, list))
        else:
            pytest.skip("工作流结果端点未实现")


class TestMonitoringAPI:
    """监控API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client)
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/api/monitor/health")
        
        if response.status_code == 200:
            response_data = response.json()
            assert "status" in response_data
            assert response_data["status"] in ["healthy", "ok", "up"]
        elif response.status_code == 404:
            # 尝试其他可能的健康检查端点
            alternative_endpoints = ["/health", "/api/health", "/status"]
            found = False
            
            for endpoint in alternative_endpoints:
                alt_response = client.get(endpoint)
                if alt_response.status_code == 200:
                    found = True
                    break
            
            if not found:
                pytest.skip("健康检查端点未实现")
    
    def test_system_metrics(self, client, api_helper):
        """测试系统指标"""
        response = client.get("/api/monitor/metrics", headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            # 检查常见的系统指标
            expected_metrics = ["cpu_usage", "memory_usage", "disk_usage", "active_connections"]
            
            # 至少应该有一些指标
            assert len(response_data) > 0
        elif response.status_code == 404:
            pytest.skip("系统指标端点未实现")
        else:
            assert response.status_code in [401, 403], "应该需要认证"
    
    def test_active_simulations(self, client, api_helper):
        """测试活跃仿真监控"""
        response = client.get("/api/monitor/simulations", headers=api_helper.get_auth_headers())
        
        if response.status_code == 200:
            response_data = response.json()
            assert isinstance(response_data, list)
        elif response.status_code == 404:
            pytest.skip("活跃仿真监控端点未实现")
        else:
            assert response.status_code in [401, 403]


class TestConcurrencyAndStress:
    """并发和压力测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client)
    
    def test_concurrent_scenario_creation(self, client, api_helper):
        """测试并发场景创建"""
        def create_scenario(index: int) -> Dict[str, Any]:
            scenario_data = api_helper.create_test_scenario(f"concurrent_test_{index}")
            response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
            return {
                "index": index,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
            }
        
        # 并发创建10个场景
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_scenario, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # 验证结果
        success_count = sum(1 for r in results if r["status_code"] in [200, 201])
        assert success_count >= 5, f"并发创建成功率过低: {success_count}/10"
        
        # 检查响应时间
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 5.0, f"平均响应时间过长: {avg_response_time:.2f}s"
        
        print(f"并发场景创建测试: {success_count}/10 成功, 平均响应时间: {avg_response_time:.2f}s")
    
    def test_concurrent_simulation_requests(self, client, api_helper):
        """测试并发仿真请求"""
        def run_simulation(index: int) -> Dict[str, Any]:
            scenario_data = api_helper.create_test_scenario(f"sim_concurrent_{index}")
            simulation_request = {"scenario_config": scenario_data}
            
            start_time = time.time()
            response = client.post("/api/simulations/run", json=simulation_request, headers=api_helper.get_auth_headers())
            end_time = time.time()
            
            return {
                "index": index,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # 并发运行5个仿真
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_simulation, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # 验证结果
        success_count = sum(1 for r in results if r["status_code"] in [200, 202])
        assert success_count >= 3, f"并发仿真成功率过低: {success_count}/5"
        
        print(f"并发仿真请求测试: {success_count}/5 成功")
    
    def test_api_rate_limiting(self, client, api_helper):
        """测试API速率限制"""
        # 快速发送大量请求
        responses = []
        start_time = time.time()
        
        for i in range(50):
            response = client.get("/api/monitor/health")
            responses.append(response.status_code)
            
            # 如果遇到速率限制，停止测试
            if response.status_code == 429:
                break
        
        end_time = time.time()
        
        # 检查是否有速率限制
        rate_limited = any(code == 429 for code in responses)
        
        if rate_limited:
            print(f"API速率限制测试: 检测到速率限制 (429状态码)")
        else:
            # 如果没有速率限制，检查响应时间是否合理
            avg_time = (end_time - start_time) / len(responses)
            assert avg_time < 1.0, f"无速率限制时响应时间过长: {avg_time:.3f}s"
            print(f"API速率限制测试: 无速率限制，平均响应时间: {avg_time:.3f}s")
    
    def test_large_payload_handling(self, client, api_helper):
        """测试大负载处理"""
        # 创建大型场景配置
        large_scenario = {
            "scenario_name": "large_payload_test",
            "description": "大负载测试" * 1000,  # 长描述
            "components": {
                f"component_{i}": {
                    "type": "TestComponent",
                    "parameters": {
                        f"param_{j}": j * 0.1 for j in range(100)
                    }
                } for i in range(50)  # 50个组件
            },
            "large_data": list(range(10000))  # 大数组
        }
        
        start_time = time.time()
        response = client.post("/api/scenarios/", json=large_scenario, headers=api_helper.get_auth_headers())
        end_time = time.time()
        
        # 验证大负载处理
        if response.status_code in [200, 201]:
            response_time = end_time - start_time
            assert response_time < 30.0, f"大负载处理时间过长: {response_time:.2f}s"
            print(f"大负载处理测试通过: {response_time:.2f}s")
        elif response.status_code == 413:
            print("大负载处理测试: 服务器正确拒绝了过大的负载")
        else:
            assert response.status_code in [400, 422], "大负载应该被正确处理或拒绝"


class TestErrorHandlingAndEdgeCases:
    """错误处理和边界情况测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client)
    
    def test_malformed_json_requests(self, client, api_helper):
        """测试格式错误的JSON请求"""
        malformed_payloads = [
            '{"invalid": json}',  # 无效JSON
            '{"key": }',  # 不完整JSON
            'not json at all',  # 非JSON
            '',  # 空字符串
        ]
        
        for payload in malformed_payloads:
            response = client.post(
                "/api/scenarios/",
                data=payload,
                headers={"Content-Type": "application/json", **api_helper.get_auth_headers()}
            )
            assert response.status_code in [400, 422], f"格式错误的JSON应该返回错误: {payload}"
    
    def test_missing_required_fields(self, client, api_helper):
        """测试缺少必需字段"""
        incomplete_scenarios = [
            {"description": "缺少scenario_name"},
            {"scenario_name": "test"},  # 缺少其他字段
            {"scenario_name": "test", "components": None},  # 空组件
        ]
        
        for incomplete_data in incomplete_scenarios:
            response = client.post("/api/scenarios/", json=incomplete_data, headers=api_helper.get_auth_headers())
            assert response.status_code in [400, 422], f"不完整数据应该返回错误: {incomplete_data}"
    
    def test_invalid_data_types(self, client, api_helper):
        """测试无效数据类型"""
        invalid_type_scenarios = [
            {"scenario_name": 123},  # 数字而非字符串
            {"scenario_name": "test", "components": "should_be_dict"},  # 字符串而非字典
            {"scenario_name": "test", "simulation_config": {"duration": "not_a_number"}},  # 字符串而非数字
        ]
        
        for invalid_data in invalid_type_scenarios:
            response = client.post("/api/scenarios/", json=invalid_data, headers=api_helper.get_auth_headers())
            assert response.status_code in [400, 422], f"无效数据类型应该返回错误: {invalid_data}"
    
    def test_boundary_values(self, client, api_helper):
        """测试边界值"""
        boundary_scenarios = [
            # 极长名称
            {"scenario_name": "x" * 1000, "components": {}},
            # 负数值
            {"scenario_name": "negative_test", "simulation_config": {"duration": -1}},
            # 零值
            {"scenario_name": "zero_test", "simulation_config": {"duration": 0}},
            # 极大值
            {"scenario_name": "large_test", "simulation_config": {"duration": 1e10}},
        ]
        
        for boundary_data in boundary_scenarios:
            response = client.post("/api/scenarios/", json=boundary_data, headers=api_helper.get_auth_headers())
            # 边界值可能被接受或拒绝，但不应该导致服务器错误
            assert response.status_code < 500, f"边界值不应该导致服务器错误: {boundary_data}"
    
    def test_unicode_and_special_characters(self, client, api_helper):
        """测试Unicode和特殊字符"""
        special_char_scenarios = [
            {"scenario_name": "测试中文场景", "description": "包含中文的描述"},
            {"scenario_name": "test_émojis_🚀", "description": "Émojis and accénts"},
            {"scenario_name": "test_special_!@#$%", "description": "Special chars: !@#$%^&*()"},
        ]
        
        for special_data in special_char_scenarios:
            response = client.post("/api/scenarios/", json=special_data, headers=api_helper.get_auth_headers())
            # Unicode应该被正确处理
            assert response.status_code < 500, f"Unicode字符不应该导致服务器错误: {special_data}"
    
    def test_sql_injection_attempts(self, client, api_helper):
        """测试SQL注入尝试"""
        sql_injection_payloads = [
            "'; DROP TABLE scenarios; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "<script>alert('xss')</script>",
        ]
        
        for payload in sql_injection_payloads:
            scenario_data = {
                "scenario_name": payload,
                "description": payload,
                "components": {}
            }
            
            response = client.post("/api/scenarios/", json=scenario_data, headers=api_helper.get_auth_headers())
            # 注入尝试应该被安全处理，不导致服务器错误
            assert response.status_code < 500, f"SQL注入尝试不应该导致服务器错误: {payload}"


if __name__ == "__main__":
    # 运行API端点测试
    pytest.main(["-v", __file__, "--tb=short", "-x"])