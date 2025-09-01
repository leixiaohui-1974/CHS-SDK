#!/usr/bin/env python3
"""
统一日志管理器

提供统一的日志收集、格式化和路由功能，支持：
- 多级日志等级
- 多种输出目标
- 结构化日志格式
- 异步写入和缓冲
- 日志轮转和压缩
"""

import json
import logging
import threading
import time
import gzip
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty
from abc import ABC, abstractmethod
import traceback
import psutil


class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    FATAL = 50


@dataclass
class LogRecord:
    """统一的日志记录格式"""
    timestamp: str
    level: str
    logger: str
    message: str
    context: Dict[str, Any]
    tags: List[str]
    session_id: str
    thread_id: str
    file: str
    line: int
    function: str
    exception: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=None)


class LogHandler(ABC):
    """日志处理器基类"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level
        self.filters: List[Callable[[LogRecord], bool]] = []
    
    def add_filter(self, filter_func: Callable[[LogRecord], bool]):
        """添加过滤器"""
        self.filters.append(filter_func)
    
    def should_handle(self, record: LogRecord) -> bool:
        """判断是否应该处理此日志记录"""
        # 检查日志级别
        if LogLevel[record.level].value < self.level.value:
            return False
        
        # 检查过滤器
        for filter_func in self.filters:
            if not filter_func(record):
                return False
        
        return True
    
    @abstractmethod
    def handle(self, record: LogRecord):
        """处理日志记录"""
        pass


class ConsoleHandler(LogHandler):
    """控制台输出处理器"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, colored: bool = True):
        super().__init__(level)
        self.colored = colored
        self.colors = {
            'TRACE': '\033[90m',    # 灰色
            'DEBUG': '\033[36m',    # 青色
            'INFO': '\033[32m',     # 绿色
            'WARNING': '\033[33m',  # 黄色
            'ERROR': '\033[31m',    # 红色
            'FATAL': '\033[35m',    # 紫色
            'RESET': '\033[0m'      # 重置
        }
    
    def handle(self, record: LogRecord):
        """输出到控制台"""
        if not self.should_handle(record):
            return
        
        # 格式化时间戳
        timestamp = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
        time_str = timestamp.strftime('%H:%M:%S.%f')[:-3]
        
        # 构建输出消息
        if self.colored:
            color = self.colors.get(record.level, '')
            reset = self.colors['RESET']
            output = f"{color}[{time_str}] {record.level:8} {record.logger}: {record.message}{reset}"
        else:
            output = f"[{time_str}] {record.level:8} {record.logger}: {record.message}"
        
        # 添加上下文信息
        if record.context:
            context_str = ' '.join([f"{k}={v}" for k, v in record.context.items()])
            output += f" | {context_str}"
        
        # 添加异常信息
        if record.exception:
            output += f"\n{record.exception}"
        
        print(output)


class FileHandler(LogHandler):
    """文件输出处理器"""
    
    def __init__(self, file_path: Union[str, Path], level: LogLevel = LogLevel.INFO,
                 max_size: int = 10 * 1024 * 1024, backup_count: int = 5,
                 compress: bool = True, format_type: str = 'json'):
        super().__init__(level)
        self.file_path = Path(file_path)
        self.max_size = max_size
        self.backup_count = backup_count
        self.compress = compress
        self.format_type = format_type
        self.lock = threading.Lock()
        
        # 确保目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def handle(self, record: LogRecord):
        """写入文件"""
        if not self.should_handle(record):
            return
        
        with self.lock:
            # 检查文件大小，必要时轮转
            if self.file_path.exists() and self.file_path.stat().st_size > self.max_size:
                self._rotate_file()
            
            # 格式化日志
            if self.format_type == 'json':
                log_line = record.to_json() + '\n'
            else:
                log_line = self._format_text(record) + '\n'
            
            # 写入文件
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
    
    def _format_text(self, record: LogRecord) -> str:
        """格式化为文本格式"""
        timestamp = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        output = f"[{time_str}] {record.level:8} {record.logger}: {record.message}"
        
        if record.context:
            context_str = ' '.join([f"{k}={v}" for k, v in record.context.items()])
            output += f" | {context_str}"
        
        if record.exception:
            output += f"\n{record.exception}"
        
        return output
    
    def _rotate_file(self):
        """轮转日志文件"""
        # 删除最旧的备份文件
        oldest_backup = self.file_path.with_suffix(f"{self.file_path.suffix}.{self.backup_count}")
        if self.compress:
            oldest_backup = oldest_backup.with_suffix(oldest_backup.suffix + '.gz')
        
        if oldest_backup.exists():
            oldest_backup.unlink()
        
        # 移动现有备份文件
        for i in range(self.backup_count - 1, 0, -1):
            current_backup = self.file_path.with_suffix(f"{self.file_path.suffix}.{i}")
            next_backup = self.file_path.with_suffix(f"{self.file_path.suffix}.{i + 1}")
            
            if self.compress:
                current_backup = current_backup.with_suffix(current_backup.suffix + '.gz')
                next_backup = next_backup.with_suffix(next_backup.suffix + '.gz')
            
            if current_backup.exists():
                current_backup.rename(next_backup)
        
        # 移动当前文件
        first_backup = self.file_path.with_suffix(f"{self.file_path.suffix}.1")
        if self.compress:
            # 压缩当前文件
            with open(self.file_path, 'rb') as f_in:
                with gzip.open(first_backup.with_suffix(first_backup.suffix + '.gz'), 'wb') as f_out:
                    f_out.writelines(f_in)
        else:
            self.file_path.rename(first_backup)


class DatabaseHandler(LogHandler):
    """数据库输出处理器"""
    
    def __init__(self, connection_string: str, table_name: str = 'logs',
                 level: LogLevel = LogLevel.INFO, batch_size: int = 100):
        super().__init__(level)
        self.connection_string = connection_string
        self.table_name = table_name
        self.batch_size = batch_size
        self.buffer: List[LogRecord] = []
        self.lock = threading.Lock()
        
        # 初始化数据库连接（这里使用SQLite作为示例）
        import sqlite3
        self.conn = sqlite3.connect(connection_string, check_same_thread=False)
        self._create_table()
    
    def _create_table(self):
        """创建日志表"""
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            logger TEXT NOT NULL,
            message TEXT NOT NULL,
            context TEXT,
            tags TEXT,
            session_id TEXT,
            thread_id TEXT,
            file TEXT,
            line INTEGER,
            function TEXT,
            exception TEXT
        )
        """
        self.conn.execute(create_sql)
        self.conn.commit()
    
    def handle(self, record: LogRecord):
        """写入数据库"""
        if not self.should_handle(record):
            return
        
        with self.lock:
            self.buffer.append(record)
            
            if len(self.buffer) >= self.batch_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """刷新缓冲区到数据库"""
        if not self.buffer:
            return
        
        insert_sql = f"""
        INSERT INTO {self.table_name} 
        (timestamp, level, logger, message, context, tags, session_id, 
         thread_id, file, line, function, exception)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        data = []
        for record in self.buffer:
            data.append((
                record.timestamp,
                record.level,
                record.logger,
                record.message,
                json.dumps(record.context) if record.context else None,
                json.dumps(record.tags) if record.tags else None,
                record.session_id,
                record.thread_id,
                record.file,
                record.line,
                record.function,
                record.exception
            ))
        
        self.conn.executemany(insert_sql, data)
        self.conn.commit()
        self.buffer.clear()
    
    def close(self):
        """关闭处理器"""
        with self.lock:
            self._flush_buffer()
            self.conn.close()


class LogManager:
    """统一日志管理器"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.handlers: List[LogHandler] = []
        self.async_queue: Queue = Queue()
        self.async_thread: Optional[threading.Thread] = None
        self.async_enabled = False
        self.lock = threading.Lock()
        
        # 默认添加控制台处理器
        self.add_handler(ConsoleHandler())
    
    def add_handler(self, handler: LogHandler):
        """添加日志处理器"""
        with self.lock:
            self.handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler):
        """移除日志处理器"""
        with self.lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
    
    def enable_async(self, queue_size: int = 1000):
        """启用异步日志处理"""
        if self.async_enabled:
            return
        
        self.async_queue = Queue(maxsize=queue_size)
        self.async_enabled = True
        self.async_thread = threading.Thread(target=self._async_worker, daemon=True)
        self.async_thread.start()
    
    def disable_async(self):
        """禁用异步日志处理"""
        if not self.async_enabled:
            return
        
        self.async_enabled = False
        self.async_queue.put(None)  # 发送停止信号
        if self.async_thread:
            self.async_thread.join()
    
    def _async_worker(self):
        """异步处理工作线程"""
        while self.async_enabled:
            try:
                record = self.async_queue.get(timeout=1.0)
                if record is None:  # 停止信号
                    break
                
                self._process_record(record)
                self.async_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"异步日志处理错误: {e}")
    
    def _process_record(self, record: LogRecord):
        """处理日志记录"""
        with self.lock:
            for handler in self.handlers:
                try:
                    handler.handle(record)
                except Exception as e:
                    print(f"日志处理器错误: {e}")
    
    def _create_record(self, level: str, message: str, logger: str = "root",
                      context: Optional[Dict[str, Any]] = None,
                      tags: Optional[List[str]] = None) -> LogRecord:
        """创建日志记录"""
        # 获取调用栈信息
        frame = traceback.extract_stack()[-4]  # 跳过内部调用
        
        # 获取异常信息
        exception_info = None
        if level in ['ERROR', 'FATAL']:
            exc_info = traceback.format_exc()
            if exc_info.strip() != 'NoneType: None':
                exception_info = exc_info
        
        return LogRecord(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            level=level,
            logger=logger,
            message=message,
            context=context or {},
            tags=tags or [],
            session_id=self.session_id,
            thread_id=threading.current_thread().name,
            file=frame.filename,
            line=frame.lineno,
            function=frame.name,
            exception=exception_info
        )
    
    def log(self, level: str, message: str, logger: str = "root",
            context: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None):
        """记录日志"""
        record = self._create_record(level, message, logger, context, tags)
        
        if self.async_enabled:
            try:
                self.async_queue.put_nowait(record)
            except:
                # 队列满时同步处理
                self._process_record(record)
        else:
            self._process_record(record)
    
    def trace(self, message: str, logger: str = "root", **kwargs):
        """记录TRACE级别日志"""
        self.log('TRACE', message, logger, kwargs)
    
    def debug(self, message: str, logger: str = "root", **kwargs):
        """记录DEBUG级别日志"""
        self.log('DEBUG', message, logger, kwargs)
    
    def info(self, message: str, logger: str = "root", **kwargs):
        """记录INFO级别日志"""
        self.log('INFO', message, logger, kwargs)
    
    def warning(self, message: str, logger: str = "root", **kwargs):
        """记录WARNING级别日志"""
        self.log('WARNING', message, logger, kwargs)
    
    def error(self, message: str, logger: str = "root", **kwargs):
        """记录ERROR级别日志"""
        self.log('ERROR', message, logger, kwargs)
    
    def fatal(self, message: str, logger: str = "root", **kwargs):
        """记录FATAL级别日志"""
        self.log('FATAL', message, logger, kwargs)
    
    def close(self):
        """关闭日志管理器"""
        self.disable_async()
        
        with self.lock:
            for handler in self.handlers:
                if hasattr(handler, 'close'):
                    handler.close()


# 全局日志管理器实例
_global_log_manager: Optional[LogManager] = None


def get_logger(session_id: Optional[str] = None) -> LogManager:
    """获取全局日志管理器实例"""
    global _global_log_manager
    
    if _global_log_manager is None:
        _global_log_manager = LogManager(session_id)
    
    return _global_log_manager


def setup_logging(config: Dict[str, Any]):
    """根据配置设置日志系统"""
    logger = get_logger(config.get('session_id'))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 添加控制台处理器
    if config.get('console', {}).get('enabled', True):
        console_config = config.get('console', {})
        handler = ConsoleHandler(
            level=LogLevel[console_config.get('level', 'INFO')],
            colored=console_config.get('colored', True)
        )
        logger.add_handler(handler)
    
    # 添加文件处理器
    if config.get('file', {}).get('enabled', False):
        file_config = config.get('file', {})
        handler = FileHandler(
            file_path=file_config.get('path', 'debug.log'),
            level=LogLevel[file_config.get('level', 'DEBUG')],
            max_size=file_config.get('max_size', 10 * 1024 * 1024),
            backup_count=file_config.get('backup_count', 5),
            compress=file_config.get('compress', True),
            format_type=file_config.get('format', 'json')
        )
        logger.add_handler(handler)
    
    # 添加数据库处理器
    if config.get('database', {}).get('enabled', False):
        db_config = config.get('database', {})
        handler = DatabaseHandler(
            connection_string=db_config.get('connection', 'debug.db'),
            table_name=db_config.get('table', 'logs'),
            level=LogLevel[db_config.get('level', 'INFO')],
            batch_size=db_config.get('batch_size', 100)
        )
        logger.add_handler(handler)
    
    # 启用异步处理
    if config.get('async', {}).get('enabled', True):
        logger.enable_async(config.get('async', {}).get('queue_size', 1000))
    
    return logger


# 便捷函数
def trace(message: str, logger: str = "root", **kwargs):
    """记录TRACE级别日志"""
    get_logger().trace(message, logger, **kwargs)


def debug(message: str, logger: str = "root", **kwargs):
    """记录DEBUG级别日志"""
    get_logger().debug(message, logger, **kwargs)


def info(message: str, logger: str = "root", **kwargs):
    """记录INFO级别日志"""
    get_logger().info(message, logger, **kwargs)


def warning(message: str, logger: str = "root", **kwargs):
    """记录WARNING级别日志"""
    get_logger().warning(message, logger, **kwargs)


def error(message: str, logger: str = "root", **kwargs):
    """记录ERROR级别日志"""
    get_logger().error(message, logger, **kwargs)


def fatal(message: str, logger: str = "root", **kwargs):
    """记录FATAL级别日志"""
    get_logger().fatal(message, logger, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import tempfile
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    # 配置日志系统
    config = {
        'session_id': 'test_session',
        'console': {
            'enabled': True,
            'level': 'DEBUG',
            'colored': True
        },
        'file': {
            'enabled': True,
            'path': temp_dir / 'test.log',
            'level': 'TRACE',
            'format': 'json'
        },
        'async': {
            'enabled': True,
            'queue_size': 100
        }
    }
    
    logger = setup_logging(config)
    
    # 测试各种日志级别
    logger.trace("这是一条跟踪日志", "test.module", user_id=123, action="login")
    logger.debug("这是一条调试日志", "test.module", query="SELECT * FROM users")
    logger.info("这是一条信息日志", "test.module", status="success")
    logger.warning("这是一条警告日志", "test.module", memory_usage=85.5)
    logger.error("这是一条错误日志", "test.module", error_code=500)
    
    # 测试异常日志
    try:
        1 / 0
    except:
        logger.fatal("这是一条致命错误日志", "test.module", operation="division")
    
    # 等待异步处理完成
    time.sleep(1)
    
    # 关闭日志系统
    logger.close()
    
    print(f"\n日志文件已保存到: {temp_dir / 'test.log'}")
    
    # 显示日志文件内容
    if (temp_dir / 'test.log').exists():
        print("\n日志文件内容:")
        with open(temp_dir / 'test.log', 'r', encoding='utf-8') as f:
            for line in f:
                print(line.strip())


# 全局日志管理器实例
_global_log_manager = None


def get_log_manager(session_id: str = None) -> LogManager:
    """获取全局日志管理器实例"""
    global _global_log_manager
    if _global_log_manager is None:
        _global_log_manager = LogManager(session_id or "default")
    return _global_log_manager


def setup_logging(config: Dict[str, Any] = None) -> LogManager:
    """设置日志系统"""
    global _global_log_manager
    
    if config is None:
        config = {
            'level': 'INFO',
            'handlers': {
                'console': {
                    'type': 'console',
                    'level': 'INFO'
                }
            }
        }
    
    _global_log_manager = LogManager()
    
    # 配置处理器
    for name, handler_config in config.get('handlers', {}).items():
        handler_type = handler_config.get('type', 'console')
        level = LogLevel[handler_config.get('level', 'INFO').upper()]
        
        if handler_type == 'console':
            handler = ConsoleHandler(level)
        elif handler_type == 'file':
            file_path = handler_config.get('file', 'debug.log')
            handler = FileHandler(file_path, level)
        elif handler_type == 'database':
            db_path = handler_config.get('database', 'debug.db')
            handler = DatabaseHandler(db_path, level)
        else:
            continue
        
        _global_log_manager.add_handler(handler)
    
    return _global_log_manager