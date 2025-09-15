#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入流扰动测试 - Streamlit界面

这个应用提供了一个直观的界面来测试入流扰动对物理计算核心的影响：
1. 使用动态扰动管理器应用入流变化扰动
2. 实时监控入流和水位变化过程
3. 验证扰动是否成功影响物理计算核心
4. 提供可视化分析扰动效果
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

# 配置页面
st.set_page_config(
    page_title="入流扰动测试系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 尝试导入核心模块
try:
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from core_lib.io.yaml_loader import SimulationBuilder
    from core_lib.central_coordination.collaboration.message_bus import MessageBus
    
    # 导入动态扰动管理器 - 修复路径问题
    dynamic_disturbance_path = project_root / "examples" / "distributed_digital_twin_simulation" / "15.dynamic_disturbance_manager.py"
    if dynamic_disturbance_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("dynamic_disturbance_manager", dynamic_disturbance_path)
        dynamic_disturbance_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dynamic_disturbance_module)
        DynamicDisturbanceManager = dynamic_disturbance_module.DynamicDisturbanceManager
        CORE_LIB_AVAILABLE = True
    else:
        raise ImportError("DynamicDisturbanceManager module not found")
        
except ImportError as e:
    CORE_LIB_AVAILABLE = False
    st.error(f"⚠️ 核心库导入失败: {e}")
    st.info("将使用模拟模式运行")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InflowDisturbanceSimulator:
    """入流扰动仿真器"""
    
    def __init__(self):
        self.harness = None
        self.upstream_reservoir = None
        self.message_bus = None
        self.disturbance_manager = None
        self.simulation_history = []
        self.is_initialized = False
        
    def initialize_simulation(self, working_dir="."):
        """初始化仿真环境"""
        if CORE_LIB_AVAILABLE:
            try:
                # 构建仿真
                builder = SimulationBuilder(working_dir)
                self.harness = builder.load()
                
                # 获取上游水库
                self.upstream_reservoir = self.harness.components.get('Upstream_Reservoir')
                if not self.upstream_reservoir:
                    st.error("❌ 未找到Upstream_Reservoir组件")
                    return False
                
                # 创建消息总线和扰动管理器
                self.message_bus = MessageBus()
                self.disturbance_manager = DynamicDisturbanceManager(self.message_bus)
                
                self.is_initialized = True
                return True
                
            except Exception as e:
                st.error(f"初始化仿真环境失败: {e}")
                return False
        else:
            # 模拟模式初始化
            self.is_initialized = True
            return True
    
    def run_simulation_with_disturbance(self, config):
        """运行带扰动的仿真"""
        if not self.is_initialized:
            if not self.initialize_simulation(config.get('working_dir', '.')):
                return None
        
        self.simulation_history = []
        
        if CORE_LIB_AVAILABLE and self.harness:
            return self._run_real_simulation(config)
        else:
            return self._run_mock_simulation(config)
    
    def _run_real_simulation(self, config):
        """运行真实仿真"""
        # 定义入流扰动配置
        inflow_disturbance_config = {
            'type': 'inflow_variation',
            'disturbance_scenario': {
                'type': 'inflow_variation',
                'parameters': {
                    'target_component': config['target_component'],
                    'magnitude': config['magnitude'],
                    'pattern': config['pattern']
                }
            }
        }
        
        # 注册扰动
        self.disturbance_manager.register_disturbance(
            'inflow_test', 
            inflow_disturbance_config, 
            config['start_time'], 
            config['duration']
        )
        
        # 运行仿真并监测
        dt = config['dt']
        total_time = config['total_time']
        current_time = 0.0
        
        while current_time < total_time:
            # 更新扰动管理器
            self.disturbance_manager.update(current_time, self.harness)
            
            # 执行一步仿真
            self.harness.step()
            
            # 记录关键状态
            water_level = self.upstream_reservoir.get_state()['water_level']
            current_inflow = getattr(self.upstream_reservoir, '_inflow', 100.0)
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': water_level,
                'inflow': current_inflow,
                'step': len(self.simulation_history)
            })
            
            current_time += dt
        
        return pd.DataFrame(self.simulation_history)
    
    def _run_mock_simulation(self, config):
        """运行模拟仿真"""
        dt = config['dt']
        total_time = config['total_time']
        current_time = 0.0
        
        # 模拟参数
        initial_water_level = 15.0
        base_inflow = 100.0
        magnitude = config['magnitude']
        start_time = config['start_time']
        duration = config['duration']
        
        water_level = initial_water_level
        
        while current_time < total_time:
            # 模拟入流变化
            if start_time <= current_time <= start_time + duration:
                # 扰动期间
                if config['pattern'] == 'step':
                    current_inflow = base_inflow + magnitude
                else:
                    current_inflow = base_inflow + magnitude * np.sin(2 * np.pi * (current_time - start_time) / duration)
            else:
                current_inflow = base_inflow
            
            # 模拟水位变化（简化模型）
            inflow_change = current_inflow - base_inflow
            water_level += inflow_change * dt * 0.001  # 简化的水位计算
            
            # 添加一些随机噪声
            water_level += np.random.normal(0, 0.001)
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': water_level,
                'inflow': current_inflow,
                'step': len(self.simulation_history)
            })
            
            current_time += dt
        
        return pd.DataFrame(self.simulation_history)

# 初始化仿真器
if 'inflow_simulator' not in st.session_state:
    st.session_state.inflow_simulator = InflowDisturbanceSimulator()

# 页面标题
st.title("🌊 入流扰动测试系统")
st.markdown("---")

# 创建主布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ 扰动配置")
    
    # 基本参数配置
    st.subheader("📊 基本参数")
    
    col_a, col_b = st.columns(2)
    with col_a:
        working_dir = st.text_input("工作目录", ".", help="SimulationBuilder的工作目录")
        target_component = st.text_input("目标组件", "Upstream_Reservoir", help="要施加扰动的组件名称")
    with col_b:
        magnitude = st.number_input("扰动幅值 (m³/s)", 10, 200, 50, 5, help="入流增加的量")
        pattern = st.selectbox("扰动模式", ["step", "sine"], help="step=阶跃变化, sine=正弦变化")
    
    # 时间参数配置
    st.subheader("⏰ 时间参数")
    
    col_c, col_d = st.columns(2)
    with col_c:
        start_time = st.number_input("开始时间 (s)", 0.0, 20.0, 1.0, 0.5, help="扰动开始的时间")
        duration = st.number_input("持续时间 (s)", 1.0, 30.0, 10.0, 0.5, help="扰动持续的时间")
    with col_d:
        dt = st.number_input("时间步长 (s)", 0.01, 2.0, 0.5, 0.01, help="仿真时间步长")
        total_time = st.number_input("总仿真时间 (s)", 5.0, 60.0, 15.0, 1.0, help="整个仿真的总时间")
    
    # 显示配置摘要
    st.subheader("📋 扰动摘要")
    st.info(f"**扰动配置**\n"
           f"• 目标组件: {target_component}\n"
           f"• 扰动幅值: +{magnitude} m³/s\n"
           f"• 扰动模式: {pattern}\n"
           f"• 时间: {start_time:.1f}s - {start_time + duration:.1f}s")

with col2:
    st.header("📊 测试结果")
    
    # 运行测试按钮
    if st.button("🚀 运行入流扰动测试", type="primary", use_container_width=True):
        # 构建配置
        config = {
            'working_dir': working_dir,
            'target_component': target_component,
            'magnitude': magnitude,
            'pattern': pattern,
            'start_time': start_time,
            'duration': duration,
            'dt': dt,
            'total_time': total_time
        }
        
        with st.spinner("正在运行入流扰动测试..."):
            # 运行仿真
            results = st.session_state.inflow_simulator.run_simulation_with_disturbance(config)
            
            if results is not None and not results.empty:
                st.session_state.test_results = {
                    'simulation_data': results,
                    'config': config,
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
        
        # 计算关键指标
        initial_inflow = sim_data.iloc[0]['inflow'] if not sim_data.empty else 100.0
        final_inflow = sim_data.iloc[-1]['inflow'] if not sim_data.empty else 100.0
        initial_level = sim_data.iloc[0]['water_level'] if not sim_data.empty else 15.0
        final_level = sim_data.iloc[-1]['water_level'] if not sim_data.empty else 15.0
        
        # 关键指标展示
        st.subheader("📈 关键性能指标")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("初始入流", f"{initial_inflow:.1f} m³/s", 
                     f"目标组件: {config['target_component']}")
        
        with col_b:
            st.metric("最终入流", f"{final_inflow:.1f} m³/s",
                     f"{final_inflow - initial_inflow:+.1f} m³/s")
        
        with col_c:
            st.metric("初始水位", f"{initial_level:.3f} m",
                     f"扰动幅值: +{config['magnitude']} m³/s")
        
        with col_d:
            level_change = final_level - initial_level
            st.metric("最终水位", f"{final_level:.3f} m",
                     f"{level_change*1000:+.1f} mm")
        
        # 入流和水位变化图表
        st.subheader("📊 入流和水位变化分析")
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("入流变化", "水位变化"),
            row_heights=[0.5, 0.5]
        )
        
        # 入流变化图
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=sim_data['inflow'],
                mode='lines+markers',
                name='入流量',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )
        
        # 水位变化图
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=sim_data['water_level'],
                mode='lines+markers',
                name='水位',
                line=dict(color='green', width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )
        
        # 标识扰动区间
        fig.add_vrect(
            x0=config['start_time'],
            x1=config['start_time'] + config['duration'],
            fillcolor="rgba(255,0,0,0.2)",
            opacity=0.3,
            annotation_text="扰动区间",
            annotation_position="top left",
            row=1, col=1
        )
        
        fig.add_vrect(
            x0=config['start_time'],
            x1=config['start_time'] + config['duration'],
            fillcolor="rgba(255,0,0,0.2)",
            opacity=0.3,
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title="入流扰动测试结果分析",
            height=600,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="入流量 (m³/s)", row=1, col=1)
        fig.update_yaxes(title_text="水位 (m)", row=2, col=1)
        fig.update_xaxes(title_text="时间 (s)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 扰动效果验证
        st.subheader("🔍 扰动效果验证")
        
        with st.expander("✅ 扰动效果验证结果"):
            col_x, col_y = st.columns(2)
            
            with col_x:
                st.markdown("**扰动参数：**")
                st.info(f"• 扰动幅值: {config['magnitude']} m³/s\n"
                       f"• 扰动模式: {config['pattern']}\n"
                       f"• 扰动时间: {config['start_time']:.1f}s - {config['start_time'] + config['duration']:.1f}s\n"
                       f"• 目标组件: {config['target_component']}")
            
            with col_y:
                st.markdown("**实际效果：**")
                inflow_change = final_inflow - initial_inflow
                level_change_mm = (final_level - initial_level) * 1000
                
                if abs(inflow_change) > 0.1:  # 入流有明显变化
                    st.success(f"• 入流变化: {inflow_change:+.1f} m³/s\n"
                              f"• 水位变化: {level_change_mm:+.1f} mm\n"
                              f"• **验证结果: ✅ 扰动成功**")
                else:
                    st.warning(f"• 入流变化: {inflow_change:+.1f} m³/s\n"
                              f"• 水位变化: {level_change_mm:+.1f} mm\n"
                              f"• **验证结果: ⚠️ 扰动效果不明显**")
            
            # 总体验证结论
            if abs(inflow_change) > 0.1:
                st.success("🎉 **入流扰动成功影响了物理计算核心！** 扰动产生了明显的入流变化。")
            else:
                st.warning("⚠️ **扰动效果不明显** 请检查扰动参数设置或系统配置。")
        
        # 详细数据表
        with st.expander("📋 详细仿真数据"):
            if not sim_data.empty:
                display_data = sim_data.copy()
                display_data['water_level'] = display_data['water_level'].round(6)
                display_data['inflow'] = display_data['inflow'].round(1)
                display_data.columns = ['时间(s)', '水位(m)', '入流(m³/s)', '步数']
                
                st.dataframe(display_data, use_container_width=True, height=300)

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 系统信息")
    
    # 核心模块状态
    st.subheader("核心模块依赖")
    if CORE_LIB_AVAILABLE:
        st.success("✅ core_lib.io.yaml_loader")
        st.success("✅ core_lib.central_coordination.collaboration.message_bus")
        st.success("✅ DynamicDisturbanceManager")
    else:
        st.warning("⚠️ 模拟模式运行")
        st.info("核心库不可用，使用模拟数据")
    
    # 数据源信息
    st.subheader("数据源")
    st.info("📊 仿真环境状态数据\n🌊 水库组件入流参数\n📈 实时水位变化数据\n🔧 动态扰动管理器状态")
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 🌊 入流扰动：通过动态扰动管理器施加入流变化
    2. 📊 实时监控：记录入流和水位的变化过程
    3. ✅ 效果验证：验证扰动是否影响物理计算核心
    4. 📈 可视化分析：图表展示扰动效果和系统响应
    
    **应用场景：**
    - 扰动框架功能验证
    - 物理计算核心响应测试
    - 入流变化对系统影响分析
    - 扰动参数效果评估
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **设置基本参数**：配置工作目录和目标组件
        2. **配置扰动参数**：设置扰动幅值、模式和时间
        3. **运行扰动测试**：点击"运行入流扰动测试"
        4. **分析结果**：查看入流和水位变化图表
        5. **验证效果**：确认扰动是否成功影响系统
        
        **扰动模式说明：**
        - **step**：阶跃变化，入流瞬间增加指定值
        - **sine**：正弦变化，入流按正弦波规律变化
        """)
    
    # 验证标准说明
    with st.expander("✅ 验证标准"):
        st.markdown("""
        **扰动成功标准：**
        ```
        入流变化 > 0.1 m³/s  ✅ 扰动成功
        入流变化 ≤ 0.1 m³/s  ⚠️ 扰动效果不明显
        ```
        
        **水位变化参考：**
        - 水位变化通常比入流变化小得多
        - 毫米级的水位变化已属于明显效果
        - 具体变化量取决于水库表面积和几何形状
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `4.test_inflow_disturbance.py` 的入流扰动测试系统*")
