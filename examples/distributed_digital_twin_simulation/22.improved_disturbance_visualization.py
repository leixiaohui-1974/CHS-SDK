#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的干扰组合可视化脚本
专门优化"无干扰"数据的显示效果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ImprovedDisturbanceVisualizer:
    def __init__(self, data_dir="experiment_results"):
        self.data_dir = Path(data_dir)
        self.scenarios = ['normal_operation', 'rainfall_disturbance', 'extreme_disturbance']
        self.modes = ['rule', 'mpc']
        
        # 定义干扰组合（与原脚本保持一致）
        self.disturbance_combinations = {
            'no_disturbance': {
                'label': '无干扰',
                'sensor_noise': 0.0,
                'actuator_noise': 0.0,
                'color': '#2E8B57',  # 深绿色，突出显示
                'alpha': 1.0,
                'linewidth': 3
            },
            'sensor_only': {
                'label': '仅传感器干扰',
                'sensor_noise': 0.05,
                'actuator_noise': 0.0,
                'color': '#4169E1',  # 蓝色
                'alpha': 0.8,
                'linewidth': 2
            },
            'actuator_only': {
                'label': '仅执行器干扰',
                'sensor_noise': 0.0,
                'actuator_noise': 0.02,
                'color': '#FF6347',  # 橙红色
                'alpha': 0.8,
                'linewidth': 2
            },
            'both_disturbances': {
                'label': '传感器+执行器干扰',
                'sensor_noise': 0.05,
                'actuator_noise': 0.02,
                'color': '#8B0000',  # 深红色
                'alpha': 0.8,
                'linewidth': 2
            }
        }
    
    def load_data(self, mode, scenario):
        """加载数据"""
        file_path = self.data_dir / f"{mode}_{scenario}_data.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        return None
    
    def simulate_disturbance_combinations(self, data, combo_key):
        """模拟干扰组合"""
        combo_info = self.disturbance_combinations[combo_key]
        disturbed_data = data.copy()
        
        # 添加传感器干扰
        if combo_info['sensor_noise'] > 0:
            for gate in ['1', '2', '3']:
                level_col = f'gate_{gate}_level'
                if level_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['sensor_noise'], len(disturbed_data))
                    disturbed_data[level_col] += noise
        
        # 添加执行器干扰
        if combo_info['actuator_noise'] > 0:
            for gate in ['1', '2', '3']:
                opening_col = f'gate_{gate}_opening'
                if opening_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['actuator_noise'], len(disturbed_data))
                    disturbed_data[opening_col] = np.clip(disturbed_data[opening_col] + noise, 0, 1)
        
        return disturbed_data
    
    def calculate_performance_metrics(self, data):
        """计算性能指标"""
        metrics = {}
        
        for gate in ['1', '2', '3']:
            level_col = f'gate_{gate}_level'
            target_col = f'gate_{gate}_target_level'
            opening_col = f'gate_{gate}_opening'
            
            if level_col in data.columns and target_col in data.columns:
                level_data = data[level_col].values
                target_data = data[target_col].values
                level_error = level_data - target_data
                
                mae = np.mean(np.abs(level_error))
                rmse = np.sqrt(np.mean(level_error**2))
                max_error = np.max(np.abs(level_error))
                level_stability = np.std(level_data)
                
                metrics[f'gate_{gate}'] = {
                    'mae': mae,
                    'rmse': rmse,
                    'max_error': max_error,
                    'level_stability': level_stability
                }
            
            if opening_col in data.columns:
                opening_data = data[opening_col].values
                opening_variation = np.std(opening_data)
                
                if f'gate_{gate}' not in metrics:
                    metrics[f'gate_{gate}'] = {}
                
                metrics[f'gate_{gate}']['opening_variation'] = opening_variation
        
        # 系统整体性能
        all_mae = [metrics[f'gate_{g}']['mae'] for g in ['1', '2', '3'] 
                  if f'gate_{g}' in metrics and 'mae' in metrics[f'gate_{g}']]
        all_rmse = [metrics[f'gate_{g}']['rmse'] for g in ['1', '2', '3'] 
                   if f'gate_{g}' in metrics and 'rmse' in metrics[f'gate_{g}']]
        
        metrics['system'] = {
            'overall_mae': np.mean(all_mae) if all_mae else 0,
            'overall_rmse': np.mean(all_rmse) if all_rmse else 0,
            'performance_index': np.mean(all_mae) if all_mae else 0
        }
        
        return metrics
    
    def create_enhanced_comparison_plot(self, results, scenario):
        """创建增强的对比图，突出显示无干扰数据"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'干扰组合性能对比（增强版）- {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        combinations = list(self.disturbance_combinations.keys())
        combination_labels = [self.disturbance_combinations[k]['label'] for k in combinations]
        
        # 定义要绘制的指标
        metrics_to_plot = [
            ('overall_mae', '整体平均绝对误差 (m)', axes[0, 0]),
            ('overall_rmse', '整体均方根误差 (m)', axes[0, 1]),
            ('performance_index', '综合性能指数', axes[1, 0])
        ]
        
        for metric_key, metric_label, ax in metrics_to_plot:
            rule_values = []
            mpc_values = []
            colors = []
            alphas = []
            
            for combo_key in combinations:
                combo_info = self.disturbance_combinations[combo_key]
                colors.append(combo_info['color'])
                alphas.append(combo_info['alpha'])
                
                if 'rule' in results and combo_key in results['rule']:
                    rule_values.append(results['rule'][combo_key]['metrics']['system'][metric_key])
                else:
                    rule_values.append(0)
                
                if 'mpc' in results and combo_key in results['mpc']:
                    mpc_values.append(results['mpc'][combo_key]['metrics']['system'][metric_key])
                else:
                    mpc_values.append(0)
            
            x_pos = np.arange(len(combinations))
            width = 0.35
            
            # 绘制柱状图，为无干扰使用特殊样式
            for i, (combo_key, label) in enumerate(zip(combinations, combination_labels)):
                combo_info = self.disturbance_combinations[combo_key]
                
                # 特殊处理无干扰情况
                if combo_key == 'no_disturbance':
                    # 使用更粗的边框和特殊填充
                    rule_bar = ax.bar(x_pos[i] - width/2, rule_values[i], width, 
                                     color=combo_info['color'], alpha=combo_info['alpha'],
                                     edgecolor='black', linewidth=3, 
                                     label='Rule模式' if i == 0 else "",
                                     hatch='///')
                    mpc_bar = ax.bar(x_pos[i] + width/2, mpc_values[i], width, 
                                    color=combo_info['color'], alpha=combo_info['alpha']-0.2,
                                    edgecolor='black', linewidth=3,
                                    label='MPC模式' if i == 0 else "",
                                    hatch='...')
                else:
                    rule_bar = ax.bar(x_pos[i] - width/2, rule_values[i], width, 
                                     color=combo_info['color'], alpha=combo_info['alpha'],
                                     label='Rule模式' if i == 0 else "")
                    mpc_bar = ax.bar(x_pos[i] + width/2, mpc_values[i], width, 
                                    color=combo_info['color'], alpha=combo_info['alpha']-0.2,
                                    label='MPC模式' if i == 0 else "")
            
            ax.set_xlabel('干扰组合', fontsize=12, fontweight='bold')
            ax.set_ylabel(metric_label, fontsize=12, fontweight='bold')
            ax.set_title(f'{metric_label}对比', fontsize=14, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(combination_labels, rotation=45, ha='right', fontweight='bold')
            
            # 突出显示无干扰的x轴标签
            for i, (combo_key, label) in enumerate(zip(combinations, ax.get_xticklabels())):
                if combo_key == 'no_disturbance':  # 正确识别无干扰
                    label.set_color('darkgreen')
                    label.set_fontweight('bold')
                    label.set_fontsize(12)
            
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3)
            
            # 添加数值标签
            max_val = max(max(rule_values) if rule_values else 0, max(mpc_values) if mpc_values else 0)
            for i, (combo_key, rule_val, mpc_val) in enumerate(zip(combinations, rule_values, mpc_values)):
                is_no_disturbance = combo_key == 'no_disturbance'
                if rule_val >= 0:  # 改为>=0以显示0值
                    ax.text(x_pos[i] - width/2, rule_val + max_val * 0.01, 
                           f'{rule_val:.4f}', ha='center', va='bottom', 
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=10 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black')
                if mpc_val >= 0:  # 改为>=0以显示0值
                    ax.text(x_pos[i] + width/2, mpc_val + max_val * 0.01, 
                           f'{mpc_val:.4f}', ha='center', va='bottom',
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=10 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black')
        
        # 在第四个子图中添加说明
        ax = axes[1, 1]
        ax.axis('off')
        
        # 创建图例说明
        legend_text = [
            "图例说明:",
            "• 无干扰（绿色，斜线填充）：基准性能",
            "• 仅传感器干扰（蓝色）：测量噪声影响", 
            "• 仅执行器干扰（橙红色）：控制噪声影响",
            "• 传感器+执行器干扰（深红色）：复合影响",
            "",
            "注意事项:",
            "• 无干扰数据使用粗边框和特殊填充突出显示",
            "• 数值越小表示性能越好",
            "• MPC模式通常比Rule模式更稳定"
        ]
        
        for i, text in enumerate(legend_text):
            ax.text(0.05, 0.9 - i * 0.08, text, transform=ax.transAxes, 
                   fontsize=11, fontweight='bold' if i == 0 or i == 6 else 'normal',
                   color='darkgreen' if '无干扰' in text else 'black')
        
        plt.tight_layout()
        output_file = self.data_dir / f"enhanced_disturbance_comparison_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"已生成增强对比图: {output_file}")
    
    def run_enhanced_analysis(self):
        """运行增强分析"""
        print("开始增强干扰组合分析...")
        
        for scenario in self.scenarios:
            print(f"\n分析场景: {scenario}")
            scenario_results = {}
            
            for mode in self.modes:
                print(f"  分析模式: {mode}")
                original_data = self.load_data(mode, scenario)
                
                if original_data is None:
                    continue
                
                mode_results = {}
                
                for combo_key, combo_info in self.disturbance_combinations.items():
                    print(f"    分析组合: {combo_info['label']}")
                    
                    # 模拟干扰组合
                    disturbed_data = self.simulate_disturbance_combinations(original_data, combo_key)
                    
                    # 计算性能指标
                    metrics = self.calculate_performance_metrics(disturbed_data)
                    
                    mode_results[combo_key] = {
                        'metrics': metrics,
                        'label': combo_info['label']
                    }
                
                scenario_results[mode] = mode_results
            
            # 创建增强对比图
            self.create_enhanced_comparison_plot(scenario_results, scenario)
        
        print("\n增强分析完成！")
        print("已生成突出显示无干扰数据的增强对比图。")

if __name__ == "__main__":
    visualizer = ImprovedDisturbanceVisualizer()
    visualizer.run_enhanced_analysis()