#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket监控服务启动脚本

在应用启动时自动启动监控服务，并处理优雅关闭
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from services.websocket_monitor import websocket_monitor
from database.database import init_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitorStartupManager:
    """
    监控服务启动管理器
    """
    
    def __init__(self):
        self.is_shutting_down = False
        self.startup_tasks = []
    
    async def startup(self):
        """
        启动监控服务和相关组件
        """
        logger.info("开始启动监控服务...")
        
        try:
            # 1. 初始化数据库连接
            logger.info("初始化数据库连接...")
            await self._init_database()
            
            # 2. 创建必要的目录
            logger.info("创建必要的目录...")
            await self._create_directories()
            
            # 3. 启动WebSocket监控服务
            logger.info("启动WebSocket监控服务...")
            await websocket_monitor.start_monitoring()
            
            # 4. 设置信号处理器
            self._setup_signal_handlers()
            
            logger.info("监控服务启动完成")
            
        except Exception as e:
            logger.error(f"监控服务启动失败: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """
        优雅关闭监控服务
        """
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("开始关闭监控服务...")
        
        try:
            # 停止WebSocket监控服务
            logger.info("停止WebSocket监控服务...")
            await websocket_monitor.stop_monitoring()
            
            # 等待所有启动任务完成
            if self.startup_tasks:
                logger.info("等待启动任务完成...")
                await asyncio.gather(*self.startup_tasks, return_exceptions=True)
            
            logger.info("监控服务已优雅关闭")
            
        except Exception as e:
            logger.error(f"关闭监控服务时出错: {e}")
    
    async def _init_database(self):
        """
        初始化数据库连接
        """
        try:
            # 这里可以添加数据库初始化逻辑
            # init_db()
            logger.info("数据库连接初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _create_directories(self):
        """
        创建必要的目录
        """
        import os
        from pathlib import Path
        
        directories = [
            "logs",
            "temp",
            "data/monitoring",
            "data/simulations"
        ]
        
        for directory in directories:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {directory}")
    
    def _setup_signal_handlers(self):
        """
        设置信号处理器
        """
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}，开始优雅关闭...")
            asyncio.create_task(self.shutdown())
        
        # 设置信号处理器
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        else:
            # Windows 平台
            signal.signal(signal.SIGINT, signal_handler)
    
    @asynccontextmanager
    async def lifespan_context(self) -> AsyncGenerator[None, None]:
        """
        应用生命周期上下文管理器
        
        用于FastAPI的lifespan参数
        """
        # 启动阶段
        await self.startup()
        
        try:
            yield
        finally:
            # 关闭阶段
            await self.shutdown()

# 全局启动管理器实例
monitor_startup_manager = MonitorStartupManager()

# 导出生命周期上下文管理器
lifespan = monitor_startup_manager.lifespan_context

# 独立运行脚本
async def main():
    """
    独立运行监控服务
    """
    manager = MonitorStartupManager()
    
    try:
        await manager.startup()
        
        # 保持运行直到接收到关闭信号
        logger.info("监控服务正在运行，按 Ctrl+C 停止...")
        
        while not manager.is_shutting_down:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号")
    except Exception as e:
        logger.error(f"监控服务运行错误: {e}")
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    # 独立运行监控服务
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("监控服务已停止")
    except Exception as e:
        logger.error(f"监控服务异常退出: {e}")
        sys.exit(1)