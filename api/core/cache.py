"""缓存管理模块

提供Redis缓存、内存缓存和分布式缓存的统一接口。
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import hashlib
import logging

import redis.asyncio as redis
from redis.asyncio import Redis
from cachetools import TTLCache, LRUCache

from .config import settings

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """缓存操作异常"""
    pass


class CacheManager:
    """缓存管理器
    
    支持多级缓存：内存缓存 -> Redis缓存
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟TTL
        self.lru_cache = LRUCache(maxsize=500)
        self._connected = False
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            self._connected = True
            logger.info("Redis缓存连接成功")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self._connected = False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis缓存连接已断开")
    
    def _generate_key(self, key: str, prefix: str = "") -> str:
        """生成缓存键"""
        if prefix:
            return f"{settings.CACHE_PREFIX}:{prefix}:{key}"
        return f"{settings.CACHE_PREFIX}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return json.dumps(value)
            else:
                return json.dumps(value, default=str)
        except (TypeError, ValueError):
            # 如果JSON序列化失败，使用pickle
            return pickle.dumps(value).hex()
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化值"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 尝试pickle反序列化
            try:
                return pickle.loads(bytes.fromhex(value))
            except (ValueError, pickle.PickleError):
                return value
    
    async def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._generate_key(key, prefix)
        
        # 首先检查内存缓存
        if cache_key in self.memory_cache:
            logger.debug(f"内存缓存命中: {cache_key}")
            return self.memory_cache[cache_key]
        
        # 检查Redis缓存
        if self._connected and self.redis_client:
            try:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    deserialized_value = self._deserialize_value(value)
                    # 回写到内存缓存
                    self.memory_cache[cache_key] = deserialized_value
                    logger.debug(f"Redis缓存命中: {cache_key}")
                    return deserialized_value
            except Exception as e:
                logger.error(f"Redis获取缓存失败: {e}")
        
        logger.debug(f"缓存未命中: {cache_key}")
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        prefix: str = ""
    ) -> bool:
        """设置缓存值"""
        cache_key = self._generate_key(key, prefix)
        
        # 设置内存缓存
        self.memory_cache[cache_key] = value
        
        # 设置Redis缓存
        if self._connected and self.redis_client:
            try:
                serialized_value = self._serialize_value(value)
                if ttl:
                    await self.redis_client.setex(cache_key, ttl, serialized_value)
                else:
                    await self.redis_client.set(cache_key, serialized_value)
                
                logger.debug(f"缓存设置成功: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Redis设置缓存失败: {e}")
                return False
        
        return True
    
    async def delete(self, key: str, prefix: str = "") -> bool:
        """删除缓存"""
        cache_key = self._generate_key(key, prefix)
        
        # 删除内存缓存
        self.memory_cache.pop(cache_key, None)
        
        # 删除Redis缓存
        if self._connected and self.redis_client:
            try:
                result = await self.redis_client.delete(cache_key)
                logger.debug(f"缓存删除: {cache_key}")
                return bool(result)
            except Exception as e:
                logger.error(f"Redis删除缓存失败: {e}")
                return False
        
        return True
    
    async def exists(self, key: str, prefix: str = "") -> bool:
        """检查缓存是否存在"""
        cache_key = self._generate_key(key, prefix)
        
        # 检查内存缓存
        if cache_key in self.memory_cache:
            return True
        
        # 检查Redis缓存
        if self._connected and self.redis_client:
            try:
                result = await self.redis_client.exists(cache_key)
                return bool(result)
            except Exception as e:
                logger.error(f"Redis检查缓存存在性失败: {e}")
                return False
        
        return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self._connected or not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(f"{settings.CACHE_PREFIX}:{pattern}")
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"清除缓存模式 {pattern}: {deleted} 个键")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_maxsize": self.memory_cache.maxsize,
            "lru_cache_size": len(self.lru_cache),
            "lru_cache_maxsize": self.lru_cache.maxsize,
            "redis_connected": self._connected
        }
        
        if self._connected and self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats.update({
                    "redis_used_memory": redis_info.get("used_memory_human"),
                    "redis_used_memory_peak": redis_info.get("used_memory_peak_human"),
                    "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "redis_keyspace_misses": redis_info.get("keyspace_misses", 0)
                })
            except Exception as e:
                logger.error(f"获取Redis统计信息失败: {e}")
        
        return stats


# 全局缓存管理器实例
cache_manager = CacheManager()


def cache_key_generator(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = []
    
    # 添加位置参数
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # 添加关键字参数
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}:{type(v).__name__}:{v.id}")
        else:
            key_parts.append(f"{k}:{v}")
    
    # 生成哈希
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 300,
    prefix: str = "",
    key_generator: Optional[callable] = None
):
    """缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        prefix: 缓存键前缀
        key_generator: 自定义键生成器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key, prefix)
            if cached_result is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache_manager.set(cache_key, result, ttl, prefix)
            logger.debug(f"缓存设置: {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


class SimulationCache:
    """仿真专用缓存"""
    
    @staticmethod
    async def get_simulation_result(simulation_id: str) -> Optional[Dict[str, Any]]:
        """获取仿真结果缓存"""
        return await cache_manager.get(
            f"simulation_result:{simulation_id}",
            prefix="simulation"
        )
    
    @staticmethod
    async def set_simulation_result(
        simulation_id: str, 
        result: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """设置仿真结果缓存"""
        return await cache_manager.set(
            f"simulation_result:{simulation_id}",
            result,
            ttl,
            prefix="simulation"
        )
    
    @staticmethod
    async def get_simulation_config(config_hash: str) -> Optional[Dict[str, Any]]:
        """获取仿真配置缓存"""
        return await cache_manager.get(
            f"simulation_config:{config_hash}",
            prefix="simulation"
        )
    
    @staticmethod
    async def set_simulation_config(
        config_hash: str, 
        config: Dict[str, Any], 
        ttl: int = 7200
    ) -> bool:
        """设置仿真配置缓存"""
        return await cache_manager.set(
            f"simulation_config:{config_hash}",
            config,
            ttl,
            prefix="simulation"
        )
    
    @staticmethod
    async def clear_simulation_cache(simulation_id: str) -> bool:
        """清除特定仿真的缓存"""
        pattern = f"simulation:*{simulation_id}*"
        deleted = await cache_manager.clear_pattern(pattern)
        return deleted > 0


class UserCache:
    """用户专用缓存"""
    
    @staticmethod
    async def get_user_sessions(user_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取用户会话缓存"""
        return await cache_manager.get(
            f"user_sessions:{user_id}",
            prefix="user"
        )
    
    @staticmethod
    async def set_user_sessions(
        user_id: str, 
        sessions: List[Dict[str, Any]], 
        ttl: int = 1800
    ) -> bool:
        """设置用户会话缓存"""
        return await cache_manager.set(
            f"user_sessions:{user_id}",
            sessions,
            ttl,
            prefix="user"
        )
    
    @staticmethod
    async def get_user_preferences(user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置缓存"""
        return await cache_manager.get(
            f"user_preferences:{user_id}",
            prefix="user"
        )
    
    @staticmethod
    async def set_user_preferences(
        user_id: str, 
        preferences: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """设置用户偏好设置缓存"""
        return await cache_manager.set(
            f"user_preferences:{user_id}",
            preferences,
            ttl,
            prefix="user"
        )
    
    @staticmethod
    async def clear_user_cache(user_id: str) -> bool:
        """清除用户缓存"""
        pattern = f"user:*{user_id}*"
        deleted = await cache_manager.clear_pattern(pattern)
        return deleted > 0


# 缓存预热
class CacheWarmer:
    """缓存预热器"""
    
    @staticmethod
    async def warm_up_common_data():
        """预热常用数据"""
        logger.info("开始缓存预热...")
        
        try:
            # 预热系统配置
            # await cache_manager.set("system_config", get_system_config(), 7200)
            
            # 预热常用仿真模板
            # templates = await get_simulation_templates()
            # await cache_manager.set("simulation_templates", templates, 3600)
            
            logger.info("缓存预热完成")
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")


# 缓存清理
class CacheCleaner:
    """缓存清理器"""
    
    @staticmethod
    async def clean_expired_cache():
        """清理过期缓存"""
        if not cache_manager._connected:
            return
        
        try:
            # 清理过期的仿真结果
            expired_simulations = await cache_manager.clear_pattern(
                "simulation:simulation_result:*"
            )
            
            # 清理过期的用户会话
            expired_sessions = await cache_manager.clear_pattern(
                "user:user_sessions:*"
            )
            
            logger.info(
                f"清理过期缓存: 仿真结果 {expired_simulations}, "
                f"用户会话 {expired_sessions}"
            )
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
    
    @staticmethod
    async def clean_memory_cache():
        """清理内存缓存"""
        cache_manager.memory_cache.clear()
        cache_manager.lru_cache.clear()
        logger.info("内存缓存已清理")


# 导出的便捷函数
async def get_cache(key: str, prefix: str = "") -> Optional[Any]:
    """获取缓存"""
    return await cache_manager.get(key, prefix)


async def set_cache(
    key: str, 
    value: Any, 
    ttl: Optional[int] = None, 
    prefix: str = ""
) -> bool:
    """设置缓存"""
    return await cache_manager.set(key, value, ttl, prefix)


async def delete_cache(key: str, prefix: str = "") -> bool:
    """删除缓存"""
    return await cache_manager.delete(key, prefix)


async def clear_cache_pattern(pattern: str) -> int:
    """清除匹配模式的缓存"""
    return await cache_manager.clear_pattern(pattern)