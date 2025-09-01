from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# 仿真状态枚举
class SimulationStatus(str, Enum):
    CREATED = "created"
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"
    CRASHED = "crashed"

# 组件类型枚举
class ComponentType(str, Enum):
    RESERVOIR = "reservoir"
    GATE = "gate"
    PIPE = "pipe"
    CANAL = "canal"
    PUMP = "pump"
    VALVE = "valve"
    JUNCTION = "junction"
    SENSOR = "sensor"

# 仿真会话模型
class SimulationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="会话ID")
    name: str = Field(..., description="会话名称")
    description: Optional[str] = Field(default=None, description="会话描述")
    status: SimulationStatus = Field(default=SimulationStatus.IDLE, description="仿真状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    ended_at: Optional[datetime] = Field(default=None, description="结束时间")
    current_step: int = Field(default=0, description="当前步数")
    total_steps: Optional[int] = Field(default=None, description="总步数")
    time_step: float = Field(default=1.0, description="时间步长 (s)")
    simulation_time: float = Field(default=0.0, description="仿真时间 (s)")
    real_time_factor: float = Field(default=1.0, description="实时倍率")
    configuration: Optional[Dict[str, Any]] = Field(default=None, description="仿真配置")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "name": "水库调度仿真",
                "description": "测试水库在不同调度策略下的表现",
                "status": "running",
                "created_at": "2024-01-20T10:00:00Z",
                "started_at": "2024-01-20T10:05:00Z",
                "current_step": 150,
                "total_steps": 1000,
                "time_step": 1.0,
                "simulation_time": 150.0,
                "real_time_factor": 10.0
            }
        }

# 创建仿真请求模型
class CreateSimulationRequest(BaseModel):
    name: str = Field(..., description="仿真名称")
    description: Optional[str] = Field(default=None, description="仿真描述")
    configuration: Dict[str, Any] = Field(..., description="仿真配置")
    time_step: float = Field(default=1.0, gt=0, description="时间步长 (s)")
    total_steps: Optional[int] = Field(default=None, gt=0, description="总步数")
    real_time_factor: float = Field(default=1.0, gt=0, description="实时倍率")
    auto_start: bool = Field(default=False, description="是否自动开始")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "水库调度仿真",
                "description": "测试不同调度策略",
                "configuration": {
                    "components": {
                        "reservoirs": [{"id": "res1", "capacity": 1000000}],
                        "gates": [{"id": "gate1", "max_flow": 100}]
                    },
                    "topology": {
                        "connections": [{"from": "res1", "to": "gate1"}]
                    }
                },
                "time_step": 1.0,
                "total_steps": 1000,
                "real_time_factor": 10.0,
                "auto_start": False
            }
        }

# 仿真响应模型
class SimulationResponse(BaseModel):
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 仿真控制请求模型
class SimulationControlRequest(BaseModel):
    action: str = Field(..., description="控制动作: start, pause, resume, stop, reset")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="动作参数")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "start",
                "parameters": {
                    "real_time_factor": 1.0,
                    "max_steps": 1000
                }
            }
        }

# 组件配置基础模型
class ComponentConfig(BaseModel):
    id: str = Field(..., description="组件ID")
    name: str = Field(..., description="组件名称")
    type: ComponentType = Field(..., description="组件类型")
    position: Optional[Dict[str, float]] = Field(default=None, description="位置坐标")
    properties: Dict[str, Any] = Field(default_factory=dict, description="组件属性")
    initial_state: Optional[Dict[str, Any]] = Field(default=None, description="初始状态")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "reservoir_1",
                "name": "主水库",
                "type": "reservoir",
                "position": {"x": 100, "y": 200},
                "properties": {
                    "capacity": 1000000,
                    "max_level": 20.0,
                    "min_level": 5.0
                },
                "initial_state": {
                    "water_level": 15.0,
                    "volume": 750000
                }
            }
        }

# 水库配置模型
class ReservoirConfig(ComponentConfig):
    capacity: float = Field(..., gt=0, description="容量 (m³)")
    max_level: float = Field(..., gt=0, description="最大水位 (m)")
    min_level: float = Field(default=0.0, ge=0, description="最小水位 (m)")
    surface_area: Optional[float] = Field(default=None, gt=0, description="表面积 (m²)")
    
    @validator('min_level')
    def validate_levels(cls, v, values):
        if 'max_level' in values and v >= values['max_level']:
            raise ValueError('min_level must be less than max_level')
        return v

# 闸门配置模型
class GateConfig(ComponentConfig):
    max_flow: float = Field(..., gt=0, description="最大流量 (m³/s)")
    max_opening: float = Field(default=1.0, gt=0, le=1.0, description="最大开度")
    min_opening: float = Field(default=0.0, ge=0, description="最小开度")
    operation_time: float = Field(default=60.0, gt=0, description="操作时间 (s)")
    
    @validator('min_opening')
    def validate_openings(cls, v, values):
        if 'max_opening' in values and v >= values['max_opening']:
            raise ValueError('min_opening must be less than max_opening')
        return v

# 管道配置模型
class PipeConfig(ComponentConfig):
    diameter: float = Field(..., gt=0, description="直径 (m)")
    length: float = Field(..., gt=0, description="长度 (m)")
    roughness: float = Field(default=0.001, gt=0, description="粗糙度")
    material: Optional[str] = Field(default=None, description="材料")
    max_pressure: Optional[float] = Field(default=None, gt=0, description="最大压力 (Pa)")

# 运河配置模型
class CanalConfig(ComponentConfig):
    width: float = Field(..., gt=0, description="宽度 (m)")
    depth: float = Field(..., gt=0, description="深度 (m)")
    length: float = Field(..., gt=0, description="长度 (m)")
    slope: float = Field(default=0.001, gt=0, description="坡度")
    manning_coefficient: float = Field(default=0.025, gt=0, description="曼宁系数")

# 连接配置模型
class ConnectionConfig(BaseModel):
    id: str = Field(..., description="连接ID")
    from_component: str = Field(..., description="源组件ID")
    to_component: str = Field(..., description="目标组件ID")
    from_port: Optional[str] = Field(default=None, description="源端口")
    to_port: Optional[str] = Field(default=None, description="目标端口")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="连接属性")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "conn_1",
                "from_component": "reservoir_1",
                "to_component": "gate_1",
                "from_port": "outlet",
                "to_port": "inlet",
                "properties": {
                    "pipe_diameter": 1.5,
                    "pipe_length": 100.0
                }
            }
        }

# 仿真配置模型
class SimulationConfig(BaseModel):
    components: List[ComponentConfig] = Field(..., description="组件配置列表")
    connections: List[ConnectionConfig] = Field(..., description="连接配置列表")
    global_parameters: Optional[Dict[str, Any]] = Field(default=None, description="全局参数")
    solver_settings: Optional[Dict[str, Any]] = Field(default=None, description="求解器设置")
    output_settings: Optional[Dict[str, Any]] = Field(default=None, description="输出设置")
    
    class Config:
        schema_extra = {
            "example": {
                "components": [
                    {
                        "id": "reservoir_1",
                        "name": "主水库",
                        "type": "reservoir",
                        "properties": {"capacity": 1000000}
                    }
                ],
                "connections": [
                    {
                        "id": "conn_1",
                        "from_component": "reservoir_1",
                        "to_component": "gate_1"
                    }
                ],
                "global_parameters": {
                    "gravity": 9.81,
                    "water_density": 1000.0
                },
                "solver_settings": {
                    "method": "runge_kutta",
                    "tolerance": 1e-6
                }
            }
        }

# 仿真结果模型
class SimulationResult(BaseModel):
    session_id: str = Field(..., description="会话ID")
    step: int = Field(..., description="步数")
    timestamp: float = Field(..., description="仿真时间戳")
    components_data: List[Dict[str, Any]] = Field(..., description="组件数据")
    metrics: Optional[Dict[str, float]] = Field(default=None, description="仿真指标")
    events: Optional[List[Dict[str, Any]]] = Field(default=None, description="事件列表")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "step": 100,
                "timestamp": 100.0,
                "components_data": [
                    {
                        "id": "reservoir_1",
                        "type": "reservoir",
                        "water_level": 15.5,
                        "volume": 775000
                    }
                ],
                "metrics": {
                    "total_flow": 500.0,
                    "energy_consumption": 1200.0
                },
                "events": [
                    {
                        "type": "warning",
                        "message": "Water level approaching maximum",
                        "component_id": "reservoir_1"
                    }
                ]
            }
        }

# 仿真统计模型
class SimulationStatistics(BaseModel):
    session_id: str = Field(..., description="会话ID")
    total_steps: int = Field(..., description="总步数")
    completed_steps: int = Field(..., description="已完成步数")
    progress: float = Field(..., ge=0.0, le=1.0, description="进度 (0-1)")
    elapsed_time: float = Field(..., description="已用时间 (s)")
    estimated_remaining_time: Optional[float] = Field(default=None, description="预计剩余时间 (s)")
    average_step_time: float = Field(..., description="平均步时间 (s)")
    performance_metrics: Optional[Dict[str, float]] = Field(default=None, description="性能指标")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "total_steps": 1000,
                "completed_steps": 150,
                "progress": 0.15,
                "elapsed_time": 75.0,
                "estimated_remaining_time": 425.0,
                "average_step_time": 0.5,
                "performance_metrics": {
                    "cpu_usage": 45.5,
                    "memory_usage": 62.3,
                    "fps": 60.0
                }
            }
        }

# 仿真事件模型
class SimulationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="事件ID")
    session_id: str = Field(..., description="会话ID")
    timestamp: float = Field(..., description="事件时间戳")
    step: int = Field(..., description="事件步数")
    event_type: str = Field(..., description="事件类型")
    severity: str = Field(default="info", description="严重程度")
    message: str = Field(..., description="事件消息")
    component_id: Optional[str] = Field(default=None, description="相关组件ID")
    data: Optional[Dict[str, Any]] = Field(default=None, description="事件数据")
    acknowledged: bool = Field(default=False, description="是否已确认")
    
    class Config:
        schema_extra = {
            "example": {
                "event_id": "event_001",
                "session_id": "session_123",
                "timestamp": 150.0,
                "step": 150,
                "event_type": "threshold_exceeded",
                "severity": "warning",
                "message": "Water level exceeds 90% of capacity",
                "component_id": "reservoir_1",
                "data": {
                    "current_level": 18.0,
                    "threshold": 18.0,
                    "capacity_percentage": 0.9
                },
                "acknowledged": False
            }
        }

# 控制动作模型
class ControlAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="动作ID")
    session_id: str = Field(..., description="会话ID")
    timestamp: float = Field(..., description="动作时间戳")
    action_type: str = Field(..., description="动作类型")
    target_component: str = Field(..., description="目标组件ID")
    parameters: Dict[str, Any] = Field(..., description="动作参数")
    status: str = Field(default="pending", description="动作状态")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    
    class Config:
        schema_extra = {
            "example": {
                "action_id": "action_001",
                "session_id": "session_123",
                "timestamp": 150.0,
                "action_type": "set_gate_opening",
                "target_component": "gate_1",
                "parameters": {
                    "opening": 0.8,
                    "duration": 30.0
                },
                "status": "completed",
                "result": {
                    "success": True,
                    "final_opening": 0.8,
                    "execution_time": 28.5
                }
            }
        }

# 仿真快照模型
class SimulationSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="快照ID")
    session_id: str = Field(..., description="会话ID")
    timestamp: float = Field(..., description="快照时间戳")
    step: int = Field(..., description="快照步数")
    name: Optional[str] = Field(default=None, description="快照名称")
    description: Optional[str] = Field(default=None, description="快照描述")
    state_data: Dict[str, Any] = Field(..., description="状态数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "snapshot_id": "snapshot_001",
                "session_id": "session_123",
                "timestamp": 150.0,
                "step": 150,
                "name": "高水位状态",
                "description": "水库达到90%容量时的状态",
                "state_data": {
                    "components": {
                        "reservoir_1": {"water_level": 18.0, "volume": 900000}
                    },
                    "global_state": {"total_volume": 900000}
                }
            }
        }