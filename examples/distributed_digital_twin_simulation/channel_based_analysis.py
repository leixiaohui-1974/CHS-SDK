#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渠道为中心的控制分析可视化
按照每个渠道（被控对象）为单元，展示扰动、响应和控制指令的关系
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.font_manager as fm
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ChannelBasedAnalyzer:
    """基于渠道的控制分析器"""
    
    def __init__(self, results_dir="experiment_results"):
        self.results_dir = Path(results_dir)
        self.scenarios = ["normal_operation", "rainfall_disturbance", "extreme_disturbance"]
        self.modes = ["rule", "mpc"]
        
        # 渠道-闸站映射关系
        self.channel_gate_mapping = {
            "Channel_1": "Gate_1",  # 渠道1由闸站1控制
            "Channel_2": "Gate_2",  # 渠道2由闸站2控制  
            "Channel_3": "Gate_3"   # 渠道3由闸站3控制
        }
        
        # 目标水位
        self.target_levels = {
            "Channel_1": 10.0,
            "Channel_2": 8.0,
            "Channel_3": 6.0
        }
    
    def load_scenario_data(self, mode, scenario):
        """加载特定场景的数据"""
        file_path = self.results_dir / f"{mode}_{scenario}_data.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            print(f"警告: 文件 {file_path} 不存在")
            return None
    
    def create_channel_analysis_plots(self):
        """为每个渠道创建综合分析图"""
        
        for scenario in self.scenarios:
            # 加载数据
            rule_data = self.load_scenario_data("rule", scenario)
            mpc_data = self.load_scenario_data("mpc", scenario)
            
            if rule_data is None or mpc_data is None:
                continue
                
            # 为每个渠道创建分析图
            for channel, gate in self.channel_gate_mapping.items():
                self._plot_channel_analysis(channel, gate, scenario, rule_data, mpc_data)
    
    def _plot_channel_analysis(self, channel, gate, scenario, rule_data, mpc_data):
        """为单个渠道创建分析图"""
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 12))
        fig.suptitle(f'{channel} 控制分析 - {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        # 时间轴
        time_rule = rule_data['time'] / 60  # 转换为分钟
        time_mpc = mpc_data['time'] / 60
        
        # 1. 扰动输入分析
        ax1 = axes[0]
        ax1.plot(time_rule, rule_data['rainfall_inflow'], 'b-', label='降雨入流', linewidth=2)
        ax1.plot(time_rule, rule_data[f'water_demand_{gate[-1]}'], 'r--', label='用水需求', linewidth=2)
        ax1.set_ylabel('扰动量\n(m³/s)', fontsize=12)
        ax1.set_title(f'{channel} 扰动输入', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 渠道水位响应对比
        ax2 = axes[1]
        target_level = self.target_levels[channel]
        
        # 目标水位线
        ax2.axhline(y=target_level, color='k', linestyle=':', linewidth=2, label='目标水位')
        
        # Rule模式响应
        ax2.plot(time_rule, rule_data[f'{gate}_upstream_level'], 'b-', 
                label='Rule模式实际水位', linewidth=2, alpha=0.8)
        
        # MPC模式响应
        ax2.plot(time_mpc, mpc_data[f'{gate}_upstream_level'], 'r-', 
                label='MPC模式实际水位', linewidth=2, alpha=0.8)
        
        ax2.set_ylabel('水位 (m)', fontsize=12)
        ax2.set_title(f'{channel} 水位响应对比', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 闸站控制指令对比
        ax3 = axes[2]
        
        # Rule模式控制指令（固定目标值）
        ax3.plot(time_rule, rule_data[f'control_command_{gate[-1]}'], 'b-', 
                label='Rule模式控制指令', linewidth=2, alpha=0.8)
        
        # MPC模式控制指令（优化设定点）
        ax3.plot(time_mpc, mpc_data[f'control_command_{gate[-1]}'], 'r-', 
                label='MPC模式控制指令', linewidth=2, alpha=0.8)
        
        # 目标水位参考线
        ax3.axhline(y=target_level, color='k', linestyle=':', linewidth=2, label='基准目标水位')
        
        ax3.set_ylabel('控制指令\n(水位设定点, m)', fontsize=12)
        ax3.set_title(f'{gate} 控制指令对比', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 闸门开度响应
        ax4 = axes[3]
        
        ax4.plot(time_rule, rule_data[f'{gate}_opening'], 'b-', 
                label='Rule模式闸门开度', linewidth=2, alpha=0.8)
        ax4.plot(time_mpc, mpc_data[f'{gate}_opening'], 'r-', 
                label='MPC模式闸门开度', linewidth=2, alpha=0.8)
        
        ax4.set_ylabel('闸门开度\n(0-1)', fontsize=12)
        ax4.set_xlabel('时间 (分钟)', fontsize=12)
        ax4.set_title(f'{gate} 开度响应对比', fontsize=14, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        output_file = self.results_dir / f"{channel}_{scenario}_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"已生成 {channel} 在 {scenario} 场景下的分析图: {output_file}")
    
    def create_comprehensive_comparison(self):
        """创建综合对比分析"""
        
        # 为每个场景创建所有渠道的对比图
        for scenario in self.scenarios:
            rule_data = self.load_scenario_data("rule", scenario)
            mpc_data = self.load_scenario_data("mpc", scenario)
            
            if rule_data is None or mpc_data is None:
                continue
                
            self._create_scenario_comprehensive_plot(scenario, rule_data, mpc_data)
    
    def _create_scenario_comprehensive_plot(self, scenario, rule_data, mpc_data):
        """创建单个场景的综合对比图"""
        
        fig, axes = plt.subplots(3, 3, figsize=(18, 12))
        fig.suptitle(f'综合控制分析 - {scenario.replace("_", " ").title()}', 
                    fontsize=16, fontweight='bold')
        
        time_rule = rule_data['time'] / 60
        time_mpc = mpc_data['time'] / 60
        
        channels = list(self.channel_gate_mapping.keys())
        
        for i, (channel, gate) in enumerate(self.channel_gate_mapping.items()):
            # 扰动输入
            ax_dist = axes[i, 0]
            ax_dist.plot(time_rule, rule_data['rainfall_inflow'], 'b-', label='降雨', linewidth=2)
            ax_dist.plot(time_rule, rule_data[f'water_demand_{gate[-1]}'], 'r--', label='需水', linewidth=2)
            ax_dist.set_title(f'{channel} 扰动', fontweight='bold')
            ax_dist.set_ylabel('扰动量 (m³/s)')
            if i == 0:
                ax_dist.legend()
            ax_dist.grid(True, alpha=0.3)
            
            # 水位响应
            ax_level = axes[i, 1]
            target = self.target_levels[channel]
            ax_level.axhline(y=target, color='k', linestyle=':', linewidth=2, alpha=0.7)
            ax_level.plot(time_rule, rule_data[f'{gate}_upstream_level'], 'b-', 
                         label='Rule', linewidth=2, alpha=0.8)
            ax_level.plot(time_mpc, mpc_data[f'{gate}_upstream_level'], 'r-', 
                         label='MPC', linewidth=2, alpha=0.8)
            ax_level.set_title(f'{channel} 水位响应', fontweight='bold')
            ax_level.set_ylabel('水位 (m)')
            if i == 0:
                ax_level.legend()
            ax_level.grid(True, alpha=0.3)
            
            # 控制指令
            ax_cmd = axes[i, 2]
            ax_cmd.axhline(y=target, color='k', linestyle=':', linewidth=2, alpha=0.7)
            ax_cmd.plot(time_rule, rule_data[f'control_command_{gate[-1]}'], 'b-', 
                       label='Rule指令', linewidth=2, alpha=0.8)
            ax_cmd.plot(time_mpc, mpc_data[f'control_command_{gate[-1]}'], 'r-', 
                       label='MPC指令', linewidth=2, alpha=0.8)
            ax_cmd.set_title(f'{gate} 控制指令', fontweight='bold')
            ax_cmd.set_ylabel('设定点 (m)')
            if i == 0:
                ax_cmd.legend()
            ax_cmd.grid(True, alpha=0.3)
            
            # 最后一行添加x轴标签
            if i == 2:
                ax_dist.set_xlabel('时间 (分钟)')
                ax_level.set_xlabel('时间 (分钟)')
                ax_cmd.set_xlabel('时间 (分钟)')
        
        plt.tight_layout()
        
        # 保存图片
        output_file = self.results_dir / f"comprehensive_{scenario}_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"已生成 {scenario} 场景综合分析图: {output_file}")
    
    def generate_analysis_report(self):
        """生成分析报告"""
        
        report_content = f"""
# 基于渠道的控制分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 控制架构说明

### 被控对象与控制对象关系
- **被控对象**: 渠道（Channel_1, Channel_2, Channel_3）
- **控制对象**: 闸站（Gate_1, Gate_2, Gate_3）
- **控制关系**: 每个闸站控制对应的渠道水位

### 控制映射关系
"""
        
        for channel, gate in self.channel_gate_mapping.items():
            target = self.target_levels[channel]
            report_content += f"- {channel} ← {gate} (目标水位: {target}m)\n"
        
        report_content += """

## 分析维度

### 1. 扰动输入分析
- **降雨入流**: 外部降雨对渠道的扰动输入
- **用水需求**: 下游用水对渠道的扰动输入

### 2. 渠道响应分析
- **实际水位**: 渠道在扰动和控制作用下的实际水位变化
- **目标跟踪**: 实际水位与目标水位的偏差分析

### 3. 控制指令分析
- **Rule模式**: 固定目标水位设定点，无中央协调
- **MPC模式**: 动态优化的水位设定点，考虑预测和协调

### 4. 执行器响应分析
- **闸门开度**: 闸站执行控制指令的实际开度变化
- **控制平滑性**: 开度变化的平滑程度对比

## 可视化文件说明

### 单渠道详细分析
"""
        
        for scenario in self.scenarios:
            for channel in self.channel_gate_mapping.keys():
                report_content += f"- `{channel}_{scenario}_analysis.png`: {channel}在{scenario}场景下的详细分析\n"
        
        report_content += """

### 综合对比分析
"""
        
        for scenario in self.scenarios:
            report_content += f"- `comprehensive_{scenario}_analysis.png`: {scenario}场景下所有渠道的综合对比\n"
        
        report_content += """

## 分析要点

1. **扰动传播**: 观察扰动如何影响各渠道水位
2. **控制协调**: 对比Rule模式和MPC模式的协调效果
3. **响应特性**: 分析不同控制模式下的响应速度和稳定性
4. **执行效率**: 评估闸门开度变化的合理性和平滑性

## 建议

- 重点关注扰动期间各渠道的水位偏差
- 对比两种控制模式的设定点调节策略
- 分析闸门开度变化与水位响应的关联性
- 评估系统整体的协调控制效果
"""
        
        # 保存报告
        report_file = self.results_dir / "channel_based_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"已生成分析报告: {report_file}")
    
    def run_analysis(self):
        """运行完整分析"""
        print("开始基于渠道的控制分析...")
        print("="*50)
        
        # 创建单渠道分析图
        print("\n1. 生成单渠道详细分析图...")
        self.create_channel_analysis_plots()
        
        # 创建综合对比图
        print("\n2. 生成综合对比分析图...")
        self.create_comprehensive_comparison()
        
        # 生成分析报告
        print("\n3. 生成分析报告...")
        self.generate_analysis_report()
        
        print("\n分析完成！")
        print(f"结果保存在: {self.results_dir}")

if __name__ == "__main__":
    analyzer = ChannelBasedAnalyzer()
    analyzer.run_analysis()