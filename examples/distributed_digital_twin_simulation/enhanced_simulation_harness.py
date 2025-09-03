#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版仿真框架，集成网络扰动功能
支持物理扰动和网络扰动的统一管理
"""

import sys
import os
import threading
import copy
from collections import deque
from typing import List, Dict, Any, NamedTuple, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core_lib.core.interfaces import Simulatable, Agent, Controller
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.disturbances.disturbance_framework import DisturbanceManager, BaseDisturbance

# 导入网络扰动相关模块
from enhanced_message_bus import EnhancedMessageBus
from network_disturbance import NetworkDisturbanceManager, NetworkDelayDisturbance, PacketLossDisturbance
from dynamic_disturbance_manager import DynamicDisturbanceManager

class ControllerSpec(NamedTuple):
    """定义控制器在简单仿真中的连接规范"""
    controller: Controller
    controlled_id: str
    observed_id: str
    observation_key: str

class EnhancedSimulationHarness:
    """
    增强版仿真框架，支持物理扰动和网络扰动的统一管理
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.start_time = config.get('start_time', 0)
        self.end_time = config.get('end_time', 100)
        self.dt = config.get('dt', 1.0)
        self.t = self.start_time

        self.history = []

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}

        # 图表示：下游和上游连接的邻接列表
        self.topology: Dict[str, List[str]] = {}
        self.inverse_topology: Dict[str, List[str]] = {}
        self.sorted_components: List[str] = []

        # 根据配置选择消息总线类型
        self.enable_network_disturbance = config.get('enable_network_disturbance', False)
        
        if self.enable_network_disturbance:
            self.message_bus = EnhancedMessageBus()
            print("使用增强消息总线，支持网络扰动")
        else:
            self.message_bus = MessageBus()
            print("使用标准消息总线")
        
        self._is_paused = threading.Event()
        self.is_running = False
        
        # 物理扰动管理器
        self.disturbance_manager = DisturbanceManager()
        
        # 动态扰动管理器（用于传感器、执行器等扰动）
        self.dynamic_disturbance_manager = DynamicDisturbanceManager(self.message_bus)
        
        # 网络扰动管理器（仅在启用网络扰动时创建）
        self.network_disturbance_manager = None
        if self.enable_network_disturbance:
            self.network_disturbance_manager = NetworkDisturbanceManager(self.message_bus)
            print("网络扰动管理器已创建")

        print("增强版仿真框架已创建")

    def add_component(self, component_id: str, component: Simulatable):
        """向仿真中添加物理或逻辑组件"""
        if component_id in self.components:
            raise ValueError(f"ID为'{component_id}'的组件已存在")
        self.components[component_id] = component
        self.topology[component_id] = []
        self.inverse_topology[component_id] = []
        print(f"组件'{component_id}'已添加")

    def add_connection(self, upstream_id: str, downstream_id: str):
        """在两个组件之间添加有向连接"""
        if upstream_id not in self.components:
            raise ValueError(f"上游组件'{upstream_id}'未找到")
        if downstream_id not in self.components:
            raise ValueError(f"下游组件'{downstream_id}'未找到")

        self.topology[upstream_id].append(downstream_id)
        self.inverse_topology[downstream_id].append(upstream_id)
        print(f"连接已添加: {upstream_id} -> {downstream_id}")

    def add_agent(self, agent: Agent):
        """向仿真中添加智能体"""
        self.agents.append(agent)
        
        # 如果启用了网络扰动，为智能体设置增强消息总线
        if hasattr(agent, 'set_message_bus') and self.enable_network_disturbance:
            agent.set_message_bus(self.message_bus)
            print(f"智能体 {getattr(agent, 'agent_id', 'unknown')} 已配置增强消息总线")

    def add_controller(self, controller_id: str, controller: Controller, controlled_id: str, observed_id: str, observation_key: str):
        """将控制器与特定组件及其观测源关联"""
        spec = ControllerSpec(controller, controlled_id, observed_id, observation_key)
        self.controllers[controller_id] = spec
        print(f"控制器'{controller_id}'已与组件'{controlled_id}'关联")
    
    def add_disturbance(self, disturbance: BaseDisturbance):
        """添加物理扰动到仿真中"""
        self.disturbance_manager.register_disturbance(disturbance)
        print(f"物理扰动 {disturbance.config.disturbance_id} 已添加到仿真中")
    
    def add_network_disturbance(self, disturbance_id: str, disturbance_type: str, config: Dict[str, Any]):
        """添加网络扰动到仿真中"""
        if not self.enable_network_disturbance:
            raise ValueError("网络扰动功能未启用，请在配置中设置 enable_network_disturbance=True")
        
        if not self.network_disturbance_manager:
            raise ValueError("网络扰动管理器未初始化")
        
        if disturbance_type == 'delay':
            disturbance = self.network_disturbance_manager.create_network_delay_disturbance(disturbance_id, config)
        elif disturbance_type == 'packet_loss':
            disturbance = self.network_disturbance_manager.create_packet_loss_disturbance(disturbance_id, config)
        else:
            raise ValueError(f"不支持的网络扰动类型: {disturbance_type}")
        
        print(f"网络扰动 {disturbance_id} ({disturbance_type}) 已添加到仿真中")
        return disturbance
    
    def activate_network_disturbance(self, disturbance_id: str, start_time: float, duration: float):
        """激活网络扰动"""
        if not self.network_disturbance_manager:
            raise ValueError("网络扰动管理器未初始化")
        
        self.network_disturbance_manager.activate_disturbance(disturbance_id, start_time, duration)
        print(f"网络扰动 {disturbance_id} 已激活，开始时间: {start_time}, 持续时间: {duration}")
    
    def add_dynamic_disturbance(self, disturbance_config: Dict[str, Any]):
        """添加动态扰动（传感器、执行器等）"""
        disturbance_id = disturbance_config.get('disturbance_id', 'unknown')
        start_time = disturbance_config.get('start_time', 0.0)
        duration = disturbance_config.get('duration', 10.0)
        self.dynamic_disturbance_manager.register_disturbance(disturbance_id, disturbance_config, start_time, duration)
        print(f"动态扰动 {disturbance_config['disturbance_id']} 已添加")
    
    def activate_dynamic_disturbance(self, disturbance_id: str, target_component: str, start_time: float, duration: float):
        """激活动态扰动"""
        disturbance_config = {
            'disturbance_id': disturbance_id,
            'type': 'sensor_noise',
            'target_component': target_component,
            'parameters': {
                'noise_std': 0.01,
                'interference_level': 0.15
            }
        }
        self.dynamic_disturbance_manager.register_disturbance(
            disturbance_id, disturbance_config, start_time, duration
        )
        print(f"动态扰动 {disturbance_id} 已在组件 {target_component} 上激活")
    
    def remove_disturbance(self, disturbance_id: str):
        """从仿真中移除扰动"""
        # 尝试从物理扰动管理器中移除
        try:
            self.disturbance_manager.remove_disturbance(disturbance_id)
            print(f"物理扰动 {disturbance_id} 已从仿真中移除")
            return
        except:
            pass
        
        # 尝试从网络扰动管理器中移除
        if self.network_disturbance_manager:
            try:
                self.network_disturbance_manager.deactivate_disturbance(disturbance_id)
                print(f"网络扰动 {disturbance_id} 已从仿真中移除")
                return
            except:
                pass
        
        # 尝试从动态扰动管理器中移除
        try:
            self.dynamic_disturbance_manager.deactivate_disturbance(disturbance_id)
            print(f"动态扰动 {disturbance_id} 已从仿真中移除")
            return
        except:
            pass
        
        print(f"警告: 未找到扰动 {disturbance_id}")
    
    def get_active_disturbances(self) -> Dict[str, List[str]]:
        """获取当前活跃的扰动列表"""
        result = {
            'physical': self.disturbance_manager.get_active_disturbances(),
            'dynamic': list(self.dynamic_disturbance_manager.active_disturbances.keys()),
            'network': []
        }
        
        if self.network_disturbance_manager:
            status = self.network_disturbance_manager.get_all_status()
            result['network'] = list(status['active_disturbances'].keys())
        
        return result
    
    def get_disturbance_status(self) -> Dict[str, Any]:
        """获取所有扰动的详细状态"""
        status = {
            'physical': {
                'active': self.disturbance_manager.get_active_disturbances(),
                'history': self.disturbance_manager.get_disturbance_history()
            },
            'dynamic': {
                'active': list(self.dynamic_disturbance_manager.active_disturbances.keys()),
                'registered': list(self.dynamic_disturbance_manager.active_disturbances.keys())
            },
            'network': None
        }
        
        if self.network_disturbance_manager:
            status['network'] = self.network_disturbance_manager.get_all_status()
        
        return status

    def _topological_sort(self):
        """对组件进行拓扑排序以确保正确的计算顺序"""
        in_degree = {cid: len(self.inverse_topology[cid]) for cid in self.components}
        queue = deque([cid for cid, degree in in_degree.items() if degree == 0])
        sorted_order = []

        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            for neighbor in self.topology[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(self.components):
            raise ValueError("检测到循环依赖，无法进行拓扑排序")

        self.sorted_components = sorted_order
        print(f"拓扑排序完成: {self.sorted_components}")

    def build(self):
        """构建仿真环境"""
        self._topological_sort()
        self.message_bus.set_component_topology(self.topology)
        self.is_running = True
        print("仿真环境构建完成")

    def pause(self):
        """暂停仿真"""
        self._is_paused.set()
        print("仿真已暂停")

    def resume(self):
        """恢复仿真"""
        self._is_paused.clear()
        print("仿真已恢复")

    def step(self):
        """执行一个仿真步骤（多智能体模式）"""
        # Phase 1: 更新所有扰动
        self._update_all_disturbances()
        
        # Phase 2: 智能体感知和决策
        for agent in self.agents:
            try:
                agent.perceive()
                agent.decide()
            except Exception as e:
                print(f"智能体 {getattr(agent, 'agent_id', 'unknown')} 执行错误: {e}")
        
        # Phase 3: 步进物理模型
        self._step_physical_models(self.dt)
        
        # Phase 4: 智能体执行动作
        for agent in self.agents:
            try:
                agent.act()
            except Exception as e:
                print(f"智能体 {getattr(agent, 'agent_id', 'unknown')} 动作执行错误: {e}")
        
        # Phase 5: 记录历史
        step_history = {'time': self.t}
        for cid in self.sorted_components:
            step_history[cid] = self.components[cid].get_state()
        
        # 添加扰动状态信息
        step_history['disturbance_status'] = self.get_disturbance_status()
        
        self.history.append(step_history)
        
        # 更新时间
        self.t += self.dt

    def _update_all_disturbances(self):
        """更新所有类型的扰动"""
        # 更新物理扰动
        disturbance_effects = self.disturbance_manager.update(self.t, self.dt, self.components)
        
        # 更新动态扰动
        self.dynamic_disturbance_manager.update(self.t, self.agents)
        
        # 更新网络扰动
        if self.network_disturbance_manager:
            self.network_disturbance_manager.update_all(self.t)

    def run_mas_simulation(self):
        """运行多智能体系统仿真"""
        print(f"开始多智能体仿真，时间范围: {self.start_time} 到 {self.end_time}，步长: {self.dt}")
        
        while self.t < self.end_time and self.is_running:
            # 检查是否暂停
            if self._is_paused.is_set():
                self._is_paused.wait()
                continue
            
            # 执行一个仿真步骤
            self.step()
        
        print(f"多智能体仿真完成，结束时间: {self.t:.2f}s")
        print(f"生成了 {len(self.history)} 步历史数据")

    def run_simulation(self):
        """运行简单仿真（非智能体模式）"""
        print(f"开始简单仿真，时间范围: {self.start_time} 到 {self.end_time}，步长: {self.dt}")
        
        while self.t < self.end_time and self.is_running:
            # 检查是否暂停
            if self._is_paused.is_set():
                self._is_paused.wait()
                continue
            
            # Phase 1: 更新所有扰动
            self._update_all_disturbances()
            
            # Phase 2: 计算控制器动作
            controller_actions = {}
            for controller_id, spec in self.controllers.items():
                try:
                    # 获取观测值
                    observed_component = self.components[spec.observed_id]
                    observation = observed_component.get_state().get(spec.observation_key, 0)
                    
                    # 计算控制动作
                    action = spec.controller.compute_control_action({'process_variable': observation}, self.dt)
                    controller_actions[spec.controlled_id] = action
                    
                except Exception as e:
                    print(f"控制器 {controller_id} 错误: {e}")
            
            # Phase 3: 步进物理模型
            self._step_physical_models(self.dt, controller_actions)
            
            # Phase 4: 记录历史
            step_history = {'time': self.t}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            
            # 添加扰动状态信息
            step_history['disturbance_status'] = self.get_disturbance_status()
            
            self.history.append(step_history)
            
            # 更新时间
            self.t += self.dt
        
        print(f"简单仿真完成，结束时间: {self.t:.2f}s")
        print(f"生成了 {len(self.history)} 步历史数据")

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        """步进物理模型"""
        if controller_actions is None:
            controller_actions = {}

        # 更新物理扰动状态
        disturbance_effects = self.disturbance_manager.update(self.t, dt, self.components)
        
        new_states = {}
        current_step_outflows = {}
        
        # 记录哪些组件受到扰动影响，避免自动入流覆盖
        disturbed_components = set()
        for disturbance_id, effect in disturbance_effects.items():
            if 'applied_inflow' in effect:
                # 找到对应的扰动配置
                for dist_id, disturbance in self.disturbance_manager.active_disturbances.items():
                    if dist_id == disturbance_id and hasattr(disturbance, 'config'):
                        target_component = disturbance.config.target_component
                        disturbed_components.add(target_component)
                        break
        
        # 按拓扑顺序更新组件
        for component_id in self.sorted_components:
            component = self.components[component_id]
            
            # 计算入流
            total_inflow = 0
            if component_id not in disturbed_components:  # 只有未受扰动影响的组件才使用自动入流
                for upstream_id in self.inverse_topology[component_id]:
                    if upstream_id in current_step_outflows:
                        total_inflow += current_step_outflows[upstream_id]
            
            # 应用控制器动作
            control_action = controller_actions.get(component_id, {})
            
            # 步进组件
            component.step(dt, total_inflow, **control_action)
            
            # 记录新状态和出流
            new_state = component.get_state()
            new_states[component_id] = new_state
            current_step_outflows[component_id] = new_state.get('outflow', 0)

    def export_output_data(self, output_dir: str = "output"):
        """导出输出数据"""
        import json
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 导出仿真历史
        history_file = os.path.join(output_dir, "simulation_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        
        # 导出扰动状态
        disturbance_file = os.path.join(output_dir, "disturbance_status.json")
        with open(disturbance_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_disturbance_status(), f, indent=2, ensure_ascii=False)
        
        # 导出网络扰动统计（如果有）
        if self.network_disturbance_manager:
            network_stats_file = os.path.join(output_dir, "network_disturbance_stats.json")
            network_status = self.network_disturbance_manager.get_all_status()
            with open(network_stats_file, 'w', encoding='utf-8') as f:
                json.dump(network_status, f, indent=2, ensure_ascii=False)
        
        print(f"输出数据已导出到 {output_dir}")
    
    def shutdown(self):
        """关闭仿真框架"""
        self.is_running = False
        
        # 关闭网络扰动管理器
        if self.network_disturbance_manager:
            self.network_disturbance_manager.shutdown()
        
        # 关闭消息总线
        if hasattr(self.message_bus, 'shutdown'):
            self.message_bus.shutdown()
        
        print("增强版仿真框架已关闭")

    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass