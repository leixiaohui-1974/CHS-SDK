"""数据库优化模块

提供数据库连接池、查询优化、索引管理等功能。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from .config import settings
from .database import get_db_session

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.engine = None
        self.connection_pool = None
        self._stats = {
            "queries_executed": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self):
        """初始化数据库优化器"""
        # 创建优化的数据库引擎
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,  # 连接池大小
            max_overflow=30,  # 最大溢出连接数
            pool_pre_ping=True,  # 连接前ping检查
            pool_recycle=3600,  # 连接回收时间（秒）
            echo=settings.DEBUG,  # 是否打印SQL
            echo_pool=settings.DEBUG,  # 是否打印连接池信息
            connect_args={
                "server_settings": {
                    "application_name": "chs_simulation_api",
                    "jit": "off",  # 关闭JIT以提高小查询性能
                }
            }
        )
        
        logger.info("数据库优化器初始化完成")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    
    async def analyze_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """分析慢查询"""
        async with get_db_session() as session:
            try:
                # 启用pg_stat_statements扩展（如果未启用）
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                
                # 查询慢查询统计
                query = text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY mean_time DESC 
                    LIMIT :limit
                """)
                
                result = await session.execute(query, {"limit": limit})
                return [
                    {
                        "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                        "calls": row.calls,
                        "total_time": round(row.total_time, 2),
                        "mean_time": round(row.mean_time, 2),
                        "rows": row.rows,
                        "hit_percent": round(row.hit_percent or 0, 2)
                    }
                    for row in result
                ]
            except Exception as e:
                logger.error(f"分析慢查询失败: {e}")
                return []
    
    async def get_table_stats(self) -> List[Dict[str, Any]]:
        """获取表统计信息"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, attname
                """)
                
                result = await session.execute(query)
                return [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "column": row.attname,
                        "distinct_values": row.n_distinct,
                        "correlation": row.correlation
                    }
                    for row in result
                ]
            except Exception as e:
                logger.error(f"获取表统计信息失败: {e}")
                return []
    
    async def get_index_usage(self) -> List[Dict[str, Any]]:
        """获取索引使用情况"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch,
                        idx_scan
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_scan DESC
                """)
                
                result = await session.execute(query)
                return [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch,
                        "scans": row.idx_scan
                    }
                    for row in result
                ]
            except Exception as e:
                logger.error(f"获取索引使用情况失败: {e}")
                return []
    
    async def suggest_indexes(self) -> List[Dict[str, Any]]:
        """建议创建的索引"""
        suggestions = []
        
        async with get_db_session() as session:
            try:
                # 查找缺少索引的外键
                query = text("""
                    SELECT 
                        conrelid::regclass AS table_name,
                        conname AS constraint_name,
                        pg_get_constraintdef(c.oid) AS constraint_def
                    FROM pg_constraint c 
                    WHERE contype = 'f' 
                    AND NOT EXISTS (
                        SELECT 1 FROM pg_index i 
                        WHERE i.indrelid = c.conrelid 
                        AND i.indkey::int2[] <@ c.conkey::int2[]
                    )
                """)
                
                result = await session.execute(query)
                for row in result:
                    suggestions.append({
                        "type": "foreign_key_index",
                        "table": str(row.table_name),
                        "constraint": row.constraint_name,
                        "definition": row.constraint_def,
                        "priority": "high"
                    })
                
                # 查找经常查询但没有索引的列
                # 这需要分析查询日志，这里提供一个示例
                common_queries = [
                    {"table": "simulation_sessions", "column": "status", "priority": "medium"},
                    {"table": "simulation_sessions", "column": "created_at", "priority": "medium"},
                    {"table": "simulation_results", "column": "session_id", "priority": "high"},
                    {"table": "users", "column": "email", "priority": "high"},
                    {"table": "users", "column": "is_active", "priority": "low"}
                ]
                
                for query_info in common_queries:
                    suggestions.append({
                        "type": "query_optimization_index",
                        "table": query_info["table"],
                        "column": query_info["column"],
                        "priority": query_info["priority"]
                    })
                
            except Exception as e:
                logger.error(f"生成索引建议失败: {e}")
        
        return suggestions
    
    async def optimize_table(self, table_name: str) -> Dict[str, Any]:
        """优化表"""
        async with get_db_session() as session:
            try:
                # 更新表统计信息
                await session.execute(text(f"ANALYZE {table_name}"))
                
                # 获取表大小信息
                size_query = text("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                        pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                        pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) as index_size
                """)
                
                result = await session.execute(size_query, {"table_name": table_name})
                row = result.first()
                
                return {
                    "table": table_name,
                    "total_size": row.total_size,
                    "table_size": row.table_size,
                    "index_size": row.index_size,
                    "optimized_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"优化表 {table_name} 失败: {e}")
                return {"error": str(e)}
    
    async def vacuum_analyze_all(self) -> Dict[str, Any]:
        """对所有表执行VACUUM ANALYZE"""
        async with get_db_session() as session:
            try:
                # 获取所有用户表
                tables_query = text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                
                result = await session.execute(tables_query)
                tables = [row.tablename for row in result]
                
                optimized_tables = []
                for table in tables:
                    try:
                        await session.execute(text(f"VACUUM ANALYZE {table}"))
                        optimized_tables.append(table)
                    except Exception as e:
                        logger.error(f"优化表 {table} 失败: {e}")
                
                return {
                    "optimized_tables": optimized_tables,
                    "total_tables": len(tables),
                    "optimized_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"批量优化表失败: {e}")
                return {"error": str(e)}


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    async def explain_query(query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析查询执行计划"""
        async with get_db_session() as session:
            try:
                explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
                result = await session.execute(explain_query, params or {})
                plan = result.scalar()
                return plan[0] if plan else {}
            except Exception as e:
                logger.error(f"分析查询执行计划失败: {e}")
                return {"error": str(e)}
    
    @staticmethod
    async def get_query_performance(query_hash: str) -> Optional[Dict[str, Any]]:
        """获取查询性能统计"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        min_time,
                        max_time,
                        stddev_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE queryid = :query_hash
                """)
                
                result = await session.execute(query, {"query_hash": query_hash})
                row = result.first()
                
                if row:
                    return {
                        "query": row.query,
                        "calls": row.calls,
                        "total_time": row.total_time,
                        "mean_time": row.mean_time,
                        "min_time": row.min_time,
                        "max_time": row.max_time,
                        "stddev_time": row.stddev_time,
                        "rows": row.rows
                    }
                return None
            except Exception as e:
                logger.error(f"获取查询性能统计失败: {e}")
                return None


class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self):
        self.pools: Dict[str, asyncpg.Pool] = {}
    
    async def create_pool(
        self, 
        name: str, 
        dsn: str, 
        min_size: int = 10, 
        max_size: int = 20
    ) -> asyncpg.Pool:
        """创建连接池"""
        try:
            pool = await asyncpg.create_pool(
                dsn,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
                server_settings={
                    'application_name': 'chs_simulation_api',
                    'jit': 'off'
                }
            )
            self.pools[name] = pool
            logger.info(f"连接池 {name} 创建成功")
            return pool
        except Exception as e:
            logger.error(f"创建连接池 {name} 失败: {e}")
            raise
    
    async def get_pool(self, name: str) -> Optional[asyncpg.Pool]:
        """获取连接池"""
        return self.pools.get(name)
    
    async def close_pool(self, name: str):
        """关闭连接池"""
        if name in self.pools:
            await self.pools[name].close()
            del self.pools[name]
            logger.info(f"连接池 {name} 已关闭")
    
    async def close_all_pools(self):
        """关闭所有连接池"""
        for name in list(self.pools.keys()):
            await self.close_pool(name)
    
    @asynccontextmanager
    async def acquire_connection(self, pool_name: str):
        """获取数据库连接"""
        pool = self.pools.get(pool_name)
        if not pool:
            raise ValueError(f"连接池 {pool_name} 不存在")
        
        async with pool.acquire() as connection:
            yield connection


class DatabaseMonitor:
    """数据库监控器"""
    
    @staticmethod
    async def get_database_size() -> Dict[str, Any]:
        """获取数据库大小信息"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        pg_database.datname,
                        pg_size_pretty(pg_database_size(pg_database.datname)) AS size,
                        pg_database_size(pg_database.datname) AS size_bytes
                    FROM pg_database
                    WHERE pg_database.datname = current_database()
                """)
                
                result = await session.execute(query)
                row = result.first()
                
                return {
                    "database_name": row.datname,
                    "size": row.size,
                    "size_bytes": row.size_bytes
                }
            except Exception as e:
                logger.error(f"获取数据库大小失败: {e}")
                return {}
    
    @staticmethod
    async def get_active_connections() -> List[Dict[str, Any]]:
        """获取活跃连接信息"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query_start,
                        state_change,
                        query
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                    AND pid != pg_backend_pid()
                """)
                
                result = await session.execute(query)
                return [
                    {
                        "pid": row.pid,
                        "username": row.usename,
                        "application": row.application_name,
                        "client_addr": str(row.client_addr) if row.client_addr else None,
                        "state": row.state,
                        "query_start": row.query_start.isoformat() if row.query_start else None,
                        "state_change": row.state_change.isoformat() if row.state_change else None,
                        "query": row.query[:100] + "..." if len(row.query) > 100 else row.query
                    }
                    for row in result
                ]
            except Exception as e:
                logger.error(f"获取活跃连接失败: {e}")
                return []
    
    @staticmethod
    async def get_lock_info() -> List[Dict[str, Any]]:
        """获取锁信息"""
        async with get_db_session() as session:
            try:
                query = text("""
                    SELECT 
                        l.pid,
                        l.mode,
                        l.locktype,
                        l.granted,
                        a.usename,
                        a.query,
                        a.query_start
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON l.pid = a.pid
                    WHERE NOT l.granted
                """)
                
                result = await session.execute(query)
                return [
                    {
                        "pid": row.pid,
                        "mode": row.mode,
                        "locktype": row.locktype,
                        "granted": row.granted,
                        "username": row.usename,
                        "query": row.query[:100] + "..." if len(row.query) > 100 else row.query,
                        "query_start": row.query_start.isoformat() if row.query_start else None
                    }
                    for row in result
                ]
            except Exception as e:
                logger.error(f"获取锁信息失败: {e}")
                return []


# 全局实例
db_optimizer = DatabaseOptimizer()
query_optimizer = QueryOptimizer()
pool_manager = ConnectionPoolManager()
db_monitor = DatabaseMonitor()


# 便捷函数
async def optimize_database():
    """优化数据库"""
    return await db_optimizer.vacuum_analyze_all()


async def get_db_stats() -> Dict[str, Any]:
    """获取数据库统计信息"""
    return {
        "connection_stats": await db_optimizer.get_connection_stats(),
        "slow_queries": await db_optimizer.analyze_slow_queries(),
        "database_size": await db_monitor.get_database_size(),
        "active_connections": await db_monitor.get_active_connections(),
        "locks": await db_monitor.get_lock_info()
    }


async def suggest_optimizations() -> Dict[str, Any]:
    """建议优化方案"""
    return {
        "index_suggestions": await db_optimizer.suggest_indexes(),
        "slow_queries": await db_optimizer.analyze_slow_queries(5),
        "table_stats": await db_optimizer.get_table_stats(),
        "index_usage": await db_optimizer.get_index_usage()
    }