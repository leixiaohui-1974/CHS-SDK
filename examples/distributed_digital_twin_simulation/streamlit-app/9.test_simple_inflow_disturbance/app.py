#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单入流扰动测试 - Streamlit界面

这个应用提供了一个直观的界面来测试和验证入流扰动对水库系统的影响：
1. 直接修改水库入流参数验证扰动效果
2. 理论计算与实际结果对比分析
3. 实时监控水位变化过程
4. 验证扰动是否影响物理计算核心
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import logging



# 当前脚本所在目录
CURRENT_DIR = Path(__file__).resolve().parent
# 项目根目录 (E:\CHS-SDK)
PROJECT_ROOT = CURRENT_DIR.parents[2]   # 回到 E:\CHS-SDK

# 添加 core_lib 到 sys.path
sys.path.append(str(PROJECT_ROOT / "core_lib"))


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

# 配置页面
st.set_page_config(
    page_title="简单入流扰动测试系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 尝试导入核心模块
try:
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from core_lib.io.yaml_loader import SimulationBuilder
    CORE_LIB_AVAILABLE = True
except ImportError:
    CORE_LIB_AVAILABLE = False
    st.error("⚠️ 核心库 (core_lib.io.yaml_loader) 不可用，使用模拟模式")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleInflowSimulator:
    """简单入流扰动仿真器"""
    
    def __init__(self):
        self.harness = None
        self.upstream_reservoir = None
        self.simulation_history = []
        self.initial_state = {}
        self.is_initialized = False
        
    def initialize_simulation(self):
        """初始化仿真环境"""
        if CORE_LIB_AVAILABLE:
            try:
                scenario_path = Path(os.getcwd()).parent
                builder = SimulationBuilder(str(scenario_path))
                self.harness = builder.load()
                
                # 获取上游水库
                self.upstream_reservoir = self.harness.components.get('Upstream_Reservoir')
                if not self.upstream_reservoir:
                    st.error("❌ 未找到Upstream_Reservoir组件")
                    return False
                
                # 记录初始状态
                self.initial_state = {
                    'inflow': getattr(self.upstream_reservoir, '_inflow', 100.0),
                    'water_level': self.upstream_reservoir.get_state().get('water_level', 15.0),
                    'volume': self.upstream_reservoir.get_state().get('volume', 0),
                    'surface_area': self.upstream_reservoir.get_parameters().get('surface_area', 1e6),
                    'dt': self.harness.dt
                }
                
                self.is_initialized = True
                return True
                
            except Exception as e:
                st.error(f"初始化仿真环境失败: {e}")
                return False
        else:
            # 模拟模式初始化
            self.initial_state = {
                'inflow': 100.0,
                'water_level': 15.0,
                'volume': 15e6,  # 15米水深 × 1e6平方米表面积
                'surface_area': 1e6,
                'dt': 0.1
            }
            self.is_initialized = True
            return True
    
    def calculate_theoretical_change(self, inflow_increase, duration, surface_area):
        """计算理论水位变化"""
        volume_increase = inflow_increase * duration  # m³
        level_change = volume_increase / surface_area  # m
        return level_change, volume_increase
    
    def run_simulation_with_disturbance(self, config):
        """运行带扰动的仿真"""
        if not self.is_initialized:
            if not self.initialize_simulation():
                return None
        
        # 配置参数
        total_time = config['total_time']
        disturbance_start = config['disturbance_start'] 
        disturbance_end = config['disturbance_end']
        original_inflow = config['original_inflow']
        disturbed_inflow = config['disturbed_inflow']
        
        self.simulation_history = []
        
        if CORE_LIB_AVAILABLE and self.harness:
            return self._run_real_simulation(config)
        else:
            return self._run_mock_simulation(config)
    
    def _run_real_simulation(self, config):
        """运行真实仿真"""
        # 重置仿真
        self.harness.reset()
        
        current_time = 0.0
        step_count = 0
        
        while current_time < config['total_time'] and step_count < 200:  # 防止无限循环
            # 执行仿真步骤
            self.harness.step()
            current_time = self.harness.t
            
            # 应用入流扰动
            if config['disturbance_start'] <= current_time <= config['disturbance_end']:
                self.upstream_reservoir.set_inflow(config['disturbed_inflow'])
                is_disturbed = True
            else:
                self.upstream_reservoir.set_inflow(config['original_inflow'])
                is_disturbed = False
            
            # 记录状态
            state = self.upstream_reservoir.get_state()
            current_inflow = getattr(self.upstream_reservoir, '_inflow', config['original_inflow'])
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': state.get('water_level', 0),
                'volume': state.get('volume', 0),
                'inflow': current_inflow,
                'is_disturbed': is_disturbed,
                'step': step_count
            })
            
            step_count += 1
        
        return pd.DataFrame(self.simulation_history)
    
    def _run_mock_simulation(self, config):
        """运行模拟仿真"""
        dt = 0.1  # 时间步长
        current_time = 0.0
        
        # 初始状态
        water_level = self.initial_state['water_level']
        volume = self.initial_state['volume']
        surface_area = self.initial_state['surface_area']
        
        while current_time < config['total_time']:
            # 确定当前入流
            if config['disturbance_start'] <= current_time <= config['disturbance_end']:
                current_inflow = config['disturbed_inflow']
                is_disturbed = True
            else:
                current_inflow = config['original_inflow']
                is_disturbed = False
            
            # 简单的水位计算（入流影响体积，体积影响水位）
            # 假设有恒定的出流
            outflow = config['original_inflow'] * 0.95  # 略小于原始入流
            net_flow = current_inflow - outflow
            
            # 更新体积和水位
            volume += net_flow * dt
            water_level = volume / surface_area  # 简化的水位计算
            
            # 添加一些随机噪声以模拟真实情况
            noise = np.random.normal(0, 0.001)  # 1mm随机噪声
            water_level += noise
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': water_level,
                'volume': volume,
                'inflow': current_inflow,
                'is_disturbed': is_disturbed,
                'step': len(self.simulation_history)
            })
            
            current_time += dt
        
        return pd.DataFrame(self.simulation_history)

# 初始化仿真器
if 'inflow_simulator' not in st.session_state:
    st.session_state.inflow_simulator = SimpleInflowSimulator()

# 页面标题
st.title("🌊 简单入流扰动测试系统")
st.markdown("---")

# 创建主布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ 扰动配置")
    
    # 基本参数配置
    st.subheader("📊 基本参数")
    
    col_a, col_b = st.columns(2)
    with col_a:
        original_inflow = st.number_input("初始入流量 (m³/s)", 50, 200, 100, 5, help="水库的正常入流量")
        surface_area = st.number_input("水库表面积 (m²)", 1e5, 5e6, 1e6, 1e5, format="%.0e", help="用于计算水位变化")
    with col_b:
        initial_water_level = st.number_input("初始水位 (m)", 10.0, 25.0, 15.0, 0.5, help="水库初始水位")
        total_time = st.number_input("总仿真时间 (s)", 10.0, 30.0, 15.0, 1.0, help="整个测试的持续时间")
    
    # 扰动配置
    st.subheader("🌊 入流扰动配置")
    
    col_c, col_d = st.columns(2)
    with col_c:
        disturbance_start = st.number_input("扰动开始时间 (s)", 0.0, total_time-2, 1.0, 0.5)
        disturbed_inflow = st.number_input("扰动入流量 (m³/s)", original_inflow+10, 300, 150, 5, help="扰动期间的入流量")
    with col_d:
        disturbance_end = st.number_input("扰动结束时间 (s)", disturbance_start+1, total_time, 11.0, 0.5)
        inflow_increase = disturbed_inflow - original_inflow
    
    # 计算扰动持续时间
    disturbance_duration = disturbance_end - disturbance_start
    
    # 理论计算
    st.subheader("🧮 理论计算")
    theoretical_level_change, volume_increase = st.session_state.inflow_simulator.calculate_theoretical_change(
        inflow_increase, disturbance_duration, surface_area
    )
    
    col_e, col_f = st.columns(2)
    with col_e:
        st.metric("入流增量", f"{inflow_increase:.1f} m³/s", help="扰动期间的入流增加量")
        st.metric("扰动持续时间", f"{disturbance_duration:.1f} s", help="扰动作用的时间长度")
    with col_f:
        st.metric("额外体积", f"{volume_increase:.0f} m³", help="扰动期间额外增加的水量")
        st.metric("理论水位变化", f"{theoretical_level_change*1000:.3f} mm", 
                 f"{theoretical_level_change:.6f} m", help="基于体积增量计算的水位变化")
    
    # 显示配置摘要
    st.subheader("📋 扰动摘要")
    st.info(f"**扰动配置**\n"
           f"• 时间: {disturbance_start:.1f}s - {disturbance_end:.1f}s ({disturbance_duration:.1f}s)\n"
           f"• 入流: {original_inflow:.1f} → {disturbed_inflow:.1f} m³/s (+{inflow_increase:.1f})\n"
           f"• 预期水位变化: {theoretical_level_change*1000:.3f} mm")

with col2:
    st.header("📊 测试结果")
    
    # 运行测试按钮
    if st.button("🚀 运行简单入流扰动测试", type="primary", use_container_width=True):
        # 构建配置
        config = {
            'total_time': total_time,
            'disturbance_start': disturbance_start,
            'disturbance_end': disturbance_end,
            'original_inflow': original_inflow,
            'disturbed_inflow': disturbed_inflow,
            'surface_area': surface_area,
            'initial_water_level': initial_water_level
        }
        
        with st.spinner("正在运行入流扰动测试..."):
            # 运行仿真
            results = st.session_state.inflow_simulator.run_simulation_with_disturbance(config)
            
            if results is not None and not results.empty:
                st.session_state.test_results = {
                    'simulation_data': results,
                    'config': config,
                    'theoretical_change': theoretical_level_change,
                    'volume_increase': volume_increase,
                    'timestamp': datetime.now()
                }
                st.success("✅ 入流扰动测试完成！")
            else:
                st.error("❌ 测试失败")
    
    # 显示测试结果
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        sim_data = results['simulation_data']
        config = results['config']
        
        # 计算实际变化
        initial_level = sim_data.iloc[0]['water_level'] if not sim_data.empty else initial_water_level
        final_level = sim_data.iloc[-1]['water_level'] if not sim_data.empty else initial_water_level
        actual_change = final_level - initial_level
        
        # 关键指标展示
        st.subheader("📈 关键性能指标")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("初始水位", f"{initial_level:.3f} m", 
                     f"表面积: {config['surface_area']:.0e} m²")
        
        with col_b:
            st.metric("最终水位", f"{final_level:.3f} m",
                     f"{actual_change*1000:+.3f} mm")
        
        with col_c:
            st.metric("理论变化", f"{results['theoretical_change']*1000:.3f} mm",
                     f"额外体积: {results['volume_increase']:.0f} m³")
        
        with col_d:
            error = abs(actual_change - results['theoretical_change'])
            accuracy = max(0, 100 - (error / max(abs(results['theoretical_change']), 0.001)) * 100)
            st.metric("理论准确度", f"{accuracy:.1f}%",
                     f"误差: {error*1000:.3f} mm")
        
        # 水位变化时序图
        st.subheader("📊 水位变化分析")
        
        # 创建主图表
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("水位变化", "入流变化"),
            row_heights=[0.7, 0.3]
        )
        
        # 水位变化曲线
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=sim_data['water_level'],
                mode='lines+markers',
                name='实际水位',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )
        
        # 理论水位线
        theoretical_final = initial_level + results['theoretical_change']
        fig.add_hline(
            y=initial_level,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"初始水位 ({initial_level:.3f}m)",
            row=1, col=1
        )
        
        fig.add_hline(
            y=theoretical_final,
            line_dash="dash", 
            line_color="red",
            annotation_text=f"理论最终水位 ({theoretical_final:.3f}m)",
            row=1, col=1
        )
        
        # 入流变化
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=sim_data['inflow'],
                mode='lines+markers',
                name='入流量',
                line=dict(color='green', width=2),
                marker=dict(size=4),
                fill='tonexty'
            ),
            row=2, col=1
        )
        
        # 标识扰动区间
        fig.add_vrect(
            x0=config['disturbance_start'],
            x1=config['disturbance_end'],
            fillcolor="rgba(255,0,0,0.2)",
            opacity=0.3,
            annotation_text="扰动区间",
            annotation_position="top left",
            row=1, col=1
        )
        
        fig.add_vrect(
            x0=config['disturbance_start'],
            x1=config['disturbance_end'],
            fillcolor="rgba(255,0,0,0.2)",
            opacity=0.3,
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title="简单入流扰动测试结果分析",
            height=600,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
        fig.update_yaxes(title_text="入流量 (m³/s)", row=2, col=1)
        fig.update_xaxes(title_text="时间 (s)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 详细分析
        st.subheader("🔍 详细分析")
        
        # 扰动效果验证
        with st.expander("✅ 扰动效果验证"):
            st.markdown("**理论 vs 实际对比：**")
            
            col_x, col_y = st.columns(2)
            with col_x:
                st.success(f"**理论计算**\n"
                          f"• 入流增量: {config['disturbed_inflow'] - config['original_inflow']:.1f} m³/s\n"
                          f"• 扰动持续: {config['disturbance_end'] - config['disturbance_start']:.1f} s\n"
                          f"• 额外体积: {results['volume_increase']:.0f} m³\n"
                          f"• 预期水位变化: {results['theoretical_change']*1000:.3f} mm")
            
            with col_y:
                st.info(f"**实际结果**\n"
                       f"• 初始水位: {initial_level:.3f} m\n"
                       f"• 最终水位: {final_level:.3f} m\n"
                       f"• 实际变化: {actual_change*1000:+.3f} mm\n"
                       f"• 准确度: {accuracy:.1f}%")
            
            # 验证结论
            if abs(actual_change) > 0.001:  # 超过1mm变化
                st.success("🎉 **验证成功！** 入流扰动成功影响了物理计算核心，水位发生了明显变化。")
            else:
                st.warning("⚠️ **需要检查** 入流扰动未产生明显的水位变化，可能需要调整参数。")
        
        # 仿真历史统计
        with st.expander("📊 仿真历史统计"):
            if not sim_data.empty:
                # 基本统计
                st.markdown("**仿真基本信息：**")
                st.write(f"• 总仿真步数: {len(sim_data)}")
                st.write(f"• 仿真时间范围: {sim_data['time'].min():.1f}s - {sim_data['time'].max():.1f}s")
                st.write(f"• 平均时间步长: {(sim_data['time'].max() - sim_data['time'].min()) / len(sim_data):.3f}s")
                
                # 扰动期间统计
                disturbed_data = sim_data[sim_data['is_disturbed'] == True]
                if not disturbed_data.empty:
                    st.markdown("**扰动期间统计：**")
                    st.write(f"• 扰动步数: {len(disturbed_data)}")
                    st.write(f"• 扰动期间平均入流: {disturbed_data['inflow'].mean():.1f} m³/s")
                    st.write(f"• 扰动期间水位变化: {disturbed_data['water_level'].min():.3f} - {disturbed_data['water_level'].max():.3f} m")
                
                # 显示原始数据表格
                st.markdown("**详细数据记录：**")
                display_data = sim_data[['time', 'water_level', 'inflow', 'volume', 'is_disturbed']].copy()
                display_data['water_level'] = display_data['water_level'].round(6)
                display_data['inflow'] = display_data['inflow'].round(1)
                display_data['volume'] = display_data['volume'].round(0)
                display_data['扰动状态'] = display_data['is_disturbed'].map({True: '🔴 扰动中', False: '🟢 正常'})
                display_data = display_data.drop('is_disturbed', axis=1)
                display_data.columns = ['时间(s)', '水位(m)', '入流(m³/s)', '体积(m³)', '状态']
                
                st.dataframe(display_data, use_container_width=True, height=300)

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 系统信息")
    
    # 核心模块状态
    st.subheader("核心模块依赖")
    if CORE_LIB_AVAILABLE:
        st.success("✅ core_lib.io.yaml_loader")
    else:
        st.warning("⚠️ 模拟模式运行")
        st.info("核心库不可用，使用模拟数据")
    
    # 数据源信息
    st.subheader("数据源")
    st.info("📊 仿真环境状态数据\n🌊 水库组件参数\n📈 实时水位变化数据\n🧮 理论计算结果")
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 🌊 直接入流扰动：直接修改水库入流参数
    2. 📊 理论计算：基于物理原理预测水位变化
    3. 🔄 实时监控：记录仿真过程中的状态变化
    4. ✅ 效果验证：验证扰动是否影响物理计算
    5. 📈 对比分析：理论预期与实际结果对比
    
    **应用场景：**
    - 水库入流调节效果验证
    - 扰动框架基础功能测试
    - 物理计算核心响应验证
    - 水位预测准确性评估
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **设置基本参数**：配置初始入流、水位、表面积等
        2. **配置扰动参数**：设置扰动时间和强度
        3. **查看理论计算**：了解预期的水位变化
        4. **运行测试**：执行入流扰动仿真
        5. **分析结果**：查看实际效果与理论对比
        
        **关键参数说明：**
        - **表面积**：影响水位变化幅度，面积越大变化越小
        - **入流增量**：扰动强度，决定额外水量
        - **扰动持续时间**：影响总的体积变化量
        - **理论准确度**：评估仿真计算的精度
        """)
    
    # 计算公式说明
    with st.expander("🧮 计算公式"):
        st.markdown("""
        **理论水位变化计算：**
        ```
        额外体积 = 入流增量 × 扰动持续时间
        水位变化 = 额外体积 ÷ 水库表面积
        ```
        
        **准确度计算：**
        ```
        误差 = |实际变化 - 理论变化|
        准确度 = 100% - (误差/理论变化) × 100%
        ```
        
        这些公式基于简化的水库模型，实际系统可能更复杂。
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `9.test_simple_inflow_disturbance.py` 的简单入流扰动测试系统*")
