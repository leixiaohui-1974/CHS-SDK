"""
通信协议定义

定义标准化的通信协议和消息格式。
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time
import uuid


class MessageType(Enum):
    """消息类型"""
    STATE_UPDATE = "state_update"           # 状态更新
    COMMAND = "command"                     # 命令
    RESPONSE = "response"                   # 响应
    EVENT = "event"                        # 事件
    HEARTBEAT = "heartbeat"                # 心跳
    ERROR = "error"                        # 错误
    REQUEST = "request"                    # 请求
    ACKNOWLEDGMENT = "acknowledgment"       # 确认


@dataclass
class StandardMessage:
    """标准消息格式"""
    message_id: str
    message_type: MessageType
    sender_id: str
    timestamp: float
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expires_at: Optional[float] = None
    
    @classmethod
    def create(cls, message_type: MessageType, sender_id: str, 
               data: Dict[str, Any], correlation_id: Optional[str] = None,
               reply_to: Optional[str] = None, ttl_seconds: Optional[float] = None) -> 'StandardMessage':
        """
        创建标准消息
        
        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            data: 消息数据
            correlation_id: 关联ID
            reply_to: 回复主题
            ttl_seconds: 消息生存时间（秒）
            
        Returns:
            StandardMessage: 标准消息实例
        """
        message_id = str(uuid.uuid4())
        timestamp = time.time()
        expires_at = timestamp + ttl_seconds if ttl_seconds else None
        
        return cls(
            message_id=message_id,
            message_type=message_type,
            sender_id=sender_id,
            timestamp=timestamp,
            data=data,
            correlation_id=correlation_id,
            reply_to=reply_to,
            expires_at=expires_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "expires_at": self.expires_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardMessage':
        """从字典创建"""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            timestamp=data["timestamp"],
            data=data["data"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            expires_at=data.get("expires_at")
        )
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CommunicationProtocol:
    """
    通信协议管理器
    
    提供标准化的消息创建、验证和处理功能。
    """
    
    @staticmethod
    def create_state_message(sender_id: str, component_id: str, 
                           state_data: Dict[str, Any]) -> StandardMessage:
        """
        创建状态消息
        
        Args:
            sender_id: 发送者ID
            component_id: 组件ID
            state_data: 状态数据
            
        Returns:
            StandardMessage: 状态消息
        """
        data = {
            "component_id": component_id,
            "state": state_data
        }
        return StandardMessage.create(MessageType.STATE_UPDATE, sender_id, data)
    
    @staticmethod
    def create_command_message(sender_id: str, target_id: str,
                             command: str, parameters: Dict[str, Any]) -> StandardMessage:
        """
        创建命令消息
        
        Args:
            sender_id: 发送者ID
            target_id: 目标ID
            command: 命令名称
            parameters: 命令参数
            
        Returns:
            StandardMessage: 命令消息
        """
        data = {
            "target_id": target_id,
            "command": command,
            "parameters": parameters
        }
        return StandardMessage.create(MessageType.COMMAND, sender_id, data)
    
    @staticmethod
    def create_response_message(sender_id: str, request_message: StandardMessage,
                              result: Dict[str, Any], success: bool = True) -> StandardMessage:
        """
        创建响应消息
        
        Args:
            sender_id: 发送者ID
            request_message: 原始请求消息
            result: 响应结果
            success: 是否成功
            
        Returns:
            StandardMessage: 响应消息
        """
        data = {
            "success": success,
            "result": result,
            "original_message_id": request_message.message_id
        }
        return StandardMessage.create(
            MessageType.RESPONSE, 
            sender_id, 
            data,
            correlation_id=request_message.message_id
        )
    
    @staticmethod
    def create_event_message(sender_id: str, event_type: str,
                           event_data: Dict[str, Any]) -> StandardMessage:
        """
        创建事件消息
        
        Args:
            sender_id: 发送者ID
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            StandardMessage: 事件消息
        """
        data = {
            "event_type": event_type,
            "event_data": event_data
        }
        return StandardMessage.create(MessageType.EVENT, sender_id, data)
    
    @staticmethod
    def create_heartbeat_message(sender_id: str, 
                               status_info: Dict[str, Any]) -> StandardMessage:
        """
        创建心跳消息
        
        Args:
            sender_id: 发送者ID
            status_info: 状态信息
            
        Returns:
            StandardMessage: 心跳消息
        """
        data = {
            "status": status_info,
            "agent_id": sender_id
        }
        return StandardMessage.create(MessageType.HEARTBEAT, sender_id, data)
    
    @staticmethod
    def create_error_message(sender_id: str, error_code: str,
                           error_message: str, context: Optional[Dict[str, Any]] = None) -> StandardMessage:
        """
        创建错误消息
        
        Args:
            sender_id: 发送者ID
            error_code: 错误代码
            error_message: 错误消息
            context: 错误上下文
            
        Returns:
            StandardMessage: 错误消息
        """
        data = {
            "error_code": error_code,
            "error_message": error_message,
            "context": context or {}
        }
        return StandardMessage.create(MessageType.ERROR, sender_id, data)
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """
        验证消息格式
        
        Args:
            message: 消息字典
            
        Returns:
            bool: 消息是否有效
        """
        required_fields = ["message_id", "message_type", "sender_id", "timestamp", "data"]
        
        # 检查必填字段
        for field in required_fields:
            if field not in message:
                return False
        
        # 检查消息类型
        try:
            MessageType(message["message_type"])
        except ValueError:
            return False
        
        # 检查时间戳
        if not isinstance(message["timestamp"], (int, float)):
            return False
        
        # 检查数据字段
        if not isinstance(message["data"], dict):
            return False
        
        return True


# 主题命名约定
class TopicConvention:
    """主题命名约定"""
    
    # 状态主题格式: state/{component_type}/{component_id}/{state_name}
    STATE_PATTERN = "state/{component_type}/{component_id}/{state_name}"
    
    # 命令主题格式: command/{component_type}/{component_id}/{command_name}
    COMMAND_PATTERN = "command/{component_type}/{component_id}/{command_name}"
    
    # 事件主题格式: event/{event_category}/{event_type}
    EVENT_PATTERN = "event/{event_category}/{event_type}"
    
    # 数据主题格式: data/{data_type}/{source_id}
    DATA_PATTERN = "data/{data_type}/{source_id}"
    
    @staticmethod
    def create_state_topic(component_type: str, component_id: str, state_name: str = "state") -> str:
        """创建状态主题"""
        return f"state/{component_type}/{component_id}/{state_name}"
    
    @staticmethod
    def create_command_topic(component_type: str, component_id: str, command_name: str = "action") -> str:
        """创建命令主题"""
        return f"command/{component_type}/{component_id}/{command_name}"
    
    @staticmethod
    def create_event_topic(event_category: str, event_type: str) -> str:
        """创建事件主题"""
        return f"event/{event_category}/{event_type}"
    
    @staticmethod
    def create_data_topic(data_type: str, source_id: str) -> str:
        """创建数据主题"""
        return f"data/{data_type}/{source_id}"