"""
中央协调Agent实现

负责任务调度、资源分配、系统健康监控
分离协调职责与控制职责
"""
import time
import threading
import queue
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from core_lib.core.new_interfaces import CentralCoordinatorAgent, Config, Message, State
from core_lib.core.event_bus import get_global_event_bus

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    priority: TaskPriority
    target_agent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_time: float = field(default_factory=time.time)
    assigned_time: Optional[float] = None
    completed_time: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_type: str
    status: str
    load: float = 0.0
    capabilities: Set[str] = field(default_factory=set)
    last_heartbeat: float = field(default_factory=time.time)
    current_tasks: List[str] = field(default_factory=list)

class CentralCoordinatorAgentImpl(CentralCoordinatorAgent):
    """
    中央协调Agent实现
    
    职责：
    1. 任务调度和分发
    2. 负载均衡
    3. 系统健康监控
    4. Agent注册和发现
    5. 故障处理和恢复
    """
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        
        # 任务管理
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.task_counter = 0
        
        # Agent管理
        self.registered_agents: Dict[str, AgentInfo] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        
        # 配置
        self.task_queue_size = config.get('task_queue_size', 100) if config else 100
        self.load_balancing = config.get('load_balancing', True) if config else True
        self.health_check_interval = config.get('health_check_interval', 10.0) if config else 10.0
        self.heartbeat_timeout = config.get('heartbeat_timeout', 30.0) if config else 30.0
        
        # 工作线程
        self._coordinator_thread: Optional[threading.Thread] = None
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 统计信息
        self.coordination_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_agents': 0,
            'system_load': 0.0
        }
        
        print(f"[CentralCoordinator] Initialized coordinator: {agent_id}")
    
    def configure(self, config: Config) -> bool:
        """配置协调器"""
        try:
            self.config.update(config)
            self.task_queue_size = config.get('task_queue_size', self.task_queue_size)
            self.load_balancing = config.get('load_balancing', self.load_balancing)
            self.health_check_interval = config.get('health_check_interval', self.health_check_interval)
            
            self._log("info", "Coordinator configuration updated")
            return True
        except Exception as e:
            self._log("error", f"Configuration failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动协调器"""
        try:
            # 设置事件总线
            if not self.event_bus:
                self.event_bus = get_global_event_bus()
            
            # 订阅系统事件
            self._setup_subscriptions()
            
            # 启动工作线程
            self._start_worker_threads()
            
            self.status = self.status.__class__.RUNNING
            self._log("info", "Central coordinator started")
            return True
        except Exception as e:
            self._log("error", f"Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止协调器"""
        try:
            self._stop_event.set()
            
            # 等待工作线程结束
            if self._coordinator_thread and self._coordinator_thread.is_alive():
                self._coordinator_thread.join(timeout=5.0)
            
            if self._health_monitor_thread and self._health_monitor_thread.is_alive():
                self._health_monitor_thread.join(timeout=5.0)
            
            self.status = self.status.__class__.STOPPED
            self._log("info", "Central coordinator stopped")
            return True
        except Exception as e:
            self._log("error", f"Stop failed: {e}")
            return False
    
    def step(self, current_time: float) -> bool:
        """执行一个时间步"""
        try:
            # 更新系统统计
            self._update_system_stats()
            
            # 处理待处理任务
            self._process_pending_tasks()
            
            return True
        except Exception as e:
            self._log("error", f"Step execution failed: {e}")
            return False
    
    def coordinate_agents(self, agent_states: Dict[str, State]) -> Dict[str, Message]:
        """协调管理的Agent"""
        coordination_commands = {}
        
        try:
            # 更新Agent状态
            for agent_id, state in agent_states.items():
                self._update_agent_state(agent_id, state)
            
            # 负载均衡
            if self.load_balancing:
                balance_commands = self._perform_load_balancing()
                coordination_commands.update(balance_commands)
            
            # 健康检查和故障处理
            health_commands = self._handle_unhealthy_agents()
            coordination_commands.update(health_commands)
            
            return coordination_commands
            
        except Exception as e:
            self._log("error", f"Agent coordination failed: {e}")
            return {}
    
    def dispatch_tasks(self, tasks: List[Message]) -> Dict[str, Message]:
        """任务调度"""
        dispatch_results = {}
        
        try:
            for task_msg in tasks:
                task = self._create_task_from_message(task_msg)
                if task:
                    # 添加到任务队列
                    priority_value = task.priority.value
                    self.task_queue.put((priority_value, task.created_time, task))
                    self.coordination_stats['total_tasks'] += 1
                    
                    dispatch_results[task.task_id] = {
                        'status': 'queued',
                        'task_id': task.task_id,
                        'queue_position': self.task_queue.qsize()
                    }
                    
                    self._log("info", f"Task {task.task_id} queued with priority {task.priority.name}")
            
            return dispatch_results
            
        except Exception as e:
            self._log("error", f"Task dispatch failed: {e}")
            return {}
    
    def monitor_system_health(self) -> State:
        """系统健康监控"""
        try:
            current_time = time.time()
            healthy_agents = 0
            total_load = 0.0
            
            for agent_info in self.registered_agents.values():
                if current_time - agent_info.last_heartbeat < self.heartbeat_timeout:
                    healthy_agents += 1
                    total_load += agent_info.load
            
            system_health = {
                'timestamp': current_time,
                'total_agents': len(self.registered_agents),
                'healthy_agents': healthy_agents,
                'unhealthy_agents': len(self.registered_agents) - healthy_agents,
                'average_load': total_load / max(healthy_agents, 1),
                'task_queue_size': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'system_status': 'healthy' if healthy_agents > 0 else 'critical'
            }
            
            self.coordination_stats['active_agents'] = healthy_agents
            self.coordination_stats['system_load'] = system_health['average_load']
            
            return system_health
            
        except Exception as e:
            self._log("error", f"Health monitoring failed: {e}")
            return {'system_status': 'error', 'error': str(e)}
    
    def register_agent(self, agent_id: str, agent_type: str, capabilities: Set[str]):
        """注册Agent"""
        try:
            agent_info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                status='active',
                capabilities=capabilities
            )
            
            self.registered_agents[agent_id] = agent_info
            self.agent_capabilities[agent_id] = capabilities
            
            self._log("info", f"Agent registered: {agent_id} ({agent_type})")
            
            # 发布Agent注册事件
            if self.event_bus:
                self.event_bus.publish('system.agent.registered', {
                    'agent_id': agent_id,
                    'agent_type': agent_type,
                    'capabilities': list(capabilities)
                })
            
        except Exception as e:
            self._log("error", f"Agent registration failed: {e}")
    
    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        try:
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                del self.agent_capabilities[agent_id]
                
                self._log("info", f"Agent unregistered: {agent_id}")
                
                # 发布Agent注销事件
                if self.event_bus:
                    self.event_bus.publish('system.agent.unregistered', {
                        'agent_id': agent_id
                    })
            
        except Exception as e:
            self._log("error", f"Agent unregistration failed: {e}")
    
    def _setup_subscriptions(self):
        """设置事件订阅"""
        if self.event_bus:
            # 订阅Agent心跳
            self.event_bus.subscribe('system.heartbeat.*', self._handle_heartbeat)
            
            # 订阅任务事件
            self.event_bus.subscribe('task.completed', self._handle_task_completed)
            self.event_bus.subscribe('task.failed', self._handle_task_failed)
            
            # 订阅Agent注册事件
            self.event_bus.subscribe('system.agent.register', self._handle_agent_registration)
            
            self._log("info", "Event subscriptions set up")
    
    def _start_worker_threads(self):
        """启动工作线程"""
        # 任务协调线程
        self._coordinator_thread = threading.Thread(
            target=self._coordinator_worker,
            daemon=True
        )
        self._coordinator_thread.start()
        
        # 健康监控线程
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_worker,
            daemon=True
        )
        self._health_monitor_thread.start()
        
        self._log("info", "Worker threads started")
    
    def _coordinator_worker(self):
        """协调器工作线程"""
        while not self._stop_event.is_set():
            try:
                # 处理任务队列
                self._process_task_queue()
                
                # 短暂休眠
                time.sleep(0.1)
                
            except Exception as e:
                self._log("error", f"Coordinator worker error: {e}")
    
    def _health_monitor_worker(self):
        """健康监控工作线程"""
        while not self._stop_event.is_set():
            try:
                # 执行健康检查
                health_state = self.monitor_system_health()
                
                # 发布健康状态
                if self.event_bus:
                    self.event_bus.publish('system.health', health_state)
                
                # 等待下一个检查周期
                self._stop_event.wait(self.health_check_interval)
                
            except Exception as e:
                self._log("error", f"Health monitor worker error: {e}")
    
    def _process_task_queue(self):
        """处理任务队列"""
        try:
            # 获取待处理任务
            if not self.task_queue.empty():
                _, _, task = self.task_queue.get_nowait()
                
                # 分配任务
                assigned_agent = self._assign_task(task)
                if assigned_agent:
                    task.target_agent = assigned_agent
                    task.status = TaskStatus.ASSIGNED
                    task.assigned_time = time.time()
                    
                    self.active_tasks[task.task_id] = task
                    
                    # 发送任务给Agent
                    self._send_task_to_agent(task, assigned_agent)
                    
                    self._log("info", f"Task {task.task_id} assigned to {assigned_agent}")
                else:
                    # 无可用Agent，重新排队
                    priority_value = task.priority.value
                    self.task_queue.put((priority_value, task.created_time, task))
        
        except queue.Empty:
            pass
        except Exception as e:
            self._log("error", f"Task queue processing error: {e}")
    
    def _assign_task(self, task: Task) -> Optional[str]:
        """分配任务给最合适的Agent"""
        try:
            suitable_agents = []
            
            # 查找具有所需能力的Agent
            required_capability = task.task_type
            for agent_id, capabilities in self.agent_capabilities.items():
                if required_capability in capabilities:
                    agent_info = self.registered_agents.get(agent_id)
                    if agent_info and agent_info.status == 'active':
                        suitable_agents.append((agent_id, agent_info.load))
            
            if not suitable_agents:
                return None
            
            # 选择负载最低的Agent
            if self.load_balancing:
                suitable_agents.sort(key=lambda x: x[1])
            
            return suitable_agents[0][0]
            
        except Exception as e:
            self._log("error", f"Task assignment failed: {e}")
            return None
    
    def _send_task_to_agent(self, task: Task, agent_id: str):
        """发送任务给Agent"""
        try:
            task_message = {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'parameters': task.parameters,
                'priority': task.priority.name,
                'assigned_time': task.assigned_time
            }
            
            if self.event_bus:
                self.event_bus.publish(f'task.assign.{agent_id}', task_message)
            
        except Exception as e:
            self._log("error", f"Task sending failed: {e}")
    
    def _create_task_from_message(self, message: Message) -> Optional[Task]:
        """从消息创建任务"""
        try:
            self.task_counter += 1
            task_id = message.get('task_id', f'task_{self.task_counter}')
            
            priority_str = message.get('priority', 'NORMAL')
            priority = TaskPriority[priority_str.upper()]
            
            task = Task(
                task_id=task_id,
                task_type=message.get('task_type', 'unknown'),
                priority=priority,
                parameters=message.get('parameters', {})
            )
            
            return task
            
        except Exception as e:
            self._log("error", f"Task creation failed: {e}")
            return None
    
    def _handle_heartbeat(self, message: Message):
        """处理心跳消息"""
        try:
            agent_id = message.get('agent_id')
            if agent_id and agent_id in self.registered_agents:
                agent_info = self.registered_agents[agent_id]
                agent_info.last_heartbeat = time.time()
                agent_info.load = message.get('load', 0.0)
                agent_info.status = message.get('status', 'active')
                
        except Exception as e:
            self._log("error", f"Heartbeat handling failed: {e}")
    
    def _handle_task_completed(self, message: Message):
        """处理任务完成消息"""
        try:
            task_id = message.get('task_id')
            if task_id and task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_time = time.time()
                
                # 移动到完成任务列表
                self.completed_tasks[task_id] = task
                del self.active_tasks[task_id]
                
                self.coordination_stats['completed_tasks'] += 1
                
                self._log("info", f"Task {task_id} completed")
                
        except Exception as e:
            self._log("error", f"Task completion handling failed: {e}")
    
    def _handle_task_failed(self, message: Message):
        """处理任务失败消息"""
        try:
            task_id = message.get('task_id')
            if task_id and task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.retry_count += 1
                
                if task.retry_count < task.max_retries:
                    # 重新排队
                    task.status = TaskStatus.PENDING
                    priority_value = task.priority.value
                    self.task_queue.put((priority_value, task.created_time, task))
                    del self.active_tasks[task_id]
                    
                    self._log("info", f"Task {task_id} requeued for retry ({task.retry_count}/{task.max_retries})")
                else:
                    # 标记为失败
                    task.status = TaskStatus.FAILED
                    self.completed_tasks[task_id] = task
                    del self.active_tasks[task_id]
                    
                    self.coordination_stats['failed_tasks'] += 1
                    
                    self._log("error", f"Task {task_id} failed after {task.max_retries} retries")
                
        except Exception as e:
            self._log("error", f"Task failure handling failed: {e}")
    
    def _handle_agent_registration(self, message: Message):
        """处理Agent注册消息"""
        try:
            agent_id = message.get('agent_id')
            agent_type = message.get('agent_type')
            capabilities = set(message.get('capabilities', []))
            
            if agent_id and agent_type:
                self.register_agent(agent_id, agent_type, capabilities)
                
        except Exception as e:
            self._log("error", f"Agent registration handling failed: {e}")
    
    def _update_agent_state(self, agent_id: str, state: State):
        """更新Agent状态"""
        try:
            if agent_id in self.registered_agents:
                agent_info = self.registered_agents[agent_id]
                agent_info.status = state.get('status', 'unknown')
                agent_info.load = state.get('load', 0.0)
                agent_info.last_heartbeat = time.time()
                
        except Exception as e:
            self._log("error", f"Agent state update failed: {e}")
    
    def _perform_load_balancing(self) -> Dict[str, Message]:
        """执行负载均衡"""
        commands = {}
        
        try:
            # 简单的负载均衡逻辑
            if len(self.registered_agents) < 2:
                return commands
            
            # 计算平均负载
            total_load = sum(agent.load for agent in self.registered_agents.values())
            avg_load = total_load / len(self.registered_agents)
            
            # 找出高负载和低负载的Agent
            high_load_agents = []
            low_load_agents = []
            
            for agent_id, agent_info in self.registered_agents.items():
                if agent_info.load > avg_load * 1.5:
                    high_load_agents.append((agent_id, agent_info.load))
                elif agent_info.load < avg_load * 0.5:
                    low_load_agents.append((agent_id, agent_info.load))
            
            # 生成负载均衡命令
            for agent_id, load in high_load_agents:
                commands[agent_id] = {
                    'command_type': 'reduce_load',
                    'current_load': load,
                    'target_load': avg_load
                }
            
            return commands
            
        except Exception as e:
            self._log("error", f"Load balancing failed: {e}")
            return {}
    
    def _handle_unhealthy_agents(self) -> Dict[str, Message]:
        """处理不健康的Agent"""
        commands = {}
        current_time = time.time()
        
        try:
            for agent_id, agent_info in self.registered_agents.items():
                if current_time - agent_info.last_heartbeat > self.heartbeat_timeout:
                    # Agent可能已失联
                    commands[agent_id] = {
                        'command_type': 'health_check',
                        'last_seen': agent_info.last_heartbeat,
                        'timeout': self.heartbeat_timeout
                    }
                    
                    self._log("warning", f"Agent {agent_id} may be unhealthy")
            
            return commands
            
        except Exception as e:
            self._log("error", f"Unhealthy agent handling failed: {e}")
            return {}
    
    def _update_system_stats(self):
        """更新系统统计"""
        try:
            self.coordination_stats['active_agents'] = len([
                agent for agent in self.registered_agents.values()
                if time.time() - agent.last_heartbeat < self.heartbeat_timeout
            ])
            
        except Exception as e:
            self._log("error", f"System stats update failed: {e}")
    
    def _process_pending_tasks(self):
        """处理待处理任务"""
        # 这个方法在step中调用，用于处理一些周期性的任务管理
        pass
