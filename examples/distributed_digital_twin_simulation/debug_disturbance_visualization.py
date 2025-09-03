#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版干扰组合可视化分析
解决无干扰数据显示问题
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

class DebugDisturbanceVisualizer:
    def __init__(self, data_dir="experiment_results"):
        self.data_dir = Path(data_dir)
        self.scenarios = ['normal_operation', 'rainfall_disturbance', 'extreme_disturbance']
        self.modes = ['rule', 'mpc']
        
        # 定义干扰组合
        self.disturbance_combinations = {
            'no_disturbance': {
                'label': '无干扰',
                'sensor_noise': 0.0,
                'actuator_noise': 0.0,
                'color': 'darkgreen',
                'alpha': 0.8
            },
            'sensor_only': {
                'label': '仅传感器干扰',
                'sensor_noise': 0.02,
                'actuator_noise': 0.0,
                'color': 'blue',
                'alpha': 0.7
            },
            'actuator_only': {
                'label': '仅执行器干扰',
                'sensor_noise': 0.0,
                'actuator_noise': 0.05,
                'color': 'orange',
                'alpha': 0.7
            },
            'both_disturbances': {
                'label': '传感器+执行器干扰',
                'sensor_noise': 0.02,
                'actuator_noise': 0.05,
                'color': 'red',
                'alpha': 0.7
            }
        }
    
    def load_data(self, mode, scenario):
        """加载数据"""
        file_path = self.data_dir / f"{mode}_{scenario}_data.csv"
        if file_path.exists():
            data = pd.read_csv(file_path)
            print(f"  加载数据: {file_path}, 形状: {data.shape}")
            return data
        else:
            print(f"  警告: 文件不存在 {file_path}")
            return None
    
    def simulate_disturbance_combinations(self, data, combo_key):
        """模拟干扰组合"""
        combo_info = self.disturbance_combinations[combo_key]
        disturbed_data = data.copy()
        
        print(f"    应用干扰组合: {combo_info['label']}")
        print(f"    传感器噪声: {combo_info['sensor_noise']}, 执行器噪声: {combo_info['actuator_noise']}")
        
        # 添加传感器干扰
        if combo_info['sensor_noise'] > 0:
            for gate in ['1', '2', '3']:
                level_col = f'gate_{gate}_level'
                if level_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['sensor_noise'], len(disturbed_data))
                    original_mean = disturbed_data[level_col].mean()
                    disturbed_data[level_col] += noise
                    new_mean = disturbed_data[level_col].mean()
                    print(f"      {level_col}: 原始均值={original_mean:.4f}, 干扰后均值={new_mean:.4f}")
        
        # 添加执行器干扰
        if combo_info['actuator_noise'] > 0:
            for gate in ['1', '2', '3']:
                opening_col = f'gate_{gate}_opening'
                if opening_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['actuator_noise'], len(disturbed_data))
                    original_mean = disturbed_data[opening_col].mean()
                    disturbed_data[opening_col] = np.clip(disturbed_data[opening_col] + noise, 0, 1)
                    new_mean = disturbed_data[opening_col].mean()
                    print(f"      {opening_col}: 原始均值={original_mean:.4f}, 干扰后均值={new_mean:.4f}")
        
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
                
                print(f"      {gate}号闸门: MAE={mae:.6f}, RMSE={rmse:.6f}, 最大误差={max_error:.6f}")
                
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
        
        overall_mae = np.mean(all_mae) if all_mae else 0
        overall_rmse = np.mean(all_rmse) if all_rmse else 0
        
        print(f"      系统整体: MAE={overall_mae:.6f}, RMSE={overall_rmse:.6f}")
        
        metrics['system'] = {
            'overall_mae': overall_mae,
            'overall_rmse': overall_rmse,
            'performance_index': overall_mae
        }
        
        return metrics
    
    def create_debug_comparison_plot(self, results, scenario):
        """创建调试对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'干扰组合性能对比（调试版）- {scenario.replace("_", " ").title()}', 
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
            
            print(f"\n绘制指标: {metric_label}")
            
            for combo_key in combinations:
                combo_info = self.disturbance_combinations[combo_key]
                
                if 'rule' in results and combo_key in results['rule']:
                    rule_val = results['rule'][combo_key]['metrics']['system'][metric_key]
                    rule_values.append(rule_val)
                    print(f"  {combo_info['label']} - Rule: {rule_val:.6f}")
                else:
                    rule_values.append(0)
                    print(f"  {combo_info['label']} - Rule: 无数据")
                
                if 'mpc' in results and combo_key in results['mpc']:
                    mpc_val = results['mpc'][combo_key]['metrics']['system'][metric_key]
                    mpc_values.append(mpc_val)
                    print(f"  {combo_info['label']} - MPC: {mpc_val:.6f}")
                else:
                    mpc_values.append(0)
                    print(f"  {combo_info['label']} - MPC: 无数据")
            
            x_pos = np.arange(len(combinations))
            width = 0.35
            
            # 确保有可见的最小高度
            min_visible_height = max(max(rule_values) if rule_values else 0, 
                                   max(mpc_values) if mpc_values else 0) * 0.01
            if min_visible_height == 0:
                min_visible_height = 0.001  # 设置最小可见高度
            
            # 绘制柱状图
            for i, (combo_key, label) in enumerate(zip(combinations, combination_labels)):
                combo_info = self.disturbance_combinations[combo_key]
                
                # 确保值至少有最小可见高度
                rule_height = max(rule_values[i], min_visible_height) if rule_values[i] >= 0 else rule_values[i]
                mpc_height = max(mpc_values[i], min_visible_height) if mpc_values[i] >= 0 else mpc_values[i]
                
                # 特殊处理无干扰情况
                if combo_key == 'no_disturbance':
                    rule_bar = ax.bar(x_pos[i] - width/2, rule_height, width, 
                                     color=combo_info['color'], alpha=combo_info['alpha'],
                                     edgecolor='black', linewidth=3, 
                                     label='Rule模式' if i == 0 else "",
                                     hatch='///')
                    mpc_bar = ax.bar(x_pos[i] + width/2, mpc_height, width, 
                                    color=combo_info['color'], alpha=combo_info['alpha']-0.2,
                                    edgecolor='black', linewidth=3,
                                    label='MPC模式' if i == 0 else "",
                                    hatch='...')
                else:
                    rule_bar = ax.bar(x_pos[i] - width/2, rule_height, width, 
                                     color=combo_info['color'], alpha=combo_info['alpha'],
                                     label='Rule模式' if i == 0 else "")
                    mpc_bar = ax.bar(x_pos[i] + width/2, mpc_height, width, 
                                    color=combo_info['color'], alpha=combo_info['alpha']-0.2,
                                    label='MPC模式' if i == 0 else "")
            
            ax.set_xlabel('干扰组合', fontsize=12, fontweight='bold')
            ax.set_ylabel(metric_label, fontsize=12, fontweight='bold')
            ax.set_title(f'{metric_label}对比', fontsize=14, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(combination_labels, rotation=45, ha='right')
            
            # 突出显示无干扰的x轴标签
            for i, (combo_key, label) in enumerate(zip(combinations, ax.get_xticklabels())):
                if combo_key == 'no_disturbance':
                    label.set_color('darkgreen')
                    label.set_fontweight('bold')
                    label.set_fontsize(12)
            
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3)
            
            # 添加数值标签
            max_val = max(max(rule_values) if rule_values else 0, max(mpc_values) if mpc_values else 0)
            if max_val == 0:
                max_val = min_visible_height * 10
            
            for i, (combo_key, rule_val, mpc_val) in enumerate(zip(combinations, rule_values, mpc_values)):
                is_no_disturbance = combo_key == 'no_disturbance'
                
                # 显示实际值，不管多小
                if rule_val >= 0:
                    display_height = max(rule_val, min_visible_height)
                    ax.text(x_pos[i] - width/2, display_height + max_val * 0.02, 
                           f'{rule_val:.6f}', ha='center', va='bottom', 
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=9 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black',
                           rotation=90 if rule_val < max_val * 0.1 else 0)
                
                if mpc_val >= 0:
                    display_height = max(mpc_val, min_visible_height)
                    ax.text(x_pos[i] + width/2, display_height + max_val * 0.02, 
                           f'{mpc_val:.6f}', ha='center', va='bottom',
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=9 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black',
                           rotation=90 if mpc_val < max_val * 0.1 else 0)
        
        # 在第四个子图中添加说明
        ax = axes[1, 1]
        ax.axis('off')
        
        # 创建图例说明
        legend_text = [
            "调试信息:",
            "• 无干扰（绿色，斜线填充）：基准性能",
            "• 仅传感器干扰（蓝色）：测量噪声影响", 
            "• 仅执行器干扰（橙色）：控制噪声影响",
            "• 传感器+执行器干扰（红色）：复合影响",
            "",
            "注意事项:",
            "• 数值显示到6位小数以显示微小差异",
            "• 设置了最小可见高度确保所有数据可见",
            "• 无干扰数据用粗边框和特殊填充突出显示",
            "• 小数值的标签可能旋转90度以避免重叠"
        ]
        
        for i, text in enumerate(legend_text):
            ax.text(0.05, 0.9 - i * 0.08, text, transform=ax.transAxes, 
                   fontsize=10, fontweight='bold' if i == 0 or i == 6 else 'normal',
                   color='darkgreen' if '无干扰' in text else 'black')
        
        plt.tight_layout()
        output_file = self.data_dir / f"debug_disturbance_comparison_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"已生成调试对比图: {output_file}")
    
    def run_debug_analysis(self):
        """运行调试分析"""
        print("开始调试干扰组合分析...")
        
        for scenario in self.scenarios:
            print(f"\n=== 分析场景: {scenario} ===")
            scenario_results = {}
            
            for mode in self.modes:
                print(f"\n--- 分析模式: {mode} ---")
                original_data = self.load_data(mode, scenario)
                
                if original_data is None:
                    continue
                
                mode_results = {}
                
                for combo_key in self.disturbance_combinations:
                    print(f"\n  处理干扰组合: {combo_key}")
                    
                    # 应用干扰
                    disturbed_data = self.simulate_disturbance_combinations(original_data, combo_key)
                    
                    # 计算性能指标
                    metrics = self.calculate_performance_metrics(disturbed_data)
                    
                    mode_results[combo_key] = {
                        'data': disturbed_data,
                        'metrics': metrics
                    }
                
                scenario_results[mode] = mode_results
            
            # 生成对比图
            if scenario_results:
                print(f"\n生成 {scenario} 场景的调试对比图...")
                self.create_debug_comparison_plot(scenario_results, scenario)
        
        print("\n调试分析完成！")

if __name__ == "__main__":
    visualizer = DebugDisturbanceVisualizer()
    visualizer.run_debug_analysis()