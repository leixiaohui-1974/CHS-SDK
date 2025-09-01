import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import psutil
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    监控请求响应时间、内存使用、CPU使用率等指标
    """
    
    def __init__(self, app, max_history: int = 1000):
        super().__init__(app)
        self.max_history = max_history
        self.request_times = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        self.system_stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used_mb': 0
        }
        self._monitor_task = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 启动系统监控任务（如果尚未启动）
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_system())
        
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 更新统计信息
            self._update_stats(endpoint, process_time, response.status_code >= 400)
            
            # 添加性能头信息
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-CPU-Usage"] = str(self.system_stats['cpu_percent'])
            response.headers["X-Memory-Usage"] = str(self.system_stats['memory_percent'])
            
            # 记录慢请求
            if process_time > 1.0:  # 超过1秒的请求
                logger.warning(
                    f"Slow request: {endpoint} took {process_time:.2f}s"
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self._update_stats(endpoint, process_time, True)
            logger.error(f"Request error: {endpoint} - {str(e)}")
            raise
    
    def _update_stats(self, endpoint: str, process_time: float, is_error: bool):
        """
        更新端点统计信息
        """
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += process_time
        stats['min_time'] = min(stats['min_time'], process_time)
        stats['max_time'] = max(stats['max_time'], process_time)
        
        if is_error:
            stats['errors'] += 1
        
        # 记录请求时间历史
        self.request_times.append({
            'endpoint': endpoint,
            'time': process_time,
            'timestamp': datetime.now(),
            'is_error': is_error
        })
    
    async def _monitor_system(self):
        """
        监控系统资源使用情况
        """
        while True:
            try:
                # 获取CPU使用率
                self.system_stats['cpu_percent'] = psutil.cpu_percent(interval=1)
                
                # 获取内存使用情况
                memory = psutil.virtual_memory()
                self.system_stats['memory_percent'] = memory.percent
                self.system_stats['memory_used_mb'] = memory.used / 1024 / 1024
                
                await asyncio.sleep(5)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(10)
    
    def get_performance_stats(self) -> dict:
        """
        获取性能统计信息
        """
        # 计算总体统计
        total_requests = sum(stats['count'] for stats in self.endpoint_stats.values())
        total_errors = sum(stats['errors'] for stats in self.endpoint_stats.values())
        
        # 计算平均响应时间
        recent_times = [req['time'] for req in list(self.request_times)[-100:]]
        avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
        
        # 端点统计
        endpoint_stats = {}
        for endpoint, stats in self.endpoint_stats.items():
            endpoint_stats[endpoint] = {
                'count': stats['count'],
                'avg_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0,
                'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                'max_time': stats['max_time'],
                'error_rate': stats['errors'] / stats['count'] if stats['count'] > 0 else 0
            }
        
        return {
            'system': self.system_stats,
            'requests': {
                'total': total_requests,
                'errors': total_errors,
                'error_rate': total_errors / total_requests if total_requests > 0 else 0,
                'avg_response_time': avg_response_time
            },
            'endpoints': endpoint_stats,
            'recent_requests': list(self.request_times)[-20:]  # 最近20个请求
        }

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    简单的速率限制中间件
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        now = datetime.now()
        
        # 清理过期的请求记录
        cutoff_time = now - timedelta(minutes=1)
        client_queue = self.client_requests[client_ip]
        
        while client_queue and client_queue[0] < cutoff_time:
            client_queue.popleft()
        
        # 检查是否超过限制
        if len(client_queue) >= self.requests_per_minute:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # 记录当前请求
        client_queue.append(now)
        
        return await call_next(request)

class CompressionMiddleware(BaseHTTPMiddleware):
    """
    响应压缩中间件
    """
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 检查是否支持gzip压缩
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # 检查响应大小
        if hasattr(response, 'body') and len(response.body) < self.minimum_size:
            return response
        
        # 添加压缩头（实际压缩由FastAPI的GZipMiddleware处理）
        response.headers["vary"] = "Accept-Encoding"
        
        return response