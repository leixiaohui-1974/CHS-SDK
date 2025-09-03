#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渠道延迟响应分析脚本
分析分布式数字孪生系统中每个渠道的积分时滞模型响应过程
"""

import numpy as np
import matplotlib.pyplot as plt
import yaml
from pathlib import Path
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_config():
    """加载配置文件"""
    config_path = Path('config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def analyze_integral_delay_model(channel_config, channel_name):
    """分析积分时滞模型的特性"""
    model_config = channel_config['IntegralDelayModel']
    
    # 提取参数
    time_delay = model_config['time_delay']  # 秒
    integral_coeff = model_config['integral_coefficient']
    
    # 模拟时间序列
    dt = 1.0  # 时间步长（秒）
    total_time = 3600  # 总时间（秒）
    time_steps = int(total_time / dt)
    time_array = np.arange(0, total_time, dt)
    
    # 创建入流扰动信号
    inflow_base = 10.0  # 基础入流 m³/s
    inflow = np.full(time_steps, inflow_base)
    
    # 添加阶跃扰动（在t=600s时增加20%）
    step_time = 600
    step_magnitude = 0.2 * inflow_base
    inflow[int(step_time/dt):int((step_time+600)/dt)] += step_magnitude
    
    # 添加脉冲扰动（在t=1800s时短暂增加50%）
    pulse_time = 1800
    pulse_duration = 120  # 2分钟
    pulse_magnitude = 0.5 * inflow_base
    inflow[int(pulse_time/dt):int((pulse_time+pulse_duration)/dt)] += pulse_magnitude
    
    # 模拟积分时滞模型响应
    delay_steps = int(time_delay / dt)
    water_level = np.zeros(time_steps)
    outflow = np.zeros(time_steps)
    
    # 初始水位
    initial_level = 5.0  # 米
    water_level[0] = initial_level
    
    # 延迟队列
    inflow_history = [inflow_base] * (delay_steps + 1)
    
    for i in range(1, time_steps):
        # 更新延迟队列
        inflow_history.append(inflow[i])
        if len(inflow_history) > delay_steps + 1:
            inflow_history.pop(0)
        
        # 延迟后的入流
        delayed_inflow = inflow_history[0] if len(inflow_history) > delay_steps else inflow_base
        outflow[i] = delayed_inflow
        
        # 积分特性：水位变化 = 积分系数 * (入流 - 出流) * dt
        water_level_change = integral_coeff * (inflow[i] - outflow[i]) * dt
        water_level[i] = water_level[i-1] + water_level_change
    
    return {
        'time': time_array,
        'inflow': inflow,
        'outflow': outflow,
        'water_level': water_level,
        'time_delay': time_delay,
        'integral_coeff': integral_coeff,
        'channel_name': channel_name
    }

def create_comprehensive_analysis_chart():
    """创建综合分析图表"""
    # 加载配置
    config = load_config()
    digital_twin_config = config['digital_twin']['channel_models']
    
    # 分析每个渠道
    channel_results = {}
    for channel_name, channel_config in digital_twin_config.items():
        if channel_config.get('model_type') == 'IntegralDelayModel':
            # 重构配置格式以适配分析函数
            adapted_config = {
                'IntegralDelayModel': {
                    'time_delay': channel_config['initial_parameters']['time_delay'],
                    'integral_coefficient': channel_config['initial_parameters']['integral_coefficient']
                }
            }
            result = analyze_integral_delay_model(adapted_config, channel_name)
            channel_results[channel_name] = result
    
    # 创建图表
    fig = plt.figure(figsize=(20, 16))
    gs = GridSpec(4, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # 主标题
    fig.suptitle('分布式数字孪生系统 - 渠道积分时滞模型延迟响应分析\nIntegral-Delay Model Response Analysis for Multiple Channels', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # 颜色方案
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    # 1. 入流扰动设计图
    ax1 = fig.add_subplot(gs[0, :])
    time_example = channel_results[list(channel_results.keys())[0]]['time']
    inflow_example = channel_results[list(channel_results.keys())[0]]['inflow']
    
    ax1.plot(time_example/60, inflow_example, linewidth=2.5, color='#1f77b4', label='入流扰动信号')
    ax1.axhspan(10, 12, xmin=10, xmax=20, alpha=0.3, color='orange', label='阶跃扰动 (+20%)')
    ax1.axhspan(10, 15, xmin=30, xmax=32, alpha=0.3, color='red', label='脉冲扰动 (+50%)')
    ax1.set_xlabel('时间 (分钟)')
    ax1.set_ylabel('入流量 (m³/s)')
    ax1.set_title('入流扰动设计 - 测试系统对不同类型扰动的响应能力', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. 各渠道响应对比
    ax2 = fig.add_subplot(gs[1, :])
    for i, (channel_name, result) in enumerate(channel_results.items()):
        ax2.plot(result['time']/60, result['water_level'], 
                linewidth=2, color=colors[i % len(colors)], 
                label=f"{channel_name} (延迟={result['time_delay']}s, 积分系数={result['integral_coeff']})")
    
    ax2.set_xlabel('时间 (分钟)')
    ax2.set_ylabel('水位 (m)')
    ax2.set_title('各渠道水位响应对比 - 不同延迟参数的影响', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. 延迟特性分析（每个渠道单独显示）
    for i, (channel_name, result) in enumerate(channel_results.items()):
        row = 2 + i // 3
        col = i % 3
        if row >= 4:  # 限制显示的渠道数量
            break
            
        ax = fig.add_subplot(gs[row, col])
        
        # 绘制入流和出流
        ax.plot(result['time']/60, result['inflow'], 
               linewidth=2, color='blue', alpha=0.7, label='入流')
        ax.plot(result['time']/60, result['outflow'], 
               linewidth=2, color='red', alpha=0.7, label='出流（延迟后）')
        
        # 标注延迟时间
        delay_minutes = result['time_delay'] / 60
        ax.axvline(x=10, color='blue', linestyle='--', alpha=0.5)
        ax.axvline(x=10+delay_minutes, color='red', linestyle='--', alpha=0.5)
        ax.annotate(f'延迟 {delay_minutes:.1f}分钟', 
                   xy=(10+delay_minutes/2, 11), 
                   xytext=(10+delay_minutes/2, 13),
                   arrowprops=dict(arrowstyle='<->', color='black', alpha=0.7),
                   ha='center', fontsize=9)
        
        ax.set_xlabel('时间 (分钟)')
        ax.set_ylabel('流量 (m³/s)')
        ax.set_title(f'{channel_name} 延迟特性\n时滞={result["time_delay"]}s', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    
    # 4. 参数对比表格
    ax_table = fig.add_subplot(gs[3, :])
    ax_table.axis('off')
    
    # 创建参数对比数据
    table_data = []
    for channel_name, result in channel_results.items():
        # 计算响应特性
        step_response_time = None
        steady_state_error = None
        
        # 找到阶跃响应的90%稳定时间
        step_start_idx = int(600)  # 阶跃开始时间
        step_end_idx = int(1200)   # 阶跃结束时间
        
        if step_start_idx < len(result['water_level']) and step_end_idx < len(result['water_level']):
            initial_level = result['water_level'][step_start_idx-1]
            final_level = result['water_level'][step_end_idx]
            target_level = initial_level + 0.9 * (final_level - initial_level)
            
            for j in range(step_start_idx, step_end_idx):
                if result['water_level'][j] >= target_level:
                    step_response_time = (j - step_start_idx)
                    break
        
        table_data.append([
            channel_name,
            f"{result['time_delay']:.0f}s",
            f"{result['integral_coeff']:.2f}",
            f"{step_response_time:.0f}s" if step_response_time else "N/A",
            "快速" if result['time_delay'] < 300 else "中等" if result['time_delay'] < 400 else "较慢"
        ])
    
    # 创建表格
    table = ax_table.table(cellText=table_data,
                          colLabels=['渠道名称', '时滞参数', '积分系数', '90%响应时间', '响应速度'],
                          cellLoc='center',
                          loc='center',
                          bbox=[0.1, 0.3, 0.8, 0.4])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # 设置表格样式
    for i in range(len(table_data) + 1):
        for j in range(5):
            cell = table[(i, j)]
            if i == 0:  # 表头
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
    
    # 添加说明文字
    ax_table.text(0.5, 0.1, 
                 '积分时滞模型特性说明：\n'
                 '• 时滞参数：控制系统响应的延迟时间，反映水流传播的物理延迟\n'
                 '• 积分系数：控制水位变化的幅度，反映渠道的蓄水能力\n'
                 '• 响应时间：系统达到稳态的时间，受时滞和积分系数共同影响',
                 transform=ax_table.transAxes, ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7),
                 fontsize=10)
    
    plt.tight_layout()
    plt.savefig('channel_delay_response_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('channel_delay_response_analysis.pdf', bbox_inches='tight')
    print("\n=== 渠道延迟响应分析完成 ===")
    print(f"已生成分析图表: channel_delay_response_analysis.png")
    print(f"已生成PDF版本: channel_delay_response_analysis.pdf")
    
    return channel_results

def create_delay_mechanism_explanation():
    """创建延迟机制解释图"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('积分时滞模型延迟机制详解\nIntegral-Delay Model Mechanism Explanation', 
                 fontsize=16, fontweight='bold')
    
    # 1. 延迟队列示意图
    ax1 = axes[0, 0]
    time_points = np.arange(0, 10)
    queue_values = [10, 10, 12, 12, 12, 10, 10, 10, 10, 10]
    
    # 绘制延迟队列
    for i, val in enumerate(queue_values):
        color = 'red' if i < 3 else 'lightblue'
        rect = Rectangle((i, 0), 0.8, val, facecolor=color, edgecolor='black', alpha=0.7)
        ax1.add_patch(rect)
        ax1.text(i+0.4, val+0.5, f't-{len(queue_values)-1-i}', ha='center', fontsize=8)
    
    ax1.set_xlim(-0.5, len(queue_values))
    ax1.set_ylim(0, 15)
    ax1.set_xlabel('时间步')
    ax1.set_ylabel('入流量')
    ax1.set_title('延迟队列机制\n红色部分为当前输出')
    ax1.grid(True, alpha=0.3)
    
    # 2. 积分过程示意图
    ax2 = axes[0, 1]
    t = np.linspace(0, 10, 100)
    inflow = np.where((t >= 2) & (t <= 4), 12, 10)
    outflow = np.where((t >= 5) & (t <= 7), 12, 10)  # 延迟3个单位
    
    water_level = np.zeros_like(t)
    water_level[0] = 5.0
    dt = t[1] - t[0]
    integral_coeff = 0.1
    
    for i in range(1, len(t)):
        water_level[i] = water_level[i-1] + integral_coeff * (inflow[i] - outflow[i]) * dt
    
    ax2.plot(t, inflow, 'b-', linewidth=2, label='入流')
    ax2.plot(t, outflow, 'r-', linewidth=2, label='出流（延迟后）')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(t, water_level, 'g-', linewidth=2, label='水位')
    
    ax2.set_xlabel('时间')
    ax2.set_ylabel('流量', color='blue')
    ax2_twin.set_ylabel('水位', color='green')
    ax2.set_title('积分过程\n水位 = ∫(入流-出流)dt')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    
    # 3. 参数影响分析
    ax3 = axes[1, 0]
    t = np.linspace(0, 20, 200)
    step_input = np.where(t >= 5, 2, 0)
    
    # 不同延迟时间的影响
    delays = [1, 3, 5]
    colors = ['blue', 'red', 'green']
    
    for delay, color in zip(delays, colors):
        delayed_output = np.zeros_like(t)
        for i in range(len(t)):
            delay_idx = max(0, i - int(delay * 10))  # 10 points per unit time
            delayed_output[i] = step_input[delay_idx]
        
        ax3.plot(t, delayed_output, color=color, linewidth=2, label=f'延迟={delay}s')
    
    ax3.plot(t, step_input, 'k--', linewidth=1, alpha=0.7, label='输入信号')
    ax3.set_xlabel('时间')
    ax3.set_ylabel('输出')
    ax3.set_title('延迟参数影响\n不同延迟时间的响应')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. 积分系数影响分析
    ax4 = axes[1, 1]
    t = np.linspace(0, 10, 100)
    flow_diff = np.where((t >= 2) & (t <= 6), 2, 0)
    
    # 不同积分系数的影响
    coeffs = [0.1, 0.3, 0.5]
    colors = ['blue', 'red', 'green']
    
    for coeff, color in zip(coeffs, colors):
        water_level = np.zeros_like(t)
        water_level[0] = 5.0
        dt = t[1] - t[0]
        
        for i in range(1, len(t)):
            water_level[i] = water_level[i-1] + coeff * flow_diff[i] * dt
        
        ax4.plot(t, water_level, color=color, linewidth=2, label=f'积分系数={coeff}')
    
    ax4.set_xlabel('时间')
    ax4.set_ylabel('水位变化')
    ax4.set_title('积分系数影响\n不同积分系数的水位响应')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig('delay_mechanism_explanation.png', dpi=300, bbox_inches='tight')
    print(f"已生成延迟机制解释图: delay_mechanism_explanation.png")

def main():
    """主函数"""
    print("=== 分布式数字孪生系统 - 渠道积分时滞模型分析 ===")
    print("正在分析各渠道的延迟响应特性...")
    
    try:
        # 创建综合分析图表
        channel_results = create_comprehensive_analysis_chart()
        
        # 创建延迟机制解释图
        create_delay_mechanism_explanation()
        
        # 输出分析结果
        print("\n=== 分析结果总结 ===")
        for channel_name, result in channel_results.items():
            print(f"\n{channel_name}:")
            print(f"  时滞参数: {result['time_delay']}秒 ({result['time_delay']/60:.1f}分钟)")
            print(f"  积分系数: {result['integral_coeff']}")
            print(f"  延迟特性: 入流变化需要{result['time_delay']}秒才能反映到出流")
            print(f"  积分特性: 水位变化速率 = {result['integral_coeff']} × (入流-出流)")
        
        print("\n=== 技术要点 ===")
        print("1. 积分时滞模型结合了延迟和积分两种特性")
        print("2. 延迟特性模拟水流传播的物理延迟")
        print("3. 积分特性模拟渠道的蓄水能力")
        print("4. 不同渠道的参数差异反映了实际工程中的多样性")
        print("5. 系统能够同时处理多个渠道的不同延迟特性")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()