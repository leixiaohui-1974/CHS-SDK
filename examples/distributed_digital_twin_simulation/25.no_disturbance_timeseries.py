#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无干扰情况下的时间序列对比可视化
专门展示Rule模式vs MPC模式在无传感器和执行器干扰条件下的时间序列数据
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

def create_timeseries_comparison(scenarios):
    """创建无干扰情况下的时间序列对比图表"""
    
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
        
        # 获取闸门数量
        gate_columns = [col for col in rule_data.columns if 'Gate_' in col and '_upstream_level' in col]
        num_gates = len(gate_columns)
        
        print(f"检测到 {num_gates} 个闸门")
        
        # 创建时间序列图表
        fig, axes = plt.subplots(3, num_gates, figsize=(5*num_gates, 15))
        if num_gates == 1:
            axes = axes.reshape(-1, 1)
        
        fig.suptitle(f'无干扰情况下的时间序列对比 - {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        # 为每个闸门绘制时间序列
        for gate_idx in range(num_gates):
            gate_id = f"Gate_{gate_idx + 1}"
            
            # 水位时间序列
            level_col = f"{gate_id}_upstream_level"
            if level_col in rule_data.columns and level_col in mpc_data.columns:
                ax = axes[0, gate_idx]
                
                # 绘制Rule模式
                ax.plot(rule_data['time'], rule_data[level_col], 
                       label='Rule模式', color='red', linewidth=2, alpha=0.8)
                
                # 绘制MPC模式
                ax.plot(mpc_data['time'], mpc_data[level_col], 
                       label='MPC模式', color='blue', linewidth=2, alpha=0.8)
                
                ax.set_title(f'{gate_id} 上游水位', fontsize=12, fontweight='bold')
                ax.set_xlabel('时间 (s)')
                ax.set_ylabel('水位 (m)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 计算并显示统计信息
                rule_mean = rule_data[level_col].mean()
                mpc_mean = mpc_data[level_col].mean()
                rule_std = rule_data[level_col].std()
                mpc_std = mpc_data[level_col].std()
                
                # 添加统计信息文本框
                stats_text = f'Rule: μ={rule_mean:.3f}, σ={rule_std:.3f}\nMPC: μ={mpc_mean:.3f}, σ={mpc_std:.3f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # 开度时间序列
            opening_col = f"{gate_id}_opening"
            if opening_col in rule_data.columns and opening_col in mpc_data.columns:
                ax = axes[1, gate_idx]
                
                # 绘制Rule模式
                ax.plot(rule_data['time'], rule_data[opening_col], 
                       label='Rule模式', color='red', linewidth=2, alpha=0.8)
                
                # 绘制MPC模式
                ax.plot(mpc_data['time'], mpc_data[opening_col], 
                       label='MPC模式', color='blue', linewidth=2, alpha=0.8)
                
                ax.set_title(f'{gate_id} 开度', fontsize=12, fontweight='bold')
                ax.set_xlabel('时间 (s)')
                ax.set_ylabel('开度 (m)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 计算并显示统计信息
                rule_mean = rule_data[opening_col].mean()
                mpc_mean = mpc_data[opening_col].mean()
                rule_std = rule_data[opening_col].std()
                mpc_std = mpc_data[opening_col].std()
                
                # 计算开度变化度（平滑性指标）
                rule_change = np.mean(np.abs(np.diff(rule_data[opening_col])))
                mpc_change = np.mean(np.abs(np.diff(mpc_data[opening_col])))
                
                stats_text = f'Rule: μ={rule_mean:.3f}, Δ={rule_change:.4f}\nMPC: μ={mpc_mean:.3f}, Δ={mpc_change:.4f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            # 流量时间序列
            flow_col = f"{gate_id}_flow"
            if flow_col in rule_data.columns and flow_col in mpc_data.columns:
                ax = axes[2, gate_idx]
                
                # 绘制Rule模式
                ax.plot(rule_data['time'], rule_data[flow_col], 
                       label='Rule模式', color='red', linewidth=2, alpha=0.8)
                
                # 绘制MPC模式
                ax.plot(mpc_data['time'], mpc_data[flow_col], 
                       label='MPC模式', color='blue', linewidth=2, alpha=0.8)
                
                ax.set_title(f'{gate_id} 流量', fontsize=12, fontweight='bold')
                ax.set_xlabel('时间 (s)')
                ax.set_ylabel('流量 (m³/s)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 计算并显示统计信息
                rule_mean = rule_data[flow_col].mean()
                mpc_mean = mpc_data[flow_col].mean()
                rule_std = rule_data[flow_col].std()
                mpc_std = mpc_data[flow_col].std()
                
                stats_text = f'Rule: μ={rule_mean:.2f}, σ={rule_std:.2f}\nMPC: μ={mpc_mean:.2f}, σ={mpc_std:.2f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        plt.tight_layout()
        
        # 保存图表
        output_file = f"experiment_results/no_disturbance_timeseries_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"已生成无干扰时间序列图: {output_file}")
        plt.close()
        
        # 生成详细的时间序列分析报告
        print(f"\n=== {scenario.replace('_', ' ').title()} 场景时间序列分析报告 ===")
        
        for gate_idx in range(num_gates):
            gate_id = f"Gate_{gate_idx + 1}"
            print(f"\n{gate_id} 分析:")
            
            # 水位分析
            level_col = f"{gate_id}_upstream_level"
            if level_col in rule_data.columns and level_col in mpc_data.columns:
                rule_level = rule_data[level_col]
                mpc_level = mpc_data[level_col]
                
                print(f"  水位控制:")
                print(f"    Rule模式: 均值={rule_level.mean():.4f}m, 标准差={rule_level.std():.4f}m")
                print(f"    MPC模式:  均值={mpc_level.mean():.4f}m, 标准差={mpc_level.std():.4f}m")
                print(f"    稳定性改进: {((rule_level.std() - mpc_level.std()) / rule_level.std() * 100):.2f}%")
            
            # 开度分析
            opening_col = f"{gate_id}_opening"
            if opening_col in rule_data.columns and opening_col in mpc_data.columns:
                rule_opening = rule_data[opening_col]
                mpc_opening = mpc_data[opening_col]
                
                rule_change = np.mean(np.abs(np.diff(rule_opening)))
                mpc_change = np.mean(np.abs(np.diff(mpc_opening)))
                
                print(f"  开度控制:")
                print(f"    Rule模式: 均值={rule_opening.mean():.4f}m, 变化度={rule_change:.6f}")
                print(f"    MPC模式:  均值={mpc_opening.mean():.4f}m, 变化度={mpc_change:.6f}")
                print(f"    平滑性改进: {((rule_change - mpc_change) / rule_change * 100):.2f}%")
            
            # 流量分析
            flow_col = f"{gate_id}_flow"
            if flow_col in rule_data.columns and flow_col in mpc_data.columns:
                rule_flow = rule_data[flow_col]
                mpc_flow = mpc_data[flow_col]
                
                print(f"  流量控制:")
                print(f"    Rule模式: 均值={rule_flow.mean():.2f}m³/s, 标准差={rule_flow.std():.2f}m³/s")
                print(f"    MPC模式:  均值={mpc_flow.mean():.2f}m³/s, 标准差={mpc_flow.std():.2f}m³/s")
                print(f"    流量稳定性改进: {((rule_flow.std() - mpc_flow.std()) / rule_flow.std() * 100):.2f}%")

def create_system_overview_timeseries(scenarios):
    """创建系统整体时间序列概览图"""
    
    for scenario in scenarios:
        print(f"\n创建系统整体时间序列概览: {scenario}")
        
        # 加载数据
        rule_file = f"experiment_results/rule_{scenario}_data.csv"
        mpc_file = f"experiment_results/mpc_{scenario}_data.csv"
        
        rule_data = load_data(rule_file)
        mpc_data = load_data(mpc_file)
        
        if rule_data is None or mpc_data is None:
            continue
        
        # 创建系统概览图
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'系统整体时间序列概览 - {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        # 获取所有闸门的水位数据
        gate_columns = [col for col in rule_data.columns if 'Gate_' in col and '_upstream_level' in col]
        
        # 1. 所有闸门水位对比
        ax = axes[0, 0]
        for col in gate_columns:
            gate_num = col.split('_')[1]
            ax.plot(rule_data['time'], rule_data[col], 
                   label=f'Rule-Gate{gate_num}', linestyle='-', alpha=0.7)
            ax.plot(mpc_data['time'], mpc_data[col], 
                   label=f'MPC-Gate{gate_num}', linestyle='--', alpha=0.7)
        
        ax.set_title('所有闸门水位对比', fontweight='bold')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('水位 (m)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 2. 平均水位
        ax = axes[0, 1]
        rule_avg_level = rule_data[[col for col in gate_columns]].mean(axis=1)
        mpc_avg_level = mpc_data[[col for col in gate_columns]].mean(axis=1)
        
        ax.plot(rule_data['time'], rule_avg_level, 
               label='Rule模式平均', color='red', linewidth=3)
        ax.plot(mpc_data['time'], mpc_avg_level, 
               label='MPC模式平均', color='blue', linewidth=3)
        
        ax.set_title('系统平均水位', fontweight='bold')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('平均水位 (m)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. 所有闸门开度对比
        ax = axes[1, 0]
        opening_columns = [col for col in rule_data.columns if 'Gate_' in col and '_opening' in col]
        for col in opening_columns:
            gate_num = col.split('_')[1]
            ax.plot(rule_data['time'], rule_data[col], 
                   label=f'Rule-Gate{gate_num}', linestyle='-', alpha=0.7)
            ax.plot(mpc_data['time'], mpc_data[col], 
                   label=f'MPC-Gate{gate_num}', linestyle='--', alpha=0.7)
        
        ax.set_title('所有闸门开度对比', fontweight='bold')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('开度 (m)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 4. 总流量对比
        ax = axes[1, 1]
        flow_columns = [col for col in rule_data.columns if 'Gate_' in col and '_flow' in col]
        rule_total_flow = rule_data[flow_columns].sum(axis=1)
        mpc_total_flow = mpc_data[flow_columns].sum(axis=1)
        
        ax.plot(rule_data['time'], rule_total_flow, 
               label='Rule模式总流量', color='red', linewidth=3)
        ax.plot(mpc_data['time'], mpc_total_flow, 
               label='MPC模式总流量', color='blue', linewidth=3)
        
        ax.set_title('系统总流量', fontweight='bold')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('总流量 (m³/s)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_file = f"experiment_results/system_overview_timeseries_{scenario}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"已生成系统概览时间序列图: {output_file}")
        plt.close()

def main():
    """主函数"""
    print("开始生成无干扰情况下的时间序列对比图表...")
    
    # 确保输出目录存在
    Path("experiment_results").mkdir(exist_ok=True)
    
    # 定义要分析的场景
    scenarios = ['normal_operation', 'rainfall_disturbance', 'extreme_disturbance']
    
    # 生成详细的时间序列对比图表
    create_timeseries_comparison(scenarios)
    
    # 生成系统整体概览图
    create_system_overview_timeseries(scenarios)
    
    print("\n无干扰时间序列分析完成！")

if __name__ == "__main__":
    main()