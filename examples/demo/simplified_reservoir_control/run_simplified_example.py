#!/usr/bin/env python3
"""
简化的水库控制示例

本示例展示如何使用通用工具库来简化仿真代码，让开发者专注于业务逻辑。

使用的通用工具：
- SimulationBuilder: 简化仿真系统构建
- SimulationPlotter: 统一的可视化
- PerformanceAnalyzer: 标准化性能分析
- ExampleRunner: 通用运行框架
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import logging
from typing import Dict, Any

# 导入通用工具
from core_lib.utils.simulation_builder import SimulationBuilder, PresetSimulations
from core_lib.utils.visualization_utils import SimulationPlotter, quick_plot
from core_lib.utils.performance_analysis import PerformanceAnalyzer, quick_analysis
from core_lib.utils.example_utils import ExampleRunner, print_section_header, print_performance_summary

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedReservoirControlExample(ExampleRunner):
    """
    简化的水库控制示例类
    
    展示如何使用通用工具库来减少代码复杂度。
    """
    
    def __init__(self):
        super().__init__(__file__)
        self.example_name = "简化水库控制示例"
        self.description = "使用通用工具库构建的水库PID控制系统"
        
        # 仿真参数
        self.simulation_params = {
            'duration': 200,
            'dt': 1.0,
            'setpoint': 12.0
        }
        
        # 初始化工具
        self.plotter = SimulationPlotter()
        self.analyzer = PerformanceAnalyzer(dt=self.simulation_params['dt'])
    
    def setup_simulation(self) -> SimulationBuilder:
        """
        设置仿真系统
        
        Returns:
            SimulationBuilder: 配置好的仿真构建器
        """
        print_section_header("设置仿真系统")
        
        # 使用预设仿真模式
        builder = PresetSimulations.single_reservoir_control(
            reservoir_setpoint=self.simulation_params['setpoint'],
            simulation_duration=self.simulation_params['duration'],
            dt=self.simulation_params['dt']
        )
        
        logger.info("仿真系统设置完成")
        return builder
    
    def run_simulation(self, builder: SimulationBuilder) -> Dict[str, Any]:
        """
        运行仿真
        
        Args:
            builder: 仿真构建器
            
        Returns:
            Dict[str, Any]: 仿真结果
        """
        print_section_header("运行仿真")
        
        # 运行仿真
        results = builder.run()
        
        logger.info(f"仿真运行完成，时长: {self.simulation_params['duration']}s")
        return results
    
    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析仿真结果
        
        Args:
            results: 仿真结果
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        print_section_header("性能分析")
        
        # 提取数据
        time_data = results.get('time', [])
        reservoir_data = results.get('reservoir_water_level', [])
        gate_data = results.get('gate_opening', [])
        
        if not time_data or not reservoir_data:
            logger.warning("仿真结果数据不完整")
            return {}
        
        # 转换为numpy数组
        time = np.array(time_data)
        water_level = np.array(reservoir_data)
        gate_opening = np.array(gate_data) if gate_data else None
        
        # 控制性能分析
        control_metrics = self.analyzer.calculate_control_metrics(
            setpoint=self.simulation_params['setpoint'],
            actual=water_level,
            control_signal=gate_opening,
            time=time
        )
        
        # 统计分析
        statistical_metrics = self.analyzer.calculate_statistical_metrics(water_level)
        
        # 稳定性分析
        stability_metrics = self.analyzer.calculate_stability_metrics(water_level)
        
        # 振荡检测
        oscillation_results = self.analyzer.detect_oscillations(water_level)
        
        # 生成综合报告
        performance_report = self.analyzer.generate_performance_report(
            control_metrics=control_metrics,
            statistical_metrics=statistical_metrics,
            stability_metrics=stability_metrics,
            save_path=self.get_output_path('performance_report.json')
        )
        
        # 打印关键指标
        print_performance_summary({
            'RMSE': control_metrics.rmse,
            '稳态误差': control_metrics.steady_state_error,
            '调节时间': control_metrics.settling_time,
            '超调量(%)': control_metrics.overshoot,
            '稳定性指数': stability_metrics['stability_index'],
            '收敛误差': stability_metrics['convergence_error'],
            '综合评分': performance_report['overall_score']
        })
        
        return {
            'time': time,
            'water_level': water_level,
            'gate_opening': gate_opening,
            'control_metrics': control_metrics,
            'statistical_metrics': statistical_metrics,
            'stability_metrics': stability_metrics,
            'oscillation_results': oscillation_results,
            'performance_report': performance_report
        }
    
    def create_visualizations(self, analysis_results: Dict[str, Any]) -> None:
        """
        创建可视化图表
        
        Args:
            analysis_results: 分析结果
        """
        print_section_header("生成可视化图表")
        
        time = analysis_results['time']
        water_level = analysis_results['water_level']
        gate_opening = analysis_results['gate_opening']
        control_metrics = analysis_results['control_metrics']
        
        # 1. 控制性能图
        self.plotter.plot_control_performance(
            time=time,
            setpoint=self.simulation_params['setpoint'],
            actual=water_level,
            control_signal=gate_opening,
            title="水库水位控制性能",
            save_path=self.get_output_path('control_performance.png')
        )
        
        # 2. 时间序列图
        time_series_data = {
            '水位 (m)': water_level,
            '闸门开度': gate_opening if gate_opening is not None else np.zeros_like(water_level)
        }
        
        self.plotter.plot_time_series(
            data=time_series_data,
            time=time,
            title="系统状态时间序列",
            xlabel="时间 (s)",
            save_path=self.get_output_path('time_series.png')
        )
        
        # 3. 性能指标图
        metrics_data = {
            'RMSE': control_metrics.rmse,
            'MAE': control_metrics.mae,
            '稳态误差': control_metrics.steady_state_error,
            '超调量(%)': control_metrics.overshoot,
            '调节时间(s)': control_metrics.settling_time / 10,  # 缩放以便显示
            '控制努力': control_metrics.control_effort / 1000  # 缩放以便显示
        }
        
        self.plotter.plot_performance_metrics(
            metrics=metrics_data,
            title="控制性能指标",
            save_path=self.get_output_path('performance_metrics.png')
        )
        
        # 4. 综合仪表板
        dashboard_data = {
            'time_series': {
                'time': time,
                '水位': water_level,
                '设定值': np.full_like(time, self.simulation_params['setpoint']),
                '闸门开度': gate_opening if gate_opening is not None else np.zeros_like(time)
            },
            'metrics': {
                'RMSE': control_metrics.rmse,
                '稳态误差': control_metrics.steady_state_error,
                '超调量': control_metrics.overshoot,
                '稳定性': analysis_results['stability_metrics']['stability_index']
            },
            'control_signals': gate_opening if gate_opening is not None else np.zeros_like(time),
            'system_state': {
                '正常运行': 0.8,
                '调节中': 0.15,
                '异常': 0.05
            }
        }
        
        self.plotter.create_dashboard(
            data=dashboard_data,
            title="水库控制系统仪表板",
            save_path=self.get_output_path('dashboard.png')
        )
        
        logger.info("所有可视化图表已生成")
    
    def run_example(self) -> Dict[str, Any]:
        """
        运行完整示例
        
        Returns:
            Dict[str, Any]: 示例运行结果
        """
        self.print_header()
        
        try:
            # 1. 设置仿真
            builder = self.setup_simulation()
            
            # 2. 运行仿真
            simulation_results = self.run_simulation(builder)
            
            # 3. 分析结果
            analysis_results = self.analyze_results(simulation_results)
            
            # 4. 创建可视化
            if analysis_results:
                self.create_visualizations(analysis_results)
            
            # 5. 保存结果
            self.save_results_to_csv({
                'time': analysis_results.get('time', []),
                'water_level': analysis_results.get('water_level', []),
                'gate_opening': analysis_results.get('gate_opening', []),
                'setpoint': [self.simulation_params['setpoint']] * len(analysis_results.get('time', []))
            }, 'simulation_results.csv')
            
            print_section_header("示例运行完成")
            logger.info(f"所有结果已保存到: {self.output_dir}")
            
            return {
                'success': True,
                'simulation_results': simulation_results,
                'analysis_results': analysis_results,
                'output_directory': str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"示例运行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def demonstrate_quick_tools():
    """
    演示快速工具的使用
    """
    print_section_header("快速工具演示")
    
    # 生成示例数据
    time = np.linspace(0, 100, 1000)
    setpoint = 12.0
    noise = np.random.normal(0, 0.1, len(time))
    
    # 模拟阶跃响应
    response = setpoint * (1 - np.exp(-time/20)) + noise
    control_signal = np.exp(-time/30) * 0.8
    
    # 快速分析
    analysis = quick_analysis(response, setpoint=setpoint, dt=0.1)
    
    print("快速分析结果:")
    print(f"  均值: {analysis['statistics'].mean:.3f}")
    print(f"  标准差: {analysis['statistics'].std:.3f}")
    print(f"  稳定性指数: {analysis['stability']['stability_index']:.3f}")
    print(f"  是否收敛: {analysis['stability']['is_converged']}")
    print(f"  RMSE: {analysis['control'].rmse:.3f}")
    print(f"  稳态误差: {analysis['control'].steady_state_error:.3f}")
    
    # 快速绘图
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    quick_plot(
        data=time,
        plot_type='control',
        setpoint=setpoint,
        actual=response,
        control_signal=control_signal,
        title="快速控制性能图",
        save_path=str(output_dir / 'quick_control_plot.png')
    )
    
    logger.info("快速工具演示完成")

def main():
    """
    主函数
    """
    print("=" * 80)
    print("简化示例演示 - 使用通用工具库")
    print("=" * 80)
    
    # 运行主示例
    example = SimplifiedReservoirControlExample()
    results = example.run_example()
    
    if results['success']:
        print("\n✅ 主示例运行成功!")
        print(f"📁 输出目录: {results['output_directory']}")
    else:
        print(f"\n❌ 主示例运行失败: {results['error']}")
    
    print("\n" + "-" * 80)
    
    # 演示快速工具
    demonstrate_quick_tools()
    
    print("\n" + "=" * 80)
    print("演示完成!")
    print("\n通过使用通用工具库，我们将原本复杂的仿真代码简化为:")
    print("1. 使用 SimulationBuilder 快速构建仿真系统")
    print("2. 使用 SimulationPlotter 统一生成可视化图表")
    print("3. 使用 PerformanceAnalyzer 标准化性能分析")
    print("4. 使用 ExampleRunner 提供通用运行框架")
    print("\n这样开发者可以专注于业务逻辑，而不是重复的基础设施代码。")
    print("=" * 80)

if __name__ == "__main__":
    main()