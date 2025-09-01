#!/usr/bin/env python3
"""
可视化工具 (Visualization Utils)

提供统一的图表样式和输出格式，简化示例代码中的可视化部分。

主要功能：
- 标准化的图表样式
- 常见图表类型的快速创建
- 多种输出格式支持
- 自动布局和美化
- 中文字体支持
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PlotStyle:
    """
    图表样式配置类
    """
    
    # 颜色方案
    COLORS = {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e', 
        'success': '#2ca02c',
        'danger': '#d62728',
        'warning': '#ff7f0e',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40'
    }
    
    # 线条样式
    LINE_STYLES = ['-', '--', '-.', ':']
    
    # 标记样式
    MARKERS = ['o', 's', '^', 'v', 'D', 'p', '*', 'h']
    
    # 默认图表配置
    DEFAULT_CONFIG = {
        'figure_size': (12, 8),
        'dpi': 100,
        'line_width': 2,
        'marker_size': 6,
        'font_size': 12,
        'title_size': 14,
        'label_size': 12,
        'legend_size': 10,
        'grid': True,
        'grid_alpha': 0.3
    }

class SimulationPlotter:
    """
    仿真结果绘图器
    
    提供标准化的仿真结果可视化功能。
    """
    
    def __init__(self, style_config: Optional[Dict[str, Any]] = None):
        """
        初始化绘图器
        
        Args:
            style_config: 样式配置字典
        """
        self.config = PlotStyle.DEFAULT_CONFIG.copy()
        if style_config:
            self.config.update(style_config)
        
        # 设置matplotlib样式
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
        
        logger.info("仿真绘图器初始化完成")
    
    def plot_time_series(self, data: Dict[str, Union[List, np.ndarray]], 
                        time: Optional[Union[List, np.ndarray]] = None,
                        title: str = "时间序列图",
                        xlabel: str = "时间 (s)",
                        ylabel: str = "数值",
                        save_path: Optional[str] = None,
                        show_legend: bool = True,
                        subplot_layout: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        绘制时间序列图
        
        Args:
            data: 数据字典，键为变量名，值为数据数组
            time: 时间数组，如果为None则使用索引
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            save_path: 保存路径
            show_legend: 是否显示图例
            subplot_layout: 子图布局 (rows, cols)
            
        Returns:
            plt.Figure: 图表对象
        """
        # 确定子图布局
        if subplot_layout is None:
            n_vars = len(data)
            if n_vars <= 2:
                subplot_layout = (1, n_vars)
            elif n_vars <= 4:
                subplot_layout = (2, 2)
            else:
                subplot_layout = (int(np.ceil(n_vars / 3)), 3)
        
        fig, axes = plt.subplots(*subplot_layout, figsize=self.config['figure_size'], 
                                dpi=self.config['dpi'])
        
        if not isinstance(axes, np.ndarray):
            axes = [axes]
        else:
            axes = axes.flatten()
        
        # 生成时间轴
        if time is None:
            first_key = list(data.keys())[0]
            time = np.arange(len(data[first_key]))
        
        # 绘制每个变量
        for i, (var_name, var_data) in enumerate(data.items()):
            if i >= len(axes):
                break
                
            ax = axes[i]
            color = list(PlotStyle.COLORS.values())[i % len(PlotStyle.COLORS)]
            
            ax.plot(time, var_data, 
                   color=color,
                   linewidth=self.config['line_width'],
                   label=var_name)
            
            ax.set_title(f"{var_name}", fontsize=self.config['title_size'])
            ax.set_xlabel(xlabel, fontsize=self.config['label_size'])
            ax.set_ylabel(ylabel, fontsize=self.config['label_size'])
            
            if self.config['grid']:
                ax.grid(True, alpha=self.config['grid_alpha'])
            
            if show_legend:
                ax.legend(fontsize=self.config['legend_size'])
        
        # 隐藏多余的子图
        for i in range(len(data), len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle(title, fontsize=self.config['title_size'] + 2)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'], bbox_inches='tight')
            logger.info(f"图表已保存到: {save_path}")
        
        return fig
    
    def plot_control_performance(self, time: Union[List, np.ndarray],
                               setpoint: Union[float, List, np.ndarray],
                               actual: Union[List, np.ndarray],
                               control_signal: Optional[Union[List, np.ndarray]] = None,
                               title: str = "控制性能图",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制控制性能图
        
        Args:
            time: 时间数组
            setpoint: 设定值
            actual: 实际值
            control_signal: 控制信号
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        n_subplots = 2 if control_signal is not None else 1
        fig, axes = plt.subplots(n_subplots, 1, figsize=self.config['figure_size'],
                                dpi=self.config['dpi'])
        
        if n_subplots == 1:
            axes = [axes]
        
        # 绘制设定值vs实际值
        ax1 = axes[0]
        
        # 处理设定值
        if isinstance(setpoint, (int, float)):
            setpoint_array = np.full_like(time, setpoint)
        else:
            setpoint_array = np.array(setpoint)
        
        ax1.plot(time, setpoint_array, 
                color=PlotStyle.COLORS['danger'], 
                linewidth=self.config['line_width'],
                linestyle='--', label='设定值')
        
        ax1.plot(time, actual, 
                color=PlotStyle.COLORS['primary'],
                linewidth=self.config['line_width'],
                label='实际值')
        
        ax1.set_title("跟踪性能", fontsize=self.config['title_size'])
        ax1.set_xlabel("时间 (s)", fontsize=self.config['label_size'])
        ax1.set_ylabel("数值", fontsize=self.config['label_size'])
        ax1.legend(fontsize=self.config['legend_size'])
        
        if self.config['grid']:
            ax1.grid(True, alpha=self.config['grid_alpha'])
        
        # 绘制控制信号
        if control_signal is not None:
            ax2 = axes[1]
            ax2.plot(time, control_signal,
                    color=PlotStyle.COLORS['success'],
                    linewidth=self.config['line_width'],
                    label='控制信号')
            
            ax2.set_title("控制信号", fontsize=self.config['title_size'])
            ax2.set_xlabel("时间 (s)", fontsize=self.config['label_size'])
            ax2.set_ylabel("控制量", fontsize=self.config['label_size'])
            ax2.legend(fontsize=self.config['legend_size'])
            
            if self.config['grid']:
                ax2.grid(True, alpha=self.config['grid_alpha'])
        
        plt.suptitle(title, fontsize=self.config['title_size'] + 2)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'], bbox_inches='tight')
            logger.info(f"控制性能图已保存到: {save_path}")
        
        return fig
    
    def plot_system_topology(self, components: Dict[str, Dict[str, Any]],
                           connections: List[Tuple[str, str]],
                           title: str = "系统拓扑图",
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制系统拓扑图
        
        Args:
            components: 组件字典
            connections: 连接列表
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("NetworkX未安装，无法绘制拓扑图")
            return None
        
        fig, ax = plt.subplots(figsize=self.config['figure_size'], 
                              dpi=self.config['dpi'])
        
        # 创建图
        G = nx.DiGraph()
        
        # 添加节点
        for comp_name, comp_info in components.items():
            G.add_node(comp_name, **comp_info)
        
        # 添加边
        G.add_edges_from(connections)
        
        # 计算布局
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # 绘制节点
        node_colors = [PlotStyle.COLORS['primary'] for _ in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              node_size=3000, alpha=0.8, ax=ax)
        
        # 绘制边
        nx.draw_networkx_edges(G, pos, edge_color=PlotStyle.COLORS['dark'],
                              arrows=True, arrowsize=20, alpha=0.6, ax=ax)
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, font_size=self.config['font_size'],
                               font_weight='bold', ax=ax)
        
        ax.set_title(title, fontsize=self.config['title_size'])
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'], bbox_inches='tight')
            logger.info(f"拓扑图已保存到: {save_path}")
        
        return fig
    
    def plot_performance_metrics(self, metrics: Dict[str, float],
                               title: str = "性能指标",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制性能指标柱状图
        
        Args:
            metrics: 性能指标字典
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'],
                              dpi=self.config['dpi'])
        
        metric_names = list(metrics.keys())
        metric_values = list(metrics.values())
        
        colors = [list(PlotStyle.COLORS.values())[i % len(PlotStyle.COLORS)] 
                 for i in range(len(metric_names))]
        
        bars = ax.bar(metric_names, metric_values, color=colors, alpha=0.8)
        
        # 添加数值标签
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'{value:.4f}', ha='center', va='bottom',
                   fontsize=self.config['font_size'])
        
        ax.set_title(title, fontsize=self.config['title_size'])
        ax.set_ylabel("数值", fontsize=self.config['label_size'])
        
        if self.config['grid']:
            ax.grid(True, alpha=self.config['grid_alpha'], axis='y')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'], bbox_inches='tight')
            logger.info(f"性能指标图已保存到: {save_path}")
        
        return fig
    
    def create_dashboard(self, data: Dict[str, Any],
                        title: str = "仿真仪表板",
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        创建综合仪表板
        
        Args:
            data: 包含各种数据的字典
            title: 仪表板标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        fig = plt.figure(figsize=(16, 12), dpi=self.config['dpi'])
        
        # 创建网格布局
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 时间序列图 (占据上半部分)
        if 'time_series' in data:
            ax1 = fig.add_subplot(gs[0:2, :])
            time_data = data['time_series']
            time = time_data.get('time', np.arange(len(list(time_data.values())[0])))
            
            for i, (var_name, var_data) in enumerate(time_data.items()):
                if var_name == 'time':
                    continue
                color = list(PlotStyle.COLORS.values())[i % len(PlotStyle.COLORS)]
                ax1.plot(time, var_data, label=var_name, 
                        color=color, linewidth=self.config['line_width'])
            
            ax1.set_title("主要变量时间序列", fontsize=self.config['title_size'])
            ax1.set_xlabel("时间 (s)", fontsize=self.config['label_size'])
            ax1.legend(fontsize=self.config['legend_size'])
            ax1.grid(True, alpha=self.config['grid_alpha'])
        
        # 性能指标 (左下)
        if 'metrics' in data:
            ax2 = fig.add_subplot(gs[2, 0])
            metrics = data['metrics']
            metric_names = list(metrics.keys())
            metric_values = list(metrics.values())
            
            ax2.bar(range(len(metric_names)), metric_values, 
                   color=PlotStyle.COLORS['primary'], alpha=0.8)
            ax2.set_xticks(range(len(metric_names)))
            ax2.set_xticklabels(metric_names, rotation=45, ha='right')
            ax2.set_title("性能指标", fontsize=self.config['title_size'])
            ax2.grid(True, alpha=self.config['grid_alpha'], axis='y')
        
        # 控制信号分布 (中下)
        if 'control_signals' in data:
            ax3 = fig.add_subplot(gs[2, 1])
            control_data = data['control_signals']
            
            if isinstance(control_data, dict):
                for signal_name, signal_values in control_data.items():
                    ax3.hist(signal_values, alpha=0.7, label=signal_name, bins=20)
                ax3.legend(fontsize=self.config['legend_size'])
            else:
                ax3.hist(control_data, alpha=0.7, bins=20, 
                        color=PlotStyle.COLORS['success'])
            
            ax3.set_title("控制信号分布", fontsize=self.config['title_size'])
            ax3.set_xlabel("控制量")
            ax3.set_ylabel("频次")
            ax3.grid(True, alpha=self.config['grid_alpha'])
        
        # 系统状态 (右下)
        if 'system_state' in data:
            ax4 = fig.add_subplot(gs[2, 2])
            state_data = data['system_state']
            
            # 创建饼图显示系统状态
            if isinstance(state_data, dict):
                labels = list(state_data.keys())
                sizes = list(state_data.values())
                colors = [list(PlotStyle.COLORS.values())[i % len(PlotStyle.COLORS)] 
                         for i in range(len(labels))]
                
                ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                       startangle=90)
                ax4.set_title("系统状态分布", fontsize=self.config['title_size'])
        
        plt.suptitle(title, fontsize=self.config['title_size'] + 4)
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'], bbox_inches='tight')
            logger.info(f"仪表板已保存到: {save_path}")
        
        return fig

def quick_plot(data: Union[Dict, List, np.ndarray], 
              plot_type: str = 'line',
              title: str = "快速绘图",
              save_path: Optional[str] = None,
              **kwargs) -> plt.Figure:
    """
    快速绘图函数
    
    Args:
        data: 数据
        plot_type: 图表类型 ('line', 'bar', 'hist', 'scatter')
        title: 标题
        save_path: 保存路径
        **kwargs: 其他参数
        
    Returns:
        plt.Figure: 图表对象
    """
    plotter = SimulationPlotter()
    
    if plot_type == 'line':
        if isinstance(data, dict):
            return plotter.plot_time_series(data, title=title, save_path=save_path, **kwargs)
        else:
            return plotter.plot_time_series({'data': data}, title=title, save_path=save_path, **kwargs)
    
    elif plot_type == 'control':
        if 'setpoint' in kwargs and 'actual' in kwargs:
            return plotter.plot_control_performance(
                time=data, 
                setpoint=kwargs['setpoint'],
                actual=kwargs['actual'],
                control_signal=kwargs.get('control_signal'),
                title=title,
                save_path=save_path
            )
    
    elif plot_type == 'metrics':
        if isinstance(data, dict):
            return plotter.plot_performance_metrics(data, title=title, save_path=save_path)
    
    elif plot_type == 'dashboard':
        if isinstance(data, dict):
            return plotter.create_dashboard(data, title=title, save_path=save_path)
    
    else:
        logger.warning(f"不支持的图表类型: {plot_type}")
        return None

def save_plots_to_pdf(figures: List[plt.Figure], output_path: str):
    """
    将多个图表保存到PDF文件
    
    Args:
        figures: 图表列表
        output_path: 输出PDF路径
    """
    try:
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages(output_path) as pdf:
            for fig in figures:
                pdf.savefig(fig, bbox_inches='tight')
        
        logger.info(f"所有图表已保存到PDF: {output_path}")
    
    except ImportError:
        logger.error("无法导入PdfPages，请安装完整的matplotlib")

def create_animation(data: Dict[str, List], 
                    time_steps: List[float],
                    save_path: str,
                    interval: int = 100) -> None:
    """
    创建动画
    
    Args:
        data: 时间序列数据
        time_steps: 时间步列表
        save_path: 保存路径
        interval: 动画间隔(毫秒)
    """
    try:
        from matplotlib.animation import FuncAnimation
        
        fig, ax = plt.subplots(figsize=PlotStyle.DEFAULT_CONFIG['figure_size'])
        
        lines = {}
        for var_name in data.keys():
            line, = ax.plot([], [], label=var_name, 
                           linewidth=PlotStyle.DEFAULT_CONFIG['line_width'])
            lines[var_name] = line
        
        ax.legend()
        ax.grid(True, alpha=PlotStyle.DEFAULT_CONFIG['grid_alpha'])
        
        def animate(frame):
            for var_name, line in lines.items():
                x_data = time_steps[:frame+1]
                y_data = data[var_name][:frame+1]
                line.set_data(x_data, y_data)
            
            ax.relim()
            ax.autoscale_view()
            return list(lines.values())
        
        anim = FuncAnimation(fig, animate, frames=len(time_steps),
                           interval=interval, blit=True, repeat=True)
        
        anim.save(save_path, writer='pillow')
        logger.info(f"动画已保存到: {save_path}")
        
    except ImportError:
        logger.error("无法创建动画，请安装pillow或其他动画编写器")

# 预设样式配置
STYLE_PRESETS = {
    'default': PlotStyle.DEFAULT_CONFIG,
    'presentation': {
        **PlotStyle.DEFAULT_CONFIG,
        'figure_size': (14, 10),
        'font_size': 14,
        'title_size': 18,
        'label_size': 16,
        'legend_size': 14,
        'line_width': 3
    },
    'paper': {
        **PlotStyle.DEFAULT_CONFIG,
        'figure_size': (10, 6),
        'font_size': 10,
        'title_size': 12,
        'label_size': 11,
        'legend_size': 9,
        'line_width': 1.5,
        'dpi': 300
    },
    'compact': {
        **PlotStyle.DEFAULT_CONFIG,
        'figure_size': (8, 6),
        'font_size': 9,
        'title_size': 11,
        'label_size': 10,
        'legend_size': 8,
        'line_width': 1.5
    }
}

def get_plotter(style: str = 'default') -> SimulationPlotter:
    """
    获取预配置的绘图器
    
    Args:
        style: 样式名称 ('default', 'presentation', 'paper', 'compact')
        
    Returns:
        SimulationPlotter: 配置好的绘图器
    """
    if style not in STYLE_PRESETS:
        logger.warning(f"未知样式: {style}，使用默认样式")
        style = 'default'
    
    return SimulationPlotter(STYLE_PRESETS[style])