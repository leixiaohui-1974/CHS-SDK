#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
先进自适应参数辨识算法
实现更高级的自适应机制，提高收敛速度和鲁棒性
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
import os
from scipy import signal
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class AdvancedAdaptiveIdentifier:
    """
    先进自适应参数辨识器
    集成多种先进算法：RLS、Kalman滤波、粒子群优化等
    """
    
    def __init__(self, initial_params, method='hybrid'):
        self.initial_params = np.array(initial_params)
        self.method = method
        self.params = self.initial_params.copy()
        self.param_history = [self.params.copy()]
        
        # 算法配置
        self.config = {
            'rls': {
                'forgetting_factor': 0.98,
                'initial_covariance': 1000.0
            },
            'kalman': {
                'process_noise': 0.01,
                'measurement_noise': 0.1,
                'initial_uncertainty': 1.0
            },
            'pso': {
                'n_particles': 20,
                'w': 0.7,  # 惯性权重
                'c1': 1.5,  # 个体学习因子
                'c2': 1.5   # 群体学习因子
            },
            'hybrid': {
                'rls_weight': 0.4,
                'kalman_weight': 0.3,
                'pso_weight': 0.3
            }
        }
        
        # 初始化各算法状态
        self._initialize_algorithms()
        
        # 性能监控
        self.performance_history = []
        self.convergence_threshold = 0.01
        self.stagnation_counter = 0
        self.max_stagnation = 50
        
    def _initialize_algorithms(self):
        """
        初始化各种算法的状态变量
        """
        n_params = len(self.initial_params)
        
        # RLS算法状态
        self.rls_state = {
            'P': np.eye(n_params) * self.config['rls']['initial_covariance'],
            'theta': self.initial_params.copy(),
            'lambda': self.config['rls']['forgetting_factor']
        }
        
        # Kalman滤波状态
        self.kalman_state = {
            'x': self.initial_params.copy(),  # 状态估计
            'P': np.eye(n_params) * self.config['kalman']['initial_uncertainty'],  # 协方差矩阵
            'Q': np.eye(n_params) * self.config['kalman']['process_noise'],  # 过程噪声
            'R': self.config['kalman']['measurement_noise']  # 测量噪声
        }
        
        # PSO算法状态
        n_particles = self.config['pso']['n_particles']
        self.pso_state = {
            'particles': np.random.uniform(
                low=self.initial_params * 0.5,
                high=self.initial_params * 1.5,
                size=(n_particles, n_params)
            ),
            'velocities': np.random.uniform(-0.1, 0.1, size=(n_particles, n_params)),
            'personal_best': None,
            'global_best': self.initial_params.copy(),
            'personal_best_scores': np.full(n_particles, np.inf),
            'global_best_score': np.inf
        }
        self.pso_state['personal_best'] = self.pso_state['particles'].copy()
    
    def rls_update(self, phi, y):
        """
        递推最小二乘(RLS)更新
        """
        P = self.rls_state['P']
        theta = self.rls_state['theta']
        lam = self.rls_state['lambda']
        
        # 确保phi是列向量
        phi = phi.reshape(-1, 1)
        
        # 计算增益向量
        denominator = lam + phi.T @ P @ phi
        K = P @ phi / denominator
        
        # 更新参数估计
        error = y - phi.T @ theta
        theta_new = theta + K.flatten() * error
        
        # 更新协方差矩阵
        P_new = (P - K @ phi.T @ P) / lam
        
        # 更新状态
        self.rls_state['P'] = P_new
        self.rls_state['theta'] = theta_new
        
        return theta_new
    
    def kalman_update(self, measurement, control_input):
        """
        Kalman滤波更新
        """
        x = self.kalman_state['x']
        P = self.kalman_state['P']
        Q = self.kalman_state['Q']
        R = self.kalman_state['R']
        
        # 预测步骤
        x_pred = x  # 假设状态转移矩阵为单位矩阵
        P_pred = P + Q
        
        # 更新步骤
        H = np.eye(len(x))  # 观测矩阵
        S = H @ P_pred @ H.T + R * np.eye(len(x))
        K = P_pred @ H.T @ np.linalg.inv(S)
        
        x_new = x_pred + K @ (measurement - H @ x_pred)
        P_new = (np.eye(len(x)) - K @ H) @ P_pred
        
        # 更新状态
        self.kalman_state['x'] = x_new
        self.kalman_state['P'] = P_new
        
        return x_new
    
    def pso_update(self, objective_function):
        """
        粒子群优化(PSO)更新
        """
        particles = self.pso_state['particles']
        velocities = self.pso_state['velocities']
        personal_best = self.pso_state['personal_best']
        global_best = self.pso_state['global_best']
        personal_best_scores = self.pso_state['personal_best_scores']
        global_best_score = self.pso_state['global_best_score']
        
        w = self.config['pso']['w']
        c1 = self.config['pso']['c1']
        c2 = self.config['pso']['c2']
        
        # 评估所有粒子
        for i, particle in enumerate(particles):
            score = objective_function(particle)
            
            # 更新个体最优
            if score < personal_best_scores[i]:
                personal_best_scores[i] = score
                personal_best[i] = particle.copy()
                
                # 更新全局最优
                if score < global_best_score:
                    global_best_score = score
                    global_best = particle.copy()
        
        # 更新速度和位置
        r1 = np.random.random(particles.shape)
        r2 = np.random.random(particles.shape)
        
        velocities = (w * velocities + 
                     c1 * r1 * (personal_best - particles) +
                     c2 * r2 * (global_best - particles))
        
        particles = particles + velocities
        
        # 边界约束
        particles = np.clip(particles, 
                           self.initial_params * 0.1, 
                           self.initial_params * 3.0)
        
        # 更新状态
        self.pso_state['particles'] = particles
        self.pso_state['velocities'] = velocities
        self.pso_state['personal_best'] = personal_best
        self.pso_state['global_best'] = global_best
        self.pso_state['personal_best_scores'] = personal_best_scores
        self.pso_state['global_best_score'] = global_best_score
        
        return global_best
    
    def hybrid_update(self, phi, y, control_input, objective_function):
        """
        混合算法更新
        """
        # 获取各算法的估计
        rls_estimate = self.rls_update(phi, y)
        kalman_estimate = self.kalman_update(self.params, control_input)
        pso_estimate = self.pso_update(objective_function)
        
        # 加权融合
        weights = self.config['hybrid']
        hybrid_estimate = (weights['rls_weight'] * rls_estimate +
                          weights['kalman_weight'] * kalman_estimate +
                          weights['pso_weight'] * pso_estimate)
        
        return hybrid_estimate
    
    def update_parameters(self, measurement_data, control_input=None):
        """
        更新参数估计
        """
        # 构造回归向量
        phi = self._construct_regressor(measurement_data, control_input)
        y = measurement_data[-1]  # 当前测量值
        
        # 定义目标函数
        def objective_function(params):
            predicted = np.dot(phi, params)
            return (y - predicted) ** 2
        
        # 根据选择的方法更新参数
        if self.method == 'rls':
            new_params = self.rls_update(phi, y)
        elif self.method == 'kalman':
            new_params = self.kalman_update(self.params, control_input)
        elif self.method == 'pso':
            new_params = self.pso_update(objective_function)
        elif self.method == 'hybrid':
            new_params = self.hybrid_update(phi, y, control_input, objective_function)
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # 更新参数
        self.params = new_params
        self.param_history.append(self.params.copy())
        
        # 性能监控
        current_error = objective_function(new_params)
        self.performance_history.append(current_error)
        
        # 检查收敛性
        self._check_convergence()
        
        return new_params
    
    def _construct_regressor(self, measurement_data, control_input):
        """
        构造回归向量
        """
        # 简化的回归向量构造
        if len(measurement_data) < 2:
            return np.array([1.0, 0.0])
        
        # 基于测量数据构造特征
        integral_feature = np.sum(measurement_data[:-1]) * 0.1  # 积分特征
        delay_feature = measurement_data[-2] if len(measurement_data) > 1 else 0.0  # 时滞特征
        
        # 确保返回的是列向量
        regressor = np.array([integral_feature, delay_feature])
        return regressor
    
    def _check_convergence(self):
        """
        检查收敛性
        """
        if len(self.performance_history) < 2:
            return False
        
        # 检查性能改进
        recent_improvement = abs(self.performance_history[-2] - self.performance_history[-1])
        
        if recent_improvement < self.convergence_threshold:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0
        
        # 如果停滞太久，调整算法参数
        if self.stagnation_counter > self.max_stagnation:
            self._adapt_algorithm_parameters()
            self.stagnation_counter = 0
        
        return self.stagnation_counter == 0
    
    def _adapt_algorithm_parameters(self):
        """
        自适应调整算法参数
        """
        # 调整RLS遗忘因子
        if self.method in ['rls', 'hybrid']:
            self.rls_state['lambda'] = max(0.95, self.rls_state['lambda'] - 0.01)
        
        # 调整Kalman滤波噪声参数
        if self.method in ['kalman', 'hybrid']:
            self.kalman_state['Q'] *= 1.1  # 增加过程噪声
        
        # 调整PSO参数
        if self.method in ['pso', 'hybrid']:
            self.config['pso']['w'] = max(0.4, self.config['pso']['w'] - 0.05)
            self.config['pso']['c1'] = min(2.0, self.config['pso']['c1'] + 0.1)
    
    def get_parameter_history(self):
        """
        获取参数历史
        """
        return np.array(self.param_history)
    
    def get_performance_history(self):
        """
        获取性能历史
        """
        return np.array(self.performance_history)

class MultiObjectiveOptimizer:
    """
    多目标优化器
    同时优化辨识精度和收敛速度
    """
    
    def __init__(self, weight_accuracy=0.7, weight_speed=0.3):
        self.weight_accuracy = weight_accuracy
        self.weight_speed = weight_speed
    
    def evaluate_solution(self, identifier, true_params, max_iterations=500):
        """
        评估解的质量
        """
        # 运行辨识过程
        param_history = []
        performance_history = []
        
        # 模拟测量数据
        measurement_data = []
        
        for i in range(max_iterations):
            # 生成模拟测量
            measurement = self._generate_measurement(i, true_params)
            measurement_data.append(measurement)
            
            # 更新参数
            if len(measurement_data) >= 2:
                new_params = identifier.update_parameters(measurement_data)
                param_history.append(new_params.copy())
                
                # 计算当前误差
                error = np.linalg.norm(new_params - true_params)
                performance_history.append(error)
                
                # 检查收敛
                if error < 0.05 and i > 50:
                    convergence_time = i
                    break
        else:
            convergence_time = max_iterations
        
        # 计算最终精度
        final_error = np.linalg.norm(param_history[-1] - true_params) if param_history else 1.0
        
        # 多目标评分
        accuracy_score = 1.0 / (1.0 + final_error)
        speed_score = 1.0 / (1.0 + convergence_time / 100.0)
        
        total_score = (self.weight_accuracy * accuracy_score + 
                      self.weight_speed * speed_score)
        
        return {
            'total_score': total_score,
            'accuracy_score': accuracy_score,
            'speed_score': speed_score,
            'final_error': final_error,
            'convergence_time': convergence_time,
            'param_history': param_history,
            'performance_history': performance_history
        }
    
    def _generate_measurement(self, time_step, true_params):
        """
        生成模拟测量数据
        """
        # 简化的系统模型
        t = time_step * 0.1
        
        # 激励信号
        excitation = np.sin(0.1 * t) + 0.5 * np.sin(0.05 * t)
        
        # 系统响应（积分 + 时滞）
        integral_response = true_params[0] * excitation * t
        delay_response = true_params[1] * np.sin(0.1 * (t - true_params[1]))
        
        # 添加噪声
        noise = np.random.normal(0, 0.02)
        
        return integral_response + delay_response + noise

def compare_identification_methods():
    """
    比较不同辨识方法的性能
    """
    # 测试参数
    true_params_sets = {
        'Channel_1': np.array([0.15, 2.5]),
        'Channel_2': np.array([1.8, 3.0]),
        'Channel_3': np.array([0.12, 2.8])
    }
    
    methods = ['rls', 'kalman', 'pso', 'hybrid']
    method_names = ['递推最小二乘', 'Kalman滤波', '粒子群优化', '混合算法']
    
    results = {}
    optimizer = MultiObjectiveOptimizer()
    
    for channel, true_params in true_params_sets.items():
        print(f"测试 {channel}...")
        channel_results = {}
        
        for method, method_name in zip(methods, method_names):
            print(f"  运行 {method_name}...")
            
            # 创建辨识器
            identifier = AdvancedAdaptiveIdentifier(
                initial_params=[0.1, 2.0],
                method=method
            )
            
            # 评估性能
            result = optimizer.evaluate_solution(identifier, true_params)
            channel_results[method] = {
                'method_name': method_name,
                'result': result
            }
        
        results[channel] = channel_results
    
    return results

def plot_method_comparison(results):
    """
    绘制方法比较结果
    """
    channels = list(results.keys())
    methods = ['rls', 'kalman', 'pso', 'hybrid']
    method_names = ['递推最小二乘', 'Kalman滤波', '粒子群优化', '混合算法']
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('先进自适应辨识算法性能比较', fontsize=16, fontweight='bold')
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # 总体评分比较
    ax1 = axes[0, 0]
    for i, method in enumerate(methods):
        scores = [results[ch][method]['result']['total_score'] for ch in channels]
        x_pos = np.arange(len(channels)) + i * 0.2
        ax1.bar(x_pos, scores, width=0.2, label=method_names[i], 
               color=colors[i], alpha=0.8)
    
    ax1.set_title('总体性能评分')
    ax1.set_xlabel('渠道')
    ax1.set_ylabel('评分')
    ax1.set_xticks(np.arange(len(channels)) + 0.3)
    ax1.set_xticklabels(channels)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 精度评分比较
    ax2 = axes[0, 1]
    for i, method in enumerate(methods):
        scores = [results[ch][method]['result']['accuracy_score'] for ch in channels]
        x_pos = np.arange(len(channels)) + i * 0.2
        ax2.bar(x_pos, scores, width=0.2, label=method_names[i], 
               color=colors[i], alpha=0.8)
    
    ax2.set_title('辨识精度评分')
    ax2.set_xlabel('渠道')
    ax2.set_ylabel('精度评分')
    ax2.set_xticks(np.arange(len(channels)) + 0.3)
    ax2.set_xticklabels(channels)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 收敛速度比较
    ax3 = axes[0, 2]
    for i, method in enumerate(methods):
        times = [results[ch][method]['result']['convergence_time'] for ch in channels]
        x_pos = np.arange(len(channels)) + i * 0.2
        ax3.bar(x_pos, times, width=0.2, label=method_names[i], 
               color=colors[i], alpha=0.8)
    
    ax3.set_title('收敛时间比较')
    ax3.set_xlabel('渠道')
    ax3.set_ylabel('收敛时间 (步)')
    ax3.set_xticks(np.arange(len(channels)) + 0.3)
    ax3.set_xticklabels(channels)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 参数收敛过程（以Channel_1为例）
    ax4 = axes[1, 0]
    channel = channels[0]
    for i, method in enumerate(methods):
        param_history = results[channel][method]['result']['param_history']
        if param_history:
            param_array = np.array(param_history)
            time_steps = np.arange(len(param_array))
            ax4.plot(time_steps, param_array[:, 0], 
                    color=colors[i], linewidth=2, label=f'{method_names[i]} - 积分系数')
    
    ax4.axhline(y=0.15, color='red', linestyle='--', linewidth=2, label='真实值')
    ax4.set_title(f'{channel} 积分系数收敛过程')
    ax4.set_xlabel('迭代步数')
    ax4.set_ylabel('积分系数')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 误差收敛过程
    ax5 = axes[1, 1]
    for i, method in enumerate(methods):
        performance_history = results[channel][method]['result']['performance_history']
        if performance_history:
            time_steps = np.arange(len(performance_history))
            ax5.semilogy(time_steps, performance_history, 
                        color=colors[i], linewidth=2, label=method_names[i])
    
    ax5.set_title(f'{channel} 误差收敛过程')
    ax5.set_xlabel('迭代步数')
    ax5.set_ylabel('误差 (log)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 方法综合排名
    ax6 = axes[1, 2]
    method_scores = []
    for method in methods:
        total_scores = [results[ch][method]['result']['total_score'] for ch in channels]
        avg_score = np.mean(total_scores)
        method_scores.append(avg_score)
    
    sorted_indices = np.argsort(method_scores)[::-1]
    sorted_methods = [method_names[i] for i in sorted_indices]
    sorted_scores = [method_scores[i] for i in sorted_indices]
    
    bars = ax6.bar(range(len(sorted_methods)), sorted_scores, 
                   color=[colors[i] for i in sorted_indices], alpha=0.8)
    ax6.set_title('算法综合排名')
    ax6.set_xlabel('算法')
    ax6.set_ylabel('平均评分')
    ax6.set_xticks(range(len(sorted_methods)))
    ax6.set_xticklabels(sorted_methods, rotation=45)
    ax6.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, score in zip(bars, sorted_scores):
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{score:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # 保存图片
    os.makedirs('experiment_results', exist_ok=True)
    plt.savefig('experiment_results/advanced_identification_comparison.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def calculate_improvement_metrics(results):
    """
    计算改进指标
    """
    channels = list(results.keys())
    methods = ['rls', 'kalman', 'pso', 'hybrid']
    method_names = ['递推最小二乘', 'Kalman滤波', '粒子群优化', '混合算法']
    
    metrics = {
        'method_performance': {},
        'channel_performance': {},
        'overall_improvement': {}
    }
    
    # 各方法性能统计
    for method, method_name in zip(methods, method_names):
        total_scores = []
        accuracy_scores = []
        convergence_times = []
        final_errors = []
        
        for channel in channels:
            result = results[channel][method]['result']
            total_scores.append(result['total_score'])
            accuracy_scores.append(result['accuracy_score'])
            convergence_times.append(result['convergence_time'])
            final_errors.append(result['final_error'])
        
        metrics['method_performance'][method] = {
            'method_name': method_name,
            'average_total_score': float(np.mean(total_scores)),
            'average_accuracy_score': float(np.mean(accuracy_scores)),
            'average_convergence_time': float(np.mean(convergence_times)),
            'average_final_error': float(np.mean(final_errors)),
            'std_total_score': float(np.std(total_scores)),
            'best_channel': channels[np.argmax(total_scores)],
            'worst_channel': channels[np.argmin(total_scores)]
        }
    
    # 各渠道性能统计
    for channel in channels:
        channel_scores = []
        best_method = None
        best_score = 0
        
        for method in methods:
            score = results[channel][method]['result']['total_score']
            channel_scores.append(score)
            if score > best_score:
                best_score = score
                best_method = method
        
        metrics['channel_performance'][channel] = {
            'best_method': best_method,
            'best_score': float(best_score),
            'score_variance': float(np.var(channel_scores)),
            'improvement_potential': float(best_score - np.min(channel_scores))
        }
    
    # 整体改进评估
    best_method_overall = max(methods, 
                             key=lambda m: metrics['method_performance'][m]['average_total_score'])
    
    best_avg_score = metrics['method_performance'][best_method_overall]['average_total_score']
    best_avg_error = metrics['method_performance'][best_method_overall]['average_final_error']
    best_avg_time = metrics['method_performance'][best_method_overall]['average_convergence_time']
    
    metrics['overall_improvement'] = {
        'best_method': best_method_overall,
        'best_method_name': metrics['method_performance'][best_method_overall]['method_name'],
        'best_average_score': float(best_avg_score),
        'best_average_error': float(best_avg_error),
        'best_average_convergence_time': float(best_avg_time),
        'improvement_grade': 'excellent' if best_avg_score > 0.8 else
                           'good' if best_avg_score > 0.6 else
                           'satisfactory' if best_avg_score > 0.4 else
                           'needs_improvement'
    }
    
    return metrics

def generate_advanced_report(results, metrics):
    """
    生成先进算法分析报告
    """
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'algorithm_comparison': {
            'tested_methods': [
                '递推最小二乘(RLS)',
                'Kalman滤波',
                '粒子群优化(PSO)',
                '混合自适应算法'
            ],
            'performance_metrics': metrics
        },
        'key_findings': {},
        'recommendations': []
    }
    
    # 关键发现
    best_method = metrics['overall_improvement']['best_method']
    best_method_name = metrics['overall_improvement']['best_method_name']
    
    report['key_findings'] = {
        'best_overall_method': {
            'method': best_method_name,
            'average_score': metrics['overall_improvement']['best_average_score'],
            'average_error': metrics['overall_improvement']['best_average_error'],
            'average_convergence_time': metrics['overall_improvement']['best_average_convergence_time']
        },
        'method_ranking': [],
        'channel_analysis': {}
    }
    
    # 方法排名
    methods = ['rls', 'kalman', 'pso', 'hybrid']
    method_scores = [(method, metrics['method_performance'][method]['average_total_score']) 
                    for method in methods]
    method_scores.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (method, score) in enumerate(method_scores, 1):
        method_name = metrics['method_performance'][method]['method_name']
        report['key_findings']['method_ranking'].append({
            'rank': rank,
            'method': method_name,
            'score': score
        })
    
    # 渠道分析
    channels = list(results.keys())
    for channel in channels:
        channel_metrics = metrics['channel_performance'][channel]
        best_method_for_channel = channel_metrics['best_method']
        best_method_name_for_channel = metrics['method_performance'][best_method_for_channel]['method_name']
        
        report['key_findings']['channel_analysis'][channel] = {
            'best_method': best_method_name_for_channel,
            'best_score': channel_metrics['best_score'],
            'improvement_potential': channel_metrics['improvement_potential']
        }
    
    # 生成建议
    improvement_grade = metrics['overall_improvement']['improvement_grade']
    
    if improvement_grade == 'excellent':
        report['recommendations'].extend([
            f'推荐使用{best_method_name}作为主要辨识算法',
            '当前算法性能优秀，可直接应用于实际系统',
            '建议进行长期稳定性测试',
            '可考虑针对特定渠道进行算法微调'
        ])
    elif improvement_grade == 'good':
        report['recommendations'].extend([
            f'{best_method_name}表现良好，建议作为首选方案',
            '可进一步优化算法参数以提升性能',
            '建议增加更多测试场景验证鲁棒性',
            '考虑实施自适应参数调整机制'
        ])
    else:
        report['recommendations'].extend([
            '需要进一步改进算法设计',
            '建议结合多种算法的优势',
            '增加更强的自适应机制',
            '考虑引入机器学习方法'
        ])
    
    return report

def main():
    """
    主函数
    """
    print("开始先进自适应辨识算法比较分析...")
    
    # 比较不同辨识方法
    print("比较不同辨识方法...")
    results = compare_identification_methods()
    
    # 绘制比较结果
    print("绘制比较结果...")
    plot_method_comparison(results)
    
    # 计算改进指标
    print("计算改进指标...")
    metrics = calculate_improvement_metrics(results)
    
    # 生成分析报告
    print("生成分析报告...")
    report = generate_advanced_report(results, metrics)
    
    # 保存结果
    os.makedirs('experiment_results', exist_ok=True)
    
    # 保存指标
    with open('experiment_results/advanced_identification_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # 保存报告
    with open('experiment_results/advanced_identification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    best_method_name = metrics['overall_improvement']['best_method_name']
    best_score = metrics['overall_improvement']['best_average_score']
    
    markdown_report = f"""
# 先进自适应参数辨识算法分析报告

## 测试算法

1. **递推最小二乘(RLS)**
   - 遗忘因子自适应调整
   - 协方差矩阵更新
   - 适用于时变参数

2. **Kalman滤波**
   - 状态空间建模
   - 噪声自适应估计
   - 最优线性估计

3. **粒子群优化(PSO)**
   - 全局优化能力
   - 参数自适应调整
   - 避免局部最优

4. **混合自适应算法**
   - 多算法融合
   - 权重自适应分配
   - 综合各算法优势

## 性能比较结果

### 最佳算法
- **推荐算法**: {best_method_name}
- **平均评分**: {best_score:.3f}
- **改进等级**: {metrics['overall_improvement']['improvement_grade']}

### 算法排名
"""
    
    for item in report['key_findings']['method_ranking']:
        markdown_report += f"{item['rank']}. {item['method']}: {item['score']:.3f}\n"
    
    markdown_report += f"""

### 各渠道最佳算法

"""
    
    for channel, analysis in report['key_findings']['channel_analysis'].items():
        markdown_report += f"- **{channel}**: {analysis['best_method']} (评分: {analysis['best_score']:.3f})\n"
    
    markdown_report += f"""

## 改进建议

"""
    for i, recommendation in enumerate(report['recommendations'], 1):
        markdown_report += f"{i}. {recommendation}\n"
    
    with open('experiment_results/advanced_identification_report.md', 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print("\n=== 先进自适应辨识算法分析完成 ===")
    print(f"分析结果已保存到 experiment_results 目录")
    print(f"\n主要结果:")
    print(f"- 最佳算法: {best_method_name}")
    print(f"- 平均评分: {best_score:.3f}")
    print(f"- 改进等级: {metrics['overall_improvement']['improvement_grade']}")
    
    return results, metrics, report

if __name__ == "__main__":
    results, metrics, report = main()