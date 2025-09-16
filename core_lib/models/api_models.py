"""
Pydantic models for the main API request body.

This file defines the top-level structures that aggregate the component,
agent, and topology models into a single, validatable request object
for the /run_simulation endpoint.
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Union, Literal, Any, Dict
from datetime import datetime

# Import parameter models from other files
from .physical_models import (
    ReservoirModel,
    GateModel,
    PipeModel,
    UnifiedCanalModel,
)
from .agent_models import (
    GateControlAgentParams,
    ReservoirPerceptionAgentParams,
    CSVInflowAgentParams,
)

# --- Components Model ---

class ComponentsModel(BaseModel):
    """A container for all physical components in the simulation, grouped by type."""
    reservoirs: List[ReservoirModel] = Field(default_factory=list, description="List of reservoir components.")
    gates: List[GateModel] = Field(default_factory=list, description="List of gate components.")
    pipes: List[PipeModel] = Field(default_factory=list, description="List of pipe components.")
    unified_canals: List[UnifiedCanalModel] = Field(default_factory=list, description="List of unified canal components.")

    def get_all_component_names(self) -> List[str]:
        """Helper method to get a flat list of all component names for validation."""
        names = []
        for component_list in [self.reservoirs, self.gates, self.pipes, self.unified_canals]:
            for component in component_list:
                names.append(component.name)
        return names

# --- Topology Model ---

class TopologyConnectionModel(BaseModel):
    """Defines a single connection between two components."""
    upstream: str = Field(..., description="Name of the upstream component.")
    downstream: str = Field(..., description="Name of the downstream component.")

class TopologyModel(BaseModel):
    """Defines the connection graph of the physical components."""
    connections: List[TopologyConnectionModel] = Field(default_factory=list, description="List of all connections in the system.")

# --- Agent Models ---

class GenericAgentConfig(BaseModel):
    """A generic model for any agent configuration."""
    id: str = Field(..., description="Unique identifier for the agent instance.")
    class_name: str = Field(..., alias="class", description="The Python class for the agent.")
    params: Dict[str, Any] = Field({}, description="Parameters for the agent's constructor.")


class AgentsModel(BaseModel):
    """A container for all agent configurations."""
    agents: List[GenericAgentConfig]


# --- Main API Request Body Model ---

class SimulationRequest(BaseModel):
    """
    The main request body for the /run_simulation endpoint.
    It includes the full definition of the simulation scenario.
    """
    components: ComponentsModel
    topology: TopologyModel
    agents: AgentsModel

    @root_validator(skip_on_failure=True)
    def validate_topology_and_agents(cls, values):
        """
        Performs cross-model validation after individual model validation passes.
        1. Checks that all components in the topology exist in the components list.
        2. Checks that all `target_component` fields in agent params exist.
        """
        components = values.get('components')
        topology = values.get('topology')
        agents = values.get('agents')
        
        if not components or not topology or not agents:
            return values
        
        all_component_names = components.get_all_component_names()
        
        # Validate topology connections
        for conn in topology.connections:
            if conn.upstream not in all_component_names:
                raise ValueError(f"Topology validation failed: Upstream component '{conn.upstream}' not found in components list.")
            if conn.downstream not in all_component_names:
                raise ValueError(f"Topology validation failed: Downstream component '{conn.downstream}' not found in components list.")
        
        # Validate agent targets
        for agent_config in agents.agents:
            # Check if agent params has target_component
            if isinstance(agent_config.params, dict) and 'target_component' in agent_config.params:
                target = agent_config.params['target_component']
                if target and target not in all_component_names:
                    raise ValueError(f"Agent validation failed: Agent '{agent_config.id}' targets non-existent component '{target}'.")
        
        return values

# --- Additional Models for Core Library ---

class SimulationResult(BaseModel):
    """仿真结果模型"""
    simulation_id: str = Field(..., description="仿真ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="仿真输出结果")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="仿真参数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    execution_time: float = Field(0.0, description="执行时间（秒）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    @validator('execution_time')
    def validate_execution_time(cls, v):
        """验证执行时间必须为非负数"""
        if v < 0:
            raise ValueError('执行时间不能为负数')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class BatchSimulationRequest(BaseModel):
    """批量仿真请求模型"""
    name: str = Field(..., description="批量任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    simulations: List[SimulationRequest] = Field(..., description="仿真请求列表")
    parallel_count: int = Field(4, description="并行执行数量")
    timeout_minutes: int = Field(60, description="超时时间（分钟）")
    auto_retry: bool = Field(True, description="是否自动重试")
    retry_count: int = Field(3, description="重试次数")
    notification_webhook: Optional[str] = Field(None, description="通知webhook")
    
    @validator('parallel_count')
    def validate_parallel_count(cls, v):
        """验证并行数量"""
        if v <= 0:
            raise ValueError('并行执行数量必须大于0')
        if v > 20:
            raise ValueError('并行执行数量不能超过20')
        return v
    
    @validator('timeout_minutes')
    def validate_timeout_minutes(cls, v):
        """验证超时时间"""
        if v <= 0:
            raise ValueError('超时时间必须大于0')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        """验证重试次数"""
        if v < 0:
            raise ValueError('重试次数不能为负数')
        if v > 10:
            raise ValueError('重试次数不能超过10')
        return v
    
    @validator('simulations')
    def validate_simulations_not_empty(cls, v):
        """验证仿真列表不为空"""
        if not v:
            raise ValueError('仿真请求列表不能为空')
        return v
