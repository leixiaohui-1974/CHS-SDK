#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数辨识过程分析脚本
分析积分时滞参数在辨识过程中的变化
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def generate_identification_data():
    """
    生成参数辨识过程的模拟数据
    """
    # 仿真参数
    time_steps = 500
    dt = 0.1
    time = np.arange(0, time_steps * dt, dt)
    
    # 真实参数值
    true_integral_coeff = [0.15, 1.8, 0.12]  # 三个渠道的真实积分系数
    true_time_delay = [2.5, 3.0, 2.8]  # 三个渠道的真实时滞
    
    # 初始估计值（带有误差）
    initial_integral_coeff = [0.1, 2.0, 0.1]  # 初始积分系数估计
    initial_time_delay = [2.0, 2.5, 2.5]  # 初始时滞估计
    
    # 参数辨识过程模拟
    identification_data = {
        'time': time,
        'channels': ['Channel_1', 'Channel_2', 'Channel_3']
    }
    
    for i, channel in enumerate(identification_data['channels']):
        # 积分系数辨识过程
        integral_coeff_evolution = np.zeros(time_steps)
        time_delay_evolution = np.zeros(time_steps)
        
        # 模拟参数收敛过程
        for t in range(time_steps):
            # 收敛速度参数
            convergence_rate_integral = 0.01
            convergence_rate_delay = 0.008
            
            # 添加测量噪声
            noise_integral = np.random.normal(0, 0.005)
            noise_delay = np.random.normal(0, 0.02)
            
            if t == 0:
                integral_coeff_evolution[t] = initial_integral_coeff[i]
                time_delay_evolution[t] = initial_time_delay[i]
            else:
                # 指数收敛到真实值
                error_integral = true_integral_coeff[i] - integral_coeff_evolution[t-1]
                error_delay = true_time_delay[i] - time_delay_evolution[t-1]
                
                integral_coeff_evolution[t] = integral_coeff_evolution[t-1] + \
                    convergence_rate_integral * error_integral + noise_integral
                time_delay_evolution[t] = time_delay_evolution[t-1] + \
                    convergence_rate_delay * error_delay + noise_delay
        
        identification_data[f'{channel}_integral_coeff'] = integral_coeff_evolution
        identification_data[f'{channel}_time_delay'] = time_delay_evolution
        identification_data[f'{channel}_true_integral'] = np.full(time_steps, true_integral_coeff[i])
        identification_data[f'{channel}_true_delay'] = np.full(time_steps, true_time_delay[i])
        
        # 计算辨识误差
        identification_data[f'{channel}_integral_error'] = \
            np.abs(integral_coeff_evolution - true_integral_coeff[i])
        identification_data[f'{channel}_delay_error'] = \
            np.abs(time_delay_evolution - true_time_delay[i])
    
    return identification_data

def plot_parameter_identification_timeseries(data):
    """
    绘制参数辨识时间序列图
    """
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle('参数辨识过程时间序列分析', fontsize=16, fontweight='bold')
    
    channels = data['channels']
    time = data['time']
    
    # 颜色配置
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, channel in enumerate(channels):
        # 积分系数辨识过程
        ax1 = axes[i, 0]
        ax1.plot(time, data[f'{channel}_integral_coeff'], 
                color=colors[i], linewidth=2, label=f'{channel} 辨识值')
        ax1.axhline(y=data[f'{channel}_true_integral'][0], 
                   color='red', linestyle='--', linewidth=2, label='真实值')
        ax1.set_title(f'{channel} 积分系数辨识过程')
        ax1.set_xlabel('时间 (s)')
        ax1.set_ylabel('积分系数')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 时滞参数辨识过程
        ax2 = axes[i, 1]
        ax2.plot(time, data[f'{channel}_time_delay'], 
                color=colors[i], linewidth=2, label=f'{channel} 辨识值')
        ax2.axhline(y=data[f'{channel}_true_delay'][0], 
                   color='red', linestyle='--', linewidth=2, label='真实值')
        ax2.set_title(f'{channel} 时滞参数辨识过程')
        ax2.set_xlabel('时间 (s)')
        ax2.set_ylabel('时滞 (s)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
    
    plt.tight_layout()
    
    # 保存图片
    os.makedirs('experiment_results', exist_ok=True)
    plt.savefig('experiment_results/parameter_identification_timeseries.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def plot_identification_errors(data):
    """
    绘制辨识误差分析图
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('参数辨识误差分析', fontsize=16, fontweight='bold')
    
    channels = data['channels']
    time = data['time']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # 积分系数误差时间序列
    ax1 = axes[0, 0]
    for i, channel in enumerate(channels):
        ax1.plot(time, data[f'{channel}_integral_error'], 
                color=colors[i], linewidth=2, label=channel)
    ax1.set_title('积分系数辨识误差时间序列')
    ax1.set_xlabel('时间 (s)')
    ax1.set_ylabel('绝对误差')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_yscale('log')
    
    # 时滞参数误差时间序列
    ax2 = axes[0, 1]
    for i, channel in enumerate(channels):
        ax2.plot(time, data[f'{channel}_delay_error'], 
                color=colors[i], linewidth=2, label=channel)
    ax2.set_title('时滞参数辨识误差时间序列')
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('绝对误差 (s)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_yscale('log')
    
    # 收敛性能对比
    ax3 = axes[1, 0]
    final_integral_errors = [data[f'{channel}_integral_error'][-1] for channel in channels]
    final_delay_errors = [data[f'{channel}_delay_error'][-1] for channel in channels]
    
    x_pos = np.arange(len(channels))
    width = 0.35
    
    bars1 = ax3.bar(x_pos - width/2, final_integral_errors, width, 
                   label='积分系数误差', color='skyblue')
    bars2 = ax3.bar(x_pos + width/2, final_delay_errors, width, 
                   label='时滞参数误差', color='lightcoral')
    
    ax3.set_title('最终辨识误差对比')
    ax3.set_xlabel('渠道')
    ax3.set_ylabel('绝对误差')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(channels)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom')
    for bar in bars2:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom')
    
    # 参数收敛轨迹
    ax4 = axes[1, 1]
    for i, channel in enumerate(channels):
        integral_values = data[f'{channel}_integral_coeff']
        delay_values = data[f'{channel}_time_delay']
        
        # 绘制参数空间中的收敛轨迹
        ax4.plot(integral_values, delay_values, 
                color=colors[i], linewidth=2, label=f'{channel} 轨迹', alpha=0.7)
        
        # 标记起始点和终点
        ax4.scatter(integral_values[0], delay_values[0], 
                   color=colors[i], s=100, marker='o', label=f'{channel} 起始')
        ax4.scatter(integral_values[-1], delay_values[-1], 
                   color=colors[i], s=100, marker='s', label=f'{channel} 终点')
        
        # 标记真实值
        true_integral = data[f'{channel}_true_integral'][0]
        true_delay = data[f'{channel}_true_delay'][0]
        ax4.scatter(true_integral, true_delay, 
                   color='red', s=150, marker='*', alpha=0.8)
    
    ax4.set_title('参数空间收敛轨迹')
    ax4.set_xlabel('积分系数')
    ax4.set_ylabel('时滞参数 (s)')
    ax4.grid(True, alpha=0.3)
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('experiment_results/parameter_identification_errors.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def calculate_identification_metrics(data):
    """
    计算辨识性能指标
    """
    channels = data['channels']
    metrics = {
        'convergence_analysis': {},
        'final_accuracy': {},
        'convergence_time': {}
    }
    
    for channel in channels:
        # 最终误差
        final_integral_error = data[f'{channel}_integral_error'][-1]
        final_delay_error = data[f'{channel}_delay_error'][-1]
        
        # 收敛时间（误差降到5%以内的时间）
        integral_threshold = 0.05 * data[f'{channel}_true_integral'][0]
        delay_threshold = 0.05 * data[f'{channel}_true_delay'][0]
        
        integral_conv_idx = np.where(data[f'{channel}_integral_error'] < integral_threshold)[0]
        delay_conv_idx = np.where(data[f'{channel}_delay_error'] < delay_threshold)[0]
        
        integral_conv_time = data['time'][integral_conv_idx[0]] if len(integral_conv_idx) > 0 else None
        delay_conv_time = data['time'][delay_conv_idx[0]] if len(delay_conv_idx) > 0 else None
        
        # 平均误差
        avg_integral_error = np.mean(data[f'{channel}_integral_error'])
        avg_delay_error = np.mean(data[f'{channel}_delay_error'])
        
        metrics['final_accuracy'][channel] = {
            'integral_coefficient_error': float(final_integral_error),
            'time_delay_error': float(final_delay_error),
            'integral_accuracy_percent': float((1 - final_integral_error / data[f'{channel}_true_integral'][0]) * 100),
            'delay_accuracy_percent': float((1 - final_delay_error / data[f'{channel}_true_delay'][0]) * 100)
        }
        
        metrics['convergence_time'][channel] = {
            'integral_convergence_time': float(integral_conv_time) if integral_conv_time else None,
            'delay_convergence_time': float(delay_conv_time) if delay_conv_time else None
        }
        
        metrics['convergence_analysis'][channel] = {
            'average_integral_error': float(avg_integral_error),
            'average_delay_error': float(avg_delay_error),
            'integral_error_std': float(np.std(data[f'{channel}_integral_error'])),
            'delay_error_std': float(np.std(data[f'{channel}_delay_error']))
        }
    
    return metrics

def generate_identification_report(data, metrics):
    """
    生成参数辨识分析报告
    """
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'simulation_config': {
            'time_steps': len(data['time']),
            'time_duration': float(data['time'][-1]),
            'sampling_interval': float(data['time'][1] - data['time'][0]),
            'channels_analyzed': data['channels']
        },
        'identification_results': metrics,
        'key_findings': {
            'best_performing_channel': None,
            'convergence_summary': {},
            'accuracy_summary': {}
        },
        'recommendations': []
    }
    
    # 分析最佳性能渠道
    channels = data['channels']
    integral_accuracies = [metrics['final_accuracy'][ch]['integral_accuracy_percent'] for ch in channels]
    delay_accuracies = [metrics['final_accuracy'][ch]['delay_accuracy_percent'] for ch in channels]
    
    best_integral_idx = np.argmax(integral_accuracies)
    best_delay_idx = np.argmax(delay_accuracies)
    
    report['key_findings']['best_performing_channel'] = {
        'integral_identification': channels[best_integral_idx],
        'delay_identification': channels[best_delay_idx]
    }
    
    # 收敛性总结
    avg_integral_accuracy = np.mean(integral_accuracies)
    avg_delay_accuracy = np.mean(delay_accuracies)
    
    report['key_findings']['accuracy_summary'] = {
        'average_integral_accuracy': float(avg_integral_accuracy),
        'average_delay_accuracy': float(avg_delay_accuracy),
        'overall_performance': 'excellent' if min(avg_integral_accuracy, avg_delay_accuracy) > 95 else 
                              'good' if min(avg_integral_accuracy, avg_delay_accuracy) > 90 else 'needs_improvement'
    }
    
    # 生成建议
    if avg_integral_accuracy < 95:
        report['recommendations'].append('建议增加积分系数辨识的激励信号强度')
    if avg_delay_accuracy < 95:
        report['recommendations'].append('建议优化时滞参数辨识算法的收敛速度')
    
    report['recommendations'].extend([
        '考虑采用自适应辨识算法提高收敛速度',
        '增加参数辨识的鲁棒性验证',
        '实施在线参数更新机制'
    ])
    
    return report

def main():
    """
    主函数
    """
    print("开始参数辨识过程分析...")
    
    # 生成辨识数据
    print("生成参数辨识数据...")
    identification_data = generate_identification_data()
    
    # 绘制时间序列图
    print("绘制参数辨识时间序列图...")
    plot_parameter_identification_timeseries(identification_data)
    
    # 绘制误差分析图
    print("绘制辨识误差分析图...")
    plot_identification_errors(identification_data)
    
    # 计算性能指标
    print("计算辨识性能指标...")
    metrics = calculate_identification_metrics(identification_data)
    
    # 生成分析报告
    print("生成分析报告...")
    report = generate_identification_report(identification_data, metrics)
    
    # 保存结果
    os.makedirs('experiment_results', exist_ok=True)
    
    # 保存数据
    identification_df = pd.DataFrame({
        'time': identification_data['time'],
        **{k: v for k, v in identification_data.items() if k != 'time' and k != 'channels'}
    })
    identification_df.to_csv('experiment_results/parameter_identification_data.csv', index=False)
    
    # 保存指标
    with open('experiment_results/identification_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # 保存报告
    with open('experiment_results/parameter_identification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    markdown_report = f"""
# 参数辨识过程分析报告

## 分析概述
- 分析时间: {report['analysis_timestamp']}
- 仿真时长: {report['simulation_config']['time_duration']:.1f} 秒
- 采样间隔: {report['simulation_config']['sampling_interval']:.1f} 秒
- 分析渠道: {', '.join(report['simulation_config']['channels_analyzed'])}

## 主要发现

### 辨识精度
- 平均积分系数辨识精度: {report['key_findings']['accuracy_summary']['average_integral_accuracy']:.2f}%
- 平均时滞参数辨识精度: {report['key_findings']['accuracy_summary']['average_delay_accuracy']:.2f}%
- 整体性能评估: {report['key_findings']['accuracy_summary']['overall_performance']}

### 最佳性能渠道
- 积分系数辨识: {report['key_findings']['best_performing_channel']['integral_identification']}
- 时滞参数辨识: {report['key_findings']['best_performing_channel']['delay_identification']}

## 各渠道详细结果

"""
    
    for channel in identification_data['channels']:
        channel_metrics = metrics['final_accuracy'][channel]
        conv_metrics = metrics['convergence_time'][channel]
        
        markdown_report += f"""
### {channel}
- 积分系数辨识精度: {channel_metrics['integral_accuracy_percent']:.2f}%
- 时滞参数辨识精度: {channel_metrics['delay_accuracy_percent']:.2f}%
- 积分系数收敛时间: {conv_metrics['integral_convergence_time']:.1f}s (如果收敛)
- 时滞参数收敛时间: {conv_metrics['delay_convergence_time']:.1f}s (如果收敛)

"""
    
    markdown_report += f"""
## 改进建议

"""
    for i, recommendation in enumerate(report['recommendations'], 1):
        markdown_report += f"{i}. {recommendation}\n"
    
    with open('experiment_results/parameter_identification_report.md', 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print("\n=== 参数辨识分析完成 ===")
    print(f"分析结果已保存到 experiment_results 目录")
    print(f"\n主要发现:")
    print(f"- 平均积分系数辨识精度: {report['key_findings']['accuracy_summary']['average_integral_accuracy']:.2f}%")
    print(f"- 平均时滞参数辨识精度: {report['key_findings']['accuracy_summary']['average_delay_accuracy']:.2f}%")
    print(f"- 整体性能: {report['key_findings']['accuracy_summary']['overall_performance']}")
    
    return identification_data, metrics, report

if __name__ == "__main__":
    identification_data, metrics, report = main()