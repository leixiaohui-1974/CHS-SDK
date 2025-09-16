"""
统一配置Schema定义

标准化所有Agent的配置格式，支持验证和类型检查
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from core_lib.core.new_interfaces import DeviceType, ControlStrategy, DataSourceType

# 基础配置模型

class BaseAgentConfig(BaseModel):
    """Agent基础配置"""
    agent_id: str = Field(..., description="Agent唯一标识")
    agent_type: str = Field(..., description="Agent类型")
    enabled: bool = Field(True, description="是否启用")
    debug: bool = Field(False, description="是否开启调试模式")
    log_level: str = Field("INFO", description="日志级别")
    
    # 事件总线配置
    event_bus_config: Optional[Dict[str, Any]] = Field(None, description="事件总线配置")
    
    # 扩展配置
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

class TopicConfig(BaseModel):
    """主题配置"""
    observation_topic: Optional[str] = Field(None, description="观测主题")
    action_topic: Optional[str] = Field(None, description="动作主题")
    command_topic: Optional[str] = Field(None, description="命令主题")
    feedback_topic: Optional[str] = Field(None, description="反馈主题")
    state_topic: Optional[str] = Field(None, description="状态主题")

# 控制器配置

class PIDControllerConfig(BaseModel):
    """PID控制器配置"""
    kp: float = Field(..., description="比例增益")
    ki: float = Field(0.0, description="积分增益")
    kd: float = Field(0.0, description="微分增益")
    setpoint: float = Field(0.0, description="设定值")
    output_limits: Optional[tuple] = Field(None, description="输出限制 (min, max)")
    sample_time: Optional[float] = Field(None, description="采样时间")

class MPCControllerConfig(BaseModel):
    """MPC控制器配置"""
    prediction_horizon: int = Field(10, description="预测时域")
    control_horizon: int = Field(5, description="控制时域")
    weights_output: List[float] = Field([1.0], description="输出权重")
    weights_input: List[float] = Field([0.1], description="输入权重")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")

class RuleBasedControllerConfig(BaseModel):
    """基于规则的控制器配置"""
    rules: List[Dict[str, Any]] = Field(..., description="控制规则列表")
    default_action: Any = Field(0.0, description="默认动作")

ControllerConfigUnion = Union[PIDControllerConfig, MPCControllerConfig, RuleBasedControllerConfig]

# 本地Agent配置

class LocalAgentConfig(BaseAgentConfig):
    """本地Agent配置"""
    device_type: DeviceType = Field(..., description="设备类型")
    target_component: Optional[str] = Field(None, description="目标组件名称")
    topics: Optional[TopicConfig] = Field(None, description="主题配置")

class PerceptionAgentConfig(LocalAgentConfig):
    """感知Agent配置"""
    perception_interval: float = Field(1.0, description="感知间隔(秒)")
    state_keys: List[str] = Field(..., description="要感知的状态键")
    filters: Optional[Dict[str, Any]] = Field(None, description="数据过滤器配置")

class LocalControlAgentConfig(LocalAgentConfig):
    """本地控制Agent配置"""
    control_strategy: ControlStrategy = Field(..., description="控制策略")
    controller_config: ControllerConfigUnion = Field(..., description="控制器配置")
    observation_key: str = Field("value", description="观测数据键")
    control_limits: Optional[Dict[str, float]] = Field(None, description="控制限制")

# 中央Agent配置

class CentralAgentConfig(BaseAgentConfig):
    """中央Agent配置"""
    managed_agents: List[str] = Field([], description="管理的Agent列表")
    coordination_interval: float = Field(5.0, description="协调间隔(秒)")

class CentralCoordinatorConfig(CentralAgentConfig):
    """中央协调Agent配置"""
    task_queue_size: int = Field(100, description="任务队列大小")
    load_balancing: bool = Field(True, description="是否启用负载均衡")
    health_check_interval: float = Field(10.0, description="健康检查间隔")

class CentralControlConfig(CentralAgentConfig):
    """中央控制Agent配置"""
    optimization_method: str = Field("mpc", description="优化方法")
    objectives: Dict[str, float] = Field(..., description="优化目标和权重")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")

class MonitoringAgentConfig(CentralAgentConfig):
    """监控Agent配置"""
    metrics_collection_interval: float = Field(1.0, description="指标收集间隔")
    anomaly_detection_enabled: bool = Field(True, description="是否启用异常检测")
    alert_thresholds: Dict[str, float] = Field({}, description="告警阈值")

# 服务Agent配置

class ServiceAgentConfig(BaseAgentConfig):
    """服务Agent配置"""
    service_type: str = Field(..., description="服务类型")
    service_port: Optional[int] = Field(None, description="服务端口")

class DataSourceConfig(ServiceAgentConfig):
    """数据源配置"""
    source_type: DataSourceType = Field(..., description="数据源类型")
    connection_config: Dict[str, Any] = Field(..., description="连接配置")
    
    # CSV特定配置
    csv_file_path: Optional[str] = Field(None, description="CSV文件路径")
    time_column: Optional[str] = Field(None, description="时间列名")
    data_columns: Optional[List[str]] = Field(None, description="数据列名")
    
    # 数据库特定配置
    database_url: Optional[str] = Field(None, description="数据库URL")
    table_name: Optional[str] = Field(None, description="表名")
    query: Optional[str] = Field(None, description="查询语句")
    
    # API特定配置
    api_url: Optional[str] = Field(None, description="API URL")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置")
    
    # 实时数据配置
    stream_config: Optional[Dict[str, Any]] = Field(None, description="流配置")

class DisturbanceConfig(ServiceAgentConfig):
    """扰动配置"""
    disturbance_type: str = Field(..., description="扰动类型")
    parameters: Dict[str, Any] = Field(..., description="扰动参数")
    start_time: float = Field(0.0, description="开始时间")
    end_time: Optional[float] = Field(None, description="结束时间")
    target_components: List[str] = Field([], description="目标组件")

class IdentificationConfig(ServiceAgentConfig):
    """参数识别配置"""
    identification_method: str = Field("offline", description="识别方法")
    target_parameters: List[str] = Field(..., description="目标参数")
    data_source: str = Field(..., description="数据源")
    validation_split: float = Field(0.2, description="验证集比例")
    optimization_config: Optional[Dict[str, Any]] = Field(None, description="优化配置")

# 系统级配置

class SystemConfig(BaseModel):
    """系统配置"""
    simulation_config: Dict[str, Any] = Field(..., description="仿真配置")
    agents: List[Union[
        LocalControlAgentConfig, 
        PerceptionAgentConfig,
        CentralCoordinatorConfig,
        CentralControlConfig,
        MonitoringAgentConfig,
        DataSourceConfig,
        DisturbanceConfig,
        IdentificationConfig
    ]] = Field(..., description="Agent配置列表")
    
    # 全局配置
    global_event_bus: Optional[Dict[str, Any]] = Field(None, description="全局事件总线配置")
    global_logger: Optional[Dict[str, Any]] = Field(None, description="全局日志配置")
    
    @validator('agents')
    def validate_unique_agent_ids(cls, v):
        """验证Agent ID唯一性"""
        agent_ids = [agent.agent_id for agent in v]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("Agent IDs must be unique")
        return v

# 配置验证工具

def validate_config(config_dict: Dict[str, Any]) -> SystemConfig:
    """验证配置字典"""
    try:
        return SystemConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

def load_config_from_file(file_path: str) -> SystemConfig:
    """从文件加载配置"""
    import yaml
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                config_dict = yaml.safe_load(f)
            elif file_path.endswith('.json'):
                config_dict = json.load(f)
            else:
                raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")
        
        return validate_config(config_dict)
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {file_path}: {e}")

def save_config_to_file(config: SystemConfig, file_path: str):
    """保存配置到文件"""
    import yaml
    import json
    
    config_dict = config.dict()
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif file_path.endswith('.json'):
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")
        
        print(f"Configuration saved to {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save config to {file_path}: {e}")
