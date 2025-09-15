#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鲁棒性验证脚本
测试参数辨识算法在不同工况下的性能表现
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
from scipy import signal
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class RobustnessValidator:
    """鲁棒性验证器"""
    
    def __init__(self, num_channels=3, simulation_time=1000):
        self.num_channels = num_channels
        self.simulation_time = simulation_time
        self.dt = 0.1
        self.time = np.arange(0, simulation_time, self.dt)
        
        # 不同工况参数
        self.test_scenarios = {
            'nominal': {'noise_level': 0.01, 'disturbance_level': 0.0, 'parameter_drift': 0.0},
            'high_noise': {'noise_level': 0.1, 'disturbance_level': 0.0, 'parameter_drift': 0.0},
            'with_disturbance': {'noise_level': 0.01, 'disturbance_level': 0.5, 'parameter_drift': 0.0},
            'parameter_drift': {'noise_level': 0.01, 'disturbance_level': 0.0, 'parameter_drift': 0.2},
            'extreme_conditions': {'noise_level': 0.2, 'disturbance_level': 1.0, 'parameter_drift': 0.3}
        }
        
        # 真实参数
        self.true_params = {
            'Channel_1': {'Ki': 0.8, 'delay': 2.0},
            'Channel_2': {'Ki': 1.2, 'delay': 1.5},
            'Channel_3': {'Ki': 1.0, 'delay': 2.5}
        }
        
        self.results = {}
        
    def generate_system_response(self, channel_id, scenario_params):
        """生成系统响应数据"""
        true_Ki = self.true_params[channel_id]['Ki']
        true_delay = self.true_params[channel_id]['delay']
        
        # 参数漂移
        if scenario_params['parameter_drift'] > 0:
            drift_factor = 1 + scenario_params['parameter_drift'] * np.sin(0.01 * self.time)
            Ki_actual = true_Ki * drift_factor
            delay_actual = true_delay * (1 + 0.1 * scenario_params['parameter_drift'] * np.cos(0.005 * self.time))
        else:
            Ki_actual = true_Ki * np.ones_like(self.time)
            delay_actual = true_delay * np.ones_like(self.time)
        
        # 输入信号（多频率激励）
        u = (0.5 * np.sin(0.1 * self.time) + 
             0.3 * np.sin(0.05 * self.time) + 
             0.2 * np.random.randn(len(self.time)))
        
        # 系统响应（积分+时滞）
        y = np.zeros_like(self.time)
        for i in range(len(self.time)):
            if i > int(delay_actual[i] / self.dt):
                delay_idx = int(delay_actual[i] / self.dt)
                # 积分响应
                y[i] = Ki_actual[i] * np.trapz(u[max(0, i-delay_idx-50):i-delay_idx], 
                                               dx=self.dt) if i > delay_idx + 50 else 0
        
        # 添加扰动
        if scenario_params['disturbance_level'] > 0:
            disturbance = scenario_params['disturbance_level'] * np.random.randn(len(self.time))
            y += disturbance
        
        # 添加噪声
        noise = scenario_params['noise_level'] * np.random.randn(len(self.time))
        y_noisy = y + noise
        
        return u, y_noisy, Ki_actual, delay_actual
    
    def kalman_identification(self, u, y, channel_id):
        """Kalman滤波参数辨识"""
        # 状态向量: [Ki, delay]
        x = np.array([1.0, 2.0])  # 初始估计
        P = np.eye(2) * 10  # 初始协方差
        Q = np.eye(2) * 0.01  # 过程噪声
        R = 0.1  # 观测噪声
        
        Ki_est = []
        delay_est = []
        
        for k in range(50, len(y)):
            # 预测步
            x_pred = x
            P_pred = P + Q
            
            # 构造观测模型
            if k > int(x[1] / self.dt) + 10:
                delay_idx = int(x[1] / self.dt)
                h_k = np.trapz(u[max(0, k-delay_idx-10):k-delay_idx], dx=self.dt)
                H = np.array([h_k, 0])  # 观测矩阵
                
                # 更新步
                if abs(h_k) > 1e-6:
                    y_pred = x[0] * h_k
                    innovation = y[k] - y_pred
                    S = H @ P_pred @ H.T + R
                    K = P_pred @ H.T / S
                    
                    x = x_pred + K * innovation
                    P = (np.eye(2) - np.outer(K, H)) @ P_pred
                    
                    # 约束参数范围
                    x[0] = np.clip(x[0], 0.1, 5.0)  # Ki
                    x[1] = np.clip(x[1], 0.5, 10.0)  # delay
            
            Ki_est.append(x[0])
            delay_est.append(x[1])
        
        return np.array(Ki_est), np.array(delay_est)
    
    def evaluate_robustness(self, scenario, channel_id, Ki_est, delay_est, Ki_true, delay_true):
        """评估鲁棒性指标"""
        # 最终误差
        final_Ki_error = abs(Ki_est[-1] - Ki_true[-1]) / Ki_true[-1]
        final_delay_error = abs(delay_est[-1] - delay_true[-1]) / delay_true[-1]
        
        # 收敛性（方差）
        Ki_variance = np.var(Ki_est[-100:]) if len(Ki_est) > 100 else np.var(Ki_est)
        delay_variance = np.var(delay_est[-100:]) if len(delay_est) > 100 else np.var(delay_est)
        
        # 稳定性（最大偏差）
        Ki_max_deviation = np.max(np.abs(Ki_est - Ki_true[-len(Ki_est):]))
        delay_max_deviation = np.max(np.abs(delay_est - delay_true[-len(delay_est):]))
        
        # 综合鲁棒性评分
        robustness_score = 1.0 / (1.0 + final_Ki_error + final_delay_error + 
                                  Ki_variance + delay_variance + 
                                  Ki_max_deviation + delay_max_deviation)
        
        return {
            'final_Ki_error': final_Ki_error,
            'final_delay_error': final_delay_error,
            'Ki_variance': Ki_variance,
            'delay_variance': delay_variance,
            'Ki_max_deviation': Ki_max_deviation,
            'delay_max_deviation': delay_max_deviation,
            'robustness_score': robustness_score
        }
    
    def run_robustness_tests(self):
        """运行鲁棒性测试"""
        print("开始鲁棒性验证测试...")
        
        for scenario_name, scenario_params in self.test_scenarios.items():
            print(f"\n测试场景: {scenario_name}")
            self.results[scenario_name] = {}
            
            for channel_id in [f'Channel_{i+1}' for i in range(self.num_channels)]:
                print(f"  处理 {channel_id}...")
                
                # 生成系统响应
                u, y, Ki_true, delay_true = self.generate_system_response(channel_id, scenario_params)
                
                # 参数辨识
                Ki_est, delay_est = self.kalman_identification(u, y, channel_id)
                
                # 评估鲁棒性
                robustness_metrics = self.evaluate_robustness(
                    scenario_name, channel_id, Ki_est, delay_est, Ki_true, delay_true
                )
                
                self.results[scenario_name][channel_id] = {
                    'input': u.tolist(),
                    'output': y.tolist(),
                    'Ki_true': Ki_true.tolist(),
                    'delay_true': delay_true.tolist(),
                    'Ki_estimated': Ki_est.tolist(),
                    'delay_estimated': delay_est.tolist(),
                    'robustness_metrics': robustness_metrics,
                    'scenario_params': scenario_params
                }
        
        print("\n鲁棒性验证测试完成！")
    
    def plot_robustness_results(self):
        """绘制鲁棒性测试结果"""
        # 创建结果目录
        os.makedirs('experiment_results', exist_ok=True)
        
        # 1. 不同场景下的鲁棒性评分对比
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('参数辨识算法鲁棒性验证结果', fontsize=16, fontweight='bold')
        
        # 鲁棒性评分对比
        scenarios = list(self.test_scenarios.keys())
        channels = [f'Channel_{i+1}' for i in range(self.num_channels)]
        
        robustness_scores = np.zeros((len(scenarios), len(channels)))
        for i, scenario in enumerate(scenarios):
            for j, channel in enumerate(channels):
                robustness_scores[i, j] = self.results[scenario][channel]['robustness_metrics']['robustness_score']
        
        im = axes[0, 0].imshow(robustness_scores, cmap='RdYlGn', aspect='auto')
        axes[0, 0].set_xticks(range(len(channels)))
        axes[0, 0].set_xticklabels(channels)
        axes[0, 0].set_yticks(range(len(scenarios)))
        axes[0, 0].set_yticklabels(scenarios)
        axes[0, 0].set_title('鲁棒性评分热力图')
        plt.colorbar(im, ax=axes[0, 0])
        
        # 在热力图上添加数值
        for i in range(len(scenarios)):
            for j in range(len(channels)):
                axes[0, 0].text(j, i, f'{robustness_scores[i, j]:.3f}', 
                               ha='center', va='center', fontweight='bold')
        
        # 平均鲁棒性评分
        avg_scores = np.mean(robustness_scores, axis=1)
        axes[0, 1].bar(scenarios, avg_scores, color=['green', 'orange', 'red', 'purple', 'brown'])
        axes[0, 1].set_title('各场景平均鲁棒性评分')
        axes[0, 1].set_ylabel('鲁棒性评分')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 误差分析
        Ki_errors = []
        delay_errors = []
        for scenario in scenarios:
            Ki_err = np.mean([self.results[scenario][ch]['robustness_metrics']['final_Ki_error'] 
                             for ch in channels])
            delay_err = np.mean([self.results[scenario][ch]['robustness_metrics']['final_delay_error'] 
                                for ch in channels])
            Ki_errors.append(Ki_err)
            delay_errors.append(delay_err)
        
        x = np.arange(len(scenarios))
        width = 0.35
        axes[1, 0].bar(x - width/2, Ki_errors, width, label='积分系数误差', alpha=0.8)
        axes[1, 0].bar(x + width/2, delay_errors, width, label='时滞误差', alpha=0.8)
        axes[1, 0].set_title('各场景参数辨识误差对比')
        axes[1, 0].set_ylabel('相对误差')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(scenarios, rotation=45)
        axes[1, 0].legend()
        
        # 稳定性分析
        Ki_variances = []
        delay_variances = []
        for scenario in scenarios:
            Ki_var = np.mean([self.results[scenario][ch]['robustness_metrics']['Ki_variance'] 
                             for ch in channels])
            delay_var = np.mean([self.results[scenario][ch]['robustness_metrics']['delay_variance'] 
                                for ch in channels])
            Ki_variances.append(Ki_var)
            delay_variances.append(delay_var)
        
        axes[1, 1].bar(x - width/2, Ki_variances, width, label='积分系数方差', alpha=0.8)
        axes[1, 1].bar(x + width/2, delay_variances, width, label='时滞方差', alpha=0.8)
        axes[1, 1].set_title('各场景参数估计稳定性对比')
        axes[1, 1].set_ylabel('方差')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(scenarios, rotation=45)
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('experiment_results/robustness_validation_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 2. 典型场景的参数辨识过程
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('典型场景下的参数辨识过程', fontsize=16, fontweight='bold')
        
        test_scenarios = ['nominal', 'high_noise', 'extreme_conditions']
        for i, scenario in enumerate(test_scenarios):
            for j, channel in enumerate(channels):
                if j < 2:  # 只显示前两个渠道
                    Ki_est = self.results[scenario][channel]['Ki_estimated']
                    delay_est = self.results[scenario][channel]['delay_estimated']
                    Ki_true = self.results[scenario][channel]['Ki_true'][-len(Ki_est):]
                    delay_true = self.results[scenario][channel]['delay_true'][-len(delay_est):]
                    
                    time_est = self.time[50:50+len(Ki_est)]
                    
                    # 积分系数
                    axes[j, i].plot(time_est, Ki_true, 'g-', label='真实值', linewidth=2)
                    axes[j, i].plot(time_est, Ki_est, 'r--', label='估计值', linewidth=2)
                    axes[j, i].set_title(f'{scenario} - {channel} - 积分系数')
                    axes[j, i].set_ylabel('Ki')
                    axes[j, i].legend()
                    axes[j, i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('experiment_results/robustness_identification_process.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_robustness_report(self):
        """生成鲁棒性验证报告"""
        # 计算总体统计
        overall_stats = {}
        for scenario in self.test_scenarios.keys():
            scenario_scores = [self.results[scenario][ch]['robustness_metrics']['robustness_score'] 
                              for ch in [f'Channel_{i+1}' for i in range(self.num_channels)]]
            overall_stats[scenario] = {
                'average_robustness_score': np.mean(scenario_scores),
                'std_robustness_score': np.std(scenario_scores),
                'min_robustness_score': np.min(scenario_scores),
                'max_robustness_score': np.max(scenario_scores)
            }
        
        # 找出最佳和最差场景
        best_scenario = max(overall_stats.keys(), 
                           key=lambda x: overall_stats[x]['average_robustness_score'])
        worst_scenario = min(overall_stats.keys(), 
                            key=lambda x: overall_stats[x]['average_robustness_score'])
        
        # 生成报告
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'test_configuration': {
                'num_channels': self.num_channels,
                'simulation_time': self.simulation_time,
                'test_scenarios': self.test_scenarios
            },
            'overall_statistics': overall_stats,
            'detailed_results': self.results,
            'key_findings': {
                'best_scenario': {
                    'name': best_scenario,
                    'average_score': overall_stats[best_scenario]['average_robustness_score']
                },
                'worst_scenario': {
                    'name': worst_scenario,
                    'average_score': overall_stats[worst_scenario]['average_robustness_score']
                },
                'robustness_grade': self._assess_robustness_grade(overall_stats)
            },
            'recommendations': self._generate_recommendations(overall_stats)
        }
        
        # 保存报告
        os.makedirs('experiment_results', exist_ok=True)
        with open('experiment_results/robustness_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def _assess_robustness_grade(self, stats):
        """评估鲁棒性等级"""
        avg_score = np.mean([stats[scenario]['average_robustness_score'] 
                            for scenario in stats.keys()])
        
        if avg_score >= 0.8:
            return 'excellent'
        elif avg_score >= 0.6:
            return 'good'
        elif avg_score >= 0.4:
            return 'satisfactory'
        elif avg_score >= 0.2:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def _generate_recommendations(self, stats):
        """生成改进建议"""
        avg_score = np.mean([stats[scenario]['average_robustness_score'] 
                            for scenario in stats.keys()])
        
        recommendations = []
        
        if avg_score < 0.6:
            recommendations.append("需要增强算法的鲁棒性设计")
            recommendations.append("建议采用更强的噪声抑制机制")
        
        if stats['high_noise']['average_robustness_score'] < 0.4:
            recommendations.append("在高噪声环境下性能不佳，需要改进滤波算法")
        
        if stats['parameter_drift']['average_robustness_score'] < 0.4:
            recommendations.append("对参数漂移的适应性不足，建议增加自适应跟踪机制")
        
        if stats['extreme_conditions']['average_robustness_score'] < 0.3:
            recommendations.append("极端条件下性能严重下降，需要设计更鲁棒的算法")
        
        recommendations.append("建议结合多种辨识算法以提高整体鲁棒性")
        
        return recommendations

def main():
    """主函数"""
    print("=" * 60)
    print("参数辨识算法鲁棒性验证")
    print("=" * 60)
    
    # 创建验证器
    validator = RobustnessValidator(num_channels=3, simulation_time=1000)
    
    # 运行鲁棒性测试
    validator.run_robustness_tests()
    
    # 绘制结果
    validator.plot_robustness_results()
    
    # 生成报告
    report = validator.generate_robustness_report()
    
    # 显示关键结果
    print("\n=== 鲁棒性验证结果摘要 ===")
    print(f"最佳场景: {report['key_findings']['best_scenario']['name']} "
          f"(评分: {report['key_findings']['best_scenario']['average_score']:.3f})")
    print(f"最差场景: {report['key_findings']['worst_scenario']['name']} "
          f"(评分: {report['key_findings']['worst_scenario']['average_score']:.3f})")
    print(f"整体鲁棒性等级: {report['key_findings']['robustness_grade']}")
    
    print("\n=== 改进建议 ===")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print(f"\n详细结果已保存到 experiment_results/ 目录")
    print("鲁棒性验证完成！")

if __name__ == "__main__":
    main()