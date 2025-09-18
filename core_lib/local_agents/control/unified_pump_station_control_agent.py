"""
统一泵站控制代理 - 基于统一架构的高级泵站控制

遵循单一职责原则，只负责泵站控制逻辑
"""

from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy as ControlStrategyEnum
from core_lib.local_agents.control.pump_control_strategies import (
    PumpControlStrategy, OptimalControlStrategy, SequentialControlStrategy, 
    ParallelControlStrategy, ControlStrategyType
)
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.pump import PumpStation
from typing import Optional, Dict, Any, List
import math

class UnifiedPumpStationControlAgent(UnifiedLocalControlAgent):
    """
    统一泵站控制代理
    
    单一职责：管理泵站控制逻辑
    - 接收需求信号
    - 选择控制策略
    - 计算控制动作
    - 发布控制命令
    """
    
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 pump_station: PumpStation,
                 demand_topic: str,
                 control_topic_prefix: str,
                 control_strategy_type: ControlStrategyType = ControlStrategyType.OPTIMAL,
                 time_step: float = 1.0,
                 **kwargs):
        """
        初始化统一泵站控制代理
        
        Args:
            agent_id: 代理标识
            message_bus: 消息总线
            pump_station: 泵站对象
            demand_topic: 需求主题
            control_topic_prefix: 控制主题前缀
            control_strategy_type: 控制策略类型
            time_step: 时间步长
            **kwargs: 其他配置参数
        """
        # 泵站特定属性（在父类初始化前设置）
        self.pump_station = pump_station
        self.control_topic_prefix = control_topic_prefix
        self.current_demand = 0.0
        self.control_strategy_type = control_strategy_type
        
        # 调用父类构造函数，使用多执行器控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
            control_strategy=ControlStrategyEnum.MULTI_ACTUATOR,
            observation_topic=demand_topic,
            observation_key='value',
            action_topic=None,  # 多执行器模式
            controller=None,  # 多执行器模式不需要单一控制器
            controller_config={},
            device_config={},
            **kwargs
        )
        
        # 初始化控制策略和泵信息（在父类初始化后，避免被覆盖）
        self.pump_control_strategy = self._create_control_strategy(control_strategy_type)
        self.pumps_info = self._initialize_pumps_info()
        
        print(f"[{self.agent_id}] Initialized with {len(self.pumps_info)} pumps")
        print(f"[{self.agent_id}] Control strategy: {control_strategy_type.value}")
    
    def _initialize_device_specific(self, **kwargs):
        """泵站特定初始化"""
        # 泵站配置
        self.max_pumps = kwargs.get('max_pumps', len(self.pumps_info) if hasattr(self, 'pumps_info') else 0)
        self.min_pumps = kwargs.get('min_pumps', 0)
        self.pump_startup_delay = kwargs.get('pump_startup_delay', 0)
        self.pump_shutdown_delay = kwargs.get('pump_shutdown_delay', 0)
        
        # 控制参数
        self.control_deadband = kwargs.get('control_deadband', 0.1)  # 10%死区
        self.max_flow_rate = kwargs.get('max_flow_rate', 
                                      sum(p['max_flow'] for p in self.pumps_info) if hasattr(self, 'pumps_info') else 0)
        
        print(f"[{self.agent_id}] Device-specific initialization completed")
        print(f"[{self.agent_id}] Max pumps: {self.max_pumps}, Min pumps: {self.min_pumps}")
        print(f"[{self.agent_id}] Control deadband: {self.control_deadband:.1%}")
    
    def _create_control_strategy(self, strategy_type: ControlStrategyType) -> PumpControlStrategy:
        """创建控制策略"""
        if strategy_type == ControlStrategyType.OPTIMAL:
            return OptimalControlStrategy()
        elif strategy_type == ControlStrategyType.SEQUENTIAL:
            return SequentialControlStrategy()
        elif strategy_type == ControlStrategyType.PARALLEL:
            return ParallelControlStrategy()
        else:
            return OptimalControlStrategy()  # 默认策略
    
    def _initialize_pumps_info(self) -> List[Dict[str, Any]]:
        """初始化泵信息"""
        pumps_info = []
        for i, pump in enumerate(self.pump_station.pumps):
            pump_info = {
                'pump_id': f"pump_{i+1}",
                'max_flow': pump.get_parameters().get('max_flow_rate', 10.0),
                'max_head': pump.get_parameters().get('max_head', 20.0),
                'rated_power': pump.get_parameters().get('power_consumption_kw', 50.0),
                'efficiency': pump.get_parameters().get('efficiency', 0.8)
            }
            pumps_info.append(pump_info)
        return pumps_info
    
    def preprocess_observation(self, message: Message) -> Message:
        """预处理观测数据"""
        self.current_demand = message.get('value', 0.0)
        print(f"[{self.agent_id}] Current demand: {self.current_demand:.2f} m³/s")
        return message
    
    def compute_multi_actuator_control_action(self, message: Message) -> Optional[Dict[str, Any]]:
        """计算多执行器控制动作"""
        if not self.pumps_info or self.current_demand <= 0:
            return None
        
        # 获取当前状态
        current_status = self._get_current_status()
        
        # 使用控制策略计算控制动作
        control_result = self.pump_control_strategy.compute_control_action(
            self.current_demand, self.pumps_info, current_status
        )
        
        # 转换为消息总线格式
        control_signals = {}
        pump_commands = control_result.get('pump_commands', {})
        
        # 为所有泵发送控制信号（包括停止信号）
        for pump_idx in range(len(self.pump_station.pumps)):
            pump = self.pump_station.pumps[pump_idx]
            topic = f"{self.control_topic_prefix}.{pump.name}"
            
            # 如果泵在命令中，发送启动信号；否则发送停止信号
            command = pump_commands.get(pump_idx, 0)
            control_signals[topic] = int(command)
        
        print(f"[{self.agent_id}] Generated {len(control_signals)} control signals for demand {self.current_demand} m³/s")
        return control_signals
    
    def _get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        total_flow = 0
        running_pumps = []
        
        for i, pump in enumerate(self.pump_station.pumps):
            pump_state = pump.get_state()
            if pump_state.get('status', 0) == 1:  # 运行中
                running_pumps.append(i)
                total_flow += pump_state.get('outflow', 0)
        
        return {
            'total_flow': total_flow,
            'running_pumps': running_pumps,
            'total_pumps': len(self.pump_station.pumps)
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        current_status = self._get_current_status()
        total_power = 0
        
        for i, pump in enumerate(self.pump_station.pumps):
            pump_state = pump.get_state()
            if pump_state.get('status', 0) == 1:
                power = pump_state.get('power_draw_kw', 0)
                total_power += power
        
        return {
            'demand': self.current_demand,
            'total_flow': current_status['total_flow'],
            'running_pumps': len(current_status['running_pumps']),
            'total_pumps': current_status['total_pumps'],
            'total_power': total_power,
            'efficiency': (current_status['total_flow'] * 9.81 * 20) / (total_power * 1000) if total_power > 0 else 0
        }
    
    def validate_control_effectiveness(self) -> bool:
        """验证控制效果"""
        status = self.get_system_status()
        
        # 检查控制效果
        if self.current_demand > 0:
            flow_error = abs(status['total_flow'] - self.current_demand)
            flow_error_percentage = flow_error / self.current_demand if self.current_demand > 0 else 0
            
            if flow_error_percentage > 0.5:  # 50%误差阈值
                print(f"[{self.agent_id}] WARNING: Large flow error - Demand: {self.current_demand:.1f} m³/s, "
                      f"Actual: {status['total_flow']:.1f} m³/s, Error: {flow_error_percentage:.1%}")
                return False
            
            if status['total_power'] == 0 and self.current_demand > 0:
                print(f"[{self.agent_id}] ERROR: No power consumption despite demand {self.current_demand:.1f} m³/s")
                return False
        
        return True
