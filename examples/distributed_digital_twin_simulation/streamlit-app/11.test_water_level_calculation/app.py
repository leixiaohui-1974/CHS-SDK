#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水位变化计算测试 - Streamlit界面

这个应用提供了一个直观的界面来验证和分析水位变化计算的准确性：
1. 获取和分析水库基本参数（初始水位、体积、表面积等）
2. 解析和可视化库容曲线，计算不同水位段的表面积
3. 基于库容曲线进行精确的理论水位变化计算
4. 预测扰动效果并提供参数优化建议
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
    page_title="水位变化计算测试系统",
    page_icon="📐",
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

class WaterLevelCalculationAnalyzer:
    """水位计算分析器"""
    
    def __init__(self):
        self.harness = None
        self.upstream_reservoir = None
        self.reservoir_params = {}
        self.storage_curve = []
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
                
                # 获取水库参数
                initial_state = self.upstream_reservoir.get_state()
                parameters = self.upstream_reservoir.get_parameters()
                
                self.reservoir_params = {
                    'initial_water_level': initial_state.get('water_level', 15.0),
                    'initial_volume': initial_state.get('volume', 0),
                    'surface_area': parameters.get('surface_area', None),
                    'storage_curve': parameters.get('storage_curve', []),
                    'capacity': parameters.get('capacity', None)
                }
                
                self.storage_curve = self.reservoir_params['storage_curve']
                self.is_initialized = True
                return True
                
            except Exception as e:
                st.error(f"初始化仿真环境失败: {e}")
                return False
        else:
            # 模拟模式初始化
            self.reservoir_params = {
                'initial_water_level': 15.0,
                'initial_volume': 15e6,
                'surface_area': 1e6,
                'storage_curve': [
                    (0, 10.0),
                    (5e6, 12.5),
                    (15e6, 15.0),
                    (30e6, 17.5),
                    (50e6, 20.0)
                ],
                'capacity': 50e6
            }
            self.storage_curve = self.reservoir_params['storage_curve']
            self.is_initialized = True
            return True
    
    def analyze_storage_curve(self):
        """分析库容曲线"""
        if not self.storage_curve:
            return None, None
        
        # 转换为DataFrame便于分析
        curve_df = pd.DataFrame(self.storage_curve, columns=['volume', 'water_level'])
        curve_df = curve_df.sort_values('water_level')
        
        # 计算各段的表面积
        surface_areas = []
        for i in range(len(curve_df) - 1):
            v1, l1 = curve_df.iloc[i]['volume'], curve_df.iloc[i]['water_level']
            v2, l2 = curve_df.iloc[i + 1]['volume'], curve_df.iloc[i + 1]['water_level']
            
            if l2 != l1:
                avg_surface_area = (v2 - v1) / (l2 - l1)
                surface_areas.append({
                    'level_range': f"{l1:.1f}-{l2:.1f}m",
                    'volume_range': f"{v1/1e6:.1f}-{v2/1e6:.1f}M m³",
                    'surface_area': avg_surface_area,
                    'level_start': l1,
                    'level_end': l2,
                    'volume_start': v1,
                    'volume_end': v2
                })
        
        surface_area_df = pd.DataFrame(surface_areas)
        return curve_df, surface_area_df
    
    def find_current_surface_area(self, current_level):
        """根据当前水位找到对应的表面积"""
        curve_df, surface_area_df = self.analyze_storage_curve()
        
        if surface_area_df is None or surface_area_df.empty:
            return self.reservoir_params.get('surface_area', 1e6)
        
        # 找到当前水位所在的段
        for _, row in surface_area_df.iterrows():
            if row['level_start'] <= current_level <= row['level_end']:
                return row['surface_area']
        
        # 如果没有找到，使用最接近的段
        if current_level < surface_area_df['level_start'].min():
            return surface_area_df.iloc[0]['surface_area']
        elif current_level > surface_area_df['level_end'].max():
            return surface_area_df.iloc[-1]['surface_area']
        
        return 1e6  # 默认值
    
    def calculate_theoretical_change(self, inflow_increase, duration, current_level):
        """计算理论水位变化"""
        surface_area = self.find_current_surface_area(current_level)
        volume_increase = inflow_increase * duration
        level_change = volume_increase / surface_area
        
        return level_change, volume_increase, surface_area
    
    def get_optimization_suggestions(self, theoretical_change):
        """获取优化建议"""
        suggestions = []
        
        if theoretical_change < 0.0001:  # 小于0.1mm
            suggestions.append("🚨 **水位变化极小**，强烈建议：")
            suggestions.append("• 将入流增量提高至500-1000 m³/s")
            suggestions.append("• 延长扰动时间至30-60秒")
            suggestions.append("• 考虑使用强扰动测试模式")
        elif theoretical_change < 0.001:  # 小于1mm
            suggestions.append("⚠️ **水位变化较小**，建议：")
            suggestions.append("• 增加入流增量至200-500 m³/s")
            suggestions.append("• 延长扰动时间至20-30秒")
            suggestions.append("• 使用高精度监控输出")
        elif theoretical_change < 0.01:  # 小于1cm
            suggestions.append("✅ **水位变化适中**，可以观察到效果")
            suggestions.append("• 当前参数设置合理")
            suggestions.append("• 建议监控精度设为毫米级")
        else:  # 大于1cm
            suggestions.append("🎯 **水位变化显著**，效果应该很明显")
            suggestions.append("• 参数设置很好，效果容易观察")
            suggestions.append("• 可以验证计算模型的准确性")
        
        return suggestions

# 初始化分析器
if 'water_level_analyzer' not in st.session_state:
    st.session_state.water_level_analyzer = WaterLevelCalculationAnalyzer()

# 页面标题
st.title("📐 水位变化计算测试系统")
st.markdown("---")

# 创建主布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📊 系统参数分析")
    
    # 初始化按钮
    if st.button("🔄 加载水库参数", type="primary", use_container_width=True):
        with st.spinner("正在加载水库参数..."):
            if st.session_state.water_level_analyzer.initialize_simulation():
                st.success("✅ 水库参数加载成功！")
                st.session_state.params_loaded = True
            else:
                st.error("❌ 参数加载失败")
    
    # 显示水库参数
    if hasattr(st.session_state, 'params_loaded') and st.session_state.params_loaded:
        analyzer = st.session_state.water_level_analyzer
        params = analyzer.reservoir_params
        
        st.subheader("🏗️ 水库基本参数")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("初始水位", f"{params['initial_water_level']:.3f} m")
            st.metric("初始体积", f"{params['initial_volume']/1e6:.1f} M m³")
        with col_b:
            if params.get('surface_area'):
                st.metric("表面积", f"{params['surface_area']/1e6:.2f} km²")
            else:
                st.info("表面积：从库容曲线计算")
            if params.get('capacity'):
                st.metric("库容", f"{params['capacity']/1e6:.1f} M m³")
        
        # 扰动参数设置
        st.subheader("🌊 扰动参数设置")
        
        col_c, col_d = st.columns(2)
        with col_c:
            inflow_increase = st.number_input("入流增量 (m³/s)", 10, 1000, 50, 10, 
                                            help="相对于基础入流的增量")
            duration = st.number_input("扰动持续时间 (s)", 1, 60, 10, 1,
                                     help="扰动作用的时间长度")
        with col_d:
            target_level = st.number_input("计算水位 (m)", 
                                         params['initial_water_level']-1, 
                                         params['initial_water_level']+5, 
                                         params['initial_water_level'], 0.1,
                                         help="用于计算的目标水位")
        
        # 计算理论变化
        if st.button("🧮 计算理论水位变化", use_container_width=True):
            theoretical_change, volume_increase, surface_area = analyzer.calculate_theoretical_change(
                inflow_increase, duration, target_level
            )
            
            st.session_state.calculation_results = {
                'theoretical_change': theoretical_change,
                'volume_increase': volume_increase,
                'surface_area': surface_area,
                'inflow_increase': inflow_increase,
                'duration': duration,
                'target_level': target_level
            }
        
        # 显示计算结果
        if 'calculation_results' in st.session_state:
            results = st.session_state.calculation_results
            
            st.subheader("📐 理论计算结果")
            
            col_e, col_f = st.columns(2)
            with col_e:
                st.metric("额外体积", f"{results['volume_increase']:.0f} m³")
                st.metric("当前表面积", f"{results['surface_area']/1e6:.2f} km²")
            with col_f:
                st.metric("理论水位变化", f"{results['theoretical_change']:.6f} m",
                         f"{results['theoretical_change']*1000:.3f} mm")
                
                # 效果评估
                if results['theoretical_change'] >= 0.001:
                    st.success("✅ 效果明显")
                elif results['theoretical_change'] >= 0.0001:
                    st.warning("⚠️ 效果一般")
                else:
                    st.error("❌ 效果微弱")
            
            # 优化建议
            st.subheader("💡 优化建议")
            suggestions = analyzer.get_optimization_suggestions(results['theoretical_change'])
            for suggestion in suggestions:
                st.markdown(suggestion)
    
    else:
        st.info("👆 点击上方按钮加载水库参数")

with col2:
    st.header("📈 分析结果展示")
    
    if hasattr(st.session_state, 'params_loaded') and st.session_state.params_loaded:
        analyzer = st.session_state.water_level_analyzer
        
        # 库容曲线分析
        st.subheader("📊 库容曲线分析")
        
        curve_df, surface_area_df = analyzer.analyze_storage_curve()
        
        if curve_df is not None and not curve_df.empty:
            # 创建库容曲线图
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=False,
                vertical_spacing=0.1,
                subplot_titles=("库容曲线 (体积 vs 水位)", "各段平均表面积"),
                row_heights=[0.6, 0.4]
            )
            
            # 库容曲线
            fig.add_trace(
                go.Scatter(
                    x=curve_df['water_level'],
                    y=curve_df['volume'] / 1e6,  # 转换为百万立方米
                    mode='lines+markers',
                    name='库容曲线',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=1
            )
            
            # 标识当前水位
            params = analyzer.reservoir_params
            current_level = params['initial_water_level']
            current_volume = params['initial_volume']
            
            fig.add_trace(
                go.Scatter(
                    x=[current_level],
                    y=[current_volume / 1e6],
                    mode='markers+text',
                    name='当前状态',
                    marker=dict(color='red', size=12, symbol='star'),
                    text=[f'当前状态<br>{current_level:.1f}m<br>{current_volume/1e6:.1f}M m³'],
                    textposition='top center'
                ),
                row=1, col=1
            )
            
            # 各段表面积
            if surface_area_df is not None and not surface_area_df.empty:
                mid_levels = [(row['level_start'] + row['level_end']) / 2 
                             for _, row in surface_area_df.iterrows()]
                
                fig.add_trace(
                    go.Bar(
                        x=[f"{row['level_range']}" for _, row in surface_area_df.iterrows()],
                        y=[row['surface_area'] / 1e6 for _, row in surface_area_df.iterrows()],
                        name='平均表面积',
                        marker_color='lightblue',
                        opacity=0.7
                    ),
                    row=2, col=1
                )
            
            # 更新布局
            fig.update_layout(
                title="水库库容曲线和表面积分析",
                height=700,
                showlegend=True
            )
            
            fig.update_yaxes(title_text="体积 (M m³)", row=1, col=1)
            fig.update_yaxes(title_text="表面积 (km²)", row=2, col=1)
            fig.update_xaxes(title_text="水位 (m)", row=1, col=1)
            fig.update_xaxes(title_text="水位段", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 库容曲线数据表
            with st.expander("📋 库容曲线详细数据"):
                st.markdown("**库容曲线控制点：**")
                curve_display = curve_df.copy()
                curve_display['volume_M'] = curve_display['volume'] / 1e6
                curve_display = curve_display[['water_level', 'volume_M']].round(3)
                curve_display.columns = ['水位 (m)', '体积 (M m³)']
                st.dataframe(curve_display, use_container_width=True)
                
                if surface_area_df is not None and not surface_area_df.empty:
                    st.markdown("**各水位段表面积：**")
                    surface_display = surface_area_df.copy()
                    surface_display['surface_area_km2'] = surface_display['surface_area'] / 1e6
                    display_cols = ['level_range', 'volume_range', 'surface_area_km2']
                    surface_display = surface_display[display_cols].round(3)
                    surface_display.columns = ['水位段 (m)', '体积段 (M m³)', '平均表面积 (km²)']
                    st.dataframe(surface_display, use_container_width=True)
        
        # 计算验证结果
        if 'calculation_results' in st.session_state:
            st.subheader("🔍 计算验证详情")
            
            results = st.session_state.calculation_results
            
            # 创建计算过程展示
            col_x, col_y = st.columns(2)
            
            with col_x:
                st.markdown("**计算输入参数：**")
                st.info(f"• 入流增量: {results['inflow_increase']} m³/s\n"
                        f"• 扰动持续时间: {results['duration']} s\n"
                        f"• 计算水位: {results['target_level']:.3f} m\n"
                        f"• 对应表面积: {results['surface_area']/1e6:.3f} km²")
            
            with col_y:
                st.markdown("**计算过程和结果：**")
                st.success(f"• 额外体积 = {results['inflow_increase']} × {results['duration']} = {results['volume_increase']} m³\n"
                          f"• 水位变化 = {results['volume_increase']} ÷ {results['surface_area']:.0f} = {results['theoretical_change']:.6f} m\n"
                          f"• **结果: {results['theoretical_change']*1000:.3f} mm**")
            
            # 效果预测和建议
            with st.expander("📊 效果预测和参数建议"):
                theoretical_change = results['theoretical_change']
                
                # 效果分级
                if theoretical_change >= 0.01:
                    effect_level = "🔥 显著效果"
                    color = "success"
                elif theoretical_change >= 0.001:
                    effect_level = "✅ 明显效果"  
                    color = "success"
                elif theoretical_change >= 0.0001:
                    effect_level = "⚠️ 轻微效果"
                    color = "warning"
                else:
                    effect_level = "❌ 效果微弱"
                    color = "error"
                
                if color == "success":
                    st.success(f"**{effect_level}**\n水位变化: {theoretical_change*1000:.3f} mm")
                elif color == "warning":
                    st.warning(f"**{effect_level}**\n水位变化: {theoretical_change*1000:.3f} mm")
                else:
                    st.error(f"**{effect_level}**\n水位变化: {theoretical_change*1000:.3f} mm")
                
                # 参数优化建议表格
                st.markdown("**参数优化建议表：**")
                
                suggestions_data = []
                base_inflow = results['inflow_increase']
                base_duration = results['duration']
                
                # 生成不同组合的建议
                for mult in [0.5, 1.0, 2.0, 5.0]:
                    for dur_mult in [1.0, 2.0, 3.0]:
                        new_inflow = base_inflow * mult
                        new_duration = base_duration * dur_mult
                        new_change, _, _ = analyzer.calculate_theoretical_change(
                            new_inflow, new_duration, results['target_level']
                        )
                        
                        suggestions_data.append({
                            '入流增量': f"{new_inflow:.0f} m³/s",
                            '持续时间': f"{new_duration:.0f} s",
                            '预期变化': f"{new_change*1000:.3f} mm",
                            '效果评级': "🔥显著" if new_change >= 0.01 else "✅明显" if new_change >= 0.001 else "⚠️轻微" if new_change >= 0.0001 else "❌微弱"
                        })
                
                suggestions_df = pd.DataFrame(suggestions_data)
                # 按预期变化排序
                suggestions_df = suggestions_df.iloc[suggestions_df['预期变化'].str.replace(' mm', '').astype(float).argsort()[::-1]]
                
                st.dataframe(suggestions_df.head(10), use_container_width=True, height=300)
    
    else:
        st.info("💡 请先在左侧加载水库参数以查看分析结果")

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
    st.info("📊 水库组件状态数据\n🏗️ 水库物理参数\n📈 库容曲线数据\n📐 表面积计算结果\n💡 理论计算验证")
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 📊 参数获取：获取水库的完整物理参数
    2. 📈 库容分析：解析库容曲线，计算各段表面积
    3. 📐 理论计算：基于准确表面积计算水位变化
    4. ✅ 计算验证：验证理论计算公式的正确性
    5. 💡 效果预测：预测不同参数下的扰动效果
    
    **应用场景：**
    - 扰动参数设计前的理论验证
    - 计算模型准确性验证
    - 扰动效果预测和优化
    - 水库特性参数分析
    """)
    
    # 计算方法说明
    st.subheader("📐 计算方法")
    st.markdown("""
    **表面积计算：**
    - 基于库容曲线的分段线性插值
    - 各段平均表面积 = Δ体积 / Δ水位
    - 根据当前水位找到对应段的表面积
    
    **水位变化计算：**
    ```
    水位变化 = 额外体积 / 当前表面积
    额外体积 = 入流增量 × 持续时间
    ```
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **加载参数**：点击"加载水库参数"获取系统参数
        2. **设置扰动参数**：配置入流增量、持续时间、计算水位
        3. **执行计算**：点击"计算理论水位变化"
        4. **分析结果**：查看库容曲线和计算验证结果
        5. **优化参数**：根据建议优化扰动参数设置
        
        **重要概念：**
        - **库容曲线**：描述水库体积与水位关系的曲线
        - **表面积变化**：不同水位段具有不同的平均表面积
        - **线性插值**：在库容曲线控制点间进行线性插值
        """)
    
    # 效果评级标准
    with st.expander("📊 效果评级标准"):
        st.markdown("""
        **水位变化效果分级：**
        ```
        🔥 显著效果：≥ 10.0 mm
        ✅ 明显效果：1.0 - 10.0 mm
        ⚠️ 轻微效果：0.1 - 1.0 mm  
        ❌ 效果微弱：< 0.1 mm
        ```
        
        **建议：**
        - 显著/明显效果：参数设置合理，容易观察
        - 轻微效果：建议增强参数，提高观测精度
        - 效果微弱：必须大幅调整参数或使用强扰动模式
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `11.test_water_level_calculation.py` 的水位变化计算测试系统*")
