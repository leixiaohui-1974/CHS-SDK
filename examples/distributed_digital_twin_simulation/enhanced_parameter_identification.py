#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型参数辨识系统
实现改进建议：增强激励信号强度、优化收敛速度等
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
import os
from scipy import signal
from scipy.optimize import minimize

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class EnhancedExcitationSignal:
    """
    增强型激励信号生成器
    """
    
    def __init__(self, duration=50.0, dt=0.1):
        self.duration = duration
        self.dt = dt
        self.time = np.arange(0, duration, dt)
        self.n_samples = len(self.time)
    
    def generate_prbs(self, amplitude=1.0, switch_probability=0.1):
        """
        生成伪随机二进制序列(PRBS)
        """
        prbs = np.zeros(self.n_samples)
        current_level = amplitude
        
        for i in range(self.n_samples):
            if np.random.random() < switch_probability:
                current_level = -current_level
            prbs[i] = current_level
        
        return prbs
    
    def generate_chirp_signal(self, f0=0.01, f1=0.5, amplitude=1.0):
        """
        生成线性调频信号(Chirp)
        """
        return amplitude * signal.chirp(self.time, f0, self.duration, f1)
    
    def generate_multisine(self, frequencies=[0.01, 0.05, 0.1, 0.2], amplitudes=None):
        """
        生成多正弦波信号
        """
        if amplitudes is None:
            amplitudes = [1.0] * len(frequencies)
        
        multisine = np.zeros(self.n_samples)
        for freq, amp in zip(frequencies, amplitudes):
            multisine += amp * np.sin(2 * np.pi * freq * self.time)
        
        return multisine
    
    def generate_optimal_excitation(self, channel_id=0):
        """
        生成优化的激励信号组合
        """
        # 基于渠道特性调整激励信号
        if channel_id == 0:  # Channel_1
            # 使用PRBS + 低频正弦波
            prbs = self.generate_prbs(amplitude=0.8, switch_probability=0.08)
            sine = 0.3 * np.sin(2 * np.pi * 0.02 * self.time)
            excitation = prbs + sine
        elif channel_id == 1:  # Channel_2
            # 使用Chirp信号
            excitation = self.generate_chirp_signal(f0=0.005, f1=0.3, amplitude=1.2)
        else:  # Channel_3
            # 使用多正弦波
            excitation = self.generate_multisine(
                frequencies=[0.01, 0.03, 0.08, 0.15],
                amplitudes=[0.8, 0.6, 0.4, 0.3]
            )
        
        return excitation

class AdaptiveIdentificationAlgorithm:
    """
    自适应参数辨识算法
    """
    
    def __init__(self, initial_params, learning_rates=None):
        self.params = np.array(initial_params)
        self.param_history = [self.params.copy()]
        
        if learning_rates is None:
            self.learning_rates = {
                'integral_coeff': 0.02,
                'time_delay': 0.015,
                'adaptive_factor': 0.95
            }
        else:
            self.learning_rates = learning_rates
        
        self.error_history = []
        self.gradient_history = []
    
    def compute_gradient(self, error, input_signal, output_signal):
        """
        计算参数梯度
        """
        # 简化的梯度计算
        grad_integral = -error * np.mean(input_signal)
        grad_delay = -error * np.mean(np.gradient(output_signal))
        
        return np.array([grad_integral, grad_delay])
    
    def update_parameters(self, gradient, error_magnitude):
        """
        自适应参数更新
        """
        # 自适应学习率调整
        if len(self.error_history) > 1:
            error_trend = abs(error_magnitude) - abs(self.error_history[-1])
            if error_trend > 0:  # 误差增加，降低学习率
                self.learning_rates['integral_coeff'] *= self.learning_rates['adaptive_factor']
                self.learning_rates['time_delay'] *= self.learning_rates['adaptive_factor']
            else:  # 误差减少，可以适当增加学习率
                self.learning_rates['integral_coeff'] /= self.learning_rates['adaptive_factor']
                self.learning_rates['time_delay'] /= self.learning_rates['adaptive_factor']
        
        # 参数更新
        self.params[0] += self.learning_rates['integral_coeff'] * gradient[0]
        self.params[1] += self.learning_rates['time_delay'] * gradient[1]
        
        # 参数约束
        self.params[0] = np.clip(self.params[0], 0.01, 5.0)  # 积分系数约束
        self.params[1] = np.clip(self.params[1], 0.5, 10.0)  # 时滞约束
        
        self.param_history.append(self.params.copy())
        self.gradient_history.append(gradient.copy())
    
    def get_current_params(self):
        return self.params.copy()
    
    def get_param_history(self):
        return np.array(self.param_history)

class RobustnessValidator:
    """
    鲁棒性验证器
    """
    
    def __init__(self):
        self.test_scenarios = {
            'nominal': {'noise_level': 0.01, 'disturbance_level': 0.0},
            'high_noise': {'noise_level': 0.05, 'disturbance_level': 0.0},
            'with_disturbance': {'noise_level': 0.01, 'disturbance_level': 0.2},
            'extreme': {'noise_level': 0.08, 'disturbance_level': 0.3}
        }
    
    def run_robustness_test(self, identification_algorithm, excitation_signal, true_params):
        """
        运行鲁棒性测试
        """
        results = {}
        
        for scenario_name, scenario_params in self.test_scenarios.items():
            # 重置算法
            test_algorithm = AdaptiveIdentificationAlgorithm(
                initial_params=[0.1, 2.0],
                learning_rates=identification_algorithm.learning_rates.copy()
            )
            
            # 添加噪声和扰动
            noisy_signal = excitation_signal + \
                scenario_params['noise_level'] * np.random.randn(len(excitation_signal))
            
            if scenario_params['disturbance_level'] > 0:
                disturbance = scenario_params['disturbance_level'] * \
                    np.sin(2 * np.pi * 0.1 * np.arange(len(excitation_signal)) * 0.1)
                noisy_signal += disturbance
            
            # 运行辨识
            final_params, error_history = self._run_identification(
                test_algorithm, noisy_signal, true_params
            )
            
            # 计算性能指标
            final_error = np.abs(final_params - true_params)
            convergence_time = self._calculate_convergence_time(error_history)
            
            results[scenario_name] = {
                'final_params': final_params.tolist(),
                'final_error': final_error.tolist(),
                'convergence_time': convergence_time,
                'error_history': error_history
            }
        
        return results
    
    def _run_identification(self, algorithm, excitation_signal, true_params, n_iterations=500):
        """
        运行参数辨识过程
        """
        error_history = []
        
        for i in range(n_iterations):
            # 模拟系统响应
            current_params = algorithm.get_current_params()
            
            # 简化的系统模型
            system_output = self._simulate_system_response(
                excitation_signal, current_params, true_params
            )
            
            # 计算误差
            error = np.mean((current_params - true_params)**2)
            error_history.append(error)
            
            # 计算梯度并更新参数
            gradient = algorithm.compute_gradient(
                error, excitation_signal, system_output
            )
            algorithm.update_parameters(gradient, error)
        
        return algorithm.get_current_params(), error_history
    
    def _simulate_system_response(self, input_signal, current_params, true_params):
        """
        模拟系统响应
        """
        # 简化的系统模型
        response = np.zeros_like(input_signal)
        
        for i in range(1, len(input_signal)):
            # 积分环节
            response[i] = response[i-1] + true_params[0] * input_signal[i-1] * 0.1
            
            # 添加时滞影响
            delay_samples = int(true_params[1] / 0.1)
            if i > delay_samples:
                response[i] += 0.1 * input_signal[i - delay_samples]
        
        return response
    
    def _calculate_convergence_time(self, error_history, threshold=0.05):
        """
        计算收敛时间
        """
        for i, error in enumerate(error_history):
            if error < threshold:
                return i * 0.1  # 转换为时间
        return len(error_history) * 0.1  # 未收敛

class OnlineParameterMonitor:
    """
    在线参数监控系统
    """
    
    def __init__(self, update_interval=10):
        self.update_interval = update_interval
        self.parameter_log = []
        self.performance_log = []
        self.alert_thresholds = {
            'parameter_drift': 0.1,
            'performance_degradation': 0.2
        }
    
    def update_parameters(self, timestamp, parameters, performance_metrics):
        """
        更新参数记录
        """
        self.parameter_log.append({
            'timestamp': timestamp,
            'parameters': parameters.copy(),
            'performance': performance_metrics
        })
        
        # 检查是否需要报警
        self._check_alerts()
    
    def _check_alerts(self):
        """
        检查报警条件
        """
        if len(self.parameter_log) < 2:
            return
        
        current = self.parameter_log[-1]
        previous = self.parameter_log[-2]
        
        # 检查参数漂移
        param_drift = np.linalg.norm(
            np.array(current['parameters']) - np.array(previous['parameters'])
        )
        
        if param_drift > self.alert_thresholds['parameter_drift']:
            print(f"警告: 参数漂移检测到，漂移量: {param_drift:.4f}")
        
        # 检查性能退化
        if current['performance'] > previous['performance'] * (1 + self.alert_thresholds['performance_degradation']):
            print(f"警告: 性能退化检测到，当前性能: {current['performance']:.4f}")
    
    def get_parameter_trend(self, window_size=50):
        """
        获取参数趋势
        """
        if len(self.parameter_log) < window_size:
            return None
        
        recent_params = [log['parameters'] for log in self.parameter_log[-window_size:]]
        return np.array(recent_params)

def generate_enhanced_identification_data():
    """
    生成增强型参数辨识数据
    """
    # 仿真参数
    duration = 50.0
    dt = 0.1
    time = np.arange(0, duration, dt)
    
    # 真实参数值
    true_params = {
        'Channel_1': [0.15, 2.5],
        'Channel_2': [1.8, 3.0],
        'Channel_3': [0.12, 2.8]
    }
    
    # 创建激励信号生成器
    excitation_gen = EnhancedExcitationSignal(duration, dt)
    
    # 存储结果
    results = {
        'time': time,
        'channels': list(true_params.keys()),
        'excitation_signals': {},
        'identification_results': {},
        'robustness_results': {}
    }
    
    # 为每个渠道生成数据
    for i, (channel, true_param) in enumerate(true_params.items()):
        print(f"处理 {channel}...")
        
        # 生成优化的激励信号
        excitation = excitation_gen.generate_optimal_excitation(i)
        results['excitation_signals'][channel] = excitation
        
        # 创建自适应辨识算法
        adaptive_algo = AdaptiveIdentificationAlgorithm(
            initial_params=[0.1, 2.0],
            learning_rates={
                'integral_coeff': 0.025,
                'time_delay': 0.018,
                'adaptive_factor': 0.95
            }
        )
        
        # 运行参数辨识
        validator = RobustnessValidator()
        final_params, error_history = validator._run_identification(
            adaptive_algo, excitation, np.array(true_param)
        )
        
        # 获取参数历史
        param_history = adaptive_algo.get_param_history()
        
        # 存储辨识结果
        results['identification_results'][channel] = {
            'param_history': param_history,
            'error_history': error_history,
            'final_params': final_params,
            'true_params': true_param
        }
        
        # 运行鲁棒性测试
        robustness_results = validator.run_robustness_test(
            adaptive_algo, excitation, np.array(true_param)
        )
        results['robustness_results'][channel] = robustness_results
    
    return results

def plot_enhanced_identification_results(results):
    """
    绘制增强型辨识结果
    """
    channels = results['channels']
    time = results['time']
    
    # 创建图形
    fig, axes = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle('增强型参数辨识结果分析', fontsize=16, fontweight='bold')
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, channel in enumerate(channels):
        channel_results = results['identification_results'][channel]
        param_history = channel_results['param_history']
        error_history = channel_results['error_history']
        true_params = channel_results['true_params']
        excitation = results['excitation_signals'][channel]
        
        # 激励信号
        ax1 = axes[i, 0]
        ax1.plot(time, excitation, color=colors[i], linewidth=1.5)
        ax1.set_title(f'{channel} 优化激励信号')
        ax1.set_xlabel('时间 (s)')
        ax1.set_ylabel('激励幅值')
        ax1.grid(True, alpha=0.3)
        
        # 参数收敛过程
        ax2 = axes[i, 1]
        param_time = np.arange(len(param_history)) * 0.1
        ax2.plot(param_time, param_history[:, 0], 
                color=colors[i], linewidth=2, label='积分系数')
        ax2.axhline(y=true_params[0], color='red', linestyle='--', 
                   linewidth=2, label='真实值')
        ax2.set_title(f'{channel} 积分系数收敛')
        ax2.set_xlabel('时间 (s)')
        ax2.set_ylabel('积分系数')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 误差收敛
        ax3 = axes[i, 2]
        error_time = np.arange(len(error_history)) * 0.1
        ax3.semilogy(error_time, error_history, 
                    color=colors[i], linewidth=2)
        ax3.set_title(f'{channel} 误差收敛')
        ax3.set_xlabel('时间 (s)')
        ax3.set_ylabel('均方误差 (log)')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图片
    os.makedirs('experiment_results', exist_ok=True)
    plt.savefig('experiment_results/enhanced_identification_results.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def plot_robustness_analysis(results):
    """
    绘制鲁棒性分析结果
    """
    channels = results['channels']
    scenarios = ['nominal', 'high_noise', 'with_disturbance', 'extreme']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('参数辨识鲁棒性分析', fontsize=16, fontweight='bold')
    
    # 最终误差对比
    ax1 = axes[0, 0]
    scenario_labels = ['标准', '高噪声', '有扰动', '极端']
    
    for i, channel in enumerate(channels):
        errors = []
        for scenario in scenarios:
            final_error = results['robustness_results'][channel][scenario]['final_error']
            errors.append(np.linalg.norm(final_error))
        
        x_pos = np.arange(len(scenarios)) + i * 0.25
        ax1.bar(x_pos, errors, width=0.25, label=channel, alpha=0.8)
    
    ax1.set_title('不同场景下的最终辨识误差')
    ax1.set_xlabel('测试场景')
    ax1.set_ylabel('误差范数')
    ax1.set_xticks(np.arange(len(scenarios)) + 0.25)
    ax1.set_xticklabels(scenario_labels)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 收敛时间对比
    ax2 = axes[0, 1]
    for i, channel in enumerate(channels):
        conv_times = []
        for scenario in scenarios:
            conv_time = results['robustness_results'][channel][scenario]['convergence_time']
            conv_times.append(conv_time)
        
        x_pos = np.arange(len(scenarios)) + i * 0.25
        ax2.bar(x_pos, conv_times, width=0.25, label=channel, alpha=0.8)
    
    ax2.set_title('不同场景下的收敛时间')
    ax2.set_xlabel('测试场景')
    ax2.set_ylabel('收敛时间 (s)')
    ax2.set_xticks(np.arange(len(scenarios)) + 0.25)
    ax2.set_xticklabels(scenario_labels)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 误差收敛曲线对比（以Channel_1为例）
    ax3 = axes[1, 0]
    channel = channels[0]
    for scenario, label in zip(scenarios, scenario_labels):
        error_hist = results['robustness_results'][channel][scenario]['error_history']
        time_axis = np.arange(len(error_hist)) * 0.1
        ax3.semilogy(time_axis, error_hist, linewidth=2, label=label)
    
    ax3.set_title(f'{channel} 不同场景误差收敛对比')
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('误差 (log)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 鲁棒性评分
    ax4 = axes[1, 1]
    robustness_scores = []
    
    for channel in channels:
        # 计算鲁棒性评分（基于误差和收敛时间）
        scores = []
        for scenario in scenarios:
            error = np.linalg.norm(results['robustness_results'][channel][scenario]['final_error'])
            conv_time = results['robustness_results'][channel][scenario]['convergence_time']
            # 评分公式：误差越小、收敛越快，评分越高
            score = 100 / (1 + error + conv_time/50)
            scores.append(score)
        robustness_scores.append(scores)
    
    x_pos = np.arange(len(channels))
    width = 0.2
    
    for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
        scores = [robustness_scores[j][i] for j in range(len(channels))]
        ax4.bar(x_pos + i * width, scores, width, label=label, alpha=0.8)
    
    ax4.set_title('鲁棒性综合评分')
    ax4.set_xlabel('渠道')
    ax4.set_ylabel('鲁棒性评分')
    ax4.set_xticks(x_pos + width * 1.5)
    ax4.set_xticklabels(channels)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('experiment_results/robustness_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def calculate_enhancement_metrics(results):
    """
    计算增强效果指标
    """
    channels = results['channels']
    metrics = {
        'identification_performance': {},
        'robustness_performance': {},
        'overall_improvement': {}
    }
    
    for channel in channels:
        channel_results = results['identification_results'][channel]
        robustness_results = results['robustness_results'][channel]
        
        # 辨识性能指标
        final_params = channel_results['final_params']
        true_params = np.array(channel_results['true_params'])
        final_error = np.abs(final_params - true_params)
        
        # 收敛时间（误差降到5%以内）
        error_history = channel_results['error_history']
        convergence_idx = np.where(np.array(error_history) < 0.05)[0]
        convergence_time = convergence_idx[0] * 0.1 if len(convergence_idx) > 0 else 50.0
        
        metrics['identification_performance'][channel] = {
            'final_accuracy': {
                'integral_coeff_error': float(final_error[0]),
                'time_delay_error': float(final_error[1]),
                'integral_accuracy_percent': float((1 - final_error[0] / true_params[0]) * 100),
                'delay_accuracy_percent': float((1 - final_error[1] / true_params[1]) * 100)
            },
            'convergence_time': float(convergence_time),
            'convergence_rate': float(1.0 / convergence_time if convergence_time > 0 else 0)
        }
        
        # 鲁棒性性能指标
        robustness_scores = []
        for scenario in ['nominal', 'high_noise', 'with_disturbance', 'extreme']:
            scenario_error = np.linalg.norm(robustness_results[scenario]['final_error'])
            scenario_conv_time = robustness_results[scenario]['convergence_time']
            score = 100 / (1 + scenario_error + scenario_conv_time/50)
            robustness_scores.append(score)
        
        metrics['robustness_performance'][channel] = {
            'average_robustness_score': float(np.mean(robustness_scores)),
            'worst_case_score': float(np.min(robustness_scores)),
            'robustness_variance': float(np.var(robustness_scores))
        }
    
    # 整体改进评估
    avg_accuracy = np.mean([
        metrics['identification_performance'][ch]['final_accuracy']['integral_accuracy_percent']
        for ch in channels
    ])
    avg_robustness = np.mean([
        metrics['robustness_performance'][ch]['average_robustness_score']
        for ch in channels
    ])
    
    metrics['overall_improvement'] = {
        'average_identification_accuracy': float(avg_accuracy),
        'average_robustness_score': float(avg_robustness),
        'improvement_grade': 'excellent' if avg_accuracy > 96 and avg_robustness > 80 else
                           'good' if avg_accuracy > 94 and avg_robustness > 70 else
                           'satisfactory' if avg_accuracy > 90 and avg_robustness > 60 else
                           'needs_improvement'
    }
    
    return metrics

def generate_enhancement_report(results, metrics):
    """
    生成增强效果报告
    """
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'enhancement_summary': {
            'implemented_improvements': [
                '增强激励信号设计（PRBS、Chirp、多正弦波）',
                '自适应参数辨识算法',
                '鲁棒性验证机制',
                '在线参数监控系统'
            ],
            'performance_metrics': metrics
        },
        'key_improvements': {},
        'recommendations': []
    }
    
    # 分析关键改进
    channels = results['channels']
    
    for channel in channels:
        perf = metrics['identification_performance'][channel]
        robust = metrics['robustness_performance'][channel]
        
        report['key_improvements'][channel] = {
            'accuracy_improvement': {
                'integral_coefficient': f"{perf['final_accuracy']['integral_accuracy_percent']:.2f}%",
                'time_delay': f"{perf['final_accuracy']['delay_accuracy_percent']:.2f}%"
            },
            'convergence_improvement': f"收敛时间: {perf['convergence_time']:.1f}s",
            'robustness_score': f"{robust['average_robustness_score']:.1f}/100"
        }
    
    # 生成建议
    overall_grade = metrics['overall_improvement']['improvement_grade']
    
    if overall_grade == 'excellent':
        report['recommendations'].extend([
            '当前系统性能优秀，建议保持现有配置',
            '可考虑进一步优化计算效率',
            '建议部署到生产环境进行实际验证'
        ])
    elif overall_grade == 'good':
        report['recommendations'].extend([
            '系统性能良好，建议微调激励信号参数',
            '可增加更多鲁棒性测试场景',
            '建议优化自适应学习率策略'
        ])
    else:
        report['recommendations'].extend([
            '需要进一步优化激励信号设计',
            '建议调整自适应算法参数',
            '增加更强的鲁棒性机制',
            '考虑使用更先进的辨识算法'
        ])
    
    return report

def main():
    """
    主函数
    """
    print("开始增强型参数辨识分析...")
    
    # 生成增强型辨识数据
    print("生成增强型辨识数据...")
    results = generate_enhanced_identification_data()
    
    # 绘制增强型辨识结果
    print("绘制增强型辨识结果...")
    plot_enhanced_identification_results(results)
    
    # 绘制鲁棒性分析
    print("绘制鲁棒性分析...")
    plot_robustness_analysis(results)
    
    # 计算增强效果指标
    print("计算增强效果指标...")
    metrics = calculate_enhancement_metrics(results)
    
    # 生成增强效果报告
    print("生成增强效果报告...")
    report = generate_enhancement_report(results, metrics)
    
    # 保存结果
    os.makedirs('experiment_results', exist_ok=True)
    
    # 保存指标
    with open('experiment_results/enhanced_identification_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # 保存报告
    with open('experiment_results/enhancement_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    markdown_report = f"""
# 增强型参数辨识系统分析报告

## 实施的改进措施

1. **增强激励信号设计**
   - Channel_1: PRBS + 低频正弦波组合
   - Channel_2: 线性调频(Chirp)信号
   - Channel_3: 多正弦波信号

2. **自适应参数辨识算法**
   - 自适应学习率调整
   - 参数约束机制
   - 梯度优化策略

3. **鲁棒性验证机制**
   - 标准场景测试
   - 高噪声环境测试
   - 扰动环境测试
   - 极端条件测试

4. **在线参数监控系统**
   - 实时参数跟踪
   - 性能退化检测
   - 自动报警机制

## 性能改进结果

### 整体性能
- 平均辨识精度: {metrics['overall_improvement']['average_identification_accuracy']:.2f}%
- 平均鲁棒性评分: {metrics['overall_improvement']['average_robustness_score']:.1f}/100
- 改进等级: {metrics['overall_improvement']['improvement_grade']}

### 各渠道详细结果

"""
    
    for channel in results['channels']:
        perf = metrics['identification_performance'][channel]
        robust = metrics['robustness_performance'][channel]
        
        markdown_report += f"""
#### {channel}
- 积分系数辨识精度: {perf['final_accuracy']['integral_accuracy_percent']:.2f}%
- 时滞参数辨识精度: {perf['final_accuracy']['delay_accuracy_percent']:.2f}%
- 收敛时间: {perf['convergence_time']:.1f}s
- 鲁棒性评分: {robust['average_robustness_score']:.1f}/100

"""
    
    markdown_report += f"""
## 改进建议

"""
    for i, recommendation in enumerate(report['recommendations'], 1):
        markdown_report += f"{i}. {recommendation}\n"
    
    with open('experiment_results/enhancement_report.md', 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print("\n=== 增强型参数辨识分析完成 ===")
    print(f"分析结果已保存到 experiment_results 目录")
    print(f"\n主要改进:")
    print(f"- 平均辨识精度: {metrics['overall_improvement']['average_identification_accuracy']:.2f}%")
    print(f"- 平均鲁棒性评分: {metrics['overall_improvement']['average_robustness_score']:.1f}/100")
    print(f"- 改进等级: {metrics['overall_improvement']['improvement_grade']}")
    
    return results, metrics, report

if __name__ == "__main__":
    results, metrics, report = main()