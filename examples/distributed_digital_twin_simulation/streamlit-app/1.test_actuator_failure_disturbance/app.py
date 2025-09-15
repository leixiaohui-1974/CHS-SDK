#!/usr/bin/env python3
"""
Streamlit 可视化页面：执行器故障扰动仿真演示

功能概览：
- 项目根路径配置与核心库动态导入（core_lib.*）
- 加载仿真环境（SimulationBuilder.load）
- 添加三类执行器故障扰动：延迟/部分/完全
- 运行仿真、记录关键时间点、分析组件行为
- 可视化记录（表格/折线图）与关键统计

注意：
- 本页面基于 1.test_actuator_failure_disturbance.py 的业务逻辑进行可视化改造。
- 若当前工作区缺少 core_lib 相关模块，请通过侧边栏设置“项目根路径”，指向包含 core_lib 的工程根目录。
"""



import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import pandas as pd
import numpy as np

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


# ============= 工具函数：动态导入与环境加载 ============= #

def try_import_core_lib(project_root: Optional[str]) -> Tuple[Any, Any, Any, Any, Optional[str]]:
    """尝试动态导入 core_lib 相关模块。

    返回：(SimulationBuilder, DisturbanceConfig, DisturbanceType, create_disturbance, error)
    失败时前四项为 None，第五项为错误信息。
    """
    if project_root:
        project_root = str(Path(project_root).resolve())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

    try:
        from importlib import import_module

        yaml_loader_mod = import_module("core_lib.io.yaml_loader")
        disturbance_mod = import_module("core_lib.disturbances.disturbance_framework")

        SimulationBuilder = getattr(yaml_loader_mod, "SimulationBuilder")
        DisturbanceConfig = getattr(disturbance_mod, "DisturbanceConfig")
        DisturbanceType = getattr(disturbance_mod, "DisturbanceType")
        create_disturbance = getattr(disturbance_mod, "create_disturbance")
        return SimulationBuilder, DisturbanceConfig, DisturbanceType, create_disturbance, None
    except Exception as e:  # noqa: BLE001
        return None, None, None, None, str(e)


def load_harness(SimulationBuilder: Any, scenario_path: str) -> Any:
    """根据场景路径加载仿真环境。"""
    builder = SimulationBuilder(scenario_path=scenario_path)
    harness = builder.load()
    return harness


# ============= SessionState 初始化 ============= #

def ensure_session_state():
    if "project_root" not in st.session_state:
        # 默认：应用所在目录上两级（工作区根目录），用户可在侧栏修改
        st.session_state.project_root = str(Path(__file__).resolve().parents[2])

    if "scenario_path" not in st.session_state:
        # 默认：同上，指向工作区根目录（与原测试脚本相近），用户可修改
        st.session_state.scenario_path = str(Path(__file__).resolve().parents[2])

    if "imports" not in st.session_state:
        st.session_state.imports = {
            "SimulationBuilder": None,
            "DisturbanceConfig": None,
            "DisturbanceType": None,
            "create_disturbance": None,
            "error": "尚未尝试导入",
        }

    if "harness" not in st.session_state:
        st.session_state.harness = None

    if "disturbances" not in st.session_state:
        st.session_state.disturbances = []  # type: List[Dict[str, Any]]

    if "recorded_states" not in st.session_state:
        st.session_state.recorded_states = {}  # time -> dict

    if "component_behaviors" not in st.session_state:
        st.session_state.component_behaviors = []


# ============= 业务逻辑复用：组件行为分析 ============= #

def analyze_component_behavior(component: Any, component_id: str, time_value: float) -> Dict[str, Any]:
    """分析组件行为，获取关键状态数据"""
    state = component.get_state()
    
    # 获取入流数据 - 优先从状态，再从属性
    inflow_value = state.get("inflow", 0.0)
    if inflow_value == 0.0 and hasattr(component, "_inflow"):
        inflow_value = getattr(component, "_inflow", 0.0)
    
    # 获取出流数据 - 优先从状态，再从属性
    outflow_value = state.get("outflow", 0.0)
    if outflow_value == 0.0 and hasattr(component, "_outflow"):
        outflow_value = getattr(component, "_outflow", 0.0)
    
    behavior: Dict[str, Any] = {
        "时间": time_value,
        "组件ID": component_id,
        "水位": state.get("water_level", 0.0),
        "库容": state.get("volume", 0.0),
        "入流": inflow_value,
        "出流": outflow_value,
    }
    
    # 添加更多状态信息
    if hasattr(component, "_efficiency"):
        behavior["效率"] = getattr(component, "_efficiency")
    if hasattr(component, "_actuator_status"):
        behavior["执行器状态"] = getattr(component, "_actuator_status")
    if "opening" in state:
        behavior["开度"] = state["opening"]
    
    # 调试信息 - 打印组件状态
    print(f"[调试] 时间={time_value:.1f}s, 组件={component_id}")
    print(f"  状态字典: {state}")
    print(f"  _inflow属性: {getattr(component, '_inflow', '无')}")
    print(f"  最终入流: {inflow_value}, 最终出流: {outflow_value}")
    
    return behavior


# ============= UI 构建 ============= #

def sidebar_controls():
    st.sidebar.header("全局设置")

    project_root = st.sidebar.text_input(
        "项目根路径（包含 core_lib 的工程根目录）",
        value=st.session_state.project_root,
    )

    cols = st.sidebar.columns([1, 1])
    with cols[0]:
        if st.button("应用项目根路径并导入库", use_container_width=True):
            st.session_state.project_root = project_root
            SimB, DC, DT, CR, err = try_import_core_lib(project_root)
            st.session_state.imports = {
                "SimulationBuilder": SimB,
                "DisturbanceConfig": DC,
                "DisturbanceType": DT,
                "create_disturbance": CR,
                "error": err,
            }

    scenario_path = st.sidebar.text_input(
        "场景目录（传给 SimulationBuilder 的 scenario_path）",
        value=st.session_state.scenario_path,
    )

    with cols[1]:
        if st.button("加载仿真环境", use_container_width=True):
            st.session_state.scenario_path = scenario_path
            SimB = st.session_state.imports.get("SimulationBuilder")
            if SimB is None:
                st.warning("请先成功导入 core_lib（点击左侧按钮）")
            else:
                try:
                    st.session_state.harness = load_harness(SimB, scenario_path)
                    st.success("仿真环境加载成功")
                except Exception as e:  # noqa: BLE001
                    st.session_state.harness = None
                    st.error(f"仿真环境加载失败：{e}")

    # 导入状态提示
    imp_err = st.session_state.imports.get("error")
    if imp_err:
        if imp_err == "尚未尝试导入":
            st.sidebar.info("请先设置项目根路径并点击导入库。")
        elif st.session_state.imports.get("SimulationBuilder") is None:
            st.sidebar.error(f"导入失败：{imp_err}")
        else:
            st.sidebar.success("core_lib 导入成功")


def disturbance_form():
    st.header("扰动配置")
    st.caption("在这里添加三种执行器故障扰动，随后在‘运行与结果’中执行仿真。")

    default_upstream = "Upstream_Reservoir"
    default_downstream = "Downstream_Reservoir"

    with st.expander("延迟故障（控制信号延迟生效）", expanded=True):
        st.text_input("扰动 ID", value="gate_delay_failure", key="delay_id")
        st.text_input("目标组件 ID", value=default_upstream, key="delay_target")
        st.text_input("目标执行器", value="outlet_gate", key="delay_actuator")
        c1, c2, c3 = st.columns(3)
        c1.number_input("开始时间 s", value=5.0, key="delay_start")
        c2.number_input("结束时间 s", value=15.0, key="delay_end")
        c3.number_input("延迟时间 s", value=3.0, key="delay_delay")
        st.slider("强度", 0.0, 2.0, 1.0, 0.1, key="delay_intensity")
        st.text_input("描述", value="测试闸门延迟故障：控制信号延迟3秒生效", key="delay_desc")
        if st.button("添加延迟故障", key="add_delay"):
            st.session_state.disturbances.append({
                "disturbance_id": st.session_state.delay_id,
                "disturbance_type": "ACTUATOR_FAILURE",
                "target_component_id": st.session_state.delay_target,
                "start_time": float(st.session_state.delay_start),
                "end_time": float(st.session_state.delay_end),
                "intensity": float(st.session_state.delay_intensity),
                "parameters": {
                    "failure_type": "delay",
                    "delay_time": float(st.session_state.delay_delay),
                    "target_actuator": st.session_state.delay_actuator,
                },
                "description": st.session_state.delay_desc,
            })
            st.success("已添加：延迟故障")

    with st.expander("部分故障（执行器效率下降）", expanded=True):
        st.text_input("扰动 ID", value="pump_efficiency_failure", key="partial_id")
        st.text_input("目标组件 ID", value=default_downstream, key="partial_target")
        st.text_input("目标执行器", value="main_pump", key="partial_actuator")
        c1, c2, c3 = st.columns(3)
        c1.number_input("开始时间 s", value=8.0, key="partial_start")
        c2.number_input("结束时间 s", value=18.0, key="partial_end")
        c3.number_input("效率因子 (0-1)", value=0.6, min_value=0.0, max_value=1.0, step=0.05, key="partial_eff")
        st.slider("强度", 0.0, 2.0, 0.6, 0.1, key="partial_intensity")
        st.text_input("描述", value="测试泵站效率故障：效率降至60%", key="partial_desc")
        if st.button("添加部分故障", key="add_partial"):
            st.session_state.disturbances.append({
                "disturbance_id": st.session_state.partial_id,
                "disturbance_type": "ACTUATOR_FAILURE",
                "target_component_id": st.session_state.partial_target,
                "start_time": float(st.session_state.partial_start),
                "end_time": float(st.session_state.partial_end),
                "intensity": float(st.session_state.partial_intensity),
                "parameters": {
                    "failure_type": "partial",
                    "efficiency_factor": float(st.session_state.partial_eff),
                    "target_actuator": st.session_state.partial_actuator,
                },
                "description": st.session_state.partial_desc,
            })
            st.success("已添加：部分故障")

    with st.expander("完全故障（执行器无响应）", expanded=True):
        st.text_input("扰动 ID", value="valve_complete_failure", key="complete_id")
        st.text_input("目标组件 ID", value=default_upstream, key="complete_target")
        st.text_input("目标执行器", value="control_valve", key="complete_actuator")
        c1, c2 = st.columns(2)
        c1.number_input("开始时间 s", value=12.0, key="complete_start")
        c2.number_input("结束时间 s", value=20.0, key="complete_end")
        st.slider("强度", 0.0, 2.0, 1.0, 0.1, key="complete_intensity")
        st.text_input("描述", value="测试控制阀完全故障：无响应", key="complete_desc")
        if st.button("添加完全故障", key="add_complete"):
            st.session_state.disturbances.append({
                "disturbance_id": st.session_state.complete_id,
                "disturbance_type": "ACTUATOR_FAILURE",
                "target_component_id": st.session_state.complete_target,
                "start_time": float(st.session_state.complete_start),
                "end_time": float(st.session_state.complete_end),
                "intensity": float(st.session_state.complete_intensity),
                "parameters": {
                    "failure_type": "complete",
                    "target_actuator": st.session_state.complete_actuator,
                },
                "description": st.session_state.complete_desc,
            })
            st.success("已添加：完全故障")

    if st.session_state.disturbances:
        st.subheader("已添加的扰动")
        df = pd.DataFrame(st.session_state.disturbances)
        st.dataframe(df, use_container_width=True)
        if st.button("清空已添加扰动"):
            st.session_state.disturbances = []
            st.info("已清空扰动列表")


def run_and_visualize():
    st.header("运行与结果")
    harness = st.session_state.harness
    if harness is None:
        st.warning("请先加载仿真环境")
        return

    key_times_default = [4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 21.0]
    key_times_str = st.text_input(
        "关键时间点（秒，逗号分隔）",
        value=", ".join(str(x) for x in key_times_default),
    )
    try:
        key_times = [float(x.strip()) for x in key_times_str.split(",") if x.strip()]
    except Exception:  # noqa: BLE001
        st.warning("关键时间点解析失败，已回退到默认值")
        key_times = key_times_default

    imp = st.session_state.imports
    DisturbanceConfig = imp.get("DisturbanceConfig")
    DisturbanceType = imp.get("DisturbanceType")
    create_disturbance = imp.get("create_disturbance")

    if DisturbanceConfig is None or DisturbanceType is None or create_disturbance is None:
        st.error("core_lib 相关类型未就绪，请在侧边栏先导入库。")
        return

    # 注入扰动
    for cfg in st.session_state.disturbances:
        try:
            cfg_obj = DisturbanceConfig(
                disturbance_id=cfg["disturbance_id"],
                disturbance_type=getattr(DisturbanceType, cfg.get("disturbance_type", "ACTUATOR_FAILURE")),
                target_component_id=cfg["target_component_id"],
                start_time=float(cfg["start_time"]),
                end_time=float(cfg["end_time"]),
                intensity=float(cfg.get("intensity", 1.0)),
                parameters=cfg.get("parameters", {}),
                description=cfg.get("description", ""),
            )
            disturbance = create_disturbance(cfg_obj)
            harness.add_disturbance(disturbance)
        except Exception as e:  # noqa: BLE001
            st.warning(f"扰动 {cfg.get('disturbance_id')} 添加失败：{e}")

    run_col1, run_col2, run_col3 = st.columns([1, 1, 1])
    fast_mode = run_col2.toggle("快速运行（减少 UI 刷新）", value=True)
    run_clicked = run_col1.button("开始运行仿真", use_container_width=True)
    reset_clicked = run_col3.button("重置记录", use_container_width=True)

    if reset_clicked:
        st.session_state.recorded_states = {}
        st.session_state.component_behaviors = []
        st.info("已清空运行记录")

    if not run_clicked:
        return

    recorded_states: Dict[float, Dict[str, Any]] = {}
    component_behaviors: List[Dict[str, Any]] = []

    # 动态检测系统中的组件
    available_components = list(harness.components.keys())
    st.info(f"可用组件：{available_components}")
    
    # 尝试多种可能的组件ID
    possible_upstream_ids = ["Upstream_Reservoir", "upstream_reservoir", "reservoir_1", "R1"]
    possible_downstream_ids = ["Downstream_Reservoir", "downstream_reservoir", "reservoir_2", "R2"]
    
    upstream_id = None
    downstream_id = None
    
    # 查找上游组件
    for uid in possible_upstream_ids:
        if uid in harness.components:
            upstream_id = uid
            break
    
    # 查找下游组件
    for did in possible_downstream_ids:
        if did in harness.components:
            downstream_id = did
            break
    
    # 如果找不到预设ID，使用前两个组件
    if upstream_id is None and len(available_components) > 0:
        upstream_id = available_components[0]
    if downstream_id is None and len(available_components) > 1:
        downstream_id = available_components[1]
    elif downstream_id is None and len(available_components) > 0:
        downstream_id = available_components[0]  # 如果只有一个组件，同时作为上下游
    
    st.info(f"使用的组件：上游={upstream_id}, 下游={downstream_id}")
    
    upstream_component = harness.components.get(upstream_id) if upstream_id else None
    downstream_component = harness.components.get(downstream_id) if downstream_id else None

    progress = st.progress(0)
    last_update = time.time()
    max_steps = 2_000_000
    steps = 0

    # 构建仿真环境
    harness.build()
    
    # 添加调试信息
    st.info(f"仿真配置：开始时间={harness.start_time}s, 结束时间={harness.end_time}s, 时间步长={harness.dt}s")
    st.info(f"系统组件：{list(harness.components.keys())}")
    
    # 为上游水库设置初始入流，确保系统有水流动
    if upstream_component is not None:
        initial_inflow = 10.0  # 设置10 m³/s的初始入流
        upstream_component.set_inflow(initial_inflow)
        st.info(f"已为上游水库设置初始入流：{initial_inflow} m³/s")
        
        # 检查初始状态
        initial_state = upstream_component.get_state()
        st.write(f"上游水库初始状态：{initial_state}")
    
    if downstream_component is not None:
        initial_state = downstream_component.get_state()
        st.write(f"下游水库初始状态：{initial_state}")
    
    try:
        while getattr(harness, "t", 0.0) < getattr(harness, "end_time", 0.0):
            t_now = float(getattr(harness, "t", 0.0))
            
            # 持续为上游组件设置入流，确保系统有持续的水流
            if upstream_component is not None and steps % 10 == 0:  # 每10步设置一次
                continuous_inflow = 10.0 + 5.0 * np.sin(t_now * 0.1)  # 变化的入流
                upstream_component.set_inflow(continuous_inflow)
            
            # 记录所有时间点的数据，不只是关键时间点
            if steps % 50 == 0 or any(abs(t_now - kt) < harness.dt for kt in key_times):
                active_disturbances = harness.get_active_disturbances()

                upstream_behavior = None
                if upstream_component is not None:
                    upstream_behavior = analyze_component_behavior(upstream_component, upstream_id, t_now)
                    component_behaviors.append(upstream_behavior)

                downstream_behavior = None
                if downstream_component is not None:
                    downstream_behavior = analyze_component_behavior(downstream_component, downstream_id, t_now)
                    component_behaviors.append(downstream_behavior)

                recorded_states[t_now] = {
                    "active_disturbances": active_disturbances,
                    "upstream": upstream_behavior,
                    "downstream": downstream_behavior,
                }

            if not fast_mode and (time.time() - last_update) > 0.1:
                et = float(getattr(harness, "end_time", 1.0) or 1.0)
                progress.progress(min(1.0, t_now / et))
                last_update = time.time()

            harness.step()
            steps += 1
            if steps >= max_steps:
                st.warning("达到最大步数保护上限，已提前停止。")
                break

        progress.progress(1.0)
        st.success(f"仿真完成！共执行 {steps} 步，记录了 {len(recorded_states)} 个时间点的数据")
    except Exception as e:  # noqa: BLE001
        st.error(f"运行中断：{e}")
        import traceback
        st.error(f"详细错误信息：{traceback.format_exc()}")

    st.session_state.recorded_states = recorded_states
    st.session_state.component_behaviors = component_behaviors

    st.subheader("结果概览")

    try:
        disturbance_history = harness.get_disturbance_history()
        st.write(f"扰动历史记录总数：{len(disturbance_history)}")
    except Exception:
        disturbance_history = []
        st.info("当前 harness 未提供扰动历史接口或无记录。")

    def count_by_effect(disturbance_id: Optional[str]) -> int:
        if not disturbance_id:
            return 0
        count = 0
        for r in disturbance_history:
            effects = r.get("effects") or {}
            if disturbance_id in effects:
                count += 1
        return count

    # 通过 failure_type 推断三个 ID（若已添加）
    delay_id = next((d["disturbance_id"] for d in st.session_state.disturbances if d["parameters"].get("failure_type") == "delay"), None)
    partial_id = next((d["disturbance_id"] for d in st.session_state.disturbances if d["parameters"].get("failure_type") == "partial"), None)
    complete_id = next((d["disturbance_id"] for d in st.session_state.disturbances if d["parameters"].get("failure_type") == "complete"), None)

    st.write(
        f"延迟故障记录数：{count_by_effect(delay_id)} | "
        f"部分故障记录数：{count_by_effect(partial_id)} | "
        f"完全故障记录数：{count_by_effect(complete_id)}"
    )

    post_times = [t for t in st.session_state.recorded_states.keys() if t > 20.0]
    if post_times:
        recovery_time = min(post_times)
        st.write(f"故障恢复后首个记录时间：{recovery_time:.1f}s")

    upstream_behaviors = [b for b in st.session_state.component_behaviors if b and b.get("组件ID") == upstream_id]
    if len(upstream_behaviors) >= 2:
        initial, final = upstream_behaviors[0], upstream_behaviors[-1]
        water_level_change_mm = (final["水位"] - initial["水位"]) * 1000.0
        volume_change = final["库容"] - initial["库容"]
        st.write(
            f"上游水位变化：{water_level_change_mm:.3f} mm | 体积变化：{volume_change:.1f} m³ | "
            f"初始入流：{initial['入流']:.1f} m³/s → 最终入流：{final['入流']:.1f} m³/s"
        )

    st.subheader("时间点记录明细")
    if st.session_state.recorded_states:
        rows = []
        for t, rec in sorted(st.session_state.recorded_states.items(), key=lambda x: x[0]):
            up = rec.get("upstream") or {}
            dn = rec.get("downstream") or {}
            rows.append({
                "时间": t,
                "活跃扰动数": len(rec.get("active_disturbances", [])),
                "上游水位": up.get("水位"),
                "上游入流": up.get("入流"),
                "上游出流": up.get("出流"),
                "下游水位": dn.get("水位"),
                "下游入流": dn.get("入流"),
                "下游出流": dn.get("出流"),
            })
        
        if not rows:
            st.warning("没有收集到有效数据，请检查组件ID是否正确")
            return
            
        df = pd.DataFrame(rows)
        
        # 过滤掉全为None或NaN的列
        df_clean = df.dropna(axis=1, how='all')
        numeric_cols = df_clean.select_dtypes(include=[float, int]).columns
        
        st.write(f"数据概览：共 {len(df)} 行记录，{len(numeric_cols)} 个数值列")
        st.dataframe(df_clean, use_container_width=True)

        # 使用plotly创建更好的图表
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        if len(df) > 1:  # 确保有足够数据绘图
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('水位变化', '入流变化', '出流变化', '扰动活跃度'),
                vertical_spacing=0.12
            )
            
            # 水位图
            water_level_cols = [c for c in df.columns if '水位' in c and df[c].notna().any()]
            for col in water_level_cols:
                fig.add_trace(
                    go.Scatter(x=df['时间'], y=df[col], name=col, mode='lines+markers'),
                    row=1, col=1
                )
            
            # 入流图
            inflow_cols = [c for c in df.columns if '入流' in c and df[c].notna().any()]
            for col in inflow_cols:
                fig.add_trace(
                    go.Scatter(x=df['时间'], y=df[col], name=col, mode='lines+markers'),
                    row=1, col=2
                )
            
            # 出流图
            outflow_cols = [c for c in df.columns if '出流' in c and df[c].notna().any()]
            for col in outflow_cols:
                fig.add_trace(
                    go.Scatter(x=df['时间'], y=df[col], name=col, mode='lines+markers'),
                    row=2, col=1
                )
            
            # 扰动活跃度
            fig.add_trace(
                go.Scatter(x=df['时间'], y=df['活跃扰动数'], name='活跃扰动数', 
                          mode='lines+markers', line=dict(color='red')),
                row=2, col=2
            )
            
            fig.update_layout(
                height=800,
                title_text="执行器故障扰动仿真结果",
                showlegend=True
            )
            fig.update_xaxes(title_text="时间 (s)")
            fig.update_yaxes(title_text="水位 (m)", row=1, col=1)
            fig.update_yaxes(title_text="流量 (m³/s)", row=1, col=2)
            fig.update_yaxes(title_text="流量 (m³/s)", row=2, col=1)
            fig.update_yaxes(title_text="数量", row=2, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 简化的streamlit图表作为备选
        chart_cols = st.columns(2)
        with chart_cols[0]:
            water_cols = [c for c in df.columns if '水位' in c and df[c].notna().any()]
            if water_cols:
                st.subheader("水位变化")
                st.line_chart(df.set_index("时间")[water_cols])
        
        with chart_cols[1]:
            flow_cols = [c for c in df.columns if ('入流' in c or '出流' in c) and df[c].notna().any()]
            if flow_cols:
                st.subheader("流量变化")
                st.line_chart(df.set_index("时间")[flow_cols])
    else:
        st.info("尚无记录，请先运行仿真。")


def main():
    st.set_page_config(page_title="执行器故障扰动仿真", layout="wide")
    st.title("执行器故障扰动仿真演示")
    st.caption("基于测试脚本的业务逻辑，提供零代码的可视化交互界面。")

    ensure_session_state()
    sidebar_controls()

    tabs = st.tabs(["扰动配置", "运行与结果"])  # 两页完成全部流程
    with tabs[0]:
        disturbance_form()
    with tabs[1]:
        run_and_visualize()


if __name__ == "__main__":
    main()


