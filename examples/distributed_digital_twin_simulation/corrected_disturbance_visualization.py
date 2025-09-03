#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版干扰组合可视化分析
使用正确的列名和性能指标
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

class CorrectedDisturbanceVisualizer:
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
            print(f"  列名: {list(data.columns)}")
            return data
        else:
            print(f"  警告: 文件不存在 {file_path}")
            return None
    
    def simulate_disturbance_combinations(self, data, combo_key):
        """模拟干扰组合"""
        combo_info = self.disturbance_combinations[combo_key]
        disturbed_data = data.copy()
        
        print(f"    应用干扰组合: {combo_info['label']}")
        
        # 添加传感器干扰（水位测量噪声）
        if combo_info['sensor_noise'] > 0:
            for gate in [1, 2, 3]:
                level_col = f'Gate_{gate}_upstream_level'
                if level_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['sensor_noise'], len(disturbed_data))
                    original_std = disturbed_data[level_col].std()
                    disturbed_data[level_col] += noise
                    new_std = disturbed_data[level_col].std()
                    print(f"      {level_col}: 原始标准差={original_std:.4f}, 干扰后标准差={new_std:.4f}")
        
        # 添加执行器干扰（闸门开度噪声）
        if combo_info['actuator_noise'] > 0:
            for gate in [1, 2, 3]:
                opening_col = f'Gate_{gate}_opening'
                if opening_col in disturbed_data.columns:
                    noise = np.random.normal(0, combo_info['actuator_noise'], len(disturbed_data))
                    original_std = disturbed_data[opening_col].std()
                    disturbed_data[opening_col] = np.clip(disturbed_data[opening_col] + noise, 0, 1)
                    new_std = disturbed_data[opening_col].std()
                    print(f"      {opening_col}: 原始标准差={original_std:.4f}, 干扰后标准差={new_std:.4f}")
        
        return disturbed_data
    
    def calculate_performance_metrics(self, data):
        """计算性能指标"""
        metrics = {}
        
        # 目标水位（假设为初始水位）
        target_levels = {
            1: 10.0,  # Gate 1 目标水位
            2: 8.0,   # Gate 2 目标水位
            3: 6.0    # Gate 3 目标水位
        }
        
        for gate in [1, 2, 3]:
            level_col = f'Gate_{gate}_upstream_level'
            opening_col = f'Gate_{gate}_opening'
            flow_col = f'Gate_{gate}_flow'
            
            gate_metrics = {}
            
            if level_col in data.columns:
                level_data = data[level_col].values
                target_level = target_levels[gate]
                
                # 水位控制误差
                level_error = level_data - target_level
                mae = np.mean(np.abs(level_error))
                rmse = np.sqrt(np.mean(level_error**2))
                max_error = np.max(np.abs(level_error))
                
                # 水位稳定性（标准差）
                level_stability = np.std(level_data)
                
                gate_metrics.update({
                    'mae': mae,
                    'rmse': rmse,
                    'max_error': max_error,
                    'level_stability': level_stability
                })
                
                print(f"      Gate_{gate}: MAE={mae:.6f}, RMSE={rmse:.6f}, 稳定性={level_stability:.6f}")
            
            if opening_col in data.columns:
                opening_data = data[opening_col].values
                opening_variation = np.std(opening_data)
                gate_metrics['opening_variation'] = opening_variation
                print(f"      Gate_{gate}_opening: 变化度={opening_variation:.6f}")
            
            if flow_col in data.columns:
                flow_data = data[flow_col].values
                flow_stability = np.std(flow_data)
                gate_metrics['flow_stability'] = flow_stability
                print(f"      Gate_{gate}_flow: 流量稳定性={flow_stability:.6f}")
            
            metrics[f'gate_{gate}'] = gate_metrics
        
        # 系统整体性能
        all_mae = [metrics[f'gate_{g}']['mae'] for g in [1, 2, 3] 
                  if f'gate_{g}' in metrics and 'mae' in metrics[f'gate_{g}']]
        all_rmse = [metrics[f'gate_{g}']['rmse'] for g in [1, 2, 3] 
                   if f'gate_{g}' in metrics and 'rmse' in metrics[f'gate_{g}']]
        all_stability = [metrics[f'gate_{g}']['level_stability'] for g in [1, 2, 3] 
                        if f'gate_{g}' in metrics and 'level_stability' in metrics[f'gate_{g}']]
        all_opening_var = [metrics[f'gate_{g}']['opening_variation'] for g in [1, 2, 3] 
                          if f'gate_{g}' in metrics and 'opening_variation' in metrics[f'gate_{g}']]
        
        overall_mae = np.mean(all_mae) if all_mae else 0
        overall_rmse = np.mean(all_rmse) if all_rmse else 0
        overall_stability = np.mean(all_stability) if all_stability else 0
        overall_opening_var = np.mean(all_opening_var) if all_opening_var else 0
        
        # 综合性能指数（越小越好）
        performance_index = overall_mae + overall_stability * 0.5 + overall_opening_var * 0.3
        
        print(f"      系统整体: MAE={overall_mae:.6f}, RMSE={overall_rmse:.6f}, 综合指数={performance_index:.6f}")
        
        metrics['system'] = {
            'overall_mae': overall_mae,
            'overall_rmse': overall_rmse,
            'overall_stability': overall_stability,
            'overall_opening_variation': overall_opening_var,
            'performance_index': performance_index
        }
        
        return metrics
    
    def create_corrected_comparison_plot(self, results, scenario):
        """创建修正的对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'干扰组合性能对比（修正版）- {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        combinations = list(self.disturbance_combinations.keys())
        combination_labels = [self.disturbance_combinations[k]['label'] for k in combinations]
        
        # 定义要绘制的指标
        metrics_to_plot = [
            ('overall_mae', '整体平均绝对误差 (m)', axes[0, 0]),
            ('overall_stability', '整体水位稳定性 (m)', axes[0, 1]),
            ('overall_opening_variation', '整体开度变化度', axes[1, 0]),
            ('performance_index', '综合性能指数', axes[1, 1])
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
            max_val = max(max(rule_values) if rule_values else 0, 
                         max(mpc_values) if mpc_values else 0)
            min_visible_height = max_val * 0.01 if max_val > 0 else 0.001
            
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
            if max_val == 0:
                max_val = min_visible_height * 10
            
            for i, (combo_key, rule_val, mpc_val) in enumerate(zip(combinations, rule_values, mpc_values)):
                is_no_disturbance = combo_key == 'no_disturbance'
                
                # 显示实际值
                if rule_val >= 0:
                    display_height = max(rule_val, min_visible_height)
                    ax.text(x_pos[i] - width/2, display_height + max_val * 0.02, 
                           f'{rule_val:.4f}', ha='center', va='bottom', 
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=9 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black',
                           rotation=90 if rule_val < max_val * 0.1 else 0)
                
                if mpc_val >= 0:
                    display_height = max(mpc_val, min_visible_height)
                    ax.text(x_pos[i] + width/2, display_height + max_val * 0.02, 
                           f'{mpc_val:.4f}', ha='center', va='bottom',
                           fontweight='bold' if is_no_disturbance else 'normal',
                           fontsize=9 if is_no_disturbance else 8,
                           color='darkgreen' if is_no_disturbance else 'black',
                           rotation=90 if mpc_val < max_val * 0.1 else 0)
        
        plt.tight_layout()
        output_file = self.data_dir / f"corrected_disturbance_comparison_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"已生成修正对比图: {output_file}")
    
    def run_corrected_analysis(self):
        """运行修正分析"""
        print("开始修正干扰组合分析...")
        
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
                print(f"\n生成 {scenario} 场景的修正对比图...")
                self.create_corrected_comparison_plot(scenario_results, scenario)
        
        print("\n修正分析完成！")

if __name__ == "__main__":
    visualizer = CorrectedDisturbanceVisualizer()
    visualizer.run_corrected_analysis()