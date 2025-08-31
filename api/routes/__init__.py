# API路由模块初始化文件

from .simulation import router as simulation_router
from .websocket import router as websocket_router
from .auth import router as auth_router

__all__ = [
    "simulation_router",
    "websocket_router",
    "auth_router",
]