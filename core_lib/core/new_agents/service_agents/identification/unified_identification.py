"""
统一参数识别Agent实现

收敛所有参数识别功能
替代：IdentificationAgent、ModelUpdaterAgent等
"""
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import pickle
from pathlib import Path

from core_lib.core.new_interfaces import IdentificationAgent, Config, Message, Parameters
from core_lib.core.event_bus import get_global_event_bus

class IdentificationMethod(Enum):
    """参数识别方法枚举"""
    OFFLINE = "offline"
    ONLINE = "online"
    BATCH = "batch"
    RECURSIVE = "recursive"

class OptimizationAlgorithm(Enum):
    """优化算法枚举"""
    LEAST_SQUARES = "least_squares"
    GRADIENT_DESCENT = "gradient_descent"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"

@dataclass
class IdentificationResult:
    """识别结果"""
    parameters: Parameters
    objective_value: float
    iterations: int
    convergence_achieved: bool
    computation_time: float
    validation_metrics: Dict[str, float]
    method: str
    timestamp: float

@dataclass
class ValidationMetrics:
    """验证指标"""
    mse: float = 0.0          # 均方误差
    rmse: float = 0.0         # 均方根误差
    mae: float = 0.0          # 平均绝对误差
    r2: float = 0.0           # 决定系数
    aic: float = 0.0          # 赤池信息准则
    bic: float = 0.0          # 贝叶斯信息准则

class UnifiedIdentificationAgent(IdentificationAgent):
    """
    统一参数识别Agent
    
    功能：
    1. 离线参数识别
    2. 在线参数更新
    3. 批处理识别
    4. 递归识别
    5. 模型验证
    6. 参数不确定性分析
    """
    
    def __init__(self, agent_id: str, config: Optional[Config] = None):
        super().__init__(agent_id, config)
        
        # 识别配置
        self.identification_method = IdentificationMethod.OFFLINE
        if config and 'identification_method' in config:
            self.identification_method = IdentificationMethod(config['identification_method'])
        
        self.optimization_algorithm = OptimizationAlgorithm.LEAST_SQUARES
        if config and 'optimization_algorithm' in config:
            self.optimization_algorithm = OptimizationAlgorithm(config['optimization_algorithm'])
        
        # 目标参数
        self.target_parameters = config.get('target_parameters', []) if config else []
        self.parameter_bounds = config.get('parameter_bounds', {}) if config else {}
        self.initial_parameters = config.get('initial_parameters', {}) if config else {}
        
        # 数据配置
        self.data_source = config.get('data_source', '') if config else ''
        self.validation_split = config.get('validation_split', 0.2) if config else 0.2
        self.window_size = config.get('window_size', 100) if config else 100  # 在线识别窗口大小
        
        # 优化配置
        self.optimization_config = config.get('optimization_config', {}) if config else {}
        self.max_iterations = self.optimization_config.get('max_iterations', 1000)
        self.tolerance = self.optimization_config.get('tolerance', 1e-6)
        self.learning_rate = self.optimization_config.get('learning_rate', 0.01)
        
        # 状态管理
        self.current_parameters: Parameters = self.initial_parameters.copy()
        self.identification_history: List[IdentificationResult] = []
        self.data_buffer: List[Dict[str, Any]] = []
        self.last_identification_time = 0.0
        
        # 在线识别状态
        self.online_enabled = False
        self.online_update_interval = config.get('online_update_interval', 10.0) if config else 10.0
        self._online_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 性能指标
        self.identification_metrics = {
            'total_identifications': 0,
            'successful_identifications': 0,
            'failed_identifications': 0,
            'average_computation_time': 0.0,
            'best_objective_value': float('inf'),
            'parameter_stability': {}
        }
        
        print(f"[UnifiedIdentification] Initialized identification agent: {agent_id}")
    
    def configure(self, config: Config) -> bool:
        """配置识别Agent"""
        try:
            self.config.update(config)
            
            # 更新识别方法
            if 'identification_method' in config:
                self.identification_method = IdentificationMethod(config['identification_method'])
            
            # 更新目标参数
            if 'target_parameters' in config:
                self.target_parameters = config['target_parameters']
            
            # 更新参数边界
            if 'parameter_bounds' in config:
                self.parameter_bounds.update(config['parameter_bounds'])
            
            self._log("info", "Identification configuration updated")
            return True
        except Exception as e:
            self._log("error", f"Configuration failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动识别Agent"""
        try:
            # 设置事件总线
            if not self.event_bus:
                self.event_bus = get_global_event_bus()
            
            # 订阅数据更新事件
            self._setup_subscriptions()
            
            # 启动在线识别线程
            if self.identification_method in [IdentificationMethod.ONLINE, IdentificationMethod.RECURSIVE]:
                self._start_online_identification()
            
            self.status = self.status.__class__.RUNNING
            self._log("info", "Identification agent started")
            return True
        except Exception as e:
            self._log("error", f"Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止识别Agent"""
        try:
            self._stop_event.set()
            
            if self._online_thread and self._online_thread.is_alive():
                self._online_thread.join(timeout=5.0)
            
            self.status = self.status.__class__.STOPPED
            self._log("info", "Identification agent stopped")
            return True
        except Exception as e:
            self._log("error", f"Stop failed: {e}")
            return False
    
    def step(self, current_time: float) -> bool:
        """执行一个时间步"""
        try:
            # 处理数据缓冲区
            self._process_data_buffer()
            
            # 检查是否需要触发识别
            if self.identification_method == IdentificationMethod.BATCH:
                if len(self.data_buffer) >= self.window_size:
                    self._trigger_batch_identification(current_time)
            
            return True
        except Exception as e:
            self._log("error", f"Step execution failed: {e}")
            return False
    
    def fit_parameters(self, data: List[Dict[str, Any]], method: str = 'offline') -> Parameters:
        """拟合参数"""
        start_time = time.time()
        
        try:
            self.identification_metrics['total_identifications'] += 1
            
            # 预处理数据
            processed_data = self._preprocess_data(data)
            
            # 分割训练和验证数据
            train_data, val_data = self._split_data(processed_data, self.validation_split)
            
            # 执行参数识别
            if self.optimization_algorithm == OptimizationAlgorithm.LEAST_SQUARES:
                result = self._fit_least_squares(train_data, val_data)
            elif self.optimization_algorithm == OptimizationAlgorithm.GRADIENT_DESCENT:
                result = self._fit_gradient_descent(train_data, val_data)
            elif self.optimization_algorithm == OptimizationAlgorithm.GENETIC_ALGORITHM:
                result = self._fit_genetic_algorithm(train_data, val_data)
            else:
                result = self._fit_generic(train_data, val_data)
            
            # 更新当前参数
            if result.convergence_achieved:
                self.current_parameters.update(result.parameters)
                self.identification_metrics['successful_identifications'] += 1
                
                # 更新最佳目标值
                if result.objective_value < self.identification_metrics['best_objective_value']:
                    self.identification_metrics['best_objective_value'] = result.objective_value
                
                self._log("info", f"Parameter identification successful: objective={result.objective_value:.6f}")
            else:
                self.identification_metrics['failed_identifications'] += 1
                self._log("warning", "Parameter identification failed to converge")
            
            # 更新性能指标
            computation_time = time.time() - start_time
            self._update_identification_metrics(computation_time)
            
            # 记录结果
            result.computation_time = computation_time
            result.timestamp = time.time()
            self.identification_history.append(result)
            
            # 限制历史长度
            max_history = 100
            if len(self.identification_history) > max_history:
                self.identification_history = self.identification_history[-max_history:]
            
            return result.parameters
            
        except Exception as e:
            self.identification_metrics['failed_identifications'] += 1
            self._log("error", f"Parameter fitting failed: {e}")
            return {}
    
    def validate_parameters(self, parameters: Parameters, validation_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """验证参数"""
        try:
            # 使用参数进行预测
            predictions = self._predict_with_parameters(parameters, validation_data)
            
            # 提取真实值
            actual_values = [data.get('output', 0.0) for data in validation_data]
            
            # 计算验证指标
            metrics = self._calculate_validation_metrics(actual_values, predictions)
            
            return {
                'mse': metrics.mse,
                'rmse': metrics.rmse,
                'mae': metrics.mae,
                'r2': metrics.r2,
                'aic': metrics.aic,
                'bic': metrics.bic
            }
            
        except Exception as e:
            self._log("error", f"Parameter validation failed: {e}")
            return {}
    
    def update_online(self, new_data: Dict[str, Any]) -> Parameters:
        """在线更新参数"""
        try:
            # 添加数据到缓冲区
            self.data_buffer.append(new_data)
            
            # 保持缓冲区大小
            if len(self.data_buffer) > self.window_size:
                self.data_buffer.pop(0)
            
            # 检查是否有足够数据进行更新
            if len(self.data_buffer) >= self.window_size:
                # 使用滑动窗口数据进行递归更新
                updated_params = self._recursive_update(new_data)
                
                if updated_params:
                    self.current_parameters.update(updated_params)
                    self._log("debug", f"Online parameters updated: {updated_params}")
                
                return self.current_parameters
            
            return {}
            
        except Exception as e:
            self._log("error", f"Online update failed: {e}")
            return {}
    
    def provide_service(self, request: Message) -> Message:
        """提供识别服务"""
        try:
            service_type = request.get('service_type')
            
            if service_type == 'get_current_parameters':
                return {
                    'status': 'success',
                    'parameters': self.current_parameters,
                    'timestamp': time.time()
                }
            
            elif service_type == 'fit_parameters':
                data = request.get('data', [])
                method = request.get('method', 'offline')
                
                if data:
                    parameters = self.fit_parameters(data, method)
                    return {
                        'status': 'success',
                        'parameters': parameters
                    }
                else:
                    return {'status': 'error', 'message': 'No data provided'}
            
            elif service_type == 'validate_parameters':
                parameters = request.get('parameters', {})
                validation_data = request.get('validation_data', [])
                
                if parameters and validation_data:
                    metrics = self.validate_parameters(parameters, validation_data)
                    return {
                        'status': 'success',
                        'validation_metrics': metrics
                    }
                else:
                    return {'status': 'error', 'message': 'Missing parameters or validation data'}
            
            elif service_type == 'get_identification_history':
                count = request.get('count', 10)
                history = self.identification_history[-count:] if self.identification_history else []
                return {
                    'status': 'success',
                    'history': [self._result_to_dict(result) for result in history]
                }
            
            else:
                return {'status': 'error', 'message': f'Unknown service type: {service_type}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _setup_subscriptions(self):
        """设置事件订阅"""
        if self.event_bus:
            # 订阅数据更新
            if self.data_source:
                self.event_bus.subscribe(f'data.{self.data_source}', self._handle_data_update)
            
            # 订阅识别请求
            self.event_bus.subscribe(f'identification.request.{self.agent_id}', self._handle_identification_request)
            
            self._log("info", "Event subscriptions set up")
    
    def _start_online_identification(self):
        """启动在线识别线程"""
        self.online_enabled = True
        self._online_thread = threading.Thread(
            target=self._online_identification_worker,
            daemon=True
        )
        self._online_thread.start()
        self._log("info", "Online identification thread started")
    
    def _online_identification_worker(self):
        """在线识别工作线程"""
        while self.online_enabled and not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # 检查是否需要更新参数
                if (current_time - self.last_identification_time >= self.online_update_interval and
                    len(self.data_buffer) >= self.window_size):
                    
                    # 执行在线识别
                    self._perform_online_identification(current_time)
                    self.last_identification_time = current_time
                
                # 等待下一个更新周期
                self._stop_event.wait(1.0)
                
            except Exception as e:
                self._log("error", f"Online identification worker error: {e}")
    
    def _preprocess_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理数据"""
        try:
            processed_data = []
            
            for record in data:
                # 数据清洗
                processed_record = {}
                for key, value in record.items():
                    if isinstance(value, (int, float)) and not np.isnan(value):
                        processed_record[key] = float(value)
                    elif isinstance(value, str):
                        try:
                            processed_record[key] = float(value)
                        except ValueError:
                            processed_record[key] = value
                    else:
                        processed_record[key] = value
                
                if processed_record:
                    processed_data.append(processed_record)
            
            return processed_data
            
        except Exception as e:
            self._log("error", f"Data preprocessing failed: {e}")
            return data
    
    def _split_data(self, data: List[Dict[str, Any]], validation_split: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """分割训练和验证数据"""
        try:
            n_total = len(data)
            n_val = int(n_total * validation_split)
            n_train = n_total - n_val
            
            # 随机打乱数据
            shuffled_data = data.copy()
            np.random.shuffle(shuffled_data)
            
            train_data = shuffled_data[:n_train]
            val_data = shuffled_data[n_train:]
            
            return train_data, val_data
            
        except Exception as e:
            self._log("error", f"Data splitting failed: {e}")
            return data, []
    
    def _fit_least_squares(self, train_data: List[Dict[str, Any]], val_data: List[Dict[str, Any]]) -> IdentificationResult:
        """最小二乘法拟合"""
        try:
            # 构建设计矩阵和观测向量
            X, y = self._build_regression_matrices(train_data)
            
            if X.size == 0 or y.size == 0:
                raise ValueError("Insufficient data for least squares fitting")
            
            # 最小二乘解
            params_array = np.linalg.lstsq(X, y, rcond=None)[0]
            
            # 构建参数字典
            parameters = {}
            for i, param_name in enumerate(self.target_parameters):
                if i < len(params_array):
                    parameters[param_name] = float(params_array[i])
            
            # 计算目标函数值
            predictions = X @ params_array
            objective_value = np.mean((y - predictions)**2)
            
            # 验证
            validation_metrics = {}
            if val_data:
                validation_metrics = self.validate_parameters(parameters, val_data)
            
            return IdentificationResult(
                parameters=parameters,
                objective_value=objective_value,
                iterations=1,
                convergence_achieved=True,
                computation_time=0.0,
                validation_metrics=validation_metrics,
                method='least_squares',
                timestamp=time.time()
            )
            
        except Exception as e:
            self._log("error", f"Least squares fitting failed: {e}")
            return IdentificationResult(
                parameters={},
                objective_value=float('inf'),
                iterations=0,
                convergence_achieved=False,
                computation_time=0.0,
                validation_metrics={},
                method='least_squares',
                timestamp=time.time()
            )
    
    def _fit_gradient_descent(self, train_data: List[Dict[str, Any]], val_data: List[Dict[str, Any]]) -> IdentificationResult:
        """梯度下降拟合"""
        try:
            # 初始化参数
            params = np.array([self.initial_parameters.get(name, 0.0) for name in self.target_parameters])
            
            # 构建数据矩阵
            X, y = self._build_regression_matrices(train_data)
            
            if X.size == 0 or y.size == 0:
                raise ValueError("Insufficient data for gradient descent")
            
            # 梯度下降迭代
            for iteration in range(self.max_iterations):
                # 前向传播
                predictions = X @ params
                
                # 计算损失
                loss = np.mean((y - predictions)**2)
                
                # 计算梯度
                gradient = -2 * X.T @ (y - predictions) / len(y)
                
                # 更新参数
                params -= self.learning_rate * gradient
                
                # 应用参数边界
                params = self._apply_parameter_bounds(params)
                
                # 检查收敛
                if np.linalg.norm(gradient) < self.tolerance:
                    break
            
            # 构建参数字典
            parameters = {}
            for i, param_name in enumerate(self.target_parameters):
                if i < len(params):
                    parameters[param_name] = float(params[i])
            
            # 验证
            validation_metrics = {}
            if val_data:
                validation_metrics = self.validate_parameters(parameters, val_data)
            
            return IdentificationResult(
                parameters=parameters,
                objective_value=loss,
                iterations=iteration + 1,
                convergence_achieved=iteration < self.max_iterations - 1,
                computation_time=0.0,
                validation_metrics=validation_metrics,
                method='gradient_descent',
                timestamp=time.time()
            )
            
        except Exception as e:
            self._log("error", f"Gradient descent fitting failed: {e}")
            return IdentificationResult(
                parameters={},
                objective_value=float('inf'),
                iterations=0,
                convergence_achieved=False,
                computation_time=0.0,
                validation_metrics={},
                method='gradient_descent',
                timestamp=time.time()
            )
    
    def _fit_genetic_algorithm(self, train_data: List[Dict[str, Any]], val_data: List[Dict[str, Any]]) -> IdentificationResult:
        """遗传算法拟合"""
        try:
            # 简化的遗传算法实现
            population_size = self.optimization_config.get('population_size', 50)
            generations = self.optimization_config.get('generations', 100)
            mutation_rate = self.optimization_config.get('mutation_rate', 0.1)
            
            # 构建数据矩阵
            X, y = self._build_regression_matrices(train_data)
            
            if X.size == 0 or y.size == 0:
                raise ValueError("Insufficient data for genetic algorithm")
            
            # 初始化种群
            population = []
            for _ in range(population_size):
                individual = np.random.uniform(-1, 1, len(self.target_parameters))
                population.append(individual)
            
            best_individual = None
            best_fitness = float('inf')
            
            # 进化过程
            for generation in range(generations):
                # 评估适应度
                fitness_scores = []
                for individual in population:
                    predictions = X @ individual
                    fitness = np.mean((y - predictions)**2)
                    fitness_scores.append(fitness)
                    
                    if fitness < best_fitness:
                        best_fitness = fitness
                        best_individual = individual.copy()
                
                # 选择、交叉、变异（简化实现）
                new_population = []
                for _ in range(population_size):
                    # 轮盘赌选择
                    parent1_idx = np.random.choice(len(population), p=self._softmax(-np.array(fitness_scores)))
                    parent2_idx = np.random.choice(len(population), p=self._softmax(-np.array(fitness_scores)))
                    
                    # 交叉
                    child = 0.5 * (population[parent1_idx] + population[parent2_idx])
                    
                    # 变异
                    if np.random.random() < mutation_rate:
                        child += np.random.normal(0, 0.1, len(child))
                    
                    child = self._apply_parameter_bounds(child)
                    new_population.append(child)
                
                population = new_population
            
            # 构建参数字典
            parameters = {}
            if best_individual is not None:
                for i, param_name in enumerate(self.target_parameters):
                    if i < len(best_individual):
                        parameters[param_name] = float(best_individual[i])
            
            # 验证
            validation_metrics = {}
            if val_data:
                validation_metrics = self.validate_parameters(parameters, val_data)
            
            return IdentificationResult(
                parameters=parameters,
                objective_value=best_fitness,
                iterations=generations,
                convergence_achieved=True,
                computation_time=0.0,
                validation_metrics=validation_metrics,
                method='genetic_algorithm',
                timestamp=time.time()
            )
            
        except Exception as e:
            self._log("error", f"Genetic algorithm fitting failed: {e}")
            return IdentificationResult(
                parameters={},
                objective_value=float('inf'),
                iterations=0,
                convergence_achieved=False,
                computation_time=0.0,
                validation_metrics={},
                method='genetic_algorithm',
                timestamp=time.time()
            )
    
    def _fit_generic(self, train_data: List[Dict[str, Any]], val_data: List[Dict[str, Any]]) -> IdentificationResult:
        """通用拟合方法"""
        try:
            # 简单的平均值估计
            parameters = {}
            
            for param_name in self.target_parameters:
                values = [data.get(param_name, 0.0) for data in train_data if param_name in data]
                if values:
                    parameters[param_name] = float(np.mean(values))
                else:
                    parameters[param_name] = self.initial_parameters.get(param_name, 0.0)
            
            # 计算简单的目标函数值
            objective_value = 1.0
            
            # 验证
            validation_metrics = {}
            if val_data:
                validation_metrics = self.validate_parameters(parameters, val_data)
            
            return IdentificationResult(
                parameters=parameters,
                objective_value=objective_value,
                iterations=1,
                convergence_achieved=True,
                computation_time=0.0,
                validation_metrics=validation_metrics,
                method='generic',
                timestamp=time.time()
            )
            
        except Exception as e:
            self._log("error", f"Generic fitting failed: {e}")
            return IdentificationResult(
                parameters={},
                objective_value=float('inf'),
                iterations=0,
                convergence_achieved=False,
                computation_time=0.0,
                validation_metrics={},
                method='generic',
                timestamp=time.time()
            )
    
    def _build_regression_matrices(self, data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """构建回归矩阵"""
        try:
            if not data:
                return np.array([]), np.array([])
            
            # 提取输入和输出
            X_list = []
            y_list = []
            
            for record in data:
                # 构建输入向量（使用目标参数作为特征）
                x_row = []
                for param_name in self.target_parameters:
                    x_row.append(record.get(f'input_{param_name}', 1.0))
                
                # 输出值
                y_val = record.get('output', 0.0)
                
                if x_row and not np.isnan(y_val):
                    X_list.append(x_row)
                    y_list.append(y_val)
            
            if not X_list:
                return np.array([]), np.array([])
            
            X = np.array(X_list)
            y = np.array(y_list)
            
            return X, y
            
        except Exception as e:
            self._log("error", f"Regression matrix building failed: {e}")
            return np.array([]), np.array([])
    
    def _apply_parameter_bounds(self, params: np.ndarray) -> np.ndarray:
        """应用参数边界"""
        try:
            bounded_params = params.copy()
            
            for i, param_name in enumerate(self.target_parameters):
                if i < len(bounded_params) and param_name in self.parameter_bounds:
                    bounds = self.parameter_bounds[param_name]
                    if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                        bounded_params[i] = np.clip(bounded_params[i], bounds[0], bounds[1])
            
            return bounded_params
            
        except Exception as e:
            self._log("error", f"Parameter bounds application failed: {e}")
            return params
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax函数"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def _predict_with_parameters(self, parameters: Parameters, data: List[Dict[str, Any]]) -> List[float]:
        """使用参数进行预测"""
        try:
            predictions = []
            
            for record in data:
                # 简单的线性预测模型
                prediction = 0.0
                for param_name, param_value in parameters.items():
                    input_key = f'input_{param_name}'
                    if input_key in record:
                        prediction += param_value * record[input_key]
                
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            self._log("error", f"Prediction failed: {e}")
            return [0.0] * len(data)
    
    def _calculate_validation_metrics(self, actual: List[float], predicted: List[float]) -> ValidationMetrics:
        """计算验证指标"""
        try:
            actual_arr = np.array(actual)
            predicted_arr = np.array(predicted)
            
            # 均方误差
            mse = np.mean((actual_arr - predicted_arr)**2)
            
            # 均方根误差
            rmse = np.sqrt(mse)
            
            # 平均绝对误差
            mae = np.mean(np.abs(actual_arr - predicted_arr))
            
            # 决定系数
            ss_res = np.sum((actual_arr - predicted_arr)**2)
            ss_tot = np.sum((actual_arr - np.mean(actual_arr))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
            
            # AIC和BIC（简化计算）
            n = len(actual)
            k = len(self.target_parameters)
            aic = n * np.log(mse) + 2 * k if mse > 0 else float('inf')
            bic = n * np.log(mse) + k * np.log(n) if mse > 0 else float('inf')
            
            return ValidationMetrics(
                mse=mse,
                rmse=rmse,
                mae=mae,
                r2=r2,
                aic=aic,
                bic=bic
            )
            
        except Exception as e:
            self._log("error", f"Validation metrics calculation failed: {e}")
            return ValidationMetrics()
    
    def _recursive_update(self, new_data: Dict[str, Any]) -> Optional[Parameters]:
        """递归参数更新"""
        try:
            # 简化的递归最小二乘更新
            # 在实际应用中，这里会实现完整的RLS算法
            
            # 使用最近的数据进行快速更新
            recent_data = self.data_buffer[-10:] if len(self.data_buffer) >= 10 else self.data_buffer
            
            if len(recent_data) < 2:
                return None
            
            # 简单的移动平均更新
            updated_params = {}
            for param_name in self.target_parameters:
                values = [data.get(param_name, self.current_parameters.get(param_name, 0.0)) 
                         for data in recent_data if param_name in data]
                
                if values:
                    # 指数移动平均
                    alpha = 0.1  # 学习率
                    current_value = self.current_parameters.get(param_name, 0.0)
                    new_value = values[-1]
                    updated_params[param_name] = (1 - alpha) * current_value + alpha * new_value
            
            return updated_params if updated_params else None
            
        except Exception as e:
            self._log("error", f"Recursive update failed: {e}")
            return None
    
    def _perform_online_identification(self, current_time: float):
        """执行在线识别"""
        try:
            if len(self.data_buffer) >= self.window_size:
                # 使用滑动窗口数据进行识别
                window_data = self.data_buffer[-self.window_size:]
                
                # 执行快速识别
                updated_params = self.fit_parameters(window_data, 'online')
                
                if updated_params:
                    # 发布参数更新事件
                    if self.event_bus:
                        self.event_bus.publish(f'identification.updated.{self.agent_id}', {
                            'agent_id': self.agent_id,
                            'parameters': updated_params,
                            'timestamp': current_time,
                            'method': 'online'
                        })
                    
                    self._log("info", f"Online identification completed: {len(updated_params)} parameters updated")
            
        except Exception as e:
            self._log("error", f"Online identification failed: {e}")
    
    def _trigger_batch_identification(self, current_time: float):
        """触发批处理识别"""
        try:
            batch_data = self.data_buffer.copy()
            self.data_buffer.clear()  # 清空缓冲区
            
            # 执行批处理识别
            updated_params = self.fit_parameters(batch_data, 'batch')
            
            if updated_params:
                # 发布参数更新事件
                if self.event_bus:
                    self.event_bus.publish(f'identification.updated.{self.agent_id}', {
                        'agent_id': self.agent_id,
                        'parameters': updated_params,
                        'timestamp': current_time,
                        'method': 'batch'
                    })
                
                self._log("info", f"Batch identification completed: {len(updated_params)} parameters updated")
        
        except Exception as e:
            self._log("error", f"Batch identification failed: {e}")
    
    def _process_data_buffer(self):
        """处理数据缓冲区"""
        # 移除过时的数据
        current_time = time.time()
        max_age = self.optimization_config.get('max_data_age', 3600.0)  # 1小时
        
        self.data_buffer = [
            data for data in self.data_buffer 
            if current_time - data.get('timestamp', current_time) <= max_age
        ]
    
    def _update_identification_metrics(self, computation_time: float):
        """更新识别指标"""
        try:
            # 更新平均计算时间
            total_count = self.identification_metrics['total_identifications']
            current_avg = self.identification_metrics['average_computation_time']
            
            new_avg = ((total_count - 1) * current_avg + computation_time) / total_count
            self.identification_metrics['average_computation_time'] = new_avg
            
        except Exception as e:
            self._log("error", f"Metrics update failed: {e}")
    
    def _result_to_dict(self, result: IdentificationResult) -> Dict[str, Any]:
        """将识别结果转换为字典"""
        return {
            'parameters': result.parameters,
            'objective_value': result.objective_value,
            'iterations': result.iterations,
            'convergence_achieved': result.convergence_achieved,
            'computation_time': result.computation_time,
            'validation_metrics': result.validation_metrics,
            'method': result.method,
            'timestamp': result.timestamp
        }
    
    def _handle_data_update(self, message: Message):
        """处理数据更新"""
        try:
            # 将新数据添加到缓冲区
            data_record = {
                'timestamp': message.get('_timestamp', time.time()),
                **message
            }
            
            self.data_buffer.append(data_record)
            
            # 在线更新
            if self.identification_method in [IdentificationMethod.ONLINE, IdentificationMethod.RECURSIVE]:
                self.update_online(data_record)
            
        except Exception as e:
            self._log("error", f"Data update handling failed: {e}")
    
    def _handle_identification_request(self, message: Message):
        """处理识别请求"""
        try:
            request_type = message.get('request_type', 'fit')
            
            if request_type == 'fit':
                data = message.get('data', [])
                method = message.get('method', 'offline')
                
                if data:
                    parameters = self.fit_parameters(data, method)
                    
                    # 发送响应
                    if self.event_bus:
                        response_topic = message.get('response_topic', f'identification.response.{self.agent_id}')
                        self.event_bus.publish(response_topic, {
                            'request_id': message.get('request_id'),
                            'status': 'success',
                            'parameters': parameters
                        })
            
        except Exception as e:
            self._log("error", f"Identification request handling failed: {e}")
