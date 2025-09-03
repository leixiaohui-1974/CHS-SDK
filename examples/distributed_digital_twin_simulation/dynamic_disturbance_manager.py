#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态扰动管理器
在仿真运行期间持续应用扰动效果，确保扰动能够真正影响物理计算过程
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

logger = logging.getLogger(__name__)

class DynamicDisturbanceManager:
    """动态扰动管理器，在仿真运行期间持续应用扰动效果"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.active_disturbances = {}
        self.disturbance_history = []
        
    def register_disturbance(self, disturbance_id: str, disturbance_config: Dict[str, Any], 
                           start_time: float, duration: float):
        """注册一个扰动场景"""
        self.active_disturbances[disturbance_id] = {
            'config': disturbance_config,
            'start_time': start_time,
            'end_time': start_time + duration,
            'is_active': False,
            'applied_components': set()
        }
        logger.info(f"注册扰动 {disturbance_id}，开始时间: {start_time}s，持续时间: {duration}s")
    
    def update(self, current_time: float, harness):
        """在每个仿真步骤中更新扰动状态"""
        for disturbance_id, disturbance_info in self.active_disturbances.items():
            start_time = disturbance_info['start_time']
            end_time = disturbance_info['end_time']
            
            # 检查扰动是否应该激活
            should_be_active = start_time <= current_time <= end_time
            
            if should_be_active and not disturbance_info['is_active']:
                # 激活扰动
                self._activate_disturbance(disturbance_id, disturbance_info, harness)
                disturbance_info['is_active'] = True
                logger.info(f"激活扰动 {disturbance_id} 在时间 {current_time}s")
                
            elif not should_be_active and disturbance_info['is_active']:
                # 停用扰动
                self._deactivate_disturbance(disturbance_id, disturbance_info, harness)
                disturbance_info['is_active'] = False
                logger.info(f"停用扰动 {disturbance_id} 在时间 {current_time}s")
                
            elif should_be_active and disturbance_info['is_active']:
                # 持续应用扰动
                self._apply_continuous_disturbance(disturbance_id, disturbance_info, harness, current_time)
    
    def _activate_disturbance(self, disturbance_id: str, disturbance_info: Dict, harness):
        """激活扰动"""
        config = disturbance_info['config']
        disturbance_type = config.get('type', '')
        
        if 'network_delay' in disturbance_type:
            self._apply_network_delay_disturbance(disturbance_info, harness)
        elif 'inflow_variation' in disturbance_type:
            self._apply_inflow_variation_disturbance(disturbance_info, harness)
        elif 'sensor_interference' in disturbance_type:
            self._apply_sensor_interference_disturbance(disturbance_info, harness)
        elif 'actuator_interference' in disturbance_type:
            self._apply_actuator_interference_disturbance(disturbance_info, harness)
        elif 'demand_change' in disturbance_type:
            self._apply_demand_change_disturbance(disturbance_info, harness)
    
    def _deactivate_disturbance(self, disturbance_id: str, disturbance_info: Dict, harness):
        """停用扰动，恢复组件正常状态"""
        for component_name in disturbance_info['applied_components']:
            if component_name in harness.components:
                component = harness.components[component_name]
                # 移除扰动标记
                if hasattr(component, '_disturbance_active'):
                    component._disturbance_active = False
                if hasattr(component, '_disturbance_factors'):
                    component._disturbance_factors.clear()
        
        disturbance_info['applied_components'].clear()
    
    def _apply_continuous_disturbance(self, disturbance_id: str, disturbance_info: Dict, 
                                    harness, current_time: float):
        """持续应用扰动效果"""
        config = disturbance_info['config']
        disturbance_type = config.get('type', '')
        
        # 对于需要持续变化的扰动（如随机噪声），在这里更新参数
        if 'sensor_interference' in disturbance_type:
            self._update_sensor_noise(disturbance_info, harness, current_time)
        elif 'inflow_variation' in disturbance_type:
            self._update_inflow_variation(disturbance_info, harness, current_time)
    
    def _apply_network_delay_disturbance(self, disturbance_info: Dict, harness):
        """应用网络延迟扰动"""
        config = disturbance_info['config']
        parameters = config.get('disturbance_scenario', {}).get('parameters', {})
        
        # 为所有智能体添加通信延迟
        for agent_name, agent in harness.agents.items():
            if hasattr(agent, 'message_bus'):
                # 添加延迟标记
                agent._disturbance_delay = parameters.get('base_delay', 100) / 1000.0  # 转换为秒
                agent._disturbance_jitter = parameters.get('jitter', 50) / 1000.0
                agent._disturbance_packet_loss = parameters.get('packet_loss', 0.05)
                agent._disturbance_active = True
                disturbance_info['applied_components'].add(agent_name)
    
    def _apply_inflow_variation_disturbance(self, disturbance_info: Dict, harness):
        """应用入流变化扰动"""
        config = disturbance_info['config']
        parameters = config.get('disturbance_scenario', {}).get('parameters', {})
        
        for component_name, component in harness.components.items():
            if 'Reservoir' in str(type(component)) or 'reservoir' in component_name.lower():
                # 设置入流变化参数
                component._disturbance_inflow_base = parameters.get('base_inflow', 100.0)
                component._disturbance_inflow_amplitude = parameters.get('seasonal_variation', {}).get('amplitude', 60.0)
                component._disturbance_inflow_noise = parameters.get('random_noise', {}).get('std_dev', 15.0)
                component._disturbance_active = True
                disturbance_info['applied_components'].add(component_name)
    
    def _apply_sensor_interference_disturbance(self, disturbance_info: Dict, harness):
        """应用传感器干扰扰动"""
        config = disturbance_info['config']
        parameters = config.get('disturbance_scenario', {}).get('parameters', {})
        
        for agent_name, agent in harness.agents.items():
            if 'perception' in agent_name.lower() or 'sensor' in agent_name.lower():
                # 设置传感器噪声参数
                noise_params = parameters.get('noise_characteristics', {})
                agent._disturbance_noise_std = noise_params.get('gaussian', {}).get('std_dev', 0.15)
                agent._disturbance_noise_uniform = noise_params.get('uniform', {}).get('range', [-0.3, 0.3])
                agent._disturbance_spike_prob = noise_params.get('spike', {}).get('probability', 0.05)
                agent._disturbance_spike_amplitude = noise_params.get('spike', {}).get('amplitude', 1.0)
                agent._disturbance_active = True
                disturbance_info['applied_components'].add(agent_name)
    
    def _apply_actuator_interference_disturbance(self, disturbance_info: Dict, harness):
        """应用执行器干扰扰动"""
        config = disturbance_info['config']
        parameters = config.get('disturbance_scenario', {}).get('parameters', {})
        
        for component_name, component in harness.components.items():
            if 'Gate' in str(type(component)) or 'Pump' in str(type(component)):
                # 设置执行器干扰参数
                interference = parameters.get('interference_types', {})
                component._disturbance_bias = interference.get('bias', {}).get('constant_offset', 0.3)
                component._disturbance_noise_std = interference.get('noise', {}).get('gaussian_std', 0.2)
                component._disturbance_delay = interference.get('delay', {}).get('response_delay', 5.0)
                component._disturbance_active = True
                disturbance_info['applied_components'].add(component_name)
    
    def _apply_demand_change_disturbance(self, disturbance_info: Dict, harness):
        """应用需水量变化扰动"""
        config = disturbance_info['config']
        parameters = config.get('disturbance_scenario', {}).get('parameters', {})
        
        for component_name, component in harness.components.items():
            if hasattr(component, '_state') and 'demand' in str(component._state).lower():
                # 设置需水量变化参数
                component._disturbance_demand_multiplier = parameters.get('seasonal_variation', {}).get('summer_multiplier', 2.5)
                component._disturbance_demand_noise = parameters.get('random_fluctuation', {}).get('variation_range', 0.5)
                component._disturbance_active = True
                disturbance_info['applied_components'].add(component_name)
    
    def _update_sensor_noise(self, disturbance_info: Dict, harness, current_time: float):
        """更新传感器噪声"""
        for component_name in disturbance_info['applied_components']:
            if component_name in harness.agents:
                agent = harness.agents[component_name]
                if hasattr(agent, '_disturbance_active') and agent._disturbance_active:
                    # 生成新的噪声值
                    if hasattr(agent, '_disturbance_noise_std'):
                        agent._current_noise = np.random.normal(0, agent._disturbance_noise_std)
    
    def _update_inflow_variation(self, disturbance_info: Dict, harness, current_time: float):
        """更新入流变化"""
        for component_name in disturbance_info['applied_components']:
            if component_name in harness.components:
                component = harness.components[component_name]
                if hasattr(component, '_disturbance_active') and component._disturbance_active:
                    # 计算时变入流
                    base_inflow = getattr(component, '_disturbance_inflow_base', 100.0)
                    amplitude = getattr(component, '_disturbance_inflow_amplitude', 60.0)
                    noise_std = getattr(component, '_disturbance_inflow_noise', 15.0)
                    
                    # 季节性变化（简化为正弦波）
                    seasonal_factor = amplitude * np.sin(2 * np.pi * current_time / 8760)  # 年周期
                    # 随机噪声
                    noise_factor = np.random.normal(0, noise_std)
                    
                    # 计算扰动后的入流
                    disturbed_inflow = base_inflow + seasonal_factor + noise_factor
                    
                    # 直接修改组件的入流
                    if hasattr(component, '_inflow'):
                        component._inflow = max(0, disturbed_inflow)
                    elif hasattr(component, 'data_inflow'):
                        component.data_inflow = max(0, disturbed_inflow)
    
    def get_disturbance_status(self) -> Dict[str, Any]:
        """获取当前扰动状态"""
        status = {}
        for disturbance_id, info in self.active_disturbances.items():
            status[disturbance_id] = {
                'is_active': info['is_active'],
                'start_time': info['start_time'],
                'end_time': info['end_time'],
                'affected_components': list(info['applied_components'])
            }
        return status