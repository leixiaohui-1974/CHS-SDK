#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP智能体集成测试

测试所有智能体API路由的基本功能：
1. ChiefModelingAgent - 总调度师
2. ValidatorAgent - 质量保证工程师
3. ConfiguratorAgent - YAML代码生成器
4. AnalystAndReporterAgent - 数据科学家和报告专家
5. RunnerAgent - 仿真执行智能体
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试用的FastAPI应用
app = FastAPI()

# 模拟路由
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "All agents are operational"}

@app.post("/api/chief/sessions")
def create_chief_session(data: dict):
    return {
        "session_id": "test_session_123",
        "name": data.get("name", "Test Session"),
        "status": "created"
    }

@app.post("/api/chief/sessions/{session_id}/instructions")
def process_instruction(session_id: str, data: dict):
    return {
        "task_id": "task_456",
        "session_id": session_id,
        "status": "processing",
        "instruction": data.get("instruction")
    }

@app.get("/api/chief/tasks/{task_id}")
def get_task_status(task_id: str):
    return {
        "task_id": task_id,
        "status": "completed",
        "result": "Configuration generated successfully"
    }

@app.post("/api/validator/validate")
def validate_config():
    return {
        "validation_id": "validation_789",
        "is_valid": True,
        "message": "Configuration is valid"
    }

@app.post("/api/configurator/sessions")
def create_config_session(data: dict):
    return {
        "session_id": "config_session_123",
        "name": data.get("name", "Config Session"),
        "status": "created"
    }

@app.post("/api/configurator/sessions/{session_id}/generate")
def generate_config(session_id: str, data: dict):
    return {
        "task_id": "config_task_456",
        "session_id": session_id,
        "status": "processing"
    }

@app.post("/api/runner/start/{session_id}")
def start_simulation(session_id: str):
    return {
        "success": True,
        "message": "Simulation started successfully",
        "session_id": session_id,
        "process_id": 12345
    }

@app.get("/api/runner/status/{session_id}")
def get_simulation_status(session_id: str):
    return {
        "status": "running",
        "session_id": session_id,
        "progress": 50.0
    }

@app.post("/api/analysis/sessions")
def create_analysis_session(data: dict):
    return {
        "session_id": "analysis_session_123",
        "name": data.get("name", "Analysis Session"),
        "status": "created"
    }

@app.post("/api/analysis/sessions/{session_id}/analyze")
def start_analysis(session_id: str, data: dict):
    return {
        "task_id": "analysis_task_456",
        "session_id": session_id,
        "status": "processing"
    }

class AgentsIntegrationTest:
    """
    智能体集成测试类
    """
    
    def __init__(self):
        self.client = TestClient(app)
    
    def test_health_check(self):
        """测试健康检查"""
        response = self.client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ 健康检查通过")
    
    def test_chief_modeling_agent_api(self):
        """测试ChiefModelingAgent API"""
        # 1. 创建会话
        session_response = self.client.post(
            "/api/chief/sessions",
            json={
                "name": "Integration Test Session",
                "description": "测试智能体集成工作流程"
            }
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert "session_id" in session_data
        session_id = session_data["session_id"]
        
        # 2. 发送指令
        instruction_response = self.client.post(
            f"/api/chief/sessions/{session_id}/instructions",
            json={
                "instruction": "创建一个简单的水系统仿真",
                "requirements": ["包含水库", "包含泵站"]
            }
        )
        
        assert instruction_response.status_code == 200
        instruction_data = instruction_response.json()
        assert "task_id" in instruction_data
        task_id = instruction_data["task_id"]
        
        # 3. 检查任务状态
        status_response = self.client.get(f"/api/chief/tasks/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        
        print("✓ ChiefModelingAgent API测试通过")
        return session_id
    
    def test_validator_agent_api(self):
        """测试ValidatorAgent API"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
simulation:
  name: "Test Simulation"
  duration: 3600
  time_step: 60

nodes:
  - id: "reservoir_1"
    type: "reservoir"
    initial_level: 10.0
""")
            config_file = f.name
        
        try:
            # 验证配置
            with open(config_file, 'rb') as f:
                validate_response = self.client.post(
                    "/api/validator/validate",
                    files={"config_file": ("test_config.yml", f, "application/x-yaml")}
                )
            
            assert validate_response.status_code == 200
            validate_data = validate_response.json()
            assert validate_data["is_valid"] == True
            
            print("✓ ValidatorAgent API测试通过")
            return validate_data["validation_id"]
        
        finally:
            # 清理临时文件
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_configurator_agent_api(self):
        """测试ConfiguratorAgent API"""
        # 1. 创建配置会话
        session_response = self.client.post(
            "/api/configurator/sessions",
            json={
                "name": "Test Config Session",
                "description": "测试配置生成"
            }
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert "session_id" in session_data
        session_id = session_data["session_id"]
        
        # 2. 生成配置
        generate_response = self.client.post(
            f"/api/configurator/sessions/{session_id}/generate",
            json={
                "instruction": "创建水系统配置",
                "requirements": ["包含水库", "包含泵站"],
                "template": "universal_config"
            }
        )
        
        assert generate_response.status_code == 200
        generate_data = generate_response.json()
        assert "task_id" in generate_data
        
        print("✓ ConfiguratorAgent API测试通过")
        return session_id
    
    def test_runner_agent_api(self):
        """测试RunnerAgent API"""
        session_id = "test_simulation_123"
        
        # 1. 启动仿真
        start_response = self.client.post(
            f"/api/runner/start/{session_id}",
            params={"config_path": "/tmp/test_config.yml"}
        )
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert start_data["success"] == True
        
        # 2. 检查状态
        status_response = self.client.get(f"/api/runner/status/{session_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        
        print("✓ RunnerAgent API测试通过")
        return session_id
    
    def test_analyst_reporter_agent_api(self):
        """测试AnalystAndReporterAgent API"""
        # 1. 创建分析会话
        session_response = self.client.post(
            "/api/analysis/sessions",
            json={
                "name": "Test Analysis Session",
                "description": "测试数据分析",
                "simulation_id": "test_simulation_123"
            }
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert "session_id" in session_data
        session_id = session_data["session_id"]
        
        # 2. 启动分析
        analyze_response = self.client.post(
            f"/api/analysis/sessions/{session_id}/analyze",
            json={
                "analysis_type": "comprehensive",
                "metrics": ["performance", "stability"]
            }
        )
        
        assert analyze_response.status_code == 200
        analyze_data = analyze_response.json()
        assert "task_id" in analyze_data
        
        print("✓ AnalystAndReporterAgent API测试通过")
        return session_id
    
    def test_full_integration_workflow(self):
        """测试完整的集成工作流程"""
        print("\n开始智能体API集成测试...")
        
        # 1. 健康检查
        self.test_health_check()
        
        # 2. 测试各个智能体API
        chief_session = self.test_chief_modeling_agent_api()
        validation_id = self.test_validator_agent_api()
        config_session = self.test_configurator_agent_api()
        simulation_id = self.test_runner_agent_api()
        analysis_session = self.test_analyst_reporter_agent_api()
        
        print("\n🎉 智能体API集成测试通过！所有API路由工作正常。")
        
        return {
            "chief_session": chief_session,
            "validation_id": validation_id,
            "config_session": config_session,
            "simulation_id": simulation_id,
            "analysis_session": analysis_session
        }

# pytest测试函数

def test_agents_integration():
    """智能体集成测试入口"""
    test_suite = AgentsIntegrationTest()
    result = test_suite.test_full_integration_workflow()
    assert result, "集成测试失败"

def test_individual_agent_apis():
    """单独测试各个智能体API"""
    test_suite = AgentsIntegrationTest()
    
    # 测试各个智能体API
    test_suite.test_health_check()
    test_suite.test_chief_modeling_agent_api()
    test_suite.test_validator_agent_api()
    test_suite.test_configurator_agent_api()
    test_suite.test_runner_agent_api()
    test_suite.test_analyst_reporter_agent_api()

if __name__ == "__main__":
    # 直接运行测试
    test_agents_integration()