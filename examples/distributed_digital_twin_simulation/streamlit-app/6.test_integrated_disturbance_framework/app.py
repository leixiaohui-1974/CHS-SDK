#!/usr/bin/env python3
"""Streamlit 可视化：集成扰动框架测试

此页面对应 `6.test_integrated_disturbance_framework.py` 的业务逻辑，
提供无需写代码的交互式操作：
- 加载仿真环境
- 设定入流扰动参数
- 添加扰动并执行仿真
- 显示关键时间点与完整时序的结果与图表
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

# 当前脚本所在目录
CURRENT_DIR = Path(__file__).resolve().parent
# 项目根目录 (E:\CHS-SDK)
PROJECT_ROOT = CURRENT_DIR.parents[2]   # 回到 E:\CHS-SDK

# 添加 core_lib 到 sys.path
sys.path.append(str(PROJECT_ROOT / "core_lib"))

# 尽力寻找项目根目录以导入核心模块
def _ensure_project_root_on_path() -> None:
    current = Path(__file__).resolve()
    # 优先加入数层父目录，直到找到 `core_lib` 目录
    for ancestor in [current.parent, *current.parents]:
        candidate = ancestor
        if (candidate / "core_lib").exists():
            sys.path.insert(0, str(candidate))
            return

_ensure_project_root_on_path()

try:
    from core_lib.io.yaml_loader import SimulationBuilder
    from core_lib.disturbances.disturbance_framework import (
        DisturbanceConfig,
        DisturbanceType,
        create_disturbance,
    )
    CORE_LIB_AVAILABLE = True
except ImportError as e:
    CORE_LIB_AVAILABLE = False
    st.error(f"⚠️ 核心库导入失败: {e}")

# 日志设定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置页面
st.set_page_config(
    page_title="集成扰动框架测试系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_business_flow_diagram():
    """创建业务流程图"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 创建有向图
    G = nx.DiGraph()
    
    # 添加节点
    nodes = [
        ("加载仿真", {"pos": (0, 4), "color": "#FF6B6B"}),
        ("选择组件", {"pos": (2, 4), "color": "#4ECDC4"}),
        ("配置扰动", {"pos": (4, 4), "color": "#45B7D1"}),
        ("设置监控", {"pos": (6, 4), "color": "#96CEB4"}),
        ("执行仿真", {"pos": (8, 4), "color": "#FECA57"}),
        ("数据分析", {"pos": (4, 2), "color": "#FF9FF3"}),
        ("结果展示", {"pos": (6, 2), "color": "#54A0FF"}),
        ("生成报告", {"pos": (8, 2), "color": "#5F27CD"})
    ]
    
    for node, attrs in nodes:
        G.add_node(node, **attrs)
    
    # 添加边
    edges = [
        ("加载仿真", "选择组件"),
        ("选择组件", "配置扰动"), 
        ("配置扰动", "设置监控"),
        ("设置监控", "执行仿真"),
        ("执行仿真", "数据分析"),
        ("数据分析", "结果展示"),
        ("结果展示", "生成报告")
    ]
    
    G.add_edges_from(edges)
    
    # 绘制图
    pos = nx.get_node_attributes(G, 'pos')
    colors = [G.nodes[node]['color'] for node in G.nodes()]
    
    # 清除坐标轴
    ax.set_xlim(-1, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # 绘制节点和边
    nx.draw(G, pos, ax=ax, 
            node_color=colors,
            node_size=3000,
            font_size=10,
            font_weight='bold',
            font_color='white',
            with_labels=True,
            edge_color='#2C3E50',
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            width=2)
    
    # 添加标题
    ax.set_title("集成扰动框架测试业务流程", fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

def load_simulation_harness(scenario_path: str):
    """加载仿真环境"""
    builder = SimulationBuilder(scenario_path=scenario_path)
    harness = builder.load()
    return harness

def build_disturbance_config(
    disturbance_id: str,
    target_component_id: str,
    start_time: float,
    end_time: float,
    target_inflow: float,
    intensity: float,
    description: str,
):
    return DisturbanceConfig(
        disturbance_id=disturbance_id,
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id=target_component_id,
        start_time=start_time,
        end_time=end_time,
        intensity=intensity,
        parameters={
            'target_inflow': float(target_inflow)
        },
        description=description,
    )

def find_closest_time_point(current_time: float, key_times: List[float], tolerance: float = 0.2) -> float:
    """找到最接近的关键时间点"""
    for key_time in key_times:
        if abs(current_time - key_time) <= tolerance:
            return key_time
    return None

def run_simulation(harness, upstream_id: str, key_times: List[float]):
    """执行仿真并返回完整时序与关键快照"""
    upstream = harness.components[upstream_id]
    
    timeline_records: List[Dict[str, Any]] = []
    key_snapshots: Dict[float, Dict[str, Any]] = {}
    captured_times = set()  # 记录已捕获的关键时间点
    
    # 增加容差和智能匹配
    tolerance = 0.3  # 增加容差到0.3秒
    
    # 以时间步进到 end_time
    while harness.t < harness.end_time:
        state = upstream.get_state()
        record = {
            'time': harness.t,
            'water_level': state.get('water_level', 0.0),
            'volume': state.get('volume', 0.0),
            'inflow': getattr(upstream, '_inflow', 0.0),
            'active_disturbances': len(harness.get_active_disturbances())
        }
        timeline_records.append(record)
        
        # 改进的关键时间点捕获逻辑
        closest_key_time = find_closest_time_point(harness.t, key_times, tolerance)
        if closest_key_time is not None and closest_key_time not in captured_times:
            key_snapshots[closest_key_time] = record.copy()
            captured_times.add(closest_key_time)
        
        harness.step()
    
    # 最终状态再记录一次（避免错过 end_time）
    state = upstream.get_state()
    final_record = {
        'time': harness.t,
        'water_level': state.get('water_level', 0.0),
        'volume': state.get('volume', 0.0),
        'inflow': getattr(upstream, '_inflow', 0.0),
        'active_disturbances': len(harness.get_active_disturbances())
    }
    timeline_records.append(final_record)
    
    # 检查是否还有未捕获的关键时间点
    for key_time in key_times:
        if key_time not in captured_times:
            # 找到时序中最接近的记录
            closest_record = min(timeline_records, 
                                key=lambda r: abs(r['time'] - key_time))
            if abs(closest_record['time'] - key_time) <= tolerance * 2:
                key_snapshots[key_time] = closest_record.copy()
    
    return timeline_records, key_snapshots

def create_enhanced_visualizations(df: pd.DataFrame, key_snapshots: Dict, disturbance_start: float, disturbance_end: float):
    """创建增强的可视化图表"""
    # 创建子图
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=('水位变化趋势', '入流量变化', '体积变化', '活跃扰动数量', '扰动效果分析', '关键时间点对比'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"colspan": 2}, None]],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # 水位变化图
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['water_level'], 
                  mode='lines+markers', name='水位', 
                  line=dict(color='blue', width=2),
                  marker=dict(size=4)),
        row=1, col=1
    )
    
    # 入流量变化图
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['inflow'], 
                  mode='lines+markers', name='入流量',
                  line=dict(color='green', width=2),
                  marker=dict(size=4)),
        row=1, col=2
    )
    
    # 体积变化图
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['volume'], 
                  mode='lines+markers', name='体积',
                  line=dict(color='orange', width=2),
                  marker=dict(size=4)),
        row=2, col=1
    )
    
    # 活跃扰动数量图
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['active_disturbances'], 
                  mode='lines+markers', name='活跃扰动数',
                  line=dict(color='red', width=2),
                  marker=dict(size=6)),
        row=2, col=2
    )
    
    # 扰动效果分析（水位变化量）
    if not df.empty:
        baseline_level = df['water_level'].iloc[0]
        level_changes = (df['water_level'] - baseline_level) * 1000  # 转换为mm
        
        fig.add_trace(
            go.Scatter(x=df['time'], y=level_changes, 
                      mode='lines+markers', name='水位变化量 (mm)',
                      line=dict(color='purple', width=2),
                      marker=dict(size=4)),
            row=3, col=1
        )
    
    # 添加扰动区间标识
    for row in range(1, 4):
        for col in range(1, 3):
            if row == 3 and col == 2:
                continue
            fig.add_vrect(
                x0=disturbance_start, x1=disturbance_end,
                fillcolor="rgba(255,0,0,0.2)", opacity=0.3,
                annotation_text="扰动期间" if row == 1 and col == 1 else "",
                annotation_position="top left",
                row=row, col=col
            )
    
    # 标记关键时间点
    if key_snapshots:
        for key_time, snapshot in key_snapshots.items():
            # 在水位图上标记
            fig.add_trace(
                go.Scatter(x=[key_time], y=[snapshot['water_level']],
                          mode='markers+text', name=f't={key_time}s',
                          marker=dict(size=12, color='red', symbol='star'),
                          text=[f'{key_time}s'],
                          textposition='top center',
                          showlegend=False),
                row=1, col=1
            )
    
    # 更新布局
    fig.update_layout(
        title="集成扰动框架测试结果综合分析",
        height=800,
        showlegend=True
    )
    
    # 更新坐标轴标签
    fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
    fig.update_yaxes(title_text="入流量 (m³/s)", row=1, col=2)
    fig.update_yaxes(title_text="体积 (m³)", row=2, col=1)
    fig.update_yaxes(title_text="扰动数量", row=2, col=2)
    fig.update_yaxes(title_text="水位变化量 (mm)", row=3, col=1)
    
    fig.update_xaxes(title_text="时间 (s)", row=3, col=1)
    
    return fig

def create_key_points_analysis(key_snapshots: Dict):
    """创建关键时间点分析"""
    if not key_snapshots:
        return None
    
    # 转换为DataFrame
    key_data = []
    for time, snapshot in sorted(key_snapshots.items()):
        key_data.append({
            '时间(s)': time,
            '水位(m)': snapshot['water_level'],
            '入流量(m³/s)': snapshot['inflow'],
            '体积(m³)': snapshot['volume'],
            '活跃扰动数': snapshot['active_disturbances']
        })
    
    key_df = pd.DataFrame(key_data)
    
    # 计算变化量
    if len(key_df) > 1:
        key_df['水位变化(mm)'] = (key_df['水位(m)'] - key_df['水位(m)'].iloc[0]) * 1000
        key_df['入流变化(m³/s)'] = key_df['入流量(m³/s)'] - key_df['入流量(m³/s)'].iloc[0]
        key_df['体积变化(m³)'] = key_df['体积(m³)'] - key_df['体积(m³)'].iloc[0]
    
    return key_df

def main():
    st.title("⚙️ 集成扰动框架测试系统")
    st.markdown("---")
    
    # 显示业务流程图
    st.subheader("📋 业务流程图")
    with st.expander("查看详细业务流程", expanded=False):
        if 'matplotlib' in sys.modules:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            flow_fig = create_business_flow_diagram()
            st.pyplot(flow_fig)
        else:
            st.info("流程图需要matplotlib支持，请安装后查看")
        
        st.markdown("""
        **业务流程说明：**
        1. **加载仿真** - 从YAML配置加载仿真环境
        2. **选择组件** - 选择要施加扰动的目标组件
        3. **配置扰动** - 设置扰动类型、强度、时间等参数
        4. **设置监控** - 配置关键时间点和监控指标
        5. **执行仿真** - 运行仿真并应用扰动
        6. **数据分析** - 分析仿真结果和扰动效果
        7. **结果展示** - 生成图表和可视化结果
        8. **生成报告** - 输出测试报告和结论
        """)
    
    # 预设场景路径
    default_scenario = str(Path(__file__).resolve().parent.parent.parent)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🔧 配置参数")
        
        # 1. 加载仿真环境
        st.subheader("1️⃣ 加载仿真环境")
        scenario_path = st.text_input("场景路径", value=default_scenario, help="仿真环境YAML配置文件所在目录")
        load_clicked = st.button("🚀 加载仿真环境", type="primary", use_container_width=True)
        
        st.divider()
        
        # 2. 扰动参数设定
        st.subheader("2️⃣ 扰动参数设定")
        disturbance_id = st.text_input("扰动ID", value="test_inflow_disturbance", help="扰动的唯一标识")
        
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input("开始时间 (s)", value=10.0, step=0.5, min_value=0.0, help="扰动开始时间")
            intensity = st.number_input("强度倍率", value=1.0, step=0.1, min_value=0.1, help="扰动强度系数")
        with col2:
            end_time = st.number_input("结束时间 (s)", value=15.0, step=0.5, min_value=start_time+0.5, help="扰动结束时间")
            target_inflow = st.number_input("目标入流 (m³/s)", value=5100.0, step=100.0, help="扰动后的目标入流量")
        
        description = st.text_area("描述", value="测试入流扰动：增加入流到5100 m³/s", help="扰动的详细描述")
        
        st.divider()
        
        # 3. 监测与执行
        st.subheader("3️⃣ 监测与执行")
        key_times_str = st.text_input("关键时间点 (逗号分隔)", value="9,10,12.5,15,16", 
                                    help="需要重点监测的时间点，用逗号分隔")
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            tolerance = st.slider("时间点容差 (s)", 0.1, 1.0, 0.3, 0.1, help="关键时间点的匹配容差")
            max_simulation_time = st.number_input("最大仿真时间 (s)", value=25.0, step=1.0, help="仿真的最大运行时间")
        
        run_clicked = st.button("▶️ 添加扰动并执行仿真", type="primary", use_container_width=True)
    
    # 状态保存
    if 'harness' not in st.session_state:
        st.session_state.harness = None
        st.session_state.components = []
        st.session_state.last_results = None
    
    # 主内容区域
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 系统状态")
        
        # 加载仿真
        if load_clicked:
            if not CORE_LIB_AVAILABLE:
                st.error("❌ 核心库不可用，无法加载仿真环境")
            else:
                try:
                    with st.spinner("正在加载仿真环境..."):
                        harness = load_simulation_harness(scenario_path)
                        st.session_state.harness = harness
                        st.session_state.components = list(harness.components.keys())
                    st.success("✅ 仿真环境加载成功！")
                    st.balloons()
                except Exception as e:
                    st.session_state.harness = None
                    st.session_state.components = []
                    st.error(f"❌ 加载失败：{e}")
        
        # 显示系统信息
        if st.session_state.harness is None:
            st.info("🔄 请在左侧加载仿真环境")
            st.markdown("**状态**: 未加载")
        else:
            st.success("**状态**: 已加载")
            st.markdown(f"**组件数量**: {len(st.session_state.components)}")
            st.markdown(f"**当前时间**: {st.session_state.harness.t:.2f}s")
            st.markdown(f"**结束时间**: {st.session_state.harness.end_time:.2f}s")
        
        # 可用组件
        st.subheader("🎯 可用组件")
        if st.session_state.components:
            components_df = pd.DataFrame({
                '组件ID': st.session_state.components,
                '类型': ['水库组件' if 'Reservoir' in comp else '其他组件' for comp in st.session_state.components]
            })
            st.dataframe(components_df, use_container_width=True)
        else:
            st.info("暂无可用组件")
    
    with col2:
        st.subheader("🎯 目标组件选择")
        if st.session_state.harness is None:
            st.info("请先在左侧加载仿真环境")
            target_component_id = None
        else:
            # 智能选择默认目标组件
            default_target = None
            for comp in st.session_state.components:
                if "Upstream_Reservoir" in comp:
                    default_target = comp
                    break
                elif "Reservoir" in comp:
                    default_target = comp
                    break
            
            if not default_target and st.session_state.components:
                default_target = st.session_state.components[0]
            
            if default_target:
                default_index = st.session_state.components.index(default_target)
            else:
                default_index = 0
            
            target_component_id = st.selectbox(
                "选择目标组件", 
                options=st.session_state.components, 
                index=default_index,
                help="选择要施加扰动的组件"
            )
            
            # 显示组件信息
            if target_component_id:
                st.info(f"**已选择**: {target_component_id}")
                st.markdown("**扰动类型**: 入流变化扰动")
                st.markdown(f"**扰动时间**: {start_time:.1f}s - {end_time:.1f}s")
                st.markdown(f"**目标入流**: {target_inflow:.0f} m³/s")
    
    st.divider()
    
    # 执行结果区域
    st.subheader("📊 执行结果")
    
    if run_clicked:
        if not CORE_LIB_AVAILABLE:
            st.error("❌ 核心库不可用，无法执行仿真")
            st.stop()
            
        if st.session_state.harness is None:
            st.error("❌ 尚未加载仿真环境，请先加载")
            st.stop()
        
        try:
            # 显示执行信息
            with st.expander("📝 执行配置信息", expanded=True):
                config_col1, config_col2 = st.columns(2)
                with config_col1:
                    st.markdown(f"**扰动ID**: {disturbance_id}")
                    st.markdown(f"**目标组件**: {target_component_id}")
                    st.markdown(f"**扰动时间**: {start_time:.1f}s - {end_time:.1f}s")
                    st.markdown(f"**扰动持续**: {end_time - start_time:.1f}s")
                with config_col2:
                    st.markdown(f"**目标入流**: {target_inflow:.0f} m³/s")
                    st.markdown(f"**强度倍率**: {intensity:.1f}")
                    st.markdown(f"**时间容差**: {tolerance:.1f}s")
                    st.markdown(f"**监测点**: {key_times_str}")
            
            # 创建扰动配置
            cfg = build_disturbance_config(
                disturbance_id=disturbance_id,
                target_component_id=target_component_id,
                start_time=float(start_time),
                end_time=float(end_time),
                target_inflow=float(target_inflow),
                intensity=float(intensity),
                description=description,
            )
            
            disturbance = create_disturbance(cfg)
            
            # 添加扰动
            st.session_state.harness.add_disturbance(disturbance)
            
            # 解析关键时间
            try:
                key_times = [float(x.strip()) for x in key_times_str.split(',') if x.strip()]
            except Exception:
                key_times = [9.0, 10.0, 12.5, 15.0, 16.0]
                st.warning("⚠️ 关键时间点解析失败，使用默认值")
            
            # 执行仿真
            with st.spinner("🔄 仿真执行中，请稍候..."):
                timeline_records, key_snapshots = run_simulation(
                    st.session_state.harness,
                    upstream_id=target_component_id,
                    key_times=key_times,
                )
            
            # 保存结果
            df = pd.DataFrame(timeline_records)
            st.session_state.last_results = {
                'dataframe': df,
                'key_snapshots': key_snapshots,
                'config': cfg,
                'timestamp': datetime.now()
            }
            
            st.success("✅ 仿真执行完成！")
            st.balloons()
            
            # 关键指标展示
            st.subheader("📈 关键性能指标")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                if not df.empty:
                    initial_level = df['water_level'].iloc[0]
                    final_level = df['water_level'].iloc[-1]
                    level_change = (final_level - initial_level) * 1000
                    st.metric("水位变化", f"{level_change:.3f} mm", f"{final_level:.3f} m")
            
            with metric_col2:
                if not df.empty:
                    initial_inflow = df['inflow'].iloc[0]
                    max_inflow = df['inflow'].max()
                    inflow_increase = max_inflow - initial_inflow
                    st.metric("最大入流增量", f"{inflow_increase:.0f} m³/s", f"峰值: {max_inflow:.0f}")
            
            with metric_col3:
                captured_points = len(key_snapshots)
                total_points = len(key_times)
                capture_rate = (captured_points / total_points * 100) if total_points > 0 else 0
                st.metric("关键点捕获率", f"{capture_rate:.0f}%", f"{captured_points}/{total_points}")
            
            with metric_col4:
                if not df.empty:
                    simulation_duration = df['time'].iloc[-1] - df['time'].iloc[0]
                    st.metric("仿真时长", f"{simulation_duration:.1f}s", f"步数: {len(df)}")
            
            # 关键时间点分析
            st.subheader("🎯 关键时间点分析")
            
            if key_snapshots:
                st.success(f"✅ 成功捕获 {len(key_snapshots)} 个关键时间点")
                
                # 创建关键时间点分析表
                key_analysis_df = create_key_points_analysis(key_snapshots)
                if key_analysis_df is not None:
                    st.dataframe(key_analysis_df, use_container_width=True)
                
                # 关键时间点对比分析
                if len(key_snapshots) >= 2:
                    times = sorted(key_snapshots.keys())
                    initial_snapshot = key_snapshots[times[0]]
                    final_snapshot = key_snapshots[times[-1]]
                    
                    st.markdown("**首末对比分析**")
                    comparison_col1, comparison_col2, comparison_col3 = st.columns(3)
                    
                    with comparison_col1:
                        water_change = (final_snapshot['water_level'] - initial_snapshot['water_level']) * 1000
                        st.metric(f"水位变化 ({times[0]}s→{times[-1]}s)", f"{water_change:.3f} mm")
                    
                    with comparison_col2:
                        inflow_change = final_snapshot['inflow'] - initial_snapshot['inflow']
                        st.metric(f"入流变化 ({times[0]}s→{times[-1]}s)", f"{inflow_change:.0f} m³/s")
                    
                    with comparison_col3:
                        volume_change = final_snapshot['volume'] - initial_snapshot['volume']
                        st.metric(f"体积变化 ({times[0]}s→{times[-1]}s)", f"{volume_change:.0f} m³")
                        
            else:
                st.warning("⚠️ 未能捕获关键时间点")
                st.info(f"💡 建议调整时间容差（当前: {tolerance}s）或检查关键时间点设置")
            
            # 增强可视化图表
            st.subheader("📊 详细结果可视化")
            
            if not df.empty:
                enhanced_fig = create_enhanced_visualizations(df, key_snapshots, start_time, end_time)
                st.plotly_chart(enhanced_fig, use_container_width=True)
            
            # 扰动历史分析
            st.subheader("📜 扰动历史分析")
            
            try:
                history = st.session_state.harness.get_disturbance_history()
                st.info(f"📊 扰动历史记录数量: {len(history)}")
                
                if history:
                    # 显示最近的扰动记录
                    show_n = min(10, len(history))
                    history_df = pd.DataFrame(history[:show_n])
                    if not history_df.empty:
                        st.dataframe(history_df, use_container_width=True)
                else:
                    st.warning("暂无扰动历史记录")
            except Exception as e:
                st.warning(f"获取扰动历史失败: {e}")
            
            # 数据导出
            st.subheader("💾 数据导出")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if not df.empty:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 下载时序数据 (CSV)",
                        data=csv_data,
                        file_name=f"simulation_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with export_col2:
                if key_snapshots:
                    key_csv_data = pd.DataFrame([
                        {"time": t, **data} for t, data in sorted(key_snapshots.items())
                    ]).to_csv(index=False)
                    st.download_button(
                        label="📥 下载关键点数据 (CSV)",
                        data=key_csv_data,
                        file_name=f"key_snapshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
        except Exception as e:
            logger.exception("执行失败")
            st.error(f"❌ 执行失败: {e}")
            st.exception(e)
    
    # 历史结果查看
    if st.session_state.last_results is not None:
        st.divider()
        st.subheader("📋 最近执行结果")
        
        with st.expander("查看最近一次执行的详细结果", expanded=False):
            last_df = st.session_state.last_results['dataframe']
            last_snapshots = st.session_state.last_results['key_snapshots']
            last_timestamp = st.session_state.last_results['timestamp']
            
            st.markdown(f"**执行时间**: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**数据点数量**: {len(last_df)}")
            st.markdown(f"**关键点数量**: {len(last_snapshots)}")
            
            if not last_df.empty:
                st.line_chart(last_df.set_index('time')[['water_level', 'inflow']])
    
    # 使用说明
    with st.expander("📖 使用说明", expanded=False):
        st.markdown("""
        ### 🚀 快速开始
        1. **加载环境**: 在左侧输入场景路径，点击"加载仿真环境"
        2. **配置扰动**: 设置扰动参数（开始/结束时间、强度、目标入流等）
        3. **设置监控**: 配置关键时间点和监控容差
        4. **执行仿真**: 点击"添加扰动并执行仿真"
        5. **分析结果**: 查看关键指标、图表和详细分析
        
        ### 📊 功能特色
        - **智能时间点捕获**: 自动调整容差，确保关键时间点不遗漏
        - **丰富可视化**: 多维度图表展示仿真结果
        - **实时指标**: 关键性能指标实时计算和展示
        - **数据导出**: 支持CSV格式数据导出
        - **历史记录**: 保存和查看历史执行结果
        
        ### 🔧 故障排除
        - **未捕获关键点**: 调整时间容差或检查时间点设置
        - **仿真报错**: 检查场景路径和配置文件
        - **图表异常**: 确认数据完整性和参数合理性
        - **性能问题**: 减少仿真时间或降低监控点密度
        
        ### 💡 最佳实践
        - 建议时间容差设置为0.2-0.5秒
        - 关键时间点应覆盖扰动前、中、后各阶段
        - 扰动强度建议从小到大逐步测试
        - 定期导出和备份重要测试数据
        """)

if __name__ == "__main__":
    main()