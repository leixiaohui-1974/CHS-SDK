import random
import time
from ..core.interfaces import Agent
from ..central_coordination.collaboration.message_bus import MessageBus
from ..config.parameter_manager import get_parameter_manager
from ..config.constants import PhysicalConstants, HydraulicConstants


class OntologySimulationAgent(Agent):
    """
    1. 本体仿真智能体
    作为高保真的虚拟物理世界，为其他智能体提供“真实”的仿真环境。
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict = None, **kwargs):
        super().__init__(agent_id)
        self.broker = message_bus
        if config is None:
            config = {}
        
        # 获取参数管理器
        self.param_manager = get_parameter_manager()
        
        # 从config中提取initial_state
        initial_state = config.get('initial_state', {})
        
        # 物理常量（从常量类获取）
        self.GRAVITY_ACCELERATION = PhysicalConstants.GRAVITY_ACCELERATION
        self.WEIR_FLOW_EXPONENT = HydraulicConstants.WEIR_FLOW_EXPONENT
        
        # 仿真框架常量（从参数管理器获取）
        self.DEFAULT_TIME_STEP = self.param_manager.get_parameter('simulation', 'time_step', 1.0)
        self.DEFAULT_PRINT_INTERVAL = self.param_manager.get_parameter('simulation', 'print_interval', 10)
        self.MIN_OPENING_LIMIT = HydraulicConstants.MIN_OPENING
        self.MAX_OPENING_LIMIT = HydraulicConstants.MAX_OPENING
        self.DEFAULT_NOISE_LEVEL = self.param_manager.get_parameter('sensor_parameters', 'default_noise_level', 0.01)
        
        # 从配置获取仿真参数
        simulation_config = config.get('simulation', {})
        self.simulation_step = simulation_config.get('step', 60.0)
        self.time_step = simulation_config.get('time_step', self.DEFAULT_TIME_STEP)
        self.print_interval = simulation_config.get('print_interval', self.DEFAULT_PRINT_INTERVAL)
        
        # 从配置获取物理系统参数（必须由用户提供）
        physical_config = config.get('physical_system', {})
        if not physical_config:
            raise ValueError("物理系统配置 'physical_system' 是必需的")
        
        self.channel_surface_area = physical_config['channel_surface_area']  # 必需参数
        
        # 从配置获取闸门参数（必须由用户提供）
        gate_config = config.get('gate_parameters', {})
        if not gate_config:
            raise ValueError("闸门参数配置 'gate_parameters' 是必需的")
        
        self.max_gate_speed = gate_config['max_speed']  # 必需参数
        self.gate_flow_coefficient = gate_config['flow_coefficient']  # 必需参数
        
        # 从配置获取扰动参数（可选）
        disturbance_config = config.get('disturbances', {})
        self.disturbance_enabled = disturbance_config.get('enabled', False)
        if self.disturbance_enabled:
            self.disturbance_start_step = disturbance_config['start_step']
            self.disturbance_end_step = disturbance_config['end_step'] 
            self.disturbance_inflow = disturbance_config['inflow_value']
            self.downstream_outflow = disturbance_config.get('downstream_outflow', 0.0)
        
        # 传感器配置（可选）
        sensor_config = config.get('sensors', {})
        self.noise_level = sensor_config.get('noise_level', self.DEFAULT_NOISE_LEVEL)
        self.inflow_noise_range = sensor_config.get('inflow_noise_range', self.noise_level * 10)
        
        # 其他配置文件
        self.components_file = config.get('components_file', 'components.yml')
        self.topology_file = config.get('topology_file', 'topology.yml')
        self.monitoring_config = config.get('monitoring_config', {})
        
        # 物理状态（从initial_state获取，必须由用户提供）
        if 'upstream_level' not in initial_state:
            raise ValueError("初始上游水位 'upstream_level' 是必需的")
        if 'downstream_level' not in initial_state:
            raise ValueError("初始下游水位 'downstream_level' 是必需的")
        if 'inflow' not in initial_state:
            raise ValueError("初始入流量 'inflow' 是必需的")
            
        self.upstream_level = initial_state['upstream_level']
        self.downstream_level = initial_state['downstream_level']
        self.inflow = initial_state['inflow']

        # 闸门执行器状态（从initial_state获取）
        self.gate_opening = initial_state.get('gate_opening', 0.0)  # 默认关闭
        self.gate_flow = 0.0  # 计算值，总是从0开始
        self.target_gate_opening = self.gate_opening
        self.side_inflow = 0.0  # 扰动值，总是从0开始

        # 订阅控制指令
        control_topic = config.get('control_topic', 'gate_control_command')
        self.broker.subscribe(control_topic, self._handle_gate_command)

    def _handle_gate_command(self, message):
        """处理来自控制智能体的闸门开度指令。"""
        self.target_gate_opening = message.get('target_opening', self.target_gate_opening)
        # print(f"SIMULATOR: Received new target gate opening: {self.target_gate_opening:.2f}")

    def run_step(self, time_step: int):
        # --- 1. 执行器仿真 ---
        # 模拟闸门开度的变化，考虑最大速度限制
        error = self.target_gate_opening - self.gate_opening
        delta = min(abs(error), self.max_gate_speed * self.time_step)
        if error > 0:
            self.gate_opening += delta
        else:
            self.gate_opening -= delta
        self.gate_opening = max(self.MIN_OPENING_LIMIT, min(self.MAX_OPENING_LIMIT, self.gate_opening))

        # --- 2. 水动力学仿真 ---
        # 简化水动力学模型
        # a. 计算过闸流量 (简化的堰流公式)
        head_diff = self.upstream_level - self.downstream_level
        if head_diff > 0 and self.gate_opening > 0:
            self.gate_flow = self.gate_flow_coefficient * self.gate_opening * (head_diff ** self.WEIR_FLOW_EXPONENT)
        else:
            self.gate_flow = 0

        # b. 更新上下游水位 (质量平衡)
        # 假设上游水位受总入流和过闸流量影响，下游水位受过闸流量和某个固定出流影响
        self.upstream_level += (self.inflow - self.gate_flow) * self.time_step / self.channel_surface_area
        
        # 下游水位变化（仅在有扰动配置时考虑固定出流）
        downstream_change = self.gate_flow + self.side_inflow
        if self.disturbance_enabled:
            downstream_change -= self.downstream_outflow
        self.downstream_level += downstream_change * self.time_step / self.channel_surface_area

        # 注入扰动（仅在配置启用时）
        if self.disturbance_enabled:
            if time_step == self.disturbance_start_step:
                print(f"\n!!! SIMULATOR: Disturbance injected: side inflow of {self.disturbance_inflow} m^3/s !!!\n")
                self.side_inflow = self.disturbance_inflow
            elif time_step == self.disturbance_end_step:
                print(f"\n!!! SIMULATOR: Disturbance ended !!!\n")
                self.side_inflow = 0.0

        # --- 3. 传感器仿真 ---
        # 为"真实"数据添加噪声
        simulated_upstream_level = self.upstream_level + random.uniform(-self.noise_level, self.noise_level)
        simulated_downstream_level = self.downstream_level + random.uniform(-self.noise_level, self.noise_level)
        simulated_inflow = self.inflow + random.uniform(-self.inflow_noise_range, self.inflow_noise_range)

        # --- 4. 发布输出 ---
        # 发布原始传感器数据
        sensor_data = {
            'timestamp': time.time(),
            'upstream_level': simulated_upstream_level,
            'downstream_level': simulated_downstream_level,
            'inflow': simulated_inflow
        }
        self.broker.publish("raw_sensor_data", sensor_data)

        # 发布执行器状态
        executor_status = {
            'timestamp': time.time(),
            'actual_opening': self.gate_opening
        }
        self.broker.publish("gate_executor_status", executor_status)

        # 打印真实状态用于验证
        if time_step % self.print_interval == 0:
            print(f"--- Step {time_step}: SIMULATOR STATE ---")
            print(f"  Levels (U/D): {self.upstream_level:.3f}m / {self.downstream_level:.3f}m | Gate Opening: {self.gate_opening:.2%} | Gate Flow: {self.gate_flow:.2f} m^3/s")

    def run(self, current_time: float):
        """
        实现Agent基类要求的run方法
        """
        # 将current_time转换为时间步
        time_step = int(current_time)
        self.run_step(time_step)
