#!/usr/bin/env python3
"""分布式数字孪生仿真 - 多种扰动类型测试的Streamlit界面

这个应用提供了一个直观的界面来测试和可视化不同类型的扰动对水库系统的影响：
1. 入流扰动：改变水库入流量
2. 传感器噪声扰动：对传感器读数添加噪声
3. 多扰动同时作用：观察多个扰动的交互影响
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import yaml
import logging
from pathlib import Path
from datetime import datetime



import sys
from pathlib import Path

def find_core_lib(start: Path) -> Path:
    for parent in start.resolve().parents:
        candidate = parent / "core_lib"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("core_lib not found")

CORE_LIB_PATH = find_core_lib(Path(__file__).parent)
print(f"CORE_LIB_PATH: {CORE_LIB_PATH}")
sys.path.append(str(CORE_LIB_PATH))
sys.path.append(str(CORE_LIB_PATH.parent))

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
print(f"project_root: {project_root}")
sys.path.insert(0, str(project_root))


import os
from pathlib import Path

project_root = Path(os.getcwd())
print(f"project_root: {project_root.parent}")



try:
    from core_lib.io.yaml_loader import SimulationBuilder
    from core_lib.disturbances.disturbance_framework import (
        DisturbanceConfig, DisturbanceType, InflowDisturbance, SensorNoiseDisturbance, create_disturbance
    )
    CORE_LIB_AVAILABLE = True
except ImportError:
    CORE_LIB_AVAILABLE = False
    st.error("⚠️ 核心库 (core_lib) 不可用，部分功能将被模拟")

# 配置页面
st.set_page_config(
    page_title="分布式数字孪生仿真 - 多种扰动类型测试",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationManager:
    """仿真管理器 - 处理仿真逻辑"""
    
    def __init__(self):
        self.harness = None
        self.is_initialized = False
        self.simulation_results = []
        
    def initialize_simulation(self):
        """初始化仿真环境"""
        if CORE_LIB_AVAILABLE:
            try:
                scenario_path = Path(os.getcwd()).parent
                print(f'scenario_path:{scenario_path}')
                builder = SimulationBuilder(scenario_path=str(scenario_path))
                self.harness = builder.load()
                self.is_initialized = True
                return True
            except Exception as e:
                st.error(f"初始化仿真环境失败: {e}")
                return False
        else:
            # 模拟模式
            self.is_initialized = True
            return True
    
    def create_mock_results(self, disturbances, simulation_time):
        """创建模拟结果数据"""
        times = np.linspace(0, simulation_time, 100)
        base_water_level = 100.0
        base_inflow = 2000.0
        
        water_levels = []
        inflows = []
        volumes = []
        active_disturbances_count = []
        
        for t in times:
            # 基础水位
            water_level = base_water_level + 0.1 * np.sin(0.1 * t)
            inflow = base_inflow
            
            active_count = 0
            
            # 应用入流扰动
            for dist in disturbances:
                if dist['type'] == 'inflow' and dist['start_time'] <= t <= dist['end_time']:
                    inflow = dist['target_inflow']
                    water_level += (inflow - base_inflow) * 0.0001 * (t - dist['start_time'])
                    active_count += 1
                
                # 应用传感器噪声
                elif dist['type'] == 'sensor_noise' and dist['start_time'] <= t <= dist['end_time']:
                    noise = np.random.normal(0, dist['noise_std'])
                    water_level += noise
                    active_count += 1
            
            water_levels.append(water_level)
            inflows.append(inflow)
            volumes.append(water_level * 10000)  # 模拟体积计算
            active_disturbances_count.append(active_count)
        
        return pd.DataFrame({
            'time': times,
            'water_level': water_levels,
            'inflow': inflows,
            'volume': volumes,
            'active_disturbances': active_disturbances_count
        })
    
    def run_simulation(self, disturbances, simulation_time):
        """运行仿真"""
        if not self.is_initialized:
            if not self.initialize_simulation():
                return None
        
        if CORE_LIB_AVAILABLE and self.harness:
            # 真实仿真逻辑
            return self._run_real_simulation(disturbances, simulation_time)
        else:
            # 模拟数据
            return self.create_mock_results(disturbances, simulation_time)
    
    def _run_real_simulation(self, disturbances, simulation_time):
        """运行真实仿真（使用core_lib）"""
        # 清除之前的扰动
        dm = self.harness.disturbance_manager
        # 逐个移除已注册的扰动（remove_disturbance 内部会先停用活跃扰动）
        for _did in list(getattr(dm, 'disturbances', {}).keys()):
            dm.remove_disturbance(_did)
        # 清空历史（如有）
        if hasattr(dm, 'clear_history'):
            dm.clear_history()
        
        # 添加扰动
        for i, dist_config in enumerate(disturbances):
            if dist_config['type'] == 'inflow':
                config = DisturbanceConfig(
                    disturbance_id=f"inflow_{i}",
                    disturbance_type=DisturbanceType.INFLOW_CHANGE,
                    target_component_id="Upstream_Reservoir",
                    start_time=dist_config['start_time'],
                    end_time=dist_config['end_time'],
                    intensity=dist_config['intensity'],
                    parameters={'target_inflow': dist_config['target_inflow']},
                    description=dist_config['description']
                )
            elif dist_config['type'] == 'sensor_noise':
                config = DisturbanceConfig(
                    disturbance_id=f"sensor_{i}",
                    disturbance_type=DisturbanceType.SENSOR_NOISE,
                    target_component_id="Upstream_Reservoir",
                    start_time=dist_config['start_time'],
                    end_time=dist_config['end_time'],
                    intensity=dist_config['intensity'],
                    parameters={
                        'noise_std': dist_config['noise_std'],
                        'sensor_type': 'water_level'
                    },
                    description=dist_config['description']
                )
            
            disturbance = create_disturbance(config)
            self.harness.add_disturbance(disturbance)
        
        # 重置仿真到初始时间（兼容无 reset() 的实现）
        # 优先使用 reset()，若不存在则手动回到0并设置终止时间
        if hasattr(self.harness, 'reset') and callable(getattr(self.harness, 'reset')):
            self.harness.reset()
        else:
            # 手动复位：回到起点时间，并确保 end_time 为目标仿真时长
            try:
                self.harness.t = 0.0
            except Exception:
                pass
        self.harness.end_time = simulation_time
        
        # 运行仿真并记录数据
        results = []
        while self.harness.t < self.harness.end_time:
            if "Upstream_Reservoir" in self.harness.components:
                reservoir = self.harness.components["Upstream_Reservoir"]
                state = reservoir.get_state()
                active_disturbances = self.harness.get_active_disturbances()
                
                results.append({
                    'time': self.harness.t,
                    'water_level': state.get('water_level', 0),
                    'volume': state.get('volume', 0),
                    'inflow': getattr(reservoir, '_inflow', 0),
                    'active_disturbances': len(active_disturbances)
                })
            
            self.harness.step()
        
        return pd.DataFrame(results)

# 初始化仿真管理器
if 'sim_manager' not in st.session_state:
    st.session_state.sim_manager = SimulationManager()

# 页面标题
st.title("🏗️ 分布式数字孪生仿真：多种扰动类型测试")
st.markdown("---")

# 创建两列布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 仿真配置")
    
    # 基本仿真参数
    st.subheader("⏱️ 仿真参数")
    simulation_time = st.number_input(
        "仿真时间 (秒)", 
        min_value=10, 
        max_value=100, 
        value=25, 
        step=5,
        help="总仿真时间，建议25-50秒以观察扰动效果"
    )
    
    # 扰动配置
    st.subheader("🌊 扰动配置")
    
    # 使用tabs来组织不同类型的扰动
    inflow_tab, sensor_tab = st.tabs(["入流扰动", "传感器噪声"])
    
    disturbances = []
    
    with inflow_tab:
        st.markdown("**入流扰动** - 改变水库入流量")
        
        enable_inflow = st.checkbox("启用入流扰动", value=True)
        
        if enable_inflow:
            col_a, col_b = st.columns(2)
            with col_a:
                inflow_start = st.number_input("开始时间 (s)", 0.0, float(simulation_time-1), 5.0, 0.5, key="inflow_start")
                inflow_target = st.number_input("目标入流量 (m³/s)", 1000, 5000, 3000, 100, key="inflow_target")
            with col_b:
                inflow_end = st.number_input("结束时间 (s)", inflow_start+1, float(simulation_time), 10.0, 0.5, key="inflow_end")
                inflow_intensity = st.slider("强度", 0.1, 2.0, 1.0, 0.1, key="inflow_intensity")
            
            inflow_desc = st.text_input("扰动描述", "入流量增加扰动", key="inflow_desc")
            
            disturbances.append({
                'type': 'inflow',
                'start_time': inflow_start,
                'end_time': inflow_end,
                'intensity': inflow_intensity,
                'target_inflow': inflow_target,
                'description': inflow_desc
            })
    
    with sensor_tab:
        st.markdown("**传感器噪声扰动** - 对水位传感器添加噪声")
        
        enable_sensor = st.checkbox("启用传感器噪声", value=True)
        
        if enable_sensor:
            col_c, col_d = st.columns(2)
            with col_c:
                sensor_start = st.number_input("开始时间 (s)", 0.0, float(simulation_time-1), 12.0, 0.5, key="sensor_start")
                sensor_std = st.number_input("噪声标准差 (m)", 0.001, 0.1, 0.01, 0.001, key="sensor_std", format="%.3f")
            with col_d:
                sensor_end = st.number_input("结束时间 (s)", sensor_start+1, float(simulation_time), 18.0, 0.5, key="sensor_end")
                sensor_intensity = st.slider("强度", 0.1, 2.0, 0.5, 0.1, key="sensor_intensity")
            
            sensor_desc = st.text_input("扰动描述", "水位传感器噪声", key="sensor_desc")
            
            disturbances.append({
                'type': 'sensor_noise',
                'start_time': sensor_start,
                'end_time': sensor_end,
                'intensity': sensor_intensity,
                'noise_std': sensor_std,
                'description': sensor_desc
            })
    
    # 显示扰动摘要
    if disturbances:
        st.subheader("📊 扰动摘要")
        for i, dist in enumerate(disturbances, 1):
            type_name = "入流扰动" if dist['type'] == 'inflow' else "传感器噪声"
            st.info(f"**{i}. {type_name}**\n"
                   f"时间: {dist['start_time']:.1f}s - {dist['end_time']:.1f}s\n"
                   f"描述: {dist['description']}")

with col2:
    st.header("🎯 仿真结果")
    
    # 运行仿真按钮
    if st.button("🚀 运行仿真", type="primary", use_container_width=True):
        if not disturbances:
            st.warning("请至少配置一个扰动后再运行仿真")
        else:
            with st.spinner("正在运行仿真..."):
                results = st.session_state.sim_manager.run_simulation(disturbances, simulation_time)
                
                if results is not None:
                    st.session_state.simulation_results = results
                    st.success("✅ 仿真完成！")
                else:
                    st.error("❌ 仿真失败")
    
    # 显示结果
    if 'simulation_results' in st.session_state and not st.session_state.simulation_results.empty:
        results = st.session_state.simulation_results
        
        # 创建子图
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("水位变化", "入流量变化", "水库容积变化", "活跃扰动数量"),
            row_heights=[0.3, 0.25, 0.25, 0.2]
        )
        
        # 水位图
        fig.add_trace(
            go.Scatter(x=results['time'], y=results['water_level'], 
                      name='水位 (m)', line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # 入流量图
        fig.add_trace(
            go.Scatter(x=results['time'], y=results['inflow'], 
                      name='入流量 (m³/s)', line=dict(color='green', width=2)),
            row=2, col=1
        )
        
        # 容积图
        fig.add_trace(
            go.Scatter(x=results['time'], y=results['volume'], 
                      name='容积 (m³)', line=dict(color='orange', width=2)),
            row=3, col=1
        )
        
        # 活跃扰动数量
        fig.add_trace(
            go.Scatter(x=results['time'], y=results['active_disturbances'], 
                      mode='lines+markers', name='活跃扰动数', 
                      line=dict(color='red', width=2)),
            row=4, col=1
        )
        
        # 添加扰动时间区间
        colors = ['rgba(255,0,0,0.2)', 'rgba(0,255,0,0.2)', 'rgba(0,0,255,0.2)']
        for i, dist in enumerate(disturbances):
            color = colors[i % len(colors)]
            type_name = "入流扰动" if dist['type'] == 'inflow' else "传感器噪声"
            
            # 在所有子图上添加扰动区间
            for row in range(1, 5):
                fig.add_vrect(
                    x0=dist['start_time'], x1=dist['end_time'],
                    fillcolor=color, opacity=0.3,
                    annotation_text=f"{type_name}" if row == 1 else "",
                    annotation_position="top left",
                    row=row, col=1
                )
        
        # 更新布局
        fig.update_layout(
            title="仿真结果详细分析",
            height=800,
            showlegend=False,
            xaxis4_title="时间 (秒)"
        )
        
        fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
        fig.update_yaxes(title_text="入流量 (m³/s)", row=2, col=1)
        fig.update_yaxes(title_text="容积 (m³)", row=3, col=1)
        fig.update_yaxes(title_text="扰动数量", row=4, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 数据统计分析
        st.subheader("📈 数据统计分析")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均水位", f"{results['water_level'].mean():.3f} m", 
                     f"{results['water_level'].std():.3f} m")
        
        with col2:
            st.metric("平均入流量", f"{results['inflow'].mean():.0f} m³/s",
                     f"±{results['inflow'].std():.0f} m³/s")
        
        with col3:
            st.metric("最大容积", f"{results['volume'].max():.0f} m³",
                     f"{(results['volume'].max() - results['volume'].min()):.0f} m³")
        
        with col4:
            max_active = results['active_disturbances'].max()
            st.metric("最大同时扰动", f"{int(max_active)} 个",
                     f"总时长 {len(results[results['active_disturbances'] > 0])/len(results)*100:.1f}%")
        
        # 扰动效果分析
        st.subheader("🔍 扰动效果分析")
        
        for i, dist in enumerate(disturbances):
            type_name = "入流扰动" if dist['type'] == 'inflow' else "传感器噪声扰动"
            
            # 筛选扰动期间的数据
            mask = (results['time'] >= dist['start_time']) & (results['time'] <= dist['end_time'])
            during_disturbance = results[mask]
            
            # 扰动前后对比
            before_mask = results['time'] < dist['start_time']
            after_mask = results['time'] > dist['end_time']
            
            if len(during_disturbance) > 0:
                with st.expander(f"📊 {type_name} ({dist['start_time']:.1f}s - {dist['end_time']:.1f}s)"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    if dist['type'] == 'inflow':
                        with col_a:
                            before_level = results[before_mask]['water_level'].iloc[-1] if len(results[before_mask]) > 0 else 0
                            during_level = during_disturbance['water_level'].mean()
                            level_change = (during_level - before_level) * 1000  # 转换为mm
                            st.metric("水位变化", f"{level_change:.1f} mm", 
                                     f"扰动期间平均: {during_level:.3f} m")
                        
                        with col_b:
                            target_inflow = dist['target_inflow']
                            actual_inflow = during_disturbance['inflow'].mean()
                            st.metric("入流量", f"{actual_inflow:.0f} m³/s",
                                     f"目标: {target_inflow:.0f} m³/s")
                    
                    elif dist['type'] == 'sensor_noise':
                        with col_a:
                            level_variance = during_disturbance['water_level'].var()
                            noise_effect = np.sqrt(level_variance) * 1000  # 转换为mm
                            st.metric("噪声效果", f"±{noise_effect:.1f} mm",
                                     f"标准差: {dist['noise_std']*1000:.1f} mm")
                    
                    with col_c:
                        duration = dist['end_time'] - dist['start_time']
                        st.metric("扰动持续时间", f"{duration:.1f} 秒",
                                 f"强度: {dist['intensity']:.1f}")

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 系统信息")
    
    # 核心模块状态
    st.subheader("核心模块依赖")
    if CORE_LIB_AVAILABLE:
        st.success("✅ core_lib.io.yaml_loader")
        st.success("✅ core_lib.disturbances.disturbance_framework")
    else:
        st.warning("⚠️ 模拟模式运行")
        st.info("核心库不可用，使用模拟数据")
    
    # 数据源信息
    st.subheader("数据源")
    st.info("📄 YAML配置文件\n📊 仿真状态数据\n📈 扰动历史记录")
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 🌊 入流扰动：模拟水库入流量变化
    2. 📡 传感器噪声：模拟传感器测量误差
    3. 🔄 多扰动交互：观察多个扰动同时作用的影响
    4. 📊 实时监控：记录水位、流量、容积变化
    5. 📈 结果分析：量化扰动对系统的影响
    
    **应用场景：**
    - 水库调度策略验证
    - 传感器故障影响评估
    - 系统鲁棒性测试
    - 应急预案演练
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **配置仿真参数**：设置仿真总时长
        2. **选择扰动类型**：启用入流扰动和/或传感器噪声
        3. **设置扰动参数**：配置时间范围、强度等
        4. **运行仿真**：点击"运行仿真"按钮
        5. **分析结果**：查看图表和统计数据
        
        **提示：**
        - 扰动时间不要重叠太多以便观察单独效果
        - 建议仿真时间设为25-50秒
        - 可以同时启用多个扰动观察交互效果
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `7.test_multiple_disturbance_types.py` 的分布式数字孪生仿真系统*")
