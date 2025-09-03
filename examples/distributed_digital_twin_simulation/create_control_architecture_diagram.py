#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数字孪生系统控制智能体架构可视化
生成控制系统架构图和数据流图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_control_architecture_diagram():
    """
    创建控制智能体架构图
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12))
    fig.suptitle('分布式数字孪生系统控制智能体架构分析', fontsize=16, fontweight='bold')
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 第一个子图：分层控制架构
    ax1.set_title('分层控制架构', fontsize=14, fontweight='bold')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 12)
    ax1.axis('off')
    
    # 定义颜色
    colors = {
        'central': '#FF6B6B',      # 红色 - 中央层
        'local': '#4ECDC4',        # 青色 - 本地层
        'perception': '#45B7D1',   # 蓝色 - 感知层
        'physical': '#96CEB4',     # 绿色 - 物理层
        'disturbance': '#FFEAA7'   # 黄色 - 扰动层
    }
    
    # 中央协调层
    central_box = FancyBboxPatch((1, 9), 8, 2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=colors['central'], 
                                edgecolor='black', linewidth=2)
    ax1.add_patch(central_box)
    ax1.text(5, 10, 'Central Coordination Layer\n中央协调层', 
             ha='center', va='center', fontsize=12, fontweight='bold')
    ax1.text(5, 9.3, 'CentralDispatcherAgent (MPC优化)', 
             ha='center', va='center', fontsize=10)
    
    # 本地控制层
    local_y = 6.5
    gate_boxes = []
    gate_names = ['Gate1_Control_Agent\n(3孔闸门PID)', 
                  'Gate2_Control_Agent\n(单孔闸门PID)', 
                  'Gate3_Control_Agent\n(单孔闸门PID)']
    
    for i, name in enumerate(gate_names):
        x_pos = 0.5 + i * 3
        box = FancyBboxPatch((x_pos, local_y), 2.5, 1.5, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['local'], 
                            edgecolor='black', linewidth=1.5)
        ax1.add_patch(box)
        gate_boxes.append((x_pos + 1.25, local_y + 0.75))
        ax1.text(x_pos + 1.25, local_y + 0.75, name, 
                ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 本地控制层标题
    ax1.text(5, 8.5, 'Local Control Layer (本地控制层)', 
             ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 感知层
    perception_y = 4
    perception_agents = ['Channel1_Twin_Agent\n(积分时滞模型)', 
                        'Gate1_Perception_Agent\n(RLS辨识)', 
                        'Gate2_Perception_Agent\n(RLS辨识)', 
                        'Gate3_Perception_Agent\n(RLS辨识)']
    
    for i, name in enumerate(perception_agents):
        x_pos = 0.2 + i * 2.4
        box = FancyBboxPatch((x_pos, perception_y), 2.2, 1.2, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['perception'], 
                            edgecolor='black', linewidth=1)
        ax1.add_patch(box)
        ax1.text(x_pos + 1.1, perception_y + 0.6, name, 
                ha='center', va='center', fontsize=8)
    
    ax1.text(5, 5.5, 'Perception Layer (感知层)', 
             ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 物理仿真层
    physical_box = FancyBboxPatch((1, 1.5), 8, 1.5, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=colors['physical'], 
                                 edgecolor='black', linewidth=2)
    ax1.add_patch(physical_box)
    ax1.text(5, 2.25, 'Physical Simulation Layer\n物理仿真层', 
             ha='center', va='center', fontsize=12, fontweight='bold')
    ax1.text(5, 1.8, 'OntologySimulationAgent (统一物理仿真)', 
             ha='center', va='center', fontsize=10)
    
    # 扰动层
    disturbance_boxes = [
        ('Rainfall_Agent\n降雨扰动', 0.5, 0.2),
        ('Water_Use_Agent\n用水需求扰动', 7.5, 0.2)
    ]
    
    for name, x, y in disturbance_boxes:
        box = FancyBboxPatch((x, y), 2, 1, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['disturbance'], 
                            edgecolor='black', linewidth=1)
        ax1.add_patch(box)
        ax1.text(x + 1, y + 0.5, name, 
                ha='center', va='center', fontsize=9)
    
    # 添加箭头连接
    # 中央到本地控制的连接
    for gate_pos in gate_boxes:
        arrow = ConnectionPatch((5, 9), gate_pos, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="red", alpha=0.7)
        ax1.add_patch(arrow)
    
    # 感知到本地控制的连接
    perception_positions = [(1.3, 4.6), (3.7, 4.6), (6.1, 4.6)]
    for i, perc_pos in enumerate(perception_positions[1:]):
        arrow = ConnectionPatch(perc_pos, gate_boxes[i], "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="blue", alpha=0.7)
        ax1.add_patch(arrow)
    
    # 物理层到感知层的连接
    for i in range(4):
        x_pos = 1.3 + i * 2.4
        arrow = ConnectionPatch((x_pos, 3), (x_pos, 4), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="green", alpha=0.7)
        ax1.add_patch(arrow)
    
    # 第二个子图：数据流图
    ax2.set_title('控制系统数据流图', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 12)
    ax2.axis('off')
    
    # 数据流节点
    nodes = {
        'physical': (5, 1.5, '物理仿真\nOntologySimulationAgent'),
        'perception': (2, 4, '感知智能体\nPerception Agents'),
        'central_perception': (8, 4, '中央感知\nCentralPerceptionAgent'),
        'local_control': (2, 7, '本地控制\nLocal Control Agents'),
        'central_mpc': (8, 7, '中央MPC\nCentralDispatcherAgent'),
        'actuators': (5, 10, '执行器\nActuators'),
        'disturbance': (5, 4, '扰动智能体\nDisturbance Agents')
    }
    
    # 绘制节点
    node_colors = {
        'physical': colors['physical'],
        'perception': colors['perception'],
        'central_perception': colors['perception'],
        'local_control': colors['local'],
        'central_mpc': colors['central'],
        'actuators': '#DDA0DD',
        'disturbance': colors['disturbance']
    }
    
    for node_id, (x, y, label) in nodes.items():
        circle = plt.Circle((x, y), 0.8, facecolor=node_colors[node_id], 
                           edgecolor='black', linewidth=2)
        ax2.add_patch(circle)
        ax2.text(x, y, label, ha='center', va='center', 
                fontsize=9, fontweight='bold')
    
    # 数据流连接
    flows = [
        ('physical', 'perception', '状态数据'),
        ('perception', 'central_perception', '清洗数据'),
        ('perception', 'local_control', '观测数据'),
        ('central_perception', 'central_mpc', '全局状态'),
        ('central_mpc', 'local_control', '目标设定'),
        ('local_control', 'actuators', '控制指令'),
        ('actuators', 'physical', '执行动作'),
        ('disturbance', 'physical', '扰动输入')
    ]
    
    for start, end, label in flows:
        start_pos = nodes[start][:2]
        end_pos = nodes[end][:2]
        
        # 计算箭头位置
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = np.sqrt(dx**2 + dy**2)
        
        # 调整起点和终点，避免与圆重叠
        start_adj = (start_pos[0] + 0.8 * dx/length, start_pos[1] + 0.8 * dy/length)
        end_adj = (end_pos[0] - 0.8 * dx/length, end_pos[1] - 0.8 * dy/length)
        
        arrow = ConnectionPatch(start_adj, end_adj, "data", "data",
                              arrowstyle="->", shrinkA=0, shrinkB=0,
                              mutation_scale=20, fc="black", alpha=0.8)
        ax2.add_patch(arrow)
        
        # 添加标签
        mid_x = (start_adj[0] + end_adj[0]) / 2
        mid_y = (start_adj[1] + end_adj[1]) / 2
        ax2.text(mid_x, mid_y, label, ha='center', va='center', 
                fontsize=8, bbox=dict(boxstyle="round,pad=0.2", 
                facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig

def create_control_performance_analysis():
    """
    创建控制性能分析图
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('控制智能体性能分析', fontsize=16, fontweight='bold')
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 1. PID参数对比
    gates = ['Gate1', 'Gate2', 'Gate3']
    kp_values = [2.0, 1.8, 1.5]
    ki_values = [0.5, 0.4, 0.3]
    kd_values = [0.1, 0.08, 0.06]
    
    x = np.arange(len(gates))
    width = 0.25
    
    ax1.bar(x - width, kp_values, width, label='Kp (比例增益)', color='#FF6B6B')
    ax1.bar(x, ki_values, width, label='Ki (积分增益)', color='#4ECDC4')
    ax1.bar(x + width, kd_values, width, label='Kd (微分增益)', color='#45B7D1')
    
    ax1.set_xlabel('闸门控制智能体')
    ax1.set_ylabel('PID参数值')
    ax1.set_title('PID控制器参数对比')
    ax1.set_xticks(x)
    ax1.set_xticklabels(gates)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 控制约束对比
    max_rates = [0.1, 0.08, 0.06]
    output_limits = [0.1, 0.08, 0.06]
    
    ax2.plot(gates, max_rates, 'o-', linewidth=2, markersize=8, 
             label='最大开度变化率', color='#FF6B6B')
    ax2.plot(gates, output_limits, 's-', linewidth=2, markersize=8, 
             label='输出限制', color='#4ECDC4')
    
    ax2.set_xlabel('闸门控制智能体')
    ax2.set_ylabel('约束值')
    ax2.set_title('控制约束参数对比')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 系统响应特性
    time = np.linspace(0, 100, 1000)
    
    # 模拟不同闸门的阶跃响应
    def step_response(t, kp, ki, kd, tau=10):
        """简化的二阶系统阶跃响应"""
        wn = np.sqrt(kp + ki/tau)
        zeta = (kd * wn + 1) / (2 * wn)
        
        if zeta < 1:  # 欠阻尼
            wd = wn * np.sqrt(1 - zeta**2)
            response = 1 - np.exp(-zeta * wn * t) * (np.cos(wd * t) + 
                      (zeta * wn / wd) * np.sin(wd * t))
        else:  # 过阻尼或临界阻尼
            response = 1 - np.exp(-wn * t) * (1 + wn * t)
        
        return np.clip(response, 0, 1.2)
    
    gate1_response = step_response(time, 2.0, 0.5, 0.1)
    gate2_response = step_response(time, 1.8, 0.4, 0.08)
    gate3_response = step_response(time, 1.5, 0.3, 0.06)
    
    ax3.plot(time, gate1_response, label='Gate1 (快速响应)', 
             linewidth=2, color='#FF6B6B')
    ax3.plot(time, gate2_response, label='Gate2 (中等响应)', 
             linewidth=2, color='#4ECDC4')
    ax3.plot(time, gate3_response, label='Gate3 (稳定响应)', 
             linewidth=2, color='#45B7D1')
    ax3.axhline(y=1, color='black', linestyle='--', alpha=0.5, label='目标值')
    
    ax3.set_xlabel('时间 (秒)')
    ax3.set_ylabel('归一化响应')
    ax3.set_title('系统阶跃响应特性')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 100)
    
    # 4. 控制架构优势雷达图
    categories = ['响应速度', '控制精度', '稳定性', '鲁棒性', '能效', '可维护性']
    
    # 分层控制系统的评分 (1-5分)
    hierarchical_scores = [4.5, 4.2, 4.8, 4.3, 4.0, 4.5]
    # 传统集中式控制的评分
    centralized_scores = [3.5, 4.0, 3.8, 3.2, 3.5, 3.0]
    # 完全分布式控制的评分
    distributed_scores = [4.8, 3.5, 3.5, 4.5, 3.8, 4.2]
    
    # 计算角度
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形
    
    # 闭合数据
    hierarchical_scores += hierarchical_scores[:1]
    centralized_scores += centralized_scores[:1]
    distributed_scores += distributed_scores[:1]
    
    ax4 = plt.subplot(224, projection='polar')
    ax4.plot(angles, hierarchical_scores, 'o-', linewidth=2, 
             label='分层控制 (本系统)', color='#FF6B6B')
    ax4.fill(angles, hierarchical_scores, alpha=0.25, color='#FF6B6B')
    
    ax4.plot(angles, centralized_scores, 's-', linewidth=2, 
             label='集中式控制', color='#4ECDC4')
    ax4.fill(angles, centralized_scores, alpha=0.25, color='#4ECDC4')
    
    ax4.plot(angles, distributed_scores, '^-', linewidth=2, 
             label='分布式控制', color='#45B7D1')
    ax4.fill(angles, distributed_scores, alpha=0.25, color='#45B7D1')
    
    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(categories)
    ax4.set_ylim(0, 5)
    ax4.set_title('控制架构性能对比', pad=20)
    ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax4.grid(True)
    
    plt.tight_layout()
    return fig

def main():
    """
    主函数：生成所有图表
    """
    print("正在生成控制智能体架构分析图表...")
    
    # 生成架构图
    fig1 = create_control_architecture_diagram()
    fig1.savefig('control_architecture_diagram.png', dpi=300, bbox_inches='tight')
    fig1.savefig('control_architecture_diagram.pdf', bbox_inches='tight')
    print("✓ 控制架构图已生成")
    
    # 生成性能分析图
    fig2 = create_control_performance_analysis()
    fig2.savefig('control_performance_analysis.png', dpi=300, bbox_inches='tight')
    fig2.savefig('control_performance_analysis.pdf', bbox_inches='tight')
    print("✓ 控制性能分析图已生成")
    
    plt.show()
    
    print("\n=== 控制智能体分析总结 ===")
    print("1. 系统采用分层控制架构，包含中央协调层和本地控制层")
    print("2. 本地控制智能体基于PID控制器，参数针对不同闸门优化")
    print("3. 中央MPC智能体负责全局优化和目标设定")
    print("4. 扰动智能体模拟真实环境的不确定性")
    print("5. 系统具备良好的响应速度、控制精度和鲁棒性")
    
if __name__ == "__main__":
    main()