# -*- coding: utf-8 -*-
"""
Scenario Management Routes for MCP Service

实现ChiefModelingAgent的核心功能：
- 接收用户自然语言指令
- 任务分解和派发
- 对话管理和会话状态维护
- 调用ConfiguratorAgent和ValidatorAgent
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
import logging
import asyncio
from datetime import datetime

# 导入现有的智能体
from core_lib.llm_integration_agents.llm_system_builder_agent import LLMSystemBuilderAgent
from core_lib.llm_integration_agents.llm_scenario_designer_agent import LLMScenarioDesignerAgent

# 导入配置验证工具
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenario", tags=["scenario"])

# 会话状态存储（生产环境应使用Redis等持久化存储）
session_store: Dict[str, Dict[str, Any]] = {}

# Pydantic模型定义
class ScenarioCreateRequest(BaseModel):
    """创建场景请求"""
    description: str
    user_id: Optional[str] = None
    project_name: Optional[str] = None

class ScenarioUpdateRequest(BaseModel):
    """更新场景请求"""
    session_id: str
    instruction: str
    context: Optional[Dict[str, Any]] = None

class ScenarioValidateRequest(BaseModel):
    """验证场景请求"""
    session_id: str

class ChiefModelingAgentResponse(BaseModel):
    """首席建模智能体响应"""
    session_id: str
    status: str  # "success", "clarification_needed", "error"
    message: str
    clarification_questions: Optional[List[str]] = None
    generated_config: Optional[Dict[str, Any]] = None
    next_steps: Optional[List[str]] = None

class ConfiguratorAgentResponse(BaseModel):
    """配置生成智能体响应"""
    config_yaml: str
    config_type: str  # "universal_config", "unified_config", "components"
    validation_status: str
    errors: Optional[List[str]] = None

class ChiefModelingAgent:
    """首席建模智能体 - 总调度师和项目经理"""
    
    def __init__(self):
        self.system_builder = None
        self.scenario_designer = None
        
    async def process_user_instruction(self, description: str, session_id: str) -> ChiefModelingAgentResponse:
        """
        处理用户的自然语言指令
        
        Args:
            description: 用户的自然语言描述
            session_id: 会话ID
            
        Returns:
            ChiefModelingAgentResponse: 处理结果
        """
        try:
            logger.info(f"ChiefModelingAgent processing instruction for session {session_id}: {description}")
            
            # 分析用户指令的复杂度和明确性
            analysis_result = await self._analyze_instruction(description)
            
            if analysis_result["needs_clarification"]:
                return ChiefModelingAgentResponse(
                    session_id=session_id,
                    status="clarification_needed",
                    message="需要更多信息来完成您的请求",
                    clarification_questions=analysis_result["questions"]
                )
            
            # 分解任务并生成结构化指令
            structured_tasks = await self._decompose_tasks(description, analysis_result)
            
            # 更新会话状态
            if session_id not in session_store:
                session_store[session_id] = {
                    "created_at": datetime.now().isoformat(),
                    "user_description": description,
                    "tasks": structured_tasks,
                    "current_config": None,
                    "conversation_history": []
                }
            
            session_store[session_id]["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "user_instruction",
                "content": description
            })
            
            # 调用ConfiguratorAgent生成配置
            configurator = ConfiguratorAgent()
            config_result = await configurator.generate_config(structured_tasks, session_id)
            
            session_store[session_id]["current_config"] = config_result.config_yaml
            
            return ChiefModelingAgentResponse(
                session_id=session_id,
                status="success",
                message="已成功生成仿真配置",
                generated_config={"yaml": config_result.config_yaml},
                next_steps=["验证配置", "运行仿真", "分析结果"]
            )
            
        except Exception as e:
            logger.error(f"ChiefModelingAgent error: {str(e)}")
            return ChiefModelingAgentResponse(
                session_id=session_id,
                status="error",
                message=f"处理指令时发生错误: {str(e)}"
            )
    
    async def _analyze_instruction(self, description: str) -> Dict[str, Any]:
        """
        分析用户指令的复杂度和明确性
        
        在实际实现中，这里会调用LLM API进行智能分析
        """
        # 简化的分析逻辑（实际应使用LLM）
        keywords = ["水库", "渠道", "河流", "闸门", "泵站", "reservoir", "canal", "river", "gate", "pump"]
        has_components = any(keyword in description.lower() for keyword in keywords)
        
        if not has_components:
            return {
                "needs_clarification": True,
                "questions": [
                    "请描述您要仿真的水利系统包含哪些组件（如水库、渠道、闸门等）？",
                    "您希望仿真多长时间？",
                    "有什么特定的控制策略或场景需要测试吗？"
                ]
            }
        
        return {
            "needs_clarification": False,
            "complexity": "medium",
            "components_identified": True
        }
    
    async def _decompose_tasks(self, description: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将用户指令分解为结构化任务
        
        在实际实现中，这里会使用LLM进行智能任务分解
        """
        # 简化的任务分解逻辑
        tasks = [
            {
                "action": "create_simulation",
                "description": description,
                "priority": 1,
                "agent": "configurator"
            },
            {
                "action": "validate_config",
                "priority": 2,
                "agent": "validator"
            }
        ]
        
        return tasks

class ConfiguratorAgent:
    """配置生成智能体 - YAML代码生成器"""
    
    async def generate_config(self, tasks: List[Dict[str, Any]], session_id: str) -> ConfiguratorAgentResponse:
        """
        根据结构化指令生成YAML配置
        
        Args:
            tasks: 结构化任务列表
            session_id: 会话ID
            
        Returns:
            ConfiguratorAgentResponse: 生成的配置
        """
        try:
            logger.info(f"ConfiguratorAgent generating config for session {session_id}")
            
            # 使用现有的LLMSystemBuilderAgent
            system_builder = LLMSystemBuilderAgent(f"builder_{session_id}", None)
            
            # 提取主要任务描述
            main_task = next((task for task in tasks if task["action"] == "create_simulation"), None)
            if not main_task:
                raise ValueError("No simulation creation task found")
            
            # 生成配置（这里使用简化的模板，实际应调用LLM）
            config_yaml = self._generate_universal_config_template(main_task["description"])
            
            return ConfiguratorAgentResponse(
                config_yaml=config_yaml,
                config_type="universal_config",
                validation_status="pending"
            )
            
        except Exception as e:
            logger.error(f"ConfiguratorAgent error: {str(e)}")
            return ConfiguratorAgentResponse(
                config_yaml="",
                config_type="universal_config",
                validation_status="error",
                errors=[str(e)]
            )
    
    def _generate_universal_config_template(self, description: str) -> str:
        """
        生成universal_config.yml模板
        
        实际实现中应使用LLM根据描述生成精确的配置
        """
        template = f"""# AI生成的仿真配置
# 基于描述: {description}

metadata:
  name: "AI生成的仿真场景"
  description: "{description}"
  version: "1.0"
  category: "ai_generated"

simulation:
  duration: 100
  dt: 1.0

components:
  - class: Reservoir
    id: main_reservoir
    inflow_topic: inflow/main_reservoir
    initial_state:
      volume: 1000.0
      water_level: 10.0
    parameters:
      surface_area: 100.0
      outlet_coeff: 0.7
      
  - class: Gate
    id: control_gate
    control_topic: control/control_gate
    initial_state:
      opening: 0.5
    parameters:
      max_opening: 1.0
      discharge_coeff: 0.8
      gate_width: 2.0

connections:
  - from: main_reservoir
    to: control_gate
    type: outlet

control:
  pid_controller:
    target_variable: main_reservoir.water_level
    control_variable: control_gate.opening
    setpoint: 12.0
    kp: 0.5
    ki: 0.1
    kd: 0.05
    output_limits: [0.0, 1.0]

inflow:
  main_reservoir:
    type: constant
    value: 10.0

output:
  variables:
    - main_reservoir.water_level
    - main_reservoir.volume
    - control_gate.opening
    - control_gate.outflow
  save_to_file: true
  plot: true
"""
        return template

class ValidatorAgent:
    """验证与诊断智能体 - 质量保证工程师"""
    
    async def validate_config(self, session_id: str) -> Dict[str, Any]:
        """
        验证配置文件
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 验证结果
        """
        try:
            if session_id not in session_store:
                raise ValueError(f"Session {session_id} not found")
            
            config_yaml = session_store[session_id].get("current_config")
            if not config_yaml:
                raise ValueError("No configuration found for validation")
            
            # 创建临时配置文件
            temp_config_path = Path(f"/tmp/temp_config_{session_id}.yml")
            temp_config_path.write_text(config_yaml, encoding='utf-8')
            
            # 调用config_check.py进行验证
            result = await self._run_config_check(temp_config_path)
            
            # 清理临时文件
            if temp_config_path.exists():
                temp_config_path.unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"ValidatorAgent error: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "suggestions": []
            }
    
    async def _run_config_check(self, config_path: Path) -> Dict[str, Any]:
        """
        运行配置检查脚本
        """
        try:
            # 运行config_check.py
            cmd = ["python", "examples/config_check.py", str(config_path)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent.parent
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "suggestions": [],
                    "output": stdout.decode('utf-8')
                }
            else:
                return {
                    "valid": False,
                    "errors": [stderr.decode('utf-8')],
                    "warnings": [],
                    "suggestions": ["请检查配置文件格式和必需字段"]
                }
                
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"配置验证失败: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }

# 实例化智能体
chief_agent = ChiefModelingAgent()
validator_agent = ValidatorAgent()

# API路由定义
@router.post("/create", response_model=ChiefModelingAgentResponse)
async def create_scenario(request: ScenarioCreateRequest):
    """
    创建新的仿真场景
    
    接收用户的自然语言描述，通过ChiefModelingAgent进行处理
    """
    session_id = str(uuid.uuid4())
    
    try:
        response = await chief_agent.process_user_instruction(
            description=request.description,
            session_id=session_id
        )
        
        logger.info(f"Created scenario session {session_id} for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update", response_model=ChiefModelingAgentResponse)
async def update_scenario(request: ScenarioUpdateRequest):
    """
    更新现有场景
    
    处理用户的后续指令和修改请求
    """
    try:
        if request.session_id not in session_store:
            raise HTTPException(status_code=404, detail="Session not found")
        
        response = await chief_agent.process_user_instruction(
            description=request.instruction,
            session_id=request.session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error updating scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/{session_id}")
async def validate_scenario(session_id: str):
    """
    验证场景配置
    
    使用ValidatorAgent验证当前配置的正确性
    """
    try:
        result = await validator_agent.validate_config(session_id)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error validating scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_scenario_status(session_id: str):
    """
    获取场景状态
    
    返回会话的当前状态和配置信息
    """
    try:
        if session_id not in session_store:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_store[session_id]
        return JSONResponse(content={
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "user_description": session_data["user_description"],
            "has_config": session_data["current_config"] is not None,
            "conversation_history": session_data["conversation_history"][-5:]  # 最近5条记录
        })
        
    except Exception as e:
        logger.error(f"Error getting scenario status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/{session_id}")
async def get_scenario_config(session_id: str):
    """
    获取场景配置
    
    返回当前生成的配置文件内容
    """
    try:
        if session_id not in session_store:
            raise HTTPException(status_code=404, detail="Session not found")
        
        config_yaml = session_store[session_id].get("current_config")
        if not config_yaml:
            raise HTTPException(status_code=404, detail="No configuration found")
        
        return JSONResponse(content={
            "session_id": session_id,
            "config_yaml": config_yaml,
            "config_type": "universal_config"
        })
        
    except Exception as e:
        logger.error(f"Error getting scenario config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_scenario_session(session_id: str):
    """
    删除场景会话
    
    清理会话数据和临时文件
    """
    try:
        if session_id in session_store:
            del session_store[session_id]
            logger.info(f"Deleted scenario session {session_id}")
        
        return JSONResponse(content={"message": "Session deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting scenario session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))