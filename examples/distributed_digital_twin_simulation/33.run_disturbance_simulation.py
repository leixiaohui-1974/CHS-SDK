#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数字孪生扰动场景仿真运行脚本

本脚本用于运行各种扰动场景的仿真计算，包括：
- 基础扰动场景（网络延迟、数据丢包、节点故障等）
- 组合扰动场景（多种扰动的叠加效应）
- 性能指标监测和分析
- 结果数据收集和可视化
"""

import sys
import os
import logging
import yaml
import json
import pandas as pd
import numpy as np
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入CHS-SDK核心模块
from core_lib.io.yaml_loader import SimulationBuilder
from dynamic_disturbance_manager import DynamicDisturbanceManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('disturbance_simulation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DisturbanceSimulationRunner:
    """扰动场景仿真运行器"""
    
    def __init__(self, scenario_path: str):
        self.scenario_path = Path(scenario_path)
        self.disturbance_scenarios_path = self.scenario_path / "disturbance_scenarios"
        self.results_path = self.disturbance_scenarios_path / "analysis_results"
        self.results_path.mkdir(exist_ok=True)
        
        # 创建时间戳目录
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_results_path = self.results_path / f"session_{self.timestamp}"
        self.session_results_path.mkdir(exist_ok=True)
        
        logger.info(f"扰动仿真会话路径: {self.session_results_path}")
    
    def load_disturbance_scenarios(self) -> Dict[str, List[str]]:
        """加载所有扰动场景配置文件"""
        scenarios = {
            "basic_disturbances": [],
            "combined_disturbances": []
        }
        
        # 加载基础扰动场景
        basic_path = self.disturbance_scenarios_path / "basic_disturbances"
        if basic_path.exists():
            for yml_file in basic_path.glob("*.yml"):
                scenarios["basic_disturbances"].append(str(yml_file))
        
        # 加载组合扰动场景
        combined_path = self.disturbance_scenarios_path / "combined_disturbances"
        if combined_path.exists():
            for yml_file in combined_path.glob("*.yml"):
                scenarios["combined_disturbances"].append(str(yml_file))
        
        logger.info(f"发现 {len(scenarios['basic_disturbances'])} 个基础扰动场景")
        logger.info(f"发现 {len(scenarios['combined_disturbances'])} 个组合扰动场景")
        
        return scenarios
    
    def run_baseline_simulation(self) -> Dict[str, Any]:
        """运行基准仿真（无扰动）"""
        logger.info("=== 开始基准仿真（无扰动） ===")
        
        try:
            # 创建SimulationBuilder
            builder = SimulationBuilder(scenario_path=str(self.scenario_path))
            harness = builder.load()
            
            # 运行仿真
            result = harness.run_mas_simulation()
            
            # 收集性能指标
            baseline_metrics = self.collect_performance_metrics(harness, "baseline")
            
            # 保存基准结果
            baseline_file = self.session_results_path / "baseline_results.json"
            with open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(baseline_metrics, f, indent=2, ensure_ascii=False)
            
            logger.info("基准仿真完成")
            return baseline_metrics
            
        except Exception as e:
            logger.error(f"基准仿真失败: {e}")
            raise
    
    def load_disturbance_config(self, scenario_file: str) -> Dict[str, Any]:
        """加载扰动配置文件"""
        with open(scenario_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def run_disturbance_simulation(self, disturbance_config_file: str) -> Dict[str, Any]:
        """运行单个扰动场景仿真"""
        disturbance_name = Path(disturbance_config_file).stem
        logger.info(f"=== 开始扰动仿真: {disturbance_name} ===")
        
        try:
            # 加载并应用扰动配置
            disturbance_config = self.load_disturbance_config(disturbance_config_file)
            
            # 创建SimulationBuilder
            builder = SimulationBuilder(scenario_path=str(self.scenario_path))
            harness = builder.load()
            
            # 创建动态扰动管理器
            disturbance_manager = DynamicDisturbanceManager(harness.message_bus)
            
            # 注册扰动到动态管理器
            self.register_disturbances_to_manager(disturbance_manager, disturbance_config)
            
            # 运行带动态扰动管理的仿真
            result = self.run_simulation_with_dynamic_disturbances(harness, disturbance_manager)
            
            # 收集性能指标
            disturbance_metrics = self.collect_performance_metrics(harness, disturbance_name)
            disturbance_metrics["disturbance_config"] = disturbance_config
            
            # 保存扰动结果
            result_file = self.session_results_path / f"{disturbance_name}_results.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(disturbance_metrics, f, indent=2, ensure_ascii=False)
            
            logger.info(f"扰动仿真 {disturbance_name} 完成")
            return disturbance_metrics
            
        except Exception as e:
            logger.error(f"扰动仿真 {disturbance_name} 失败: {e}")
            raise
    
    def apply_disturbance_config(self, harness, disturbance_config: Dict[str, Any]):
        """应用扰动配置到仿真系统"""
        scenario_info = disturbance_config.get('disturbance_scenario', {})
        scenario_name = scenario_info.get('name', 'Unknown')
        scenario_type = scenario_info.get('type', 'unknown')
        
        logger.info(f"应用扰动配置: {scenario_name} (类型: {scenario_type})")
        
        # 根据扰动类型应用不同的扰动
        if scenario_type == 'network_delay':
            self.apply_network_delay_disturbance(harness, disturbance_config)
        elif scenario_type == 'data_packet_loss':
            self.apply_packet_loss_disturbance(harness, disturbance_config)
        elif scenario_type == 'node_failure':
            self.apply_node_failure_disturbance(harness, disturbance_config)
        elif scenario_type == 'inflow_variation':
            self.apply_inflow_variation_disturbance(harness, disturbance_config)
        elif scenario_type == 'demand_change':
            self.apply_demand_change_disturbance(harness, disturbance_config)
        elif scenario_type == 'sensor_interference':
            self.apply_sensor_interference_disturbance(harness, disturbance_config)
        elif scenario_type == 'actuator_interference':
            self.apply_actuator_interference_disturbance(harness, disturbance_config)
        elif scenario_type == 'combined':
            self.apply_combined_disturbance(harness, disturbance_config)
        else:
            logger.warning(f"未知的扰动类型: {scenario_type}")
            # 尝试通用的扰动应用方法
            self.apply_generic_disturbance(harness, disturbance_config)
    
    def apply_network_delay_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用网络延迟扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        delay_levels = parameters.get('delay_levels', {})
        affected_links = parameters.get('affected_links', [])
        
        logger.info(f"应用网络延迟扰动，影响 {len(affected_links)} 个通信链路")
        
        # 模拟网络延迟效果：随机延迟组件状态更新
        for component_name, component in harness.components.items():
            if 'Agent' in component_name or 'Twin' in component_name:
                # 为智能体组件添加随机延迟效果
                self.add_component_delay_effect(component, delay_levels.get('medium', {}))
     
    def apply_packet_loss_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用数据丢包扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        loss_rate = parameters.get('packet_loss_rate', 0.05)
        
        logger.info(f"应用数据丢包扰动，丢包率: {loss_rate*100}%")
        
        # 模拟数据丢包：随机跳过某些组件的状态更新
        for component_name, component in harness.components.items():
            if random.random() < loss_rate:
                self.add_component_packet_loss_effect(component)
     
    def apply_node_failure_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用节点故障扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        failed_nodes = parameters.get('failed_nodes', [])
        
        logger.info(f"应用节点故障扰动，故障节点: {failed_nodes}")
        
        # 模拟节点故障：禁用指定组件
        for node_name in failed_nodes:
            for component_name, component in harness.components.items():
                if node_name.lower() in component_name.lower():
                    self.add_component_failure_effect(component)
     
    def apply_inflow_variation_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用来水变化扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        variation_amplitude = parameters.get('variation_amplitude', 0.2)
        
        logger.info(f"应用来水变化扰动，变化幅度: {variation_amplitude*100}%")
        
        # 修改水库的初始水位和入流
        for component_name, component in harness.components.items():
            if 'Reservoir' in component_name or 'reservoir' in component_name:
                self.modify_reservoir_inflow(component, variation_amplitude)
     
    def apply_demand_change_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用需水变化扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        demand_change = parameters.get('demand_change_ratio', 0.3)
        
        logger.info(f"应用需水变化扰动，需求变化: {demand_change*100}%")
        
        # 修改下游需水量
        for component_name, component in harness.components.items():
            if 'Demand' in component_name or 'demand' in component_name:
                self.modify_demand_pattern(component, demand_change)
     
    def apply_sensor_interference_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用传感器干扰扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        noise_level = parameters.get('noise_level', 0.1)
        
        logger.info(f"应用传感器干扰扰动，噪声水平: {noise_level}")
        
        # 为传感器相关组件添加噪声
        for component_name, component in harness.components.items():
            if 'Sensor' in component_name or 'sensor' in component_name or 'Perception' in component_name:
                self.add_sensor_noise_effect(component, noise_level)
     
    def apply_actuator_interference_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用执行器干扰扰动"""
        parameters = disturbance_config.get('disturbance_scenario', {}).get('parameters', {})
        interference_level = parameters.get('interference_level', 0.15)
        
        logger.info(f"应用执行器干扰扰动，干扰水平: {interference_level}")
        
        # 为执行器相关组件添加干扰
        for component_name, component in harness.components.items():
            if 'Gate' in component_name or 'gate' in component_name or 'Control' in component_name:
                self.add_actuator_interference_effect(component, interference_level)
     
    def apply_combined_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用组合扰动"""
        combined_params = disturbance_config.get('combined_disturbance_parameters', {})
        
        logger.info("应用组合扰动")
        
        # 应用水文系统扰动
        hydrological_params = combined_params.get('hydrological_system', {})
        if hydrological_params:
            self.apply_hydrological_disturbance(harness, hydrological_params)
        
        # 应用控制系统扰动
        control_params = combined_params.get('control_system', {})
        if control_params:
            self.apply_control_system_disturbance(harness, control_params)
     
    def apply_generic_disturbance(self, harness, disturbance_config: Dict[str, Any]):
        """应用通用扰动"""
        logger.info("应用通用扰动效果")
        
        # 为所有组件添加轻微的随机扰动
        for component_name, component in harness.components.items():
            self.add_generic_disturbance_effect(component)
     
    # 辅助方法
    def add_component_delay_effect(self, component, delay_config: Dict[str, Any]):
        """为组件添加延迟效果"""
        # 通过修改组件的内部状态来模拟延迟
        if hasattr(component, '_disturbance_delay'):
            component._disturbance_delay = delay_config.get('base_delay', 50)
    
    def add_component_packet_loss_effect(self, component):
        """为组件添加丢包效果"""
        if hasattr(component, '_disturbance_packet_loss'):
            component._disturbance_packet_loss = True
    
    def add_component_failure_effect(self, component):
        """为组件添加故障效果"""
        if hasattr(component, '_disturbance_failed'):
            component._disturbance_failed = True
     
    def modify_reservoir_inflow(self, component, variation_amplitude: float):
        """修改水库入流"""
        try:
            # 直接修改组件的入流参数
            if hasattr(component, 'set_inflow'):
                # 生成变化的入流值
                base_inflow = getattr(component, '_base_inflow', 100.0)  # 默认基础入流
                variation = 1.0 + (random.random() - 0.5) * 2 * variation_amplitude
                new_inflow = base_inflow * variation
                component.set_inflow(new_inflow)
                logger.info(f"修改水库入流: {base_inflow} -> {new_inflow}")
            elif hasattr(component, '_state') and isinstance(component._state, dict):
                # 修改状态字典中的入流
                original_inflow = component._state.get('inflow', 100.0)
                variation = 1.0 + (random.random() - 0.5) * 2 * variation_amplitude
                new_inflow = original_inflow * variation
                component._state['inflow'] = new_inflow
                logger.info(f"修改水库入流状态: {original_inflow} -> {new_inflow}")
            else:
                # 为组件添加入流变化标记
                component._disturbance_inflow_variation = variation_amplitude
                logger.info(f"为组件添加入流变化标记: {variation_amplitude}")
        except Exception as e:
            logger.warning(f"无法修改水库入流: {e}")
     
    def modify_demand_pattern(self, component, demand_change: float):
        """修改需水模式"""
        try:
            # 尝试多种方式修改需水量
            if hasattr(component, 'set_demand'):
                # 直接设置需水量
                base_demand = getattr(component, '_base_demand', 50.0)  # 默认基础需水量
                new_demand = base_demand * (1 + demand_change)
                component.set_demand(new_demand)
                logger.info(f"修改需水量: {base_demand} -> {new_demand}")
            elif hasattr(component, '_state') and isinstance(component._state, dict):
                # 修改状态字典中的需水量
                original_demand = component._state.get('demand', 50.0)
                new_demand = original_demand * (1 + demand_change)
                component._state['demand'] = new_demand
                logger.info(f"修改需水量状态: {original_demand} -> {new_demand}")
            elif hasattr(component, '_state') and hasattr(component._state, 'demand'):
                # 修改状态对象的需水量属性
                original_demand = getattr(component._state, 'demand', 50.0)
                new_demand = original_demand * (1 + demand_change)
                setattr(component._state, 'demand', new_demand)
                logger.info(f"修改需水量属性: {original_demand} -> {new_demand}")
            else:
                # 为组件添加需水变化标记
                component._disturbance_demand_change = demand_change
                logger.info(f"为组件添加需水变化标记: {demand_change}")
        except Exception as e:
            logger.warning(f"无法修改需水量: {e}")
     
    def add_sensor_noise_effect(self, component, noise_level: float):
        """为传感器添加噪声效果"""
        try:
            # 为传感器组件添加噪声
            component._disturbance_noise_level = noise_level
            
            # 如果组件有状态，添加噪声到状态值
            if hasattr(component, '_state') and isinstance(component._state, dict):
                for key, value in component._state.items():
                    if isinstance(value, (int, float)):
                        noise = random.gauss(0, abs(value) * noise_level)
                        component._state[key] = value + noise
                        logger.info(f"为传感器 {key} 添加噪声: {value} -> {value + noise}")
            
            logger.info(f"为传感器组件添加噪声效果，噪声水平: {noise_level}")
        except Exception as e:
            logger.warning(f"无法添加传感器噪声: {e}")
    
    def add_actuator_interference_effect(self, component, interference_level: float):
        """为执行器添加干扰效果"""
        try:
            # 为执行器组件添加干扰
            component._disturbance_interference_level = interference_level
            
            # 如果组件有控制输出，添加干扰
            if hasattr(component, '_state') and isinstance(component._state, dict):
                for key, value in component._state.items():
                    if 'opening' in key.lower() or 'control' in key.lower():
                        if isinstance(value, (int, float)):
                            interference = random.uniform(-interference_level, interference_level)
                            new_value = max(0, min(1, value + interference))  # 限制在0-1范围内
                            component._state[key] = new_value
                            logger.info(f"为执行器 {key} 添加干扰: {value} -> {new_value}")
            
            logger.info(f"为执行器组件添加干扰效果，干扰水平: {interference_level}")
        except Exception as e:
            logger.warning(f"无法添加执行器干扰: {e}")
     
    def apply_hydrological_disturbance(self, harness, hydro_params: Dict[str, Any]):
        """应用水文系统扰动"""
        inflow_variation = hydro_params.get('inflow_variation', {})
        if inflow_variation:
            amplitude = inflow_variation.get('amplitude', 0.2)
            for component_name, component in harness.components.items():
                if 'Reservoir' in component_name:
                    self.modify_reservoir_inflow(component, amplitude)
    
    def apply_control_system_disturbance(self, harness, control_params: Dict[str, Any]):
        """应用控制系统扰动"""
        actuator_interference = control_params.get('actuator_interference', {})
        if actuator_interference:
            interference_level = actuator_interference.get('interference_level', 0.15)
            for component_name, component in harness.components.items():
                if 'Gate' in component_name:
                    self.add_actuator_interference_effect(component, interference_level)
    
    def add_generic_disturbance_effect(self, component):
        """添加通用扰动效果"""
        # 为组件添加轻微的随机扰动标记
        if hasattr(component, '_disturbance_generic'):
            component._disturbance_generic = True
    
    def register_disturbances_to_manager(self, disturbance_manager: DynamicDisturbanceManager, 
                                        disturbance_config: Dict[str, Any]):
        """将扰动注册到动态管理器"""
        scenario = disturbance_config.get('disturbance_scenario', {})
        disturbance_type = scenario.get('type', '')
        
        # 从配置中获取触发条件
        trigger_conditions = scenario.get('trigger_conditions', {})
        start_time = trigger_conditions.get('time_based', {}).get('start_time', 10.0)  # 默认10秒后开始
        disturbance_duration = trigger_conditions.get('time_based', {}).get('duration', 100.0)  # 默认持续100秒
        
        # 注册扰动
        disturbance_manager.register_disturbance(
            disturbance_id=disturbance_type,
            disturbance_config=disturbance_config,
            start_time=start_time,
            duration=disturbance_duration
        )
    
    def run_simulation_with_dynamic_disturbances(self, harness, disturbance_manager: DynamicDisturbanceManager):
        """运行带动态扰动管理的仿真"""
        logger.info("开始运行动态扰动仿真")
        
        # 手动运行仿真循环以集成扰动管理
        dt = 1.0  # 时间步长
        current_time = 0.0
        duration = 200.0  # 仿真总时长
        step_count = 0
        
        while current_time < duration:
            # 更新扰动管理器
            disturbance_manager.update(current_time, harness)
            
            # 运行一个仿真步骤
            if hasattr(harness, 'step'):
                harness.step()  # step方法不接受参数
            else:
                # 如果没有step方法，使用run_mas_simulation的简化版本
                for agent in harness.agents.values():
                    if hasattr(agent, 'step'):
                        agent.step(dt)
                for controller in harness.controllers.values():
                    if hasattr(controller, 'step'):
                        controller.step(dt)
            
            current_time += dt
            step_count += 1
            
            if step_count % 10 == 0:
                logger.debug(f"仿真进度: {current_time:.1f}/{duration}秒")
        
        return {"simulation_completed": True, "final_time": current_time}
    
    def collect_performance_metrics(self, harness, scenario_name: str) -> Dict[str, Any]:
        """收集仿真性能指标"""
        metrics = {
            "scenario_name": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "simulation_time": len(harness.history),
            "components_count": len(harness.components),
            "agents_count": len(harness.agents),
            "controllers_count": len(harness.controllers)
        }
        
        # 收集组件状态数据
        component_data = {}
        water_levels = []
        flow_rates = []
        gate_openings = []
        
        # 从仿真历史中提取数据
        for step_idx, step_data in enumerate(harness.history):
            # 遍历所有组件，收集状态数据
            for comp_name, component in harness.components.items():
                if comp_name not in component_data:
                    component_data[comp_name] = []
                
                # 获取组件当前状态
                try:
                    state = component.get_state()
                    if hasattr(state, '__dict__'):
                        state_dict = state.__dict__
                    else:
                        state_dict = state
                    
                    component_data[comp_name].append({
                        "time_step": step_idx,
                        "state": state_dict
                    })
                    
                    # 提取特定类型的数据
                    if isinstance(state_dict, dict):
                        # 水位数据
                        if 'water_level' in state_dict:
                            water_levels.append(state_dict['water_level'])
                        elif 'level' in state_dict:
                            water_levels.append(state_dict['level'])
                        
                        # 流量数据
                        if 'flow_rate' in state_dict:
                            flow_rates.append(state_dict['flow_rate'])
                        elif 'outflow' in state_dict:
                            flow_rates.append(state_dict['outflow'])
                        elif 'inflow' in state_dict:
                            flow_rates.append(state_dict['inflow'])
                        
                        # 闸门开度数据
                        if 'opening' in state_dict:
                            gate_openings.append(state_dict['opening'])
                        elif 'gate_opening' in state_dict:
                            gate_openings.append(state_dict['gate_opening'])
                
                except Exception as e:
                    logger.warning(f"无法获取组件 {comp_name} 的状态: {e}")
        
        # 计算统计指标
        if water_levels:
            metrics["water_level_stats"] = self.calculate_stats(water_levels)
            metrics["water_level_count"] = len(water_levels)
        
        if flow_rates:
            metrics["flow_rate_stats"] = self.calculate_stats(flow_rates)
            metrics["flow_rate_count"] = len(flow_rates)
        
        if gate_openings:
            metrics["gate_opening_stats"] = self.calculate_stats(gate_openings)
            metrics["gate_opening_count"] = len(gate_openings)
        
        # 添加组件级别的统计
        metrics["component_statistics"] = {}
        for comp_name, comp_data in component_data.items():
            if comp_data:
                metrics["component_statistics"][comp_name] = {
                    "data_points": len(comp_data),
                    "last_state": comp_data[-1]["state"] if comp_data else None
                }
        
        # 计算系统稳定性指标
        if water_levels:
            metrics["system_stability"] = {
                "water_level_variance": float(np.var(water_levels)),
                "water_level_range": float(max(water_levels) - min(water_levels)),
                "coefficient_of_variation": float(np.std(water_levels) / np.mean(water_levels)) if np.mean(water_levels) != 0 else 0
            }
        
        return metrics
    
    def calculate_stats(self, data_series: List[Any]) -> Dict[str, float]:
        """计算数据序列的统计指标"""
        if not data_series:
            return {}
        
        # 转换为numpy数组进行计算
        try:
            if isinstance(data_series[0], dict):
                # 如果是字典数据，提取数值
                values = []
                for item in data_series:
                    if isinstance(item, dict):
                        values.extend(item.values())
                    else:
                        values.append(item)
                data_array = np.array(values, dtype=float)
            else:
                data_array = np.array(data_series, dtype=float)
            
            return {
                "mean": float(np.mean(data_array)),
                "std": float(np.std(data_array)),
                "min": float(np.min(data_array)),
                "max": float(np.max(data_array)),
                "median": float(np.median(data_array))
            }
        except Exception as e:
            logger.warning(f"统计计算失败: {e}")
            return {}
    
    def run_all_scenarios(self) -> Dict[str, Any]:
        """运行所有扰动场景"""
        logger.info("=== 开始运行所有扰动场景 ===")
        
        # 加载扰动场景
        scenarios = self.load_disturbance_scenarios()
        
        # 运行基准仿真
        baseline_results = self.run_baseline_simulation()
        
        # 存储所有结果
        all_results = {
            "baseline": baseline_results,
            "basic_disturbances": {},
            "combined_disturbances": {}
        }
        
        # 运行基础扰动场景
        for scenario_file in scenarios["basic_disturbances"]:
            scenario_name = Path(scenario_file).stem
            try:
                result = self.run_disturbance_simulation(scenario_file)
                all_results["basic_disturbances"][scenario_name] = result
            except Exception as e:
                logger.error(f"基础扰动场景 {scenario_name} 运行失败: {e}")
                all_results["basic_disturbances"][scenario_name] = {"error": str(e)}
        
        # 运行组合扰动场景
        for scenario_file in scenarios["combined_disturbances"]:
            scenario_name = Path(scenario_file).stem
            try:
                result = self.run_disturbance_simulation(scenario_file)
                all_results["combined_disturbances"][scenario_name] = result
            except Exception as e:
                logger.error(f"组合扰动场景 {scenario_name} 运行失败: {e}")
                all_results["combined_disturbances"][scenario_name] = {"error": str(e)}
        
        # 保存汇总结果
        summary_file = self.session_results_path / "simulation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        # 生成分析报告
        self.generate_analysis_report(all_results)
        
        logger.info("所有扰动场景仿真完成")
        return all_results
    
    def generate_analysis_report(self, all_results: Dict[str, Any]):
        """生成分析报告"""
        logger.info("生成分析报告...")
        
        report = {
            "session_info": {
                "timestamp": self.timestamp,
                "total_scenarios": len(all_results["basic_disturbances"]) + len(all_results["combined_disturbances"]),
                "successful_scenarios": 0,
                "failed_scenarios": 0
            },
            "performance_comparison": {},
            "disturbance_impact_analysis": {}
        }
        
        # 统计成功和失败的场景
        for category in ["basic_disturbances", "combined_disturbances"]:
            for scenario_name, result in all_results[category].items():
                if "error" in result:
                    report["session_info"]["failed_scenarios"] += 1
                else:
                    report["session_info"]["successful_scenarios"] += 1
        
        # 性能对比分析
        baseline_metrics = all_results["baseline"]
        for category in ["basic_disturbances", "combined_disturbances"]:
            for scenario_name, result in all_results[category].items():
                if "error" not in result:
                    impact = self.calculate_disturbance_impact(baseline_metrics, result)
                    report["disturbance_impact_analysis"][scenario_name] = impact
        
        # 保存报告
        report_file = self.session_results_path / "analysis_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"分析报告已保存: {report_file}")
    
    def calculate_disturbance_impact(self, baseline: Dict[str, Any], disturbance: Dict[str, Any]) -> Dict[str, Any]:
        """计算扰动影响"""
        impact = {
            "scenario_name": disturbance.get("scenario_name", "Unknown"),
            "performance_degradation": {}
        }
        
        # 比较水位统计
        if "water_level_stats" in baseline and "water_level_stats" in disturbance:
            baseline_stats = baseline["water_level_stats"]
            disturbance_stats = disturbance["water_level_stats"]
            
            impact["performance_degradation"]["water_level"] = {
                "std_change": disturbance_stats.get("std", 0) - baseline_stats.get("std", 0),
                "mean_change": disturbance_stats.get("mean", 0) - baseline_stats.get("mean", 0)
            }
        
        # 比较流量统计
        if "flow_rate_stats" in baseline and "flow_rate_stats" in disturbance:
            baseline_stats = baseline["flow_rate_stats"]
            disturbance_stats = disturbance["flow_rate_stats"]
            
            impact["performance_degradation"]["flow_rate"] = {
                "std_change": disturbance_stats.get("std", 0) - baseline_stats.get("std", 0),
                "mean_change": disturbance_stats.get("mean", 0) - baseline_stats.get("mean", 0)
            }
        
        return impact

def main():
    """主函数"""
    try:
        # 获取当前目录作为场景路径
        scenario_path = Path(__file__).parent
        
        # 创建扰动仿真运行器
        runner = DisturbanceSimulationRunner(str(scenario_path))
        
        # 运行所有扰动场景
        results = runner.run_all_scenarios()
        
        logger.info("=== 扰动场景仿真全部完成 ===")
        logger.info(f"结果保存在: {runner.session_results_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"扰动仿真运行失败: {e}")
        logger.exception("详细错误信息:")
        raise

if __name__ == "__main__":
    main()