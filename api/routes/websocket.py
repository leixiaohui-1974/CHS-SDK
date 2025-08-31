from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel
import uuid

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(tags=["websocket"])

# WebSocket消息类型
class WebSocketMessageType:
    DATA = "data"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SIMULATION_STATE = "simulation_state"
    CONTROL = "control"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

# WebSocket消息模型
class WebSocketMessage(BaseModel):
    type: str
    payload: Any
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    client_id: Optional[str] = None

# 仿真数据模型
class SimulationData(BaseModel):
    timestamp: float
    id: str
    component_type: str
    water_level: Optional[float] = None
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    volume: Optional[float] = None
    status: Optional[str] = None
    metadata: Optional[Dict] = None

# 客户端连接信息
class ClientConnection:
    def __init__(self, websocket: WebSocket, client_id: str, session_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.session_id = session_id
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.subscriptions: Set[str] = set()
        self.is_active = True

# 连接管理器
class ConnectionManager:
    def __init__(self):
        # 按会话ID组织的连接
        self.connections: Dict[str, Dict[str, ClientConnection]] = {}
        # 全局连接映射
        self.client_connections: Dict[str, ClientConnection] = {}
        # 订阅管理
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> client_ids
        # 心跳任务
        self.heartbeat_task: Optional[asyncio.Task] = None
        # 数据广播任务
        self.broadcast_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """
        建立WebSocket连接
        """
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        connection = ClientConnection(websocket, client_id, session_id)
        
        # 存储连接
        if session_id not in self.connections:
            self.connections[session_id] = {}
        
        self.connections[session_id][client_id] = connection
        self.client_connections[client_id] = connection
        
        logger.info(f"Client {client_id} connected to session {session_id}")
        
        # 启动心跳检测（如果还没有启动）
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 启动数据广播（如果还没有启动）
        if self.broadcast_task is None or self.broadcast_task.done():
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """
        断开WebSocket连接
        """
        if client_id in self.client_connections:
            connection = self.client_connections[client_id]
            session_id = connection.session_id
            
            # 清理订阅
            for topic in list(connection.subscriptions):
                await self.unsubscribe(client_id, topic)
            
            # 移除连接
            if session_id in self.connections and client_id in self.connections[session_id]:
                del self.connections[session_id][client_id]
                
                # 如果会话没有连接了，清理会话
                if not self.connections[session_id]:
                    del self.connections[session_id]
            
            del self.client_connections[client_id]
            
            logger.info(f"Client {client_id} disconnected from session {session_id}")
    
    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """
        向指定客户端发送消息
        """
        if client_id in self.client_connections:
            connection = self.client_connections[client_id]
            if connection.is_active:
                try:
                    message.timestamp = datetime.now()
                    message.client_id = client_id
                    await connection.websocket.send_text(message.json())
                except Exception as e:
                    logger.error(f"Failed to send message to client {client_id}: {e}")
                    connection.is_active = False
    
    async def send_to_session(self, session_id: str, message: WebSocketMessage):
        """
        向会话中的所有客户端发送消息
        """
        if session_id in self.connections:
            message.session_id = session_id
            tasks = []
            for client_id in self.connections[session_id]:
                tasks.append(self.send_to_client(client_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """
        向所有客户端广播消息
        """
        tasks = []
        for client_id in self.client_connections:
            tasks.append(self.send_to_client(client_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(self, client_id: str, topic: str):
        """
        订阅主题
        """
        if client_id in self.client_connections:
            connection = self.client_connections[client_id]
            connection.subscriptions.add(topic)
            
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)
            
            logger.info(f"Client {client_id} subscribed to topic {topic}")
    
    async def unsubscribe(self, client_id: str, topic: str):
        """
        取消订阅主题
        """
        if client_id in self.client_connections:
            connection = self.client_connections[client_id]
            connection.subscriptions.discard(topic)
            
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            logger.info(f"Client {client_id} unsubscribed from topic {topic}")
    
    async def publish_to_topic(self, topic: str, message: WebSocketMessage):
        """
        向主题订阅者发布消息
        """
        if topic in self.subscriptions:
            tasks = []
            for client_id in self.subscriptions[topic]:
                tasks.append(self.send_to_client(client_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_session_clients(self, session_id: str) -> List[str]:
        """
        获取会话中的所有客户端ID
        """
        if session_id in self.connections:
            return list(self.connections[session_id].keys())
        return []
    
    def get_connection_stats(self) -> Dict:
        """
        获取连接统计信息
        """
        total_connections = len(self.client_connections)
        active_connections = len([c for c in self.client_connections.values() if c.is_active])
        sessions_count = len(self.connections)
        topics_count = len(self.subscriptions)
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "sessions_count": sessions_count,
            "topics_count": topics_count,
            "subscriptions": {topic: len(clients) for topic, clients in self.subscriptions.items()}
        }
    
    async def _heartbeat_loop(self):
        """
        心跳检测循环
        """
        while True:
            try:
                current_time = datetime.now()
                inactive_clients = []
                
                for client_id, connection in self.client_connections.items():
                    if connection.is_active:
                        # 发送心跳
                        heartbeat_message = WebSocketMessage(
                            type=WebSocketMessageType.HEARTBEAT,
                            payload={"timestamp": current_time.isoformat()}
                        )
                        await self.send_to_client(client_id, heartbeat_message)
                        
                        # 检查客户端是否超时
                        time_since_heartbeat = (current_time - connection.last_heartbeat).total_seconds()
                        if time_since_heartbeat > 60:  # 60秒超时
                            inactive_clients.append(client_id)
                
                # 清理非活跃连接
                for client_id in inactive_clients:
                    await self.disconnect(client_id)
                
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_loop(self):
        """
        数据广播循环
        """
        while True:
            try:
                # 这里可以添加定期广播的逻辑
                # 例如系统状态、性能指标等
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"Broadcast loop error: {e}")
                await asyncio.sleep(5)

# 全局连接管理器实例
connection_manager = ConnectionManager()

# WebSocket端点
@router.websocket("/ws/simulations/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket连接端点
    """
    client_id = None
    
    try:
        # 建立连接
        client_id = await connection_manager.connect(websocket, session_id)
        
        # 发送连接确认
        welcome_message = WebSocketMessage(
            type=WebSocketMessageType.STATUS,
            payload={
                "status": "connected",
                "client_id": client_id,
                "session_id": session_id,
                "server_time": datetime.now().isoformat()
            }
        )
        await connection_manager.send_to_client(client_id, welcome_message)
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 解析消息
                message = WebSocketMessage(**message_data)
                
                # 更新心跳时间
                if client_id in connection_manager.client_connections:
                    connection_manager.client_connections[client_id].last_heartbeat = datetime.now()
                
                # 处理消息
                await handle_websocket_message(client_id, session_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                error_message = WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    payload={"error": "Invalid JSON format", "details": str(e)}
                )
                await connection_manager.send_to_client(client_id, error_message)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                error_message = WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    payload={"error": "Message processing failed", "details": str(e)}
                )
                await connection_manager.send_to_client(client_id, error_message)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # 清理连接
        if client_id:
            await connection_manager.disconnect(client_id)

async def handle_websocket_message(client_id: str, session_id: str, message: WebSocketMessage):
    """
    处理WebSocket消息
    """
    try:
        if message.type == WebSocketMessageType.HEARTBEAT:
            # 心跳响应
            response = WebSocketMessage(
                type=WebSocketMessageType.HEARTBEAT,
                payload={"timestamp": datetime.now().isoformat(), "status": "alive"}
            )
            await connection_manager.send_to_client(client_id, response)
        
        elif message.type == WebSocketMessageType.SUBSCRIBE:
            # 订阅主题
            topic = message.payload.get("topic")
            if topic:
                await connection_manager.subscribe(client_id, topic)
                response = WebSocketMessage(
                    type=WebSocketMessageType.STATUS,
                    payload={"status": "subscribed", "topic": topic}
                )
                await connection_manager.send_to_client(client_id, response)
        
        elif message.type == WebSocketMessageType.UNSUBSCRIBE:
            # 取消订阅
            topic = message.payload.get("topic")
            if topic:
                await connection_manager.unsubscribe(client_id, topic)
                response = WebSocketMessage(
                    type=WebSocketMessageType.STATUS,
                    payload={"status": "unsubscribed", "topic": topic}
                )
                await connection_manager.send_to_client(client_id, response)
        
        elif message.type == WebSocketMessageType.CONTROL:
            # 仿真控制消息
            await handle_simulation_control(client_id, session_id, message.payload)
        
        else:
            # 未知消息类型
            error_message = WebSocketMessage(
                type=WebSocketMessageType.ERROR,
                payload={"error": f"Unknown message type: {message.type}"}
            )
            await connection_manager.send_to_client(client_id, error_message)
    
    except Exception as e:
        logger.error(f"Error handling message type {message.type}: {e}")
        error_message = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            payload={"error": "Message handling failed", "details": str(e)}
        )
        await connection_manager.send_to_client(client_id, error_message)

async def handle_simulation_control(client_id: str, session_id: str, payload: Dict):
    """
    处理仿真控制消息
    """
    action = payload.get("action")
    
    if action in ["start", "pause", "resume", "stop", "reset"]:
        # 这里应该调用仿真控制API
        # 目前发送确认消息
        response = WebSocketMessage(
            type=WebSocketMessageType.STATUS,
            payload={
                "status": "control_received",
                "action": action,
                "session_id": session_id
            }
        )
        await connection_manager.send_to_client(client_id, response)
    else:
        error_message = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            payload={"error": f"Unknown control action: {action}"}
        )
        await connection_manager.send_to_client(client_id, error_message)

# 数据发布函数
async def publish_simulation_data(session_id: str, data: SimulationData):
    """
    发布仿真数据到WebSocket客户端
    """
    message = WebSocketMessage(
        type=WebSocketMessageType.DATA,
        payload=data.dict()
    )
    await connection_manager.send_to_session(session_id, message)

async def publish_simulation_status(session_id: str, status: Dict):
    """
    发布仿真状态到WebSocket客户端
    """
    message = WebSocketMessage(
        type=WebSocketMessageType.SIMULATION_STATE,
        payload=status
    )
    await connection_manager.send_to_session(session_id, message)

async def publish_error(session_id: str, error: Dict):
    """
    发布错误信息到WebSocket客户端
    """
    message = WebSocketMessage(
        type=WebSocketMessageType.ERROR,
        payload=error
    )
    await connection_manager.send_to_session(session_id, message)

# 获取连接统计信息的API端点
@router.get("/ws/stats")
async def get_websocket_stats():
    """
    获取WebSocket连接统计信息
    """
    return connection_manager.get_connection_stats()

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
    for client_id in list(connection_manager.client_connections.keys()):
        try:
            await connection_manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")
    
    # 取消后台任务
    if connection_manager.heartbeat_task and not connection_manager.heartbeat_task.done():
        connection_manager.heartbeat_task.cancel()
    
    if connection_manager.broadcast_task and not connection_manager.broadcast_task.done():
        connection_manager.broadcast_task.cancel()
    
    logger.info("WebSocket resources cleaned up")