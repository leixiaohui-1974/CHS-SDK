#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 前端：可视化运行 3.test_disturbance_with_harness_fix.py

功能：
- 动态加载脚本模块
- 一键运行原脚本 main() 并捕获日志/打印
- 自定义参数仿真（基于脚本内 load_simulation_harness 与 patch_harness_for_disturbance）
- 结果可视化（曲线/指标）与下载
- 文档页签（模块与函数 docstring）

说明：为避免 Windows 下“同名文件与文件夹”冲突，目录名使用后缀 _app。
"""

import os
import sys
import io
import json
import time
import logging
import importlib.util
import inspect
from typing import Any, Dict, List, Optional
from contextlib import redirect_stdout

import pandas as pd
import streamlit as st

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


st.set_page_config(page_title="扰动功能修复演示", layout="wide")


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

project_root = Path(get_project_root())
DEFAULT_SCRIPT_PATH = project_root.parent / "3.test_comprehensive_disturbance.py"
# DEFAULT_SCRIPT_PATH = os.path.join(get_project_root(), "3.test_disturbance_with_harness_fix.py")


@st.cache_resource(show_spinner=False)
def load_script_module(script_path: str):
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"未找到脚本文件: {script_path}")
    module_name = "test_harness_fix_module"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError("无法为脚本创建导入规格（spec）。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def verify_module_api(module) -> Dict[str, bool]:
    required = ["load_simulation_harness", "patch_harness_for_disturbance", "main"]
    return {name: hasattr(module, name) for name in required}


class StreamCaptureHandler(logging.Handler):
    def __init__(self, buffer: io.StringIO):
        super().__init__()
        self.buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.buffer.write(msg + "\n")
        except Exception:  # noqa: BLE001
            pass


def run_with_captures(fn, *args, **kwargs):
    log_buffer = io.StringIO()
    out_buffer = io.StringIO()

    # logging 捕获
    handler = StreamCaptureHandler(log_buffer)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    prev_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    try:
        # stdout 捕获
        with redirect_stdout(out_buffer):
            result = fn(*args, **kwargs)
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(prev_level)

    logs = log_buffer.getvalue()
    prints = out_buffer.getvalue()
    log_buffer.close()
    out_buffer.close()
    return result, logs, prints


def run_custom_simulation(module, *,
                          disturbed_component_id: str,
                          disturbance_start_time: float,
                          disturbance_duration: float,
                          dt: float,
                          total_time: float,
                          inflow_delta: float,
                          surface_area: float) -> Dict[str, Any]:
    # 加载 harness
    harness = module.load_simulation_harness()

    # 获取组件
    components = getattr(harness, "components", {})
    if not isinstance(components, dict):
        raise RuntimeError("harness.components 不是 dict，无法继续自定义仿真。")

    upstream = components.get(disturbed_component_id)
    if upstream is None:
        available = list(components.keys())
        raise RuntimeError(f"未找到组件 {disturbed_component_id}。可用组件: {available}")

    # 初始状态
    initial_state = upstream.get_state()
    initial_water_level = initial_state.get('water_level', 0.0)
    original_inflow = getattr(upstream, '_inflow', 0.0)

    # 理论增量
    delta_inflow = inflow_delta
    delta_volume = delta_inflow * disturbance_duration
    theoretical_water_level_change = delta_volume / max(surface_area, 1e-6)

    # 打补丁
    disturbance_active_flag = {'active': False}
    original_method = module.patch_harness_for_disturbance(harness, disturbed_component_id, disturbance_active_flag)

    # 仿真循环
    steps = int(total_time / max(dt, 1e-9))
    time_data: List[float] = []
    water_level_data: List[float] = []
    inflow_data: List[float] = []

    for step in range(steps):
        current_time = step * dt

        if disturbance_start_time <= current_time < (disturbance_start_time + disturbance_duration):
            if not disturbance_active_flag['active']:
                disturbance_active_flag['active'] = True
                upstream.set_inflow(original_inflow + inflow_delta)
        elif current_time >= (disturbance_start_time + disturbance_duration):
            if disturbance_active_flag['active']:
                disturbance_active_flag['active'] = False
                upstream.set_inflow(original_inflow)

        # 执行仿真步骤
        harness.step()

        # 记录
        current_state = upstream.get_state()
        current_water_level = current_state.get('water_level', 0.0)
        current_inflow = getattr(upstream, '_inflow', 0.0)

        time_data.append(current_time)
        water_level_data.append(current_water_level)
        inflow_data.append(current_inflow)

    # 恢复原方法
    harness._step_physical_models = original_method

    # 最终状态
    final_state = upstream.get_state()
    final_water_level = final_state.get('water_level', 0.0)
    actual_water_level_change = final_water_level - initial_water_level

    return {
        'time': time_data,
        'water_level': water_level_data,
        'inflow': inflow_data,
        'initial_water_level': initial_water_level,
        'final_water_level': final_water_level,
        'theoretical_water_level_change': theoretical_water_level_change,
        'actual_water_level_change': actual_water_level_change,
        'dt': dt,
        'total_time': total_time,
        'disturbance_start_time': disturbance_start_time,
        'disturbance_duration': disturbance_duration,
        'inflow_delta': inflow_delta,
        'surface_area': surface_area,
        'component_id': disturbed_component_id,
    }


def render_business_flow():
    with st.expander("业务流程图", expanded=True):
        st.markdown("**扰动期间跳过自动入流设置的补丁机制**")
        try:
            from graphviz import Digraph
            g = Digraph("G", format="svg")
            g.attr(rankdir="LR", fontsize="10")

            g.node("Harness", "SimulationHarness", shape="box")
            g.node("Comp", "Upstream_Reservoir", shape="box")
            g.node("Patch", "patched _step_physical_models", shape="component")
            g.node("Flag", "disturbance_active_flag", shape="diamond")

            g.edge("Patch", "Harness", label="monkey patch")
            g.edge("Flag", "Patch", label="active?", style="dashed")
            g.edge("Harness", "Comp", label="step / set_inflow")
            st.graphviz_chart(g)
        except Exception:
            st.info("可选安装 graphviz 以查看流程图：pip install graphviz")


with st.sidebar:
    st.header("配置")
    script_path = st.text_input("脚本路径", value=DEFAULT_SCRIPT_PATH)

    st.subheader("自定义仿真参数")
    disturbed_component_id = st.text_input("组件ID", value="Upstream_Reservoir")
    col1, col2, col3 = st.columns(3)
    with col1:
        dt = st.number_input("dt", value=0.1, step=0.05, min_value=0.01)
    with col2:
        total_time = st.number_input("总时间(s)", value=20.0, step=1.0, min_value=1.0)
    with col3:
        surface_area = st.number_input("表面积(m²)", value=1_000_000.0, step=100_000.0, min_value=1_000.0)

    col4, col5, col6 = st.columns(3)
    with col4:
        disturbance_start = st.number_input("扰动开始(s)", value=5.0, step=0.5, min_value=0.0)
    with col5:
        disturbance_duration = st.number_input("扰动时长(s)", value=10.0, step=0.5, min_value=0.1)
    with col6:
        inflow_delta = st.number_input("入流增量(m³/s)", value=5000.0, step=500.0)


st.title("扰动功能修复演示面板")
render_business_flow()


tab_run, tab_logs, tab_results, tab_docs = st.tabs(["运行", "日志", "结果与下载", "文档"])

if "third_run_logs" not in st.session_state:
    st.session_state.third_run_logs = ""
if "third_run_prints" not in st.session_state:
    st.session_state.third_run_prints = ""
if "third_results" not in st.session_state:
    st.session_state.third_results = {}


with tab_run:
    st.subheader("操作")
    col_a, col_b = st.columns(2)

    # 加载模块
    module: Optional[Any] = None
    api_ok: Dict[str, bool] = {}
    load_error: Optional[str] = None
    with st.spinner("加载脚本模块中..."):
        try:
            module = load_script_module(script_path)
            api_ok = verify_module_api(module)
        except Exception as e:  # noqa: BLE001
            load_error = str(e)

    if load_error:
        st.error(f"脚本加载失败：{load_error}")
        st.stop()

    missing = [k for k, v in api_ok.items() if not v]
    if missing:
        st.error("脚本缺少必要函数：" + ", ".join(missing))
        st.stop()

    with col_a:
        if st.button("运行原脚本 main()", use_container_width=True):
            with st.spinner("运行 main() 中..."):
                _, logs, prints = run_with_captures(module.main)
                st.session_state.third_run_logs += f"\n==== main() 运行日志 ===="\
                                                   f"\n{logs}\n"
                st.session_state.third_run_prints += f"\n==== main() 输出 ===="\
                                                     f"\n{prints}\n"
            st.success("main() 运行完成")

    with col_b:
        if st.button("运行自定义仿真", use_container_width=True):
            with st.spinner("运行自定义仿真中..."):
                def _fn():
                    return run_custom_simulation(
                        module,
                        disturbed_component_id=disturbed_component_id,
                        disturbance_start_time=disturbance_start,
                        disturbance_duration=disturbance_duration,
                        dt=dt,
                        total_time=total_time,
                        inflow_delta=inflow_delta,
                        surface_area=surface_area,
                    )

                res, logs, prints = run_with_captures(_fn)
                st.session_state.third_results["custom"] = res
                st.session_state.third_run_logs += f"\n==== 自定义仿真日志 ===="\
                                                   f"\n{logs}\n"
                st.session_state.third_run_prints += f"\n==== 自定义仿真输出 ===="\
                                                     f"\n{prints}\n"
            st.success("自定义仿真完成")


with tab_logs:
    st.subheader("日志与输出")
    st.caption("捕获 logging 与 stdout")
    c1, c2 = st.columns(2)
    with c1:
        st.text_area("日志(logging)", value=st.session_state.get("third_run_logs", ""), height=360)
    with c2:
        st.text_area("控制台输出(stdout)", value=st.session_state.get("third_run_prints", ""), height=360)
    if st.session_state.get("third_run_logs"):
        st.download_button("下载日志.txt", data=st.session_state["third_run_logs"], file_name="third_logs.txt")
    if st.session_state.get("third_run_prints"):
        st.download_button("下载输出.txt", data=st.session_state["third_run_prints"], file_name="third_prints.txt")


def render_custom_result(res: Dict[str, Any]):
    st.markdown("**自定义仿真结果**")
    m1, m2, m3 = st.columns(3)
    m1.metric("dt", f"{res.get('dt', 0.0):.3f}s")
    m2.metric("总时间", f"{res.get('total_time', 0.0):.1f}s")
    m3.metric("组件", res.get('component_id', '-'))

    m4, m5, m6 = st.columns(3)
    m4.metric("起始水位", f"{res.get('initial_water_level', 0.0):.6f} m")
    m5.metric("最终水位", f"{res.get('final_water_level', 0.0):.6f} m")
    m6.metric("实际变化", f"{res.get('actual_water_level_change', 0.0):.6f} m")

    st.caption("理论变化 = 入流增量 × 扰动时长 ÷ 表面积")
    st.metric("理论变化", f"{res.get('theoretical_water_level_change', 0.0):.6f} m")

    # 曲线
    df = pd.DataFrame({
        'time': res.get('time', []),
        'water_level': res.get('water_level', []),
        'inflow': res.get('inflow', []),
    })
    if not df.empty:
        st.line_chart(df.set_index('time')[['water_level']], height=240)
        st.line_chart(df.set_index('time')[['inflow']], height=240)

    with st.expander("完整结果 JSON", expanded=False):
        st.json(res)


with tab_results:
    st.subheader("结果与下载")
    res_all: Dict[str, Any] = st.session_state.get("third_results", {})

    if not res_all:
        st.info("请先运行原脚本或自定义仿真。")
    else:
        if "custom" in res_all:
            render_custom_result(res_all["custom"])  # type: ignore[arg-type]

        res_json = json.dumps(res_all, ensure_ascii=False, indent=2)
        st.download_button("下载结果.json", data=res_json.encode('utf-8'), file_name="third_results.json", mime="application/json")


with tab_docs:
    st.subheader("脚本文档与说明")
    try:
        module = load_script_module(script_path)
        st.markdown("**模块说明**")
        st.write(inspect.getdoc(module) or "(无模块 docstring)")

        st.markdown("**函数说明**")
        for fn_name in ["load_simulation_harness", "patch_harness_for_disturbance", "main"]:
            if hasattr(module, fn_name):
                fn = getattr(module, fn_name)
                with st.expander(fn_name, expanded=False):
                    st.write(inspect.getdoc(fn) or "(无文档)")
    except Exception as e:  # noqa: BLE001
        st.info(f"无法加载脚本文档：{e}")

with st.expander("使用说明", expanded=False):
    st.markdown(
        "- **脚本路径**：默认指向 `3.test_disturbance_with_harness_fix.py`。\n"
        "- **运行原脚本**：点击“运行原脚本 main()”。\n"
        "- **自定义仿真**：在侧边栏配置参数后点击“运行自定义仿真”。\n"
        "- **结果**：在“结果与下载”页签查看曲线、指标与 JSON 并下载。\n"
        "- **流程图**：如需显示，请安装 `graphviz`（可选）。"
    )


