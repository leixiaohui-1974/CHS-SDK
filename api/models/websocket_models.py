from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

# WebSocket消息类型枚举
class WebSocketMessageType(str, Enum):
    DATA = "data"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SIMULATION_STATE = "simulation_state"
    CONTROL = "control"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    METRICS = "metrics"
    PERFORMANCE = "performance"
    COMPONENT_UPDATE = "component_update"
    TOPOLOGY_UPDATE = "topology_update"

# WebSocket消息基础模型
class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    payload: Any
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    message_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 仿真数据模型
class SimulationData(BaseModel):
    timestamp: float = Field(..., description="仿真时间戳")
    step: int = Field(..., description="仿真步数")
    components: List[Dict[str, Any]] = Field(default_factory=list, description="组件数据列表")
    metrics: Optional[Dict[str, float]] = Field(default=None, description="仿真指标")
    status: str = Field(default="running", description="仿真状态")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1234567890.123,
                "step": 100,
                "components": [
                    {
                        "id": "reservoir_1",
                        "type": "reservoir",
                        "water_level": 15.5,
                        "volume": 1000000.0,
                        "status": "normal"
                    }
                ],
                "metrics": {
                    "total_flow": 500.0,
                    "average_pressure": 2.5,
                    "energy_consumption": 1200.0
                },
                "status": "running"
            }
        }

# 组件数据基础模型
class ComponentData(BaseModel):
    id: str = Field(..., description="组件ID")
    type: str = Field(..., description="组件类型")
    timestamp: float = Field(..., description="数据时间戳")
    status: str = Field(default="normal", description="组件状态")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

# 水库数据模型
class ReservoirData(ComponentData):
    water_level: float = Field(..., description="水位 (m)")
    volume: float = Field(..., description="水量 (m³)")
    inflow: float = Field(default=0.0, description="入流量 (m³/s)")
    outflow: float = Field(default=0.0, description="出流量 (m³/s)")
    temperature: Optional[float] = Field(default=None, description="水温 (°C)")
    capacity: Optional[float] = Field(default=None, description="容量 (m³)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "reservoir_1",
                "type": "reservoir",
                "timestamp": 1234567890.123,
                "water_level": 15.5,
                "volume": 1000000.0,
                "inflow": 50.0,
                "outflow": 45.0,
                "temperature": 18.5,
                "capacity": 2000000.0,
                "status": "normal"
            }
        }

# 闸门数据模型
class GateData(ComponentData):
    opening: float = Field(..., ge=0.0, le=1.0, description="开度 (0-1)")
    flow_rate: float = Field(..., description="流量 (m³/s)")
    upstream_level: Optional[float] = Field(default=None, description="上游水位 (m)")
    downstream_level: Optional[float] = Field(default=None, description="下游水位 (m)")
    pressure_difference: Optional[float] = Field(default=None, description="压差 (Pa)")
    operation_mode: str = Field(default="manual", description="操作模式")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "gate_1",
                "type": "gate",
                "timestamp": 1234567890.123,
                "opening": 0.75,
                "flow_rate": 25.0,
                "upstream_level": 15.5,
                "downstream_level": 12.0,
                "pressure_difference": 34300.0,
                "operation_mode": "automatic",
                "status": "normal"
            }
        }

# 管道数据模型
class PipeData(ComponentData):
    flow_rate: float = Field(..., description="流量 (m³/s)")
    velocity: float = Field(..., description="流速 (m/s)")
    pressure: float = Field(..., description="压力 (Pa)")
    diameter: Optional[float] = Field(default=None, description="直径 (m)")
    length: Optional[float] = Field(default=None, description="长度 (m)")
    roughness: Optional[float] = Field(default=None, description="粗糙度")
    head_loss: Optional[float] = Field(default=None, description="水头损失 (m)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "pipe_1",
                "type": "pipe",
                "timestamp": 1234567890.123,
                "flow_rate": 30.0,
                "velocity": 2.5,
                "pressure": 250000.0,
                "diameter": 1.2,
                "length": 500.0,
                "roughness": 0.001,
                "head_loss": 0.5,
                "status": "normal"
            }
        }

# 运河数据模型
class CanalData(ComponentData):
    water_level: float = Field(..., description="水位 (m)")
    flow_rate: float = Field(..., description="流量 (m³/s)")
    velocity: float = Field(..., description="流速 (m/s)")
    width: Optional[float] = Field(default=None, description="宽度 (m)")
    depth: Optional[float] = Field(default=None, description="深度 (m)")
    slope: Optional[float] = Field(default=None, description="坡度")
    manning_coefficient: Optional[float] = Field(default=None, description="曼宁系数")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "canal_1",
                "type": "canal",
                "timestamp": 1234567890.123,
                "water_level": 3.5,
                "flow_rate": 15.0,
                "velocity": 1.2,
                "width": 10.0,
                "depth": 4.0,
                "slope": 0.001,
                "manning_coefficient": 0.025,
                "status": "normal"
            }
        }

# 仿真指标模型
class SimulationMetrics(BaseModel):
    timestamp: float = Field(..., description="时间戳")
    step: int = Field(..., description="仿真步数")
    total_volume: float = Field(..., description="总水量 (m³)")
    total_flow: float = Field(..., description="总流量 (m³/s)")
    average_pressure: float = Field(..., description="平均压力 (Pa)")
    energy_consumption: float = Field(..., description="能耗 (kWh)")
    efficiency: float = Field(..., ge=0.0, le=1.0, description="效率 (0-1)")
    water_loss: float = Field(default=0.0, description="水损失 (m³)")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1234567890.123,
                "step": 100,
                "total_volume": 5000000.0,
                "total_flow": 500.0,
                "average_pressure": 200000.0,
                "energy_consumption": 1200.0,
                "efficiency": 0.85,
                "water_loss": 50.0
            }
        }

# 性能数据模型
class PerformanceData(BaseModel):
    timestamp: float = Field(..., description="时间戳")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU使用率 (%)")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="内存使用率 (%)")
    fps: float = Field(..., description="帧率 (FPS)")
    latency: float = Field(..., description="延迟 (ms)")
    throughput: float = Field(..., description="吞吐量 (ops/s)")
    active_connections: int = Field(..., description="活跃连接数")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1234567890.123,
                "cpu_usage": 45.5,
                "memory_usage": 62.3,
                "fps": 60.0,
                "latency": 15.2,
                "throughput": 1000.0,
                "active_connections": 5
            }
        }

# 错误数据模型
class ErrorData(BaseModel):
    timestamp: float = Field(..., description="时间戳")
    error_id: str = Field(..., description="错误ID")
    error_type: str = Field(..., description="错误类型")
    severity: str = Field(..., description="严重程度")
    message: str = Field(..., description="错误消息")
    component_id: Optional[str] = Field(default=None, description="相关组件ID")
    stack_trace: Optional[str] = Field(default=None, description="堆栈跟踪")
    context: Optional[Dict[str, Any]] = Field(default=None, description="错误上下文")
    resolved: bool = Field(default=False, description="是否已解决")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1234567890.123,
                "error_id": "err_001",
                "error_type": "simulation_error",
                "severity": "warning",
                "message": "Water level exceeds normal range",
                "component_id": "reservoir_1",
                "context": {
                    "current_level": 18.5,
                    "max_level": 18.0
                },
                "resolved": False
            }
        }

# 订阅请求模型
class SubscriptionRequest(BaseModel):
    topics: List[str] = Field(..., description="订阅主题列表")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    
    class Config:
        schema_extra = {
            "example": {
                "topics": ["simulation_data", "performance_metrics"],
                "filters": {
                    "component_types": ["reservoir", "gate"],
                    "severity": ["error", "warning"]
                }
            }
        }

# 控制命令模型
class ControlCommand(BaseModel):
    action: str = Field(..., description="控制动作")
    target: Optional[str] = Field(default=None, description="目标对象")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="参数")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "set_gate_opening",
                "target": "gate_1",
                "parameters": {
                    "opening": 0.8,
                    "duration": 30.0
                }
            }
        }

# WebSocket状态模型
class WebSocketStatus(BaseModel):
    connected: bool = Field(..., description="连接状态")
    client_id: str = Field(..., description="客户端ID")
    session_id: str = Field(..., description="会话ID")
    connected_at: datetime = Field(..., description="连接时间")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    subscriptions: List[str] = Field(default_factory=list, description="订阅列表")
    message_count: int = Field(default=0, description="消息计数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "connected": True,
                "client_id": "client_123",
                "session_id": "session_456",
                "connected_at": "2024-01-20T10:30:00Z",
                "last_heartbeat": "2024-01-20T10:35:00Z",
                "subscriptions": ["simulation_data", "errors"],
                "message_count": 150
            }
        }

# 批量数据模型
class BatchData(BaseModel):
    batch_id: str = Field(..., description="批次ID")
    timestamp: float = Field(..., description="时间戳")
    data_type: str = Field(..., description="数据类型")
    items: List[Dict[str, Any]] = Field(..., description="数据项列表")
    total_count: int = Field(..., description="总数量")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_001",
                "timestamp": 1234567890.123,
                "data_type": "component_data",
                "items": [
                    {"id": "reservoir_1", "water_level": 15.5},
                    {"id": "gate_1", "opening": 0.75}
                ],
                "total_count": 2
            }
        }