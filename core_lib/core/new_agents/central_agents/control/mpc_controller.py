"""
MPC控制智能体

基于模型预测控制的中央控制智能体，继承新的接口规范。
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.optimize import minimize

from core_lib.core.new_interfaces import CentralControlAgent
from core_lib.core.event_bus import get_global_event_bus, Message


class MPCController:
    """
    MPC控制器实现
    
    迁移自旧的MPCAgent，现在作为CentralControlAgent的控制策略
    """
    """
    MPC (Model Predictive Control) 中央控制智能体
    
    使用模型预测控制算法计算最优的水位设定点，并发送给下游的PID控制器。
    基于新的标准化接口实现，提供更好的可维护性和扩展性。
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, **config):
        """
        初始化MPC智能体
        
        Args:
            agent_id: 智能体ID
            message_bus: 消息总线
            **config: 配置参数
        """
        super().__init__(agent_id, message_bus, **config)
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{agent_id}")
        
        # MPC参数
        self.prediction_horizon = config.get("prediction_horizon", 10)
        self.control_horizon = config.get("control_horizon", 3)
        self.time_step = config.get("time_step", 60.0)
        self.q_weight = config.get("q_weight", 1.0)
        self.r_weight = config.get("r_weight", 0.1)
        
        # 控制目标和状态
        self.control_targets = config.get("control_targets", [])
        self.state_sources = config.get("state_sources", {})
        self.command_topics = config.get("command_topics", {})
        
        # 模型参数
        self.target_levels = np.array(config.get("target_water_levels", []))
        self.mpc_pid_model_kp = config.get("mpc_pid_model_kp", 0.5)
        self.level_bounds = config.get("level_setpoint_bounds", [])
        self.flood_thresholds = np.array(config.get("flood_thresholds", []))
        self.canal_areas = np.array(config.get("canal_surface_areas", []))
        self.outflow_coeff = config.get("outflow_coefficient", 1000.0)
        
        # 状态存储
        self.latest_states: Dict[str, float] = {}
        self.latest_forecast: List[float] = [0.0] * self.prediction_horizon
        
        # 性能指标
        self.metrics = {
            "optimization_calls": 0,
            "successful_optimizations": 0,
            "average_cost": 0.0,
            "last_optimization_time": 0.0
        }
        
        self.logger.info(f"MPCAgent '{agent_id}' created with {len(self.control_targets)} targets")

    def initialize(self) -> bool:
        """初始化智能体"""
        try:
            # 订阅状态主题
            for state_name, topic in self.state_sources.items():
                handler = MessageHandler(
                    lambda msg, name=state_name: self._handle_state_message(msg, name),
                    f"{self.agent_id}_state_{state_name}",
                    include_envelope=False
                )
                self.message_bus.subscribe(topic, handler)
                self.logger.info(f"Subscribed to state topic '{topic}' for '{state_name}'")
            
            # 订阅预测主题
            forecast_topic = self.config.get("forecast_topic")
            if forecast_topic:
                handler = MessageHandler(
                    self._handle_forecast_message,
                    f"{self.agent_id}_forecast",
                    include_envelope=False
                )
                self.message_bus.subscribe(forecast_topic, handler)
                self.logger.info(f"Subscribed to forecast topic '{forecast_topic}'")
            
            self.status = "initialized"
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            self.status = "error"
            return False

    def start(self) -> bool:
        """启动智能体"""
        if self.status != "initialized":
            return False
        
        self.is_active = True
        self.status = "running"
        self.logger.info(f"MPCAgent '{self.agent_id}' started")
        return True

    def stop(self) -> bool:
        """停止智能体"""
        self.is_active = False
        self.status = "stopped"
        self.logger.info(f"MPCAgent '{self.agent_id}' stopped")
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "is_active": self.is_active,
            "control_targets": self.control_targets,
            "state_count": len(self.latest_states),
            "last_run_time": getattr(self, '_last_run_time', None)
        }

    def get_metrics(self) -> Dict[str, float]:
        """获取性能指标"""
        success_rate = 0.0
        if self.metrics["optimization_calls"] > 0:
            success_rate = self.metrics["successful_optimizations"] / self.metrics["optimization_calls"]
        
        return {
            "optimization_calls": float(self.metrics["optimization_calls"]),
            "successful_optimizations": float(self.metrics["successful_optimizations"]),
            "success_rate": success_rate,
            "average_cost": self.metrics["average_cost"],
            "last_optimization_time": self.metrics["last_optimization_time"]
        }

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 更新可动态修改的参数
            if "q_weight" in new_config:
                self.q_weight = new_config["q_weight"]
            if "r_weight" in new_config:
                self.r_weight = new_config["r_weight"]
            if "target_water_levels" in new_config:
                self.target_levels = np.array(new_config["target_water_levels"])
            
            self.config.update(new_config)
            self.logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False

    def run(self, current_time: float):
        """主运行循环"""
        if not self.is_active:
            return
        
        self._last_run_time = current_time
        
        # 检查是否有足够的状态数据
        if len(self.latest_states) < len(self.state_sources):
            self.logger.debug("Waiting for all state updates")
            return
        
        # 计算控制动作
        control_actions = self.compute_control_actions(current_time)
        
        # 发布控制动作
        self._publish_control_actions(control_actions)

    def compute_control_actions(self, current_time: float) -> Dict[str, Any]:
        """计算控制动作"""
        import time
        start_time = time.time()
        
        try:
            self.metrics["optimization_calls"] += 1
            
            # 获取当前状态
            current_states = np.array([
                self.latest_states.get(key, 0.0) for key in self.state_sources.keys()
            ])
            
            # 设置优化初值
            num_states = len(current_states)
            initial_guess = np.tile(self.target_levels[:num_states], self.prediction_horizon)
            
            # 设置边界约束
            bounds = self.level_bounds * self.prediction_horizon if self.level_bounds else None
            
            # 执行优化
            result = minimize(
                self._objective_function,
                initial_guess,
                args=(current_states, self.latest_forecast, self.target_levels[:num_states]),
                method='SLSQP',
                bounds=bounds
            )
            
            # 处理优化结果
            control_actions = {}
            if result.success:
                self.metrics["successful_optimizations"] += 1
                optimal_sequence = result.x.reshape((self.prediction_horizon, num_states))
                first_setpoints = optimal_sequence[0]
                
                # 创建控制动作字典
                for i, (target_id, topic) in enumerate(self.command_topics.items()):
                    if i < len(first_setpoints):
                        control_actions[target_id] = {
                            "topic": topic,
                            "setpoint": float(first_setpoints[i]),
                            "timestamp": current_time
                        }
                
                # 更新指标
                self.metrics["average_cost"] = float(result.fun)
                
            else:
                self.logger.warning(f"MPC optimization failed: {result.message}")
                # 使用目标值作为后备
                for i, (target_id, topic) in enumerate(self.command_topics.items()):
                    if i < len(self.target_levels):
                        control_actions[target_id] = {
                            "topic": topic,
                            "setpoint": float(self.target_levels[i]),
                            "timestamp": current_time
                        }
            
            self.metrics["last_optimization_time"] = time.time() - start_time
            return control_actions
            
        except Exception as e:
            self.logger.error(f"Error in MPC computation: {e}")
            return {}

    def get_control_targets(self) -> List[str]:
        """获取控制目标列表"""
        return self.control_targets

    def _handle_state_message(self, message: Dict[str, Any], state_name: str):
        """处理状态消息"""
        value = message.get('value', message.get('water_level', 0.0))
        self.latest_states[state_name] = float(value)
        self.logger.debug(f"Updated state '{state_name}': {value}")

    def _handle_forecast_message(self, message: Dict[str, Any]):
        """处理预测消息"""
        forecast = message.get('inflow_forecast', message.get('forecast', []))
        if isinstance(forecast, list) and len(forecast) >= self.prediction_horizon:
            self.latest_forecast = forecast[:self.prediction_horizon]
        else:
            # 使用默认值或扩展现有预测
            self.latest_forecast = [0.0] * self.prediction_horizon
        
        self.logger.debug(f"Updated forecast: {self.latest_forecast[:3]}...")

    def _publish_control_actions(self, control_actions: Dict[str, Any]):
        """发布控制动作"""
        for target_id, action in control_actions.items():
            topic = action["topic"]
            message = {
                "value": action["setpoint"],
                "timestamp": action["timestamp"],
                "sender": self.agent_id,
                "target": target_id
            }
            
            self.message_bus.publish(topic, message, sender_id=self.agent_id)
            self.logger.debug(f"Published setpoint {action['setpoint']:.3f} to '{topic}'")

    def _objective_function(self, setpoint_sequence: np.ndarray, 
                          initial_states: np.ndarray, forecast: List[float],
                          target_levels: np.ndarray) -> float:
        """MPC目标函数"""
        try:
            cost = 0.0
            num_states = len(initial_states)
            setpoints = setpoint_sequence.reshape((self.prediction_horizon, num_states))
            predicted_states = initial_states.copy()
            
            for k in range(self.prediction_horizon):
                # 简化的系统动态模型
                # 假设PID控制器响应：opening = Kp * (setpoint - current_level)
                errors = setpoints[k] - predicted_states
                openings = np.clip(self.mpc_pid_model_kp * errors, 0, 1)
                
                # 水位变化计算（简化模型）
                inflow = forecast[k] if k < len(forecast) else 0.0
                
                # 上游渠道
                outflow_upstream = 0.0
                if len(predicted_states) >= 1:
                    outflow_upstream = self.outflow_coeff * openings[0] * np.sqrt(
                        2 * 9.81 * max(predicted_states[0], 0.01)
                    )
                    level_change = (inflow - outflow_upstream) * self.time_step / self.canal_areas[0]
                    predicted_states[0] += level_change
                
                # 下游渠道
                if len(predicted_states) >= 2:
                    inflow_downstream = outflow_upstream
                    outflow_downstream = self.outflow_coeff * openings[1] * np.sqrt(
                        2 * 9.81 * max(predicted_states[1], 0.01)
                    )
                    level_change = (inflow_downstream - outflow_downstream) * self.time_step / self.canal_areas[1]
                    predicted_states[1] += level_change
                
                # 目标函数项
                # 1. 水位跟踪误差
                tracking_error = np.sum((predicted_states - target_levels) ** 2)
                cost += self.q_weight * tracking_error
                
                # 2. 控制变化惩罚
                if k > 0:
                    control_change = np.sum((setpoints[k] - setpoints[k-1]) ** 2)
                    cost += self.r_weight * control_change
                
                # 3. 洪水约束惩罚
                for i in range(len(predicted_states)):
                    if i < len(self.flood_thresholds) and predicted_states[i] > self.flood_thresholds[i]:
                        cost += 1e6 * (predicted_states[i] - self.flood_thresholds[i])
                
                # 4. 负水位惩罚
                for level in predicted_states:
                    if level < 0:
                        cost += 1e6 * (-level)
            
            return cost
            
        except Exception as e:
            self.logger.error(f"Error in objective function: {e}")
            return 1e9  # 返回一个很大的值表示失败