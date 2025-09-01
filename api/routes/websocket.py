from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel
import uuid
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import UserDB
from auth import get_current_active_user
from websocket.connection_manager import connection_manager
from models.websocket_models import WebSocketMessage, SimulationData

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(tags=["websocket"])

# 客户端连接信息
class ClientConnection:
    def __init__(self, websocket: WebSocket, client_id: str, session_id: str, user_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.session_id = session_id
        self.user_id = user_id
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.subscriptions: Set[str] = set()
        self.is_active = True



# WebSocket端点
@router.websocket("/ws/simulations/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    WebSocket连接端点
    """
    client_id = None
    
    try:
        # 建立连接
        client_id = await connection_manager.connect(websocket, session_id, current_user.id)
        
        # 发送连接确认
        welcome_message = {
            "type": "status",
            "payload": {
                "status": "connected",
                "client_id": client_id,
                "session_id": session_id,
                "user_id": current_user.id,
                "server_time": datetime.now().isoformat()
            }
        }
        await connection_manager.send_personal_message(client_id, welcome_message)
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 解析消息
                message = WebSocketMessage(**message_data)
                
                # 处理消息
                await handle_websocket_message(client_id, session_id, message, current_user.id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                error_message = {
                    "type": "error",
                    "payload": {"error": "Invalid JSON format", "details": str(e)}
                }
                await connection_manager.send_personal_message(client_id, error_message)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                error_message = {
                    "type": "error",
                    "payload": {"error": "Message processing failed", "details": str(e)}
                }
                await connection_manager.send_personal_message(client_id, error_message)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # 清理连接
        if client_id:
            await connection_manager.disconnect(client_id)

async def handle_websocket_message(client_id: str, session_id: str, message: WebSocketMessage, user_id: str):
    """
    处理WebSocket消息
    """
    try:
        if message.type == "heartbeat":
            # 心跳响应
            response = {
                "type": "heartbeat",
                "payload": {"timestamp": datetime.now().isoformat(), "status": "alive"}
            }
            await connection_manager.send_personal_message(client_id, response)
        
        elif message.type == "subscribe":
            # 订阅主题
            topic = message.payload.get("topic")
            if topic:
                await connection_manager.subscribe_to_session(client_id, topic)
                response = {
                    "type": "status",
                    "payload": {"status": "subscribed", "topic": topic}
                }
                await connection_manager.send_personal_message(client_id, response)
        
        elif message.type == "unsubscribe":
            # 取消订阅
            topic = message.payload.get("topic")
            if topic:
                await connection_manager.unsubscribe_from_session(client_id, topic)
                response = {
                    "type": "status",
                    "payload": {"status": "unsubscribed", "topic": topic}
                }
                await connection_manager.send_personal_message(client_id, response)
        
        elif message.type == "control":
            # 仿真控制消息
            await handle_simulation_control(client_id, session_id, message.payload, user_id)
        
        else:
            # 未知消息类型
            error_message = {
                "type": "error",
                "payload": {"error": f"Unknown message type: {message.type}"}
            }
            await connection_manager.send_personal_message(client_id, error_message)
    
    except Exception as e:
        logger.error(f"Error handling message type {message.type}: {e}")
        error_message = {
            "type": "error",
            "payload": {"error": "Message handling failed", "details": str(e)}
        }
        await connection_manager.send_personal_message(client_id, error_message)

async def handle_simulation_control(client_id: str, session_id: str, payload: Dict, user_id: str):
    """
    处理仿真控制消息
    """
    action = payload.get("action")
    
    if action in ["start", "pause", "resume", "stop", "reset"]:
        # 这里应该调用仿真控制API
        # 目前发送确认消息
        response = {
            "type": "status",
            "payload": {
                "status": "control_received",
                "action": action,
                "session_id": session_id,
                "user_id": user_id
            }
        }
        await connection_manager.send_personal_message(client_id, response)
    else:
        error_message = {
            "type": "error",
            "payload": {"error": f"Unknown control action: {action}"}
        }
        await connection_manager.send_personal_message(client_id, error_message)

# 数据发布函数
async def publish_simulation_data(session_id: str, data: SimulationData):
    """
    发布仿真数据到WebSocket客户端
    """
    message = {
        "type": "simulation_data",
        "payload": data.dict()
    }
    await connection_manager.broadcast_to_session(message, session_id)

async def publish_simulation_status(session_id: str, status: Dict):
    """
    发布仿真状态到WebSocket客户端
    """
    message = {
        "type": "simulation_status",
        "payload": status
    }
    await connection_manager.broadcast_to_session(message, session_id)

async def publish_error(session_id: str, error: Dict):
    """
    发布错误信息到WebSocket客户端
    """
    message = {
        "type": "error",
        "payload": error
    }
    await connection_manager.broadcast_to_session(message, session_id)

# 获取连接统计信息的API端点
@router.get("/ws/stats")
async def get_websocket_stats():
    """
    获取WebSocket连接统计信息
    """
    return connection_manager.get_stats()

@router.get("/ws/sessions/{session_id}/clients")
async def get_session_clients(session_id: str):
    """
    获取指定会话的客户端列表
    """
    clients = connection_manager.get_session_clients(session_id)
    return {"session_id": session_id, "clients": clients, "count": len(clients)}

# 清理函数
async def cleanup_websocket_resources():
    """
    清理WebSocket资源
    """
    logger.info("Cleaning up WebSocket resources...")
    
    # 断开所有连接
    for client_id in list(connection_manager.user_connections.keys()):
        try:
            await connection_manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")
    
    logger.info("WebSocket resources cleaned up")