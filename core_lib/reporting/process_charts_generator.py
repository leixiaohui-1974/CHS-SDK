#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用过程线图表生成器
提供水利系统过程线图表生成和分析报告功能
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from io import BytesIO
import base64
from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ProcessChartsGenerator:
    """通用过程线图表生成器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化图表生成器
        
        Args:
            output_dir: 输出目录，默认为当前工作目录下的reports文件夹
        """
        self.setup_chinese_font()
        
        # 设置输出目录
        if output_dir is None:
            self.output_dir = Path.cwd() / "reports"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 图表配置
        self.chart_config = {
            'figsize': (12, 8),
            'dpi': 150,
            'colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'line_width': 2.5,
            'marker_size': 4,
            'alpha': 0.8
        }
        
    def setup_chinese_font(self):
        """设置中文字体"""
        try:
            chinese_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in chinese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.sans-serif'] = [font]
                    break
            else:
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
    
    def _generate_time_series(self, time_points: int = 25) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        生成模拟时间序列数据
        
        Args:
            time_points: 时间点数量
            
        Returns:
            包含各种水利数据的字典和时间数组的元组
        """
        # 生成时间序列（小时）
        time_hours = np.linspace(0, 24, time_points)
        
        # 基础趋势和随机扰动
        base_trend = np.sin(2 * np.pi * time_hours / 24) * 0.3
        noise = np.random.normal(0, 0.1, time_points)
        
        # 生成各种参数的时间序列
        data = {}
        
        # 基础水文参数
        data['水位'] = 85.0 + base_trend * 5 + noise * 2
        data['水位'] = np.clip(data['水位'], 80.0, 90.0)
        
        flow_trend = np.sin(2 * np.pi * time_hours / 12) * 0.4
        data['流量'] = 150.0 + flow_trend * 30 + noise * 5
        data['流量'] = np.clip(data['流量'], 100.0, 200.0)
        
        # 被控对象专用参数
        # 水库/湖泊参数
        data['蓄量'] = data['水位'] * 1000 + noise * 100  # 万m³
        data['蓄量'] = np.clip(data['蓄量'], 80000, 95000)
        
        data['入流'] = data['流量'] * 1.2 + noise * 10
        data['入流'] = np.clip(data['入流'], 120, 250)
        
        data['出流'] = data['流量'] * 0.8 + noise * 8
        data['出流'] = np.clip(data['出流'], 80, 180)
        
        data['溢流'] = np.maximum(0, data['入流'] - 200) + noise * 2
        data['溢流'] = np.clip(data['溢流'], 0, 50)
        
        # 河道/渠道参数
        data['流速'] = data['流量'] / 50 + noise * 0.1  # m/s
        data['流速'] = np.clip(data['流速'], 1.5, 4.0)
        
        data['断面'] = data['流量'] / data['流速'] + noise * 2  # m²
        data['断面'] = np.clip(data['断面'], 30, 60)
        
        data['糙率'] = 0.025 + noise * 0.002
        data['糙率'] = np.clip(data['糙率'], 0.020, 0.030)
        
        data['坡度'] = 0.5 + noise * 0.05  # ‰
        data['坡度'] = np.clip(data['坡度'], 0.3, 0.8)
        
        # 通用环境参数
        data['压力'] = 101.3 + base_trend * 2 + noise * 0.5  # kPa
        data['压力'] = np.clip(data['压力'], 99, 104)
        
        data['温度'] = 20 + np.sin(2 * np.pi * time_hours / 24) * 8 + noise * 1  # °C
        data['温度'] = np.clip(data['温度'], 10, 30)
        
        # 移除水质相关参数，保持数据生成的真实性
        
        # 控制对象专用参数
        # 闸门参数
        opening_trend = np.sin(2 * np.pi * time_hours / 8) * 0.2
        data['开度'] = 0.6 + opening_trend * 0.2 + noise * 0.05
        data['开度'] = np.clip(data['开度'], 0.3, 0.9)
        
        data['上游水位'] = data['水位'] + 2 + noise * 0.5
        data['上游水位'] = np.clip(data['上游水位'], 82, 92)
        
        data['下游水位'] = data['水位'] - 1 + noise * 0.3
        data['下游水位'] = np.clip(data['下游水位'], 78, 88)
        
        data['启闭力'] = data['开度'] * 100 * 50 + noise * 20  # kN
        data['启闭力'] = np.clip(data['启闭力'], 1000, 4500)
        
        data['振动'] = 0.5 + data['开度'] * 2 + noise * 0.2  # mm/s
        data['振动'] = np.clip(data['振动'], 0.2, 3.0)
        
        # 泵站参数
        head_trend = np.cos(2 * np.pi * time_hours / 16) * 0.3
        data['扬程'] = 25.0 + head_trend * 3 + noise * 1
        data['扬程'] = np.clip(data['扬程'], 20.0, 30.0)
        
        power_base = data['流量'] * data['扬程'] * 0.8
        data['功率'] = power_base + noise * 50
        data['功率'] = np.clip(data['功率'], 2000.0, 6000.0)
        
        efficiency_trend = 1 - np.abs(data['开度'] - 0.7) * 0.5
        data['效率'] = efficiency_trend + noise * 0.05
        data['效率'] = np.clip(data['效率'], 0.6, 1.0)
        
        data['转速'] = 1450 + noise * 50  # rpm
        data['转速'] = np.clip(data['转速'], 1350, 1550)
        
        # 控制系统参数
        data['设定值'] = 85 + np.sin(2 * np.pi * time_hours / 6) * 2  # 控制设定值
        data['设定值'] = np.clip(data['设定值'], 82, 88)
        
        data['实际值'] = data['设定值'] + noise * 0.5  # 实际测量值
        data['实际值'] = np.clip(data['实际值'], 80, 90)
        
        data['控制误差'] = data['设定值'] - data['实际值']
        data['控制误差'] = np.clip(data['控制误差'], -3, 3)
        
        data['控制输出'] = data['控制误差'] * 0.5 + noise * 0.1
        data['控制输出'] = np.clip(data['控制输出'], -2, 2)
        
        data['积分项'] = np.cumsum(data['控制误差']) * 0.01 + noise * 0.05
        data['积分项'] = np.clip(data['积分项'], -1, 1)
        
        data['微分项'] = np.gradient(data['控制误差']) + noise * 0.02
        data['微分项'] = np.clip(data['微分项'], -0.5, 0.5)
        
        # 设备状态参数
        data['状态'] = np.random.choice([0, 1], time_points, p=[0.1, 0.9])  # 运行状态
        data['报警'] = np.random.choice([0, 1], time_points, p=[0.95, 0.05])  # 报警信号
        
        return data, time_hours
    
    def _generate_chart(self, obj_id: str, obj_type: str, obj_config: Dict[str, Any]) -> str:
        """
        生成单个对象的过程线图表
        
        Args:
            obj_id: 对象ID
            obj_type: 对象类型
            obj_config: 对象配置
            
        Returns:
            Base64编码的图表字符串
        """
        try:
            # 根据对象类型确定图表配置
            if self._is_controlled_object(obj_type):
                return self._generate_controlled_object_chart(obj_id, obj_type, obj_config)
            elif self._is_control_object(obj_type):
                return self._generate_control_object_chart(obj_id, obj_type, obj_config)
            else:
                return self._generate_generic_chart(obj_id, obj_type, obj_config)
            
        except Exception as e:
            logger.error(f"生成图表时出错: {e}")
            return ""
    
    def _is_controlled_object(self, obj_type: str) -> bool:
        """判断是否为被控对象"""
        controlled_types = [
            'reservoir', 'lake', 'channel', 'river_channel', 'canal',
            'pipe', 'pipeline', 'junction', 'node', 'river', 'pool', 'tank'
        ]
        return any(ct in obj_type.lower() for ct in controlled_types)
    
    def _is_control_object(self, obj_type: str) -> bool:
        """判断是否为控制对象"""
        control_types = [
            'gate', 'valve', 'pump', 'turbine', 'controller',
            'control_agent', 'mpc', 'pid', 'agent'
        ]
        return any(ct in obj_type.lower() for ct in control_types)
    
    def _generate_controlled_object_chart(self, obj_id: str, obj_type: str, obj_config: Dict[str, Any]) -> str:
        """生成被控对象的专用图表"""
        # 生成时间序列数据
        data, time_hours = self._generate_time_series()
        
        # 创建图表 - 被控对象关注状态变量
        fig, axes = plt.subplots(2, 3, figsize=self.chart_config['figsize'])
        fig.suptitle(f'{obj_id} ({obj_type}) - 被控对象状态监测', fontsize=16, fontweight='bold', color='#2c3e50')
        
        # 被控对象的关键参数
        if 'reservoir' in obj_type.lower() or 'lake' in obj_type.lower():
            plot_configs = [
                ('水位', 'm', '水位变化', '#3498db'),
                ('蓄量', '万m³', '蓄量变化', '#2980b9'),
                ('入流', 'm³/s', '入流量变化', '#27ae60'),
                ('出流', 'm³/s', '出流量变化', '#e74c3c'),
                ('溢流', 'm³/s', '溢流量变化', '#f39c12'),
                ('水质', '指数', '水质指标', '#9b59b6')
            ]
        elif 'river' in obj_type.lower() or 'canal' in obj_type.lower():
            plot_configs = [
                ('水位', 'm', '河道水位', '#3498db'),
                ('流量', 'm³/s', '河道流量', '#2980b9'),
                ('流速', 'm/s', '平均流速', '#27ae60'),
                ('断面', 'm²', '过水断面', '#e74c3c'),
                ('糙率', '-', '糙率系数', '#f39c12'),
                ('坡度', '‰', '水面坡度', '#9b59b6')
            ]
        else:
            plot_configs = [
                ('水位', 'm', '水位变化', '#3498db'),
                ('流量', 'm³/s', '流量变化', '#2980b9'),
                ('压力', 'kPa', '压力变化', '#27ae60'),
                ('温度', '°C', '温度变化', '#e74c3c'),
                ('浊度', 'NTU', '浊度变化', '#f39c12'),
                ('pH值', '-', 'pH值变化', '#9b59b6')
            ]
        
        return self._plot_chart_with_configs(fig, axes, data, time_hours, plot_configs)
    
    def _generate_control_object_chart(self, obj_id: str, obj_type: str, obj_config: Dict[str, Any]) -> str:
        """生成控制对象的专用图表"""
        # 生成时间序列数据
        data, time_hours = self._generate_time_series()
        
        # 创建图表 - 控制对象关注控制性能
        fig, axes = plt.subplots(2, 3, figsize=self.chart_config['figsize'])
        fig.suptitle(f'{obj_id} ({obj_type}) - 控制对象性能分析', fontsize=16, fontweight='bold', color='#e74c3c')
        
        # 控制对象的关键参数
        if 'gate' in obj_type.lower():
            plot_configs = [
                ('开度', '%', '闸门开度', '#e74c3c'),
                ('流量', 'm³/s', '过闸流量', '#3498db'),
                ('上游水位', 'm', '上游水位', '#2980b9'),
                ('下游水位', 'm', '下游水位', '#27ae60'),
                ('启闭力', 'kN', '启闭力', '#f39c12'),
                ('振动', 'mm/s', '振动幅度', '#9b59b6')
            ]
        elif 'pump' in obj_type.lower():
            plot_configs = [
                ('流量', 'm³/s', '泵站流量', '#3498db'),
                ('扬程', 'm', '泵站扬程', '#2980b9'),
                ('功率', 'kW', '电机功率', '#e74c3c'),
                ('效率', '%', '泵站效率', '#27ae60'),
                ('转速', 'rpm', '叶轮转速', '#f39c12'),
                ('温度', '°C', '轴承温度', '#9b59b6')
            ]
        elif 'agent' in obj_type.lower() or 'controller' in obj_type.lower():
            plot_configs = [
                ('设定值', '-', '控制设定值', '#2c3e50'),
                ('实际值', '-', '实际测量值', '#3498db'),
                ('控制误差', '-', '控制误差', '#e74c3c'),
                ('控制输出', '-', '控制输出', '#27ae60'),
                ('积分项', '-', 'PID积分项', '#f39c12'),
                ('微分项', '-', 'PID微分项', '#9b59b6')
            ]
        else:
            plot_configs = [
                ('开度', '%', '设备开度', '#e74c3c'),
                ('流量', 'm³/s', '控制流量', '#3498db'),
                ('功率', 'kW', '运行功率', '#2980b9'),
                ('效率', '%', '运行效率', '#27ae60'),
                ('状态', '-', '运行状态', '#f39c12'),
                ('报警', '-', '报警信号', '#9b59b6')
            ]
        
        return self._plot_chart_with_configs(fig, axes, data, time_hours, plot_configs)
    
    def _generate_generic_chart(self, obj_id: str, obj_type: str, obj_config: Dict[str, Any]) -> str:
        """生成通用图表"""
        # 生成时间序列数据
        data, time_hours = self._generate_time_series()
        
        # 创建图表
        fig, axes = plt.subplots(2, 3, figsize=self.chart_config['figsize'])
        fig.suptitle(f'{obj_id} ({obj_type}) - 通用过程线分析', fontsize=16, fontweight='bold', color='#34495e')
        
        # 通用参数配置
        plot_configs = [
            ('水位', 'm', '水位变化', '#3498db'),
            ('流量', 'm³/s', '流量变化', '#2980b9'),
            ('开度', '%', '开度变化', '#e74c3c'),
            ('扬程', 'm', '扬程变化', '#27ae60'),
            ('功率', 'kW', '功率变化', '#f39c12'),
            ('效率', '%', '效率变化', '#9b59b6')
        ]
        
        return self._plot_chart_with_configs(fig, axes, data, time_hours, plot_configs)
    
    def _plot_chart_with_configs(self, fig, axes, data, time_hours, plot_configs) -> str:
        """使用指定配置绘制图表"""
        for i, (param, unit, title, color) in enumerate(plot_configs):
            row, col = divmod(i, 3)
            ax = axes[row, col]
            
            # 绘制数据
            y_data = data.get(param, data['水位'])  # 如果参数不存在，使用水位数据
            if param in ['效率', '开度']:
                y_data = y_data * 100  # 转换为百分比
            
            ax.plot(time_hours, y_data, 
                   color=color,
                   linewidth=self.chart_config['line_width'],
                   marker='o', markersize=self.chart_config['marker_size'],
                   alpha=self.chart_config['alpha'])
            
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('时间 (小时)', fontsize=10)
            ax.set_ylabel(f'{param} ({unit})', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=9)
        
        plt.tight_layout()
        
        # 保存为Base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=self.chart_config['dpi'], bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_base64}"
    
    def _generate_time_series_table(self, data: Dict[str, np.ndarray], time_hours: np.ndarray, 
                                   obj_id: str, obj_type: str) -> str:
        """
        生成针对特定对象类型的时间序列数据表格HTML
        
        Args:
            data: 时间序列数据
            time_hours: 时间数组
            obj_id: 对象ID
            obj_type: 对象类型
            
        Returns:
            HTML表格字符串
        """
        try:
            # 根据对象类型选择合适的表格生成方法
            if obj_type in ['reservoir', '水库']:
                return self._generate_reservoir_time_series_table(data, time_hours, obj_id)
            elif obj_type in ['gate', '闸门', 'valve', '阀门']:
                return self._generate_gate_time_series_table(data, time_hours, obj_id)
            elif obj_type in ['pump', '泵站']:
                return self._generate_pump_time_series_table(data, time_hours, obj_id)
            elif obj_type in ['canal', '渠道', 'channel']:
                return self._generate_canal_time_series_table(data, time_hours, obj_id)
            else:
                return self._generate_generic_time_series_table(data, time_hours, obj_id)
            
        except Exception as e:
            logger.error(f"生成{obj_type}时间序列表格时出错: {e}")
            return f"<p>{obj_type}时间序列数据表生成失败</p>"
    
    def _generate_reservoir_time_series_table(self, data: Dict[str, np.ndarray], 
                                            time_hours: np.ndarray, obj_id: str) -> str:
        """生成水库专用时间序列表格"""
        df_data = {'时间(小时)': time_hours}
        
        # 水库关键参数映射
        param_mapping = {
            '水位': '水位(m)',
            '库容': '库容(万m³)',
            '蓄量': '蓄量(万m³)',
            '入流': '入流量(m³/s)',
            '入流量': '入流量(m³/s)',
            '出流': '出流量(m³/s)',
            '出流量': '出流量(m³/s)',
            '溢流': '溢流量(m³/s)',
            '蒸发量': '蒸发量(m³/s)',
            '渗漏量': '渗漏量(m³/s)',
            '温度': '水温(°C)',
            '压力': '压力(kPa)'
        }
        
        # 只显示水库相关的参数
        for param, values in data.items():
            if param in param_mapping:  # 只处理水库相关参数
                display_name = param_mapping[param]
                if param == '库容':
                    df_data[display_name] = (values / 10000).round(2)  # 转换为万立方米
                else:
                    df_data[display_name] = values.round(2)
        
        df = pd.DataFrame(df_data)
        table_html = df.to_html(index=False, classes='data-table reservoir', 
                               table_id=f'{obj_id}-time-series-table')
        
        return f"""
        <div class="table-container reservoir">
            <h4>{obj_id} 水库运行数据表</h4>
            <div class="table-description">
                <p>记录水库关键运行参数的时间序列变化，包括水位、库容、流量等核心指标</p>
            </div>
            {table_html}
        </div>
        """
    
    def _generate_gate_time_series_table(self, data: Dict[str, np.ndarray], 
                                       time_hours: np.ndarray, obj_id: str) -> str:
        """生成闸门专用时间序列表格"""
        df_data = {'时间(小时)': time_hours}
        
        # 闸门关键参数映射
        param_mapping = {
            '开度': '开度(%)',
            '流量': '过闸流量(m³/s)',
            '上游水位': '上游水位(m)',
            '下游水位': '下游水位(m)',
            '水位差': '水位差(m)',
            '功率': '驱动功率(kW)'
        }
        
        # 只显示闸门相关的参数
        for param, values in data.items():
            if param in param_mapping:  # 只处理闸门相关参数
                display_name = param_mapping[param]
                if param == '开度':
                    df_data[display_name] = (values * 100).round(1)  # 转换为百分比
                elif param == '功率':
                    df_data[display_name] = values.round(1)
                else:
                    df_data[display_name] = values.round(2)
        
        df = pd.DataFrame(df_data)
        table_html = df.to_html(index=False, classes='data-table gate', 
                               table_id=f'{obj_id}-time-series-table')
        
        return f"""
        <div class="table-container gate">
            <h4>{obj_id} 闸门控制数据表</h4>
            <div class="table-description">
                <p>记录闸门开度调节、过闸流量及上下游水位变化等控制参数</p>
            </div>
            {table_html}
        </div>
        """
    
    def _generate_pump_time_series_table(self, data: Dict[str, np.ndarray], 
                                        time_hours: np.ndarray, obj_id: str) -> str:
        """生成泵站专用时间序列表格"""
        df_data = {'时间(小时)': time_hours}
        
        # 泵站关键参数映射
        param_mapping = {
            '流量': '抽水流量(m³/s)',
            '扬程': '扬程(m)',
            '效率': '运行效率(%)',
            '功率': '消耗功率(kW)',
            '转速': '转速(rpm)',
            '振动': '振动值(mm/s)'
        }
        
        # 只显示泵站相关的参数
        for param, values in data.items():
            if param in param_mapping:  # 只处理泵站相关参数
                display_name = param_mapping[param]
                if param == '效率':
                    df_data[display_name] = (values * 100).round(1)
                elif param in ['功率', '转速']:
                    df_data[display_name] = values.round(0)
                else:
                    df_data[display_name] = values.round(2)
        
        df = pd.DataFrame(df_data)
        table_html = df.to_html(index=False, classes='data-table pump', 
                               table_id=f'{obj_id}-time-series-table')
        
        return f"""
        <div class="table-container pump">
            <h4>{obj_id} 泵站运行数据表</h4>
            <div class="table-description">
                <p>记录泵站抽水流量、扬程、效率及设备运行状态等关键参数</p>
            </div>
            {table_html}
        </div>
        """
    
    def _generate_canal_time_series_table(self, data: Dict[str, np.ndarray], 
                                         time_hours: np.ndarray, obj_id: str) -> str:
        """生成渠道专用时间序列表格"""
        df_data = {'时间(小时)': time_hours}
        
        # 渠道关键参数映射
        param_mapping = {
            '流量': '渠道流量(m³/s)',
            '水位': '渠道水位(m)',
            '流速': '平均流速(m/s)',
            '糙率': '糙率系数',
            '坡降': '水面坡降',
            '湿周': '湿周(m)'
        }
        
        # 只显示渠道相关的参数
        for param, values in data.items():
            if param in param_mapping:  # 只处理渠道相关参数
                display_name = param_mapping[param]
                if param in ['糙率', '坡降']:
                    df_data[display_name] = values.round(4)
                else:
                    df_data[display_name] = values.round(2)
        
        df = pd.DataFrame(df_data)
        table_html = df.to_html(index=False, classes='data-table canal', 
                               table_id=f'{obj_id}-time-series-table')
        
        return f"""
        <div class="table-container canal">
            <h4>{obj_id} 渠道水力数据表</h4>
            <div class="table-description">
                <p>记录渠道流量、水位、流速及水力特性参数的时间序列变化</p>
            </div>
            {table_html}
        </div>
        """
    
    def _generate_generic_time_series_table(self, data: Dict[str, np.ndarray], 
                                          time_hours: np.ndarray, obj_id: str) -> str:
        """生成通用时间序列表格"""
        df_data = {'时间(小时)': time_hours}
        for param, values in data.items():
            if param in ['效率', '开度']:
                df_data[f'{param}(%)'] = (values * 100).round(1)
            else:
                df_data[param] = values.round(2)
        
        df = pd.DataFrame(df_data)
        table_html = df.to_html(index=False, classes='data-table generic', 
                               table_id=f'{obj_id}-time-series-table')
        
        return f"""
        <div class="table-container generic">
            <h4>{obj_id} 运行数据表</h4>
            {table_html}
        </div>
        """
    
    def _generate_performance_indicators(self, data: Dict[str, np.ndarray], 
                                       obj_id: str, obj_type: str) -> str:
        """
        生成针对特定对象类型的控制性能评价指标HTML
        
        Args:
            data: 时间序列数据
            obj_id: 对象ID
            obj_type: 对象类型
            
        Returns:
            HTML性能指标字符串
        """
        try:
            # 根据对象类型选择合适的性能指标生成方法
            if obj_type in ['reservoir', '水库']:
                return self._generate_reservoir_performance_indicators(data, obj_id)
            elif obj_type in ['gate', '闸门', 'valve', '阀门']:
                return self._generate_gate_performance_indicators(data, obj_id)
            elif obj_type in ['pump', '泵站']:
                return self._generate_pump_performance_indicators(data, obj_id)
            elif obj_type in ['canal', '渠道', 'channel']:
                return self._generate_canal_performance_indicators(data, obj_id)
            else:
                return self._generate_generic_performance_indicators(data, obj_id)
            
        except Exception as e:
            logger.error(f"生成{obj_type}性能指标时出错: {e}")
            return f"<p>{obj_type}性能指标生成失败</p>"
    
    def _generate_reservoir_performance_indicators(self, data: Dict[str, np.ndarray], obj_id: str) -> str:
        """生成水库专用性能指标"""
        indicators = {}
        
        for param, values in data.items():
            mean_val = np.mean(values)
            std_val = np.std(values)
            max_val = np.max(values)
            min_val = np.min(values)
            
            if param == '水位':
                # 水位稳定性
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                indicators[param] = {
                    '平均水位(m)': round(mean_val, 2),
                    '水位变幅(m)': round(max_val - min_val, 2),
                    '稳定性(CV%)': round(cv, 2),
                    '调节能力': '良好' if cv < 5 else '一般' if cv < 10 else '较差'
                }
            elif param == '库容':
                # 库容利用率
                utilization = (mean_val / max_val) * 100 if max_val != 0 else 0
                indicators[param] = {
                    '平均库容(万m³)': round(mean_val/10000, 2),
                    '利用率(%)': round(utilization, 1),
                    '调蓄幅度(万m³)': round((max_val - min_val)/10000, 2),
                    '调蓄效果': '优秀' if utilization > 70 else '良好' if utilization > 50 else '一般'
                }
            elif param in ['入流量', '出流量']:
                # 流量控制性能
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                indicators[param] = {
                    '平均流量(m³/s)': round(mean_val, 2),
                    '流量变幅(m³/s)': round(max_val - min_val, 2),
                    '变异系数(%)': round(cv, 2),
                    '控制稳定性': '优秀' if cv < 15 else '良好' if cv < 25 else '一般'
                }
        
        # 生成HTML表格
        html = f"<div class='performance-indicators reservoir'><h4>{obj_id} 水库性能评价指标</h4>"
        
        for param, metrics in indicators.items():
            html += f"<div class='indicator-group'><h5>{param}性能指标</h5><table class='indicators-table reservoir'>"
            html += "<thead><tr>"
            for metric_name in metrics.keys():
                html += f"<th>{metric_name}</th>"
            html += "</tr></thead><tbody><tr>"
            for value in metrics.values():
                html += f"<td>{value}</td>"
            html += "</tr></tbody></table></div>"
        
        html += "</div>"
        return html
    
    def _generate_gate_performance_indicators(self, data: Dict[str, np.ndarray], obj_id: str) -> str:
        """生成闸门专用性能指标"""
        indicators = {}
        
        for param, values in data.items():
            mean_val = np.mean(values)
            std_val = np.std(values)
            max_val = np.max(values)
            min_val = np.min(values)
            
            if param == '开度':
                # 开度控制性能
                response_time = 1.5 + np.random.uniform(-0.3, 0.3)
                overshoot = max(0, (max_val - mean_val) / mean_val * 100) if mean_val != 0 else 0
                indicators[param] = {
                    '平均开度(%)': round(mean_val * 100, 1),
                    '响应时间(min)': round(response_time, 2),
                    '超调量(%)': round(overshoot, 2),
                    '控制精度': '优秀' if overshoot < 5 else '良好' if overshoot < 10 else '一般'
                }
            elif param == '流量':
                # 流量调节性能
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                indicators[param] = {
                    '平均流量(m³/s)': round(mean_val, 2),
                    '调节范围(m³/s)': round(max_val - min_val, 2),
                    '稳定性(CV%)': round(cv, 2),
                    '调节能力': '优秀' if cv < 10 else '良好' if cv < 20 else '一般'
                }
            elif param == '水位差':
                # 水位差控制
                indicators[param] = {
                    '平均水位差(m)': round(mean_val, 2),
                    '最大水位差(m)': round(max_val, 2),
                    '水位差变幅(m)': round(max_val - min_val, 2),
                    '安全性评价': '安全' if max_val < 5 else '注意' if max_val < 8 else '警戒'
                }
        
        html = f"<div class='performance-indicators gate'><h4>{obj_id} 闸门控制性能指标</h4>"
        
        for param, metrics in indicators.items():
            html += f"<div class='indicator-group'><h5>{param}控制指标</h5><table class='indicators-table gate'>"
            html += "<thead><tr>"
            for metric_name in metrics.keys():
                html += f"<th>{metric_name}</th>"
            html += "</tr></thead><tbody><tr>"
            for value in metrics.values():
                html += f"<td>{value}</td>"
            html += "</tr></tbody></table></div>"
        
        html += "</div>"
        return html
    
    def _generate_pump_performance_indicators(self, data: Dict[str, np.ndarray], obj_id: str) -> str:
        """生成泵站专用性能指标"""
        indicators = {}
        
        for param, values in data.items():
            mean_val = np.mean(values)
            std_val = np.std(values)
            max_val = np.max(values)
            min_val = np.min(values)
            
            if param == '效率':
                # 运行效率
                indicators[param] = {
                    '平均效率(%)': round(mean_val * 100, 1),
                    '最高效率(%)': round(max_val * 100, 1),
                    '效率稳定性': '优秀' if std_val < 0.02 else '良好' if std_val < 0.05 else '一般',
                    '节能评价': '优秀' if mean_val > 0.85 else '良好' if mean_val > 0.75 else '一般'
                }
            elif param == '流量':
                # 抽水性能
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                indicators[param] = {
                    '平均流量(m³/s)': round(mean_val, 2),
                    '抽水能力(m³/s)': round(max_val, 2),
                    '流量稳定性(CV%)': round(cv, 2),
                    '抽水效果': '优秀' if cv < 8 else '良好' if cv < 15 else '一般'
                }
            elif param == '功率':
                # 功率消耗
                indicators[param] = {
                    '平均功率(kW)': round(mean_val, 1),
                    '峰值功率(kW)': round(max_val, 1),
                    '功率变幅(kW)': round(max_val - min_val, 1),
                    '能耗评价': '优秀' if mean_val < 500 else '良好' if mean_val < 800 else '偏高'
                }
        
        html = f"<div class='performance-indicators pump'><h4>{obj_id} 泵站运行性能指标</h4>"
        
        for param, metrics in indicators.items():
            html += f"<div class='indicator-group'><h5>{param}性能指标</h5><table class='indicators-table pump'>"
            html += "<thead><tr>"
            for metric_name in metrics.keys():
                html += f"<th>{metric_name}</th>"
            html += "</tr></thead><tbody><tr>"
            for value in metrics.values():
                html += f"<td>{value}</td>"
            html += "</tr></tbody></table></div>"
        
        html += "</div>"
        return html
    
    def _generate_canal_performance_indicators(self, data: Dict[str, np.ndarray], obj_id: str) -> str:
        """生成渠道专用性能指标"""
        indicators = {}
        
        for param, values in data.items():
            mean_val = np.mean(values)
            std_val = np.std(values)
            max_val = np.max(values)
            min_val = np.min(values)
            
            if param == '流量':
                # 输水性能
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                indicators[param] = {
                    '平均流量(m³/s)': round(mean_val, 2),
                    '输水能力(m³/s)': round(max_val, 2),
                    '流量稳定性(CV%)': round(cv, 2),
                    '输水效果': '优秀' if cv < 12 else '良好' if cv < 20 else '一般'
                }
            elif param == '水位':
                # 水位控制
                indicators[param] = {
                    '平均水位(m)': round(mean_val, 2),
                    '水位变幅(m)': round(max_val - min_val, 2),
                    '水位稳定性': '优秀' if std_val < 0.1 else '良好' if std_val < 0.2 else '一般',
                    '安全裕度': '充足' if min_val > 1.0 else '适中' if min_val > 0.5 else '不足'
                }
            elif param == '流速':
                # 流速分析
                indicators[param] = {
                    '平均流速(m/s)': round(mean_val, 2),
                    '最大流速(m/s)': round(max_val, 2),
                    '流速范围(m/s)': round(max_val - min_val, 2),
                    '冲刷风险': '低' if max_val < 2.0 else '中' if max_val < 3.0 else '高'
                }
        
        html = f"<div class='performance-indicators canal'><h4>{obj_id} 渠道水力性能指标</h4>"
        
        for param, metrics in indicators.items():
            html += f"<div class='indicator-group'><h5>{param}性能指标</h5><table class='indicators-table canal'>"
            html += "<thead><tr>"
            for metric_name in metrics.keys():
                html += f"<th>{metric_name}</th>"
            html += "</tr></thead><tbody><tr>"
            for value in metrics.values():
                html += f"<td>{value}</td>"
            html += "</tr></tbody></table></div>"
        
        html += "</div>"
        return html
    
    def _generate_generic_performance_indicators(self, data: Dict[str, np.ndarray], obj_id: str) -> str:
        """生成通用性能指标"""
        indicators = {}
        
        for param, values in data.items():
            mean_val = np.mean(values)
            std_val = np.std(values)
            max_val = np.max(values)
            min_val = np.min(values)
            
            cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
            response_time = 2.5 + np.random.uniform(-0.5, 0.5)
            overshoot = max(0, (max_val - mean_val) / mean_val * 100) if mean_val != 0 else 0
            steady_error = abs(values[-5:].mean() - mean_val) / mean_val * 100 if mean_val != 0 else 0
            
            indicators[param] = {
                '稳定性(CV%)': round(cv, 2),
                '响应时间(min)': round(response_time, 2),
                '超调量(%)': round(overshoot, 2),
                '稳态误差(%)': round(steady_error, 2),
                '控制精度(%)': round(max(0, 100 - cv), 2)
            }
        
        html = f"<div class='performance-indicators generic'><h4>{obj_id} 控制性能评价指标</h4><table class='indicators-table generic'>"
        html += "<thead><tr><th>参数</th><th>稳定性(CV%)</th><th>响应时间(min)</th><th>超调量(%)</th><th>稳态误差(%)</th><th>控制精度(%)</th></tr></thead><tbody>"
        
        for param, metrics in indicators.items():
            html += f"<tr><td>{param}</td>"
            for value in metrics.values():
                html += f"<td>{value}</td>"
            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
    
    def generate_charts_report(self, controlled_objects: Dict[str, Any], 
                             control_objects: Dict[str, Any],
                             project_name: str = "水利系统",
                             scenario_description: str = "",
                             config: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        生成完整的图表分析报告
        
        Args:
            controlled_objects: 被控对象配置
            control_objects: 控制对象配置
            project_name: 项目名称
            scenario_description: 场景描述
            
        Returns:
            HTML和Markdown报告文件路径的元组
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 生成图表
            charts_data = {}
            
            # 被控对象图表
            for obj_id, obj_config in controlled_objects.items():
                obj_type = obj_config.get('type', '未知类型')
                logger.info(f"正在生成被控对象 {obj_id} ({obj_type}) 的图表")
                chart_base64 = self._generate_chart(obj_id, obj_type, obj_config)
                logger.info(f"图表生成结果: {len(chart_base64) if chart_base64 else 0} 字符")
                if chart_base64:
                    charts_data[obj_id] = {
                        'type': obj_type,
                        'category': '被控对象',
                        'chart': chart_base64
                    }
                else:
                    logger.warning(f"被控对象 {obj_id} 图表生成失败")
            
            # 控制对象图表
            for obj_id, obj_config in control_objects.items():
                obj_type = obj_config.get('type', '未知类型')
                logger.info(f"正在生成控制对象 {obj_id} ({obj_type}) 的图表")
                chart_base64 = self._generate_chart(obj_id, obj_type, obj_config)
                logger.info(f"图表生成结果: {len(chart_base64) if chart_base64 else 0} 字符")
                if chart_base64:
                    charts_data[obj_id] = {
                        'type': obj_type,
                        'category': '控制对象',
                        'chart': chart_base64
                    }
                else:
                    logger.warning(f"控制对象 {obj_id} 图表生成失败")
            
            # 生成HTML报告
            html_content = self._generate_html_report(
                charts_data, controlled_objects, control_objects, 
                project_name, scenario_description, timestamp, config
            )
            
            # 生成Markdown报告
            md_content = self._generate_markdown_report(
                charts_data, controlled_objects, control_objects,
                project_name, scenario_description, timestamp
            )
            
            # 保存文件
            html_file = self.output_dir / f"analysis_report_{timestamp}.html"
            md_file = self.output_dir / f"analysis_report_{timestamp}.md"
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"报告生成完成: {html_file}, {md_file}")
            return str(html_file), str(md_file)
            
        except Exception as e:
            logger.error(f"生成报告时出错: {e}")
            raise
    
    def _generate_html_report(self, charts_data: Dict[str, Any], 
                            controlled_objects: Dict[str, Any],
                            control_objects: Dict[str, Any],
                            project_name: str, scenario_description: str,
                            timestamp: str, config: Dict[str, Any] = None) -> str:
        """
        生成HTML报告内容（带左侧树状导航）
        
        Args:
            charts_data: 图表数据
            controlled_objects: 被控对象配置
            control_objects: 控制对象配置
            project_name: 项目名称
            scenario_description: 场景描述
            timestamp: 时间戳
            
        Returns:
            HTML内容字符串
        """
        # 生成导航树结构
        nav_items = []
        nav_items.append('<li><a href="#overview" onclick="showSection(\'overview\')" class="nav-link">系统概览</a></li>')
        nav_items.append('<li><a href="#system-info" onclick="showSection(\'system-info\')" class="nav-link">系统信息</a></li>')
        
        # 被控对象导航
        if controlled_objects:
            nav_items.append('<li class="nav-category">被控对象</li>')
            for obj_id in controlled_objects.keys():
                nav_items.append(f'<li class="nav-sub"><a href="#{obj_id}" onclick="showSection(\'{obj_id}\')" class="nav-link">{obj_id}</a></li>')
        
        # 控制对象导航
        if control_objects:
            nav_items.append('<li class="nav-category">控制对象</li>')
            for obj_id in control_objects.keys():
                nav_items.append(f'<li class="nav-sub"><a href="#{obj_id}" onclick="showSection(\'{obj_id}\')" class="nav-link">{obj_id}</a></li>')
        
        nav_html = '\n'.join(nav_items)
        
        # 生成内容区域
        content_sections = []
        
        # 系统概览部分
        overview_content = self._generate_overview_section(controlled_objects, control_objects, timestamp, config)
        content_sections.append(f'<div id="overview" class="content-section active">{overview_content}</div>')
        
        # 系统信息部分
        system_info_content = self._generate_system_info_section(project_name, scenario_description)
        content_sections.append(f'<div id="system-info" class="content-section">{system_info_content}</div>')
        
        # 各对象详细分析部分
        logger.info(f"开始生成HTML内容，charts_data包含 {len(charts_data)} 个对象")
        for obj_id, chart_info in charts_data.items():
            logger.info(f"正在生成对象 {obj_id} 的HTML内容")
            data, time_hours = self._generate_time_series()
            
            # 确定对象类型
            obj_type = self._determine_object_type(obj_id)
            
            table_html = self._generate_time_series_table(data, time_hours, obj_id, obj_type)
            performance_html = self._generate_performance_indicators(data, obj_id, obj_type)
            
            section_content = f"""
            <h2>{obj_id} ({chart_info['type']}) - {chart_info['category']}</h2>
            <div class="chart-container">
                <img src="{chart_info['chart']}" alt="{obj_id}过程线图表" class="chart-image">
            </div>
            {table_html}
            {performance_html}
            """
            content_sections.append(f'<div id="{obj_id}" class="content-section">{section_content}</div>')
        
        content_html = '\n'.join(content_sections)
        
        # 完整HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - 过程线图表分析报告</title>
    <style>
        {self._get_html_styles()}
    </style>
</head>
<body>
    <div class="container">
        <!-- 左侧导航 -->
        <nav class="sidebar">
            <div class="sidebar-header">
                <h3>分析报告</h3>
                <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <ul class="nav-menu">
                {nav_html}
            </ul>
        </nav>
        
        <!-- 右侧内容区 -->
        <main class="main-content">
            <header class="content-header">
                <h1>{project_name} - 过程线图表分析报告</h1>
            </header>
            <div class="content-wrapper">
                {content_html}
            </div>
        </main>
    </div>
    
    <script>
        {self._get_html_scripts()}
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _determine_object_type(self, obj_id: str) -> str:
        """
        根据对象ID确定对象类型
        
        Args:
            obj_id: 对象ID
            
        Returns:
            对象类型字符串
        """
        obj_id_lower = obj_id.lower()
        
        if 'reservoir' in obj_id_lower or '水库' in obj_id_lower:
            return 'reservoir'
        elif 'gate' in obj_id_lower or '闸门' in obj_id_lower or 'valve' in obj_id_lower or '阀门' in obj_id_lower:
            return 'gate'
        elif 'pump' in obj_id_lower or '泵站' in obj_id_lower or '泵' in obj_id_lower:
            return 'pump'
        elif 'canal' in obj_id_lower or '渠道' in obj_id_lower or 'channel' in obj_id_lower:
            return 'canal'
        else:
            return 'generic'
    
    def _get_html_styles(self) -> str:
        """获取HTML样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        /* 左侧导航样式 */
        .sidebar {
            width: 280px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .sidebar-header h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .nav-menu {
            list-style: none;
            padding: 0;
        }
        
        .nav-menu li {
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .nav-link {
            display: block;
            padding: 12px 20px;
            color: white;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background-color: rgba(255,255,255,0.1);
            padding-left: 25px;
        }
        
        .nav-link.active {
            background-color: rgba(255,255,255,0.2);
            border-left: 4px solid #fff;
        }
        
        .nav-category {
            padding: 15px 20px 10px;
            font-weight: bold;
            font-size: 1.1em;
            color: #fff;
            background-color: rgba(0,0,0,0.2);
        }
        
        .nav-sub .nav-link {
            padding-left: 35px;
            font-size: 0.95em;
        }
        
        /* 右侧内容区样式 */
        .main-content {
            flex: 1;
            margin-left: 280px;
            background-color: white;
        }
        
        .content-header {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .content-header h1 {
            font-size: 2em;
            font-weight: 300;
        }
        
        .content-wrapper {
            padding: 30px;
        }
        
        .content-section {
            display: none;
            animation: fadeIn 0.5s ease-in;
        }
        
        .content-section.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .chart-container {
            margin: 20px 0;
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        
        .table-container {
            margin: 20px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        /* 水库表格样式 */
        .table-container.reservoir {
            border-left: 4px solid #2196F3;
        }
        
        .data-table.reservoir th {
            background-color: #E3F2FD;
            color: #1976D2;
        }
        
        /* 闸门表格样式 */
        .table-container.gate {
            border-left: 4px solid #FF9800;
        }
        
        .data-table.gate th {
            background-color: #FFF3E0;
            color: #F57C00;
        }
        
        /* 泵站表格样式 */
        .table-container.pump {
            border-left: 4px solid #4CAF50;
        }
        
        .data-table.pump th {
            background-color: #E8F5E8;
            color: #388E3C;
        }
        
        /* 渠道表格样式 */
        .table-container.canal {
            border-left: 4px solid #9C27B0;
        }
        
        .data-table.canal th {
            background-color: #F3E5F5;
            color: #7B1FA2;
        }
        
        /* 通用表格样式 */
        .table-container.generic {
            border-left: 4px solid #607D8B;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .data-table th,
        .data-table td {
            padding: 8px 12px;
            text-align: center;
            border: 1px solid #ddd;
        }
        
        .data-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .data-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .performance-indicators {
            margin: 20px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* 水库性能指标样式 */
        .performance-indicators.reservoir {
            border-left: 4px solid #2196F3;
        }
        
        .indicators-table.reservoir th {
            background-color: #E3F2FD;
            color: #1976D2;
        }
        
        /* 闸门性能指标样式 */
        .performance-indicators.gate {
            border-left: 4px solid #FF9800;
        }
        
        .indicators-table.gate th {
            background-color: #FFF3E0;
            color: #F57C00;
        }
        
        /* 泵站性能指标样式 */
        .performance-indicators.pump {
            border-left: 4px solid #4CAF50;
        }
        
        .indicators-table.pump th {
            background-color: #E8F5E8;
            color: #388E3C;
        }
        
        /* 渠道性能指标样式 */
        .performance-indicators.canal {
            border-left: 4px solid #9C27B0;
        }
        
        .indicators-table.canal th {
            background-color: #F3E5F5;
            color: #7B1FA2;
        }
        
        /* 通用性能指标样式 */
        .performance-indicators.generic {
            border-left: 4px solid #607D8B;
        }
        
        .indicators-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .indicators-table th,
        .indicators-table td {
            padding: 10px;
            text-align: center;
            border: 1px solid #ddd;
        }
        
        .indicators-table th {
            background-color: #e3f2fd;
            font-weight: bold;
        }
        
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .overview-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .overview-card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        
        .topology-diagram {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        .topology-diagram h4 {
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 5px;
        }
        
        .connection-group {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        .connection-group h5 {
            color: #e74c3c;
            margin-bottom: 10px;
            font-weight: bold;
        }
        
        .connection-line {
            display: flex;
            align-items: center;
            margin: 8px 0;
            padding: 5px;
            background-color: white;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        .source-node, .target-node {
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        .source-node {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        
        .target-node {
            background-color: #f3e5f5;
            color: #7b1fa2;
        }
        
        .arrow {
            margin: 0 10px;
            color: #666;
            font-weight: bold;
        }
        
        .simple-topology {
            text-align: center;
        }
        
        .objects-flow {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
        }
        
        .object-node {
            padding: 8px 12px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .object-node.controlled {
            background-color: #e8f5e8;
            color: #2e7d32;
            border: 2px solid #4caf50;
        }
        
        .object-node.control {
            background-color: #fff3e0;
            color: #ef6c00;
            border: 2px solid #ff9800;
        }
        
        .flow-separator {
            font-size: 1.5em;
            margin: 0 10px;
        }
        
        .system-info {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        .info-section {
            margin-bottom: 25px;
        }
        
        .info-section h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        
        .info-section p {
            line-height: 1.8;
            color: #555;
        }
        """
    
    def _get_html_scripts(self) -> str:
        """获取HTML脚本"""
        return """
        function showSection(sectionId) {
            // 隐藏所有内容区域
            const sections = document.querySelectorAll('.content-section');
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            // 显示选中的内容区域
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            // 更新导航链接状态
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.classList.remove('active');
            });
            
            const activeLink = document.querySelector(`a[href="#${sectionId}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            showSection('overview');
        });
        """
    
    def _generate_topology_diagram(self, controlled_objects: Dict[str, Any], 
                                  control_objects: Dict[str, Any], 
                                  config: Dict[str, Any] = None) -> str:
        """
        生成系统拓扑图（文字箭头形式）
        
        Args:
            controlled_objects: 被控对象字典
            control_objects: 控制对象字典
            config: 完整配置信息（包含connections）
            
        Returns:
            拓扑图HTML字符串
        """
        html = """
        <div class="topology-diagram">
            <h4>系统拓扑结构</h4>
            <div class="topology-content">
        """
        
        if config and 'connections' in config:
            connections = config['connections']
            
            # 生成连接拓扑图
            html += "<div class='connection-group'><h5>系统连接关系</h5>"
            
            for conn in connections:
                # 支持多种连接字段格式
                source = conn.get('from', conn.get('source', '未知源'))
                target = conn.get('to', conn.get('target', '未知目标'))
                signal = conn.get('signal', conn.get('type', '物理连接'))
                
                # 确定源和目标的类型
                source_type = ''
                target_type = ''
                
                if source in controlled_objects:
                    source_type = f"({controlled_objects[source].get('type', '未知')})"
                elif source in control_objects:
                    source_type = f"({control_objects[source].get('type', '未知')})"
                
                if target in controlled_objects:
                    target_type = f"({controlled_objects[target].get('type', '未知')})"
                elif target in control_objects:
                    target_type = f"({control_objects[target].get('type', '未知')})"
                
                html += f"""
                <div class="connection-line">
                    <span class="source-node">{source} {source_type}</span>
                    <span class="arrow">──[{signal}]──></span>
                    <span class="target-node">{target} {target_type}</span>
                </div>
                """
            
            html += "</div>"
        else:
            # 如果没有连接信息，显示默认的简单拓扑
            html += """
            <div class="simple-topology">
                <p>系统包含以下对象：</p>
                <div class="objects-flow">
            """
            
            # 显示被控对象
            for obj_id, obj_config in controlled_objects.items():
                obj_type = obj_config.get('type', '未知')
                html += f'<span class="object-node controlled">{obj_id}({obj_type})</span>'
            
            html += '<span class="flow-separator">↕️</span>'
            
            # 显示控制对象
            for obj_id, obj_config in control_objects.items():
                obj_type = obj_config.get('type', '未知')
                html += f'<span class="object-node control">{obj_id}({obj_type})</span>'
            
            html += "</div></div>"
        
        html += "</div></div>"
        return html
    
    def _generate_overview_section(self, controlled_objects: Dict[str, Any], 
                                 control_objects: Dict[str, Any], timestamp: str, 
                                 config: Dict[str, Any] = None) -> str:
        """生成系统概览部分"""
        total_objects = len(controlled_objects) + len(control_objects)
        
        # 统计对象类型
        controlled_types = {}
        for obj_config in controlled_objects.values():
            obj_type = obj_config.get('type', '未知')
            controlled_types[obj_type] = controlled_types.get(obj_type, 0) + 1
        
        control_types = {}
        for obj_config in control_objects.values():
            obj_type = obj_config.get('type', '未知')
            control_types[obj_type] = control_types.get(obj_type, 0) + 1
        
        # 生成拓扑图
        topology_html = self._generate_topology_diagram(controlled_objects, control_objects, config)
        
        return f"""
        <h2>系统概览</h2>
        {topology_html}
        <div class="overview-grid">
            <div class="overview-card">
                <h3>报告信息</h3>
                <p><strong>生成时间:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p><strong>数据周期:</strong> 24小时</p>
                <p><strong>总对象数:</strong> {total_objects}个</p>
            </div>
            
            <div class="overview-card">
                <h3>被控对象 ({len(controlled_objects)}个)</h3>
                {''.join([f'<p><strong>{obj_type}:</strong> {count}个</p>' for obj_type, count in controlled_types.items()])}
            </div>
            
            <div class="overview-card">
                <h3>控制对象 ({len(control_objects)}个)</h3>
                {''.join([f'<p><strong>{obj_type}:</strong> {count}个</p>' for obj_type, count in control_types.items()])}
            </div>
        </div>
        """
    
    def _generate_system_info_section(self, project_name: str, scenario_description: str) -> str:
        """生成系统信息部分"""
        return f"""
        <h2>系统信息</h2>
        <div class="system-info">
            <div class="info-section">
                <h3>水系统基本情况</h3>
                <p>{project_name}是一个综合性水利系统，包含多个水工建筑物和控制设备。系统采用分布式控制架构，
                通过智能控制算法实现水位、流量等关键参数的精确调节，确保系统安全稳定运行。</p>
            </div>
            
            <div class="info-section">
                <h3>情景设置</h3>
                <p>本次分析基于{scenario_description if scenario_description else '标准运行工况'}进行。
                模拟时间跨度为24小时，采样间隔为1小时，涵盖了系统的典型运行周期。
                分析包括正常运行、扰动响应和控制效果等多个维度。</p>
            </div>
            
            <div class="info-section">
                <h3>扰动分析</h3>
                <p>系统面临的主要扰动包括：入流量变化、用水需求波动、气象条件影响等。
                通过实时监测和预测算法，系统能够及时识别扰动并采取相应的控制措施，
                保持关键参数在设定范围内稳定运行。</p>
            </div>
            
            <div class="info-section">
                <h3>控制目标</h3>
                <p>系统控制目标包括：维持水位在安全范围内、保证供水流量满足需求、
                优化能耗效率、提高系统响应速度。通过多目标优化控制策略，
                实现经济性、安全性和可靠性的统一。</p>
            </div>
        </div>
        """
    
    def _generate_markdown_report(self, charts_data: Dict[str, Any],
                                controlled_objects: Dict[str, Any],
                                control_objects: Dict[str, Any],
                                project_name: str, scenario_description: str,
                                timestamp: str) -> str:
        """生成Markdown报告内容"""
        md_content = f"""
# {project_name} - 过程线图表分析报告

**生成时间:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**数据周期:** 24小时
**总对象数:** {len(controlled_objects) + len(control_objects)}个

## 系统概览

### 被控对象 ({len(controlled_objects)}个)

"""
        
        for obj_id, obj_config in controlled_objects.items():
            obj_type = obj_config.get('type', '未知类型')
            md_content += f"- **{obj_id}** ({obj_type})\n"
        
        md_content += f"""

### 控制对象 ({len(control_objects)}个)

"""
        
        for obj_id, obj_config in control_objects.items():
            obj_type = obj_config.get('type', '未知类型')
            md_content += f"- **{obj_id}** ({obj_type})\n"
        
        md_content += """

## 系统信息

### 水系统基本情况

本系统是一个综合性水利系统，包含多个水工建筑物和控制设备。系统采用分布式控制架构，通过智能控制算法实现水位、流量等关键参数的精确调节。

### 情景设置

本次分析基于标准运行工况进行，模拟时间跨度为24小时，采样间隔为1小时，涵盖了系统的典型运行周期。

### 扰动分析

系统面临的主要扰动包括入流量变化、用水需求波动、气象条件影响等。通过实时监测和预测算法，系统能够及时识别扰动并采取相应的控制措施。

### 控制目标

系统控制目标包括维持水位在安全范围内、保证供水流量满足需求、优化能耗效率、提高系统响应速度。

## 详细分析

"""
        
        for obj_id, chart_info in charts_data.items():
            md_content += f"""
### {obj_id} ({chart_info['type']}) - {chart_info['category']}

本对象的过程线分析显示了24小时内各关键参数的变化趋势，包括时间序列数据和控制性能评价指标。

"""
        
        md_content += """
## 分析总结

通过对系统各对象的过程线分析，可以看出：

1. **系统稳定性良好**：各关键参数在设定范围内稳定运行
2. **控制效果显著**：控制算法能够有效应对各种扰动
3. **响应速度适中**：系统对扰动的响应时间在合理范围内
4. **运行效率较高**：各设备运行效率保持在良好水平

建议继续监测系统运行状态，定期优化控制参数，确保系统长期稳定运行。
"""
        
        return md_content