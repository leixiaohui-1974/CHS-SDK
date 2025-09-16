"""
服务接口定义

定义中央协调模块提供的各种服务接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseServiceInterface(ABC):
    """基础服务接口"""
    
    @abstractmethod
    def start_service(self) -> bool:
        """
        启动服务
        
        Returns:
            bool: 启动是否成功
        """
        pass
        
    @abstractmethod
    def stop_service(self) -> bool:
        """
        停止服务
        
        Returns:
            bool: 停止是否成功
        """
        pass
        
    @abstractmethod
    def get_service_status(self) -> ServiceStatus:
        """
        获取服务状态
        
        Returns:
            ServiceStatus: 服务状态
        """
        pass
        
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            Dict[str, Any]: 服务信息
        """
        pass


class AnomalyDetectionServiceInterface(BaseServiceInterface):
    """异常检测服务接口"""
    
    @abstractmethod
    def register_detector(self, detector_id: str, detector_func: Callable) -> bool:
        """
        注册异常检测器
        
        Args:
            detector_id: 检测器ID
            detector_func: 检测函数
            
        Returns:
            bool: 注册是否成功
        """
        pass
        
    @abstractmethod
    def detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测异常
        
        Args:
            data: 输入数据
            
        Returns:
            List[Dict[str, Any]]: 检测到的异常列表
        """
        pass
        
    @abstractmethod
    def get_anomaly_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取异常历史
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 异常历史记录
        """
        pass


class ForecastingServiceInterface(BaseServiceInterface):
    """预测服务接口"""
    
    @abstractmethod
    def register_model(self, model_id: str, model_func: Callable) -> bool:
        """
        注册预测模型
        
        Args:
            model_id: 模型ID
            model_func: 预测函数
            
        Returns:
            bool: 注册是否成功
        """
        pass
        
    @abstractmethod
    def generate_forecast(self, model_id: str, input_data: Dict[str, Any], 
                         horizon: int) -> Dict[str, List[float]]:
        """
        生成预测
        
        Args:
            model_id: 模型ID
            input_data: 输入数据
            horizon: 预测时域
            
        Returns:
            Dict[str, List[float]]: 预测结果
        """
        pass
        
    @abstractmethod
    def update_model(self, model_id: str, training_data: Dict[str, Any]) -> bool:
        """
        更新模型
        
        Args:
            model_id: 模型ID
            training_data: 训练数据
            
        Returns:
            bool: 更新是否成功
        """
        pass


class MonitoringServiceInterface(BaseServiceInterface):
    """监控服务接口"""
    
    @abstractmethod
    def register_metric(self, metric_id: str, metric_func: Callable) -> bool:
        """
        注册监控指标
        
        Args:
            metric_id: 指标ID
            metric_func: 指标计算函数
            
        Returns:
            bool: 注册是否成功
        """
        pass
        
    @abstractmethod
    def collect_metrics(self) -> Dict[str, float]:
        """
        收集监控指标
        
        Returns:
            Dict[str, float]: 指标数据
        """
        pass
        
    @abstractmethod
    def get_metric_history(self, metric_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指标历史
        
        Args:
            metric_id: 指标ID
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 指标历史数据
        """
        pass
        
    @abstractmethod
    def set_alert_threshold(self, metric_id: str, threshold: float) -> bool:
        """
        设置告警阈值
        
        Args:
            metric_id: 指标ID
            threshold: 告警阈值
            
        Returns:
            bool: 设置是否成功
        """
        pass