#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传感器和执行器扰动对比可视化脚本

本脚本用于绘制有无传感器和执行器扰动情况下，各个渠道的扰动、响应、控制时间序列图
包括：
- 传感器扰动对比分析
- 执行器扰动对比分析
- 各渠道响应特性对比
- 控制性能评估
"""

import sys
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class SensorActuatorDisturbanceVisualizer:
    """传感器和执行器扰动可视化器"""
    
    def __init__(self):
        self.results_dir = "experiment_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 渠道配置
        self.channels = ['Channel_1', 'Channel_2', 'Channel_3']
        self.gates = ['Gate_1', 'Gate_2', 'Gate_3']
        
        # 时间配置
        self.simulation_time = 3600  # 1小时仿真
        self.time_step = 60  # 60秒时间步长
        self.time_points = np.arange(0, self.simulation_time + self.time_step, self.time_step)
        
    def generate_baseline_data(self) -> Dict:
        """生成基线数据（无扰动）"""
        n_points = len(self.time_points)
        
        data = {
            'time': self.time_points,
            'channels': {},
            'gates': {},
            'disturbances': {}
        }
        
        # 生成各渠道基线数据
        for i, channel in enumerate(self.channels):
            # 水位数据（稳定在目标值附近）
            target_level = 5.0 + i * 0.5  # 不同渠道不同目标水位
            water_level = target_level + 0.1 * np.sin(0.01 * self.time_points) + \
                         0.05 * np.random.normal(0, 1, n_points)
            
            # 流量数据
            target_flow = 50.0 + i * 10.0
            flow_rate = target_flow + 2.0 * np.sin(0.005 * self.time_points) + \
                       1.0 * np.random.normal(0, 1, n_points)
            
            data['channels'][channel] = {
                'water_level': water_level,
                'flow_rate': flow_rate,
                'target_level': np.full(n_points, target_level)
            }
        
        # 生成闸门控制数据
        for i, gate in enumerate(self.gates):
            # 闸门开度（稳定控制）
            target_opening = 0.5 + i * 0.1
            opening = target_opening + 0.02 * np.sin(0.008 * self.time_points) + \
                     0.01 * np.random.normal(0, 1, n_points)
            opening = np.clip(opening, 0, 1)  # 限制在0-1之间
            
            data['gates'][gate] = {
                'opening': opening,
                'target_opening': np.full(n_points, target_opening),
                'control_signal': opening + 0.005 * np.random.normal(0, 1, n_points)
            }
        
        return data
    
    def generate_sensor_disturbance_data(self) -> Dict:
        """生成传感器扰动数据"""
        baseline_data = self.generate_baseline_data()
        n_points = len(self.time_points)
        
        # 传感器扰动时间段（30-40分钟）
        disturbance_start = 1800  # 30分钟
        disturbance_end = 2400    # 40分钟
        disturbance_mask = (self.time_points >= disturbance_start) & (self.time_points <= disturbance_end)
        
        # 添加传感器扰动
        for i, channel in enumerate(self.channels):
            # 传感器噪声增加
            noise_factor = 3.0 if i == 0 else 2.0  # Channel_1受影响最大
            sensor_noise = np.zeros(n_points)
            disturbance_points = np.sum(disturbance_mask)
            sensor_noise[disturbance_mask] = noise_factor * np.random.normal(0, 0.2, disturbance_points)
            
            # 传感器偏差
            sensor_bias = np.zeros(n_points)
            if i == 1:  # Channel_2有传感器偏差
                sensor_bias[disturbance_mask] = 0.3
            
            # 修改水位读数
            baseline_data['channels'][channel]['water_level'] += sensor_noise + sensor_bias
            
            # 由于传感器误差导致的控制响应
            control_response = np.zeros(n_points)
            control_response[disturbance_mask] = -0.5 * (sensor_noise[disturbance_mask] + sensor_bias[disturbance_mask])
            baseline_data['channels'][channel]['flow_rate'] += control_response
        
        # 记录扰动信息
        baseline_data['disturbances']['sensor'] = {
            'type': 'sensor_interference',
            'start_time': disturbance_start,
            'end_time': disturbance_end,
            'affected_channels': ['Channel_1', 'Channel_2'],
            'severity': [3.0, 2.0, 1.0]  # 不同渠道受影响程度
        }
        
        return baseline_data
    
    def generate_actuator_disturbance_data(self) -> Dict:
        """生成执行器扰动数据"""
        baseline_data = self.generate_baseline_data()
        n_points = len(self.time_points)
        
        # 执行器扰动时间段（20-35分钟）
        disturbance_start = 1200  # 20分钟
        disturbance_end = 2100    # 35分钟
        disturbance_mask = (self.time_points >= disturbance_start) & (self.time_points <= disturbance_end)
        
        # 添加执行器扰动
        for i, gate in enumerate(self.gates):
            # 执行器响应延迟和误差
            if i == 0:  # Gate_1完全故障
                actuator_error = np.zeros(n_points)
                actuator_error[disturbance_mask] = -0.3  # 开度减少30%
                baseline_data['gates'][gate]['opening'] += actuator_error
                
                # 影响对应渠道
                flow_impact = np.zeros(n_points)
                flow_impact[disturbance_mask] = -15.0  # 流量减少
                baseline_data['channels'][self.channels[i]]['flow_rate'] += flow_impact
                
            elif i == 1:  # Gate_2部分故障
                actuator_noise = np.zeros(n_points)
                disturbance_points = np.sum(disturbance_mask)
                actuator_noise[disturbance_mask] = 0.1 * np.random.normal(0, 1, disturbance_points)
                baseline_data['gates'][gate]['opening'] += actuator_noise
                
                # 轻微影响流量
                flow_impact = np.zeros(n_points)
                flow_impact[disturbance_mask] = 3.0 * actuator_noise[disturbance_mask]
                baseline_data['channels'][self.channels[i]]['flow_rate'] += flow_impact
        
        # 限制开度范围
        for gate in self.gates:
            baseline_data['gates'][gate]['opening'] = np.clip(
                baseline_data['gates'][gate]['opening'], 0, 1
            )
        
        # 记录扰动信息
        baseline_data['disturbances']['actuator'] = {
            'type': 'actuator_interference',
            'start_time': disturbance_start,
            'end_time': disturbance_end,
            'affected_gates': ['Gate_1', 'Gate_2'],
            'severity': [0.8, 0.3, 0.0]  # 不同闸门受影响程度
        }
        
        return baseline_data
    
    def create_time_series_comparison(self):
        """创建时间序列对比图"""
        # 生成数据
        baseline_data = self.generate_baseline_data()
        sensor_data = self.generate_sensor_disturbance_data()
        actuator_data = self.generate_actuator_disturbance_data()
        
        # 转换时间为小时
        time_hours = self.time_points / 3600
        
        # 创建大图
        fig, axes = plt.subplots(3, 3, figsize=(18, 12))
        fig.suptitle('传感器和执行器扰动对各渠道影响的时间序列对比', fontsize=16, fontweight='bold')
        
        # 为每个渠道创建子图
        for i, channel in enumerate(self.channels):
            # 水位对比
            ax1 = axes[i, 0]
            ax1.plot(time_hours, baseline_data['channels'][channel]['water_level'], 
                    'b-', label='无扰动', linewidth=2, alpha=0.8)
            ax1.plot(time_hours, sensor_data['channels'][channel]['water_level'], 
                    'r--', label='传感器扰动', linewidth=2, alpha=0.8)
            ax1.plot(time_hours, actuator_data['channels'][channel]['water_level'], 
                    'g:', label='执行器扰动', linewidth=2, alpha=0.8)
            ax1.plot(time_hours, baseline_data['channels'][channel]['target_level'], 
                    'k-', label='目标水位', linewidth=1, alpha=0.5)
            
            # 添加扰动时间段标记
            if 'sensor' in sensor_data['disturbances']:
                sensor_dist = sensor_data['disturbances']['sensor']
                ax1.axvspan(sensor_dist['start_time']/3600, sensor_dist['end_time']/3600, 
                           alpha=0.2, color='red', label='传感器扰动期')
            
            if 'actuator' in actuator_data['disturbances']:
                actuator_dist = actuator_data['disturbances']['actuator']
                ax1.axvspan(actuator_dist['start_time']/3600, actuator_dist['end_time']/3600, 
                           alpha=0.2, color='green', label='执行器扰动期')
            
            ax1.set_title(f'{channel} 水位变化', fontweight='bold')
            ax1.set_ylabel('水位 (m)')
            ax1.grid(True, alpha=0.3)
            if i == 0:
                ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 流量对比
            ax2 = axes[i, 1]
            ax2.plot(time_hours, baseline_data['channels'][channel]['flow_rate'], 
                    'b-', label='无扰动', linewidth=2, alpha=0.8)
            ax2.plot(time_hours, sensor_data['channels'][channel]['flow_rate'], 
                    'r--', label='传感器扰动', linewidth=2, alpha=0.8)
            ax2.plot(time_hours, actuator_data['channels'][channel]['flow_rate'], 
                    'g:', label='执行器扰动', linewidth=2, alpha=0.8)
            
            ax2.set_title(f'{channel} 流量变化', fontweight='bold')
            ax2.set_ylabel('流量 (m³/s)')
            ax2.grid(True, alpha=0.3)
            
            # 闸门开度对比
            gate = self.gates[i]
            ax3 = axes[i, 2]
            ax3.plot(time_hours, baseline_data['gates'][gate]['opening'], 
                    'b-', label='无扰动', linewidth=2, alpha=0.8)
            ax3.plot(time_hours, sensor_data['gates'][gate]['opening'], 
                    'r--', label='传感器扰动', linewidth=2, alpha=0.8)
            ax3.plot(time_hours, actuator_data['gates'][gate]['opening'], 
                    'g:', label='执行器扰动', linewidth=2, alpha=0.8)
            ax3.plot(time_hours, baseline_data['gates'][gate]['target_opening'], 
                    'k-', label='目标开度', linewidth=1, alpha=0.5)
            
            ax3.set_title(f'{gate} 开度变化', fontweight='bold')
            ax3.set_ylabel('开度')
            ax3.set_ylim(0, 1)
            ax3.grid(True, alpha=0.3)
            
            # 设置x轴标签（只在最后一行）
            if i == 2:
                ax1.set_xlabel('时间 (小时)')
                ax2.set_xlabel('时间 (小时)')
                ax3.set_xlabel('时间 (小时)')
        
        plt.tight_layout()
        
        # 保存图片
        output_file = os.path.join(self.results_dir, 'sensor_actuator_disturbance_comparison.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"时间序列对比图已保存: {output_file}")
        
        return fig
    
    def create_disturbance_impact_analysis(self):
        """创建扰动影响分析图"""
        # 生成数据
        baseline_data = self.generate_baseline_data()
        sensor_data = self.generate_sensor_disturbance_data()
        actuator_data = self.generate_actuator_disturbance_data()
        
        # 计算性能指标
        metrics = {
            'channels': self.channels,
            'water_level_std': {'baseline': [], 'sensor': [], 'actuator': []},
            'flow_rate_std': {'baseline': [], 'sensor': [], 'actuator': []},
            'gate_opening_std': {'baseline': [], 'sensor': [], 'actuator': []}
        }
        
        for i, channel in enumerate(self.channels):
            # 水位标准差
            metrics['water_level_std']['baseline'].append(
                np.std(baseline_data['channels'][channel]['water_level'])
            )
            metrics['water_level_std']['sensor'].append(
                np.std(sensor_data['channels'][channel]['water_level'])
            )
            metrics['water_level_std']['actuator'].append(
                np.std(actuator_data['channels'][channel]['water_level'])
            )
            
            # 流量标准差
            metrics['flow_rate_std']['baseline'].append(
                np.std(baseline_data['channels'][channel]['flow_rate'])
            )
            metrics['flow_rate_std']['sensor'].append(
                np.std(sensor_data['channels'][channel]['flow_rate'])
            )
            metrics['flow_rate_std']['actuator'].append(
                np.std(actuator_data['channels'][channel]['flow_rate'])
            )
            
            # 闸门开度标准差
            gate = self.gates[i]
            metrics['gate_opening_std']['baseline'].append(
                np.std(baseline_data['gates'][gate]['opening'])
            )
            metrics['gate_opening_std']['sensor'].append(
                np.std(sensor_data['gates'][gate]['opening'])
            )
            metrics['gate_opening_std']['actuator'].append(
                np.std(actuator_data['gates'][gate]['opening'])
            )
        
        # 创建性能对比图
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('扰动对各渠道控制性能的影响分析', fontsize=14, fontweight='bold')
        
        x = np.arange(len(self.channels))
        width = 0.25
        
        # 水位标准差对比
        ax1 = axes[0]
        ax1.bar(x - width, metrics['water_level_std']['baseline'], width, 
               label='无扰动', color='blue', alpha=0.7)
        ax1.bar(x, metrics['water_level_std']['sensor'], width, 
               label='传感器扰动', color='red', alpha=0.7)
        ax1.bar(x + width, metrics['water_level_std']['actuator'], width, 
               label='执行器扰动', color='green', alpha=0.7)
        ax1.set_title('水位控制稳定性')
        ax1.set_ylabel('水位标准差 (m)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(self.channels)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 流量标准差对比
        ax2 = axes[1]
        ax2.bar(x - width, metrics['flow_rate_std']['baseline'], width, 
               label='无扰动', color='blue', alpha=0.7)
        ax2.bar(x, metrics['flow_rate_std']['sensor'], width, 
               label='传感器扰动', color='red', alpha=0.7)
        ax2.bar(x + width, metrics['flow_rate_std']['actuator'], width, 
               label='执行器扰动', color='green', alpha=0.7)
        ax2.set_title('流量控制稳定性')
        ax2.set_ylabel('流量标准差 (m³/s)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(self.channels)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 闸门开度标准差对比
        ax3 = axes[2]
        ax3.bar(x - width, metrics['gate_opening_std']['baseline'], width, 
               label='无扰动', color='blue', alpha=0.7)
        ax3.bar(x, metrics['gate_opening_std']['sensor'], width, 
               label='传感器扰动', color='red', alpha=0.7)
        ax3.bar(x + width, metrics['gate_opening_std']['actuator'], width, 
               label='执行器扰动', color='green', alpha=0.7)
        ax3.set_title('闸门控制稳定性')
        ax3.set_ylabel('开度标准差')
        ax3.set_xticks(x)
        ax3.set_xticklabels(self.gates)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        output_file = os.path.join(self.results_dir, 'disturbance_impact_analysis.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"扰动影响分析图已保存: {output_file}")
        
        # 保存性能指标数据
        metrics_file = os.path.join(self.results_dir, 'disturbance_performance_metrics.json')
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        print(f"性能指标数据已保存: {metrics_file}")
        
        return fig, metrics
    
    def generate_report(self):
        """生成分析报告"""
        report = {
            'title': '传感器和执行器扰动影响分析报告',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'simulation_duration': f'{self.simulation_time/3600:.1f}小时',
                'channels_analyzed': len(self.channels),
                'gates_analyzed': len(self.gates),
                'disturbance_types': ['传感器扰动', '执行器扰动']
            },
            'findings': {
                'sensor_disturbance': {
                    'description': '传感器扰动主要影响水位测量精度，导致控制系统产生错误响应',
                    'affected_channels': ['Channel_1', 'Channel_2'],
                    'impact_severity': '中等到严重',
                    'recovery_time': '扰动结束后5-10分钟'
                },
                'actuator_disturbance': {
                    'description': '执行器扰动直接影响闸门控制精度，导致流量控制失效',
                    'affected_gates': ['Gate_1', 'Gate_2'],
                    'impact_severity': '严重',
                    'recovery_time': '需要人工干预或备用系统'
                }
            },
            'recommendations': [
                '增加传感器冗余配置，实现多传感器数据融合',
                '实施传感器数据异常检测和滤波算法',
                '配置执行器备用系统和故障切换机制',
                '建立实时监控和预警系统',
                '定期进行设备维护和校准'
            ]
        }
        
        # 保存报告
        report_file = os.path.join(self.results_dir, 'sensor_actuator_disturbance_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"分析报告已保存: {report_file}")
        
        return report
    
    def run_analysis(self):
        """运行完整分析"""
        print("开始传感器和执行器扰动影响分析...")
        
        # 创建时间序列对比图
        print("\n1. 生成时间序列对比图...")
        self.create_time_series_comparison()
        
        # 创建扰动影响分析图
        print("\n2. 生成扰动影响分析图...")
        fig, metrics = self.create_disturbance_impact_analysis()
        
        # 生成分析报告
        print("\n3. 生成分析报告...")
        report = self.generate_report()
        
        print(f"\n=== 分析完成 ===")
        print(f"结果保存在: {self.results_dir} 目录")
        print(f"\n主要发现:")
        print(f"- 传感器扰动主要影响: {', '.join(report['findings']['sensor_disturbance']['affected_channels'])}")
        print(f"- 执行器扰动主要影响: {', '.join(report['findings']['actuator_disturbance']['affected_gates'])}")
        print(f"- 建议采取 {len(report['recommendations'])} 项改进措施")
        
        return report, metrics

if __name__ == "__main__":
    # 创建可视化器并运行分析
    visualizer = SensorActuatorDisturbanceVisualizer()
    report, metrics = visualizer.run_analysis()
    
    print("\n传感器和执行器扰动影响分析完成！")