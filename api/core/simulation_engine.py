"""仿真引擎服务

集成 core_lib 的 SimulationHarness 与 API 层面的仿真管理
"""

import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.io.yaml_loader import SimulationBuilder
from core_lib.central_coordination.collaboration.message_bus import MessageBus

logger = logging.getLogger(__name__)

@dataclass
class SimulationEngineConfig:
    """仿真引擎配置"""
    scenario_path: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 3600.0  # 1 hour
    time_step: float = 1.0
    real_time_factor: float = 1.0
    max_steps: Optional[int] = None
    enable_logging: bool = True
    log_level: str = "INFO"
    auto_save_interval: int = 100  # steps

class SimulationEngine:
    """仿真引擎
    
    负责管理和执行仿真任务，集成 core_lib 的 SimulationHarness
    """
    
    def __init__(self, session_id: str, config: SimulationEngineConfig):
        self.session_id = session_id
        self.config = config
        
        # 仿真状态
        self.is_running = False
        self.is_paused = False
        self.current_time = config.start_time
        self.step_count = 0
        self.start_timestamp = None
        self.end_timestamp = None
        self.error_message = None
        
        # 核心组件
        self.harness: Optional[SimulationHarness] = None
        self.message_bus: Optional[MessageBus] = None
        self.builder: Optional[SimulationBuilder] = None
        
        # 异步控制
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        
        # 性能监控
        self.performance_metrics = {
            "fps": 0.0,
            "avg_step_time": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
        # 历史数据
        self.history: List[Dict[str, Any]] = []
        
        logger.info(f"SimulationEngine created for session {session_id}")
    
    async def initialize(self, scenario_config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化仿真引擎
        
        Args:
            scenario_config: 场景配置，如果提供则使用内存配置，否则从文件加载
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            if scenario_config:
                # 使用内存配置创建仿真
                await self._initialize_from_config(scenario_config)
            elif self.config.scenario_path:
                # 从文件加载场景配置
                await self._initialize_from_files()
            else:
                # 创建空的仿真环境
                await self._initialize_empty()
            
            logger.info(f"SimulationEngine initialized for session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize simulation engine: {e}")
            self.error_message = str(e)
            return False
    
    async def _initialize_from_config(self, config: Dict[str, Any]):
        """从内存配置初始化"""
        # 创建仿真配置
        sim_config = {
            'start_time': self.config.start_time,
            'end_time': self.config.end_time,
            'dt': self.config.time_step
        }
        
        # 创建 SimulationHarness
        self.harness = SimulationHarness(sim_config)
        self.message_bus = MessageBus()
        
        # TODO: 根据配置添加组件和智能体
        # 这里需要实现从 API 配置到 core_lib 组件的转换
        
        # 构建仿真
        self.harness.build()
    
    async def _initialize_from_files(self):
        """从文件加载场景配置"""
        scenario_path = Path(self.config.scenario_path)
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario path not found: {scenario_path}")
        
        # 使用 SimulationBuilder 加载场景
        self.builder = SimulationBuilder(str(scenario_path))
        self.harness, self.message_bus = self.builder.load()
        
        # 更新配置
        if self.builder.config:
            sim_config = self.builder.config.get('simulation', {})
            self.config.start_time = sim_config.get('start_time', self.config.start_time)
            self.config.end_time = sim_config.get('end_time', self.config.end_time)
            self.config.time_step = sim_config.get('time_step', self.config.time_step)
    
    async def _initialize_empty(self):
        """创建空的仿真环境"""
        sim_config = {
            'start_time': self.config.start_time,
            'end_time': self.config.end_time,
            'dt': self.config.time_step
        }
        
        self.harness = SimulationHarness(sim_config)
        self.message_bus = MessageBus()
        self.harness.build()
    
    async def start(self) -> bool:
        """启动仿真"""
        if self.is_running:
            logger.warning(f"Simulation {self.session_id} is already running")
            return False
        
        if not self.harness:
            logger.error(f"Simulation {self.session_id} not initialized")
            return False
        
        try:
            self.is_running = True
            self.is_paused = False
            self.start_timestamp = datetime.now()
            self._stop_event.clear()
            self._pause_event.clear()
            
            # 启动仿真任务
            self._task = asyncio.create_task(self._run_simulation_loop())
            
            logger.info(f"Simulation {self.session_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start simulation {self.session_id}: {e}")
            self.error_message = str(e)
            self.is_running = False
            return False
    
    async def pause(self) -> bool:
        """暂停仿真"""
        if not self.is_running or self.is_paused:
            return False
        
        self.is_paused = True
        self._pause_event.set()
        
        if self.harness:
            self.harness.pause()
        
        logger.info(f"Simulation {self.session_id} paused")
        return True
    
    async def resume(self) -> bool:
        """恢复仿真"""
        if not self.is_running or not self.is_paused:
            return False
        
        self.is_paused = False
        self._pause_event.clear()
        
        if self.harness:
            self.harness.resume()
        
        logger.info(f"Simulation {self.session_id} resumed")
        return True
    
    async def stop(self) -> bool:
        """停止仿真"""
        if not self.is_running:
            return False
        
        self.is_running = False
        self._stop_event.set()
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.end_timestamp = datetime.now()
        logger.info(f"Simulation {self.session_id} stopped")
        return True
    
    async def reset(self) -> bool:
        """重置仿真"""
        await self.stop()
        
        self.current_time = self.config.start_time
        self.step_count = 0
        self.start_timestamp = None
        self.end_timestamp = None
        self.error_message = None
        self.history.clear()
        
        # 重新初始化
        if self.config.scenario_path:
            await self._initialize_from_files()
        else:
            await self._initialize_empty()
        
        logger.info(f"Simulation {self.session_id} reset")
        return True
    
    async def step(self) -> bool:
        """执行单步仿真"""
        if not self.harness or self.is_running:
            return False
        
        try:
            # 执行单步
            self.harness.step()
            self.current_time = self.harness.t
            self.step_count += 1
            
            # 记录历史
            self._record_step()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in simulation step: {e}")
            self.error_message = str(e)
            return False
    
    async def _run_simulation_loop(self):
        """仿真主循环"""
        try:
            step_start_time = asyncio.get_event_loop().time()
            
            while (self.harness.is_running and 
                   self.current_time < self.config.end_time and
                   not self._stop_event.is_set()):
                
                # 检查暂停
                if self._pause_event.is_set():
                    await asyncio.sleep(0.1)
                    continue
                
                # 检查最大步数限制
                if (self.config.max_steps and 
                    self.step_count >= self.config.max_steps):
                    break
                
                # 执行仿真步骤
                loop_start = asyncio.get_event_loop().time()
                
                self.harness.step()
                self.current_time = self.harness.t
                self.step_count += 1
                
                # 记录历史
                self._record_step()
                
                # 更新性能指标
                loop_time = asyncio.get_event_loop().time() - loop_start
                self._update_performance_metrics(loop_time)
                
                # 控制执行频率（实时因子）
                if self.config.real_time_factor > 0:
                    target_sleep = self.config.time_step / self.config.real_time_factor
                    actual_sleep = max(0, target_sleep - loop_time)
                    if actual_sleep > 0:
                        await asyncio.sleep(actual_sleep)
            
            # 仿真完成
            self.is_running = False
            self.end_timestamp = datetime.now()
            
            if self.current_time >= self.config.end_time:
                logger.info(f"Simulation {self.session_id} completed successfully")
            else:
                logger.info(f"Simulation {self.session_id} stopped early")
                
        except asyncio.CancelledError:
            logger.info(f"Simulation {self.session_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Simulation {self.session_id} error: {e}")
            self.error_message = str(e)
            self.is_running = False
            raise
    
    def _record_step(self):
        """记录当前步骤的状态"""
        if not self.harness:
            return
        
        # 从 harness 获取历史记录
        if self.harness.history:
            latest_history = self.harness.history[-1]
            self.history.append({
                'step': self.step_count,
                'time': self.current_time,
                'timestamp': datetime.now().isoformat(),
                'data': latest_history
            })
        
        # 自动保存（可选）
        if (self.config.auto_save_interval > 0 and 
            self.step_count % self.config.auto_save_interval == 0):
            self._auto_save()
    
    def _update_performance_metrics(self, step_time: float):
        """更新性能指标"""
        self.performance_metrics.update({
            "fps": 1.0 / max(step_time, 0.001),
            "avg_step_time": step_time * 1000,  # ms
            "memory_usage": 50.0 + (self.step_count % 100),  # 模拟值
            "cpu_usage": 20.0 + (self.step_count % 50),      # 模拟值
            "last_updated": datetime.now().isoformat()
        })
    
    def _auto_save(self):
        """自动保存（占位符）"""
        # TODO: 实现自动保存功能
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        progress = 0.0
        if self.config.end_time > self.config.start_time:
            progress = min(100.0, 
                         (self.current_time - self.config.start_time) / 
                         (self.config.end_time - self.config.start_time) * 100)
        
        status = "idle"
        if self.is_running:
            status = "paused" if self.is_paused else "running"
        elif self.error_message:
            status = "error"
        elif self.current_time >= self.config.end_time:
            status = "completed"
        
        return {
            "session_id": self.session_id,
            "status": status,
            "progress": progress,
            "current_time": self.current_time,
            "total_time": self.config.end_time,
            "step_count": self.step_count,
            "performance_metrics": self.performance_metrics,
            "error_message": self.error_message,
            "start_timestamp": self.start_timestamp.isoformat() if self.start_timestamp else None,
            "end_timestamp": self.end_timestamp.isoformat() if self.end_timestamp else None
        }
    
    def get_component_states(self) -> Dict[str, Any]:
        """获取组件状态"""
        if not self.harness or not self.harness.components:
            return {}
        
        states = {}
        for comp_id, component in self.harness.components.items():
            try:
                states[comp_id] = component.get_state()
            except Exception as e:
                logger.warning(f"Failed to get state for component {comp_id}: {e}")
                states[comp_id] = {"error": str(e)}
        
        return states
    
    def get_agent_states(self) -> Dict[str, Any]:
        """获取智能体状态"""
        if not self.harness or not self.harness.agents:
            return {}
        
        states = {}
        for agent in self.harness.agents:
            try:
                agent_id = getattr(agent, 'agent_id', str(agent))
                if hasattr(agent, 'get_state'):
                    states[agent_id] = agent.get_state()
                else:
                    states[agent_id] = {"status": "active"}
            except Exception as e:
                logger.warning(f"Failed to get state for agent {agent}: {e}")
                states[str(agent)] = {"error": str(e)}
        
        return states
    
    def cleanup(self):
        """清理资源"""
        if self._task and not self._task.done():
            self._task.cancel()
        
        self.harness = None
        self.message_bus = None
        self.builder = None
        self.history.clear()
        
        logger.info(f"SimulationEngine {self.session_id} cleaned up")