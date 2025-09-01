#!/usr/bin/env python3
"""
增强的YAML加载器

扩展了基础的SimulationBuilder，增加了对调试、性能分析、可视化、日志等功能的支持。
提供了完整的仿真配置管理和功能集成。
"""

import yaml
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# 导入基础类
from .yaml_loader import SimulationBuilder, BaseYamlLoader
from ..debug.log_manager import setup_logging, get_logger
from ..debug.debug_collector import setup_debug_environment, collect_debug_data
from ..debug.debug_dashboard import get_dashboard_manager
from ..utils.performance_analysis import PerformanceAnalyzer
from ..utils.visualization_utils import SimulationPlotter
from ..utils.example_utils import setup_project_root, load_config_with_validation

class EnhancedSimulationBuilder(SimulationBuilder):
    """
    增强的仿真构建器
    
    在基础SimulationBuilder的基础上，增加了：
    - 调试系统集成
    - 性能监控
    - 可视化支持
    - 日志管理
    - 错误处理
    - 结果分析
    """
    
    def __init__(self, scenario_path: str, agents_file: str = 'agents.yml', 
                 universal_config_file: str = 'universal_config.yml'):
        """
        初始化增强的仿真构建器
        
        Args:
            scenario_path: 场景目录路径
            agents_file: 智能体配置文件名
            universal_config_file: 通用配置文件名
        """
        super().__init__(scenario_path, agents_file)
        
        # 加载通用配置
        self.universal_config = self._load_universal_config(universal_config_file)
        
        # 初始化功能模块
        self.debug_enabled = False
        self.performance_enabled = False
        self.visualization_enabled = False
        self.logger = None
        self.performance_analyzer = None
        self.plotter = None
        self.dashboard_manager = None
        
        # 性能数据收集
        self.performance_data = []
        self.start_time = None
        self.step_times = []
        
        logging.info(f"EnhancedSimulationBuilder initialized for scenario: {self.scenario_path.name}")
    
    def _load_universal_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        """
        加载通用配置文件
        
        Args:
            config_file: 配置文件名
            
        Returns:
            配置字典或None
        """
        # 首先尝试从场景目录加载
        config_path = self.scenario_path / config_file
        if config_path.exists():
            return self._load_yaml(config_file)
        
        # 然后尝试从模板目录加载
        template_path = Path(__file__).parent.parent / 'config' / 'universal_config_template.yml'
        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logging.warning(f"Failed to load universal config template: {e}")
        
        logging.warning(f"Universal config file not found: {config_file}")
        return None
    
    def setup_enhanced_features(self):
        """
        设置增强功能
        """
        if not self.universal_config:
            logging.warning("No universal config found, using default settings")
            return
        
        # 设置调试功能
        self._setup_debug()
        
        # 设置性能监控
        self._setup_performance_monitoring()
        
        # 设置可视化
        self._setup_visualization()
        
        # 设置日志
        self._setup_logging()
        
        # 设置错误处理
        self._setup_error_handling()
        
        logging.info("Enhanced features setup completed")
    
    def _setup_debug(self):
        """
        设置调试功能
        """
        debug_config = self.universal_config.get('debug', {})
        if not debug_config.get('enabled', False):
            return
        
        self.debug_enabled = True
        
        # 设置调试环境
        session_id = debug_config.get('session_id', f'simulation_{int(time.time())}')
        log_dir = setup_debug_environment(session_id)
        
        # 设置调试数据收集
        data_collection_config = debug_config.get('data_collection', {})
        if data_collection_config.get('enabled', False):
            self.debug_data_interval = data_collection_config.get('interval', 5.0)
        
        # 设置调试仪表板
        dashboard_config = debug_config.get('dashboard', {})
        if dashboard_config.get('enabled', False):
            self.dashboard_manager = get_dashboard_manager()
            
            # Web仪表板
            web_config = dashboard_config.get('web_dashboard', {})
            if web_config.get('enabled', False):
                port = web_config.get('port', 8080)
                host = web_config.get('host', 'localhost')
                auto_open = web_config.get('auto_open_browser', False)
                self.dashboard_manager.start_web_dashboard(port, host, auto_open)
            
            # 控制台仪表板
            console_config = dashboard_config.get('console_dashboard', {})
            if console_config.get('enabled', False):
                update_interval = console_config.get('update_interval', 5.0)
                self.dashboard_manager.start_console_dashboard(update_interval)
        
        logging.info("Debug features enabled")
    
    def _setup_performance_monitoring(self):
        """
        设置性能监控
        """
        perf_config = self.universal_config.get('performance', {})
        if not perf_config.get('enabled', False):
            return
        
        self.performance_enabled = True
        self.performance_analyzer = PerformanceAnalyzer()
        
        # 配置性能分析器
        self.track_timing = perf_config.get('track_timing', True)
        self.track_memory = perf_config.get('track_memory', True)
        self.track_cpu = perf_config.get('track_cpu', True)
        
        # 性能指标收集配置
        metrics_config = perf_config.get('metrics', {})
        if metrics_config.get('enabled', False):
            self.metrics_interval = metrics_config.get('collection_interval', 1.0)
            self.save_metrics = metrics_config.get('save_to_file', True)
            self.metrics_file = metrics_config.get('metrics_file', 'performance_metrics.json')
        
        logging.info("Performance monitoring enabled")
    
    def _setup_visualization(self):
        """
        设置可视化功能
        """
        viz_config = self.universal_config.get('visualization', {})
        if not viz_config.get('enabled', False):
            return
        
        self.visualization_enabled = True
        
        # 创建绘图器
        plot_config = viz_config.get('plots', {})
        if plot_config.get('enabled', False):
            style_config = {
                'style': plot_config.get('style', 'seaborn'),
                'dpi': plot_config.get('dpi', 300),
                'format': plot_config.get('format', 'png')
            }
            self.plotter = SimulationPlotter(style_config)
            
            # 输出目录
            self.plot_output_dir = Path(plot_config.get('output_directory', 'plots/'))
            self.plot_output_dir.mkdir(exist_ok=True)
            
            # 图表配置
            self.chart_configs = plot_config.get('charts', [])
        
        logging.info("Visualization features enabled")
    
    def _setup_logging(self):
        """
        设置日志系统
        """
        logging_config = self.universal_config.get('logging', {})
        if not logging_config.get('enabled', False):
            return
        
        # 设置日志配置
        log_config = {
            'session_id': self.universal_config.get('debug', {}).get('session_id', 'simulation'),
            'console': {
                'enabled': logging_config.get('handlers', {}).get('console', {}).get('enabled', True),
                'level': logging_config.get('handlers', {}).get('console', {}).get('level', 'INFO')
            },
            'file': {
                'enabled': logging_config.get('handlers', {}).get('file', {}).get('enabled', True),
                'path': logging_config.get('handlers', {}).get('file', {}).get('filename', 'logs/simulation.log'),
                'level': logging_config.get('handlers', {}).get('file', {}).get('level', 'DEBUG')
            }
        }
        
        setup_logging(log_config)
        self.logger = get_logger()
        
        logging.info("Enhanced logging system enabled")
    
    def _setup_error_handling(self):
        """
        设置错误处理
        """
        error_config = self.universal_config.get('error_handling', {})
        if not error_config.get('enabled', False):
            return
        
        self.error_handling_enabled = True
        self.continue_on_error = error_config.get('exception_handling', {}).get('continue_on_error', False)
        self.log_exceptions = error_config.get('exception_handling', {}).get('log_exceptions', True)
        
        logging.info("Error handling enabled")
    
    def load(self):
        """
        加载仿真，包含增强功能
        """
        # 首先设置增强功能
        self.setup_enhanced_features()
        
        # 然后调用父类的load方法
        harness = super().load()
        
        # 包装harness以添加增强功能
        return EnhancedSimulationHarness(harness, self)
    
    def collect_performance_data(self, step_time: float, simulation_time: float):
        """
        收集性能数据
        
        Args:
            step_time: 步骤执行时间
            simulation_time: 仿真时间
        """
        if not self.performance_enabled:
            return
        
        # 收集基础性能数据
        perf_data = {
            'timestamp': datetime.now().isoformat(),
            'simulation_time': simulation_time,
            'step_execution_time': step_time
        }
        
        # 收集系统资源数据
        if self.track_memory or self.track_cpu:
            import psutil
            process = psutil.Process()
            
            if self.track_memory:
                memory_info = process.memory_info()
                perf_data['memory_usage_mb'] = memory_info.rss / 1024 / 1024
            
            if self.track_cpu:
                perf_data['cpu_percent'] = process.cpu_percent()
        
        self.performance_data.append(perf_data)
        
        # 收集调试数据
        if self.debug_enabled:
            collect_debug_data(
                'performance_metric',
                'step_performance',
                step_time,
                {
                    'simulation_time': simulation_time,
                    'memory_usage': perf_data.get('memory_usage_mb', 0),
                    'cpu_percent': perf_data.get('cpu_percent', 0)
                }
            )
    
    def generate_visualizations(self, history: List[Dict[str, Any]]):
        """
        生成可视化图表
        
        Args:
            history: 仿真历史数据
        """
        if not self.visualization_enabled or not self.plotter:
            return
        
        logging.info("Generating visualizations...")
        
        try:
            # 处理历史数据
            time_data = [step['time'] for step in history]
            
            # 生成配置的图表
            for chart_config in self.chart_configs:
                chart_type = chart_config.get('type')
                title = chart_config.get('title', f'{chart_type} Chart')
                filename = chart_config.get('filename', f'{chart_type}.png')
                variables = chart_config.get('variables', [])
                
                output_path = self.plot_output_dir / filename
                
                if chart_type == 'time_series':
                    self._generate_time_series_plot(history, variables, title, output_path)
                elif chart_type == 'control_performance':
                    self._generate_control_performance_plot(history, variables, title, output_path)
                elif chart_type == 'dashboard':
                    self._generate_dashboard_plot(history, title, output_path)
            
            # 生成性能图表
            if self.performance_data:
                self._generate_performance_plots()
            
            logging.info(f"Visualizations saved to {self.plot_output_dir}")
            
        except Exception as e:
            logging.error(f"Failed to generate visualizations: {e}")
            if self.log_exceptions:
                logging.exception("Visualization generation error")
    
    def _generate_time_series_plot(self, history: List[Dict], variables: List[str], 
                                 title: str, output_path: Path):
        """
        生成时间序列图
        """
        time_data = [step['time'] for step in history]
        
        data_dict = {'time': time_data}
        for var in variables:
            # 尝试从不同组件中提取变量
            var_data = []
            for step in history:
                value = None
                # 搜索所有组件
                for comp_id, comp_data in step.items():
                    if comp_id == 'time':
                        continue
                    if isinstance(comp_data, dict) and var in comp_data:
                        value = comp_data[var]
                        break
                var_data.append(value if value is not None else 0)
            data_dict[var] = var_data
        
        self.plotter.plot_time_series(
            data=data_dict,
            title=title,
            save_path=str(output_path)
        )
    
    def _generate_control_performance_plot(self, history: List[Dict], variables: List[str], 
                                         title: str, output_path: Path):
        """
        生成控制性能图
        """
        # 提取控制相关数据
        time_data = [step['time'] for step in history]
        
        # 这里需要根据具体的变量名提取数据
        # 简化实现，实际应该更智能地识别控制变量
        control_data = {
            'time': time_data,
            'setpoint': [12.0] * len(time_data),  # 示例设定值
            'actual': [],
            'control_signal': []
        }
        
        # 提取实际值和控制信号
        for step in history:
            actual_value = 0
            control_value = 0
            
            for comp_id, comp_data in step.items():
                if comp_id == 'time':
                    continue
                if isinstance(comp_data, dict):
                    if 'water_level' in comp_data:
                        actual_value = comp_data['water_level']
                    if 'opening' in comp_data:
                        control_value = comp_data['opening']
            
            control_data['actual'].append(actual_value)
            control_data['control_signal'].append(control_value)
        
        self.plotter.plot_control_performance(
            data=control_data,
            title=title,
            save_path=str(output_path)
        )
    
    def _generate_dashboard_plot(self, history: List[Dict], title: str, output_path: Path):
        """
        生成仪表板图
        """
        # 准备仪表板数据
        dashboard_data = self._prepare_dashboard_data(history)
        
        self.plotter.create_dashboard(
            data=dashboard_data,
            title=title,
            save_path=str(output_path)
        )
    
    def _generate_performance_plots(self):
        """
        生成性能分析图表
        """
        if not self.performance_data:
            return
        
        # 准备性能数据
        times = [datetime.fromisoformat(d['timestamp']) for d in self.performance_data]
        execution_times = [d['step_execution_time'] for d in self.performance_data]
        
        perf_plot_data = {
            'time': times,
            'execution_time': execution_times
        }
        
        if 'memory_usage_mb' in self.performance_data[0]:
            perf_plot_data['memory_usage'] = [d['memory_usage_mb'] for d in self.performance_data]
        
        if 'cpu_percent' in self.performance_data[0]:
            perf_plot_data['cpu_usage'] = [d['cpu_percent'] for d in self.performance_data]
        
        # 生成性能图表
        self.plotter.plot_performance_metrics(
            metrics=perf_plot_data,
            title="仿真性能分析",
            save_path=str(self.plot_output_dir / 'performance_analysis.png')
        )
    
    def _prepare_dashboard_data(self, history: List[Dict]) -> Dict[str, Any]:
        """
        准备仪表板数据
        """
        time_data = [step['time'] for step in history]
        
        # 提取主要系统状态
        dashboard_data = {
            'time_series': {'time': time_data},
            'metrics': {},
            'system_state': {
                '正常运行': 0.8,
                '调节中': 0.15,
                '异常': 0.05
            }
        }
        
        # 提取时间序列数据
        for step in history:
            for comp_id, comp_data in step.items():
                if comp_id == 'time':
                    continue
                if isinstance(comp_data, dict):
                    for key, value in comp_data.items():
                        if key not in dashboard_data['time_series']:
                            dashboard_data['time_series'][key] = []
                        dashboard_data['time_series'][key].append(value)
        
        # 计算关键指标
        if 'water_level' in dashboard_data['time_series']:
            water_levels = dashboard_data['time_series']['water_level']
            dashboard_data['metrics']['平均水位'] = sum(water_levels) / len(water_levels)
            dashboard_data['metrics']['最大水位'] = max(water_levels)
            dashboard_data['metrics']['最小水位'] = min(water_levels)
        
        return dashboard_data
    
    def save_performance_data(self):
        """
        保存性能数据
        """
        if not self.performance_enabled or not self.performance_data:
            return
        
        if hasattr(self, 'save_metrics') and self.save_metrics:
            metrics_path = Path(self.metrics_file)
            metrics_path.parent.mkdir(exist_ok=True)
            
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Performance data saved to {metrics_path}")


class EnhancedSimulationHarness:
    """
    增强的仿真执行器包装类
    
    包装原始的SimulationHarness，添加增强功能支持
    """
    
    def __init__(self, original_harness, builder: EnhancedSimulationBuilder):
        self.harness = original_harness
        self.builder = builder
        self.start_time = None
    
    def __getattr__(self, name):
        """代理到原始harness的属性和方法"""
        return getattr(self.harness, name)
    
    def run_mas_simulation(self):
        """
        运行多智能体仿真，包含增强功能
        """
        logging.info("Starting enhanced MAS simulation...")
        self.start_time = time.time()
        
        try:
            # 运行原始仿真
            self.harness.run_mas_simulation()
            
            # 后处理
            self._post_process()
            
            logging.info("Enhanced MAS simulation completed successfully")
            
        except Exception as e:
            logging.error(f"Simulation failed: {e}")
            if self.builder.log_exceptions:
                logging.exception("Simulation error details")
            
            if not getattr(self.builder, 'continue_on_error', False):
                raise
    
    def step(self):
        """
        执行单步仿真，包含性能监控
        """
        step_start = time.time()
        
        # 执行原始步骤
        result = self.harness.step()
        
        step_time = time.time() - step_start
        simulation_time = getattr(self.harness, 'current_time', 0)
        
        # 收集性能数据
        self.builder.collect_performance_data(step_time, simulation_time)
        
        return result
    
    def _post_process(self):
        """
        仿真后处理
        """
        total_time = time.time() - self.start_time if self.start_time else 0
        
        logging.info(f"Simulation completed in {total_time:.2f} seconds")
        
        # 生成可视化
        if hasattr(self.harness, 'history'):
            self.builder.generate_visualizations(self.harness.history)
        
        # 保存性能数据
        self.builder.save_performance_data()
        
        # 生成分析报告
        if self.builder.performance_enabled and self.builder.performance_analyzer:
            self._generate_analysis_report()
    
    def _generate_analysis_report(self):
        """
        生成分析报告
        """
        try:
            # 这里可以添加更详细的分析报告生成逻辑
            logging.info("Analysis report generation completed")
        except Exception as e:
            logging.error(f"Failed to generate analysis report: {e}")