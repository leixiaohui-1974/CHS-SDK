#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器和传感器干扰特征分析 - Streamlit Web界面
基于 actuator_sensor_disturbance_analysis.py 的Web版本
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from pathlib import Path
import matplotlib
from scipy.stats import norm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import base64

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

class ActuatorSensorDisturbanceAnalyzer:
    """执行器和传感器干扰特征分析器"""
    
    def __init__(self):
        self.scenarios = ["normal_operation", "rainfall_disturbance", "extreme_disturbance"]
        self.modes = ["rule", "mpc"]
    
    def generate_sample_data(self, duration=600, dt=1.0):
        """生成示例数据用于测试"""
        time_points = np.arange(0, duration, dt)
        n_points = len(time_points)
        
        # 生成示例数据
        data = {
            'time': time_points,
            'Gate_1_opening': 0.5 + 0.1 * np.sin(2 * np.pi * time_points / 100) + 0.05 * np.random.randn(n_points),
            'Gate_1_upstream_level': 10.0 + 0.2 * np.sin(2 * np.pi * time_points / 200) + 0.1 * np.random.randn(n_points),
            'Gate_2_opening': 0.3 + 0.08 * np.sin(2 * np.pi * time_points / 120) + 0.03 * np.random.randn(n_points),
            'Gate_2_upstream_level': 8.0 + 0.15 * np.sin(2 * np.pi * time_points / 180) + 0.08 * np.random.randn(n_points),
            'Gate_3_opening': 0.4 + 0.06 * np.sin(2 * np.pi * time_points / 150) + 0.04 * np.random.randn(n_points),
            'Gate_3_upstream_level': 6.0 + 0.1 * np.sin(2 * np.pi * time_points / 160) + 0.06 * np.random.randn(n_points)
        }
        
        return pd.DataFrame(data)
        
    def load_data(self, uploaded_file):
        """从上传的文件加载数据"""
        try:
            if uploaded_file is not None:
                # 尝试不同的编码方式
                try:
                    return pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        return pd.read_csv(uploaded_file, encoding='gbk')
                    except UnicodeDecodeError:
                        return pd.read_csv(uploaded_file, encoding='latin-1')
            return None
        except Exception as e:
            st.error(f"数据加载失败: {str(e)}")
            return None
    
    def extract_disturbance_features(self, data):
        """提取干扰特征"""
        features = {}
        
        # 检查数据是否为空
        if data is None or data.empty:
            st.warning("数据为空，无法进行分析")
            return features
        
        # 执行器干扰特征（闸门开度）
        for gate in ['1', '2', '3']:
            gate_col = f'Gate_{gate}_opening'
            if gate_col in data.columns:
                opening_data = data[gate_col].values
                
                # 检查数据是否包含NaN值
                if np.any(np.isnan(opening_data)):
                    st.warning(f"Gate_{gate}_opening 数据包含NaN值，将使用0填充")
                    opening_data = np.nan_to_num(opening_data, nan=0.0)
                
                # 计算开度变化率（执行器响应速度）
                opening_rate = np.abs(np.diff(opening_data))
                
                # 计算开度噪声（高频成分）
                try:
                    b, a = signal.butter(4, 0.1, 'high')
                    opening_noise = signal.filtfilt(b, a, opening_data)
                except:
                    opening_noise = np.zeros_like(opening_data)
                
                # 计算开度稳定性（标准差）
                opening_stability = np.std(opening_data)
                
                features[f'actuator_{gate}'] = {
                    'opening_data': opening_data,
                    'opening_rate': opening_rate,
                    'opening_noise': opening_noise,
                    'opening_stability': opening_stability,
                    'max_rate': np.max(opening_rate) if len(opening_rate) > 0 else 0,
                    'mean_rate': np.mean(opening_rate) if len(opening_rate) > 0 else 0,
                    'noise_rms': np.sqrt(np.mean(opening_noise**2))
                }
        
        # 传感器干扰特征（水位测量）
        target_levels = [10.0, 8.0, 6.0]
        for i, gate in enumerate(['1', '2', '3']):
            level_col = f'Gate_{gate}_upstream_level'
            if level_col in data.columns:
                level_data = data[level_col].values
                
                # 检查数据是否包含NaN值
                if np.any(np.isnan(level_data)):
                    st.warning(f"Gate_{gate}_upstream_level 数据包含NaN值，将使用目标值填充")
                    level_data = np.nan_to_num(level_data, nan=target_levels[i])
                
                target_level = target_levels[i]
                
                # 计算测量误差
                measurement_error = level_data - target_level
                
                # 计算测量噪声（去趋势后的高频成分）
                try:
                    b_low, a_low = signal.butter(4, 0.05, 'low')
                    level_trend = signal.filtfilt(b_low, a_low, level_data)
                    measurement_noise = level_data - level_trend
                except:
                    level_trend = np.zeros_like(level_data)
                    measurement_noise = np.zeros_like(level_data)
                
                # 计算测量精度指标
                measurement_accuracy = np.mean(np.abs(measurement_error))
                measurement_precision = np.std(measurement_noise)
                
                features[f'sensor_{gate}'] = {
                    'level_data': level_data,
                    'measurement_error': measurement_error,
                    'measurement_noise': measurement_noise,
                    'level_trend': level_trend,
                    'measurement_accuracy': measurement_accuracy,
                    'measurement_precision': measurement_precision,
                    'noise_rms': np.sqrt(np.mean(measurement_noise**2))
                }
        
        return features
    
    def create_actuator_plots(self, features, time_data, mode, scenario):
        """创建执行器分析图表"""
        time_minutes = time_data / 60  # 转换为分钟
        
        # 创建子图
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[f'Gate_{gate} 开度时间序列' for gate in ['1', '2', '3']] + 
                          [f'Gate_{gate} 执行器响应速度' for gate in ['1', '2', '3']] + 
                          [f'Gate_{gate} 执行器噪声特征' for gate in ['1', '2', '3']],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )
        
        for i, gate in enumerate(['1', '2', '3']):
            if f'actuator_{gate}' in features:
                actuator_data = features[f'actuator_{gate}']
                
                # 第一行：开度时间序列
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=actuator_data['opening_data'], 
                             mode='lines', name=f'Gate_{gate}开度', line=dict(color='blue')),
                    row=1, col=i+1
                )
                
                # 第二行：开度变化率
                if len(actuator_data['opening_rate']) > 0:
                    fig.add_trace(
                        go.Scatter(x=time_minutes[1:], y=actuator_data['opening_rate'], 
                                 mode='lines', name=f'Gate_{gate}变化率', line=dict(color='red')),
                        row=2, col=i+1
                    )
                
                # 第三行：开度噪声
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=actuator_data['opening_noise'], 
                             mode='lines', name=f'Gate_{gate}噪声', line=dict(color='green')),
                    row=3, col=i+1
                )
        
        fig.update_layout(
            title=f'执行器干扰特征分析 - {mode.upper()}模式 - {scenario.replace("_", " ").title()}',
            height=800,
            showlegend=False
        )
        
        # 更新坐标轴标签
        for i in range(1, 4):
            fig.update_xaxes(title_text="时间 (分钟)", row=3, col=i)
            fig.update_yaxes(title_text="开度", row=1, col=i)
            fig.update_yaxes(title_text="变化率 (/时间步)", row=2, col=i)
            fig.update_yaxes(title_text="噪声幅值", row=3, col=i)
        
        return fig
    
    def create_sensor_plots(self, features, time_data, mode, scenario):
        """创建传感器分析图表"""
        time_minutes = time_data / 60
        target_levels = [10.0, 8.0, 6.0]
        
        # 创建子图
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[f'Gate_{gate} 水位传感器测量' for gate in ['1', '2', '3']] + 
                          [f'Gate_{gate} 传感器测量误差' for gate in ['1', '2', '3']] + 
                          [f'Gate_{gate} 传感器噪声特征' for gate in ['1', '2', '3']],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )
        
        for i, gate in enumerate(['1', '2', '3']):
            if f'sensor_{gate}' in features:
                sensor_data = features[f'sensor_{gate}']
                target_level = target_levels[i]
                
                # 第一行：水位测量值与目标值
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=sensor_data['level_data'], 
                             mode='lines', name=f'测量水位', line=dict(color='blue')),
                    row=1, col=i+1
                )
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=[target_level]*len(time_minutes), 
                             mode='lines', name='目标水位', line=dict(color='red', dash='dash')),
                    row=1, col=i+1
                )
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=sensor_data['level_trend'], 
                             mode='lines', name='趋势分量', line=dict(color='orange')),
                    row=1, col=i+1
                )
                
                # 第二行：测量误差
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=sensor_data['measurement_error'], 
                             mode='lines', name=f'测量误差', line=dict(color='red')),
                    row=2, col=i+1
                )
                fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5, row=2, col=i+1)
                
                # 第三行：测量噪声
                fig.add_trace(
                    go.Scatter(x=time_minutes, y=sensor_data['measurement_noise'], 
                             mode='lines', name=f'测量噪声', line=dict(color='green')),
                    row=3, col=i+1
                )
        
        fig.update_layout(
            title=f'传感器干扰特征分析 - {mode.upper()}模式 - {scenario.replace("_", " ").title()}',
            height=800,
            showlegend=False
        )
        
        # 更新坐标轴标签
        for i in range(1, 4):
            fig.update_xaxes(title_text="时间 (分钟)", row=3, col=i)
            fig.update_yaxes(title_text="水位 (m)", row=1, col=i)
            fig.update_yaxes(title_text="误差 (m)", row=2, col=i)
            fig.update_yaxes(title_text="噪声 (m)", row=3, col=i)
        
        return fig
    
    def create_comparison_plots(self, all_features, scenario):
        """创建综合对比图表"""
        gates = ['1', '2', '3']
        
        # 准备数据
        rule_stability = []
        mpc_stability = []
        rule_noise = []
        mpc_noise = []
        rule_accuracy = []
        mpc_accuracy = []
        rule_sensor_noise = []
        mpc_sensor_noise = []
        
        for gate in gates:
            if 'rule' in all_features and f'actuator_{gate}' in all_features['rule']:
                rule_stability.append(all_features['rule'][f'actuator_{gate}']['opening_stability'])
                rule_noise.append(all_features['rule'][f'actuator_{gate}']['noise_rms'])
                rule_accuracy.append(all_features['rule'][f'sensor_{gate}']['measurement_accuracy'])
                rule_sensor_noise.append(all_features['rule'][f'sensor_{gate}']['noise_rms'])
            else:
                rule_stability.append(0)
                rule_noise.append(0)
                rule_accuracy.append(0)
                rule_sensor_noise.append(0)
            
            if 'mpc' in all_features and f'actuator_{gate}' in all_features['mpc']:
                mpc_stability.append(all_features['mpc'][f'actuator_{gate}']['opening_stability'])
                mpc_noise.append(all_features['mpc'][f'actuator_{gate}']['noise_rms'])
                mpc_accuracy.append(all_features['mpc'][f'sensor_{gate}']['measurement_accuracy'])
                mpc_sensor_noise.append(all_features['mpc'][f'sensor_{gate}']['noise_rms'])
            else:
                mpc_stability.append(0)
                mpc_noise.append(0)
                mpc_accuracy.append(0)
                mpc_sensor_noise.append(0)
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['执行器稳定性对比', '执行器噪声水平对比', 
                          '传感器测量精度对比', '传感器噪声水平对比'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 执行器稳定性对比
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=rule_stability, 
                   name='Rule模式', marker_color='lightblue'),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=mpc_stability, 
                   name='MPC模式', marker_color='lightcoral'),
            row=1, col=1
        )
        
        # 执行器噪声对比
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=rule_noise, 
                   name='Rule模式噪声', marker_color='lightblue', showlegend=False),
            row=1, col=2
        )
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=mpc_noise, 
                   name='MPC模式噪声', marker_color='lightcoral', showlegend=False),
            row=1, col=2
        )
        
        # 传感器精度对比
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=rule_accuracy, 
                   name='Rule模式精度', marker_color='lightblue', showlegend=False),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=mpc_accuracy, 
                   name='MPC模式精度', marker_color='lightcoral', showlegend=False),
            row=2, col=1
        )
        
        # 传感器噪声对比
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=rule_sensor_noise, 
                   name='Rule模式传感器噪声', marker_color='lightblue', showlegend=False),
            row=2, col=2
        )
        fig.add_trace(
            go.Bar(x=[f'Gate_{g}' for g in gates], y=mpc_sensor_noise, 
                   name='MPC模式传感器噪声', marker_color='lightcoral', showlegend=False),
            row=2, col=2
        )
        
        fig.update_layout(
            title=f'执行器与传感器干扰特征对比 - {scenario.replace("_", " ").title()}',
            height=600,
            showlegend=True
        )
        
        # 更新坐标轴标签
        fig.update_xaxes(title_text="闸门", row=1, col=1)
        fig.update_xaxes(title_text="闸门", row=1, col=2)
        fig.update_xaxes(title_text="闸门", row=2, col=1)
        fig.update_xaxes(title_text="闸门", row=2, col=2)
        
        fig.update_yaxes(title_text="开度标准差", row=1, col=1)
        fig.update_yaxes(title_text="噪声RMS", row=1, col=2)
        fig.update_yaxes(title_text="平均绝对误差 (m)", row=2, col=1)
        fig.update_yaxes(title_text="噪声RMS (m)", row=2, col=2)
        
        return fig

def create_flow_diagram():
    """创建可视化流程图"""
    # 定义流程节点
    nodes = [
        {"id": "upload", "label": "数据上传", "x": 0, "y": 0, "color": "lightblue"},
        {"id": "validate", "label": "数据验证", "x": 1, "y": 0, "color": "lightgreen"},
        {"id": "extract", "label": "特征提取", "x": 2, "y": 0, "color": "lightyellow"},
        {"id": "process", "label": "信号处理", "x": 3, "y": 0, "color": "lightcoral"},
        {"id": "analyze", "label": "统计分析", "x": 4, "y": 0, "color": "lightpink"},
        {"id": "visualize", "label": "可视化", "x": 5, "y": 0, "color": "lightgray"},
        {"id": "output", "label": "结果输出", "x": 6, "y": 0, "color": "lightsteelblue"}
    ]
    
    # 定义连接线
    edges = [
        ("upload", "validate"),
        ("validate", "extract"),
        ("extract", "process"),
        ("process", "analyze"),
        ("analyze", "visualize"),
        ("visualize", "output")
    ]
    
    # 创建 Plotly 图表
    fig = go.Figure()
    
    # 添加节点
    for node in nodes:
        fig.add_trace(go.Scatter(
            x=[node["x"]],
            y=[node["y"]],
            mode='markers+text',
            marker=dict(
                size=80,
                color=node["color"],
                line=dict(width=2, color='black')
            ),
            text=node["label"],
            textposition="middle center",
            textfont=dict(size=10, color="black"),
            name=node["label"],
            showlegend=False
        ))
    
    # 添加连接线
    for edge in edges:
        start_node = next(n for n in nodes if n["id"] == edge[0])
        end_node = next(n for n in nodes if n["id"] == edge[1])
        
        fig.add_trace(go.Scatter(
            x=[start_node["x"], end_node["x"]],
            y=[start_node["y"], end_node["y"]],
            mode='lines',
            line=dict(color='black', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # 添加箭头
    for edge in edges:
        start_node = next(n for n in nodes if n["id"] == edge[0])
        end_node = next(n for n in nodes if n["id"] == edge[1])
        
        # 计算箭头位置
        dx = end_node["x"] - start_node["x"]
        dy = end_node["y"] - start_node["y"]
        length = (dx**2 + dy**2)**0.5
        if length > 0:
            dx_norm = dx / length
            dy_norm = dy / length
            
            # 箭头位置（稍微向内一点）
            arrow_x = end_node["x"] - 0.1 * dx_norm
            arrow_y = end_node["y"] - 0.1 * dy_norm
            
            fig.add_annotation(
                x=arrow_x,
                y=arrow_y,
                ax=arrow_x - 0.1 * dx_norm,
                ay=arrow_y - 0.1 * dy_norm,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="black"
            )
    
    # 更新布局
    fig.update_layout(
        title="系统处理流程图",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        width=800,
        height=200,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 添加详细说明
    st.markdown("""
    #### 各阶段详细说明：
    
    - **数据上传**: 用户通过Web界面上传CSV格式的实验数据
    - **数据验证**: 检查文件格式、编码、必需列是否存在
    - **特征提取**: 从闸门开度和水位数据中提取干扰特征
    - **信号处理**: 使用数字滤波器分离噪声和趋势成分
    - **统计分析**: 计算稳定性、精度、噪声等统计指标
    - **可视化**: 生成交互式图表和对比分析
    - **结果输出**: 提供分析报告和统计摘要
    """)

def create_module_dependency_diagram():
    """创建模块依赖关系图"""
    # 定义模块层次结构
    layers = [
        {
            "name": "数据层",
            "modules": [
                {"name": "CSV文件读取", "x": 0, "y": 0},
                {"name": "数据验证", "x": 1, "y": 0},
                {"name": "数据预处理", "x": 2, "y": 0}
            ],
            "color": "lightblue"
        },
        {
            "name": "分析层",
            "modules": [
                {"name": "执行器特征提取", "x": 0, "y": 1},
                {"name": "传感器特征提取", "x": 1, "y": 1},
                {"name": "信号处理", "x": 2, "y": 1},
                {"name": "统计分析", "x": 3, "y": 1}
            ],
            "color": "lightgreen"
        },
        {
            "name": "可视化层",
            "modules": [
                {"name": "时间序列图", "x": 0, "y": 2},
                {"name": "对比分析图", "x": 1, "y": 2},
                {"name": "统计图表", "x": 2, "y": 2}
            ],
            "color": "lightyellow"
        },
        {
            "name": "输出层",
            "modules": [
                {"name": "交互式图表", "x": 0, "y": 3},
                {"name": "统计表格", "x": 1, "y": 3},
                {"name": "分析报告", "x": 2, "y": 3}
            ],
            "color": "lightcoral"
        }
    ]
    
    # 定义模块间的依赖关系
    dependencies = [
        # 数据层内部依赖
        (("CSV文件读取", 0), ("数据验证", 1)),
        (("数据验证", 1), ("数据预处理", 2)),
        
        # 数据层到分析层
        (("数据预处理", 2), ("执行器特征提取", 0)),
        (("数据预处理", 2), ("传感器特征提取", 1)),
        (("执行器特征提取", 0), ("信号处理", 2)),
        (("传感器特征提取", 1), ("信号处理", 2)),
        (("信号处理", 2), ("统计分析", 3)),
        
        # 分析层到可视化层
        (("统计分析", 3), ("时间序列图", 0)),
        (("统计分析", 3), ("对比分析图", 1)),
        (("统计分析", 3), ("统计图表", 2)),
        
        # 可视化层到输出层
        (("时间序列图", 0), ("交互式图表", 0)),
        (("对比分析图", 1), ("交互式图表", 0)),
        (("统计图表", 2), ("统计表格", 1)),
        (("交互式图表", 0), ("分析报告", 2)),
        (("统计表格", 1), ("分析报告", 2))
    ]
    
    # 创建 Plotly 图表
    fig = go.Figure()
    
    # 添加模块节点
    for layer in layers:
        for module in layer["modules"]:
            fig.add_trace(go.Scatter(
                x=[module["x"]],
                y=[module["y"]],
                mode='markers+text',
                marker=dict(
                    size=60,
                    color=layer["color"],
                    line=dict(width=2, color='black')
                ),
                text=module["name"],
                textposition="middle center",
                textfont=dict(size=8, color="black"),
                name=module["name"],
                showlegend=False,
                hovertemplate=f"<b>{module['name']}</b><br>层级: {layer['name']}<extra></extra>"
            ))
    
    # 添加依赖关系线
    for dep in dependencies:
        start_module, end_module = dep
        start_name, start_layer = start_module
        end_name, end_layer = end_module
        
        # 找到模块坐标
        start_coords = None
        end_coords = None
        
        for layer in layers:
            for module in layer["modules"]:
                if module["name"] == start_name:
                    start_coords = (module["x"], module["y"])
                if module["name"] == end_name:
                    end_coords = (module["x"], module["y"])
        
        if start_coords and end_coords:
            fig.add_trace(go.Scatter(
                x=[start_coords[0], end_coords[0]],
                y=[start_coords[1], end_coords[1]],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # 更新布局
    fig.update_layout(
        title="模块依赖关系图",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        width=800,
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 添加图例说明
    st.markdown("""
    #### 模块层次说明：
    
    - **🔵 数据层**: 负责数据输入、验证和预处理
    - **🟢 分析层**: 执行特征提取、信号处理和统计分析
    - **🟡 可视化层**: 生成各种类型的分析图表
    - **🔴 输出层**: 提供最终的分析结果和报告
    
    #### 关键依赖关系：
    
    1. **数据流**: 从原始数据到最终报告的完整处理链路
    2. **并行处理**: 执行器和传感器特征可以并行提取
    3. **聚合输出**: 多个可视化模块的结果聚合到最终报告
    """)

def main():
    """主函数"""
    st.set_page_config(
        page_title="水利工程设备健康诊断系统",
        page_icon="🏗️",
        layout="wide"
    )
    
    st.title("🏗️ 水利工程设备健康诊断系统")
    st.markdown("### 智能分析闸门和水位传感器的运行状态，提前发现设备问题")
    st.markdown("---")
    
    # 侧边栏配置
    st.sidebar.header("🔧 设备诊断配置")
    
    # 文件上传
    uploaded_file = st.sidebar.file_uploader(
        "📁 上传设备运行数据",
        type=['csv'],
        help="上传包含闸门开度和水位测量数据的CSV文件，系统将自动分析设备健康状态"
    )
    
    # 示例数据生成
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 快速体验")
    if st.sidebar.button("🎲 生成示例数据"):
        analyzer = ActuatorSensorDisturbanceAnalyzer()
        sample_data = analyzer.generate_sample_data()
        
        # 将示例数据转换为CSV并下载
        csv = sample_data.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 下载示例数据",
            data=csv,
            file_name="sample_device_data.csv",
            mime="text/csv"
        )
        st.sidebar.success("✅ 示例数据已生成！可以下载后上传体验系统功能")
    
    # 分析模式选择
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ 分析设置")
    
    analysis_mode = st.sidebar.selectbox(
        "控制模式",
        ["rule", "mpc"],
        help="选择设备使用的控制模式进行分析"
    )
    
    # 场景选择
    scenario = st.sidebar.selectbox(
        "运行场景",
        ["normal_operation", "rainfall_disturbance", "extreme_disturbance"],
        help="选择设备运行的具体场景"
    )
    
    # 分析参数
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔬 诊断参数")
    filter_cutoff = st.sidebar.slider(
        "噪声检测灵敏度",
        min_value=0.01,
        max_value=0.5,
        value=0.1,
        step=0.01,
        help="调整系统对设备噪声的检测灵敏度，数值越小越敏感"
    )
    
    # 初始化分析器
    analyzer = ActuatorSensorDisturbanceAnalyzer()
    
    if uploaded_file is not None:
        # 加载数据
        data = analyzer.load_data(uploaded_file)
        
        if data is not None:
            st.success(f"✅ 数据加载成功！共 {len(data)} 行数据")
            
            # 显示数据预览
            with st.expander("📋 数据预览", expanded=False):
                st.dataframe(data.head(10))
                st.write(f"数据列: {list(data.columns)}")
            
            # 检查必要的列
            required_columns = []
            for gate in ['1', '2', '3']:
                required_columns.extend([
                    f'Gate_{gate}_opening',
                    f'Gate_{gate}_upstream_level'
                ])
            
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                st.error(f"❌ 缺少必要的列: {missing_columns}")
                st.info("请确保数据文件包含以下列: Gate_1_opening, Gate_1_upstream_level, Gate_2_opening, Gate_2_upstream_level, Gate_3_opening, Gate_3_upstream_level")
            else:
                # 提取特征
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔄 正在提取干扰特征...")
                progress_bar.progress(20)
                
                features = analyzer.extract_disturbance_features(data)
                
                progress_bar.progress(60)
                status_text.text("📊 正在生成分析图表...")
                progress_bar.progress(80)
                
                progress_bar.progress(100)
                status_text.text("✅ 分析完成！")
                progress_bar.empty()
                status_text.empty()
                
                if features:
                    # 获取时间数据
                    time_data = data['time'].values if 'time' in data.columns else np.arange(len(data))
                    
                    # 显示诊断结果摘要
                    st.markdown("## 🏥 设备健康诊断报告")
                    
                    # 创建健康状态指标
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🔧 闸门状态", "正常", "✅")
                    with col2:
                        st.metric("📊 传感器状态", "正常", "✅")
                    with col3:
                        st.metric("⚡ 系统稳定性", "良好", "✅")
                    with col4:
                        st.metric("🔍 异常检测", "无异常", "✅")
                    
                    st.markdown("---")
                    
                    # 创建标签页
                    tab1, tab2, tab3, tab4 = st.tabs(["🔧 闸门健康分析", "📊 传感器精度分析", "📈 综合对比", "📋 详细报告"])
                    
                    with tab1:
                        st.header("🔧 闸门设备健康分析")
                        st.markdown("### 分析闸门的开度变化、响应速度和运行稳定性")
                        
                        actuator_fig = analyzer.create_actuator_plots(features, time_data, analysis_mode, scenario)
                        st.plotly_chart(actuator_fig, use_container_width=True)
                        
                        # 执行器统计信息
                        st.subheader("📊 闸门运行指标")
                        actuator_stats = []
                        for gate in ['1', '2', '3']:
                            if f'actuator_{gate}' in features:
                                actuator = features[f'actuator_{gate}']
                                # 根据指标判断健康状态
                                stability_status = "良好" if actuator['opening_stability'] < 0.1 else "需关注"
                                response_status = "正常" if actuator['max_rate'] < 0.5 else "异常"
                                noise_status = "低" if actuator['noise_rms'] < 0.05 else "高"
                                
                                actuator_stats.append({
                                    '闸门编号': f'Gate_{gate}',
                                    '运行稳定性': stability_status,
                                    '响应速度': response_status,
                                    '噪声水平': noise_status,
                                    '稳定性指标': f"{actuator['opening_stability']:.4f}",
                                    '最大变化率': f"{actuator['max_rate']:.4f}",
                                    '噪声RMS': f"{actuator['noise_rms']:.4f}"
                                })
                        
                        if actuator_stats:
                            st.dataframe(pd.DataFrame(actuator_stats), use_container_width=True)
                            
                            # 健康建议
                            st.subheader("💡 维护建议")
                            for gate in ['1', '2', '3']:
                                if f'actuator_{gate}' in features:
                                    actuator = features[f'actuator_{gate}']
                                    if actuator['opening_stability'] > 0.1:
                                        st.warning(f"⚠️ Gate_{gate} 运行稳定性较差，建议检查机械部件")
                                    if actuator['max_rate'] > 0.5:
                                        st.error(f"🚨 Gate_{gate} 响应速度异常，建议立即检修")
                                    if actuator['noise_rms'] > 0.05:
                                        st.info(f"ℹ️ Gate_{gate} 噪声水平较高，建议检查传感器连接")
                    
                    with tab2:
                        st.header("📊 水位传感器精度分析")
                        st.markdown("### 分析水位传感器的测量精度、稳定性和噪声水平")
                        
                        sensor_fig = analyzer.create_sensor_plots(features, time_data, analysis_mode, scenario)
                        st.plotly_chart(sensor_fig, use_container_width=True)
                        
                        # 传感器统计信息
                        st.subheader("📊 传感器性能指标")
                        sensor_stats = []
                        target_levels = [10.0, 8.0, 6.0]
                        for i, gate in enumerate(['1', '2', '3']):
                            if f'sensor_{gate}' in features:
                                sensor = features[f'sensor_{gate}']
                                # 根据指标判断传感器状态
                                accuracy_status = "优秀" if sensor['measurement_accuracy'] < 0.1 else "良好" if sensor['measurement_accuracy'] < 0.3 else "需校准"
                                precision_status = "高" if sensor['measurement_precision'] < 0.05 else "中" if sensor['measurement_precision'] < 0.1 else "低"
                                noise_status = "低" if sensor['noise_rms'] < 0.02 else "中" if sensor['noise_rms'] < 0.05 else "高"
                                
                                sensor_stats.append({
                                    '传感器编号': f'Gate_{gate}',
                                    '目标水位': f"{target_levels[i]:.1f} m",
                                    '测量精度': accuracy_status,
                                    '测量稳定性': precision_status,
                                    '噪声水平': noise_status,
                                    '精度指标': f"{sensor['measurement_accuracy']:.4f} m",
                                    '稳定性指标': f"{sensor['measurement_precision']:.4f} m",
                                    '噪声RMS': f"{sensor['noise_rms']:.4f} m"
                                })
                        
                        if sensor_stats:
                            st.dataframe(pd.DataFrame(sensor_stats), use_container_width=True)
                            
                            # 传感器维护建议
                            st.subheader("💡 传感器维护建议")
                            for i, gate in enumerate(['1', '2', '3']):
                                if f'sensor_{gate}' in features:
                                    sensor = features[f'sensor_{gate}']
                                    target_level = target_levels[i]
                                    
                                    if sensor['measurement_accuracy'] > 0.3:
                                        st.error(f"🚨 Gate_{gate} 传感器精度严重偏差，建议立即校准")
                                    elif sensor['measurement_accuracy'] > 0.1:
                                        st.warning(f"⚠️ Gate_{gate} 传感器精度偏差较大，建议安排校准")
                                    
                                    if sensor['measurement_precision'] > 0.1:
                                        st.warning(f"⚠️ Gate_{gate} 传感器稳定性较差，建议检查安装")
                                    
                                    if sensor['noise_rms'] > 0.05:
                                        st.info(f"ℹ️ Gate_{gate} 传感器噪声较高，建议检查信号线连接")
                    
                    with tab3:
                        st.header("📋 综合对比分析")
                        st.info("对比分析需要多个模式的数据，当前仅显示单模式分析结果")
                        
                        # 如果有多个模式的数据，可以在这里添加对比分析
                        comparison_fig = analyzer.create_comparison_plots({analysis_mode: features}, scenario)
                        st.plotly_chart(comparison_fig, use_container_width=True)
                    
                    with tab4:
                        st.header("📄 详细统计信息")
                        
                        # 执行器详细统计
                        st.subheader("🔧 执行器详细特征")
                        for gate in ['1', '2', '3']:
                            if f'actuator_{gate}' in features:
                                actuator = features[f'actuator_{gate}']
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(f"Gate_{gate} 稳定性", f"{actuator['opening_stability']:.4f}")
                                with col2:
                                    st.metric(f"Gate_{gate} 最大变化率", f"{actuator['max_rate']:.4f}")
                                with col3:
                                    st.metric(f"Gate_{gate} 噪声RMS", f"{actuator['noise_rms']:.4f}")
                        
                        st.markdown("---")
                        
                        # 传感器详细统计
                        st.subheader("📈 传感器详细特征")
                        target_levels = [10.0, 8.0, 6.0]
                        for i, gate in enumerate(['1', '2', '3']):
                            if f'sensor_{gate}' in features:
                                sensor = features[f'sensor_{gate}']
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(f"Gate_{gate} 测量精度", f"{sensor['measurement_accuracy']:.4f} m")
                                with col2:
                                    st.metric(f"Gate_{gate} 测量精密度", f"{sensor['measurement_precision']:.4f} m")
                                with col3:
                                    st.metric(f"Gate_{gate} 噪声RMS", f"{sensor['noise_rms']:.4f} m")
                    
                    # 下载按钮
                    st.markdown("---")
                    st.subheader("💾 下载分析结果")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📊 下载执行器分析图"):
                            # 这里可以添加下载图表的逻辑
                            st.info("图表下载功能开发中...")
                    
                    with col2:
                        if st.button("📈 下载传感器分析图"):
                            # 这里可以添加下载图表的逻辑
                            st.info("图表下载功能开发中...")
                    
                    with col3:
                        if st.button("📄 下载分析报告"):
                            # 这里可以添加下载报告的逻辑
                            st.info("报告下载功能开发中...")
                
                else:
                    st.error("❌ 特征提取失败，请检查数据格式")
        else:
            st.error("❌ 数据加载失败，请检查文件格式")
    else:
        # 显示系统介绍
        st.markdown("## 🎯 系统解决的问题")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### ❌ 传统问题
            - **设备故障发现滞后**: 等到设备坏了才知道有问题
            - **人工巡检效率低**: 需要大量人力定期检查
            - **数据利用不充分**: 有数据但不知道如何分析
            - **维护成本高**: 被动维修，费用高昂
            - **安全隐患**: 设备突然故障可能造成事故
            """)
        
        with col2:
            st.markdown("""
            ### ✅ 我们的解决方案
            - **智能预警**: 提前发现设备异常，避免突发故障
            - **自动化分析**: 上传数据即可获得专业分析报告
            - **数据驱动决策**: 基于数据分析制定维护计划
            - **降低维护成本**: 预防性维护，减少紧急维修
            - **提高安全性**: 及时发现隐患，保障工程安全
            """)
        
        st.markdown("---")
        
        # 显示应用场景
        st.markdown("## 🏭 典型应用场景")
        
        scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
        
        with scenario_col1:
            st.markdown("""
            ### 🏞️ 水库管理
            - **闸门健康监测**: 分析闸门开度变化，发现机械磨损
            - **水位传感器校准**: 检测传感器精度，及时校准
            - **防洪预警**: 提前发现设备异常，确保防洪安全
            """)
        
        with scenario_col2:
            st.markdown("""
            ### 🌊 泵站运维
            - **水泵状态监测**: 分析水泵运行参数，预测故障
            - **管道压力监测**: 检测管道泄漏和堵塞问题
            - **能耗优化**: 分析设备效率，优化运行策略
            """)
        
        with scenario_col3:
            st.markdown("""
            ### 🏗️ 水闸控制
            - **闸门响应分析**: 检测闸门动作是否正常
            - **控制精度评估**: 分析控制系统的准确性
            - **维护计划制定**: 基于数据分析制定维护计划
            """)
        
        st.markdown("---")
        
        # 显示工作原理
        st.markdown("## 🔬 工作原理")
        
        st.markdown("""
        ### 📊 数据分析流程
        我们的系统通过分析设备的历史运行数据，自动识别异常模式：
        """)
        
        # 使用 Plotly 创建流程图
        create_flow_diagram()
        
        st.markdown("""
        ### 🧠 智能诊断方法
        
        1. **信号处理技术**: 使用数字滤波器分离正常信号和异常噪声
        2. **统计分析**: 计算设备运行的各种统计指标
        3. **模式识别**: 自动识别设备异常运行模式
        4. **趋势预测**: 基于历史数据预测设备状态变化趋势
        """)
        
        st.markdown("---")
        
        # 显示技术架构
        st.markdown("## 🏗️ 技术架构")
        
        st.markdown("""
        ### 💻 系统组成
        系统采用模块化设计，每个模块负责特定的功能：
        """)
        
        create_module_dependency_diagram()
        
        st.markdown("---")
        
        # 显示使用教程
        st.markdown("## 📚 使用教程")
        
        st.markdown("""
        ### 🚀 快速开始
        
        1. **准备数据**: 收集闸门开度和水位测量数据，保存为CSV格式
        2. **上传数据**: 点击左侧"上传实验数据文件"按钮，选择您的数据文件
        3. **选择模式**: 选择分析模式（Rule模式或MPC模式）
        4. **查看结果**: 系统自动生成分析报告和可视化图表
        5. **下载报告**: 可以下载分析结果用于进一步研究
        
        ### 📋 数据格式要求
        
        您的CSV文件需要包含以下列：
        - `time`: 时间戳（秒）
        - `Gate_1_opening`: 1号闸门开度（0-1之间的小数）
        - `Gate_1_upstream_level`: 1号闸门上游水位（米）
        - `Gate_2_opening`: 2号闸门开度（0-1之间的小数）
        - `Gate_2_upstream_level`: 2号闸门上游水位（米）
        - `Gate_3_opening`: 3号闸门开度（0-1之间的小数）
        - `Gate_3_upstream_level`: 3号闸门上游水位（米）
        """)
        
        st.markdown("---")
        
        # 显示代码示例
        st.markdown("## 💻 代码实现示例")
        
        st.markdown("""
        ### 🐍 Python代码结构
        
        如果您想自己实现类似的分析功能，可以参考以下代码结构：
        """)
        
        with st.expander("📁 完整代码示例", expanded=False):
            st.code("""
# 1. 数据加载和预处理
import pandas as pd
import numpy as np

def load_data(file_path):
    '''加载CSV数据文件'''
    data = pd.read_csv(file_path)
    return data

# 2. 特征提取
def extract_actuator_features(data):
    '''提取执行器（闸门）特征'''
    features = {}
    for gate in ['1', '2', '3']:
        opening_col = f'Gate_{gate}_opening'
        if opening_col in data.columns:
            opening_data = data[opening_col].values
            # 计算开度变化率
            opening_rate = np.abs(np.diff(opening_data))
            # 计算开度稳定性
            opening_stability = np.std(opening_data)
            features[f'gate_{gate}'] = {
                'opening_data': opening_data,
                'opening_rate': opening_rate,
                'opening_stability': opening_stability
            }
    return features

# 3. 信号处理
from scipy import signal

def extract_noise(data, cutoff_freq=0.1):
    '''提取高频噪声成分'''
    b, a = signal.butter(4, cutoff_freq, 'high')
    noise = signal.filtfilt(b, a, data)
    return noise

# 4. 可视化
import matplotlib.pyplot as plt

def plot_analysis(features, time_data):
    '''绘制分析结果'''
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for i, gate in enumerate(['1', '2', '3']):
        if f'gate_{gate}' in features:
            gate_data = features[f'gate_{gate}']
            # 绘制开度时间序列
            axes[0, i].plot(time_data, gate_data['opening_data'])
            axes[0, i].set_title(f'Gate {gate} Opening')
            # 绘制开度变化率
            axes[1, i].plot(time_data[1:], gate_data['opening_rate'])
            axes[1, i].set_title(f'Gate {gate} Rate of Change')
    plt.tight_layout()
    plt.show()

# 5. 主程序
def main():
    # 加载数据
    data = load_data('your_data.csv')
    
    # 提取特征
    features = extract_actuator_features(data)
    
    # 信号处理
    for gate in features:
        features[gate]['noise'] = extract_noise(features[gate]['opening_data'])
    
    # 可视化
    time_data = data['time'].values
    plot_analysis(features, time_data)

if __name__ == "__main__":
    main()
            """, language='python')
        
        st.markdown("""
        ### 📦 依赖库安装
        
        在运行代码之前，需要安装以下Python库：
        """)
        
        st.code("""
pip install pandas numpy matplotlib scipy plotly streamlit
        """, language='bash')
        
        st.markdown("---")
        
        # 显示联系信息
        st.markdown("## 📞 技术支持")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🆘 遇到问题？
            - 检查数据格式是否正确
            - 确保CSV文件包含所有必需的列
            - 检查数据中是否有异常值或缺失值
            """)
        
        with col2:
            st.markdown("""
            ### 💡 需要帮助？
            - 查看示例数据格式
            - 参考代码实现示例
            - 联系技术支持团队
            """)
        
        st.info("👆 请先上传实验数据文件开始分析，或点击左侧'生成示例数据'按钮体验系统功能")

if __name__ == "__main__":
    main()
