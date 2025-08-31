from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import uuid
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field

# 导入核心模型
from core_lib.models.api_models import SimulationRequest

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/simulations", tags=["simulation"])

# 仿真会话状态枚举
class SimulationStatus(str):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"

# 仿真会话模型
class SimulationSession(BaseModel):
    session_id: str = Field(..., description="会话唯一标识符")
    status: str = Field(default=SimulationStatus.CREATED, description="仿真状态")
    config: Optional[SimulationRequest] = Field(None, description="仿真配置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="启动时间")
    stopped_at: Optional[datetime] = Field(None, description="停止时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    progress: float = Field(default=0.0, description="仿真进度 (0-100)")
    current_time: float = Field(default=0.0, description="当前仿真时间")
    total_time: float = Field(default=0.0, description="总仿真时间")
    step_count: int = Field(default=0, description="已执行步数")
    performance_metrics: Dict = Field(default_factory=dict, description="性能指标")

# 仿真创建请求
class CreateSimulationRequest(BaseModel):
    config: SimulationRequest = Field(..., description="仿真配置")
    name: Optional[str] = Field(None, description="仿真名称")
    description: Optional[str] = Field(None, description="仿真描述")
    auto_start: bool = Field(default=False, description="是否自动启动")

# 仿真控制请求
class SimulationControlRequest(BaseModel):
    action: str = Field(..., description="控制动作: start, pause, resume, stop, reset")
    parameters: Optional[Dict] = Field(default_factory=dict, description="控制参数")

# 仿真状态响应
class SimulationStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: float
    current_time: float
    total_time: float
    step_count: int
    performance_metrics: Dict
    error_message: Optional[str] = None

# 全局会话存储
simulation_sessions: Dict[str, SimulationSession] = {}
simulation_tasks: Dict[str, asyncio.Task] = {}

# 仿真执行锁
simulation_locks: Dict[str, asyncio.Lock] = {}

@router.post("/", response_model=SimulationSession)
async def create_simulation(request: CreateSimulationRequest):
    """
    创建新的仿真会话
    """
    try:
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 验证配置
        if not request.config.components:
            raise HTTPException(status_code=400, detail="仿真配置中必须包含至少一个组件")
        
        # 创建会话
        session = SimulationSession(
            session_id=session_id,
            config=request.config,
            total_time=getattr(request.config, 'total_time', 3600.0)  # 默认1小时
        )
        
        # 存储会话
        simulation_sessions[session_id] = session
        simulation_locks[session_id] = asyncio.Lock()
        
        logger.info(f"Created simulation session: {session_id}")
        
        # 如果设置了自动启动
        if request.auto_start:
            await start_simulation(session_id)
        
        return session
        
    except Exception as e:
        logger.error(f"Failed to create simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建仿真失败: {str(e)}")

@router.get("/", response_model=List[SimulationSession])
async def list_simulations():
    """
    获取所有仿真会话列表
    """
    return list(simulation_sessions.values())

@router.get("/{session_id}", response_model=SimulationSession)
async def get_simulation(session_id: str):
    """
    获取指定仿真会话信息
    """
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    return simulation_sessions[session_id]

@router.post("/{session_id}/control")
async def control_simulation(session_id: str, request: SimulationControlRequest):
    """
    控制仿真执行
    """
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    session = simulation_sessions[session_id]
    
    try:
        if request.action == "start":
            await start_simulation(session_id)
        elif request.action == "pause":
            await pause_simulation(session_id)
        elif request.action == "resume":
            await resume_simulation(session_id)
        elif request.action == "stop":
            await stop_simulation(session_id)
        elif request.action == "reset":
            await reset_simulation(session_id)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的控制动作: {request.action}")
        
        return {"message": f"仿真控制操作 '{request.action}' 执行成功", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Simulation control failed: {str(e)}")
        session.status = SimulationStatus.ERROR
        session.error_message = str(e)
        raise HTTPException(status_code=500, detail=f"仿真控制失败: {str(e)}")

@router.get("/{session_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(session_id: str):
    """
    获取仿真状态
    """
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    session = simulation_sessions[session_id]
    
    return SimulationStatusResponse(
        session_id=session_id,
        status=session.status,
        progress=session.progress,
        current_time=session.current_time,
        total_time=session.total_time,
        step_count=session.step_count,
        performance_metrics=session.performance_metrics,
        error_message=session.error_message
    )

@router.delete("/{session_id}")
async def delete_simulation(session_id: str):
    """
    删除仿真会话
    """
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    # 停止仿真（如果正在运行）
    if session_id in simulation_tasks:
        await stop_simulation(session_id)
    
    # 删除会话数据
    del simulation_sessions[session_id]
    if session_id in simulation_locks:
        del simulation_locks[session_id]
    
    logger.info(f"Deleted simulation session: {session_id}")
    
    return {"message": "仿真会话已删除", "session_id": session_id}

# 仿真控制函数
async def start_simulation(session_id: str):
    """
    启动仿真
    """
    session = simulation_sessions[session_id]
    
    if session.status == SimulationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="仿真已在运行中")
    
    async with simulation_locks[session_id]:
        session.status = SimulationStatus.RUNNING
        session.started_at = datetime.now()
        session.error_message = None
        
        # 创建仿真任务
        task = asyncio.create_task(run_simulation_loop(session_id))
        simulation_tasks[session_id] = task
        
        logger.info(f"Started simulation: {session_id}")

async def pause_simulation(session_id: str):
    """
    暂停仿真
    """
    session = simulation_sessions[session_id]
    
    if session.status != SimulationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="仿真未在运行中")
    
    async with simulation_locks[session_id]:
        session.status = SimulationStatus.PAUSED
        logger.info(f"Paused simulation: {session_id}")

async def resume_simulation(session_id: str):
    """
    恢复仿真
    """
    session = simulation_sessions[session_id]
    
    if session.status != SimulationStatus.PAUSED:
        raise HTTPException(status_code=400, detail="仿真未处于暂停状态")
    
    async with simulation_locks[session_id]:
        session.status = SimulationStatus.RUNNING
        logger.info(f"Resumed simulation: {session_id}")

async def stop_simulation(session_id: str):
    """
    停止仿真
    """
    session = simulation_sessions[session_id]
    
    async with simulation_locks[session_id]:
        session.status = SimulationStatus.STOPPED
        session.stopped_at = datetime.now()
        
        # 取消仿真任务
        if session_id in simulation_tasks:
            task = simulation_tasks[session_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del simulation_tasks[session_id]
        
        logger.info(f"Stopped simulation: {session_id}")

async def reset_simulation(session_id: str):
    """
    重置仿真
    """
    session = simulation_sessions[session_id]
    
    # 先停止仿真
    if session.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
        await stop_simulation(session_id)
    
    async with simulation_locks[session_id]:
        # 重置状态
        session.status = SimulationStatus.CREATED
        session.progress = 0.0
        session.current_time = 0.0
        session.step_count = 0
        session.started_at = None
        session.stopped_at = None
        session.error_message = None
        session.performance_metrics = {}
        
        logger.info(f"Reset simulation: {session_id}")

# 仿真执行循环
async def run_simulation_loop(session_id: str):
    """
    仿真执行主循环
    """
    session = simulation_sessions[session_id]
    
    try:
        time_step = 0.1  # 时间步长（秒）
        max_steps = int(session.total_time / time_step)
        
        logger.info(f"Starting simulation loop for session {session_id}")
        
        for step in range(max_steps):
            # 检查是否需要暂停或停止
            if session.status == SimulationStatus.PAUSED:
                while session.status == SimulationStatus.PAUSED:
                    await asyncio.sleep(0.1)
                    if session.status == SimulationStatus.STOPPED:
                        return
            
            if session.status == SimulationStatus.STOPPED:
                return
            
            # 执行仿真步骤
            await execute_simulation_step(session_id, step, time_step)
            
            # 更新进度
            session.current_time = step * time_step
            session.progress = (step / max_steps) * 100
            session.step_count = step + 1
            
            # 更新性能指标
            session.performance_metrics.update({
                "fps": 1.0 / time_step,
                "memory_usage": 50.0 + (step % 100),  # 模拟内存使用
                "cpu_usage": 20.0 + (step % 50),      # 模拟CPU使用
                "last_updated": datetime.now().isoformat()
            })
            
            # 控制执行频率
            await asyncio.sleep(time_step)
        
        # 仿真完成
        session.status = SimulationStatus.COMPLETED
        session.progress = 100.0
        session.stopped_at = datetime.now()
        
        logger.info(f"Simulation completed: {session_id}")
        
    except asyncio.CancelledError:
        logger.info(f"Simulation cancelled: {session_id}")
        raise
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        session.status = SimulationStatus.ERROR
        session.error_message = str(e)
        session.stopped_at = datetime.now()
        raise

async def execute_simulation_step(session_id: str, step: int, time_step: float):
    """
    执行单个仿真步骤
    """
    session = simulation_sessions[session_id]
    
    # 这里应该调用实际的仿真引擎
    # 目前使用模拟数据
    
    # 模拟组件数据更新
    if session.config and session.config.components:
        for component_type, components in session.config.components.dict().items():
            if components:
                for component in components:
                    # 模拟数据变化
                    component_id = getattr(component, 'id', f"{component_type}_{step}")
                    
                    # 这里可以添加实际的物理计算
                    # 目前使用简单的模拟数据
                    pass
    
    # 模拟计算延迟
    await asyncio.sleep(0.001)

# 清理函数
async def cleanup_simulation_resources():
    """
    清理仿真资源
    """
    logger.info("Cleaning up simulation resources...")
    
    # 停止所有运行中的仿真
    for session_id in list(simulation_tasks.keys()):
        try:
            await stop_simulation(session_id)
        except Exception as e:
            logger.error(f"Error stopping simulation {session_id}: {e}")
    
    # 清理数据
    simulation_sessions.clear()
    simulation_tasks.clear()
    simulation_locks.clear()
    
    logger.info("Simulation resources cleaned up")

# 获取仿真统计信息
@router.get("/stats/overview")
async def get_simulation_stats():
    """
    获取仿真统计概览
    """
    total_sessions = len(simulation_sessions)
    running_sessions = len([s for s in simulation_sessions.values() if s.status == SimulationStatus.RUNNING])
    paused_sessions = len([s for s in simulation_sessions.values() if s.status == SimulationStatus.PAUSED])
    completed_sessions = len([s for s in simulation_sessions.values() if s.status == SimulationStatus.COMPLETED])
    error_sessions = len([s for s in simulation_sessions.values() if s.status == SimulationStatus.ERROR])
    
    return {
        "total_sessions": total_sessions,
        "running_sessions": running_sessions,
        "paused_sessions": paused_sessions,
        "completed_sessions": completed_sessions,
        "error_sessions": error_sessions,
        "active_tasks": len(simulation_tasks)
    }