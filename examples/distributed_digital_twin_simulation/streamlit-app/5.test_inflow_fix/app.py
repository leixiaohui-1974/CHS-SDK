#!/usr/bin/env python3
"""
Streamlit 視覺化頁面：基於 5.test_inflow_fix.py 的業務邏輯

功能點：
- 輸入場景路徑（預設為當前目錄）
- 輸入期望 inflow（預設 100.0）
- 點擊按鈕後：
  - 使用 SimulationBuilder 載入場景
  - 列出所有元件名稱與型別
  - 如元件具備 _inflow 或 _params['inflow'] 則展示
  - 針對 Upstream_Reservoir 顯示 inflow 對比結果（成功/失敗）
"""

import os
import sys
import traceback

import streamlit as st


# 当前脚本所在目录
CURRENT_DIR = Path(__file__).resolve().parent
# 项目根目录 (E:\CHS-SDK)
PROJECT_ROOT = CURRENT_DIR.parents[2]   # 回到 E:\CHS-SDK

# 添加 core_lib 到 sys.path
sys.path.append(str(PROJECT_ROOT / "core_lib"))

# 將專案根目錄加入 sys.path，對齊原測試腳本行為
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from core_lib.io.yaml_loader import SimulationBuilder  # type: ignore


def load_harness(scenario_path: str):
    builder = SimulationBuilder(scenario_path)
    return builder.load()


def render_components(components: dict):
    st.subheader("元件列表")
    st.caption(f"找到 {len(components)} 個元件")

    for comp_name, component in components.items():
        with st.expander(f"{comp_name}"):
            st.write({
                "type": type(component).__name__,
            })
            if hasattr(component, '_inflow'):
                st.write({"_inflow": getattr(component, '_inflow')})
            if hasattr(component, '_params'):
                params = getattr(component, '_params')
                if isinstance(params, dict):
                    st.json(params)
                else:
                    st.write({"_params": str(params)})


def check_upstream_reservoir(components: dict, expected_inflow: float):
    st.subheader("Upstream_Reservoir 詳細檢查")
    upstream = components.get('Upstream_Reservoir')
    if not upstream:
        st.error("未找到 Upstream_Reservoir 元件")
        return

    comp_type = type(upstream).__name__
    inflow_value = getattr(upstream, '_inflow', None)
    params = getattr(upstream, '_params', {})

    cols = st.columns(3)
    with cols[0]:
        st.metric("類型", comp_type)
    with cols[1]:
        st.metric("_inflow", inflow_value)
    with cols[2]:
        st.metric("期望 inflow", expected_inflow)

    with st.expander("參數 _params"):
        st.json(params if isinstance(params, dict) else {"_params": str(params)})

    if inflow_value == expected_inflow:
        st.success(f"成功！inflow 參數已正確設為 {expected_inflow}")
    else:
        st.error(f"失敗！期望 inflow 為 {expected_inflow}，實際為 {inflow_value}")


def main():
    st.set_page_config(page_title="Inflow 參數檢查", page_icon="💧", layout="wide")
    st.title("💧 Inflow 參數修復效果檢視")
    st.caption("基於 5.test_inflow_fix.py 的可視化操作頁面")

    with st.sidebar:
        st.header("設定")
        default_scenario_path = '.'
        scenario_path = st.text_input("場景路徑 (scenario_path)", value=default_scenario_path)
        expected_inflow = st.number_input("期望 inflow", value=100.0, step=1.0, format="%f")
        run = st.button("載入並檢查", type="primary")

    if run:
        try:
            st.info("正在載入場景 ...")
            harness = load_harness(scenario_path)
            components = getattr(harness, 'components', {})

            render_components(components)
            check_upstream_reservoir(components, float(expected_inflow))
        except Exception as exc:
            st.error("載入或檢查過程發生錯誤")
            st.exception(exc)
            with st.expander("完整錯誤堆疊"):
                st.code(traceback.format_exc())
    else:
        st.info("請在左側輸入設定後點擊『載入並檢查』")


if __name__ == '__main__':
    main()


