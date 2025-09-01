import asyncio
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import logging
from functools import wraps
import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """
    缓存管理器
    支持内存缓存和Redis缓存
    """
    
    def __init__(self):
        self.memory_cache: Dict[str, Dict] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5分钟默认过期时间
        
    async def initialize(self):
        """
        初始化缓存管理器
        """
        try:
            # 尝试连接Redis
            self.redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache only: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        """
        # 创建唯一标识符
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        """
        try:
            # 首先尝试Redis
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            
            # 然后尝试内存缓存
            if key in self.memory_cache:
                cache_item = self.memory_cache[key]
                if cache_item['expires_at'] > datetime.now():
                    return cache_item['value']
                else:
                    # 过期，删除
                    del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        """
        if ttl is None:
            ttl = self.default_ttl
        
        try:
            # 序列化值
            serialized_value = json.dumps(value, default=str)
            
            # 存储到Redis
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
            
            # 存储到内存缓存
            self.memory_cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存值
        """
        try:
            # 从Redis删除
            if self.redis_client:
                await self.redis_client.delete(key)
            
            # 从内存缓存删除
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存
        """
        count = 0
        
        try:
            # 清除Redis中的匹配键
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    count += await self.redis_client.delete(*keys)
            
            # 清除内存缓存中的匹配键
            memory_keys_to_delete = [
                key for key in self.memory_cache.keys() 
                if self._match_pattern(key, pattern)
            ]
            
            for key in memory_keys_to_delete:
                del self.memory_cache[key]
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """
        简单的模式匹配（支持*通配符）
        """
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def cleanup_expired(self):
        """
        清理过期的内存缓存
        """
        now = datetime.now()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item['expires_at'] <= now
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# 全局缓存管理器实例
cache_manager = CacheManager()

def cached(ttl: int = 300, key_prefix: str = "default"):
    """
    缓存装饰器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_manager._generate_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存储到缓存
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class SimulationCache:
    """
    仿真专用缓存
    """
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.prefix = "simulation"
    
    async def cache_simulation_config(self, session_id: str, config: Dict) -> bool:
        """
        缓存仿真配置
        """
        key = f"{self.prefix}:config:{session_id}"
        return await self.cache_manager.set(key, config, ttl=3600)  # 1小时
    
    async def get_simulation_config(self, session_id: str) -> Optional[Dict]:
        """
        获取仿真配置
        """
        key = f"{self.prefix}:config:{session_id}"
        return await self.cache_manager.get(key)
    
    async def cache_component_state(self, session_id: str, component_id: str, state: Dict) -> bool:
        """
        缓存组件状态
        """
        key = f"{self.prefix}:component:{session_id}:{component_id}"
        return await self.cache_manager.set(key, state, ttl=60)  # 1分钟
    
    async def get_component_state(self, session_id: str, component_id: str) -> Optional[Dict]:
        """
        获取组件状态
        """
        key = f"{self.prefix}:component:{session_id}:{component_id}"
        return await self.cache_manager.get(key)
    
    async def clear_simulation_cache(self, session_id: str) -> int:
        """
        清除特定仿真的所有缓存
        """
        pattern = f"{self.prefix}:*:{session_id}*"
        return await self.cache_manager.clear_pattern(pattern)
    
    async def cache_simulation_results(self, session_id: str, results: Dict) -> bool:
        """
        缓存仿真结果
        """
        key = f"{self.prefix}:results:{session_id}"
        return await self.cache_manager.set(key, results, ttl=7200)  # 2小时
    
    async def get_simulation_results(self, session_id: str) -> Optional[Dict]:
        """
        获取仿真结果
        """
        key = f"{self.prefix}:results:{session_id}"
        return await self.cache_manager.get(key)

# 仿真缓存实例
simulation_cache = SimulationCache(cache_manager)

# 启动清理任务
async def start_cache_cleanup_task():
    """
    启动缓存清理任务
    """
    while True:
        try:
            await cache_manager.cleanup_expired()
            await asyncio.sleep(300)  # 每5分钟清理一次
        except Exception as e:
            logger.error(f"Cache cleanup task error: {e}")
            await asyncio.sleep(60)