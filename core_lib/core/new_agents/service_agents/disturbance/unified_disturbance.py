"""
统一扰动Agent实现

收敛所有扰动类型：降雨、用水、CSV扰动等
替代：RainfallAgent、WaterUseAgent、CsvReaderAgent等扰动相关类
"""
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
import threading
import math

from core_lib.core.new_interfaces import DisturbanceAgent, Config, Message
from core_lib.core.event_bus import get_global_event_bus

class UnifiedDisturbanceAgent(DisturbanceAgent):
    """
    统一扰动Agent
    
    支持的扰动类型：
    - rainfall: 降雨扰动 (替代 RainfallAgent, DynamicRainfallAgent)
    - water_use: 用水扰动 (替代 WaterUseAgent)  
    - csv: CSV文件扰动 (替代 CsvReaderAgent用于扰动)
    - sinusoidal: 正弦波扰动
    - random: 随机扰动
    - step: 阶跃扰动
    - pulse: 脉冲扰动
    - ramp: 斜坡扰动
    - composite: 复合扰动（多个扰动的组合）
    """
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        
        # 扰动配置
        self.disturbance_type = config.get('disturbance_type', 'sinusoidal') if config else 'sinusoidal'
        self.parameters = config.get('parameters', {}) if config else {}
        self.start_time = config.get('start_time', 0.0) if config else 0.0
        self.end_time = config.get('end_time') if config else None
        self.target_components = config.get('target_components', []) if config else []
        
        # 发布配置
        self.publish_topic = config.get('publish_topic', f'disturbance.{agent_id}') if config else f'disturbance.{agent_id}'
        self.publish_interval = config.get('publish_interval', 1.0) if config else 1.0
        
        # 状态管理
        self.current_value = 0.0
        self.last_publish_time = 0.0
        self.disturbance_history: List[Dict[str, Any]] = []
        
        # 类型特定数据
        self._csv_data: Optional[pd.DataFrame] = None
        self._csv_index = 0
        self._composite_disturbances: List['UnifiedDisturbanceAgent'] = []
        
        # 工作线程
        self._disturbance_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 初始化类型特定配置
        self._initialize_disturbance_type()
        
        print(f"[UnifiedDisturbance] Initialized {self.disturbance_type} disturbance: {agent_id}")
    
    def configure(self, config: Config) -> bool:
        """配置扰动Agent"""
        try:
            self.config.update(config)
            
            # 更新基础配置
            if 'parameters' in config:
                self.parameters.update(config['parameters'])
            
            if 'disturbance_type' in config:
                self.disturbance_type = config['disturbance_type']
                self._initialize_disturbance_type()
            
            self._log("info", f"Disturbance configuration updated")
            return True
        except Exception as e:
            self._log("error", f"Configuration failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动扰动Agent"""
        try:
            # 设置事件总线
            if not self.event_bus:
                self.event_bus = get_global_event_bus()
            
            # 启动扰动生成线程
            self._start_disturbance_thread()
            
            self.status = self.status.__class__.RUNNING
            self._log("info", f"Disturbance agent started")
            return True
        except Exception as e:
            self._log("error", f"Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止扰动Agent"""
        try:
            self._stop_event.set()
            
            if self._disturbance_thread and self._disturbance_thread.is_alive():
                self._disturbance_thread.join(timeout=5.0)
            
            self.status = self.status.__class__.STOPPED
            self._log("info", "Disturbance agent stopped")
            return True
        except Exception as e:
            self._log("error", f"Stop failed: {e}")
            return False
    
    def step(self, current_time: float) -> bool:
        """执行一个时间步"""
        try:
            # 检查扰动是否应该激活
            if not self.is_active(current_time):
                return True
            
            # 生成扰动值
            disturbance_value = self.generate_disturbance(current_time)
            
            # 检查是否需要发布
            if current_time - self.last_publish_time >= self.publish_interval:
                self._publish_disturbance(current_time, disturbance_value)
                self.last_publish_time = current_time
            
            return True
        except Exception as e:
            self._log("error", f"Step execution failed: {e}")
            return False
    
    def generate_disturbance(self, current_time: float) -> Dict[str, Any]:
        """生成扰动"""
        try:
            if self.disturbance_type == 'sinusoidal':
                value = self._generate_sinusoidal_disturbance(current_time)
            elif self.disturbance_type == 'random':
                value = self._generate_random_disturbance(current_time)
            elif self.disturbance_type == 'step':
                value = self._generate_step_disturbance(current_time)
            elif self.disturbance_type == 'pulse':
                value = self._generate_pulse_disturbance(current_time)
            elif self.disturbance_type == 'ramp':
                value = self._generate_ramp_disturbance(current_time)
            elif self.disturbance_type == 'csv':
                value = self._generate_csv_disturbance(current_time)
            elif self.disturbance_type == 'rainfall':
                value = self._generate_rainfall_disturbance(current_time)
            elif self.disturbance_type == 'water_use':
                value = self._generate_water_use_disturbance(current_time)
            elif self.disturbance_type == 'composite':
                value = self._generate_composite_disturbance(current_time)
            else:
                value = 0.0
            
            self.current_value = value
            
            # 记录历史
            self._record_disturbance(current_time, value)
            
            return {
                'value': value,
                'timestamp': current_time,
                'disturbance_type': self.disturbance_type,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self._log("error", f"Disturbance generation failed: {e}")
            return {'value': 0.0, 'timestamp': current_time, 'error': str(e)}
    
    def is_active(self, current_time: float) -> bool:
        """检查扰动是否激活"""
        try:
            # 检查开始时间
            if current_time < self.start_time:
                return False
            
            # 检查结束时间
            if self.end_time is not None and current_time > self.end_time:
                return False
            
            return True
            
        except Exception as e:
            self._log("error", f"Activity check failed: {e}")
            return False
    
    def provide_service(self, request: Message) -> Message:
        """提供扰动服务"""
        try:
            service_type = request.get('service_type')
            
            if service_type == 'get_current_value':
                return {
                    'status': 'success',
                    'value': self.current_value,
                    'timestamp': time.time()
                }
            
            elif service_type == 'get_history':
                count = request.get('count', 100)
                history = self.disturbance_history[-count:] if self.disturbance_history else []
                return {
                    'status': 'success',
                    'history': history
                }
            
            elif service_type == 'set_parameters':
                new_params = request.get('parameters', {})
                self.parameters.update(new_params)
                return {'status': 'success', 'message': 'Parameters updated'}
            
            else:
                return {'status': 'error', 'message': f'Unknown service type: {service_type}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _initialize_disturbance_type(self):
        """初始化扰动类型特定配置"""
        try:
            if self.disturbance_type == 'csv':
                self._initialize_csv_disturbance()
            elif self.disturbance_type == 'composite':
                self._initialize_composite_disturbance()
            elif self.disturbance_type == 'rainfall':
                self._initialize_rainfall_disturbance()
            elif self.disturbance_type == 'water_use':
                self._initialize_water_use_disturbance()
            
        except Exception as e:
            self._log("error", f"Disturbance type initialization failed: {e}")
    
    def _initialize_csv_disturbance(self):
        """初始化CSV扰动"""
        csv_file_path = self.parameters.get('csv_file_path')
        if not csv_file_path:
            raise ValueError("csv_file_path is required for CSV disturbance")
        
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        self._csv_data = pd.read_csv(csv_path)
        self._csv_index = 0
        
        self._log("info", f"CSV disturbance loaded: {len(self._csv_data)} records")
    
    def _initialize_composite_disturbance(self):
        """初始化复合扰动"""
        sub_disturbances = self.parameters.get('sub_disturbances', [])
        
        for sub_config in sub_disturbances:
            sub_agent = UnifiedDisturbanceAgent(
                agent_id=f"{self.agent_id}_{sub_config['type']}",
                config=sub_config
            )
            self._composite_disturbances.append(sub_agent)
        
        self._log("info", f"Composite disturbance initialized with {len(self._composite_disturbances)} sub-disturbances")
    
    def _initialize_rainfall_disturbance(self):
        """初始化降雨扰动"""
        # 设置默认降雨参数
        default_params = {
            'base_intensity': 0.0,      # 基础降雨强度
            'peak_intensity': 10.0,     # 峰值降雨强度
            'storm_duration': 3600.0,   # 暴雨持续时间(秒)
            'storm_frequency': 0.1,     # 暴雨频率
            'seasonal_factor': 1.0      # 季节因子
        }
        
        for key, default_value in default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        self._log("info", "Rainfall disturbance initialized")
    
    def _initialize_water_use_disturbance(self):
        """初始化用水扰动"""
        # 设置默认用水参数
        default_params = {
            'base_demand': 1.0,         # 基础需求
            'peak_factor': 2.0,         # 峰值因子
            'daily_pattern': True,      # 日周期模式
            'weekly_pattern': False,    # 周周期模式
            'seasonal_variation': 0.2   # 季节变化
        }
        
        for key, default_value in default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        self._log("info", "Water use disturbance initialized")
    
    def _start_disturbance_thread(self):
        """启动扰动线程"""
        self._disturbance_thread = threading.Thread(
            target=self._disturbance_worker,
            daemon=True
        )
        self._disturbance_thread.start()
    
    def _disturbance_worker(self):
        """扰动工作线程"""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # 执行step
                self.step(current_time)
                
                # 等待下一个周期
                self._stop_event.wait(self.publish_interval)
                
            except Exception as e:
                self._log("error", f"Disturbance worker error: {e}")
    
    def _generate_sinusoidal_disturbance(self, current_time: float) -> float:
        """生成正弦波扰动"""
        amplitude = self.parameters.get('amplitude', 1.0)
        frequency = self.parameters.get('frequency', 0.1)
        phase = self.parameters.get('phase', 0.0)
        offset = self.parameters.get('offset', 0.0)
        
        relative_time = current_time - self.start_time
        value = amplitude * math.sin(2 * math.pi * frequency * relative_time + phase) + offset
        
        return value
    
    def _generate_random_disturbance(self, current_time: float) -> float:
        """生成随机扰动"""
        distribution = self.parameters.get('distribution', 'uniform')
        
        if distribution == 'uniform':
            min_val = self.parameters.get('min', 0.0)
            max_val = self.parameters.get('max', 1.0)
            return np.random.uniform(min_val, max_val)
        elif distribution == 'normal':
            mean = self.parameters.get('mean', 0.0)
            std = self.parameters.get('std', 1.0)
            return np.random.normal(mean, std)
        else:
            return np.random.random()
    
    def _generate_step_disturbance(self, current_time: float) -> float:
        """生成阶跃扰动"""
        step_time = self.parameters.get('step_time', self.start_time + 1.0)
        initial_value = self.parameters.get('initial_value', 0.0)
        final_value = self.parameters.get('final_value', 1.0)
        
        if current_time < step_time:
            return initial_value
        else:
            return final_value
    
    def _generate_pulse_disturbance(self, current_time: float) -> float:
        """生成脉冲扰动"""
        pulse_start = self.parameters.get('pulse_start', self.start_time)
        pulse_duration = self.parameters.get('pulse_duration', 1.0)
        pulse_amplitude = self.parameters.get('pulse_amplitude', 1.0)
        baseline = self.parameters.get('baseline', 0.0)
        
        pulse_end = pulse_start + pulse_duration
        
        if pulse_start <= current_time <= pulse_end:
            return pulse_amplitude
        else:
            return baseline
    
    def _generate_ramp_disturbance(self, current_time: float) -> float:
        """生成斜坡扰动"""
        ramp_start = self.parameters.get('ramp_start', self.start_time)
        ramp_duration = self.parameters.get('ramp_duration', 10.0)
        initial_value = self.parameters.get('initial_value', 0.0)
        final_value = self.parameters.get('final_value', 1.0)
        
        if current_time < ramp_start:
            return initial_value
        elif current_time > ramp_start + ramp_duration:
            return final_value
        else:
            # 线性插值
            progress = (current_time - ramp_start) / ramp_duration
            return initial_value + progress * (final_value - initial_value)
    
    def _generate_csv_disturbance(self, current_time: float) -> float:
        """生成CSV扰动"""
        if self._csv_data is None or len(self._csv_data) == 0:
            return 0.0
        
        # 获取当前数据
        if self._csv_index < len(self._csv_data):
            row = self._csv_data.iloc[self._csv_index]
            value_column = self.parameters.get('value_column', self._csv_data.columns[-1])
            value = row[value_column] if value_column in row else 0.0
            
            self._csv_index += 1
            
            # 循环播放
            loop_data = self.parameters.get('loop_data', True)
            if self._csv_index >= len(self._csv_data) and loop_data:
                self._csv_index = 0
            
            return float(value)
        
        return 0.0
    
    def _generate_rainfall_disturbance(self, current_time: float) -> float:
        """生成降雨扰动"""
        base_intensity = self.parameters.get('base_intensity', 0.0)
        peak_intensity = self.parameters.get('peak_intensity', 10.0)
        storm_duration = self.parameters.get('storm_duration', 3600.0)
        storm_frequency = self.parameters.get('storm_frequency', 0.1)
        
        relative_time = current_time - self.start_time
        
        # 简单的降雨模式：基于随机数决定是否有暴雨
        if np.random.random() < storm_frequency * self.publish_interval / 3600.0:
            # 暴雨期间，使用正弦波模拟强度变化
            storm_phase = (relative_time % storm_duration) / storm_duration * 2 * math.pi
            intensity = base_intensity + (peak_intensity - base_intensity) * math.sin(storm_phase)**2
        else:
            # 正常降雨
            intensity = base_intensity + np.random.uniform(-0.1, 0.1) * base_intensity
        
        return max(0.0, intensity)
    
    def _generate_water_use_disturbance(self, current_time: float) -> float:
        """生成用水扰动"""
        base_demand = self.parameters.get('base_demand', 1.0)
        peak_factor = self.parameters.get('peak_factor', 2.0)
        daily_pattern = self.parameters.get('daily_pattern', True)
        
        demand = base_demand
        
        if daily_pattern:
            # 24小时周期的用水模式
            hour_of_day = (current_time / 3600.0) % 24
            
            # 早晚高峰用水模式
            morning_peak = 8.0  # 早上8点
            evening_peak = 19.0  # 晚上7点
            
            morning_factor = math.exp(-((hour_of_day - morning_peak) / 2.0)**2)
            evening_factor = math.exp(-((hour_of_day - evening_peak) / 2.0)**2)
            
            daily_factor = 1.0 + (peak_factor - 1.0) * max(morning_factor, evening_factor)
            demand *= daily_factor
        
        # 添加随机变化
        noise_factor = self.parameters.get('noise_factor', 0.1)
        demand *= (1.0 + np.random.uniform(-noise_factor, noise_factor))
        
        return max(0.0, demand)
    
    def _generate_composite_disturbance(self, current_time: float) -> float:
        """生成复合扰动"""
        total_value = 0.0
        
        for sub_disturbance in self._composite_disturbances:
            if sub_disturbance.is_active(current_time):
                sub_value = sub_disturbance.generate_disturbance(current_time)['value']
                weight = sub_disturbance.parameters.get('weight', 1.0)
                total_value += weight * sub_value
        
        return total_value
    
    def _publish_disturbance(self, current_time: float, disturbance_data: Dict[str, Any]):
        """发布扰动数据"""
        try:
            if self.event_bus:
                # 发布到通用主题
                self.event_bus.publish(self.publish_topic, disturbance_data)
                
                # 发布到目标组件特定主题
                for component in self.target_components:
                    component_topic = f'disturbance.{component}.{self.disturbance_type}'
                    self.event_bus.publish(component_topic, disturbance_data)
                
        except Exception as e:
            self._log("error", f"Disturbance publishing failed: {e}")
    
    def _record_disturbance(self, current_time: float, value: float):
        """记录扰动历史"""
        record = {
            'timestamp': current_time,
            'value': value,
            'disturbance_type': self.disturbance_type
        }
        
        self.disturbance_history.append(record)
        
        # 限制历史长度
        max_history = self.parameters.get('max_history', 1000)
        if len(self.disturbance_history) > max_history:
            self.disturbance_history = self.disturbance_history[-max_history:]
