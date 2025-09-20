#!/usr/bin/env python3
"""
增强的可视化工具

提供标准化的仿真结果可视化功能，支持多种图表类型和样式配置。
与通用配置文件集成，提供一致的可视化体验。
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import logging

from core_lib.utils import seaborn_support

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class EnhancedSimulationPlotter:
    """
    增强的仿真绘图器
    
    提供多种标准化的图表类型：
    - 时间序列图
    - 控制性能图
    - 系统仪表板
    - 性能分析图
    - 对比分析图
    - 3D可视化
    """
    
    def __init__(self, style_config: Optional[Dict[str, Any]] = None):
        """
        初始化绘图器
        
        Args:
            style_config: 样式配置字典
        """
        self.style_config = style_config or {}
        self._setup_style()
        
        # 默认颜色方案
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        logging.info("Enhanced simulation plotter initialized")
    
    def _setup_style(self):
        """
        设置绘图样式
        """
        # 设置样式
        style = self.style_config.get('style', 'seaborn-v0_8')
        applied_style = seaborn_support.ensure_matplotlib_style(style)
        if applied_style != style:
            logging.warning(f"Style '{style}' not found, using {applied_style}")

        palette_name = self.style_config.get('palette', 'husl')
        seaborn_support.set_palette(palette_name)
        
        # 设置DPI
        dpi = self.style_config.get('dpi', 300)
        plt.rcParams['figure.dpi'] = dpi
        plt.rcParams['savefig.dpi'] = dpi
        
        # 设置图形大小
        figsize = self.style_config.get('figsize', (12, 8))
        plt.rcParams['figure.figsize'] = figsize
    
    def plot_time_series(self, data: Dict[str, List], title: str = "时间序列图", 
                        save_path: Optional[str] = None, **kwargs) -> plt.Figure:
        """
        绘制时间序列图
        
        Args:
            data: 数据字典，必须包含'time'键
            title: 图表标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 8)))
        
        time_data = data.get('time', [])
        
        # 绘制每个变量
        color_idx = 0
        for key, values in data.items():
            if key == 'time':
                continue
            
            color = self.color_palette[color_idx % len(self.color_palette)]
            ax.plot(time_data, values, label=key, color=color, linewidth=2)
            color_idx += 1
        
        ax.set_xlabel('时间')
        ax.set_ylabel('数值')
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化时间轴（如果时间是datetime对象）
        if time_data and isinstance(time_data[0], datetime):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_control_performance(self, data: Dict[str, List], title: str = "控制性能图", 
                               save_path: Optional[str] = None, **kwargs) -> plt.Figure:
        """
        绘制控制性能图
        
        Args:
            data: 包含setpoint, actual, control_signal等的数据字典
            title: 图表标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=kwargs.get('figsize', (12, 10)), 
                                      sharex=True)
        
        time_data = data.get('time', [])
        setpoint = data.get('setpoint', [])
        actual = data.get('actual', [])
        control_signal = data.get('control_signal', [])
        
        # 上图：设定值 vs 实际值
        if setpoint:
            ax1.plot(time_data, setpoint, label='设定值', color='red', 
                    linestyle='--', linewidth=2)
        if actual:
            ax1.plot(time_data, actual, label='实际值', color='blue', linewidth=2)
        
        ax1.set_ylabel('水位 (m)')
        ax1.set_title(f'{title} - 跟踪性能', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 计算误差
        if setpoint and actual and len(setpoint) == len(actual):
            error = [s - a for s, a in zip(setpoint, actual)]
            ax1_twin = ax1.twinx()
            ax1_twin.plot(time_data, error, label='误差', color='orange', 
                         alpha=0.7, linewidth=1)
            ax1_twin.set_ylabel('误差 (m)', color='orange')
            ax1_twin.legend(loc='upper right')
        
        # 下图：控制信号
        if control_signal:
            ax2.plot(time_data, control_signal, label='控制信号', 
                    color='green', linewidth=2)
            ax2.fill_between(time_data, control_signal, alpha=0.3, color='green')
        
        ax2.set_xlabel('时间')
        ax2.set_ylabel('闸门开度 (%)')
        ax2.set_title('控制信号', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_dashboard(self, data: Dict[str, Any], title: str = "系统仪表板", 
                        save_path: Optional[str] = None, **kwargs) -> plt.Figure:
        """
        创建系统仪表板
        
        Args:
            data: 仪表板数据，包含time_series, metrics, system_state等
            title: 仪表板标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        fig = plt.figure(figsize=kwargs.get('figsize', (16, 12)))
        
        # 创建网格布局
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 主要时间序列图 (占据上半部分)
        ax_main = fig.add_subplot(gs[0:2, :])
        self._plot_dashboard_timeseries(ax_main, data.get('time_series', {}))
        
        # 关键指标显示
        ax_metrics = fig.add_subplot(gs[2, 0])
        self._plot_dashboard_metrics(ax_metrics, data.get('metrics', {}))
        
        # 系统状态饼图
        ax_status = fig.add_subplot(gs[2, 1])
        self._plot_dashboard_status(ax_status, data.get('system_state', {}))
        
        # 性能指标
        ax_perf = fig.add_subplot(gs[2, 2])
        self._plot_dashboard_performance(ax_perf, data.get('performance', {}))
        
        fig.suptitle(title, fontsize=18, fontweight='bold')
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _plot_dashboard_timeseries(self, ax, time_series_data: Dict[str, List]):
        """
        绘制仪表板时间序列部分
        """
        if not time_series_data:
            ax.text(0.5, 0.5, '无时间序列数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14)
            return
        
        time_data = time_series_data.get('time', [])
        
        color_idx = 0
        for key, values in time_series_data.items():
            if key == 'time':
                continue
            
            color = self.color_palette[color_idx % len(self.color_palette)]
            ax.plot(time_data, values, label=key, color=color, linewidth=2)
            color_idx += 1
        
        ax.set_title('主要系统变量', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_dashboard_metrics(self, ax, metrics: Dict[str, float]):
        """
        绘制关键指标
        """
        if not metrics:
            ax.text(0.5, 0.5, '无指标数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('关键指标', fontsize=12, fontweight='bold')
            return
        
        # 创建指标表格
        metric_names = list(metrics.keys())
        metric_values = [f"{v:.2f}" for v in metrics.values()]
        
        # 创建表格
        table_data = list(zip(metric_names, metric_values))
        table = ax.table(cellText=table_data, 
                        colLabels=['指标', '数值'],
                        cellLoc='center',
                        loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        ax.axis('off')
        ax.set_title('关键指标', fontsize=12, fontweight='bold')
    
    def _plot_dashboard_status(self, ax, system_state: Dict[str, float]):
        """
        绘制系统状态饼图
        """
        if not system_state:
            ax.text(0.5, 0.5, '无状态数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('系统状态', fontsize=12, fontweight='bold')
            return
        
        labels = list(system_state.keys())
        sizes = list(system_state.values())
        colors = ['#2ecc71', '#f39c12', '#e74c3c'][:len(labels)]
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        ax.set_title('系统状态', fontsize=12, fontweight='bold')
    
    def _plot_dashboard_performance(self, ax, performance_data: Dict[str, Any]):
        """
        绘制性能指标
        """
        if not performance_data:
            # 显示默认性能指标
            metrics = ['CPU使用率', '内存使用率', '响应时间']
            values = [25, 60, 85]  # 示例数据
            colors = ['green', 'orange', 'red']
        else:
            metrics = list(performance_data.keys())
            values = list(performance_data.values())
            colors = ['green' if v < 50 else 'orange' if v < 80 else 'red' for v in values]
        
        bars = ax.barh(metrics, values, color=colors, alpha=0.7)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + 1, i, f'{value}%', va='center', fontsize=10)
        
        ax.set_xlim(0, 100)
        ax.set_xlabel('百分比 (%)')
        ax.set_title('性能指标', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
    
    def plot_performance_metrics(self, metrics: Dict[str, List], title: str = "性能分析", 
                               save_path: Optional[str] = None, **kwargs) -> plt.Figure:
        """
        绘制性能分析图
        
        Args:
            metrics: 性能指标数据
            title: 图表标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        n_metrics = len([k for k in metrics.keys() if k != 'time'])
        n_rows = (n_metrics + 1) // 2
        
        fig, axes = plt.subplots(n_rows, 2, figsize=kwargs.get('figsize', (14, 4*n_rows)))
        if n_rows == 1:
            axes = [axes]
        
        time_data = metrics.get('time', [])
        
        plot_idx = 0
        for key, values in metrics.items():
            if key == 'time':
                continue
            
            row = plot_idx // 2
            col = plot_idx % 2
            ax = axes[row][col] if n_rows > 1 else axes[col]
            
            ax.plot(time_data, values, linewidth=2, color=self.color_palette[plot_idx])
            ax.fill_between(time_data, values, alpha=0.3, color=self.color_palette[plot_idx])
            
            ax.set_title(f'{key}', fontsize=12, fontweight='bold')
            ax.set_xlabel('时间')
            ax.grid(True, alpha=0.3)
            
            # 添加统计信息
            if values:
                mean_val = np.mean(values)
                max_val = np.max(values)
                ax.axhline(y=mean_val, color='red', linestyle='--', alpha=0.7, 
                          label=f'平均值: {mean_val:.2f}')
                ax.legend()
            
            plot_idx += 1
        
        # 隐藏多余的子图
        if n_metrics % 2 == 1 and n_rows > 1:
            axes[-1][-1].axis('off')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_comparison(self, datasets: Dict[str, Dict[str, List]], 
                       title: str = "对比分析", save_path: Optional[str] = None, 
                       **kwargs) -> plt.Figure:
        """
        绘制多数据集对比图
        
        Args:
            datasets: 多个数据集的字典
            title: 图表标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 8)))
        
        color_idx = 0
        for dataset_name, data in datasets.items():
            time_data = data.get('time', [])
            
            # 假设我们对比主要变量（除了time之外的第一个变量）
            main_var = None
            for key in data.keys():
                if key != 'time':
                    main_var = key
                    break
            
            if main_var and main_var in data:
                color = self.color_palette[color_idx % len(self.color_palette)]
                ax.plot(time_data, data[main_var], label=f'{dataset_name}', 
                       color=color, linewidth=2)
                color_idx += 1
        
        ax.set_xlabel('时间')
        ax.set_ylabel('数值')
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_3d_surface(self, x_data: List, y_data: List, z_data: List, 
                       title: str = "3D表面图", save_path: Optional[str] = None, 
                       **kwargs) -> plt.Figure:
        """
        绘制3D表面图
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据
            z_data: Z轴数据
            title: 图表标题
            save_path: 保存路径
            **kwargs: 额外的绘图参数
            
        Returns:
            matplotlib图形对象
        """
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=kwargs.get('figsize', (12, 9)))
        ax = fig.add_subplot(111, projection='3d')
        
        # 创建网格
        X, Y = np.meshgrid(x_data, y_data)
        Z = np.array(z_data).reshape(len(y_data), len(x_data))
        
        # 绘制表面
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
        
        ax.set_xlabel(kwargs.get('xlabel', 'X轴'))
        ax.set_ylabel(kwargs.get('ylabel', 'Y轴'))
        ax.set_zlabel(kwargs.get('zlabel', 'Z轴'))
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        # 添加颜色条
        fig.colorbar(surf, shrink=0.5, aspect=5)
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _save_figure(self, fig: plt.Figure, save_path: str):
        """
        保存图形
        
        Args:
            fig: matplotlib图形对象
            save_path: 保存路径
        """
        try:
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 获取文件格式
            format_type = self.style_config.get('format', 'png')
            if not save_path.endswith(f'.{format_type}'):
                save_path = f"{save_path}.{format_type}"
            
            # 保存图形
            fig.savefig(save_path, dpi=self.style_config.get('dpi', 300), 
                       bbox_inches='tight', facecolor='white')
            
            logging.info(f"Figure saved to {save_path}")
            
        except Exception as e:
            logging.error(f"Failed to save figure to {save_path}: {e}")
    
    def create_animation(self, data_frames: List[Dict[str, Any]], 
                        title: str = "动画", save_path: Optional[str] = None, 
                        **kwargs):
        """
        创建动画（需要额外的依赖）
        
        Args:
            data_frames: 数据帧列表
            title: 动画标题
            save_path: 保存路径
            **kwargs: 额外的参数
        """
        try:
            from matplotlib.animation import FuncAnimation
            
            fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 8)))
            
            def animate(frame_idx):
                ax.clear()
                frame_data = data_frames[frame_idx]
                
                # 这里需要根据具体的数据结构来绘制
                # 简化实现
                if 'x' in frame_data and 'y' in frame_data:
                    ax.plot(frame_data['x'], frame_data['y'])
                
                ax.set_title(f"{title} - 帧 {frame_idx + 1}")
            
            anim = FuncAnimation(fig, animate, frames=len(data_frames), 
                               interval=kwargs.get('interval', 200), 
                               blit=False)
            
            if save_path:
                anim.save(save_path, writer='pillow')
                logging.info(f"Animation saved to {save_path}")
            
            return anim
            
        except ImportError:
            logging.warning("Animation requires additional dependencies")
            return None
        except Exception as e:
            logging.error(f"Failed to create animation: {e}")
            return None


def create_standard_plots(history: List[Dict[str, Any]], 
                         output_dir: Union[str, Path] = "plots", 
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    创建标准的仿真结果图表
    
    Args:
        history: 仿真历史数据
        output_dir: 输出目录
        config: 绘图配置
        
    Returns:
        生成的图表文件路径字典
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    plotter = EnhancedSimulationPlotter(config)
    generated_plots = {}
    
    try:
        # 准备时间序列数据
        time_data = [step['time'] for step in history]
        
        # 提取所有变量
        all_variables = set()
        for step in history:
            for comp_id, comp_data in step.items():
                if comp_id == 'time':
                    continue
                if isinstance(comp_data, dict):
                    all_variables.update(comp_data.keys())
        
        # 创建时间序列数据字典
        ts_data = {'time': time_data}
        for var in all_variables:
            var_data = []
            for step in history:
                value = None
                for comp_id, comp_data in step.items():
                    if comp_id == 'time':
                        continue
                    if isinstance(comp_data, dict) and var in comp_data:
                        value = comp_data[var]
                        break
                var_data.append(value if value is not None else 0)
            ts_data[var] = var_data
        
        # 生成时间序列图
        ts_path = output_dir / "time_series.png"
        plotter.plot_time_series(ts_data, "系统变量时间序列", str(ts_path))
        generated_plots['time_series'] = str(ts_path)
        
        # 生成控制性能图（如果有相关数据）
        if 'water_level' in all_variables or 'opening' in all_variables:
            control_data = {
                'time': time_data,
                'setpoint': [12.0] * len(time_data),  # 示例设定值
                'actual': ts_data.get('water_level', [0] * len(time_data)),
                'control_signal': ts_data.get('opening', [0] * len(time_data))
            }
            
            control_path = output_dir / "control_performance.png"
            plotter.plot_control_performance(control_data, "控制性能分析", str(control_path))
            generated_plots['control_performance'] = str(control_path)
        
        # 生成仪表板
        dashboard_data = {
            'time_series': ts_data,
            'metrics': {},
            'system_state': {'正常': 0.8, '调节': 0.15, '异常': 0.05}
        }
        
        # 计算关键指标
        for var, values in ts_data.items():
            if var == 'time':
                continue
            if values and all(isinstance(v, (int, float)) for v in values):
                dashboard_data['metrics'][f'{var}_平均'] = np.mean(values)
                dashboard_data['metrics'][f'{var}_最大'] = np.max(values)
        
        dashboard_path = output_dir / "dashboard.png"
        plotter.create_dashboard(dashboard_data, "系统仪表板", str(dashboard_path))
        generated_plots['dashboard'] = str(dashboard_path)
        
        logging.info(f"Standard plots generated in {output_dir}")
        
    except Exception as e:
        logging.error(f"Failed to create standard plots: {e}")
    
    return generated_plots