"""负载均衡模块

提供请求分发、健康检查、故障转移等功能。
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import aiohttp
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    WEIGHTED_RANDOM = "weighted_random"


class ServerStatus(Enum):
    """服务器状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    DRAINING = "draining"


@dataclass
class ServerNode:
    """服务器节点"""
    id: str
    host: str
    port: int
    weight: int = 1
    status: ServerStatus = ServerStatus.HEALTHY
    current_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def is_available(self) -> bool:
        return self.status in [ServerStatus.HEALTHY, ServerStatus.DRAINING]
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, check_interval: int = 30, timeout: int = 5, max_failures: int = 3):
        self.check_interval = check_interval
        self.timeout = timeout
        self.max_failures = max_failures
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, servers: List[ServerNode]):
        """启动健康检查"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop(servers))
        logger.info("健康检查器已启动")
    
    async def stop(self):
        """停止健康检查"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("健康检查器已停止")
    
    async def _health_check_loop(self, servers: List[ServerNode]):
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.gather(
                    *[self._check_server(server) for server in servers],
                    return_exceptions=True
                )
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _check_server(self, server: ServerNode):
        """检查单个服务器"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{server.url}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        # 健康检查成功
                        server.response_time = response_time
                        server.last_health_check = datetime.utcnow()
                        server.health_check_failures = 0
                        
                        if server.status == ServerStatus.UNHEALTHY:
                            server.status = ServerStatus.HEALTHY
                            logger.info(f"服务器 {server.id} 恢复健康")
                    else:
                        self._handle_health_check_failure(server)
        
        except Exception as e:
            logger.warning(f"服务器 {server.id} 健康检查失败: {e}")
            self._handle_health_check_failure(server)
    
    def _handle_health_check_failure(self, server: ServerNode):
        """处理健康检查失败"""
        server.health_check_failures += 1
        
        if server.health_check_failures >= self.max_failures:
            if server.status == ServerStatus.HEALTHY:
                server.status = ServerStatus.UNHEALTHY
                logger.warning(f"服务器 {server.id} 标记为不健康")


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.servers: List[ServerNode] = []
        self.health_checker = HealthChecker()
        self._round_robin_index = 0
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
    
    async def add_server(self, server: ServerNode):
        """添加服务器"""
        self.servers.append(server)
        logger.info(f"添加服务器: {server.id} ({server.url})")
    
    async def remove_server(self, server_id: str):
        """移除服务器"""
        self.servers = [s for s in self.servers if s.id != server_id]
        logger.info(f"移除服务器: {server_id}")
    
    async def start(self):
        """启动负载均衡器"""
        await self.health_checker.start(self.servers)
        logger.info(f"负载均衡器已启动，策略: {self.strategy.value}")
    
    async def stop(self):
        """停止负载均衡器"""
        await self.health_checker.stop()
        logger.info("负载均衡器已停止")
    
    def get_available_servers(self) -> List[ServerNode]:
        """获取可用服务器列表"""
        return [server for server in self.servers if server.is_available]
    
    def select_server(self, request: Optional[Request] = None) -> Optional[ServerNode]:
        """选择服务器"""
        available_servers = self.get_available_servers()
        
        if not available_servers:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(available_servers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(available_servers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(available_servers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_LEAST_CONNECTIONS:
            return self._weighted_least_connections_select(available_servers)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_select(available_servers, request)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_select(available_servers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_select(available_servers)
        else:
            return available_servers[0]
    
    def _round_robin_select(self, servers: List[ServerNode]) -> ServerNode:
        """轮询选择"""
        server = servers[self._round_robin_index % len(servers)]
        self._round_robin_index += 1
        return server
    
    def _weighted_round_robin_select(self, servers: List[ServerNode]) -> ServerNode:
        """加权轮询选择"""
        total_weight = sum(server.weight for server in servers)
        target = self._round_robin_index % total_weight
        self._round_robin_index += 1
        
        current_weight = 0
        for server in servers:
            current_weight += server.weight
            if target < current_weight:
                return server
        
        return servers[0]
    
    def _least_connections_select(self, servers: List[ServerNode]) -> ServerNode:
        """最少连接选择"""
        return min(servers, key=lambda s: s.current_connections)
    
    def _weighted_least_connections_select(self, servers: List[ServerNode]) -> ServerNode:
        """加权最少连接选择"""
        return min(servers, key=lambda s: s.current_connections / s.weight)
    
    def _ip_hash_select(self, servers: List[ServerNode], request: Optional[Request]) -> ServerNode:
        """IP哈希选择"""
        if not request:
            return self._round_robin_select(servers)
        
        client_ip = request.client.host if request.client else "unknown"
        hash_value = hash(client_ip)
        return servers[hash_value % len(servers)]
    
    def _random_select(self, servers: List[ServerNode]) -> ServerNode:
        """随机选择"""
        return random.choice(servers)
    
    def _weighted_random_select(self, servers: List[ServerNode]) -> ServerNode:
        """加权随机选择"""
        total_weight = sum(server.weight for server in servers)
        target = random.randint(0, total_weight - 1)
        
        current_weight = 0
        for server in servers:
            current_weight += server.weight
            if target < current_weight:
                return server
        
        return servers[0]
    
    async def forward_request(
        self, 
        request: Request, 
        server: ServerNode,
        timeout: int = 30
    ) -> Response:
        """转发请求"""
        start_time = time.time()
        
        try:
            server.current_connections += 1
            server.total_requests += 1
            self._stats["total_requests"] += 1
            
            # 构建目标URL
            url = f"{server.url}{request.url.path}"
            if request.url.query:
                url += f"?{request.url.query}"
            
            # 准备请求头
            headers = dict(request.headers)
            headers.pop("host", None)  # 移除原始host头
            
            # 读取请求体
            body = await request.body()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    data=body
                ) as response:
                    content = await response.read()
                    response_time = time.time() - start_time
                    
                    # 更新服务器统计
                    server.response_time = response_time
                    self._stats["successful_requests"] += 1
                    
                    # 更新平均响应时间
                    total_time = self._stats["average_response_time"] * (self._stats["successful_requests"] - 1)
                    self._stats["average_response_time"] = (total_time + response_time) / self._stats["successful_requests"]
                    
                    return Response(
                        content=content,
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
        
        except Exception as e:
            server.failed_requests += 1
            self._stats["failed_requests"] += 1
            logger.error(f"转发请求到服务器 {server.id} 失败: {e}")
            raise HTTPException(status_code=502, detail="Bad Gateway")
        
        finally:
            server.current_connections -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "load_balancer": self._stats.copy(),
            "servers": [
                {
                    "id": server.id,
                    "url": server.url,
                    "status": server.status.value,
                    "weight": server.weight,
                    "current_connections": server.current_connections,
                    "total_requests": server.total_requests,
                    "failed_requests": server.failed_requests,
                    "success_rate": server.success_rate,
                    "response_time": server.response_time,
                    "last_health_check": server.last_health_check.isoformat() if server.last_health_check else None
                }
                for server in self.servers
            ]
        }


class LoadBalancerMiddleware(BaseHTTPMiddleware):
    """负载均衡中间件"""
    
    def __init__(self, app, load_balancer: LoadBalancer, enabled_paths: List[str] = None):
        super().__init__(app)
        self.load_balancer = load_balancer
        self.enabled_paths = enabled_paths or ["/api/"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要负载均衡
        if not any(request.url.path.startswith(path) for path in self.enabled_paths):
            return await call_next(request)
        
        # 选择服务器
        server = self.load_balancer.select_server(request)
        if not server:
            raise HTTPException(status_code=503, detail="Service Unavailable")
        
        # 转发请求
        return await self.load_balancer.forward_request(request, server)


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        """调用函数并处理熔断逻辑"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return (
            self.last_failure_time and 
            datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class RateLimiter:
    """限流器"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求"""
        now = datetime.utcnow()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # 清理过期请求
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ]
        
        # 检查是否超过限制
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """获取剩余请求数"""
        if identifier not in self.requests:
            return self.max_requests
        
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=self.time_window)
        current_requests = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ]
        
        return max(0, self.max_requests - len(current_requests))


# 全局实例
load_balancer = LoadBalancer()
rate_limiter = RateLimiter()


# 便捷函数
async def setup_load_balancer(servers_config: List[Dict[str, Any]]):
    """设置负载均衡器"""
    for server_config in servers_config:
        server = ServerNode(
            id=server_config["id"],
            host=server_config["host"],
            port=server_config["port"],
            weight=server_config.get("weight", 1)
        )
        await load_balancer.add_server(server)
    
    await load_balancer.start()
    logger.info(f"负载均衡器设置完成，共 {len(servers_config)} 个服务器")


async def get_load_balancer_stats() -> Dict[str, Any]:
    """获取负载均衡器统计信息"""
    return load_balancer.get_stats()


def create_circuit_breaker(server_id: str) -> CircuitBreaker:
    """为服务器创建熔断器"""
    return CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )