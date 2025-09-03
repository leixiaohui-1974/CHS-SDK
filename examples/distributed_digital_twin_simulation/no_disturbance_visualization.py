#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无干扰情况下的控制性能对比可视化
专门展示Rule模式vs MPC模式在无传感器和执行器干扰条件下的性能差异
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_data(file_path):
    """加载数据文件"""
    try:
        data = pd.read_csv(file_path)
        print(f"成功加载数据: {file_path}, 形状: {data.shape}")
        return data
    except Exception as e:
        print(f"加载数据失败 {file_path}: {e}")
        return None

def calculate_performance_metrics(data):
    """计算性能指标"""
    metrics = {}
    
    # 获取闸门数量
    gate_columns = [col for col in data.columns if 'Gate_' in col and '_upstream_level' in col]
    num_gates = len(gate_columns)
    
    print(f"检测到 {num_gates} 个闸门")
    
    # 为每个闸门计算指标
    gate_metrics = {}
    for i in range(1, num_gates + 1):
        gate_id = f"Gate_{i}"
        
        # 水位数据
        level_col = f"{gate_id}_upstream_level"
        opening_col = f"{gate_id}_opening"
        flow_col = f"{gate_id}_flow"
        
        if level_col in data.columns:
            level_data = data[level_col].dropna()
            
            # 计算水位控制精度 (假设目标水位为数据的均值)
            target_level = level_data.mean()
            mae = np.mean(np.abs(level_data - target_level))
            rmse = np.sqrt(np.mean((level_data - target_level) ** 2))
            stability = level_data.std()  # 水位稳定性
            
            gate_metrics[gate_id] = {
                'mae': mae,
                'rmse': rmse,
                'stability': stability
            }
            
            print(f"  {gate_id}: MAE={mae:.6f}, RMSE={rmse:.6f}, 稳定性={stability:.6f}")
            
            # 开度变化度
            if opening_col in data.columns:
                opening_data = data[opening_col].dropna()
                opening_change = np.mean(np.abs(np.diff(opening_data)))
                gate_metrics[gate_id]['opening_change'] = opening_change
                print(f"      {gate_id}_opening: 变化度={opening_change:.6f}")
            
            # 流量稳定性
            if flow_col in data.columns:
                flow_data = data[flow_col].dropna()
                flow_stability = flow_data.std()
                gate_metrics[gate_id]['flow_stability'] = flow_stability
                print(f"      {gate_id}_flow: 流量稳定性={flow_stability:.6f}")
    
    # 计算系统整体指标
    all_mae = [gate_metrics[gate]['mae'] for gate in gate_metrics if 'mae' in gate_metrics[gate]]
    all_rmse = [gate_metrics[gate]['rmse'] for gate in gate_metrics if 'rmse' in gate_metrics[gate]]
    all_stability = [gate_metrics[gate]['stability'] for gate in gate_metrics if 'stability' in gate_metrics[gate]]
    all_opening_change = [gate_metrics[gate]['opening_change'] for gate in gate_metrics if 'opening_change' in gate_metrics[gate]]
    
    system_mae = np.mean(all_mae) if all_mae else 0
    system_rmse = np.mean(all_rmse) if all_rmse else 0
    system_stability = np.mean(all_stability) if all_stability else 0
    system_opening_change = np.mean(all_opening_change) if all_opening_change else 0
    
    # 综合性能指数 (越小越好)
    performance_index = system_mae + system_rmse + system_stability * 0.5 + system_opening_change * 0.3
    
    metrics = {
        'system_mae': system_mae,
        'system_rmse': system_rmse,
        'system_stability': system_stability,
        'system_opening_change': system_opening_change,
        'performance_index': performance_index,
        'gate_metrics': gate_metrics
    }
    
    print(f"      系统整体: MAE={system_mae:.6f}, RMSE={system_rmse:.6f}, 综合指数={performance_index:.6f}")
    
    return metrics

def create_no_disturbance_comparison(scenarios):
    """创建无干扰情况下的对比图表"""
    
    for scenario in scenarios:
        print(f"\n处理场景: {scenario}")
        
        # 加载数据
        rule_file = f"experiment_results/rule_{scenario}_data.csv"
        mpc_file = f"experiment_results/mpc_{scenario}_data.csv"
        
        rule_data = load_data(rule_file)
        mpc_data = load_data(mpc_file)
        
        if rule_data is None or mpc_data is None:
            print(f"跳过场景 {scenario}，数据文件缺失")
            continue
        
        # 计算性能指标
        print("\n计算Rule模式性能指标:")
        rule_metrics = calculate_performance_metrics(rule_data)
        
        print("\n计算MPC模式性能指标:")
        mpc_metrics = calculate_performance_metrics(mpc_data)
        
        # 创建对比图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'无干扰情况下的控制性能对比 - {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        # 定义指标和标签
        metrics_info = [
            ('system_mae', '整体平均绝对误差 (m)', axes[0, 0]),
            ('system_stability', '整体水位稳定性 (m)', axes[0, 1]),
            ('system_opening_change', '整体开度变化度', axes[1, 0]),
            ('performance_index', '综合性能指数', axes[1, 1])
        ]
        
        for metric_key, metric_label, ax in metrics_info:
            # 数据
            rule_value = rule_metrics[metric_key]
            mpc_value = mpc_metrics[metric_key]
            
            print(f"\n绘制指标: {metric_label}")
            print(f"  Rule: {rule_value:.6f}")
            print(f"  MPC: {mpc_value:.6f}")
            
            # 创建柱状图
            modes = ['Rule模式', 'MPC模式']
            values = [rule_value, mpc_value]
            colors = ['#ff7f7f', '#7fbf7f']  # 红色和绿色
            
            bars = ax.bar(modes, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
            
            # 添加数值标签
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.6f}', ha='center', va='bottom', fontweight='bold')
            
            # 设置标题和标签
            ax.set_title(metric_label, fontsize=12, fontweight='bold')
            ax.set_ylabel('数值')
            ax.grid(True, alpha=0.3)
            
            # 设置y轴范围，确保数值可见
            if max(values) > 0:
                ax.set_ylim(0, max(values) * 1.15)
            
            # 突出显示性能更好的模式
            better_idx = 0 if rule_value < mpc_value else 1
            bars[better_idx].set_edgecolor('gold')
            bars[better_idx].set_linewidth(3)
        
        plt.tight_layout()
        
        # 保存图表
        output_file = f"experiment_results/no_disturbance_comparison_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"已生成无干扰对比图: {output_file}")
        plt.close()
        
        # 生成性能对比报告
        print(f"\n=== {scenario.replace('_', ' ').title()} 场景性能对比报告 ===")
        print(f"整体平均绝对误差: Rule={rule_metrics['system_mae']:.6f}m, MPC={mpc_metrics['system_mae']:.6f}m")
        print(f"整体水位稳定性: Rule={rule_metrics['system_stability']:.6f}m, MPC={mpc_metrics['system_stability']:.6f}m")
        print(f"整体开度变化度: Rule={rule_metrics['system_opening_change']:.6f}, MPC={mpc_metrics['system_opening_change']:.6f}")
        print(f"综合性能指数: Rule={rule_metrics['performance_index']:.6f}, MPC={mpc_metrics['performance_index']:.6f}")
        
        improvement_mae = (rule_metrics['system_mae'] - mpc_metrics['system_mae']) / rule_metrics['system_mae'] * 100
        improvement_stability = (rule_metrics['system_stability'] - mpc_metrics['system_stability']) / rule_metrics['system_stability'] * 100
        improvement_index = (rule_metrics['performance_index'] - mpc_metrics['performance_index']) / rule_metrics['performance_index'] * 100
        
        print(f"\nMPC相对于Rule的改进:")
        print(f"  MAE改进: {improvement_mae:.2f}%")
        print(f"  稳定性改进: {improvement_stability:.2f}%")
        print(f"  综合性能改进: {improvement_index:.2f}%")

def main():
    """主函数"""
    print("开始生成无干扰情况下的控制性能对比图表...")
    
    # 确保输出目录存在
    Path("experiment_results").mkdir(exist_ok=True)
    
    # 定义要分析的场景
    scenarios = ['normal_operation', 'rainfall_disturbance', 'extreme_disturbance']
    
    # 生成对比图表
    create_no_disturbance_comparison(scenarios)
    
    print("\n无干扰对比分析完成！")

if __name__ == "__main__":
    main()