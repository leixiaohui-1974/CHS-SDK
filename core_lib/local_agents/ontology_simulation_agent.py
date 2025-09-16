import random
import time
from ..core.interfaces import Agent
from ..central_coordination.collaboration.message_bus import MessageBus


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
        
        # 从config中提取initial_state
        initial_state = config.get('initial_state', {})
        
        # 仿真配置常量
        self.DEFAULT_SIMULATION_STEP = 60.0   # 默认仿真步长 (秒)
        
        # 存储其他配置
        self.simulation_step = config.get('simulation_step', self.DEFAULT_SIMULATION_STEP)
        self.components_file = config.get('components_file', 'components.yml')
        self.topology_file = config.get('topology_file', 'topology.yml')
        self.monitoring_config = config.get('monitoring_config', {})
        # 物理状态常量定义
        self.DEFAULT_UPSTREAM_LEVEL = 5.0     # 默认上游水位 (m)
        self.DEFAULT_DOWNSTREAM_LEVEL = 4.5   # 默认下游水位 (m)
        self.DEFAULT_CHANNEL_SURFACE_AREA = 10000  # 默认渠道表面积 (m²)
        self.DEFAULT_INFLOW = 10              # 默认入流量 (m³/s)
        
        # 闸门执行器常量定义
        self.DEFAULT_GATE_OPENING = 0.5       # 默认闸门开度 (0-1)
        self.DEFAULT_GATE_FLOW = 0            # 默认闸门流量
        self.DEFAULT_MAX_GATE_SPEED = 0.05    # 默认最大闸门速度 (5%/秒)
        self.DEFAULT_GATE_FLOW_COEFFICIENT = 20  # 默认流量系数
        self.DEFAULT_SIDE_INFLOW = 0          # 默认侧向入流
        
        # 仿真运行时常量
        self.TIME_STEP_SECONDS = 1            # 时间步长 (秒)
        self.MIN_GATE_OPENING = 0             # 最小闸门开度
        self.MAX_GATE_OPENING = 1             # 最大闸门开度
        self.POWER_EXPONENT = 0.5             # 堰流公式指数
        self.DOWNSTREAM_OUTFLOW = 8           # 下游固定出流量 (m³/s)
        self.DISTURBANCE_START_STEP = 50      # 扰动开始步数
        self.DISTURBANCE_END_STEP = 100       # 扰动结束步数
        self.DISTURBANCE_INFLOW = 5           # 扰动入流量 (m³/s)
        self.NOISE_LEVEL = 0.01               # 传感器噪声水平
        self.INFLOW_NOISE_RANGE = 0.1         # 入流噪声范围
        self.PRINT_INTERVAL = 10              # 打印间隔步数
        
        # 物理状态
        self.upstream_level = initial_state.get('upstream_level', self.DEFAULT_UPSTREAM_LEVEL)
        self.downstream_level = initial_state.get('downstream_level', self.DEFAULT_DOWNSTREAM_LEVEL)
        self.channel_surface_area = self.DEFAULT_CHANNEL_SURFACE_AREA
        self.inflow = initial_state.get('inflow', self.DEFAULT_INFLOW)

        # 闸门执行器状态
        self.gate_opening = self.DEFAULT_GATE_OPENING
        self.gate_flow = self.DEFAULT_GATE_FLOW
        self.target_gate_opening = self.gate_opening
        self.max_gate_speed = self.DEFAULT_MAX_GATE_SPEED
        self.gate_flow_coefficient = self.DEFAULT_GATE_FLOW_COEFFICIENT

        # 订阅控制指令
        self.broker.subscribe("gate_control_command", self._handle_gate_command)

        # 扰动注入
        self.side_inflow = self.DEFAULT_SIDE_INFLOW

    def _handle_gate_command(self, message):
        """处理来自控制智能体的闸门开度指令。"""
        self.target_gate_opening = message.get('target_opening', self.target_gate_opening)
        # print(f"SIMULATOR: Received new target gate opening: {self.target_gate_opening:.2f}")

    def run_step(self, time_step: int):
        # --- 1. 执行器仿真 ---
        # 模拟闸门开度的变化，考虑最大速度限制
        error = self.target_gate_opening - self.gate_opening
        delta = min(abs(error), self.max_gate_speed * self.TIME_STEP_SECONDS)
        if error > 0:
            self.gate_opening += delta
        else:
            self.gate_opening -= delta
        self.gate_opening = max(self.MIN_GATE_OPENING, min(self.MAX_GATE_OPENING, self.gate_opening))

        # --- 2. 水动力学仿真 ---
        # 简化水动力学模型
        # a. 计算过闸流量 (简化的堰流公式)
        head_diff = self.upstream_level - self.downstream_level
        if head_diff > 0 and self.gate_opening > 0:
            self.gate_flow = self.gate_flow_coefficient * self.gate_opening * (head_diff ** self.POWER_EXPONENT)
        else:
            self.gate_flow = 0

        # b. 更新上下游水位 (质量平衡)
        # 假设上游水位受总入流和过闸流量影响，下游水位受过闸流量和某个固定出流影响
        self.upstream_level += (self.inflow - self.gate_flow) * self.TIME_STEP_SECONDS / self.channel_surface_area
        # 为了简化，我们让下游渠道也有一个恒定的出流，使其水位也能动态变化
        self.downstream_level += (self.gate_flow + self.side_inflow - self.DOWNSTREAM_OUTFLOW) * self.TIME_STEP_SECONDS / self.channel_surface_area

        # 注入扰动 (例如，在第50步时发生侧向入流)
        if time_step == self.DISTURBANCE_START_STEP:
            print(f"\n!!! SIMULATOR: Disturbance injected: side inflow of {self.DISTURBANCE_INFLOW} m^3/s !!!\n")
            self.side_inflow = self.DISTURBANCE_INFLOW
        if time_step == self.DISTURBANCE_END_STEP:
            self.side_inflow = self.DEFAULT_SIDE_INFLOW

        # --- 3. 传感器仿真 ---
        # 为"真实"数据添加噪声
        simulated_upstream_level = self.upstream_level + random.uniform(-self.NOISE_LEVEL, self.NOISE_LEVEL)
        simulated_downstream_level = self.downstream_level + random.uniform(-self.NOISE_LEVEL, self.NOISE_LEVEL)
        simulated_inflow = self.inflow + random.uniform(-self.INFLOW_NOISE_RANGE, self.INFLOW_NOISE_RANGE)

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
        if time_step % self.PRINT_INTERVAL == 0:
            print(f"--- Step {time_step}: SIMULATOR STATE ---")
            print(f"  Levels (U/D): {self.upstream_level:.3f}m / {self.downstream_level:.3f}m | Gate Opening: {self.gate_opening:.2%} | Gate Flow: {self.gate_flow:.2f} m^3/s")

    def run(self, current_time: float):
        """
        实现Agent基类要求的run方法
        """
        # 将current_time转换为时间步
        time_step = int(current_time)
        self.run_step(time_step)
