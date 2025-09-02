from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import uuid
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
import tempfile
import os

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/configurator", tags=["configurator"])

# 全局存储
configurator_sessions: Dict[str, Dict] = {}
configurator_tasks: Dict[str, Dict] = {}

# ============================================================================
# Pydantic 模型定义
# ============================================================================

class ConfigurationInstruction(BaseModel):
    """配置指令模型"""
    action: str = Field(..., description="操作类型: add_component, modify_component, remove_component, set_parameter, etc.")
    target_type: str = Field(..., description="目标类型: component, simulation, debug, performance, etc.")
    target_name: Optional[str] = Field(None, description="目标名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数字典")
    section_path: Optional[str] = Field(None, description="配置节路径，如 'simulation.time' 或 'debug.data_collection'")
    
class ConfigGenerationRequest(BaseModel):
    """配置生成请求"""
    session_id: str = Field(..., description="会话ID")
    instructions: List[ConfigurationInstruction] = Field(..., description="配置指令列表")
    base_config: Optional[Dict[str, Any]] = Field(None, description="基础配置")
    template_type: str = Field("standard", description="模板类型: standard, minimal, advanced")
    validation_enabled: bool = Field(True, description="是否启用验证")
    
class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    session_id: str = Field(..., description="会话ID")
    config_content: str = Field(..., description="YAML配置内容")
    merge_strategy: str = Field("replace", description="合并策略: replace, merge, append")
    
class ConfigGenerationResponse(BaseModel):
    """配置生成响应"""
    task_id: str = Field(..., description="任务ID")
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态: pending, processing, completed, failed")
    config_content: Optional[str] = Field(None, description="生成的YAML配置")
    validation_results: Optional[Dict] = Field(None, description="验证结果")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
class ConfigSessionInfo(BaseModel):
    """配置会话信息"""
    session_id: str = Field(..., description="会话ID")
    current_config: Optional[str] = Field(None, description="当前配置")
    history: List[Dict] = Field(default_factory=list, description="操作历史")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_modified: datetime = Field(default_factory=datetime.now, description="最后修改时间")
    
# ============================================================================
# ConfiguratorAgent 核心类
# ============================================================================

class ConfiguratorAgent:
    """配置生成智能体 - 精确的YAML代码生成器"""
    
    def __init__(self):
        self.template_path = Path("E:/OneDrive/Documents/GitHub/CHS-SDK/core_lib/config")
        self.base_templates = {
            "standard": "universal_config_template.yml",
            "minimal": "example_universal_config.yml",
            "advanced": "universal_config_template.yml"
        }
        
    async def generate_config(self, instructions: List[ConfigurationInstruction], 
                            base_config: Optional[Dict] = None,
                            template_type: str = "standard") -> Dict[str, Any]:
        """根据指令生成YAML配置"""
        try:
            # 1. 加载基础模板
            config = await self._load_base_template(template_type)
            
            # 2. 应用基础配置
            if base_config:
                config = self._merge_configs(config, base_config)
                
            # 3. 执行配置指令
            for instruction in instructions:
                config = await self._apply_instruction(config, instruction)
                
            return config
            
        except Exception as e:
            logger.error(f"配置生成失败: {str(e)}")
            raise
            
    async def _load_base_template(self, template_type: str) -> Dict[str, Any]:
        """加载基础模板"""
        template_file = self.base_templates.get(template_type, "universal_config_template.yml")
        template_path = self.template_path / template_file
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"模板文件未找到: {template_path}，使用默认配置")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "simulation": {
                "name": "默认仿真",
                "description": "自动生成的仿真配置",
                "version": "1.0.0",
                "time": {
                    "start_time": 0.0,
                    "end_time": 100.0,
                    "time_step": 0.1,
                    "units": "seconds"
                }
            },
            "debug": {
                "enabled": True,
                "log_level": "INFO"
            }
        }
        
    async def _apply_instruction(self, config: Dict[str, Any], 
                               instruction: ConfigurationInstruction) -> Dict[str, Any]:
        """应用单个配置指令"""
        action = instruction.action
        target_type = instruction.target_type
        parameters = instruction.parameters
        section_path = instruction.section_path
        
        if action == "add_component":
            return self._add_component(config, target_type, instruction.target_name, parameters)
        elif action == "modify_component":
            return self._modify_component(config, target_type, instruction.target_name, parameters)
        elif action == "remove_component":
            return self._remove_component(config, target_type, instruction.target_name)
        elif action == "set_parameter":
            return self._set_parameter(config, section_path, parameters)
        elif action == "set_simulation_time":
            return self._set_simulation_time(config, parameters)
        elif action == "enable_debug":
            return self._enable_debug(config, parameters)
        elif action == "configure_performance":
            return self._configure_performance(config, parameters)
        elif action == "setup_visualization":
            return self._setup_visualization(config, parameters)
        else:
            logger.warning(f"未知的配置指令: {action}")
            return config
            
    def _add_component(self, config: Dict, component_type: str, name: str, params: Dict) -> Dict:
        """添加组件"""
        if "components" not in config:
            config["components"] = {}
            
        if component_type not in config["components"]:
            config["components"][component_type] = {}
            
        config["components"][component_type][name] = params
        return config
        
    def _modify_component(self, config: Dict, component_type: str, name: str, params: Dict) -> Dict:
        """修改组件"""
        if ("components" in config and 
            component_type in config["components"] and 
            name in config["components"][component_type]):
            config["components"][component_type][name].update(params)
        return config
        
    def _remove_component(self, config: Dict, component_type: str, name: str) -> Dict:
        """移除组件"""
        if ("components" in config and 
            component_type in config["components"] and 
            name in config["components"][component_type]):
            del config["components"][component_type][name]
        return config
        
    def _set_parameter(self, config: Dict, section_path: str, params: Dict) -> Dict:
        """设置参数"""
        if not section_path:
            config.update(params)
            return config
            
        # 解析路径并设置值
        path_parts = section_path.split('.')
        current = config
        
        # 导航到目标位置
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # 设置最终值
        if len(path_parts) == 1:
            current.update(params)
        else:
            final_key = path_parts[-1]
            if final_key not in current:
                current[final_key] = {}
            if isinstance(current[final_key], dict):
                current[final_key].update(params)
            else:
                current[final_key] = params
                
        return config
        
    def _set_simulation_time(self, config: Dict, params: Dict) -> Dict:
        """设置仿真时间参数"""
        if "simulation" not in config:
            config["simulation"] = {}
        if "time" not in config["simulation"]:
            config["simulation"]["time"] = {}
            
        config["simulation"]["time"].update(params)
        return config
        
    def _enable_debug(self, config: Dict, params: Dict) -> Dict:
        """启用调试功能"""
        if "debug" not in config:
            config["debug"] = {}
            
        default_debug = {
            "enabled": True,
            "log_level": "DEBUG",
            "data_collection": {
                "enabled": True,
                "interval": 5.0
            }
        }
        
        config["debug"].update(default_debug)
        config["debug"].update(params)
        return config
        
    def _configure_performance(self, config: Dict, params: Dict) -> Dict:
        """配置性能监控"""
        if "performance" not in config:
            config["performance"] = {}
            
        default_performance = {
            "enabled": True,
            "track_timing": True,
            "track_memory": True,
            "metrics": {
                "enabled": True,
                "collection_interval": 1.0
            }
        }
        
        config["performance"].update(default_performance)
        config["performance"].update(params)
        return config
        
    def _setup_visualization(self, config: Dict, params: Dict) -> Dict:
        """设置可视化"""
        if "visualization" not in config:
            config["visualization"] = {}
            
        default_viz = {
            "enabled": True,
            "plots": {
                "enabled": True,
                "save_plots": True,
                "format": ["png", "svg"]
            }
        }
        
        config["visualization"].update(default_viz)
        config["visualization"].update(params)
        return config
        
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def config_to_yaml(self, config: Dict[str, Any]) -> str:
        """将配置转换为YAML字符串"""
        try:
            return yaml.dump(config, default_flow_style=False, allow_unicode=True, indent=2)
        except Exception as e:
            logger.error(f"YAML转换失败: {str(e)}")
            raise
            
    async def validate_config(self, config_content: str) -> Dict[str, Any]:
        """验证配置文件"""
        try:
            # 1. YAML语法验证
            config = yaml.safe_load(config_content)
            
            # 2. 基本结构验证
            validation_results = {
                "syntax_valid": True,
                "structure_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # 检查必需的节
            required_sections = ["simulation"]
            for section in required_sections:
                if section not in config:
                    validation_results["errors"].append(f"缺少必需的配置节: {section}")
                    validation_results["structure_valid"] = False
                    
            # 检查仿真时间配置
            if "simulation" in config and "time" in config["simulation"]:
                time_config = config["simulation"]["time"]
                if "start_time" in time_config and "end_time" in time_config:
                    if time_config["start_time"] >= time_config["end_time"]:
                        validation_results["errors"].append("开始时间必须小于结束时间")
                        
            return validation_results
            
        except yaml.YAMLError as e:
            return {
                "syntax_valid": False,
                "structure_valid": False,
                "errors": [f"YAML语法错误: {str(e)}"],
                "warnings": []
            }
            
# 创建全局智能体实例
configurator_agent = ConfiguratorAgent()

# ============================================================================
# API 路由定义
# ============================================================================

@router.post("/generate", response_model=ConfigGenerationResponse)
async def generate_config(request: ConfigGenerationRequest, background_tasks: BackgroundTasks):
    """生成配置文件"""
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_info = {
        "task_id": task_id,
        "session_id": request.session_id,
        "status": "pending",
        "config_content": None,
        "validation_results": None,
        "errors": [],
        "warnings": [],
        "created_at": datetime.now(),
        "completed_at": None
    }
    
    configurator_tasks[task_id] = task_info
    
    # 启动后台任务
    background_tasks.add_task(
        _process_config_generation,
        task_id,
        request.instructions,
        request.base_config,
        request.template_type,
        request.validation_enabled
    )
    
    return ConfigGenerationResponse(**task_info)

async def _process_config_generation(task_id: str, instructions: List[ConfigurationInstruction],
                                   base_config: Optional[Dict], template_type: str,
                                   validation_enabled: bool):
    """处理配置生成任务"""
    try:
        # 更新任务状态
        configurator_tasks[task_id]["status"] = "processing"
        
        # 生成配置
        config = await configurator_agent.generate_config(
            instructions, base_config, template_type
        )
        
        # 转换为YAML
        config_content = configurator_agent.config_to_yaml(config)
        
        # 验证配置
        validation_results = None
        if validation_enabled:
            validation_results = await configurator_agent.validate_config(config_content)
            
        # 更新任务结果
        configurator_tasks[task_id].update({
            "status": "completed",
            "config_content": config_content,
            "validation_results": validation_results,
            "completed_at": datetime.now()
        })
        
        logger.info(f"配置生成任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"配置生成任务失败: {task_id}, 错误: {str(e)}")
        configurator_tasks[task_id].update({
            "status": "failed",
            "errors": [str(e)],
            "completed_at": datetime.now()
        })

@router.get("/tasks/{task_id}", response_model=ConfigGenerationResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in configurator_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    return ConfigGenerationResponse(**configurator_tasks[task_id])

@router.post("/sessions/{session_id}/update")
async def update_config(session_id: str, request: ConfigUpdateRequest):
    """更新配置"""
    try:
        # 验证配置
        validation_results = await configurator_agent.validate_config(request.config_content)
        
        # 更新会话
        if session_id not in configurator_sessions:
            configurator_sessions[session_id] = {
                "session_id": session_id,
                "current_config": None,
                "history": [],
                "created_at": datetime.now(),
                "last_modified": datetime.now()
            }
            
        # 保存历史
        if configurator_sessions[session_id]["current_config"]:
            configurator_sessions[session_id]["history"].append({
                "timestamp": datetime.now(),
                "config": configurator_sessions[session_id]["current_config"],
                "action": "backup"
            })
            
        # 更新当前配置
        configurator_sessions[session_id]["current_config"] = request.config_content
        configurator_sessions[session_id]["last_modified"] = datetime.now()
        
        return {
            "success": True,
            "session_id": session_id,
            "validation_results": validation_results,
            "message": "配置更新成功"
        }
        
    except Exception as e:
        logger.error(f"配置更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

@router.get("/sessions/{session_id}", response_model=ConfigSessionInfo)
async def get_session_info(session_id: str):
    """获取会话信息"""
    if session_id not in configurator_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
        
    return ConfigSessionInfo(**configurator_sessions[session_id])

@router.get("/sessions/{session_id}/config")
async def get_current_config(session_id: str):
    """获取当前配置"""
    if session_id not in configurator_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
        
    session = configurator_sessions[session_id]
    if not session["current_config"]:
        raise HTTPException(status_code=404, detail="会话中没有配置")
        
    return {
        "session_id": session_id,
        "config_content": session["current_config"],
        "last_modified": session["last_modified"]
    }

@router.post("/validate")
async def validate_config(config_content: str = Field(..., description="YAML配置内容")):
    """验证配置文件"""
    try:
        validation_results = await configurator_agent.validate_config(config_content)
        return {
            "success": True,
            "validation_results": validation_results
        }
    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")

@router.get("/templates")
async def list_templates():
    """列出可用的配置模板"""
    return {
        "templates": [
            {
                "name": "standard",
                "description": "标准配置模板，包含所有功能模块",
                "file": "universal_config_template.yml"
            },
            {
                "name": "minimal",
                "description": "最小配置模板，仅包含基本功能",
                "file": "example_universal_config.yml"
            },
            {
                "name": "advanced",
                "description": "高级配置模板，包含所有高级功能",
                "file": "universal_config_template.yml"
            }
        ]
    }

@router.get("/tasks")
async def list_tasks():
    """列出所有配置生成任务"""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "session_id": task_info["session_id"],
                "status": task_info["status"],
                "created_at": task_info["created_at"],
                "completed_at": task_info.get("completed_at")
            }
            for task_id, task_info in configurator_tasks.items()
        ]
    }

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除配置生成任务"""
    if task_id not in configurator_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    del configurator_tasks[task_id]
    return {"success": True, "message": f"任务 {task_id} 已删除"}

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除配置会话"""
    if session_id not in configurator_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
        
    del configurator_sessions[session_id]
    return {"success": True, "message": f"会话 {session_id} 已删除"}

@router.post("/cleanup")
async def cleanup_tasks():
    """清理已完成的任务"""
    completed_tasks = [
        task_id for task_id, task_info in configurator_tasks.items()
        if task_info["status"] in ["completed", "failed"]
    ]
    
    for task_id in completed_tasks:
        del configurator_tasks[task_id]
        
    return {
        "success": True,
        "message": f"已清理 {len(completed_tasks)} 个已完成的任务",
        "cleaned_tasks": completed_tasks
    }