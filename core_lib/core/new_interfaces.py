"""
新版核心接口 - 重构后的统一Agent架构

设计原则：
1. 清晰的三层架构（Local/Central/Service）
2. 统一的生命周期管理
3. 标准化的配置和消息接口
4. 插件化的策略和数据源
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
import asyncio
from dataclasses import dataclass
from datetime import datetime

# 类型别名
State = Dict[str, Any]
Parameters = Dict[str, Any]
Config = Dict[str, Any]
Message = Dict[str, Any]

class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class DeviceType(Enum):
    """设备类型枚举"""
    GATE = "gate"
    PUMP = "pump"
    VALVE = "valve"
    TURBINE = "turbine"
    RESERVOIR = "reservoir"
    CHANNEL = "channel"
    PIPELINE = "pipeline"

class ControlStrategy(Enum):
    """控制策略枚举"""
    PID = "pid"
    MPC = "mpc"
    RULE_BASED = "rule_based"
    DISCRETE = "discrete"
    NEURAL_NETWORK = "neural_network"
    FUZZY = "fuzzy"

class DataSourceType(Enum):
    """数据源类型枚举"""
    CSV = "csv"
    DATABASE = "database"
    API = "api"
    REALTIME = "realtime"
    MOCK = "mock"

@dataclass
class AgentMetrics:
    """Agent性能指标"""
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    error_count: int = 0
    last_execution_time: Optional[float] = None  # 使用float时间戳而不是datetime

class EventBus(ABC):
    """轻量级事件总线接口"""
    
    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[Message], None]):
        """订阅主题"""
        pass
    
    @abstractmethod
    def unsubscribe(self, topic: str, handler: Callable[[Message], None]):
        """取消订阅"""
        pass
    
    @abstractmethod
    def publish(self, topic: str, message: Message):
        """发布消息"""
        pass
    
    @abstractmethod
    def get_topics(self) -> List[str]:
        """获取所有主题"""
        pass

class BaseAgent(ABC):
    """
    新版Agent基类 - 统一生命周期和接口
    
    设计特点：
    1. 标准化生命周期：init -> configure -> start -> run/step -> stop
    2. 统一事件/消息接口
    3. 内置指标收集
    4. 配置驱动
    """
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.event_bus: Optional[EventBus] = None
        self.logger = None  # 将由依赖注入提供
        self.subscriptions: List[str] = []
        
    def set_event_bus(self, event_bus: EventBus):
        """设置事件总线"""
        self.event_bus = event_bus
    
    def set_logger(self, logger):
        """设置日志器"""
        self.logger = logger
    
    @abstractmethod
    def configure(self, config: Config) -> bool:
        """
        配置Agent
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否成功
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        启动Agent
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        停止Agent
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def step(self, current_time: float) -> bool:
        """
        执行一个时间步
        
        Args:
            current_time: 当前仿真时间
            
        Returns:
            bool: 执行是否成功
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """获取Agent状态"""
        return self.status
    
    def get_metrics(self) -> AgentMetrics:
        """获取性能指标"""
        return self.metrics
    
    def subscribe_topic(self, topic: str, handler: Optional[Callable[[Message], None]] = None):
        """订阅主题"""
        if self.event_bus:
            actual_handler = handler or self._default_message_handler
            self.event_bus.subscribe(topic, actual_handler)
            self.subscriptions.append(topic)
    
    def publish_message(self, topic: str, message: Message):
        """发布消息"""
        if self.event_bus:
            self.event_bus.publish(topic, message)
    
    def _default_message_handler(self, message: Message):
        """默认消息处理器 - 子类可重写"""
        if self.logger:
            self.logger.debug(f"[{self.agent_id}] Received message: {message}")
    
    def _log(self, level: str, message: str):
        """内部日志方法"""
        if self.logger:
            getattr(self.logger, level)(f"[{self.agent_id}] {message}")
        else:
            print(f"[{level.upper()}] [{self.agent_id}] {message}")

class LocalAgent(BaseAgent):
    """
    本地Agent基类
    
    职责：本地设备控制、感知等
    """
    
    def __init__(self, agent_id: str, device_type: DeviceType, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        self.device_type = device_type
        self.target_component: Optional[str] = None
        
    @abstractmethod
    def get_device_state(self) -> State:
        """获取设备状态"""
        pass

class CentralAgent(BaseAgent):
    """
    中央Agent基类
    
    职责：全局优化、协调决策等
    """
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        self.managed_agents: List[str] = []
        
    @abstractmethod
    def coordinate_agents(self, agent_states: Dict[str, State]) -> Dict[str, Message]:
        """协调管理的Agent"""
        pass

class ServiceAgent(BaseAgent):
    """
    服务Agent基类
    
    职责：支撑服务、数据处理等
    """
    
    def __init__(self, agent_id: str, service_type: str, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        self.service_type = service_type
        
    @abstractmethod
    def provide_service(self, request: Message) -> Message:
        """提供服务"""
        pass

# 具体Agent接口

class PerceptionAgent(LocalAgent):
    """感知Agent接口"""
    
    def __init__(self, agent_id: str, device_type: DeviceType, config: Optional[Config] = None):
        super().__init__(agent_id, device_type, config)
        
    @abstractmethod
    def perceive(self, current_time: float) -> State:
        """执行感知任务"""
        pass

class LocalControlAgent(LocalAgent):
    """本地控制Agent接口"""
    
    def __init__(self, agent_id: str, device_type: DeviceType, 
                 control_strategy: ControlStrategy, config: Optional[Config] = None):
        super().__init__(agent_id, device_type, config)
        self.control_strategy = control_strategy
        self.controller = None  # 将通过工厂创建
        
    @abstractmethod
    def compute_control_action(self, observation: State, current_time: float) -> Any:
        """计算控制动作"""
        pass
    
    @abstractmethod
    def apply_control_action(self, action: Any) -> bool:
        """应用控制动作"""
        pass

class CentralCoordinatorAgent(CentralAgent):
    """中央协调Agent"""
    
    @abstractmethod
    def dispatch_tasks(self, tasks: List[Message]) -> Dict[str, Message]:
        """任务调度"""
        pass
    
    @abstractmethod
    def monitor_system_health(self) -> State:
        """系统健康监控"""
        pass

class CentralControlAgent(CentralAgent):
    """中央控制Agent"""
    
    @abstractmethod
    def optimize_system(self, system_state: State, objectives: Dict[str, float]) -> Dict[str, Any]:
        """系统优化"""
        pass
    
    @abstractmethod
    def generate_control_commands(self, optimization_result: Dict[str, Any]) -> Dict[str, Message]:
        """生成控制命令"""
        pass

class MonitoringAgent(CentralAgent):
    """监控Agent"""
    
    @abstractmethod
    def collect_metrics(self, agents: List[BaseAgent]) -> Dict[str, Any]:
        """收集指标"""
        pass
    
    @abstractmethod
    def detect_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """异常检测"""
        pass

class DataSourceAgent(ServiceAgent):
    """数据源Agent"""
    
    def __init__(self, agent_id: str, source_type: DataSourceType, config: Optional[Config] = None):
        super().__init__(agent_id, "data_source", config)
        self.source_type = source_type
        
    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass
    
    @abstractmethod
    def read_data(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """读取数据"""
        pass
    
    @abstractmethod
    def subscribe_stream(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """订阅数据流"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass

class DisturbanceAgent(ServiceAgent):
    """扰动Agent"""
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, "disturbance", config)
        
    @abstractmethod
    def generate_disturbance(self, current_time: float) -> Dict[str, Any]:
        """生成扰动"""
        pass
    
    @abstractmethod
    def is_active(self, current_time: float) -> bool:
        """检查扰动是否激活"""
        pass

class IdentificationAgent(ServiceAgent):
    """参数识别Agent"""
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, "identification", config)
        
    @abstractmethod
    def fit_parameters(self, data: List[Dict[str, Any]], method: str = 'offline') -> Parameters:
        """拟合参数"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Parameters, validation_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """验证参数"""
        pass
    
    @abstractmethod
    def update_online(self, new_data: Dict[str, Any]) -> Parameters:
        """在线更新参数"""
        pass

# 工厂接口

class AgentFactory(ABC):
    """Agent工厂接口"""
    
    @abstractmethod
    def create_agent(self, agent_type: str, agent_id: str, config: Config) -> BaseAgent:
        """创建Agent"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的Agent类型"""
        pass

class ControllerFactory(ABC):
    """控制器工厂接口"""
    
    @abstractmethod
    def create_controller(self, strategy: ControlStrategy, config: Config) -> Any:
        """创建控制器"""
        pass
    
    @abstractmethod
    def get_supported_strategies(self) -> List[ControlStrategy]:
        """获取支持的控制策略"""
        pass

class DataSourceFactory(ABC):
    """数据源工厂接口"""
    
    @abstractmethod
    def create_data_source(self, source_type: DataSourceType, config: Config) -> DataSourceAgent:
        """创建数据源"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[DataSourceType]:
        """获取支持的数据源类型"""
        pass
