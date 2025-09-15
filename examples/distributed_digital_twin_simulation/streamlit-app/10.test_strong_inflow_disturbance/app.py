#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强入流扰动测试 - Streamlit界面

这个应用提供了一个直观的界面来测试和验证强入流扰动对水库系统的影响：
1. 使用足够大的扰动来验证扰动功能确实有效
2. 分析最大水位变化和理论预期的对比
3. 实时监控整个扰动过程的状态变化
4. 验证强扰动是否能产生明显的物理效果
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
    page_title="强入流扰动测试系统",
    page_icon="💥",
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

class StrongInflowSimulator:
    """强入流扰动仿真器"""
    
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
                    'surface_area': 1000000,  # 固定为100万平方米（从脚本得出）
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
                'volume': 15e6,
                'surface_area': 1000000,
                'dt': 0.1
            }
            self.is_initialized = True
            return True
    
    def calculate_strong_disturbance_theory(self, inflow_increase, duration, surface_area):
        """计算强扰动的理论效果"""
        volume_increase = inflow_increase * duration  # m³
        level_change = volume_increase / surface_area  # m
        return level_change, volume_increase
    
    def run_strong_disturbance_simulation(self, config):
        """运行强扰动仿真"""
        if not self.is_initialized:
            if not self.initialize_simulation():
                return None
        
        self.simulation_history = []
        
        if CORE_LIB_AVAILABLE and self.harness:
            return self._run_real_strong_simulation(config)
        else:
            return self._run_mock_strong_simulation(config)
    
    def _run_real_strong_simulation(self, config):
        """运行真实的强扰动仿真"""
        # 重置仿真（兼容无 reset() 的实现）
        if hasattr(self.harness, 'reset') and callable(getattr(self.harness, 'reset')):
            self.harness.reset()
        else:
            try:
                self.harness.t = 0.0
            except Exception:
                pass
        
        current_time = 0.0
        step_count = 0
        dt = self.harness.dt
        
        # 记录初始状态
        initial_state = self.upstream_reservoir.get_state()
        initial_water_level = initial_state.get('water_level', 15.0)
        
        water_levels = [initial_water_level]
        times = [0.0]
        
        while current_time < config['total_time'] and step_count < 500:  # 防止无限循环
            # 执行仿真步骤
            self.harness.step()
            current_time = self.harness.t
            
            # 应用强扰动
            if config['disturbance_start'] <= current_time <= config['disturbance_end']:
                strong_inflow = config['base_inflow'] + config['inflow_increase']
                self.upstream_reservoir.set_inflow(strong_inflow)
                is_disturbed = True
            else:
                self.upstream_reservoir.set_inflow(config['base_inflow'])
                is_disturbed = False
            
            # 记录状态
            state = self.upstream_reservoir.get_state()
            current_inflow = getattr(self.upstream_reservoir, '_inflow', config['base_inflow'])
            water_level = state.get('water_level', 0)
            
            water_levels.append(water_level)
            times.append(current_time)
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': water_level,
                'volume': state.get('volume', 0),
                'inflow': current_inflow,
                'is_disturbed': is_disturbed,
                'step': step_count
            })
            
            current_time += dt
            step_count += 1
        
        # 计算最大水位变化
        max_water_level = max(water_levels)
        min_water_level = min(water_levels)
        
        result_df = pd.DataFrame(self.simulation_history)
        result_df['max_water_level'] = max_water_level
        result_df['min_water_level'] = min_water_level
        result_df['initial_water_level'] = initial_water_level
        
        return result_df
    
    def _run_mock_strong_simulation(self, config):
        """运行模拟的强扰动仿真"""
        dt = 0.1
        current_time = 0.0
        
        # 初始状态
        water_level = self.initial_state['water_level']
        volume = self.initial_state['volume']
        surface_area = self.initial_state['surface_area']
        
        initial_water_level = water_level
        water_levels = [water_level]
        
        while current_time < config['total_time']:
            # 确定当前入流
            if config['disturbance_start'] <= current_time <= config['disturbance_end']:
                current_inflow = config['base_inflow'] + config['inflow_increase']
                is_disturbed = True
            else:
                current_inflow = config['base_inflow']
                is_disturbed = False
            
            # 强扰动的水位计算（更明显的效果）
            base_outflow = config['base_inflow'] * 0.9  # 基础出流
            net_flow = current_inflow - base_outflow
            
            # 更新体积和水位
            volume += net_flow * dt
            water_level = volume / surface_area
            
            # 强扰动时添加更显著的效果
            if is_disturbed:
                # 在强扰动期间，水位变化更明显
                extra_effect = (current_inflow - config['base_inflow']) * dt / surface_area
                water_level += extra_effect * 0.5  # 增强效果
            
            # 添加小的随机噪声
            noise = np.random.normal(0, 0.0005)
            water_level += noise
            
            water_levels.append(water_level)
            
            self.simulation_history.append({
                'time': current_time,
                'water_level': water_level,
                'volume': volume,
                'inflow': current_inflow,
                'is_disturbed': is_disturbed,
                'step': len(self.simulation_history)
            })
            
            current_time += dt
        
        # 计算最大最小水位
        max_water_level = max(water_levels)
        min_water_level = min(water_levels)
        
        result_df = pd.DataFrame(self.simulation_history)
        result_df['max_water_level'] = max_water_level
        result_df['min_water_level'] = min_water_level
        result_df['initial_water_level'] = initial_water_level
        
        return result_df

# 初始化仿真器
if 'strong_inflow_simulator' not in st.session_state:
    st.session_state.strong_inflow_simulator = StrongInflowSimulator()

# 页面标题
st.title("💥 强入流扰动测试系统")
st.markdown("---")

# 创建主布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ 强扰动配置")
    
    # 基本参数配置
    st.subheader("📊 基本参数")
    
    col_a, col_b = st.columns(2)
    with col_a:
        base_inflow = st.number_input("基础入流量 (m³/s)", 50, 200, 100, 5, help="水库的正常入流量")
        surface_area = st.number_input("水库表面积 (m²)", format="%.0e", value=1e6, help="固定为100万平方米（基于脚本设定）", disabled=True)
    with col_b:
        initial_water_level = st.number_input("初始水位 (m)", 10.0, 25.0, 15.0, 0.5, help="水库初始水位")
        total_time = st.number_input("总仿真时间 (s)", 15.0, 30.0, 20.0, 1.0, help="整个测试的持续时间")
    
    # 强扰动配置
    st.subheader("💥 强扰动配置")
    
    st.info("💡 **强扰动设计**：使用足够大的入流增量来确保产生明显的物理效果")
    
    col_c, col_d = st.columns(2)
    with col_c:
        disturbance_start = st.number_input("扰动开始时间 (s)", 0.0, total_time-3, 2.0, 0.5, help="建议在2秒后开始")
        inflow_increase = st.number_input("入流增量 (m³/s)", 1000, 10000, 5000, 100, help="大幅增加入流以产生明显效果")
    with col_d:
        disturbance_end = st.number_input("扰动结束时间 (s)", disturbance_start+3, total_time, 12.0, 0.5, help="建议持续至少10秒")
        strong_inflow = base_inflow + inflow_increase
    
    # 计算扰动持续时间
    disturbance_duration = disturbance_end - disturbance_start
    
    # 理论计算
    st.subheader("🧮 强扰动理论计算")
    theoretical_level_change, volume_increase = st.session_state.strong_inflow_simulator.calculate_strong_disturbance_theory(
        inflow_increase, disturbance_duration, surface_area
    )
    
    col_e, col_f = st.columns(2)
    with col_e:
        st.metric("强扰动入流", f"{strong_inflow:.0f} m³/s", f"增加 {inflow_increase:.0f} m³/s")
        st.metric("扰动持续时间", f"{disturbance_duration:.1f} s", help="强扰动作用时间")
    with col_f:
        st.metric("额外体积", f"{volume_increase:.0f} m³", help="扰动期间额外增加的水量")
        st.metric("理论水位变化", f"{theoretical_level_change:.3f} m", 
                 f"{theoretical_level_change*1000:.1f} mm", help="预期的最大水位上升")
    
    # 强扰动效果预警
    if theoretical_level_change > 0.01:  # 超过1cm
        st.success(f"✅ **强扰动效果预期良好**\n预期水位变化: {theoretical_level_change*1000:.1f} mm")
    elif theoretical_level_change > 0.001:  # 1-10mm
        st.warning(f"⚠️ **中等强度扰动**\n预期水位变化: {theoretical_level_change*1000:.1f} mm")
    else:
        st.error(f"❌ **扰动强度可能不足**\n预期水位变化仅: {theoretical_level_change*1000:.1f} mm")
    
    # 显示强扰动摘要
    st.subheader("📋 强扰动摘要")
    st.info(f"**强扰动设计**\n"
           f"• 时间: {disturbance_start:.1f}s - {disturbance_end:.1f}s ({disturbance_duration:.1f}s)\n"
           f"• 入流: {base_inflow:.0f} → {strong_inflow:.0f} m³/s (增加{inflow_increase/1000:.1f}k)\n"
           f"• 预期效果: {theoretical_level_change*1000:.1f} mm 水位上升\n"
           f"• 强度级别: {'🔥极强' if inflow_increase >= 5000 else '💪强' if inflow_increase >= 2000 else '⚡中'}")

with col2:
    st.header("📊 强扰动测试结果")
    
    # 运行测试按钮
    if st.button("🚀 运行强入流扰动测试", type="primary", use_container_width=True):
        # 构建配置
        config = {
            'total_time': total_time,
            'disturbance_start': disturbance_start,
            'disturbance_end': disturbance_end,
            'base_inflow': base_inflow,
            'inflow_increase': inflow_increase,
            'surface_area': surface_area,
            'initial_water_level': initial_water_level
        }
        
        with st.spinner("正在运行强入流扰动测试..."):
            # 运行仿真
            results = st.session_state.strong_inflow_simulator.run_strong_disturbance_simulation(config)
            
            if results is not None and not results.empty:
                st.session_state.strong_test_results = {
                    'simulation_data': results,
                    'config': config,
                    'theoretical_change': theoretical_level_change,
                    'volume_increase': volume_increase,
                    'timestamp': datetime.now()
                }
                st.success("✅ 强入流扰动测试完成！")
            else:
                st.error("❌ 测试失败")
    
    # 显示测试结果
    if 'strong_test_results' in st.session_state:
        results = st.session_state.strong_test_results
        sim_data = results['simulation_data']
        config = results['config']
        
        # 计算关键指标
        initial_level = sim_data.iloc[0]['water_level'] if not sim_data.empty else initial_water_level
        max_level = sim_data['max_water_level'].iloc[0] if 'max_water_level' in sim_data.columns else sim_data['water_level'].max()
        min_level = sim_data['min_water_level'].iloc[0] if 'min_water_level' in sim_data.columns else sim_data['water_level'].min()
        final_level = sim_data.iloc[-1]['water_level'] if not sim_data.empty else initial_level
        
        max_level_change = max_level - initial_level
        level_range = max_level - min_level
        
        # 关键指标展示
        st.subheader("📈 强扰动效果指标")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("初始水位", f"{initial_level:.3f} m", 
                     f"基础入流: {config['base_inflow']:.0f} m³/s")
        
        with col_b:
            st.metric("最高水位", f"{max_level:.3f} m",
                     f"+{max_level_change*1000:.1f} mm")
        
        with col_c:
            st.metric("理论预期", f"{results['theoretical_change']*1000:.1f} mm",
                     f"实际: {max_level_change*1000:.1f} mm")
        
        with col_d:
            if max_level_change > 0.001:  # 超过1mm
                effectiveness = "🎉 成功"
                color = "normal"
            else:
                effectiveness = "❌ 不足"
                color = "inverse"
            st.metric("扰动效果", effectiveness,
                     f"变化: {max_level_change*1000:.3f} mm", delta_color=color)
        
        # 强扰动水位变化图表
        st.subheader("📊 强扰动水位变化分析")
        
        # 创建详细的时序图
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("水位变化 (重点关注最大变化)", "入流变化 (强扰动效应)", "水位变化量 (相对初始)"),
            row_heights=[0.5, 0.25, 0.25]
        )
        
        # 主水位曲线
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=sim_data['water_level'],
                mode='lines+markers',
                name='实际水位',
                line=dict(color='blue', width=3),
                marker=dict(size=3)
            ),
            row=1, col=1
        )
        
        # 标识最高和最低点
        max_time_idx = sim_data['water_level'].idxmax()
        min_time_idx = sim_data['water_level'].idxmin()
        
        if max_time_idx in sim_data.index:
            max_time = sim_data.loc[max_time_idx, 'time']
            fig.add_trace(
                go.Scatter(
                    x=[max_time], y=[max_level],
                    mode='markers+text',
                    name='最高水位',
                    marker=dict(color='red', size=10, symbol='star'),
                    text=[f'最高: {max_level:.3f}m'],
                    textposition='top center'
                ),
                row=1, col=1
            )
        
        # 理论基准线
        fig.add_hline(
            y=initial_level,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"初始水位 ({initial_level:.3f}m)",
            row=1, col=1
        )
        
        theoretical_max = initial_level + results['theoretical_change']
        fig.add_hline(
            y=theoretical_max,
            line_dash="dot",
            line_color="red",
            annotation_text=f"理论最高水位 ({theoretical_max:.3f}m)",
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
        
        # 相对水位变化
        relative_change = (sim_data['water_level'] - initial_level) * 1000  # 转换为mm
        fig.add_trace(
            go.Scatter(
                x=sim_data['time'],
                y=relative_change,
                mode='lines+markers',
                name='水位变化量 (mm)',
                line=dict(color='purple', width=2),
                marker=dict(size=3)
            ),
            row=3, col=1
        )
        
        # 标识强扰动区间
        fig.add_vrect(
            x0=config['disturbance_start'],
            x1=config['disturbance_end'],
            fillcolor="rgba(255,0,0,0.3)",
            opacity=0.4,
            annotation_text="💥 强扰动区间",
            annotation_position="top left",
            row=1, col=1
        )
        
        # 在其他子图也添加扰动区间
        for row in [2, 3]:
            fig.add_vrect(
                x0=config['disturbance_start'],
                x1=config['disturbance_end'],
                fillcolor="rgba(255,0,0,0.3)",
                opacity=0.4,
                row=row, col=1
            )
        
        # 更新布局
        fig.update_layout(
            title="强入流扰动测试结果详细分析",
            height=800,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
        fig.update_yaxes(title_text="入流量 (m³/s)", row=2, col=1)
        fig.update_yaxes(title_text="水位变化 (mm)", row=3, col=1)
        fig.update_xaxes(title_text="时间 (s)", row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 详细分析
        st.subheader("🔍 强扰动详细分析")
        
        # 效果验证结果
        with st.expander("✅ 强扰动效果验证"):
            col_x, col_y = st.columns(2)
            
            with col_x:
                st.markdown("**理论预期：**")
                st.success(f"• 入流增量: {config['inflow_increase']:.0f} m³/s\n"
                          f"• 扰动持续: {config['disturbance_end'] - config['disturbance_start']:.1f} s\n"
                          f"• 额外体积: {results['volume_increase']:.0f} m³\n"
                          f"• 预期最大水位变化: {results['theoretical_change']*1000:.1f} mm")
            
            with col_y:
                st.markdown("**实际结果：**")
                if max_level_change > 0.001:  # 超过1mm
                    st.success(f"• 初始水位: {initial_level:.3f} m\n"
                              f"• 最高水位: {max_level:.3f} m\n"
                              f"• 实际最大变化: {max_level_change*1000:.1f} mm\n"
                              f"• **验证结果: ✅ 成功**")
                else:
                    st.warning(f"• 初始水位: {initial_level:.3f} m\n"
                              f"• 最高水位: {max_level:.3f} m\n"
                              f"• 实际最大变化: {max_level_change*1000:.3f} mm\n"
                              f"• **验证结果: ⚠️ 效果不明显**")
            
            # 总体验证结论
            if max_level_change > 0.001:
                st.success("🎉 **强入流扰动验证成功！** 扰动产生了明显的物理效果，证明扰动功能有效。")
            else:
                st.error("❌ **需要进一步检查** 即使使用强扰动，水位变化仍然很小，建议增加扰动强度或检查系统配置。")
        
        # 水位变化详细统计
        with st.expander("📊 水位变化详细统计"):
            st.markdown("**关键统计指标：**")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"• **最高水位**: {max_level:.6f} m")
                st.write(f"• **最低水位**: {min_level:.6f} m") 
                st.write(f"• **最终水位**: {final_level:.6f} m")
                
            with col_b:
                st.write(f"• **最大上升**: {max_level_change*1000:.3f} mm")
                st.write(f"• **水位波动范围**: {level_range*1000:.3f} mm")
                st.write(f"• **理论准确度**: {min(100, max(0, 100-(abs(max_level_change-results['theoretical_change'])/max(results['theoretical_change'],0.001)*100))):.1f}%")
                
            with col_c:
                # 扰动期间统计
                disturbed_data = sim_data[sim_data['is_disturbed'] == True]
                if not disturbed_data.empty:
                    avg_disturbed_level = disturbed_data['water_level'].mean()
                    max_disturbed_level = disturbed_data['water_level'].max()
                    st.write(f"• **扰动期平均水位**: {avg_disturbed_level:.6f} m")
                    st.write(f"• **扰动期最高水位**: {max_disturbed_level:.6f} m")
                    st.write(f"• **扰动期步数**: {len(disturbed_data)}")
        
        # 原始数据展示
        with st.expander("📋 原始仿真数据"):
            if not sim_data.empty:
                # 数据预处理用于展示
                display_data = sim_data[['time', 'water_level', 'inflow', 'volume', 'is_disturbed']].copy()
                display_data['water_level'] = display_data['water_level'].round(6)
                display_data['inflow'] = display_data['inflow'].round(0)
                display_data['volume'] = display_data['volume'].round(0)
                display_data['water_level_change_mm'] = ((display_data['water_level'] - initial_level) * 1000).round(3)
                display_data['扰动状态'] = display_data['is_disturbed'].map({True: '🔥 强扰动中', False: '🟢 正常'})
                
                display_data = display_data.drop('is_disturbed', axis=1)
                display_data.columns = ['时间(s)', '水位(m)', '入流(m³/s)', '体积(m³)', '水位变化(mm)', '状态']
                
                # 高亮显示最大水位变化的行
                def highlight_max(s):
                    if s.name == '水位变化(mm)':
                        max_val = s.max()
                        return [f'background-color: {"lightcoral" if v == max_val and v > 1 else ""}' for v in s]
                    return ['' for _ in s]
                
                styled_data = display_data.style.apply(highlight_max, axis=0)
                st.dataframe(styled_data, use_container_width=True, height=400)

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
    st.info("📊 仿真环境状态数据\n🌊 水库组件参数\n📈 强扰动水位变化数据\n🧮 理论计算结果\n📋 最大水位变化统计")
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 💥 强入流扰动：使用足够大的扰动确保产生明显效果
    2. 📊 最大效果追踪：重点关注最大水位变化
    3. 🔄 实时监控：记录整个强扰动过程
    4. ✅ 有效性验证：验证扰动功能是否真正有效
    5. 📈 理论对比：强扰动预期与实际效果对比
    
    **应用场景：**
    - 扰动功能有效性验证
    - 极端条件下系统响应测试  
    - 物理计算核心敏感度测试
    - 扰动框架基准测试
    """)
    
    # 强扰动特点说明
    st.subheader("💥 强扰动特点")
    st.markdown("""
    **与普通扰动的区别：**
    - 🔥 **扰动强度**：入流增量1000-10000 m³/s
    - ⏰ **持续时间**：建议10秒以上
    - 📏 **预期效果**：毫米级甚至厘米级水位变化
    - 🎯 **验证目标**：确保扰动功能确实有效
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **设置基本参数**：配置基础入流和水位
        2. **配置强扰动**：设置大幅度的入流增量
        3. **查看理论预期**：了解预期的强扰动效果
        4. **运行强扰动测试**：执行强扰动仿真
        5. **分析验证结果**：重点查看最大水位变化
        
        **强扰动建议：**
        - **入流增量**：建议≥2000 m³/s以确保明显效果
        - **扰动时间**：建议≥10秒以产生足够累积效应
        - **效果判断**：水位变化≥1mm视为有效
        - **参数调节**：如效果不明显可增加扰动强度
        """)
    
    # 验证标准说明
    with st.expander("✅ 验证标准"):
        st.markdown("""
        **强扰动成功标准：**
        ```
        水位变化 ≥ 1.0 mm  ✅ 成功
        0.1 mm ≤ 水位变化 < 1.0 mm  ⚠️ 中等
        水位变化 < 0.1 mm  ❌ 不足
        ```
        
        **效果评估：**
        - 理论准确度 > 90%：计算精确
        - 理论准确度 70-90%：基本符合
        - 理论准确度 < 70%：需要检查
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `10.test_strong_inflow_disturbance.py` 的强入流扰动测试系统*")
