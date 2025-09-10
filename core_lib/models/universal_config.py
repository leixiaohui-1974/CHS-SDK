from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional

class UniversalConfig(BaseModel):
    """通用配置模型，用于验证配置文件的结构和数据类型"""
    
    # 仿真参数配置
    simulation: Dict[str, Any] = Field(
        ..., 
        description="仿真参数配置，包含时间步长、时长等信息"
    )
    
    # 组件配置
    components: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="组件配置，包含水库、闸门等各类组件的定义"
    )
    
    # 连接配置（可选）
    connections: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="组件之间的连接配置"
    )
    
    # 场景配置（可选）
    scenario: Optional[Dict[str, Any]] = Field(
        None, 
        description="场景配置信息"
    )
    
    # 验证仿真配置中至少包含必要字段
    @validator('simulation')
    def validate_simulation_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError("simulation字段必须是字典类型")
        # 检查必要的仿真参数
        if 'time_step' not in v:
            raise ValueError("simulation配置缺少time_step字段")
        if 'end_time' not in v:
            raise ValueError("simulation配置缺少end_time字段")
        # 验证时间步长和时长必须为正数
        if v['time_step'] <= 0:
            raise ValueError("time_step必须大于0")
        if v['end_time'] <= 0:
            raise ValueError("end_time必须大于0")
        return v
    
    # 验证组件配置
    @validator('components')
    def validate_components_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError("components字段必须是字典类型")
        if not v:
            raise ValueError("components不能为空字典")
        # 验证每个组件必须包含type字段
        for comp_name, comp_config in v.items():
            if not isinstance(comp_config, dict):
                raise ValueError(f"组件{comp_name}的配置必须是字典类型")
            if 'type' not in comp_config:
                raise ValueError(f"组件{comp_name}缺少type字段")
        return v
    
    # 验证连接配置（如果存在）
    @validator('connections')
    def validate_connections_config(cls, v, values):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("connections字段必须是列表类型")
        # 验证每个连接必须包含from和to字段
        for conn in v:
            if not isinstance(conn, dict):
                raise ValueError("连接配置必须是字典类型")
            if 'from' not in conn:
                raise ValueError("连接配置缺少from字段")
            if 'to' not in conn:
                raise ValueError("连接配置缺少to字段")
        return v

    class Config:
        arbitrary_types_allowed = True