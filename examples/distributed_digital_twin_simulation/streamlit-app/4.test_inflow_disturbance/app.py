#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Dict, List

import streamlit as st
import pandas as pd

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



# 核心模組（依據 4.test_inflow_disturbance.py）
from core_lib.io.yaml_loader import SimulationBuilder
from dynamic_disturbance_manager import DynamicDisturbanceManager
from core_lib.central_coordination.collaboration.message_bus import MessageBus


def run_simulation(
    working_dir: str,
    target_component: str,
    magnitude: float,
    pattern: str,
    start_time: float,
    duration: float,
    dt: float,
    total_time: float,
) -> Dict[str, List[float]]:
    """執行一次仿真，返回時間序列資料。"""
    # 構建仿真
    builder = SimulationBuilder(working_dir)
    harness = builder.load()

    # 取得元件
    component = harness.components.get(target_component)
    if not component:
        raise RuntimeError(f"未找到目標元件: {target_component}")

    # 擾動管理器
    message_bus = MessageBus()
    disturbance_manager = DynamicDisturbanceManager(message_bus)

    # 擾動配置
    disturbance_config = {
        'type': 'inflow_variation',
        'disturbance_scenario': {
            'type': 'inflow_variation',
            'parameters': {
                'target_component': target_component,
                'magnitude': float(magnitude),
                'pattern': pattern,
            },
        },
    }

    disturbance_manager.register_disturbance(
        'inflow_test', disturbance_config, float(start_time), float(duration)
    )

    # 仿真迴圈
    current_time = 0.0
    times: List[float] = []
    inflows: List[float] = []
    water_levels: List[float] = []

    # 進度條
    progress = 0
    total_steps = int(total_time / dt) if dt > 0 else 0

    while current_time < total_time:
        disturbance_manager.update(current_time, harness)
        harness.step()

        # 記錄資料
        state = component.get_state()
        current_inflow = getattr(component, '_inflow', None)
        times.append(round(current_time, 6))
        inflows.append(float(current_inflow) if current_inflow is not None else float('nan'))
        water_levels.append(float(state.get('water_level', float('nan'))))

        current_time += dt
        progress += 1
        if total_steps > 0:
            st.session_state.progress_bar.progress(min(progress / total_steps, 1.0))

    return {
        'time': times,
        'inflow': inflows,
        'water_level': water_levels,
    }


def main() -> None:
    st.set_page_config(page_title='入流擾動仿真', page_icon='🌊', layout='wide')

    st.title('🌊 入流擾動對物理計算核心的影響（可視化）')
    st.caption('基於 4.test_inflow_disturbance.py 的交互式可視化介面')

    # 初始化 session 狀態
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = st.progress(0.0)

    # 側邊欄參數配置
    with st.sidebar:
        st.header('仿真配置')
        working_dir = st.text_input('工作目錄（SimulationBuilder 路徑）', '.', help='通常為專案執行目錄')
        target_component = st.text_input('目標元件名稱', 'Upstream_Reservoir')
        magnitude = st.number_input('擾動幅值（m³/s）', value=50.0, step=5.0, format='%.2f')
        pattern = st.selectbox('擾動模式', ['step'], index=0)

        st.divider()
        st.subheader('時間設定')
        start_time = st.number_input('開始時間（s）', value=1.0, step=0.5, format='%.2f')
        duration = st.number_input('持續時間（s）', value=10.0, step=0.5, format='%.2f')
        dt = st.number_input('時間步長 dt（s）', value=0.5, step=0.1, min_value=0.01, format='%.2f')
        total_time = st.number_input('總仿真時間（s）', value=15.0, step=1.0, min_value=dt, format='%.2f')

        st.divider()
        run_btn = st.button('▶️ 開始仿真', use_container_width=True)

    # 主區域
    log_placeholder = st.empty()
    chart_col1, chart_col2 = st.columns(2)

    if run_btn:
        try:
            st.session_state.progress_bar.progress(0.0)
            with st.spinner('正在執行仿真，請稍候...'):
                results = run_simulation(
                    working_dir=working_dir,
                    target_component=target_component,
                    magnitude=magnitude,
                    pattern=pattern,
                    start_time=start_time,
                    duration=duration,
                    dt=dt,
                    total_time=total_time,
                )

            df = pd.DataFrame(
                {
                    'time_s': results['time'],
                    'inflow_m3s': results['inflow'],
                    'water_level_m': results['water_level'],
                }
            )

            # 顯示數據表
            with st.expander('查看原始數據表', expanded=False):
                st.dataframe(df, use_container_width=True, hide_index=True)

            # 繪圖
            with chart_col1:
                st.subheader('入流（m³/s）')
                st.line_chart(df, x='time_s', y='inflow_m3s', height=300)
            with chart_col2:
                st.subheader('水位（m）')
                st.line_chart(df, x='time_s', y='water_level_m', height=300)

            # 結果摘要
            st.divider()
            st.subheader('結果摘要')
            initial_inflow = df['inflow_m3s'].iloc[0] if not df.empty else float('nan')
            final_inflow = df['inflow_m3s'].iloc[-1] if not df.empty else float('nan')
            final_level = df['water_level_m'].iloc[-1] if not df.empty else float('nan')

            col_a, col_b, col_c = st.columns(3)
            col_a.metric('初始入流 (m³/s)', f"{initial_inflow:.1f}")
            col_b.metric('最終入流 (m³/s)', f"{final_inflow:.1f}")
            col_c.metric('最終水位 (m)', f"{final_level:.3f}")

            # 驗證擾動是否生效（依據原測試腳本邏輯）
            if final_inflow != 100.0:
                st.success('入流擾動已成功影響物理計算核心 ✅')
            else:
                st.warning('入流擾動似乎未生效，請檢查設定或模型 ❗')

        except Exception as e:
            st.session_state.progress_bar.progress(0.0)
            st.error(f"執行失敗：{e}")

    st.caption('提示：可透過側邊欄調整擾動與時間參數，點擊「開始仿真」即可。')


if __name__ == '__main__':
    main()


