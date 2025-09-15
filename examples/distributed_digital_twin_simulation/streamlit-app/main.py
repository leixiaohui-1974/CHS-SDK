import streamlit as st
from streamlit_option_menu import option_menu
import subprocess
import sys
import os

# 子应用路径映射
apps = {
    "1. Actuator Failure Disturbance": "1.test_actuator_failure_disturbance/app.py",
    "2. Comprehensive Disturbance": "2.test_comprehensive_disturbance/app.py",
    "3. Disturbance with Harness Fix": "3.test_disturbance_with_harness_fix/app.py",
    "4. Inflow Disturbance": "4.test_inflow_disturbance/app.py",
    "5. Inflow Fix": "5.test_inflow_fix/app.py",
    "6. Integrated Disturbance Framework": "6.test_integrated_disturbance_framework/app.py",
    "7. Multiple Disturbance Types": "7.test_multiple_disturbance_types/app.py",
    "8. Network Disturbance": "8.test_network_disturbance/app.py",
    "9. Simple Inflow Disturbance": "9.test_simple_inflow_disturbance/app.py",
    "10. Strong Inflow Disturbance": "10.test_strong_inflow_disturbance/app.py",
    "11. Water Level Calculation": "11.test_water_level_calculation/app.py",
}

st.set_page_config(page_title="Main Control Panel", layout="centered")

st.title("📌 Disturbance Test Main Panel")

# 左侧菜单选择
choice = option_menu(
    "选择子应用",
    list(apps.keys()),
    icons=["app-indicator"] * len(apps),
    menu_icon="cast",
    default_index=0,
    orientation="vertical",
)

st.write(f"👉 当前选择的是：**{choice}**")

# 初始化 session_state 存储进程
if "running_apps" not in st.session_state:
    st.session_state.running_apps = {}
if "next_port" not in st.session_state:
    st.session_state.next_port = 8502  # 主应用一般占 8501，从 8502 开始分配

if st.button("启动该子应用 🚀"):
    script_path = apps[choice]
    python_exec = sys.executable

    if choice in st.session_state.running_apps:
        # 已经启动 → 给出链接
        port = st.session_state.running_apps[choice]["port"]
        url = f"http://localhost:{port}"
        st.info(f"🌐 子应用 `{choice}` 已经在运行，点击这里打开：[{url}]({url})")
    else:
        # 分配端口并启动
        port = st.session_state.next_port
        st.session_state.next_port += 1

        st.write(f"正在启动：`{script_path}` (端口 {port})")
        proc = subprocess.Popen([python_exec, "-m", "streamlit", "run", script_path, "--server.port", str(port)])
        st.session_state.running_apps[choice] = {"proc": proc, "port": port}

        url = f"http://localhost:{port}"
        st.success(f"✅ 子应用 `{choice}` 已启动 (PID={proc.pid})")
        st.markdown(f"👉 点击打开：[进入 {choice}]({url})")



# import streamlit as st
# from streamlit_option_menu import option_menu
# import subprocess
# import sys
# import os
#
# # 子应用路径映射
# apps = {
#     "1. Actuator Failure Disturbance": "1.test_actuator_failure_disturbance/app.py",
#     "2. Comprehensive Disturbance": "2.test_comprehensive_disturbance/app.py",
#     "3. Disturbance with Harness Fix": "3.test_disturbance_with_harness_fix/app.py",
#     "4. Inflow Disturbance": "4.test_inflow_disturbance/app.py",
#     "5. Inflow Fix": "5.test_inflow_fix/app.py",
#     "6. Integrated Disturbance Framework": "6.test_integrated_disturbance_framework/app.py",
#     "7. Multiple Disturbance Types": "7.test_multiple_disturbance_types/app.py",
#     "8. Network Disturbance": "8.test_network_disturbance/app.py",
#     "9. Simple Inflow Disturbance": "9.test_simple_inflow_disturbance/app.py",
#     "10. Strong Inflow Disturbance": "10.test_strong_inflow_disturbance/app.py",
#     "11. Water Level Calculation": "11.test_water_level_calculation/app.py",
# }
#
# st.set_page_config(page_title="Main Control Panel", layout="centered")
#
# st.title("📌 Disturbance Test Main Panel")
#
# # 左侧菜单选择
# choice = option_menu(
#     "选择子应用",
#     list(apps.keys()),
#     icons=["app-indicator"] * len(apps),
#     menu_icon="cast",
#     default_index=0,
#     orientation="vertical",
# )
#
# st.write(f"👉 当前选择的是：**{choice}**")
#
# # 初始化 session_state 存储进程
# if "running_apps" not in st.session_state:
#     st.session_state.running_apps = {}
#
# if st.button("启动该子应用 🚀"):
#     script_path = apps[choice]
#     python_exec = sys.executable
#
#     if choice in st.session_state.running_apps:
#         st.warning(f"⚠️ 子应用 `{choice}` 已经在运行！")
#     else:
#         st.write(f"正在启动：`{script_path}`")
#         proc = subprocess.Popen([python_exec, "-m", "streamlit", "run", script_path])
#         st.session_state.running_apps[choice] = proc
#         st.success(f"✅ 子应用 `{choice}` 已启动 (PID={proc.pid})")
#
#
#
# # import streamlit as st
# # from streamlit_option_menu import option_menu
# # import subprocess
# # import sys
# # import os
# #
# # # 子应用路径映射
# # apps = {
# #     "1. Actuator Failure Disturbance": "1.test_actuator_failure_disturbance/app.py",
# #     "2. Comprehensive Disturbance": "2.test_comprehensive_disturbance/app.py",
# #     "3. Disturbance with Harness Fix": "3.test_disturbance_with_harness_fix/app.py",
# #     "4. Inflow Disturbance": "4.test_inflow_disturbance/app.py",
# #     "5. Inflow Fix": "5.test_inflow_fix/app.py",
# #     "6. Integrated Disturbance Framework": "6.test_integrated_disturbance_framework/app.py",
# #     "7. Multiple Disturbance Types": "7.test_multiple_disturbance_types/app.py",
# #     "8. Network Disturbance": "8.test_network_disturbance/app.py",
# #     "9. Simple Inflow Disturbance": "9.test_simple_inflow_disturbance/app.py",
# #     "10. Strong Inflow Disturbance": "10.test_strong_inflow_disturbance/app.py",
# #     "11. Water Level Calculation": "11.test_water_level_calculation/app.py",
# # }
# #
# # st.set_page_config(page_title="Main Control Panel", layout="centered")
# #
# # st.title("📌 Disturbance Test Main Panel")
# #
# # # 左侧菜单选择
# # choice = option_menu(
# #     "选择子应用",
# #     list(apps.keys()),
# #     icons=["app-indicator"] * len(apps),
# #     menu_icon="cast",
# #     default_index=0,
# #     orientation="vertical",
# # )
# #
# # st.write(f"👉 当前选择的是：**{choice}**")
# #
# # if st.button("启动该子应用 🚀"):
# #     script_path = apps[choice]
# #     python_exec = sys.executable
# #     st.write(f"正在启动：`{script_path}`")
# #     subprocess.Popen([python_exec, "-m", "streamlit", "run", script_path])
# #
# #
# #
# #
# # # import streamlit as st
# # # import importlib.util
# # # import os
# # #
# # # st.set_page_config(
# # #     page_title="Disturbance Test Main Panel",
# # #     page_icon="🌊",
# # #     layout="centered"
# # # )
# # #
# # # st.title("🌊 Disturbance Test Main Panel")
# # #
# # # # 定义子应用路径
# # # apps = {
# # #     "1. Actuator Failure Disturbance": "1.test_actuator_failure_disturbance/app.py",
# # #     "2. Comprehensive Disturbance": "2.test_comprehensive_disturbance/app.py",
# # #     "3. Disturbance with Harness Fix": "3.test_disturbance_with_harness_fix/app.py",
# # #     "4. Inflow Disturbance": "4.test_inflow_disturbance/app.py",
# # #     "5. Inflow Fix": "5.test_inflow_fix/app.py",
# # #     "6. Integrated Disturbance Framework": "6.test_integrated_disturbance_framework/app.py",
# # #     "7. Multiple Disturbance Types": "7.test_multiple_disturbance_types/app.py",
# # #     "8. Network Disturbance": "8.test_network_disturbance/app.py",
# # #     "9. Simple Inflow Disturbance": "9.test_simple_inflow_disturbance/app.py",
# # #     "10. Strong Inflow Disturbance": "10.test_strong_inflow_disturbance/app.py",
# # #     "11. Water Level Calculation": "11.test_water_level_calculation/app.py",
# # # }
# # #
# # # # 选择子页面
# # # choice = st.sidebar.selectbox("选择子应用", list(apps.keys()))
# # #
# # # st.write(f"👉 当前页面：**{choice}**")
# # #
# # # # 动态导入对应的 app.py
# # # script_path = apps[choice]
# # # module_name = os.path.splitext(os.path.basename(script_path))[0]
# # #
# # # spec = importlib.util.spec_from_file_location(module_name, script_path)
# # # module = importlib.util.module_from_spec(spec)
# # # spec.loader.exec_module(module)
