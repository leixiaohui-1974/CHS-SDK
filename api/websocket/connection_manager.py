from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket 连接管理器
    管理客户端连接、消息广播和会话订阅
    """
    
    def __init__(self):
        # 活跃连接：{connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用户连接映射：{user_id: {connection_id}}
        self.user_connections: Dict[str, Set[str]] = {}
        
        # 会话订阅：{session_id: {connection_id}}
        self.session_subscriptions: Dict[str, Set[str]] = {}
        
        # 连接元数据：{connection_id: {user_id, session_ids, connected_at}}
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str) -> str:
        """
        接受新的 WebSocket 连接
        """
        import uuid
        connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            # 存储连接
            self.active_connections[connection_id] = websocket
            
            # 更新用户连接映射
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # 存储连接元数据
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "session_ids": set(),
                "connected_at": datetime.now()
            }
            
            logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection {connection_id}: {str(e)}")
            raise e
    
    async def disconnect(self, connection_id: str):
        """
        断开 WebSocket 连接
        """
        try:
            if connection_id in self.connection_metadata:
                metadata = self.connection_metadata[connection_id]
                user_id = metadata["user_id"]
                session_ids = metadata["session_ids"]
                
                # 从用户连接映射中移除
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # 从会话订阅中移除
                for session_id in session_ids:
                    if session_id in self.session_subscriptions:
                        self.session_subscriptions[session_id].discard(connection_id)
                        if not self.session_subscriptions[session_id]:
                            del self.session_subscriptions[session_id]
                
                # 清理连接数据
                del self.connection_metadata[connection_id]
            
            # 移除活跃连接
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            logger.info(f"WebSocket connection disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection {connection_id}: {str(e)}")
    
    async def send_personal_message(self, connection_id: str, message: dict):
        """
        向指定连接发送消息
        """
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {str(e)}")
                # 连接可能已断开，清理连接
                await self.disconnect(connection_id)
    
    async def send_to_user(self, message: dict, user_id: str):
        """
        向指定用户的所有连接发送消息
        """
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        """
        向订阅指定会话的所有连接广播消息
        """
        if session_id in self.session_subscriptions:
            connection_ids = list(self.session_subscriptions[session_id])
            for connection_id in connection_ids:
                await self.send_personal_message(connection_id, message)
    
    async def subscribe_to_session(self, connection_id: str, session_id: str):
        """
        订阅仿真会话更新
        """
        try:
            if connection_id not in self.active_connections:
                return False
            
            # 添加到会话订阅
            if session_id not in self.session_subscriptions:
                self.session_subscriptions[session_id] = set()
            self.session_subscriptions[session_id].add(connection_id)
            
            # 更新连接元数据
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["session_ids"].add(session_id)
            
            logger.info(f"Connection {connection_id} subscribed to session {session_id}")
            
            # 发送订阅确认
            await self.send_personal_message(connection_id, {
                "type": "subscription_confirmed",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe {connection_id} to session {session_id}: {str(e)}")
            return False
    
    async def unsubscribe_from_session(self, connection_id: str, session_id: str):
        """
        取消订阅仿真会话更新
        """
        try:
            # 从会话订阅中移除
            if session_id in self.session_subscriptions:
                self.session_subscriptions[session_id].discard(connection_id)
                if not self.session_subscriptions[session_id]:
                    del self.session_subscriptions[session_id]
            
            # 更新连接元数据
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["session_ids"].discard(session_id)
            
            logger.info(f"Connection {connection_id} unsubscribed from session {session_id}")
            
            # 发送取消订阅确认
            await self.send_personal_message({
                "type": "unsubscription_confirmed",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }, connection_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe {connection_id} from session {session_id}: {str(e)}")
            return False
    
    async def broadcast_simulation_update(self, session_id: str, update_data: dict):
        """
        广播仿真更新消息
        """
        message = {
            "type": "simulation_update",
            "session_id": session_id,
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_session(message, session_id)
    
    async def broadcast_simulation_status(self, session_id: str, status: str, progress: float = None):
        """
        广播仿真状态变化
        """
        message = {
            "type": "simulation_status",
            "session_id": session_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if progress is not None:
            message["progress"] = progress
        
        await self.broadcast_to_session(message, session_id)
    
    async def broadcast_simulation_error(self, session_id: str, error_message: str):
        """
        广播仿真错误消息
        """
        message = {
            "type": "simulation_error",
            "session_id": session_id,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_session(message, session_id)
    
    def get_stats(self) -> dict:
        """
        获取连接统计信息
        """
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "total_subscriptions": sum(len(subs) for subs in self.session_subscriptions.values()),
            "active_sessions": len(self.session_subscriptions)
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """
        获取用户的所有连接ID
        """
        return list(self.user_connections.get(user_id, set()))
    
    def get_session_subscribers(self, session_id: str) -> List[str]:
        """
        获取会话的所有订阅者连接ID
        """
        return list(self.session_subscriptions.get(session_id, set()))
    
    def get_session_clients(self, session_id: str) -> List[dict]:
        """
        获取会话的客户端信息列表
        """
        clients = []
        connection_ids = self.session_subscriptions.get(session_id, set())
        
        for connection_id in connection_ids:
            if connection_id in self.connection_metadata:
                metadata = self.connection_metadata[connection_id]
                clients.append({
                    "connection_id": connection_id,
                    "user_id": metadata["user_id"],
                    "connected_at": metadata["connected_at"].isoformat()
                })
        
        return clients

# 全局连接管理器实例
connection_manager = ConnectionManager()