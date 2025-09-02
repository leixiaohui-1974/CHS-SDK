from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import asyncio
import subprocess
import os
import json
import logging
from datetime import datetime
from pathlib import Path

from api.database import get_db
from api.models.user_models import UserDB
from api.auth import get_current_active_user
from api.crud.simulation_crud import SimulationSessionCRUD
from api.models.simulation_models import (
    SimulationStatus,
    SimulationSessionCreate,
    SimulationSessionUpdate,
    SimulationControlRequest
)
from core_lib.config.unified_config_manager import UnifiedConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/runner", tags=["runner"])

# RunnerAgent状态管理
running_processes: Dict[str, subprocess.Popen] = {}
process_monitors: Dict[str, asyncio.Task] = {}
process_logs: Dict[str, List[str]] = {}

class RunnerAgent:
    """
    仿真执行智能体 - 负责启动和管理仿真进程
    """
    
    def __init__(self):
        self.config_manager = UnifiedConfigManager()
        self.base_path = Path("E:/OneDrive/Documents/GitHub/CHS-SDK")
        self.runner_script = self.base_path / "run_universal_config.py"
        
    async def start_simulation(self, session_id: str, config_path: str) -> Dict[str, Any]:
        """
        启动仿真进程
        """
        try:
            # 检查配置文件是否存在
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            # 检查运行脚本是否存在
            if not self.runner_script.exists():
                raise FileNotFoundError(f"仿真运行脚本不存在: {self.runner_script}")
            
            # 构建命令
            cmd = [
                "python",
                str(self.runner_script),
                "--config", config_path,
                "--session-id", session_id,
                "--output-dir", f"outputs/{session_id}"
            ]
            
            # 启动子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.base_path)
            )
            
            # 存储进程信息
            running_processes[session_id] = process
            process_logs[session_id] = []
            
            # 启动监控任务
            monitor_task = asyncio.create_task(
                self._monitor_process(session_id, process)
            )
            process_monitors[session_id] = monitor_task
            
            logger.info(f"Started simulation process for session {session_id}, PID: {process.pid}")
            
            return {
                "success": True,
                "message": "仿真进程启动成功",
                "process_id": process.pid,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to start simulation {session_id}: {str(e)}")
            return {
                "success": False,
                "message": f"启动仿真失败: {str(e)}",
                "error": str(e)
            }
    
    async def stop_simulation(self, session_id: str) -> Dict[str, Any]:
        """
        停止仿真进程
        """
        try:
            if session_id not in running_processes:
                return {
                    "success": False,
                    "message": "仿真进程不存在或已停止"
                }
            
            process = running_processes[session_id]
            
            # 优雅停止
            process.terminate()
            
            try:
                # 等待进程结束，最多等待10秒
                await asyncio.wait_for(process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                # 强制杀死进程
                process.kill()
                await process.wait()
            
            # 清理资源
            await self._cleanup_process(session_id)
            
            logger.info(f"Stopped simulation process for session {session_id}")
            
            return {
                "success": True,
                "message": "仿真进程已停止",
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to stop simulation {session_id}: {str(e)}")
            return {
                "success": False,
                "message": f"停止仿真失败: {str(e)}",
                "error": str(e)
            }
    
    async def get_process_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取进程状态
        """
        if session_id not in running_processes:
            return {
                "status": "not_found",
                "message": "进程不存在"
            }
        
        process = running_processes[session_id]
        
        if process.returncode is None:
            status = "running"
        elif process.returncode == 0:
            status = "completed"
        else:
            status = "error"
        
        return {
            "status": status,
            "process_id": process.pid,
            "return_code": process.returncode,
            "session_id": session_id,
            "logs": process_logs.get(session_id, [])[-50:]  # 最近50条日志
        }
    
    async def get_process_logs(self, session_id: str, lines: int = 100) -> List[str]:
        """
        获取进程日志
        """
        return process_logs.get(session_id, [])[-lines:]
    
    async def _monitor_process(self, session_id: str, process: subprocess.Popen):
        """
        监控进程输出
        """
        try:
            # 监控stdout
            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    log_line = f"[STDOUT] {datetime.now().isoformat()}: {line.decode().strip()}"
                    process_logs.setdefault(session_id, []).append(log_line)
                    logger.info(f"Process {session_id}: {log_line}")
            
            # 监控stderr
            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    log_line = f"[STDERR] {datetime.now().isoformat()}: {line.decode().strip()}"
                    process_logs.setdefault(session_id, []).append(log_line)
                    logger.error(f"Process {session_id}: {log_line}")
            
            # 并发读取stdout和stderr
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                return_exceptions=True
            )
            
            # 等待进程结束
            await process.wait()
            
            # 记录进程结束
            end_log = f"[SYSTEM] {datetime.now().isoformat()}: Process ended with code {process.returncode}"
            process_logs.setdefault(session_id, []).append(end_log)
            logger.info(f"Process {session_id} ended with code {process.returncode}")
            
        except Exception as e:
            error_log = f"[ERROR] {datetime.now().isoformat()}: Monitor error: {str(e)}"
            process_logs.setdefault(session_id, []).append(error_log)
            logger.error(f"Process monitor error for {session_id}: {str(e)}")
        finally:
            # 清理监控任务
            if session_id in process_monitors:
                del process_monitors[session_id]
    
    async def _cleanup_process(self, session_id: str):
        """
        清理进程资源
        """
        # 取消监控任务
        if session_id in process_monitors:
            monitor_task = process_monitors[session_id]
            if not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            del process_monitors[session_id]
        
        # 清理进程引用
        if session_id in running_processes:
            del running_processes[session_id]
        
        # 保留日志一段时间，不立即清理
        logger.info(f"Cleaned up process resources for session {session_id}")

# 全局RunnerAgent实例
runner_agent = RunnerAgent()

# API路由

@router.post("/start/{session_id}")
async def start_simulation_process(
    session_id: str,
    config_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    启动仿真进程
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 启动仿真
        result = await runner_agent.start_simulation(session_id, config_path)
        
        if result["success"]:
            # 更新数据库状态
            update_data = SimulationSessionUpdate(
                status=SimulationStatus.RUNNING,
                started_at=datetime.now()
            )
            SimulationSessionCRUD.update(db, session_id, update_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start simulation process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动仿真进程失败: {str(e)}")

@router.post("/stop/{session_id}")
async def stop_simulation_process(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    停止仿真进程
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 停止仿真
        result = await runner_agent.stop_simulation(session_id)
        
        if result["success"]:
            # 更新数据库状态
            update_data = SimulationSessionUpdate(
                status=SimulationStatus.STOPPED,
                stopped_at=datetime.now()
            )
            SimulationSessionCRUD.update(db, session_id, update_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop simulation process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止仿真进程失败: {str(e)}")

@router.get("/status/{session_id}")
async def get_simulation_process_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取仿真进程状态
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 获取进程状态
        status = await runner_agent.get_process_status(session_id)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation process status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真进程状态失败: {str(e)}")

@router.get("/logs/{session_id}")
async def get_simulation_process_logs(
    session_id: str,
    lines: int = 100,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取仿真进程日志
    """
    try:
        # 验证会话所有权
        db_session = SimulationSessionCRUD.get(db, session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="仿真会话不存在")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此仿真会话")
        
        # 获取日志
        logs = await runner_agent.get_process_logs(session_id, lines)
        
        return {
            "session_id": session_id,
            "logs": logs,
            "total_lines": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation process logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仿真进程日志失败: {str(e)}")

@router.get("/processes")
async def list_running_processes(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    列出当前用户的所有运行中进程
    """
    try:
        user_processes = []
        
        for session_id in running_processes.keys():
            # 这里应该验证session_id是否属于当前用户
            # 为简化，暂时返回所有进程
            status = await runner_agent.get_process_status(session_id)
            user_processes.append(status)
        
        return {
            "processes": user_processes,
            "total_count": len(user_processes)
        }
        
    except Exception as e:
        logger.error(f"Failed to list running processes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取运行进程列表失败: {str(e)}")

@router.delete("/cleanup")
async def cleanup_all_processes(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    清理所有进程（管理员功能）
    """
    try:
        cleaned_count = 0
        
        # 停止所有进程
        for session_id in list(running_processes.keys()):
            try:
                await runner_agent.stop_simulation(session_id)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to stop process {session_id}: {str(e)}")
        
        # 清理日志
        process_logs.clear()
        
        return {
            "success": True,
            "message": f"已清理 {cleaned_count} 个进程",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup processes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理进程失败: {str(e)}")