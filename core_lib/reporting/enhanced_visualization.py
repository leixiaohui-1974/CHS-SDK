#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强可视化模块
提供图表叠加显示和图表与数据表组合功能
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from io import BytesIO
import base64
from typing import Dict, Any, List, Tuple
import logging
from matplotlib.gridspec import GridSpec

from core_lib.utils import seaborn_support

logger = logging.getLogger(__name__)

class EnhancedVisualization:
    """增强可视化类"""
    
    def __init__(self):
        seaborn_support.ensure_matplotlib_style('seaborn-v0_8')
        seaborn_support.set_palette('husl')
        self.setup_chinese_font()
        
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
    
    def generate_separate_analysis_charts(self, controlled_objects: Dict[str, Any], 
                                         control_objects: Dict[str, Any]) -> Dict[str, str]:
        """生成分离的6维度分析图表"""
        charts = {}
        
        try:
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            # 定义颜色映射
            colors = plt.cm.Set3(np.linspace(0, 1, len(controlled_objects) + len(control_objects)))
            
            # 1. 扰动分析图
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    disturbance = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (入流量扰动)'
                else:
                    disturbance = 10 + 5 * np.sin(time_points/600 + color_idx) + np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (外部扰动)'
                
                ax1.plot(time_minutes, disturbance, color=colors[color_idx], linewidth=2.5, 
                        label=label, alpha=0.8, marker='o', markersize=3)
                color_idx += 1
            
            ax1.set_title('扰动输入分析', fontsize=16, fontweight='bold', pad=20)
            ax1.set_xlabel('时间 (分钟)', fontsize=12)
            ax1.set_ylabel('扰动强度', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['disturbance'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            # 2. 状态响应图
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    state = 15 + 1.5 * np.sin(time_points/800 + color_idx) + 0.2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (水位)'
                else:
                    state = 5 + 2 * np.sin(time_points/800 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (状态参数)'
                
                ax2.plot(time_minutes, state, color=colors[color_idx], linewidth=2.5, 
                        label=label, alpha=0.8, marker='s', markersize=3)
                color_idx += 1
            
            ax2.set_title('状态响应分析', fontsize=16, fontweight='bold', pad=20)
            ax2.set_xlabel('时间 (分钟)', fontsize=12)
            ax2.set_ylabel('状态值', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['state'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            # 3. 控制目标图
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    target = np.where(time_points < 1800, 16.0, 16.5)
                    label = f'{comp_name} (目标水位)'
                else:
                    target = np.where(time_points < 1800, 6.0 + color_idx*0.2, 6.5 + color_idx*0.2)
                    label = f'{comp_name} (控制目标)'
                
                ax3.plot(time_minutes, target, color=colors[color_idx], linewidth=2.5, 
                        linestyle='--', label=label, alpha=0.8, marker='^', markersize=3)
                color_idx += 1
            
            ax3.set_title('控制目标设定', fontsize=16, fontweight='bold', pad=20)
            ax3.set_xlabel('时间 (分钟)', fontsize=12)
            ax3.set_ylabel('目标值', fontsize=12)
            ax3.grid(True, alpha=0.3)
            ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['target'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            # 4. 控制指令图
            fig4, ax4 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            # 被控对象的控制指令
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    command = 30 + 10 * np.sin(time_points/700 + color_idx) + 2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (泄流指令)'
                else:
                    command = 3 + 1.5 * np.sin(time_points/700 + color_idx) + 0.3 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (控制指令)'
                
                ax4.plot(time_minutes, command, color=colors[color_idx], linewidth=2.5, 
                        label=label, alpha=0.8, marker='d', markersize=3)
                color_idx += 1
            
            # 控制对象的执行指令
            for comp_name, comp_config in control_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'valve':
                    command = 0.5 + 0.3 * np.sin(time_points/600 + color_idx) + 0.1 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (开度指令)'
                elif comp_type.lower() == 'pump':
                    command = 80 + 20 * np.sin(time_points/800 + color_idx) + 5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (功率指令)'
                else:
                    command = 2 + 1 * np.sin(time_points/700 + color_idx) + 0.2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (执行指令)'
                
                ax4.plot(time_minutes, command, color=colors[color_idx], linewidth=2.5, 
                        linestyle=':', label=label, alpha=0.8, marker='v', markersize=3)
                color_idx += 1
            
            ax4.set_title('控制指令执行', fontsize=16, fontweight='bold', pad=20)
            ax4.set_xlabel('时间 (分钟)', fontsize=12)
            ax4.set_ylabel('指令值', fontsize=12)
            ax4.grid(True, alpha=0.3)
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['command'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            # 5. 流量响应图
            fig5, ax5 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    flow = 25 + 8 * np.sin(time_points/900 + color_idx) + 3 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (出流量)'
                else:
                    flow = 8 + 3 * np.sin(time_points/900 + color_idx) + 0.8 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (流量)'
                
                ax5.plot(time_minutes, flow, color=colors[color_idx], linewidth=2.5, 
                        label=label, alpha=0.8, marker='p', markersize=3)
                color_idx += 1
            
            ax5.set_title('流量响应分析', fontsize=16, fontweight='bold', pad=20)
            ax5.set_xlabel('时间 (分钟)', fontsize=12)
            ax5.set_ylabel('流量 (m³/s)', fontsize=12)
            ax5.grid(True, alpha=0.3)
            ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['flow'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            # 6. 综合状态图
            fig6, ax6 = plt.subplots(figsize=(12, 6))
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    volume = 21 + 0.5 * np.sin(time_points/1000 + color_idx) + 0.1 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (蓄水量)'
                else:
                    other_state = 12 + 2 * np.sin(time_points/1000 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (综合状态)'
                    volume = other_state
                
                ax6.plot(time_minutes, volume, color=colors[color_idx], linewidth=2.5, 
                        label=label, alpha=0.8, marker='h', markersize=3)
                color_idx += 1
            
            ax6.set_title('综合状态分析', fontsize=16, fontweight='bold', pad=20)
            ax6.set_xlabel('时间 (分钟)', fontsize=12)
            ax6.set_ylabel('状态值', fontsize=12)
            ax6.grid(True, alpha=0.3)
            ax6.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            charts['comprehensive'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            return charts
        
        except Exception as e:
            logger.error(f"分离分析图表生成失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def generate_enhanced_control_charts_per_object(self, control_objects: Dict[str, Any], 
                                                   controlled_objects: Dict[str, Any],
                                                   agents: Dict[str, Any]) -> Dict[str, str]:
        """为每个控制对象生成增强的图表：控制目标、指令、执行器状态对比图，叠加被控对象指标，控制误差分析"""
        charts = {}
        
        try:
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            # 为每个控制对象生成增强图表
            for comp_name, comp_config in control_objects.items():
                comp_type = comp_config.get('type', '未知')
                
                # 创建子图
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
                
                if comp_type.lower() == 'pump':
                    # 泵站控制图表
                    target_flow = np.where(time_points < 1800, 50.0, 60.0)
                    control_cmd = target_flow + 2 * np.sin(time_points/600) + np.random.normal(0, 1, len(time_points))
                    actual_flow = control_cmd + 3 * np.sin(time_points/500) + 1.5 * np.random.normal(0, 1, len(time_points))
                    
                    # 控制目标、指令、执行器状态对比
                    ax1.plot(time_minutes, target_flow, 'r--', linewidth=2.5, 
                            label='控制目标', alpha=0.8, marker='s', markersize=3)
                    ax1.plot(time_minutes, control_cmd, 'b-', linewidth=2.5, 
                            label='控制指令', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, actual_flow, 'g-', linewidth=2.5, 
                            label='执行器状态', alpha=0.8, marker='^', markersize=2)
                    
                    ax1.set_ylabel('流量 (m³/s)')
                    ax1.set_title('控制目标、指令、执行器状态对比', fontsize=12, fontweight='bold')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # 控制执行与被控对象响应叠加
                    controlled_water_level = 15 + 0.5 * actual_flow/50 + 0.3 * np.sin(time_points/1000) + 0.1 * np.random.normal(0, 1, len(time_points))
                    target_water_level = np.where(time_points < 1800, 14.0, 14.5)
                    
                    ax2_twin = ax2.twinx()
                    
                    # 左轴：泵站流量
                    ax2.plot(time_minutes, actual_flow, 'g-', linewidth=2.5, 
                            label='泵站流量', alpha=0.8)
                    ax2.set_ylabel('流量 (m³/s)', color='g')
                    ax2.tick_params(axis='y', labelcolor='g')
                    
                    # 右轴：被控水位
                    ax2_twin.plot(time_minutes, controlled_water_level, 'b-', linewidth=2.5, 
                                 label='实际水位', alpha=0.8)
                    ax2_twin.plot(time_minutes, target_water_level, 'r--', linewidth=2.5, 
                                 label='目标水位', alpha=0.8)
                    ax2_twin.set_ylabel('水位 (m)', color='b')
                    ax2_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax2.set_title('控制执行与被控对象响应叠加', fontsize=12, fontweight='bold')
                    
                    # 合并图例
                    lines1, labels1 = ax2.get_legend_handles_labels()
                    lines2, labels2 = ax2_twin.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                    
                    # 控制误差分析
                    flow_error = target_flow - actual_flow
                    water_level_error = target_water_level - controlled_water_level
                    
                    ax3_twin = ax3.twinx()
                    
                    # 左轴：流量误差
                    ax3.plot(time_minutes, flow_error, 'r-', linewidth=2.5, 
                            label='流量误差', alpha=0.8)
                    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3.set_ylabel('流量误差 (m³/s)', color='r')
                    ax3.tick_params(axis='y', labelcolor='r')
                    
                    # 右轴：水位误差
                    ax3_twin.plot(time_minutes, water_level_error, 'b-', linewidth=2.5, 
                                 label='水位误差', alpha=0.8)
                    ax3_twin.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3_twin.set_ylabel('水位误差 (m)', color='b')
                    ax3_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax3.set_title('控制误差过程线', fontsize=12, fontweight='bold')
                    
                    # 合并图例
                    lines3, labels3 = ax3.get_legend_handles_labels()
                    lines4, labels4 = ax3_twin.get_legend_handles_labels()
                    ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper right')
                    
                    # 控制性能评价指标
                    mae_flow = np.mean(np.abs(flow_error))
                    rmse_flow = np.sqrt(np.mean(flow_error**2))
                    mae_water = np.mean(np.abs(water_level_error))
                    rmse_water = np.sqrt(np.mean(water_level_error**2))
                    
                    stability_flow = np.std(flow_error)
                    stability_water = np.std(water_level_error)
                    
                    metrics = ['MAE\n流量', 'RMSE\n流量', 'MAE\n水位', 'RMSE\n水位', '稳定性\n流量', '稳定性\n水位']
                    values = [mae_flow, rmse_flow, mae_water*10, rmse_water*10, stability_flow, stability_water*10]
                    colors = ['#FF6B6B', '#FF8E8E', '#4ECDC4', '#6ED4D4', '#45B7D1', '#6BC5E8']
                    
                    bars = ax4.bar(metrics, values, color=colors, alpha=0.7)
                    ax4.set_title('控制性能评价指标', fontsize=12, fontweight='bold')
                    ax4.set_ylabel('误差值')
                    
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                f'{value:.3f}', ha='center', va='bottom', fontsize=9)
                
                else:
                    # 其他控制对象图表
                    target_value = np.where(time_points < 1800, 0.7, 0.9)
                    control_cmd = target_value + 0.05 * np.sin(time_points/500) + 0.02 * np.random.normal(0, 1, len(time_points))
                    actual_value = control_cmd + 0.08 * np.sin(time_points/400) + 0.03 * np.random.normal(0, 1, len(time_points))
                    
                    # 控制目标、指令、执行器状态对比
                    ax1.plot(time_minutes, target_value*100, 'r--', linewidth=2.5, 
                            label='控制目标', alpha=0.8, marker='s', markersize=3)
                    ax1.plot(time_minutes, control_cmd*100, 'b-', linewidth=2.5, 
                            label='控制指令', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, actual_value*100, 'g-', linewidth=2.5, 
                            label='执行器状态', alpha=0.8, marker='^', markersize=2)
                    
                    ax1.set_ylabel('控制量 (%)')
                    ax1.set_title('控制目标、指令、执行器状态对比', fontsize=12, fontweight='bold')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # 控制执行与被控对象响应叠加
                    controlled_indicator = 10 + 5 * actual_value + 0.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    target_indicator = np.where(time_points < 1800, 13.5, 14.5)
                    
                    ax2_twin = ax2.twinx()
                    
                    ax2.plot(time_minutes, actual_value*100, 'g-', linewidth=2.5, 
                            label='控制执行', alpha=0.8)
                    ax2.set_ylabel('控制量 (%)', color='g')
                    ax2.tick_params(axis='y', labelcolor='g')
                    
                    ax2_twin.plot(time_minutes, controlled_indicator, 'b-', linewidth=2.5, 
                                 label='实际指标', alpha=0.8)
                    ax2_twin.plot(time_minutes, target_indicator, 'r--', linewidth=2.5, 
                                 label='目标指标', alpha=0.8)
                    ax2_twin.set_ylabel('被控指标', color='b')
                    ax2_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax2.set_title('控制执行与被控对象响应叠加', fontsize=12, fontweight='bold')
                    
                    lines1, labels1 = ax2.get_legend_handles_labels()
                    lines2, labels2 = ax2_twin.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                    
                    # 控制误差分析
                    control_error = (target_value - actual_value) * 100
                    indicator_error = target_indicator - controlled_indicator
                    
                    ax3_twin = ax3.twinx()
                    
                    ax3.plot(time_minutes, control_error, 'r-', linewidth=2.5, 
                            label='控制误差', alpha=0.8)
                    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3.set_ylabel('控制误差 (%)', color='r')
                    ax3.tick_params(axis='y', labelcolor='r')
                    
                    ax3_twin.plot(time_minutes, indicator_error, 'b-', linewidth=2.5, 
                                 label='指标误差', alpha=0.8)
                    ax3_twin.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3_twin.set_ylabel('指标误差', color='b')
                    ax3_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax3.set_title('控制误差过程线', fontsize=12, fontweight='bold')
                    
                    lines3, labels3 = ax3.get_legend_handles_labels()
                    lines4, labels4 = ax3_twin.get_legend_handles_labels()
                    ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper right')
                    
                    # 控制性能评价指标
                    mae_control = np.mean(np.abs(control_error))
                    rmse_control = np.sqrt(np.mean(control_error**2))
                    mae_indicator = np.mean(np.abs(indicator_error))
                    rmse_indicator = np.sqrt(np.mean(indicator_error**2))
                    
                    stability_control = np.std(control_error)
                    stability_indicator = np.std(indicator_error)
                    
                    metrics = ['MAE\n控制', 'RMSE\n控制', 'MAE\n指标', 'RMSE\n指标', '稳定性\n控制', '稳定性\n指标']

                plt.close()
                
                charts[comp_name] = f"data:image/png;base64,{image_base64}"
        
        except Exception as e:
            logger.error(f"增强控制图表生成失败: {e}")
            import traceback
            traceback.print_exc()
        
        return charts

    def generate_enhanced_control_charts_per_object(self, controlled_objects: Dict[str, Any], 
                                                   control_objects: Dict[str, Any]) -> Dict[str, str]:
        """
        为每个被控对象生成增强的控制图表
        """
        charts = {}
        
        try:
            # 设置中文字体
            self.setup_chinese_font()
            
            # 生成时间序列
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                
                # 创建子图布局
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
                
                if comp_type.lower() == 'pump':
                    # 泵站控制分析的模拟数据
                    target_flow = np.where(time_points < 1800, 15.0, 18.0)
                    control_cmd = target_flow + 0.5 * np.sin(time_points/500) + 0.2 * np.random.normal(0, 1, len(time_points))
                    actual_flow = control_cmd + 0.8 * np.sin(time_points/400) + 0.3 * np.random.normal(0, 1, len(time_points))
                    
                    # 1. 控制目标、指令、执行器状态对比图
                    ax1.plot(time_minutes, target_flow, 'r--', linewidth=2.5, 
                            label='控制目标', alpha=0.8, marker='s', markersize=3)
                    ax1.plot(time_minutes, control_cmd, 'b-', linewidth=2.5, 
                            label='控制指令', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, actual_flow, 'g-', linewidth=2.5, 
                            label='执行器状态', alpha=0.8, marker='^', markersize=2)
                    
                    ax1.set_ylabel('流量 (m³/s)')
                    ax1.set_title('控制目标、指令、执行器状态对比', fontsize=12, fontweight='bold')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # 2. 与被控对象控制指标叠加图
                    controlled_water_level = 12 + 0.1 * actual_flow + 0.3 * np.sin(time_points/800) + 0.1 * np.random.normal(0, 1, len(time_points))
                    target_water_level = np.where(time_points < 1800, 14.0, 14.5)
                    
                    ax2_twin = ax2.twinx()
                    
                    # 左轴：泵站流量
                    ax2.plot(time_minutes, actual_flow, 'g-', linewidth=2.5, 
                            label='泵站流量', alpha=0.8)
                    ax2.set_ylabel('流量 (m³/s)', color='g')
                    ax2.tick_params(axis='y', labelcolor='g')
                    
                    # 右轴：被控对象水位
                    ax2_twin.plot(time_minutes, controlled_water_level, 'b-', linewidth=2.5, 
                                 label='实际水位', alpha=0.8)
                    ax2_twin.plot(time_minutes, target_water_level, 'r--', linewidth=2.5, 
                                 label='目标水位', alpha=0.8)
                    ax2_twin.set_ylabel('水位 (m)', color='b')
                    ax2_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax2.set_title('控制执行与被控对象响应叠加', fontsize=12, fontweight='bold')
                    
                    # 合并图例
                    lines1, labels1 = ax2.get_legend_handles_labels()
                    lines2, labels2 = ax2_twin.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                    
                    # 3. 控制误差过程线
                    flow_error = target_flow - actual_flow
                    water_level_error = target_water_level - controlled_water_level
                    
                    ax3_twin = ax3.twinx()
                    
                    # 左轴：流量误差
                    ax3.plot(time_minutes, flow_error, 'r-', linewidth=2.5, 
                            label='流量误差', alpha=0.8)
                    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3.set_ylabel('流量误差 (m³/s)', color='r')
                    ax3.tick_params(axis='y', labelcolor='r')
                    
                    # 右轴：水位误差
                    ax3_twin.plot(time_minutes, water_level_error, 'b-', linewidth=2.5, 
                                 label='水位误差', alpha=0.8)
                    ax3_twin.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3_twin.set_ylabel('水位误差 (m)', color='b')
                    ax3_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax3.set_title('控制误差过程线', fontsize=12, fontweight='bold')
                    
                    # 合并图例
                    lines3, labels3 = ax3.get_legend_handles_labels()
                    lines4, labels4 = ax3_twin.get_legend_handles_labels()
                    ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper right')
                    
                    # 4. 控制性能评价指标
                    mae_flow = np.mean(np.abs(flow_error))
                    rmse_flow = np.sqrt(np.mean(flow_error**2))
                    mae_water = np.mean(np.abs(water_level_error))
                    rmse_water = np.sqrt(np.mean(water_level_error**2))
                    
                    stability_flow = np.std(flow_error)
                    stability_water = np.std(water_level_error)
                    
                    metrics = ['MAE\n流量', 'RMSE\n流量', 'MAE\n水位', 'RMSE\n水位', '稳定性\n流量', '稳定性\n水位']
                    values = [mae_flow, rmse_flow, mae_water*10, rmse_water*10, stability_flow, stability_water*10]
                    colors = ['#FF6B6B', '#FF8E8E', '#4ECDC4', '#6ED4D4', '#45B7D1', '#6BC5E8']
                    
                    bars = ax4.bar(metrics, values, color=colors, alpha=0.7)
                    ax4.set_title('控制性能评价指标', fontsize=12, fontweight='bold')
                    ax4.set_ylabel('误差值')
                    
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                f'{value:.3f}', ha='center', va='bottom', fontsize=9)
                
                else:
                    # 其他控制对象的通用分析
                    target_value = np.where(time_points < 1800, 0.7, 0.9)
                    control_cmd = target_value + 0.05 * np.sin(time_points/500) + 0.02 * np.random.normal(0, 1, len(time_points))
                    actual_value = control_cmd + 0.08 * np.sin(time_points/400) + 0.03 * np.random.normal(0, 1, len(time_points))
                    
                    # 1. 控制目标、指令、执行器状态对比图
                    ax1.plot(time_minutes, target_value*100, 'r--', linewidth=2.5, 
                            label='控制目标', alpha=0.8, marker='s', markersize=3)
                    ax1.plot(time_minutes, control_cmd*100, 'b-', linewidth=2.5, 
                            label='控制指令', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, actual_value*100, 'g-', linewidth=2.5, 
                            label='执行器状态', alpha=0.8, marker='^', markersize=2)
                    
                    ax1.set_ylabel('控制量 (%)')
                    ax1.set_title('控制目标、指令、执行器状态对比', fontsize=12, fontweight='bold')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # 2. 与被控对象控制指标叠加图
                    controlled_indicator = 10 + 5 * actual_value + 0.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    target_indicator = np.where(time_points < 1800, 13.5, 14.5)
                    
                    ax2_twin = ax2.twinx()
                    
                    ax2.plot(time_minutes, actual_value*100, 'g-', linewidth=2.5, 
                            label='控制执行', alpha=0.8)
                    ax2.set_ylabel('控制量 (%)', color='g')
                    ax2.tick_params(axis='y', labelcolor='g')
                    
                    ax2_twin.plot(time_minutes, controlled_indicator, 'b-', linewidth=2.5, 
                                 label='实际指标', alpha=0.8)
                    ax2_twin.plot(time_minutes, target_indicator, 'r--', linewidth=2.5, 
                                 label='目标指标', alpha=0.8)
                    ax2_twin.set_ylabel('被控指标', color='b')
                    ax2_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax2.set_title('控制执行与被控对象响应叠加', fontsize=12, fontweight='bold')
                    
                    lines1, labels1 = ax2.get_legend_handles_labels()
                    lines2, labels2 = ax2_twin.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                    
                    # 3. 控制误差过程线
                    control_error = (target_value - actual_value) * 100
                    indicator_error = target_indicator - controlled_indicator
                    
                    ax3_twin = ax3.twinx()
                    
                    ax3.plot(time_minutes, control_error, 'r-', linewidth=2.5, 
                            label='控制误差', alpha=0.8)
                    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3.set_ylabel('控制误差 (%)', color='r')
                    ax3.tick_params(axis='y', labelcolor='r')
                    
                    ax3_twin.plot(time_minutes, indicator_error, 'b-', linewidth=2.5, 
                                 label='指标误差', alpha=0.8)
                    ax3_twin.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                    ax3_twin.set_ylabel('指标误差', color='b')
                    ax3_twin.tick_params(axis='y', labelcolor='b')
                    
                    ax3.set_title('控制误差过程线', fontsize=12, fontweight='bold')
                    
                    lines3, labels3 = ax3.get_legend_handles_labels()
                    lines4, labels4 = ax3_twin.get_legend_handles_labels()
                    ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper right')
                    
                    # 4. 控制性能评价指标
                    mae_control = np.mean(np.abs(control_error))
                    rmse_control = np.sqrt(np.mean(control_error**2))
                    mae_indicator = np.mean(np.abs(indicator_error))
                    rmse_indicator = np.sqrt(np.mean(indicator_error**2))
                    
                    stability_control = np.std(control_error)
                    stability_indicator = np.std(indicator_error)
                    
                    metrics = ['MAE\n控制', 'RMSE\n控制', 'MAE\n指标', 'RMSE\n指标', '稳定性\n控制', '稳定性\n指标']
                    values = [mae_control, rmse_control, mae_indicator, rmse_indicator, stability_control, stability_indicator]
                    colors = ['#FF6B6B', '#FF8E8E', '#4ECDC4', '#6ED4D4', '#45B7D1', '#6BC5E8']
                    
                    bars = ax4.bar(metrics, values, color=colors, alpha=0.7)
                    ax4.set_title('控制性能评价指标', fontsize=12, fontweight='bold')
                    ax4.set_ylabel('误差值')
                    
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                f'{value:.3f}', ha='center', va='bottom', fontsize=9)
                
                # 设置所有子图的x轴标签
                for ax in [ax1, ax2, ax3, ax4]:
                    ax.set_xlabel('时间 (分钟)')
                    ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                # 保存为base64字符串
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts[comp_name] = f"data:image/png;base64,{image_base64}"
        
        except Exception as e:
            logger.error(f"增强控制图表生成失败: {e}")
            import traceback
            traceback.print_exc()
        
        return charts
    
    def generate_overlay_analysis_chart(self, controlled_objects: Dict[str, Any], 
                                       control_objects: Dict[str, Any]) -> str:
        """生成6维度叠加分析图表（保留原方法以兼容）"""
        try:
            # 创建大图布局：3行2列，每个子图显示一个维度的所有对象
            fig = plt.figure(figsize=(20, 24))
            gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.2)
            
            fig.suptitle('水利系统扰动-响应-控制综合分析', fontsize=20, fontweight='bold', y=0.98)
            
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            # 定义颜色映射
            colors = plt.cm.Set3(np.linspace(0, 1, len(controlled_objects) + len(control_objects)))
            
            # 1. 扰动分析叠加图
            ax1 = fig.add_subplot(gs[0, 0])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    disturbance = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (入流量扰动)'
                    unit = 'm³/s'
                else:
                    disturbance = 10 + 5 * np.sin(time_points/600 + color_idx) + np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (外部扰动)'
                    unit = '扰动强度'
                
                ax1.plot(time_minutes, disturbance, color=colors[color_idx], linewidth=2, 
                        label=label, alpha=0.8)
                color_idx += 1
            
            ax1.set_title('1. 扰动输入分析', fontsize=14, fontweight='bold')
            ax1.set_xlabel('时间 (分钟)')
            ax1.set_ylabel('扰动强度')
            ax1.grid(True, alpha=0.3)
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 2. 状态响应叠加图
            ax2 = fig.add_subplot(gs[0, 1])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    state = 15 + 1.5 * np.sin(time_points/800 + color_idx) + 0.2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (水位)'
                    unit = 'm'
                else:
                    state = 5 + 2 * np.sin(time_points/800 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (状态参数)'
                    unit = '状态值'
                
                ax2.plot(time_minutes, state, color=colors[color_idx], linewidth=2, 
                        label=label, alpha=0.8)
                color_idx += 1
            
            ax2.set_title('2. 状态响应分析', fontsize=14, fontweight='bold')
            ax2.set_xlabel('时间 (分钟)')
            ax2.set_ylabel('状态值')
            ax2.grid(True, alpha=0.3)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 3. 控制目标叠加图
            ax3 = fig.add_subplot(gs[1, 0])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    target = np.where(time_points < 1800, 16.0, 16.5)
                    label = f'{comp_name} (目标水位)'
                else:
                    target = np.where(time_points < 1800, 6.0 + color_idx*0.2, 6.5 + color_idx*0.2)
                    label = f'{comp_name} (控制目标)'
                
                ax3.plot(time_minutes, target, color=colors[color_idx], linewidth=2, 
                        linestyle='--', label=label, alpha=0.8)
                color_idx += 1
            
            ax3.set_title('3. 控制目标设定', fontsize=14, fontweight='bold')
            ax3.set_xlabel('时间 (分钟)')
            ax3.set_ylabel('目标值')
            ax3.grid(True, alpha=0.3)
            ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 4. 控制指令叠加图
            ax4 = fig.add_subplot(gs[1, 1])
            color_idx = 0
            # 被控对象的控制指令
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    command = 30 + 10 * np.sin(time_points/700 + color_idx) + 2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (泄流指令)'
                else:
                    command = 3 + 1.5 * np.sin(time_points/700 + color_idx) + 0.3 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (控制指令)'
                
                ax4.plot(time_minutes, command, color=colors[color_idx], linewidth=2, 
                        label=label, alpha=0.8)
                color_idx += 1
            
            # 控制对象的执行指令
            for comp_name, comp_config in control_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'valve':
                    command = 0.5 + 0.3 * np.sin(time_points/600 + color_idx) + 0.1 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (开度指令)'
                elif comp_type.lower() == 'pump':
                    command = 80 + 20 * np.sin(time_points/800 + color_idx) + 5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (功率指令)'
                else:
                    command = 2 + 1 * np.sin(time_points/700 + color_idx) + 0.2 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (执行指令)'
                
                ax4.plot(time_minutes, command, color=colors[color_idx], linewidth=2, 
                        linestyle=':', label=label, alpha=0.8)
                color_idx += 1
            
            ax4.set_title('4. 控制指令执行', fontsize=14, fontweight='bold')
            ax4.set_xlabel('时间 (分钟)')
            ax4.set_ylabel('指令值')
            ax4.grid(True, alpha=0.3)
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 5. 流量响应叠加图
            ax5 = fig.add_subplot(gs[2, 0])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    flow = 25 + 8 * np.sin(time_points/900 + color_idx) + 3 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (出流量)'
                else:
                    flow = 8 + 3 * np.sin(time_points/900 + color_idx) + 0.8 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (流量)'
                
                ax5.plot(time_minutes, flow, color=colors[color_idx], linewidth=2, 
                        label=label, alpha=0.8)
                color_idx += 1
            
            ax5.set_title('5. 流量响应分析', fontsize=14, fontweight='bold')
            ax5.set_xlabel('时间 (分钟)')
            ax5.set_ylabel('流量 (m³/s)')
            ax5.grid(True, alpha=0.3)
            ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 6. 综合状态叠加图
            ax6 = fig.add_subplot(gs[2, 1])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    volume = 21 + 0.5 * np.sin(time_points/1000 + color_idx) + 0.1 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (蓄水量)'
                    unit = '百万m³'
                else:
                    other_state = 12 + 2 * np.sin(time_points/1000 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                    label = f'{comp_name} (综合状态)'
                    unit = '状态值'
                    volume = other_state
                
                ax6.plot(time_minutes, volume, color=colors[color_idx], linewidth=2, 
                        label=label, alpha=0.8)
                color_idx += 1
            
            ax6.set_title('6. 综合状态分析', fontsize=14, fontweight='bold')
            ax6.set_xlabel('时间 (分钟)')
            ax6.set_ylabel('状态值')
            ax6.grid(True, alpha=0.3)
            ax6.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 保存为base64字符串
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"生成叠加分析图表失败: {e}")
            return None
    
    def generate_chart_table_combination(self, controlled_objects: Dict[str, Any], 
                                       control_objects: Dict[str, Any]) -> str:
        """生成图表与数据表组合显示"""
        try:
            # 创建复合布局：上半部分是图表，下半部分是数据表
            fig = plt.figure(figsize=(24, 32))
            gs = GridSpec(4, 2, figure=fig, height_ratios=[1, 1, 0.8, 0.8], 
                         hspace=0.4, wspace=0.2)
            
            fig.suptitle('水利系统图表与数据表组合分析', fontsize=20, fontweight='bold', y=0.98)
            
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 7)  # 简化为7个时间点用于表格显示
            time_labels = [f"{int(t/60):02d}:00" for t in time_points]
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(controlled_objects)))
            
            # 上半部分：关键图表
            # 1. 扰动-响应关系图
            ax1 = fig.add_subplot(gs[0, 0])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    disturbance = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                    response = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    ax1.scatter(disturbance, response, color=colors[color_idx], s=100, 
                              label=f'{comp_name}', alpha=0.7)
                    # 添加趋势线
                    z = np.polyfit(disturbance, response, 1)
                    p = np.poly1d(z)
                    ax1.plot(disturbance, p(disturbance), color=colors[color_idx], 
                            linestyle='--', alpha=0.5)
                else:
                    disturbance = 10 + 5 * np.sin(time_points/600 + color_idx) + np.random.normal(0, 1, len(time_points))
                    response = 5 + 2 * np.sin(time_points/800 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                    ax1.scatter(disturbance, response, color=colors[color_idx], s=100, 
                              label=f'{comp_name}', alpha=0.7)
                    z = np.polyfit(disturbance, response, 1)
                    p = np.poly1d(z)
                    ax1.plot(disturbance, p(disturbance), color=colors[color_idx], 
                            linestyle='--', alpha=0.5)
                color_idx += 1
            
            ax1.set_title('扰动-响应关系分析', fontsize=14, fontweight='bold')
            ax1.set_xlabel('扰动强度')
            ax1.set_ylabel('状态响应')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 2. 控制效果分析图
            ax2 = fig.add_subplot(gs[0, 1])
            color_idx = 0
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                if comp_type.lower() == 'reservoir':
                    target = np.full(len(time_points), 16.0)
                    actual = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                else:
                    target = np.full(len(time_points), 6.0 + color_idx*0.2)
                    actual = 5 + 2 * np.sin(time_points/800 + color_idx) + 0.5 * np.random.normal(0, 1, len(time_points))
                
                ax2.plot(time_points/60, target, color=colors[color_idx], 
                        linestyle='--', linewidth=2, label=f'{comp_name} (目标)', alpha=0.8)
                ax2.plot(time_points/60, actual, color=colors[color_idx], 
                        linewidth=2, label=f'{comp_name} (实际)', alpha=0.8)
                color_idx += 1
            
            ax2.set_title('控制目标与实际效果对比', fontsize=14, fontweight='bold')
            ax2.set_xlabel('时间 (分钟)')
            ax2.set_ylabel('状态值')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 3. 系统性能热力图
            ax3 = fig.add_subplot(gs[1, :])
            
            # 创建性能矩阵数据
            objects = list(controlled_objects.keys())
            metrics = ['扰动强度', '状态响应', '控制精度', '流量稳定性', '能耗效率', '综合评分']
            
            # 生成模拟性能数据
            performance_data = np.random.rand(len(objects), len(metrics)) * 100
            
            # 创建热力图
            im = ax3.imshow(performance_data, cmap='RdYlGn', aspect='auto')
            
            # 设置标签
            ax3.set_xticks(np.arange(len(metrics)))
            ax3.set_yticks(np.arange(len(objects)))
            ax3.set_xticklabels(metrics)
            ax3.set_yticklabels(objects)
            
            # 添加数值标注
            for i in range(len(objects)):
                for j in range(len(metrics)):
                    text = ax3.text(j, i, f'{performance_data[i, j]:.1f}',
                                   ha="center", va="center", color="black", fontsize=10)
            
            ax3.set_title('系统性能综合评估热力图', fontsize=14, fontweight='bold')
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax3, orientation='horizontal', pad=0.1)
            cbar.set_label('性能评分 (0-100)', fontsize=12)
            
            # 下半部分：数据表格
            # 4. 被控对象数据表
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('tight')
            ax4.axis('off')
            
            # 创建被控对象数据表
            table_data = []
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                for i, time_label in enumerate(time_labels):
                    if comp_type.lower() == 'reservoir':
                        row = [
                            time_label,
                            comp_name,
                            f"{52.1 + 15*np.sin(i/2):.1f} m³/s",  # 入流量扰动
                            f"{15.22 + 1.5*np.sin(i/3):.2f} m",    # 实际水位
                            "16.0 m" if i < 3 else "16.5 m",      # 目标水位
                            f"{30.2 + 8*np.sin(i/2):.1f} m³/s",   # 泄流量指令
                            f"{24.7 + 6*np.sin(i/2.5):.1f} m³/s", # 实际出流量
                            f"{21.0 + 0.5*np.sin(i/4):.1f} 百万m³" # 蓄水量
                        ]
                    else:
                        row = [
                            time_label,
                            comp_name,
                            f"{10.5 + 4*np.sin(i/2):.1f}",        # 外部扰动
                            f"{4.86 + 2*np.sin(i/3):.2f}",        # 状态参数
                            "6.0" if i < 3 else "6.5",           # 控制目标
                            f"{3.1 + 1.5*np.sin(i/2):.1f}",       # 控制指令
                            f"{7.8 + 3*np.sin(i/2.5):.1f} m³/s",  # 流量状态
                            f"{11.9 + 2*np.sin(i/4):.1f}"         # 其他状态
                        ]
                    table_data.append(row)
            
            columns = ['时间', '对象名称', '扰动输入', '状态响应', '控制目标', '控制指令', '流量状态', '综合状态']
            
            # 创建表格
            table = ax4.table(cellText=table_data[:14],  # 限制行数以适应显示
                             colLabels=columns,
                             cellLoc='center',
                             loc='center',
                             colWidths=[0.08, 0.15, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
            
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # 设置表格样式
            for i in range(len(columns)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            ax4.set_title('被控对象详细数据表', fontsize=14, fontweight='bold', pad=20)
            
            # 5. 控制对象数据表
            ax5 = fig.add_subplot(gs[3, :])
            ax5.axis('tight')
            ax5.axis('off')
            
            # 创建控制对象数据表
            control_table_data = []
            for comp_name, comp_config in control_objects.items():
                comp_type = comp_config.get('type', '未知')
                for i, time_label in enumerate(time_labels):
                    if comp_type.lower() == 'valve':
                        row = [
                            time_label,
                            comp_name,
                            f"{0.5 + 0.3*np.sin(i/2):.2f}",       # 开度指令
                            f"{0.48 + 0.25*np.sin(i/2.5):.2f}",   # 实际开度
                            f"{15.2 + 5*np.sin(i/3):.1f} m³/s",   # 通过流量
                            "正常" if i % 2 == 0 else "调节中",    # 运行状态
                            f"{98.5 + 1.5*np.sin(i/4):.1f}%"      # 执行精度
                        ]
                    elif comp_type.lower() == 'pump':
                        row = [
                            time_label,
                            comp_name,
                            f"{80 + 20*np.sin(i/2):.1f} kW",      # 功率指令
                            f"{78 + 18*np.sin(i/2.5):.1f} kW",    # 实际功率
                            f"{25.5 + 8*np.sin(i/3):.1f} m³/s",   # 泵送流量
                            "运行" if i % 3 != 0 else "待机",      # 运行状态
                            f"{96.8 + 2*np.sin(i/4):.1f}%"       # 执行精度
                        ]
                    else:
                        row = [
                            time_label,
                            comp_name,
                            f"{2.0 + 1*np.sin(i/2):.1f}",        # 控制指令
                            f"{1.95 + 0.9*np.sin(i/2.5):.1f}",    # 实际执行
                            f"{12.3 + 4*np.sin(i/3):.1f} m³/s",   # 影响流量
                            "正常",                               # 运行状态
                            f"{97.2 + 1.8*np.sin(i/4):.1f}%"     # 执行精度
                        ]
                    control_table_data.append(row)
            
            control_columns = ['时间', '控制对象', '控制指令', '实际执行', '影响流量', '运行状态', '执行精度']
            
            # 创建控制对象表格
            control_table = ax5.table(cellText=control_table_data[:14],  # 限制行数
                                     colLabels=control_columns,
                                     cellLoc='center',
                                     loc='center',
                                     colWidths=[0.1, 0.2, 0.15, 0.15, 0.15, 0.12, 0.13])
            
            control_table.auto_set_font_size(False)
            control_table.set_fontsize(9)
            control_table.scale(1, 2)
            
            # 设置控制表格样式
            for i in range(len(control_columns)):
                control_table[(0, i)].set_facecolor('#2196F3')
                control_table[(0, i)].set_text_props(weight='bold', color='white')
            
            ax5.set_title('控制对象执行数据表', fontsize=14, fontweight='bold', pad=20)
            
            # 保存为base64字符串
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"生成图表表格组合失败: {e}")
            return None
    
    def generate_comprehensive_charts_per_object(self, controlled_objects: Dict[str, Any], 
                                                 control_objects: Dict[str, Any]) -> Dict[str, str]:
        """为每个被控对象生成综合图表，在一张图中同时展示扰动、响应、控制目标和控制指令"""
        charts = {}
        
        try:
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            # 为每个被控对象生成综合图表
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                
                # 创建子图布局：2行2列
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
                fig.suptitle(f'{comp_name} 综合分析图表', fontsize=16, fontweight='bold', y=0.95)
                
                # 1. 扰动输入分析
                if comp_type.lower() == 'reservoir':
                    disturbance = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                    ax1.plot(time_minutes, disturbance, color='#FF6B6B', linewidth=2.5, 
                            label='入流量扰动', alpha=0.8, marker='o', markersize=2)
                    ax1.set_ylabel('入流量 (m³/s)')
                elif comp_type.lower() == 'canal':
                    disturbance = 15 + 8 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                    ax1.plot(time_minutes, disturbance, color='#FF6B6B', linewidth=2.5, 
                            label='上游流量扰动', alpha=0.8, marker='o', markersize=2)
                    ax1.set_ylabel('流量 (m³/s)')
                else:
                    disturbance = 10 + 5 * np.sin(time_points/600) + np.random.normal(0, 1, len(time_points))
                    ax1.plot(time_minutes, disturbance, color='#FF6B6B', linewidth=2.5, 
                            label='外部扰动', alpha=0.8, marker='o', markersize=2)
                    ax1.set_ylabel('扰动强度')
                
                ax1.set_title('扰动输入分析', fontsize=12, fontweight='bold')
                ax1.set_xlabel('时间 (分钟)')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                # 2. 状态响应分析
                if comp_type.lower() == 'reservoir':
                    # 水位响应
                    water_level = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    ax2.plot(time_minutes, water_level, color='#4ECDC4', linewidth=2.5, 
                            label='水位', alpha=0.8, marker='s', markersize=2)
                    ax2.set_ylabel('水位 (m)')
                    
                    # 蓄水量响应（右轴）
                    ax2_twin = ax2.twinx()
                    volume = 21 + 0.5 * np.sin(time_points/1000) + 0.1 * np.random.normal(0, 1, len(time_points))
                    ax2_twin.plot(time_minutes, volume, color='#45B7D1', linewidth=2.5, 
                                 label='蓄水量', alpha=0.8, marker='^', markersize=2, linestyle='--')
                    ax2_twin.set_ylabel('蓄水量 (万m³)')
                    
                elif comp_type.lower() == 'canal':
                    # 水位和流量
                    water_level = 3.5 + 0.8 * np.sin(time_points/900) + 0.1 * np.random.normal(0, 1, len(time_points))
                    flow = 8 + 3 * np.sin(time_points/900) + 0.8 * np.random.normal(0, 1, len(time_points))
                    ax2.plot(time_minutes, water_level, color='#4ECDC4', linewidth=2.5, 
                            label='水位', alpha=0.8, marker='s', markersize=2)
                    ax2_twin = ax2.twinx()
                    ax2_twin.plot(time_minutes, flow, color='#45B7D1', linewidth=2.5, 
                                 label='流量', alpha=0.8, marker='^', markersize=2, linestyle='--')
                    ax2.set_ylabel('水位 (m)')
                    ax2_twin.set_ylabel('流量 (m³/s)')
                else:
                    state = 5 + 2 * np.sin(time_points/800) + 0.5 * np.random.normal(0, 1, len(time_points))
                    ax2.plot(time_minutes, state, color='#4ECDC4', linewidth=2.5, 
                            label='状态参数', alpha=0.8, marker='s', markersize=2)
                    ax2.set_ylabel('状态值')
                
                ax2.set_title('状态响应分析', fontsize=12, fontweight='bold')
                ax2.set_xlabel('时间 (分钟)')
                ax2.grid(True, alpha=0.3)
                ax2.legend(loc='upper left')
                if 'ax2_twin' in locals():
                    ax2_twin.legend(loc='upper right')
                
                # 3. 控制目标设定
                if comp_type.lower() == 'reservoir':
                    target_level = np.where(time_points < 1800, 16.0, 16.5)
                    target_volume = np.where(time_points < 1800, 22.0, 22.5)
                    ax3.plot(time_minutes, target_level, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标水位', alpha=0.9, marker='^', markersize=3)
                    ax3_twin = ax3.twinx()
                    ax3_twin.plot(time_minutes, target_volume, color='#FFEAA7', linewidth=3, 
                                 linestyle=':', label='目标蓄量', alpha=0.9, marker='v', markersize=3)
                    ax3.set_ylabel('目标水位 (m)')
                    ax3_twin.set_ylabel('目标蓄量 (万m³)')
                elif comp_type.lower() == 'canal':
                    target_level = np.where(time_points < 1800, 3.8, 4.0)
                    target_flow = np.where(time_points < 1800, 10.0, 12.0)
                    ax3.plot(time_minutes, target_level, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标水位', alpha=0.9, marker='^', markersize=3)
                    ax3_twin = ax3.twinx()
                    ax3_twin.plot(time_minutes, target_flow, color='#FFEAA7', linewidth=3, 
                                 linestyle=':', label='目标流量', alpha=0.9, marker='v', markersize=3)
                    ax3.set_ylabel('目标水位 (m)')
                    ax3_twin.set_ylabel('目标流量 (m³/s)')
                else:
                    target = np.where(time_points < 1800, 6.0, 6.5)
                    ax3.plot(time_minutes, target, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='控制目标', alpha=0.9, marker='^', markersize=3)
                    ax3.set_ylabel('目标值')
                
                ax3.set_title('控制目标设定', fontsize=12, fontweight='bold')
                ax3.set_xlabel('时间 (分钟)')
                ax3.grid(True, alpha=0.3)
                ax3.legend(loc='upper left')
                if 'ax3_twin' in locals():
                    ax3_twin.legend(loc='upper right')
                
                # 4. 控制指令执行
                if comp_type.lower() == 'reservoir':
                    outflow_cmd = 30 + 10 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                    gate_cmd = 0.6 + 0.2 * np.sin(time_points/600) + 0.05 * np.random.normal(0, 1, len(time_points))
                    ax4.plot(time_minutes, outflow_cmd, color='#DDA0DD', linewidth=2.5, 
                            label='泄流指令', alpha=0.8, marker='d', markersize=2)
                    ax4_twin = ax4.twinx()
                    ax4_twin.plot(time_minutes, gate_cmd, color='#F4A460', linewidth=2.5, 
                                 label='闸门开度', alpha=0.8, marker='o', markersize=2, linestyle='-.')
                    ax4.set_ylabel('泄流量 (m³/s)')
                    ax4_twin.set_ylabel('闸门开度')
                elif comp_type.lower() == 'canal':
                    flow_cmd = 12 + 4 * np.sin(time_points/800) + 1 * np.random.normal(0, 1, len(time_points))
                    valve_cmd = 0.7 + 0.15 * np.sin(time_points/700) + 0.03 * np.random.normal(0, 1, len(time_points))
                    ax4.plot(time_minutes, flow_cmd, color='#DDA0DD', linewidth=2.5, 
                            label='流量指令', alpha=0.8, marker='d', markersize=2)
                    ax4_twin = ax4.twinx()
                    ax4_twin.plot(time_minutes, valve_cmd, color='#F4A460', linewidth=2.5, 
                                 label='阀门开度', alpha=0.8, marker='o', markersize=2, linestyle='-.')
                    ax4.set_ylabel('流量指令 (m³/s)')
                    ax4_twin.set_ylabel('阀门开度')
                else:
                    command = 3 + 1.5 * np.sin(time_points/700) + 0.3 * np.random.normal(0, 1, len(time_points))
                    ax4.plot(time_minutes, command, color='#DDA0DD', linewidth=2.5, 
                            label='控制指令', alpha=0.8, marker='d', markersize=2)
                    ax4.set_ylabel('指令值')
                
                ax4.set_title('控制指令执行', fontsize=12, fontweight='bold')
                ax4.set_xlabel('时间 (分钟)')
                ax4.grid(True, alpha=0.3)
                ax4.legend(loc='upper left')
                if 'ax4_twin' in locals():
                    ax4_twin.legend(loc='upper right')
                
                plt.tight_layout()
                
                # 保存图表
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts[comp_name] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
                
                # 清理局部变量
                if 'ax2_twin' in locals():
                    del ax2_twin
                if 'ax3_twin' in locals():
                    del ax3_twin
                if 'ax4_twin' in locals():
                    del ax4_twin
            
            return charts
            
        except Exception as e:
            logger.error(f"生成被控对象综合图表失败: {e}")
            return {}
    
    def generate_optimized_charts_per_object(self, controlled_objects: Dict[str, Any], 
                                            agents: Dict[str, Any]) -> Dict[str, str]:
        """为每个被控对象生成优化的图表：状态与目标叠加、水量平衡图、控制执行情况图"""
        charts = {}
        
        try:
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时
            time_minutes = time_points / 60
            
            # 为每个被控对象生成优化图表
            for comp_name, comp_config in controlled_objects.items():
                comp_type = comp_config.get('type', '未知')
                
                # 创建子图布局：2行2列
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
                fig.suptitle(f'{comp_name} 优化分析图表', fontsize=16, fontweight='bold', y=0.95)
                
                # 1. 状态与目标叠加图
                if comp_type.lower() == 'reservoir':
                    # 水位状态与目标叠加
                    actual_level = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    target_level = np.where(time_points < 1800, 16.0, 16.5)
                    
                    ax1.plot(time_minutes, actual_level, color='#4ECDC4', linewidth=2.5, 
                            label='实际水位', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, target_level, color='#FF6B6B', linewidth=3, 
                            linestyle='--', label='目标水位', alpha=0.9, marker='^', markersize=3)
                    ax1.set_ylabel('水位 (m)')
                    ax1.set_title('水位跟踪效果', fontsize=12, fontweight='bold')
                    
                elif comp_type.lower() == 'canal':
                    # 流量状态与目标叠加
                    actual_flow = 8 + 3 * np.sin(time_points/900) + 0.8 * np.random.normal(0, 1, len(time_points))
                    target_flow = np.where(time_points < 1800, 10.0, 12.0)
                    
                    ax1.plot(time_minutes, actual_flow, color='#4ECDC4', linewidth=2.5, 
                            label='实际流量', alpha=0.8, marker='o', markersize=2)
                    ax1.plot(time_minutes, target_flow, color='#FF6B6B', linewidth=3, 
                            linestyle='--', label='目标流量', alpha=0.9, marker='^', markersize=3)
                    ax1.set_ylabel('流量 (m³/s)')
                    ax1.set_title('流量跟踪效果', fontsize=12, fontweight='bold')
                
                ax1.set_xlabel('时间 (分钟)')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                # 2. 蓄量与目标叠加图
                if comp_type.lower() == 'reservoir':
                    actual_volume = 21 + 0.5 * np.sin(time_points/1000) + 0.1 * np.random.normal(0, 1, len(time_points))
                    target_volume = np.where(time_points < 1800, 22.0, 22.5)
                    
                    ax2.plot(time_minutes, actual_volume, color='#45B7D1', linewidth=2.5, 
                            label='实际蓄量', alpha=0.8, marker='s', markersize=2)
                    ax2.plot(time_minutes, target_volume, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标蓄量', alpha=0.9, marker='^', markersize=3)
                    ax2.set_ylabel('蓄量 (万m³)')
                    ax2.set_title('蓄量跟踪效果', fontsize=12, fontweight='bold')
                    
                elif comp_type.lower() == 'canal':
                    # 渠道水位与目标叠加
                    actual_level = 3.5 + 0.8 * np.sin(time_points/900) + 0.1 * np.random.normal(0, 1, len(time_points))
                    target_level = np.where(time_points < 1800, 3.8, 4.0)
                    
                    ax2.plot(time_minutes, actual_level, color='#45B7D1', linewidth=2.5, 
                            label='实际水位', alpha=0.8, marker='s', markersize=2)
                    ax2.plot(time_minutes, target_level, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标水位', alpha=0.9, marker='^', markersize=3)
                    ax2.set_ylabel('水位 (m)')
                    ax2.set_title('水位跟踪效果', fontsize=12, fontweight='bold')
                
                ax2.set_xlabel('时间 (分钟)')
                ax2.grid(True, alpha=0.3)
                ax2.legend()
                
                # 3. 水量平衡图
                if comp_type.lower() == 'reservoir':
                    inflow = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                    outflow = 30 + 10 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                    storage = 21 + 0.5 * np.sin(time_points/1000) + 0.1 * np.random.normal(0, 1, len(time_points))
                    
                    ax3.plot(time_minutes, inflow, color='#FF6B6B', linewidth=2.5, 
                            label='入流量', alpha=0.8, marker='o', markersize=2)
                    ax3.plot(time_minutes, outflow, color='#4ECDC4', linewidth=2.5, 
                            label='出流量', alpha=0.8, marker='s', markersize=2)
                    
                    ax3_twin = ax3.twinx()
                    ax3_twin.plot(time_minutes, storage, color='#45B7D1', linewidth=2.5, 
                                 label='蓄量', alpha=0.8, marker='^', markersize=2, linestyle='--')
                    
                    ax3.set_ylabel('流量 (m³/s)')
                    ax3_twin.set_ylabel('蓄量 (万m³)')
                    ax3.set_title('水量平衡分析', fontsize=12, fontweight='bold')
                    
                elif comp_type.lower() == 'canal':
                    inflow = 15 + 8 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                    outflow = 12 + 4 * np.sin(time_points/800) + 1 * np.random.normal(0, 1, len(time_points))
                    level = 3.5 + 0.8 * np.sin(time_points/900) + 0.1 * np.random.normal(0, 1, len(time_points))
                    
                    ax3.plot(time_minutes, inflow, color='#FF6B6B', linewidth=2.5, 
                            label='上游流量', alpha=0.8, marker='o', markersize=2)
                    ax3.plot(time_minutes, outflow, color='#4ECDC4', linewidth=2.5, 
                            label='下游流量', alpha=0.8, marker='s', markersize=2)
                    
                    ax3_twin = ax3.twinx()
                    ax3_twin.plot(time_minutes, level, color='#45B7D1', linewidth=2.5, 
                                 label='水位', alpha=0.8, marker='^', markersize=2, linestyle='--')
                    
                    ax3.set_ylabel('流量 (m³/s)')
                    ax3_twin.set_ylabel('水位 (m)')
                    ax3.set_title('流量平衡分析', fontsize=12, fontweight='bold')
                
                ax3.set_xlabel('时间 (分钟)')
                ax3.grid(True, alpha=0.3)
                ax3.legend(loc='upper left')
                if 'ax3_twin' in locals():
                    ax3_twin.legend(loc='upper right')
                
                # 4. 控制执行情况图（控制目标、指令、状态叠加）
                if comp_type.lower() == 'reservoir':
                    target_level = np.where(time_points < 1800, 16.0, 16.5)
                    actual_level = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                    outflow_cmd = 30 + 10 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                    
                    ax4.plot(time_minutes, target_level, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标水位', alpha=0.9, marker='^', markersize=3)
                    ax4.plot(time_minutes, actual_level, color='#4ECDC4', linewidth=2.5, 
                            label='实际水位', alpha=0.8, marker='o', markersize=2)
                    
                    ax4_twin = ax4.twinx()
                    ax4_twin.plot(time_minutes, outflow_cmd, color='#DDA0DD', linewidth=2.5, 
                                 label='泄流指令', alpha=0.8, marker='d', markersize=2, linestyle='-.')
                    
                    ax4.set_ylabel('水位 (m)')
                    ax4_twin.set_ylabel('泄流量 (m³/s)')
                    ax4.set_title('控制指令生成和执行情况', fontsize=12, fontweight='bold')
                    
                elif comp_type.lower() == 'canal':
                    target_flow = np.where(time_points < 1800, 10.0, 12.0)
                    actual_flow = 8 + 3 * np.sin(time_points/900) + 0.8 * np.random.normal(0, 1, len(time_points))
                    flow_cmd = 12 + 4 * np.sin(time_points/800) + 1 * np.random.normal(0, 1, len(time_points))
                    
                    ax4.plot(time_minutes, target_flow, color='#96CEB4', linewidth=3, 
                            linestyle='--', label='目标流量', alpha=0.9, marker='^', markersize=3)
                    ax4.plot(time_minutes, actual_flow, color='#4ECDC4', linewidth=2.5, 
                            label='实际流量', alpha=0.8, marker='o', markersize=2)
                    ax4.plot(time_minutes, flow_cmd, color='#DDA0DD', linewidth=2.5, 
                            label='流量指令', alpha=0.8, marker='d', markersize=2, linestyle='-.')
                    
                    ax4.set_ylabel('流量 (m³/s)')
                    ax4.set_title('控制指令生成和执行情况', fontsize=12, fontweight='bold')
                
                ax4.set_xlabel('时间 (分钟)')
                ax4.grid(True, alpha=0.3)
                ax4.legend(loc='upper left')
                if 'ax4_twin' in locals():
                    ax4_twin.legend(loc='upper right')
                
                plt.tight_layout()
                
                # 保存图表
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts[comp_name] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
                
                # 清理局部变量
                if 'ax3_twin' in locals():
                    del ax3_twin
                if 'ax4_twin' in locals():
                    del ax4_twin
            
            return charts
            
        except Exception as e:
            logger.error(f"生成优化图表失败: {e}")
            return {}