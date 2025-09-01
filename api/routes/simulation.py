from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import uuid
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 导入核心模型
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core_lib.models.api_models import SimulationRequest
from database.database import get_db
from database.crud import SimulationSessionCRUD, ComponentConfigCRUD, SimulationResultCRUD, SimulationEventCRUD
from database.models import UserDB
from auth import get_current_active_user
from models.simulation_models import (
    SimulationSession,
    CreateSimulationRequest,
    SimulationResponse,
    SimulationStatus,
    SimulationControlRequest,
    SimulationStatistics,
    SimulationResult,
    SimulationEvent,
    ComponentConfig,
    SimulationSnapshot,
    ControlAction
)
from websocket.connection_manager import connection_manager
from core.simulation_engine import SimulationEngine, SimulationEngineConfig

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/simulations", tags=["simulation"])

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
simulation_engines: Dict[str, SimulationEngine] = {}
simulation_tasks: Dict[str, asyncio.Task] = {}

# 仿真执行锁
simulation_locks: Dict[str, asyncio.Lock] = {}

@router.post("/", response_model=SimulationSession)
async def create_simulation(
    request: CreateSimulationRequest,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    创建新的仿真会话
    """
    try:
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 验证配置
        if not request.config.components:
            raise HTTPException(status_code=400, detail="仿真配置中必须包含至少一个组件")
        
        # 准备数据库会话数据
        session_data = {
            "id": session_id,
            "user_id": current_user.id,
            "name": request.name or f"仿真会话_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": request.description,
            "status": SimulationStatus.IDLE,
            "config": request.config.dict() if request.config else {},
            "total_time": getattr(request.config, 'total_time', 3600.0),
            "time_step": 1.0,
            "current_step": 0,
            "simulation_time": 0.0,
            "progress": 0.0,
            "created_at": datetime.utcnow(),
            "metadata": {"auto_start": request.auto_start}
        }
        
        # 创建数据库会话
        db_session = SimulationSessionCRUD.create(db, session_data)
        
        # 创建内存会话对象
        session = SimulationSession(
            session_id=session_id,
            config=request.config,
            total_time=getattr(request.config, 'total_time', 3600.0)
        )
        
        # 创建仿真引擎配置
        engine_config = SimulationEngineConfig(
            start_time=0.0,
            end_time=getattr(request.config, 'total_time', 3600.0),
            time_step=getattr(request.config, 'time_step', 1.0),
            real_time_factor=1.0,
            enable_logging=True
        )
        
        # 创建仿真引擎
        simulation_engine = SimulationEngine(session_id, engine_config)
        
        # 初始化仿真引擎
        scenario_config = None
        if request.config:
            scenario_config = request.config.dict()
        
        init_success = await simulation_engine.initialize(scenario_config)
        if not init_success:
            raise HTTPException(
                status_code=500, 
                detail=f"仿真引擎初始化失败: {simulation_engine.error_message}"
            )
        
        # 存储到内存（用于运行时管理）
        simulation_sessions[session_id] = session
        simulation_engines[session_id] = simulation_engine
        simulation_locks[session_id] = asyncio.Lock()
        
        logger.info(f"Created simulation session: {session_id} for user: {current_user.username}")
        
        # 如果设置了自动启动
        if request.auto_start:
            await start_simulation(session_id, db)
        
        return session
        
    except Exception as e:
        logger.error(f"Failed to create simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建仿真失败: {str(e)}")

@router.get("/", response_model=List[SimulationSession])
async def list_simulations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取当前用户的仿真会话列表
    """
    try:
        # 获取用户的仿真会话
        db_sessions = SimulationSessionCRUD.get_by_user(db, current_user.id, skip, limit)
        
        # 转换为响应模型
        sessions = []
        for db_session in db_sessions:
            # 如果会话在内存中，使用内存数据（包含实时状态）
            if db_session.id in simulation_sessions:
                sessions.append(simulation_sessions[db_session.id])
            else:
                # 否则从数据库数据创建会话对象
                session = SimulationSession(
                    session_id=db_session.id,
                    status=db_session.status,
                    config=db_session.config,
                    created_at=db_session.created_at,
                    started_at=db_session.started_at,
                    stopped_at=db_session.stopped_at,
                    progress=db_session.progress,
                    current_time=db_session.simulation_time,
                    total_time=db_session.total_time,
                    step_count=db_session.current_step
                )
                sessions.append(session)
        
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to list simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真列表失败: {str(e)}")

@router.get("/{session_id}", response_model=SimulationSession)
async def get_simulation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取指定仿真会话信息
    """
    try:
        # 从数据库获取会话
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        # 检查用户权限
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 如果会话在内存中，返回内存数据（包含实时状态）
        if session_id in simulation_sessions:
            return simulation_sessions[session_id]
        
        # 否则从数据库数据创建会话对象
        session = SimulationSession(
            session_id=db_session.id,
            status=db_session.status,
            config=db_session.config,
            created_at=db_session.created_at,
            started_at=db_session.started_at,
            stopped_at=db_session.stopped_at,
            progress=db_session.progress,
            current_time=db_session.simulation_time,
            total_time=db_session.total_time,
            step_count=db_session.current_step
        )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真会话失败: {str(e)}")

@router.post("/{session_id}/control")
async def control_simulation(
    session_id: str, 
    request: SimulationControlRequest,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    控制仿真执行
    """
    try:
        # 从数据库获取会话并检查权限
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权控制此仿真会话")
        
        # 检查内存中是否存在会话
        if session_id not in simulation_sessions:
            raise HTTPException(status_code=400, detail="仿真会话未在运行中")
        
        session = simulation_sessions[session_id]
        
        # 执行控制动作
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
        
        # 同步状态到数据库
        update_data = {
            "status": session.status,
            "progress": session.progress,
            "simulation_time": session.current_time,
            "current_step": session.step_count
        }
        
        if request.action == "start" and not db_session.started_at:
            update_data["started_at"] = datetime.utcnow()
        elif request.action == "stop":
            update_data["stopped_at"] = datetime.utcnow()
        
        SimulationSessionCRUD.update(db, session_id, update_data)
        
        # 记录事件
        event_data = {
            "session_id": session_id,
            "event_type": f"simulation_{request.action}",
            "event_data": {"action": request.action, "user_id": current_user.id},
            "timestamp": datetime.utcnow()
        }
        SimulationEventCRUD.create(db, event_data)
        
        return {"message": f"仿真控制操作 '{request.action}' 执行成功", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation control failed: {str(e)}")
        if session_id in simulation_sessions:
            session = simulation_sessions[session_id]
            session.status = SimulationStatus.ERROR
            session.error_message = str(e)
        raise HTTPException(status_code=500, detail=f"仿真控制失败: {str(e)}")

@router.get("/{session_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取仿真状态
    """
    try:
        # 从数据库获取会话并检查权限
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        # 检查用户权限
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 优先返回内存中的实时状态
        if session_id in simulation_sessions:
            session = simulation_sessions[session_id]
            
            # 获取仿真引擎状态
            engine_status = {}
            if session_id in simulation_engines:
                engine = simulation_engines[session_id]
                engine_status = engine.get_status()
                
                # 同步引擎状态到会话
                session.current_time = engine_status.get('current_time', session.current_time)
                session.progress = engine_status.get('progress', session.progress)
                session.step_count = engine_status.get('step_count', session.step_count)
                session.performance_metrics = engine_status.get('performance_metrics', session.performance_metrics)
                if engine_status.get('error_message'):
                    session.error_message = engine_status['error_message']
            
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
        
        # 否则返回数据库中的状态
        return SimulationStatusResponse(
            session_id=session_id,
            status=db_session.status,
            progress=db_session.progress,
            current_time=db_session.simulation_time,
            total_time=db_session.total_time,
            step_count=db_session.current_step,
            performance_metrics={},
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation status {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真状态失败: {str(e)}")

@router.delete("/{session_id}")
async def delete_simulation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    删除仿真会话
    """
    try:
        # 从数据库获取会话并检查权限
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此仿真会话")
        
        # 如果会话在内存中运行，先停止它
        if session_id in simulation_sessions:
            session = simulation_sessions[session_id]
            if session.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
                await stop_simulation(session_id)
            
            # 删除会话数据
            del simulation_sessions[session_id]
            if session_id in simulation_locks:
                del simulation_locks[session_id]
        
        # 从数据库删除（级联删除相关数据）
        SimulationSessionCRUD.delete(db, session_id)
        
        # 记录删除事件
        event_data = {
            "session_id": session_id,
            "event_type": "simulation_deleted",
            "event_data": {"user_id": current_user.id},
            "timestamp": datetime.utcnow()
        }
        SimulationEventCRUD.create(db, event_data)
        
        logger.info(f"Deleted simulation session: {session_id} by user: {current_user.username}")
        
        return {"message": "仿真会话已删除", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete simulation {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除仿真失败: {str(e)}")

# 仿真控制函数
async def start_simulation(session_id: str):
    """
    启动仿真
    """
    if session_id not in simulation_sessions:
        raise ValueError(f"Simulation session {session_id} not found")
    
    if session_id not in simulation_engines:
        raise ValueError(f"Simulation engine {session_id} not found")
    
    session = simulation_sessions[session_id]
    engine = simulation_engines[session_id]
    
    if session.status == SimulationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="仿真已在运行中")
    
    async with simulation_locks[session_id]:
        # 启动仿真引擎
        success = await engine.start()
        if not success:
            raise ValueError(f"Failed to start simulation engine: {engine.error_message}")
        
        session.status = SimulationStatus.RUNNING
        session.started_at = datetime.now()
        session.error_message = None
        
        logger.info(f"Started simulation: {session_id}")

async def pause_simulation(session_id: str):
    """
    暂停仿真
    """
    if session_id not in simulation_sessions:
        raise ValueError(f"Simulation session {session_id} not found")
    
    if session_id not in simulation_engines:
        raise ValueError(f"Simulation engine {session_id} not found")
    
    session = simulation_sessions[session_id]
    engine = simulation_engines[session_id]
    
    if session.status != SimulationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="仿真未在运行中")
    
    async with simulation_locks[session_id]:
        # 暂停仿真引擎
        success = await engine.pause()
        if not success:
            raise ValueError(f"Failed to pause simulation engine")
        
        session.status = SimulationStatus.PAUSED
        logger.info(f"Paused simulation: {session_id}")

async def resume_simulation(session_id: str):
    """
    恢复仿真
    """
    if session_id not in simulation_sessions:
        raise ValueError(f"Simulation session {session_id} not found")
    
    if session_id not in simulation_engines:
        raise ValueError(f"Simulation engine {session_id} not found")
    
    session = simulation_sessions[session_id]
    engine = simulation_engines[session_id]
    
    if session.status != SimulationStatus.PAUSED:
        raise HTTPException(status_code=400, detail="仿真未处于暂停状态")
    
    async with simulation_locks[session_id]:
        # 恢复仿真引擎
        success = await engine.resume()
        if not success:
            raise ValueError(f"Failed to resume simulation engine")
        
        session.status = SimulationStatus.RUNNING
        logger.info(f"Resumed simulation: {session_id}")

async def stop_simulation(session_id: str):
    """
    停止仿真
    """
    if session_id not in simulation_sessions:
        raise ValueError(f"Simulation session {session_id} not found")
    
    if session_id not in simulation_engines:
        raise ValueError(f"Simulation engine {session_id} not found")
    
    session = simulation_sessions[session_id]
    engine = simulation_engines[session_id]
    
    async with simulation_locks[session_id]:
        # 停止仿真引擎
        success = await engine.stop()
        if not success:
            logger.warning(f"Failed to stop simulation engine {session_id}")
        
        session.status = SimulationStatus.STOPPED
        session.stopped_at = datetime.now()
        
        # 取消仿真任务（如果存在）
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
    for session_id in list(simulation_sessions.keys()):
        try:
            await stop_simulation(session_id)
        except Exception as e:
            logger.error(f"Error stopping simulation {session_id}: {e}")
    
    # 清理仿真引擎
    for session_id, engine in simulation_engines.items():
        try:
            engine.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up simulation engine {session_id}: {e}")
    
    # 清理数据
    simulation_sessions.clear()
    simulation_engines.clear()
    simulation_tasks.clear()
    simulation_locks.clear()
    
    logger.info("Simulation resources cleaned up")

# 获取仿真统计信息
@router.get("/stats/overview")
async def get_simulation_stats(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取当前用户的仿真统计概览
    """
    try:
        # 获取当前用户的所有仿真会话（数据库）
        db_sessions = SimulationSessionCRUD.get_by_user(db, current_user.id)
        
        # 统计数据库中的会话状态
        db_stats = {
            SimulationStatus.IDLE: 0,
            SimulationStatus.RUNNING: 0,
            SimulationStatus.PAUSED: 0,
            SimulationStatus.COMPLETED: 0,
            SimulationStatus.ERROR: 0,
            SimulationStatus.STOPPED: 0
        }
        
        for session in db_sessions:
            if session.status in db_stats:
                db_stats[session.status] += 1
        
        # 统计内存中当前用户的活跃会话
        user_memory_sessions = []
        for session_id, session in simulation_sessions.items():
            # 检查会话是否属于当前用户（通过数据库验证）
            db_session = SimulationSessionCRUD.get(db, session_id)
            if db_session and db_session.user_id == current_user.id:
                user_memory_sessions.append(session)
        
        active_running = len([s for s in user_memory_sessions if s.status == SimulationStatus.RUNNING])
        active_paused = len([s for s in user_memory_sessions if s.status == SimulationStatus.PAUSED])
        
        return {
            "total_sessions": len(db_sessions),
            "running_sessions": active_running,
            "paused_sessions": active_paused,
            "completed_sessions": db_stats[SimulationStatus.COMPLETED],
            "error_sessions": db_stats[SimulationStatus.ERROR],
            "stopped_sessions": db_stats[SimulationStatus.STOPPED],
            "idle_sessions": db_stats[SimulationStatus.IDLE],
            "active_memory_sessions": len(user_memory_sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get simulation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真统计失败: {str(e)}")

# 获取仿真详细状态
@router.get("/{session_id}/details")
async def get_simulation_details(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取仿真的详细状态，包括组件和智能体状态
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 获取基本状态
        basic_status = await get_simulation_status(session_id, db, current_user)
        
        # 获取详细状态
        component_states = {}
        agent_states = {}
        
        if session_id in simulation_engines:
            engine = simulation_engines[session_id]
            component_states = engine.get_component_states()
            agent_states = engine.get_agent_states()
        
        return {
            "basic_status": basic_status,
            "component_states": component_states,
            "agent_states": agent_states,
            "engine_available": session_id in simulation_engines
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真详细状态失败: {str(e)}")

# 执行单步仿真
@router.post("/{session_id}/step")
async def step_simulation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    执行单步仿真（仅在仿真未运行时可用）
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 检查仿真引擎
        if session_id not in simulation_engines:
            raise HTTPException(status_code=404, detail="仿真引擎不存在")
        
        engine = simulation_engines[session_id]
        
        # 执行单步
        success = await engine.step()
        if not success:
            raise HTTPException(status_code=400, detail=f"单步执行失败: {engine.error_message}")
        
        # 同步状态
        if session_id in simulation_sessions:
            session = simulation_sessions[session_id]
            engine_status = engine.get_status()
            session.current_time = engine_status.get('current_time', session.current_time)
            session.progress = engine_status.get('progress', session.progress)
            session.step_count = engine_status.get('step_count', session.step_count)
        
        return {
            "success": True,
            "message": "单步执行成功",
            "current_time": engine.current_time,
            "step_count": engine.step_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to step simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"单步执行失败: {str(e)}")