#!/usr/bin/env python3
"""
调试数据收集器

自动收集各种调试信息，包括：
- 仿真状态和参数
- 性能指标和统计
- 系统资源使用情况
- 错误和异常信息
- 用户操作和事件
"""

import json
import time
import threading
import psutil
import traceback
import inspect
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union, Type
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import weakref
import gc
import sys
import os

from .log_manager import get_logger, LogLevel


class DataType(Enum):
    """数据类型枚举"""
    SIMULATION_STATE = "simulation_state"
    PERFORMANCE_METRIC = "performance_metric"
    SYSTEM_RESOURCE = "system_resource"
    ERROR_INFO = "error_info"
    USER_EVENT = "user_event"
    FUNCTION_CALL = "function_call"
    VARIABLE_STATE = "variable_state"
    NETWORK_IO = "network_io"
    FILE_IO = "file_io"
    CUSTOM = "custom"


@dataclass
class DebugData:
    """调试数据记录"""
    timestamp: str
    data_type: str
    source: str
    name: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    thread_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class DataCollector:
    """数据收集器基类"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.session_id = ""
        self.callbacks: List[Callable[[DebugData], None]] = []
    
    def add_callback(self, callback: Callable[[DebugData], None]):
        """添加数据回调函数"""
        self.callbacks.append(callback)
    
    def collect(self) -> List[DebugData]:
        """收集数据（子类实现）"""
        return []
    
    def _create_data(self, data_type: DataType, name: str, value: Any,
                    source: str = None, **metadata) -> DebugData:
        """创建调试数据记录"""
        return DebugData(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            data_type=data_type.value,
            source=source or self.name,
            name=name,
            value=value,
            metadata=metadata,
            session_id=self.session_id,
            thread_id=threading.current_thread().name
        )
    
    def _notify_callbacks(self, data: DebugData):
        """通知回调函数"""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                get_logger().error(f"数据收集器回调错误: {e}", "debug_collector")


class SystemResourceCollector(DataCollector):
    """系统资源收集器"""
    
    def __init__(self, interval: float = 1.0):
        super().__init__("system_resource")
        self.interval = interval
        self.process = psutil.Process()
    
    def collect(self) -> List[DebugData]:
        """收集系统资源信息"""
        if not self.enabled:
            return []
        
        data_list = []
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            data_list.append(self._create_data(
                DataType.SYSTEM_RESOURCE, "cpu_percent", cpu_percent,
                unit="%", category="cpu"
            ))
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            data_list.append(self._create_data(
                DataType.SYSTEM_RESOURCE, "memory_percent", memory.percent,
                unit="%", category="memory", total=memory.total, available=memory.available
            ))
            
            # 进程内存使用
            process_memory = self.process.memory_info()
            data_list.append(self._create_data(
                DataType.SYSTEM_RESOURCE, "process_memory_rss", process_memory.rss,
                unit="bytes", category="process", vms=process_memory.vms
            ))
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            data_list.append(self._create_data(
                DataType.SYSTEM_RESOURCE, "disk_percent", disk.percent,
                unit="%", category="disk", total=disk.total, free=disk.free
            ))
            
            # 网络IO
            net_io = psutil.net_io_counters()
            if net_io:
                data_list.append(self._create_data(
                    DataType.NETWORK_IO, "bytes_sent", net_io.bytes_sent,
                    unit="bytes", category="network"
                ))
                data_list.append(self._create_data(
                    DataType.NETWORK_IO, "bytes_recv", net_io.bytes_recv,
                    unit="bytes", category="network"
                ))
            
            # 文件描述符数量
            try:
                num_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
                data_list.append(self._create_data(
                    DataType.SYSTEM_RESOURCE, "num_file_descriptors", num_fds,
                    category="process"
                ))
            except:
                pass
            
        except Exception as e:
            get_logger().error(f"系统资源收集错误: {e}", "debug_collector")
        
        return data_list


class PerformanceCollector(DataCollector):
    """性能指标收集器"""
    
    def __init__(self):
        super().__init__("performance")
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.timers: Dict[str, float] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    def start_timer(self, name: str):
        """开始计时"""
        with self.lock:
            self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """结束计时并记录"""
        with self.lock:
            if name in self.timers:
                duration = time.time() - self.timers[name]
                del self.timers[name]
                
                # 记录性能数据
                data = self._create_data(
                    DataType.PERFORMANCE_METRIC, f"timer_{name}", duration,
                    unit="seconds", category="timing"
                )
                self._notify_callbacks(data)
                
                # 保存到历史记录
                self.metrics[f"timer_{name}"].append({
                    'timestamp': time.time(),
                    'value': duration
                })
                
                return duration
            return 0.0
    
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        with self.lock:
            self.counters[name] += value
            
            # 记录计数数据
            data = self._create_data(
                DataType.PERFORMANCE_METRIC, f"counter_{name}", self.counters[name],
                category="counter", increment=value
            )
            self._notify_callbacks(data)
    
    def record_metric(self, name: str, value: float, unit: str = "", **metadata):
        """记录自定义指标"""
        with self.lock:
            # 记录指标数据
            data = self._create_data(
                DataType.PERFORMANCE_METRIC, name, value,
                unit=unit, category="custom", **metadata
            )
            self._notify_callbacks(data)
            
            # 保存到历史记录
            self.metrics[name].append({
                'timestamp': time.time(),
                'value': value
            })
    
    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """获取指标统计信息"""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return {}
            
            values = [item['value'] for item in self.metrics[name]]
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1]
            }
    
    def collect(self) -> List[DebugData]:
        """收集性能统计信息"""
        if not self.enabled:
            return []
        
        data_list = []
        
        with self.lock:
            # 收集计数器信息
            for name, value in self.counters.items():
                data_list.append(self._create_data(
                    DataType.PERFORMANCE_METRIC, f"counter_{name}_total", value,
                    category="counter_summary"
                ))
            
            # 收集指标统计信息
            for name, history in self.metrics.items():
                if history:
                    stats = self.get_metric_stats(name)
                    data_list.append(self._create_data(
                        DataType.PERFORMANCE_METRIC, f"{name}_stats", stats,
                        category="metric_summary"
                    ))
        
        return data_list


class FunctionCallCollector(DataCollector):
    """函数调用收集器"""
    
    def __init__(self, max_calls: int = 1000):
        super().__init__("function_call")
        self.max_calls = max_calls
        self.call_history: deque = deque(maxlen=max_calls)
        self.call_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0, 'total_time': 0.0, 'avg_time': 0.0, 'errors': 0
        })
        self.lock = threading.Lock()
    
    def trace_function(self, func: Callable) -> Callable:
        """装饰器：跟踪函数调用"""
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()
            
            # 记录调用开始
            call_data = {
                'function': func_name,
                'args_count': len(args),
                'kwargs_count': len(kwargs),
                'start_time': start_time,
                'thread': threading.current_thread().name
            }
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                
                # 记录成功调用
                call_data.update({
                    'end_time': end_time,
                    'duration': duration,
                    'status': 'success',
                    'result_type': type(result).__name__
                })
                
                # 更新统计信息
                with self.lock:
                    stats = self.call_stats[func_name]
                    stats['count'] += 1
                    stats['total_time'] += duration
                    stats['avg_time'] = stats['total_time'] / stats['count']
                    
                    self.call_history.append(call_data)
                
                # 通知回调
                data = self._create_data(
                    DataType.FUNCTION_CALL, func_name, call_data,
                    duration=duration, status="success"
                )
                self._notify_callbacks(data)
                
                return result
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                # 记录异常调用
                call_data.update({
                    'end_time': end_time,
                    'duration': duration,
                    'status': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                
                # 更新统计信息
                with self.lock:
                    stats = self.call_stats[func_name]
                    stats['count'] += 1
                    stats['errors'] += 1
                    stats['total_time'] += duration
                    stats['avg_time'] = stats['total_time'] / stats['count']
                    
                    self.call_history.append(call_data)
                
                # 通知回调
                data = self._create_data(
                    DataType.FUNCTION_CALL, func_name, call_data,
                    duration=duration, status="error", error=str(e)
                )
                self._notify_callbacks(data)
                
                raise
        
        return wrapper
    
    def get_call_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取函数调用统计"""
        with self.lock:
            return dict(self.call_stats)
    
    def collect(self) -> List[DebugData]:
        """收集函数调用统计信息"""
        if not self.enabled:
            return []
        
        data_list = []
        
        with self.lock:
            for func_name, stats in self.call_stats.items():
                data_list.append(self._create_data(
                    DataType.FUNCTION_CALL, f"{func_name}_stats", stats,
                    category="call_summary"
                ))
        
        return data_list


class VariableStateCollector(DataCollector):
    """变量状态收集器"""
    
    def __init__(self, max_snapshots: int = 100):
        super().__init__("variable_state")
        self.max_snapshots = max_snapshots
        self.watched_objects: Dict[str, weakref.ref] = {}
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.lock = threading.Lock()
    
    def watch_object(self, obj: Any, name: str):
        """监视对象状态变化"""
        with self.lock:
            self.watched_objects[name] = weakref.ref(obj)
    
    def unwatch_object(self, name: str):
        """停止监视对象"""
        with self.lock:
            if name in self.watched_objects:
                del self.watched_objects[name]
    
    def take_snapshot(self, context: str = ""):
        """拍摄变量状态快照"""
        snapshot = {
            'timestamp': time.time(),
            'context': context,
            'variables': {},
            'memory_usage': psutil.Process().memory_info().rss
        }
        
        with self.lock:
            # 收集监视对象的状态
            for name, obj_ref in list(self.watched_objects.items()):
                obj = obj_ref()
                if obj is None:
                    # 对象已被垃圾回收
                    del self.watched_objects[name]
                    continue
                
                try:
                    # 尝试序列化对象状态
                    if hasattr(obj, '__dict__'):
                        state = {k: str(v) for k, v in obj.__dict__.items()}
                    else:
                        state = str(obj)
                    
                    snapshot['variables'][name] = {
                        'type': type(obj).__name__,
                        'state': state,
                        'id': id(obj)
                    }
                except Exception as e:
                    snapshot['variables'][name] = {
                        'type': type(obj).__name__,
                        'error': str(e),
                        'id': id(obj)
                    }
            
            self.snapshots.append(snapshot)
        
        # 通知回调
        data = self._create_data(
            DataType.VARIABLE_STATE, "snapshot", snapshot,
            context=context, variable_count=len(snapshot['variables'])
        )
        self._notify_callbacks(data)
    
    def get_snapshots(self, limit: int = None) -> List[Dict[str, Any]]:
        """获取变量快照历史"""
        with self.lock:
            snapshots = list(self.snapshots)
            if limit:
                snapshots = snapshots[-limit:]
            return snapshots
    
    def collect(self) -> List[DebugData]:
        """收集变量状态信息"""
        if not self.enabled:
            return []
        
        # 自动拍摄快照
        self.take_snapshot("auto_collect")
        
        return []


class ErrorCollector(DataCollector):
    """错误信息收集器"""
    
    def __init__(self, max_errors: int = 500):
        super().__init__("error")
        self.max_errors = max_errors
        self.error_history: deque = deque(maxlen=max_errors)
        self.error_stats: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # 安装异常钩子
        self.original_excepthook = sys.excepthook
        sys.excepthook = self._exception_hook
    
    def _exception_hook(self, exc_type, exc_value, exc_traceback):
        """全局异常钩子"""
        self.record_error(exc_type, exc_value, exc_traceback)
        
        # 调用原始异常钩子
        self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def record_error(self, exc_type: Type[Exception], exc_value: Exception,
                    exc_traceback, context: str = ""):
        """记录错误信息"""
        error_info = {
            'timestamp': time.time(),
            'type': exc_type.__name__,
            'message': str(exc_value),
            'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback),
            'context': context,
            'thread': threading.current_thread().name
        }
        
        with self.lock:
            self.error_history.append(error_info)
            self.error_stats[exc_type.__name__] += 1
        
        # 通知回调
        data = self._create_data(
            DataType.ERROR_INFO, exc_type.__name__, error_info,
            context=context, message=str(exc_value)
        )
        self._notify_callbacks(data)
        
        # 记录到日志
        get_logger().error(
            f"捕获异常: {exc_type.__name__}: {exc_value}",
            "error_collector",
            context=context,
            traceback=''.join(error_info['traceback'])
        )
    
    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        with self.lock:
            return dict(self.error_stats)
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        with self.lock:
            errors = list(self.error_history)
            return errors[-limit:] if limit else errors
    
    def collect(self) -> List[DebugData]:
        """收集错误统计信息"""
        if not self.enabled:
            return []
        
        data_list = []
        
        with self.lock:
            # 收集错误统计
            for error_type, count in self.error_stats.items():
                data_list.append(self._create_data(
                    DataType.ERROR_INFO, f"{error_type}_count", count,
                    category="error_summary"
                ))
        
        return data_list
    
    def close(self):
        """关闭收集器"""
        # 恢复原始异常钩子
        sys.excepthook = self.original_excepthook


class DebugCollectorManager:
    """调试数据收集器管理器"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"debug_session_{int(time.time())}"
        self.collectors: Dict[str, DataCollector] = {}
        self.data_handlers: List[Callable[[DebugData], None]] = []
        self.auto_collect_interval = 5.0
        self.auto_collect_thread: Optional[threading.Thread] = None
        self.auto_collect_enabled = False
        self.lock = threading.Lock()
        
        # 默认添加基础收集器
        self.add_collector(SystemResourceCollector())
        self.add_collector(PerformanceCollector())
        self.add_collector(FunctionCallCollector())
        self.add_collector(VariableStateCollector())
        self.add_collector(ErrorCollector())
    
    def add_collector(self, collector: DataCollector):
        """添加数据收集器"""
        collector.session_id = self.session_id
        collector.add_callback(self._handle_data)
        
        with self.lock:
            self.collectors[collector.name] = collector
    
    def remove_collector(self, name: str):
        """移除数据收集器"""
        with self.lock:
            if name in self.collectors:
                collector = self.collectors[name]
                if hasattr(collector, 'close'):
                    collector.close()
                del self.collectors[name]
    
    def get_collector(self, name: str) -> Optional[DataCollector]:
        """获取数据收集器"""
        return self.collectors.get(name)
    
    def add_data_handler(self, handler: Callable[[DebugData], None]):
        """添加数据处理器"""
        self.data_handlers.append(handler)
    
    def _handle_data(self, data: DebugData):
        """处理收集到的数据"""
        for handler in self.data_handlers:
            try:
                handler(data)
            except Exception as e:
                get_logger().error(f"数据处理器错误: {e}", "debug_collector")
    
    def start_auto_collect(self, interval: float = 5.0):
        """启动自动收集"""
        if self.auto_collect_enabled:
            return
        
        self.auto_collect_interval = interval
        self.auto_collect_enabled = True
        self.auto_collect_thread = threading.Thread(
            target=self._auto_collect_worker, daemon=True
        )
        self.auto_collect_thread.start()
        
        get_logger().info(
            f"启动自动数据收集，间隔: {interval}秒",
            "debug_collector",
            session_id=self.session_id
        )
    
    def stop_auto_collect(self):
        """停止自动收集"""
        if not self.auto_collect_enabled:
            return
        
        self.auto_collect_enabled = False
        if self.auto_collect_thread:
            self.auto_collect_thread.join()
        
        get_logger().info("停止自动数据收集", "debug_collector")
    
    def _auto_collect_worker(self):
        """自动收集工作线程"""
        while self.auto_collect_enabled:
            try:
                self.collect_all()
                time.sleep(self.auto_collect_interval)
            except Exception as e:
                get_logger().error(f"自动收集错误: {e}", "debug_collector")
                time.sleep(1.0)
    
    def collect_all(self) -> List[DebugData]:
        """收集所有数据"""
        all_data = []
        
        with self.lock:
            for collector in self.collectors.values():
                if collector.enabled:
                    try:
                        data_list = collector.collect()
                        all_data.extend(data_list)
                    except Exception as e:
                        get_logger().error(
                            f"收集器 {collector.name} 错误: {e}",
                            "debug_collector"
                        )
        
        return all_data
    
    def get_performance_collector(self) -> Optional[PerformanceCollector]:
        """获取性能收集器"""
        return self.get_collector("performance")
    
    def get_function_collector(self) -> Optional[FunctionCallCollector]:
        """获取函数调用收集器"""
        return self.get_collector("function_call")
    
    def get_variable_collector(self) -> Optional[VariableStateCollector]:
        """获取变量状态收集器"""
        return self.get_collector("variable_state")
    
    def get_error_collector(self) -> Optional[ErrorCollector]:
        """获取错误收集器"""
        return self.get_collector("error")
    
    def close(self):
        """关闭管理器"""
        self.stop_auto_collect()
        
        with self.lock:
            for collector in self.collectors.values():
                if hasattr(collector, 'close'):
                    collector.close()
            self.collectors.clear()


# 全局收集器管理器实例
_global_collector_manager: Optional[DebugCollectorManager] = None


def get_collector_manager(session_id: str = None) -> DebugCollectorManager:
    """获取全局收集器管理器实例"""
    global _global_collector_manager
    
    if _global_collector_manager is None:
        _global_collector_manager = DebugCollectorManager(session_id)
    
    return _global_collector_manager


# 便捷函数
def start_timer(name: str):
    """开始计时"""
    perf_collector = get_collector_manager().get_performance_collector()
    if perf_collector:
        perf_collector.start_timer(name)


def end_timer(name: str) -> float:
    """结束计时"""
    perf_collector = get_collector_manager().get_performance_collector()
    if perf_collector:
        return perf_collector.end_timer(name)
    return 0.0


def record_metric(name: str, value: float, unit: str = "", **metadata):
    """记录性能指标"""
    perf_collector = get_collector_manager().get_performance_collector()
    if perf_collector:
        perf_collector.record_metric(name, value, unit, **metadata)


def increment_counter(name: str, value: int = 1):
    """增加计数器"""
    perf_collector = get_collector_manager().get_performance_collector()
    if perf_collector:
        perf_collector.increment_counter(name, value)


def trace_function(func: Callable) -> Callable:
    """装饰器：跟踪函数调用"""
    func_collector = get_collector_manager().get_function_collector()
    if func_collector:
        return func_collector.trace_function(func)
    return func


def watch_variable(obj: Any, name: str):
    """监视变量状态"""
    var_collector = get_collector_manager().get_variable_collector()
    if var_collector:
        var_collector.watch_object(obj, name)


def take_snapshot(context: str = ""):
    """拍摄变量状态快照"""
    var_collector = get_collector_manager().get_variable_collector()
    if var_collector:
        var_collector.take_snapshot(context)


if __name__ == "__main__":
    # 测试代码
    import tempfile
    from .log_manager import setup_logging
    
    # 设置日志
    temp_dir = Path(tempfile.mkdtemp())
    log_config = {
        'session_id': 'test_debug_session',
        'console': {'enabled': True, 'level': 'DEBUG'},
        'file': {
            'enabled': True,
            'path': temp_dir / 'debug_test.log',
            'level': 'TRACE'
        }
    }
    setup_logging(log_config)
    
    # 创建收集器管理器
    manager = get_collector_manager('test_debug_session')
    
    # 添加数据处理器
    def data_handler(data: DebugData):
        print(f"收集到数据: {data.data_type} - {data.name} = {data.value}")
    
    manager.add_data_handler(data_handler)
    
    # 启动自动收集
    manager.start_auto_collect(2.0)
    
    # 测试性能收集
    @trace_function
    def test_function(x, y):
        time.sleep(0.1)
        return x + y
    
    # 测试计时器
    start_timer("test_operation")
    result = test_function(1, 2)
    duration = end_timer("test_operation")
    
    # 测试指标记录
    record_metric("test_metric", 42.5, "units")
    increment_counter("test_counter")
    
    # 测试变量监视
    test_obj = {'value': 100, 'name': 'test'}
    watch_variable(test_obj, "test_object")
    take_snapshot("initial_state")
    
    test_obj['value'] = 200
    take_snapshot("after_change")
    
    # 测试错误收集
    try:
        1 / 0
    except:
        pass
    
    # 等待收集
    time.sleep(3)
    
    # 获取统计信息
    perf_collector = manager.get_performance_collector()
    if perf_collector:
        print("\n性能统计:")
        stats = perf_collector.get_metric_stats("timer_test_operation")
        print(f"计时器统计: {stats}")
    
    func_collector = manager.get_function_collector()
    if func_collector:
        print("\n函数调用统计:")
        call_stats = func_collector.get_call_stats()
        for func_name, stats in call_stats.items():
            print(f"{func_name}: {stats}")
    
    error_collector = manager.get_error_collector()
    if error_collector:
        print("\n错误统计:")
        error_stats = error_collector.get_error_stats()
        print(f"错误统计: {error_stats}")
    
    # 关闭管理器
    manager.close()
    
    print(f"\n调试日志已保存到: {temp_dir / 'debug_test.log'}")


# 全局便捷函数
def collect_debug_data(data_type: str, name: str, value: Any, metadata: Dict[str, Any] = None, source: str = "manual"):
    """收集调试数据的便捷函数"""
    manager = get_collector_manager()
    data = DebugData(
        timestamp=datetime.utcnow().isoformat() + 'Z',
        data_type=data_type,
        source=source,
        name=name,
        value=value,
        metadata=metadata or {},
        session_id=manager.session_id,
        thread_id=threading.current_thread().name
    )
    manager._handle_data(data)


def start_debug_collection(session_id: str = None, interval: float = 5.0):
    """启动调试数据收集"""
    manager = get_collector_manager(session_id)
    manager.start_auto_collect(interval)
    return manager


def stop_debug_collection(session_id: str = None):
    """停止调试数据收集"""
    manager = get_collector_manager(session_id)
    manager.close()