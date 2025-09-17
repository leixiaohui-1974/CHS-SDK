"""
"""
统一数据源Agent实现

收敛所有数据源类型：CSV、数据库、API、实时流
替代：CsvReaderAgent、CsvInflowAgent、CsvDataSourceAgent等
"""
import pandas as pd
import asyncio
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
import requests
import sqlite3
from datetime import datetime, timedelta

from core_lib.core.new_interfaces import DataSourceAgent, DataSourceType, Config, Message
from core_lib.core.event_bus import get_global_event_bus
from core_lib.core.config_schema import DataSourceConfig

class UnifiedDataSourceAgent(DataSourceAgent):
    """
    统一数据源Agent
    
    支持的数据源类型：
    - CSV文件 (替代 CsvReaderAgent, CsvInflowAgent, CsvDataSourceAgent)
    - SQLite/PostgreSQL数据库
    - REST API
    - 实时数据流
    - Mock数据
    """
    
    def __init__(self, agent_id: str, source_type: Union[DataSourceType, str] = None, config: Optional[Config] = None):
        # 处理source_type参数
        if isinstance(source_type, str):
            try:
                source_type = DataSourceType(source_type)
            except ValueError:
                source_type = DataSourceType.MOCK  # 默认值
        elif source_type is None:
            source_type = DataSourceType(config.get('source_type', 'mock')) if config else DataSourceType.MOCK
        
        super().__init__(agent_id, source_type, config)
        
        # 基础配置
        self.connection_config = config.get('connection_config', {}) if config else {}
        self.publish_topic = config.get('publish_topic', f'data.{agent_id}') if config else f'data.{agent_id}'
        self.publish_interval = config.get('publish_interval', 1.0) if config else 1.0
        
        # 数据缓存和状态
        self._data_cache: List[Dict[str, Any]] = []
        self._current_index = 0
        self._is_connected = False
        self._is_streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 类型特定配置
        self._setup_type_specific_config()
        
        print(f"[UnifiedDataSource] Initialized {source_type.value} data source: {agent_id}")
    
    def _setup_type_specific_config(self):
        """设置类型特定配置"""
        if self.source_type == DataSourceType.CSV:
            self.csv_file_path = self.config.get('csv_file_path')
            self.time_column = self.config.get('time_column', 'time')
            self.data_columns = self.config.get('data_columns', [])
            self.loop_data = self.config.get('loop_data', True)
            
        elif self.source_type == DataSourceType.DATABASE:
            self.database_url = self.config.get('database_url')
            self.table_name = self.config.get('table_name')
            self.query = self.config.get('query')
            
        elif self.source_type == DataSourceType.API:
            self.api_url = self.config.get('api_url')
            self.headers = self.config.get('headers', {})
            self.auth_config = self.config.get('auth_config', {})
            
        elif self.source_type == DataSourceType.REALTIME:
            self.stream_config = self.config.get('stream_config', {})
            
        elif self.source_type == DataSourceType.MOCK:
            self.mock_data_type = self.config.get('mock_data_type', 'sine_wave')
            self.mock_parameters = self.config.get('mock_parameters', {})
    
    def configure(self, config: Config) -> bool:
        """配置数据源"""
        try:
            self.config.update(config)
            self._setup_type_specific_config()
            self._log("info", f"Configuration updated for {self.source_type.value} data source")
            return True
        except Exception as e:
            self._log("error", f"Configuration failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动数据源"""
        try:
            if self.connect():
                self.status = self.status.__class__.RUNNING
                self._log("info", f"Data source started successfully")
                return True
            return False
        except Exception as e:
            self._log("error", f"Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止数据源"""
        try:
            self._stop_event.set()
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=5.0)
            
            self.disconnect()
            self.status = self.status.__class__.STOPPED
            self._log("info", "Data source stopped")
            return True
        except Exception as e:
            self._log("error", f"Stop failed: {e}")
            return False
    
    def step(self, current_time: float) -> bool:
        """执行一个时间步"""
        try:
            if not self._is_connected:
                return False
            
            # 根据数据源类型执行不同的步进逻辑
            if self.source_type == DataSourceType.CSV:
                return self._step_csv(current_time)
            elif self.source_type == DataSourceType.MOCK:
                return self._step_mock(current_time)
            else:
                # 其他类型通常是事件驱动的，不需要step
                return True
                
        except Exception as e:
            self._log("error", f"Step failed: {e}")
            return False
    
    def connect(self) -> bool:
        """连接数据源"""
        try:
            if self.source_type == DataSourceType.CSV:
                return self._connect_csv()
            elif self.source_type == DataSourceType.DATABASE:
                return self._connect_database()
            elif self.source_type == DataSourceType.API:
                return self._connect_api()
            elif self.source_type == DataSourceType.REALTIME:
                return self._connect_realtime()
            elif self.source_type == DataSourceType.MOCK:
                return self._connect_mock()
            else:
                raise ValueError(f"Unsupported source type: {self.source_type}")
                
        except Exception as e:
            self._log("error", f"Connection failed: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        try:
            self._is_connected = False
            self._is_streaming = False
            self._log("info", "Disconnected from data source")
            return True
        except Exception as e:
            self._log("error", f"Disconnect failed: {e}")
            return False
    
    def read_data(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """读取数据"""
        try:
            if not self._is_connected:
                self.connect()
            
            if self.source_type == DataSourceType.CSV:
                return self._read_csv_data(query)
            elif self.source_type == DataSourceType.DATABASE:
                return self._read_database_data(query)
            elif self.source_type == DataSourceType.API:
                return self._read_api_data(query)
            else:
                return self._data_cache.copy()
                
        except Exception as e:
            self._log("error", f"Read data failed: {e}")
            return []
    
    def subscribe_stream(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """订阅数据流"""
        try:
            if not self._is_connected:
                self.connect()
            
            if self._is_streaming:
                self._log("warning", "Already streaming")
                return True
            
            self._is_streaming = True
            self._stream_thread = threading.Thread(
                target=self._stream_worker,
                args=(callback,),
                daemon=True
            )
            self._stream_thread.start()
            
            self._log("info", "Data streaming started")
            return True
            
        except Exception as e:
            self._log("error", f"Stream subscription failed: {e}")
            return False
    
    def provide_service(self, request: Message) -> Message:
        """提供数据服务"""
        try:
            service_type = request.get('service_type')
            
            if service_type == 'read':
                query = request.get('query')
                data = self.read_data(query)
                return {'status': 'success', 'data': data}
            
            elif service_type == 'stream_start':
                callback_topic = request.get('callback_topic')
                if callback_topic and self.event_bus:
                    def callback(data):
                        self.event_bus.publish(callback_topic, data)
                    success = self.subscribe_stream(callback)
                    return {'status': 'success' if success else 'failed'}
            
            elif service_type == 'stream_stop':
                self._is_streaming = False
                return {'status': 'success'}
            
            else:
                return {'status': 'error', 'message': f'Unknown service type: {service_type}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # CSV数据源实现
    def _connect_csv(self) -> bool:
        """连接CSV数据源"""
        if not self.csv_file_path:
            raise ValueError("csv_file_path is required for CSV data source")
        
        csv_path = Path(self.csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
        
        # 读取CSV数据
        df = pd.read_csv(csv_path)
        
        # 转换为字典列表
        self._data_cache = df.to_dict('records')
        self._current_index = 0
        self._is_connected = True
        
        self._log("info", f"CSV loaded: {len(self._data_cache)} records from {csv_path.name}")
        return True
    
    def _step_csv(self, current_time: float) -> bool:
        """CSV数据步进"""
        if not self._data_cache:
            return False
        
        # 获取当前数据
        if self._current_index < len(self._data_cache):
            current_data = self._data_cache[self._current_index]
            
            # 发布数据
            message = {
                'source': self.agent_id,
                'timestamp': current_time,
                'data': current_data
            }
            
            if self.event_bus:
                self.event_bus.publish(self.publish_topic, message)
            
            self._current_index += 1
            
            # 循环播放
            if self._current_index >= len(self._data_cache) and self.loop_data:
                self._current_index = 0
            
            return True
        
        return False
    
    def _read_csv_data(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """读取CSV数据"""
        if not self._data_cache:
            return []
        
        if not query:
            return self._data_cache.copy()
        
        # 简单查询支持
        start_index = query.get('start_index', 0)
        end_index = query.get('end_index', len(self._data_cache))
        
        return self._data_cache[start_index:end_index]
    
    # Mock数据源实现
    def _connect_mock(self) -> bool:
        """连接Mock数据源"""
        self._is_connected = True
        self._log("info", f"Mock data source connected: {self.mock_data_type}")
        return True
    
    def _step_mock(self, current_time: float) -> bool:
        """Mock数据步进"""
        data = self._generate_mock_data(current_time)
        
        message = {
            'source': self.agent_id,
            'timestamp': current_time,
            'data': data
        }
        
        if self.event_bus:
            self.event_bus.publish(self.publish_topic, message)
        
        return True
    
    def _generate_mock_data(self, current_time: float) -> Dict[str, Any]:
        """生成Mock数据"""
        if self.mock_data_type == 'sine_wave':
            amplitude = self.mock_parameters.get('amplitude', 1.0)
            frequency = self.mock_parameters.get('frequency', 0.1)
            offset = self.mock_parameters.get('offset', 0.0)
            
            value = amplitude * pd.np.sin(2 * pd.np.pi * frequency * current_time) + offset
            return {'value': value, 'time': current_time}
        
        elif self.mock_data_type == 'random':
            import random
            min_val = self.mock_parameters.get('min', 0.0)
            max_val = self.mock_parameters.get('max', 1.0)
            
            value = random.uniform(min_val, max_val)
            return {'value': value, 'time': current_time}
        
        else:
            return {'value': 0.0, 'time': current_time}
    
    # 数据库数据源实现
    def _connect_database(self) -> bool:
        """连接数据库数据源"""
        if not self.database_url:
            raise ValueError("database_url is required for database data source")
        
        # 简单的SQLite支持
        if self.database_url.startswith('sqlite://'):
            db_path = self.database_url.replace('sqlite://', '')
            self._db_connection = sqlite3.connect(db_path)
            self._is_connected = True
            self._log("info", f"Connected to SQLite database: {db_path}")
            return True
        else:
            raise NotImplementedError("Only SQLite is currently supported")
    
    def _read_database_data(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """读取数据库数据"""
        if not hasattr(self, '_db_connection'):
            return []
        
        try:
            if self.query:
                df = pd.read_sql_query(self.query, self._db_connection)
            elif self.table_name:
                df = pd.read_sql_query(f"SELECT * FROM {self.table_name}", self._db_connection)
            else:
                return []
            
            return df.to_dict('records')
        except Exception as e:
            self._log("error", f"Database query failed: {e}")
            return []
    
    # API数据源实现
    def _connect_api(self) -> bool:
        """连接API数据源"""
        if not self.api_url:
            raise ValueError("api_url is required for API data source")
        
        # 测试API连接
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            self._is_connected = True
            self._log("info", f"Connected to API: {self.api_url}")
            return True
        except Exception as e:
            self._log("error", f"API connection failed: {e}")
            return False
    
    def _read_api_data(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """读取API数据"""
        try:
            params = query if query else {}
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                return data
            else:
                return [data]
        except Exception as e:
            self._log("error", f"API request failed: {e}")
            return []
    
    # 实时数据源实现
    def _connect_realtime(self) -> bool:
        """连接实时数据源"""
        # 实时数据源通常需要具体的实现
        self._is_connected = True
        self._log("info", "Realtime data source connected")
        return True
    
    # 流处理工作线程
    def _stream_worker(self, callback: Callable[[Dict[str, Any]], None]):
        """流处理工作线程"""
        while self._is_streaming and not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                if self.source_type == DataSourceType.CSV:
                    if self._current_index < len(self._data_cache):
                        data = self._data_cache[self._current_index]
                        callback(data)
                        self._current_index += 1
                        
                        if self._current_index >= len(self._data_cache) and self.loop_data:
                            self._current_index = 0
                
                elif self.source_type == DataSourceType.MOCK:
                    data = self._generate_mock_data(current_time)
                    callback(data)
                
                # 等待下一个发布间隔
                self._stop_event.wait(self.publish_interval)
                
            except Exception as e:
                self._log("error", f"Stream worker error: {e}")
                break
        
        self._log("info", "Stream worker stopped")
