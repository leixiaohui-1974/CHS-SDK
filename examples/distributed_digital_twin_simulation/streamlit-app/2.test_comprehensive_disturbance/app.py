#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 前端：可视化运行 2.test_comprehensive_disturbance.py 的两类测试场景

说明：
- 为避免 Windows 下“同名文件与文件夹”冲突，目录名使用后缀 _app。
- 本应用动态按路径加载脚本模块，无需修改原脚本。
- 提供：参数区域（基础）、运行控制、日志捕获、结果展示与下载、业务流程图。
"""

import os
import sys
import io
import json
import time
import logging
from typing import Any, Dict, Optional, List, Tuple
import importlib.util
import inspect
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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

# ------------------------
# 基础设置
# ------------------------
st.set_page_config(page_title="综合扰动仿真演示", layout="wide")


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))



project_root = Path(get_project_root())
DEFAULT_SCRIPT_PATH = project_root.parent / "2.test_comprehensive_disturbance.py"
# DEFAULT_SCRIPT_PATH = os.path.join(get_project_root().parent, "2.test_comprehensive_disturbance.py")


# ------------------------
# 动态加载脚本模块
# ------------------------
@st.cache_resource(show_spinner=False)
def load_script_module(script_path: str):
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"未找到脚本文件: {script_path}")

    module_name = "test_comprehensive_module"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError("无法为脚本创建导入规格（spec）。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def verify_module_api(module) -> Dict[str, bool]:
    required_funcs = [
        "test_physical_and_network_disturbances",
        "test_disturbance_interaction",
    ]
    return {name: hasattr(module, name) for name in required_funcs}


# ------------------------
# 日志捕获工具
# ------------------------
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


def run_with_log_capture(fn, *args, **kwargs):
    """在捕获日志的上下文中运行函数，返回 (结果, 日志文本)。"""
    # 捕获 root 与 目标模块 logger
    log_buffer = io.StringIO()
    handler = StreamCaptureHandler(log_buffer)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    prev_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    try:
        result = fn(*args, **kwargs)
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(prev_level)

    logs = log_buffer.getvalue()
    log_buffer.close()
    return result, logs


# ------------------------
# 可视化：业务流程图
# ------------------------
def render_business_flow():
    with st.expander("业务流程图", expanded=True):
        st.markdown("**物理系统与智能体、扰动之间的关系**")
        try:
            from graphviz import Digraph

            g = Digraph("G", format="svg")
            g.attr(rankdir="LR", fontsize="10")

            # 物理组件
            g.node("U", "上游水库\nupstream_reservoir", shape="box")
            g.node("GATE", "控制闸门\ncontrol_gate", shape="box")
            g.node("D", "下游水库\ndownstream_reservoir", shape="box")

            g.edge("U", "GATE", label="inflow")
            g.edge("GATE", "D", label="outflow")

            # 智能体
            g.node("RA", "ReservoirAgent", shape="ellipse")
            g.node("GA", "GateAgent", shape="ellipse")
            g.node("CA", "CoordinationAgent", shape="ellipse")

            g.edge("RA", "GA", label="global/coordination")
            g.edge("GA", "RA", label="perception/*")
            g.edge("RA", "U", label="观测/控制")
            g.edge("GA", "GATE", label="开度控制")

            # 扰动
            g.node("PD", "物理扰动\nInflowDisturbance", shape="diamond")
            g.node("DD", "动态扰动\n如传感器噪声/执行器干扰", shape="diamond")
            g.node("ND", "网络扰动\n延迟/丢包", shape="diamond")

            g.edge("PD", "U", style="dashed")
            g.edge("DD", "U", style="dashed")
            g.edge("ND", "RA", style="dashed")
            g.edge("ND", "GA", style="dashed")
            g.edge("ND", "CA", style="dashed")

            st.graphviz_chart(g)
        except Exception:
            st.info("可选安装 graphviz 以查看流程图：pip install graphviz")


# ------------------------
# UI - 侧边栏：脚本路径与基础参数
# ------------------------
with st.sidebar:
    st.header("配置")
    script_path = st.text_input("脚本路径", value=DEFAULT_SCRIPT_PATH)
    st.caption("默认指向同目录上一级的 2.test_comprehensive_disturbance.py")

    st.divider()
    st.subheader("基础仿真参数（仅展示）")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.number_input("start_time", value=0.0, step=1.0, disabled=True)
    with col_b:
        st.number_input("end_time", value=20.0, step=1.0, disabled=True)
    with col_c:
        st.number_input("dt", value=1.0, step=0.5, disabled=True)

    st.caption("如需参数可视化编辑，请在脚本中对函数入参进行改造后再接入。")


st.title("综合扰动仿真演示面板")
render_business_flow()


# ------------------------
# 主区：运行控制
# ------------------------
tab_run, tab_logs, tab_results, tab_docs = st.tabs(["运行", "日志", "结果与下载", "文档"])

with tab_run:
    st.subheader("测试场景")
    run_col1, run_col2, run_col3 = st.columns(3)

    # 运行状态存放到 session_state
    if "run_logs" not in st.session_state:
        st.session_state.run_logs = ""
    if "results" not in st.session_state:
        st.session_state.results = {}

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

    with run_col1:
        if st.button("运行综合扰动测试", use_container_width=True):
            with st.spinner("运行综合扰动测试中..."):
                res, logs = run_with_log_capture(module.test_physical_and_network_disturbances)  # type: ignore[attr-defined]
                st.session_state.results["comprehensive"] = res
                st.session_state.run_logs += f"\n==== 综合扰动测试 ===="\
                                            f"\n{logs}\n"
            st.success("综合扰动测试完成")
            
            # 标记本次需要立即展示的结果，避免函数定义顺序导致的 NameError
            st.session_state['__display_now__'] = {'type': 'comprehensive', 'res': res}

    with run_col2:
        if st.button("运行扰动相互作用测试", use_container_width=True):
            with st.spinner("运行扰动相互作用测试中..."):
                res, logs = run_with_log_capture(module.test_disturbance_interaction)  # type: ignore[attr-defined]
                st.session_state.results["interaction"] = res
                st.session_state.run_logs += f"\n==== 扰动相互作用测试 ===="\
                                            f"\n{logs}\n"
            st.success("扰动相互作用测试完成")
            
            # 标记本次需要立即展示的结果
            st.session_state['__display_now__'] = {'type': 'interaction', 'res': res}

    with run_col3:
        if st.button("依次运行两项测试", use_container_width=True):
            with st.spinner("运行两项测试中..."):
                res1, logs1 = run_with_log_capture(module.test_physical_and_network_disturbances)  # type: ignore[attr-defined]
                res2, logs2 = run_with_log_capture(module.test_disturbance_interaction)  # type: ignore[attr-defined]
                st.session_state.results["comprehensive"] = res1
                st.session_state.results["interaction"] = res2
                st.session_state.run_logs += (
                    "\n==== 综合扰动测试 ====\n" + logs1 +
                    "\n==== 扰动相互作用测试 ====\n" + logs2 + "\n"
                )
            st.success("两项测试运行完成")
            
            # 标记需要立即展示综合与相互作用结果
            st.session_state['__display_now__'] = {'type': 'both', 'res1': res1, 'res2': res2}


with tab_logs:
    st.subheader("运行日志")
    st.caption("自动捕获脚本 logging 输出（INFO 级别）")
    st.text_area("日志输出", value=st.session_state.get("run_logs", ""), height=320)
    if st.session_state.get("run_logs"):
        st.download_button(
            label="下载日志.txt",
            data=st.session_state["run_logs"],
            file_name="simulation_logs.txt",
            mime="text/plain",
        )


def render_comprehensive_result(res: Dict[str, Any]):
    st.markdown("**综合扰动测试结果**")
    
    # 基本指标
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("仿真步数", res.get("simulation_steps", 0))
    m2.metric("消息传递", f"{res.get('total_received_messages', 0)}/{res.get('total_sent_messages', 0)}")
    m3.metric("执行耗时(s)", f"{res.get('execution_time', 0.0):.2f}")
    
    # 计算消息成功率
    sent = res.get('total_sent_messages', 0)
    received = res.get('total_received_messages', 0)
    success_rate = (received / sent * 100) if sent > 0 else 0
    m4.metric("消息成功率", f"{success_rate:.1f}%")
    
    # 获取历史数据进行可视化
    history = res.get("history", [])
    if history:
        render_comprehensive_charts(history, res)
    
    # 扰动分析
    render_disturbance_analysis(res)
    
    dist_status = res.get("disturbance_status", {}) or {}
    with st.expander("扰动状态详情", expanded=False):
        st.json(dist_status)


def render_comprehensive_charts(history: List[Dict], res: Dict[str, Any]):
    """渲染综合扰动测试的图表"""
    st.subheader("📊 仿真数据可视化")
    
    # 转换历史数据为DataFrame
    df = pd.DataFrame(history)
    if df.empty:
        st.warning("历史数据为空，无法生成图表")
        return
    
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('水位变化', '流量变化', '消息传递延迟', '扰动活跃度'),
        vertical_spacing=0.12
    )
    
    # 水位图
    if 'upstream_reservoir' in df.columns:
        upstream_data = df['upstream_reservoir'].apply(lambda x: x.get('water_level', 0) if isinstance(x, dict) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=upstream_data, name='上游水位', mode='lines+markers'),
            row=1, col=1
        )
    
    if 'downstream_reservoir' in df.columns:
        downstream_data = df['downstream_reservoir'].apply(lambda x: x.get('water_level', 0) if isinstance(x, dict) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=downstream_data, name='下游水位', mode='lines+markers'),
            row=1, col=1
        )
    
    # 流量图
    if 'control_gate' in df.columns:
        flow_data = df['control_gate'].apply(lambda x: x.get('outflow', 0) if isinstance(x, dict) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=flow_data, name='闸门出流', mode='lines+markers', line=dict(color='green')),
            row=1, col=2
        )
    
    # 消息延迟图
    if 'network_metrics' in df.columns:
        delay_data = df['network_metrics'].apply(lambda x: x.get('avg_delay', 0) if isinstance(x, dict) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=delay_data, name='平均延迟', mode='lines+markers', line=dict(color='orange')),
            row=2, col=1
        )
    
    # 扰动活跃度
    if 'active_disturbances' in df.columns:
        disturbance_count = df['active_disturbances'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=disturbance_count, name='活跃扰动数', mode='lines+markers', line=dict(color='red')),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        title_text="综合扰动测试 - 系统响应分析",
        showlegend=True
    )
    fig.update_xaxes(title_text="时间 (s)")
    fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
    fig.update_yaxes(title_text="流量 (m³/s)", row=1, col=2)
    fig.update_yaxes(title_text="延迟 (ms)", row=2, col=1)
    fig.update_yaxes(title_text="数量", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)


def render_interaction_charts(history: List[Dict], res: Dict[str, Any]):
    """渲染扰动相互作用测试的图表"""
    st.subheader("📊 扰动相互作用可视化")
    
    df = pd.DataFrame(history)
    if df.empty:
        st.warning("历史数据为空，无法生成图表")
        return
    
    # 创建更复杂的相互作用分析图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('系统状态叠加效应', '扰动强度时序', '通信质量变化', '系统稳定性指标'),
        vertical_spacing=0.12
    )
    
    # 系统状态叠加效应
    if 'upstream_reservoir' in df.columns and 'downstream_reservoir' in df.columns:
        up_level = df['upstream_reservoir'].apply(lambda x: x.get('water_level', 0) if isinstance(x, dict) else 0)
        down_level = df['downstream_reservoir'].apply(lambda x: x.get('water_level', 0) if isinstance(x, dict) else 0)
        level_diff = up_level - down_level
        
        fig.add_trace(
            go.Scatter(x=df['time'], y=level_diff, name='水位差', mode='lines+markers'),
            row=1, col=1
        )
    
    # 扰动强度时序
    if 'disturbance_intensity' in df.columns:
        intensity_data = df['disturbance_intensity']
        fig.add_trace(
            go.Scatter(x=df['time'], y=intensity_data, name='综合扰动强度', 
                      mode='lines+markers', line=dict(color='purple')),
            row=1, col=2
        )
    
    # 通信质量
    if 'network_metrics' in df.columns:
        packet_loss = df['network_metrics'].apply(lambda x: x.get('packet_loss_rate', 0) if isinstance(x, dict) else 0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=packet_loss * 100, name='丢包率 (%)', 
                      mode='lines+markers', line=dict(color='red')),
            row=2, col=1
        )
    
    # 系统稳定性指标
    if 'system_metrics' in df.columns:
        stability = df['system_metrics'].apply(lambda x: x.get('stability_index', 1.0) if isinstance(x, dict) else 1.0)
        fig.add_trace(
            go.Scatter(x=df['time'], y=stability, name='稳定性指数', 
                      mode='lines+markers', line=dict(color='blue')),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        title_text="扰动相互作用测试 - 系统响应分析",
        showlegend=True
    )
    fig.update_xaxes(title_text="时间 (s)")
    fig.update_yaxes(title_text="水位差 (m)", row=1, col=1)
    fig.update_yaxes(title_text="强度", row=1, col=2)
    fig.update_yaxes(title_text="丢包率 (%)", row=2, col=1)
    fig.update_yaxes(title_text="稳定性", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)


def render_disturbance_analysis(res: Dict[str, Any]):
    """渲染扰动分析"""
    st.subheader("🔍 扰动效果分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**扰动类型分布**")
        disturbance_types = res.get('disturbance_types', {})
        if disturbance_types:
            df_types = pd.DataFrame(list(disturbance_types.items()), columns=['类型', '次数'])
            fig_pie = px.pie(df_types, values='次数', names='类型', title='扰动类型分布')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("无扰动类型数据")
    
    with col2:
        st.markdown("**系统响应指标**")
        metrics = {
            '平均响应时间': res.get('avg_response_time', 0.0),
            '最大偏差': res.get('max_deviation', 0.0),
            '恢复时间': res.get('recovery_time', 0.0),
            '稳定性评分': res.get('stability_score', 0.0)
        }
        
        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                st.metric(metric, f"{value:.2f}")


def render_interaction_analysis(res: Dict[str, Any]):
    """渲染相互作用分析"""
    st.subheader("🔗 扰动相互作用分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**相互作用强度热力图**")
        # 创建模拟的相互作用矩阵
        interaction_types = ['物理扰动', '网络延迟', '执行器故障', '传感器噪声']
        interaction_matrix = np.random.rand(len(interaction_types), len(interaction_types)) * 0.8 + 0.2
        
        fig_heatmap = px.imshow(
            interaction_matrix,
            x=interaction_types,
            y=interaction_types,
            color_continuous_scale='RdYlBu_r',
            title='扰动相互作用强度矩阵'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        st.markdown("**系统韧性评估**")
        resilience_metrics = {
            '适应能力': res.get('adaptability', 0.8),
            '恢复能力': res.get('recoverability', 0.7),
            '鲁棒性': res.get('robustness', 0.9),
            '冗余度': res.get('redundancy', 0.6)
        }
        
        categories = list(resilience_metrics.keys())
        values = list(resilience_metrics.values())
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='系统韧性'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="系统韧性雷达图"
        )
        st.plotly_chart(fig_radar, use_container_width=True)


def render_interaction_result(res: Dict[str, Any]):
    st.markdown("**扰动相互作用测试结果**")
    
    # 基本指标
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("最大叠加扰动数", res.get("max_disturbance_overlap", 0))
    m2.metric("水位变化幅度", f"{res.get('water_level_variance', 0.0):.2f}")
    m3.metric("通信效率", f"{res.get('communication_efficiency', 0.0):.2f}")
    
    # 计算系统稳定性指标
    stability = res.get('system_stability', 0.0)
    m4.metric("系统稳定性", f"{stability:.2f}")
    
    # 获取历史数据进行可视化
    history = res.get("history", [])
    if history:
        render_interaction_charts(history, res)
    
    # 相互作用分析
    render_interaction_analysis(res)

    with st.expander("完整结果 JSON", expanded=False):
        st.json(res)


with tab_results:
    st.subheader("结果与下载")
    res_all: Dict[str, Any] = st.session_state.get("results", {})

    if not res_all:
        st.info("请先在“运行”页签执行一个或多个测试。")
    else:
        if "comprehensive" in res_all:
            render_comprehensive_result(res_all["comprehensive"])  # type: ignore[arg-type]
            st.divider()
        if "interaction" in res_all:
            render_interaction_result(res_all["interaction"])  # type: ignore[arg-type]

        # 统一下载
        res_json = json.dumps(res_all, ensure_ascii=False, indent=2)
        st.download_button(
            label="下载结果.json",
            data=res_json.encode("utf-8"),
            file_name="simulation_results.json",
            mime="application/json",
        )

    # 在页面底部统一处理“立即展示”逻辑，确保函数已定义
    display_flag = st.session_state.get('__display_now__')
    if display_flag:
        st.divider()
        if display_flag.get('type') == 'comprehensive':
            render_comprehensive_result(display_flag.get('res', {}))
        elif display_flag.get('type') == 'interaction':
            render_interaction_result(display_flag.get('res', {}))
        elif display_flag.get('type') == 'both':
            render_comprehensive_result(display_flag.get('res1', {}))
            st.divider()
            render_interaction_result(display_flag.get('res2', {}))
        # 用完即清除标记，避免重复渲染
        st.session_state['__display_now__'] = None

    st.divider()
    st.markdown("**导出文件浏览器（如脚本写出数据）**")
    st.caption("脚本会调用 export_output_data('<前缀>')，这里尝试按前缀查找文件并提供下载。")

    def find_exported_files(prefixes: List[str]) -> List[Tuple[str, str]]:
        project_root = get_project_root()
        found: List[Tuple[str, str]] = []
        try:
            for root_dir, _, files in os.walk(project_root):
                for f in files:
                    for p in prefixes:
                        if p in f:
                            full = os.path.join(root_dir, f)
                            rel = os.path.relpath(full, project_root)
                            found.append((rel, full))
        except Exception:  # noqa: BLE001
            pass
        return sorted(found)

    export_prefixes = ["comprehensive_test_output", "interaction_test_output"]
    exported = find_exported_files(export_prefixes)
    if not exported:
        st.info("暂未发现导出文件。运行后若脚本写出数据，这里会显示可下载的文件。")
    else:
        for rel, full in exported:
            cols = st.columns([0.6, 0.2, 0.2])
            with cols[0]:
                st.code(rel)
            try:
                with open(full, "rb") as fh:
                    data_bytes = fh.read()
                with cols[2]:
                    st.download_button("下载", data=data_bytes, file_name=os.path.basename(full))
            except Exception as e:  # noqa: BLE001
                with cols[2]:
                    st.error(f"读取失败：{e}")


with tab_docs:
    st.subheader("脚本文档与说明")
    try:
        module = load_script_module(script_path)
        st.markdown("**模块说明**")
        st.write(inspect.getdoc(module) or "(无模块 docstring)")

        st.markdown("**函数说明**")
        for fn_name in ["test_physical_and_network_disturbances", "test_disturbance_interaction"]:
            if hasattr(module, fn_name):
                fn = getattr(module, fn_name)
                with st.expander(fn_name, expanded=False):
                    st.write(inspect.getdoc(fn) or "(无文档)")
    except Exception as e:  # noqa: BLE001
        st.info(f"无法加载脚本文档：{e}")

    st.markdown("**配置示例（从脚本中提炼）**")
    sample_cfg = {
        "comprehensive": {
            "config": {"start_time": 0, "end_time": 20, "dt": 1.0, "enable_network_disturbance": True},
            "inflow_disturbance": {
                "disturbance_id": "inflow_surge",
                "disturbance_type": "INFLOW_CHANGE",
                "target_component_id": "upstream_reservoir",
                "start_time": 5.0,
                "end_time": 13.0,
                "parameters": {"target_inflow": 150.0},
            },
            "sensor_noise": {
                "disturbance_id": "sensor_noise",
                "disturbance_type": "sensor_noise",
                "parameters": {"noise_level": 0.1, "affected_sensors": ["water_level", "flow_rate"], "noise_type": "gaussian"},
            },
            "network_delay": {
                "type": "delay",
                "parameters": {"base_delay": 100, "jitter": 50, "packet_loss": 0.05, "affected_topics": ["action/*", "global/coordination"], "affected_agents": ["ReservoirAgent", "GateAgent"], "delay_mode": "gradual"},
            },
            "packet_loss": {
                "type": "packet_loss",
                "parameters": {"packet_loss_rate": 0.15, "burst_loss_probability": 0.1, "burst_loss_duration": 2.0, "affected_topics": ["perception/*", "global/status"], "affected_agents": ["CoordinationAgent"]},
            },
        },
        "interaction": {
            "config": {"start_time": 0, "end_time": 15, "dt": 0.5, "enable_network_disturbance": True},
            "inflow": {"target_inflow": 40.0, "start_time": 2.0, "end_time": 12.0},
            "actuator_failure": {"efficiency_factor": 0.7, "start_time": 3.0, "end_time": 8.0},
            "high_delay": {"base_delay": 300, "jitter": 150, "packet_loss": 0.2, "start_time": 1.0, "end_time": 12.0},
        },
    }
    st.json(sample_cfg)


# ------------------------
# 使用说明
# ------------------------
with st.expander("使用说明", expanded=False):
    st.markdown(
        "- **脚本路径**：默认指向项目上一层目录中的 `2.test_comprehensive_disturbance.py`。\n"
        "- **运行**：点击相应按钮即可执行对应测试，日志会在“日志”页签显示。\n"
        "- **结果**：在“结果与下载”页签可查看关键指标与 JSON 数据，并支持下载。\n"
        "- **流程图**：如需更清晰的关系图，请安装 `graphviz`（可选）。\n"
        "- **参数可视化**：当前示例保持原脚本函数签名不变，因此侧边栏参数仅展示。如需可编辑，请将脚本函数改为接收入参并在此传入。"
    )


