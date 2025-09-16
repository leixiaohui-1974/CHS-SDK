# -*- coding: utf-8 -*-
"""
增强的YAML配置加载器
扩展SimulationBuilder类以支持通用配置文件的所有功能
"""

import os
import sys
import yaml
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder


class EnhancedSimulationBuilder(SimulationBuilder):
    """
    增强的仿真构建器
    扩展基础SimulationBuilder以支持通用配置文件的所有功能
    """
    
    def __init__(self, scenario_path=None, agents_file='agents.yml'):
        # 如果没有提供scenario_path，使用当前目录
        if scenario_path is None:
            scenario_path = "."
        super().__init__(scenario_path, agents_file)
        self.enhanced_config = None
        self.performance_monitor = None
        self.debug_manager = None
        self.visualization_manager = None
        self.logger_manager = None
        self.error_handler = None
        self.analysis_manager = None
        self.cache_manager = None
        self.environment_manager = None
        
    def load_enhanced_config(self, config_file):
        """
        加载增强配置文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.enhanced_config = yaml.safe_load(f)
                
            # 设置增强功能
            self._setup_enhanced_features()
            
            # 加载基础仿真配置
            if 'simulation' in self.enhanced_config:
                self._load_simulation_config()
                
            return self.enhanced_config
            
        except Exception as e:
            print(f"加载增强配置文件失败: {e}")
            raise
            
    def _load_simulation_config(self):
        """
        加载仿真基础配置到原有的配置结构中
        """
        sim_config = self.enhanced_config.get('simulation', {})
        
        # 将仿真配置映射到原有结构
        if not hasattr(self, 'config') or self.config is None:
            self.config = {}
            
        # 时间配置
        time_config = sim_config.get('time', {})
        if time_config:
            self.config['time'] = {
                'start_time': time_config['start_time'],
                'end_time': time_config['end_time'],
                'time_step': time_config['time_step'],
                'output_interval': time_config.get('output_interval', 1.0)
            }
            
        # 求解器配置
        solver_config = sim_config.get('solver', {})
        if solver_config:
            self.config['solver'] = {
                'type': solver_config.get('type', 'runge_kutta'),
                'order': solver_config.get('order', 4),
                'tolerance': solver_config.get('tolerance', 1e-6)
            }
            
    def _setup_enhanced_features(self):
        """
        设置增强功能
        """
        if not self.enhanced_config:
            return
            
        # 设置环境管理
        self._setup_environment_management()
        
        # 设置缓存管理
        if self.enhanced_config.get('caching', {}).get('enabled', False):
            self._setup_caching()
            
        # 设置调试功能
        if self.enhanced_config.get('debug', {}).get('enabled', False):
            self._setup_debug_features()
            
        # 设置性能监控
        if self.enhanced_config.get('performance', {}).get('enabled', False):
            self._setup_performance_monitoring()
            
        # 设置可视化
        if self.enhanced_config.get('visualization', {}).get('enabled', False):
            self._setup_visualization()
            
        # 设置日志管理
        if self.enhanced_config.get('logging', {}).get('enabled', False):
            self._setup_logging()
            
        # 设置错误处理
        if self.enhanced_config.get('error_handling', {}).get('enabled', False):
            self._setup_error_handling()
            
        # 设置分析功能
        if self.enhanced_config.get('analysis', {}).get('enabled', False):
            self._setup_analysis()
            
    def _setup_debug_features(self):
        """
        设置调试功能
        """
        debug_config = self.enhanced_config.get('debug', {})
        
        class DebugManager:
            def __init__(self, config):
                self.config = config
                self.session_id = config.get('session_id', 'debug_session')
                self.data_collection = config.get('data_collection', {})
                self.dashboard_config = config.get('dashboard', {})
                
            def start_debug_session(self):
                """
                启动调试会话
                """
                print(f"启动调试会话: {self.session_id}")
                
                # 设置数据收集
                if self.data_collection.get('enabled', False):
                    self._setup_data_collection()
                    
                # 设置调试仪表板
                if self.dashboard_config.get('enabled', False):
                    self._setup_dashboard()
                    
            def _setup_data_collection(self):
                """
                设置数据收集
                """
                variables = self.data_collection.get('variables', [])
                interval = self.data_collection.get('interval', 1.0)
                print(f"设置数据收集: 变量={variables}, 间隔={interval}s")
                
            def _setup_dashboard(self):
                """
                设置调试仪表板
                """
                web_config = self.dashboard_config.get('web_dashboard', {})
                if web_config.get('enabled', False):
                    port = web_config.get('port', 8080)
                    print(f"启动Web调试仪表板: http://localhost:{port}")
                    
        self.debug_manager = DebugManager(debug_config)
        self.debug_manager.start_debug_session()
        
    def _setup_performance_monitoring(self):
        """
        设置性能监控
        """
        perf_config = self.enhanced_config.get('performance', {})
        
        class PerformanceMonitor:
            def __init__(self, config):
                self.config = config
                self.metrics = {}
                self.start_time = None
                
            def start_monitoring(self):
                """
                开始性能监控
                """
                self.start_time = time.time()
                print("开始性能监控")
                
            def record_metric(self, name, value):
                """
                记录性能指标
                """
                if name not in self.metrics:
                    self.metrics[name] = []
                self.metrics[name].append({
                    'timestamp': time.time(),
                    'value': value
                })
                
            def get_performance_report(self):
                """
                获取性能报告
                """
                if self.start_time:
                    total_time = time.time() - self.start_time
                    return {
                        'total_execution_time': total_time,
                        'metrics': self.metrics
                    }
                return {}
                
        self.performance_monitor = PerformanceMonitor(perf_config)
        self.performance_monitor.start_monitoring()
        
    def _setup_visualization(self):
        """
        设置可视化功能
        """
        viz_config = self.enhanced_config.get('visualization', {})
        
        class VisualizationManager:
            def __init__(self, config):
                self.config = config
                self.plots_config = config.get('plots', {})
                
            def create_visualizations(self, simulation_data):
                """
                创建可视化图表
                """
                if not self.plots_config.get('enabled', False):
                    return
                    
                charts = self.plots_config.get('charts', [])
                output_dir = self.plots_config.get('output_directory', 'plots/')
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)
                
                for chart in charts:
                    chart_type = chart.get('type')
                    title = chart.get('title', 'Untitled Chart')
                    filename = chart.get('filename', 'chart')
                    
                    print(f"创建图表: {title} ({chart_type})")
                    # 这里可以集成实际的绘图逻辑
                    
        self.visualization_manager = VisualizationManager(viz_config)
        
    def _setup_logging(self):
        """
        设置日志管理
        """
        log_config = self.enhanced_config.get('logging', {})
        
        class LoggerManager:
            def __init__(self, config):
                self.config = config
                self.loggers = {}
                
            def setup_loggers(self):
                """
                设置日志记录器
                """
                log_dir = self.config.get('log_directory', 'logs/')
                os.makedirs(log_dir, exist_ok=True)
                
                # 设置根日志级别
                levels = self.config.get('levels', {})
                root_level = levels.get('root', 'INFO')
                logging.getLogger().setLevel(getattr(logging, root_level))
                
                # 设置处理器
                handlers = self.config.get('handlers', {})
                
                # 控制台处理器
                if handlers.get('console', {}).get('enabled', False):
                    console_handler = logging.StreamHandler()
                    console_level = handlers['console'].get('level', 'INFO')
                    console_handler.setLevel(getattr(logging, console_level))
                    
                    formatter = logging.Formatter(
                        handlers['console'].get('format', 
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    )
                    console_handler.setFormatter(formatter)
                    logging.getLogger().addHandler(console_handler)
                    
                # 文件处理器
                if handlers.get('file', {}).get('enabled', False):
                    file_config = handlers['file']
                    filename = file_config.get('filename', 'simulation.log')
                    file_handler = logging.FileHandler(filename, encoding='utf-8')
                    file_level = file_config.get('level', 'DEBUG')
                    file_handler.setLevel(getattr(logging, file_level))
                    
                    formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                    file_handler.setFormatter(formatter)
                    logging.getLogger().addHandler(file_handler)
                    
                print(f"日志系统已配置，日志目录: {log_dir}")
                
        self.logger_manager = LoggerManager(log_config)
        self.logger_manager.setup_loggers()
        
    def _setup_error_handling(self):
        """
        设置错误处理
        """
        error_config = self.enhanced_config.get('error_handling', {})
        
        class ErrorHandler:
            def __init__(self, config):
                self.config = config
                self.error_policy = config.get('error_policy', 'strict')
                
            def handle_error(self, error, context=None):
                """
                处理错误
                """
                error_type = type(error).__name__
                
                # 错误分类
                classification = self.config.get('classification', {})
                critical_errors = classification.get('critical_errors', [])
                recoverable_errors = classification.get('recoverable_errors', [])
                
                if error_type in critical_errors:
                    print(f"严重错误: {error}")
                    if self.error_policy == 'strict':
                        raise error
                elif error_type in recoverable_errors:
                    print(f"可恢复错误: {error}")
                    # 实现恢复逻辑
                else:
                    print(f"未分类错误: {error}")
                    
        self.error_handler = ErrorHandler(error_config)
        
    def _setup_analysis(self):
        """
        设置分析功能
        """
        analysis_config = self.enhanced_config.get('analysis', {})
        
        class AnalysisManager:
            def __init__(self, config):
                self.config = config
                self.results = {}
                
            def analyze_results(self, simulation_data):
                """
                分析仿真结果
                """
                results = {}
                
                if self.config.get('control_performance', {}).get('enabled', False):
                    results['control_performance'] = self._analyze_control_performance(simulation_data)
                    
                if self.config.get('statistical', {}).get('enabled', False):
                    results['statistical'] = self._analyze_statistics(simulation_data)
                    
                if self.config.get('system_identification', {}).get('enabled', False):
                    results['system_identification'] = self._analyze_system_identification(simulation_data)
                    
                if self.config.get('signal_processing', {}).get('enabled', False):
                    results['signal_processing'] = self._analyze_signal_processing(simulation_data)
                    
                return results
                
            def _analyze_control_performance(self, data):
                """
                控制性能分析
                """
                # 实现控制性能分析逻辑
                return {'settling_time': 0, 'overshoot': 0, 'steady_state_error': 0}
                
            def _analyze_statistics(self, data):
                """
                统计分析
                """
                # 实现统计分析逻辑
                return {'mean': 0, 'std': 0, 'correlation': {}}
                
            def _analyze_system_identification(self, data):
                """
                系统识别分析
                """
                # 实现系统识别逻辑
                return {'model_order': 2, 'parameters': [], 'validation_score': 0.95}
                
            def _analyze_signal_processing(self, data):
                """
                信号处理分析
                """
                # 实现信号处理逻辑
                return {'frequency_response': {}, 'spectral_analysis': {}}
                
        self.analysis_manager = AnalysisManager(analysis_config)
        
    def _setup_environment_management(self):
        """
        设置环境管理
        """
        env_config = self.enhanced_config.get('environment', {})
        
        class EnvironmentManager:
            def __init__(self, config):
                self.config = config
                self.current_env = config.get('current', 'development')
                
            def setup_environment(self):
                """
                设置环境配置
                """
                env_settings = self.config.get(self.current_env, {})
                
                # 应用环境特定设置
                if env_settings.get('debug', False):
                    import logging
                    logging.getLogger().setLevel(logging.DEBUG)
                    
                # 设置环境变量
                custom_vars = self.config.get('variables', {}).get('custom_vars', {})
                import os
                for key, value in custom_vars.items():
                    os.environ[key] = str(value)
                    
                return env_settings
                
        self.environment_manager = EnvironmentManager(env_config)
        self.environment_manager.setup_environment()
        
    def _setup_caching(self):
        """
        设置缓存管理
        """
        cache_config = self.enhanced_config.get('caching', {})
        
        class CacheManager:
            def __init__(self, config):
                self.config = config
                self.cache = {}
                self.cache_directory = config.get('cache_directory', 'cache/')
                
            def get(self, key):
                """
                获取缓存数据
                """
                return self.cache.get(key)
                
            def set(self, key, value):
                """
                设置缓存数据
                """
                self.cache[key] = value
                
            def clear(self):
                """
                清空缓存
                """
                self.cache.clear()
                
        self.cache_manager = CacheManager(cache_config)
        
    def build_simulation(self, enhanced_config_file=None):
        """
        构建增强仿真
        
        Args:
            enhanced_config_file: 增强配置文件路径
            
        Returns:
            构建的仿真对象
        """
        try:
            # 加载增强配置
            if enhanced_config_file:
                self.load_enhanced_config(enhanced_config_file)
                
            # 构建基础仿真
            simulation = super().build_simulation()
            
            # 添加增强功能到仿真对象
            if hasattr(simulation, '__dict__'):
                simulation.performance_monitor = self.performance_monitor
                simulation.debug_manager = self.debug_manager
                simulation.visualization_manager = self.visualization_manager
                simulation.analysis_manager = self.analysis_manager
                simulation.error_handler = self.error_handler
                
            return simulation
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(e, context='build_simulation')
            else:
                raise
                
    def run_enhanced_simulation(self, enhanced_config_file=None):
        """
        运行增强仿真
        
        Args:
            enhanced_config_file: 增强配置文件路径
            
        Returns:
            仿真结果和分析报告
        """
        try:
            # 构建仿真
            simulation = self.build_simulation(enhanced_config_file)
            
            # 运行仿真
            print("开始运行增强仿真...")
            if self.performance_monitor:
                self.performance_monitor.start_monitoring()
                
            # 这里应该调用实际的仿真运行逻辑
            # results = simulation.run()
            results = {'simulation_data': 'mock_data'}  # 模拟数据
            
            # 分析结果
            analysis_results = {}
            if self.analysis_manager:
                analysis_results = self.analysis_manager.analyze_results(results)
                
            # 创建可视化
            if self.visualization_manager:
                self.visualization_manager.create_visualizations(results)
                
            # 生成性能报告
            performance_report = {}
            if self.performance_monitor:
                performance_report = self.performance_monitor.get_performance_report()
                
            return {
                'simulation_results': results,
                'analysis_results': analysis_results,
                'performance_report': performance_report
            }
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(e, context='run_enhanced_simulation')
            else:
                raise


def load_universal_config(config_file, scenario_path=None):
    """
    加载通用配置文件的便捷函数
    
    Args:
        config_file: 配置文件路径
        scenario_path: 场景目录路径（可选）
        
    Returns:
        EnhancedSimulationBuilder实例
    """
    builder = EnhancedSimulationBuilder(scenario_path)
    builder.load_enhanced_config(config_file)
    return builder


if __name__ == "__main__":
    # 测试示例
    config_file = "example_universal_config.yml"
    
    if os.path.exists(config_file):
        builder = load_universal_config(config_file)
        results = builder.run_enhanced_simulation()
        print("仿真完成！")
        print(f"结果: {results}")
    else:
        print(f"配置文件不存在: {config_file}")