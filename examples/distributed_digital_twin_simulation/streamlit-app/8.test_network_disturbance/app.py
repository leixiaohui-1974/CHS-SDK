#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络扰动测试 - Streamlit界面

这个应用提供了一个直观的界面来测试和可视化网络扰动对分布式系统通信的影响：
1. 网络延迟扰动：模拟网络延迟、抖动等问题
2. 数据包丢失扰动：模拟网络丢包、突发丢失等情况
3. 组合扰动测试：同时应用多种网络扰动观察交互效果
4. 多代理通信监控：实时监控代理间的消息传递状况
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
import yaml
import json

import sys
from pathlib import Path

# 当前脚本所在目录
CURRENT_DIR = Path(__file__).resolve().parent
# 项目根目录 (E:\CHS-SDK)
PROJECT_ROOT = CURRENT_DIR.parents[2]   # 回到 E:\CHS-SDK
# 配置文件目录 (父目录的父目录，即与原脚本同级)
CONFIG_DIR = CURRENT_DIR.parent.parent

# 添加 core_lib 到 sys.path
sys.path.append(str(PROJECT_ROOT / "core_lib"))


# 配置页面
st.set_page_config(
    page_title="网络扰动测试系统",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 尝试导入核心模块（常规 + 动态兜底）
NETWORK_LIB_AVAILABLE = False
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from enhanced_message_bus import EnhancedMessageBus
    from network_disturbance import NetworkDisturbanceManager, NetworkDelayDisturbance, PacketLossDisturbance
    NETWORK_LIB_AVAILABLE = True
except ImportError:
    # 动态按路径导入兜底
    try:
        import importlib.util
        examples_dir = Path(__file__).resolve().parent.parent.parent  # distributed_digital_twin_simulation
        emb_path = examples_dir / 'enhanced_message_bus.py'
        ndm_path = examples_dir / 'network_disturbance.py'

        if emb_path.exists():
            spec_emb = importlib.util.spec_from_file_location('enhanced_message_bus', str(emb_path))
            mod_emb = importlib.util.module_from_spec(spec_emb)
            assert spec_emb and spec_emb.loader
            spec_emb.loader.exec_module(mod_emb)
            EnhancedMessageBus = getattr(mod_emb, 'EnhancedMessageBus')

        if ndm_path.exists():
            spec_ndm = importlib.util.spec_from_file_location('network_disturbance', str(ndm_path))
            mod_ndm = importlib.util.module_from_spec(spec_ndm)
            assert spec_ndm and spec_ndm.loader
            spec_ndm.loader.exec_module(mod_ndm)
            NetworkDisturbanceManager = getattr(mod_ndm, 'NetworkDisturbanceManager')
            NetworkDelayDisturbance = getattr(mod_ndm, 'NetworkDelayDisturbance')
            PacketLossDisturbance = getattr(mod_ndm, 'PacketLossDisturbance')

        # 若两者均就绪则启用真实模式
        if 'EnhancedMessageBus' in globals() and 'NetworkDisturbanceManager' in globals():
            NETWORK_LIB_AVAILABLE = True
            st.success('✅ 已通过路径加载网络扰动模块（真实模式）')
        else:
            st.warning('⚠️ 未找到网络扰动模块文件，继续使用模拟模式')
    except Exception as _e:
        st.warning(f"⚠️ 动态加载网络扰动模块失败：{_e}，继续使用模拟模式")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config_file():
    """从配置文件加载网络扰动参数"""
    config_files = [
        CONFIG_DIR / "network_disturbance_config.yaml",
        CONFIG_DIR / "network_disturbance_config.yml", 
        CURRENT_DIR / "network_disturbance_config.yaml",
        CURRENT_DIR / "network_disturbance_config.yml"
    ]
    
    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"成功从 {config_file} 加载配置文件")
                return config, str(config_file)
            except Exception as e:
                logger.warning(f"加载配置文件 {config_file} 失败: {e}")
                continue
    
    # 如果没有找到配置文件，返回默认配置
    logger.info("未找到配置文件，使用默认配置")
    return get_default_config(), "默认配置"

def get_default_config():
    """获取默认配置"""
    return {
        'test_environment': {
            'agent_count': 4,
            'message_count': 50,
            'message_interval': 0.2
        },
        'network_delay': {
            'enabled': True,
            'base_delay': 200,
            'jitter': 100,
            'packet_loss': 0.1,
            'delay_mode': 'fixed'
        },
        'packet_loss': {
            'enabled': False,
            'loss_rate': 0.3,
            'burst_probability': 0.1,
            'burst_duration': 1.0,
            'recovery_time': 2.0
        },
        'combined_disturbance': {
            'enabled': False,
            'intensity': 1.0,
            'duration': 8.0
        },
        'presets': {
            'light_disturbance': {
                'network_delay': {'base_delay': 50, 'jitter': 25, 'packet_loss': 0.05},
                'packet_loss': {'loss_rate': 0.1, 'burst_probability': 0.05}
            },
            'moderate_disturbance': {
                'network_delay': {'base_delay': 200, 'jitter': 100, 'packet_loss': 0.1},
                'packet_loss': {'loss_rate': 0.3, 'burst_probability': 0.1}
            },
            'heavy_disturbance': {
                'network_delay': {'base_delay': 500, 'jitter': 250, 'packet_loss': 0.2},
                'packet_loss': {'loss_rate': 0.5, 'burst_probability': 0.2}
            }
        }
    }

# 加载配置文件
if 'config' not in st.session_state:
    st.session_state.config, st.session_state.config_source = load_config_file()

config = st.session_state.config

class MockTestAgent:
    """模拟测试代理类"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.received_messages = []
        self.sent_messages = []
        self.is_active = True
        
    def send_message(self, topic: str, content: str):
        """发送消息"""
        send_time = time.time()
        message = {
            'sender': self.agent_id,
            'content': content,
            'send_time': send_time,
            'message_id': f"{self.agent_id}_{len(self.sent_messages)}"
        }
        
        self.sent_messages.append({
            'send_time': send_time,
            'topic': topic,
            'message': message.copy()
        })
        
        return message
    
    def receive_message(self, message: Dict[str, Any], delay: float = 0, dropped: bool = False):
        """接收消息（模拟）"""
        if dropped:
            return  # 消息被丢弃
            
        receive_time = time.time()
        
        message_info = {
            'receive_time': receive_time,
            'message': message.copy(),
            'agent_id': self.agent_id,
            'delay': delay
        }
        
        if delay > 0:
            message_info['actual_delay'] = delay
            
        self.received_messages.append(message_info)

class NetworkDisturbanceSimulator:
    """网络扰动模拟器"""
    
    def __init__(self):
        self.agents = {}
        self.disturbances = {}
        self.message_history = []
        self.stats = {
            'total_sent': 0,
            'total_received': 0,
            'total_dropped': 0,
            'total_delayed': 0,
            'avg_delay': 0
        }
        
    def create_agents(self, agent_count: int) -> List[MockTestAgent]:
        """创建测试代理"""
        self.agents = {}
        for i in range(agent_count):
            agent_id = f"Agent{i+1}"
            self.agents[agent_id] = MockTestAgent(agent_id)
        return list(self.agents.values())
    
    def apply_delay_disturbance(self, base_delay: float, jitter: float, packet_loss: float):
        """应用延迟扰动"""
        self.disturbances['delay'] = {
            'type': 'delay',
            'base_delay': base_delay,
            'jitter': jitter,
            'packet_loss': packet_loss
        }
    
    def apply_packet_loss_disturbance(self, loss_rate: float, burst_probability: float, burst_duration: float):
        """应用丢包扰动"""
        self.disturbances['packet_loss'] = {
            'type': 'packet_loss',
            'loss_rate': loss_rate,
            'burst_probability': burst_probability,
            'burst_duration': burst_duration
        }
    
    def simulate_message_transmission(self, sender_id: str, topic: str, content: str, target_agents: List[str] = None):
        """模拟消息传输"""
        if sender_id not in self.agents:
            return
            
        sender = self.agents[sender_id]
        message = sender.send_message(topic, content)
        self.stats['total_sent'] += 1
        
        # 确定接收者
        if target_agents is None:
            target_agents = [aid for aid in self.agents.keys() if aid != sender_id]
        
        for target_id in target_agents:
            if target_id not in self.agents:
                continue
                
            target_agent = self.agents[target_id]
            delay = 0
            dropped = False
            
            # 应用扰动
            if 'delay' in self.disturbances:
                delay_config = self.disturbances['delay']
                base_delay = delay_config['base_delay'] / 1000.0  # 转换为秒
                jitter = delay_config['jitter'] / 1000.0
                packet_loss = delay_config['packet_loss']
                
                # 计算延迟
                delay = base_delay + random.uniform(-jitter/2, jitter/2)
                delay = max(0, delay)  # 确保延迟不为负
                
                # 检查是否丢包
                if random.random() < packet_loss:
                    dropped = True
            
            if 'packet_loss' in self.disturbances and not dropped:
                loss_config = self.disturbances['packet_loss']
                loss_rate = loss_config['loss_rate']
                
                # 检查普通丢包
                if random.random() < loss_rate:
                    dropped = True
                
                # 检查突发丢包（简化实现）
                burst_prob = loss_config['burst_probability']
                if random.random() < burst_prob:
                    dropped = True
            
            # 记录消息传输结果
            transmission_record = {
                'timestamp': time.time(),
                'sender': sender_id,
                'receiver': target_id,
                'topic': topic,
                'content': content,
                'delay': delay,
                'dropped': dropped,
                'message_id': message['message_id']
            }
            
            self.message_history.append(transmission_record)
            
            # 更新统计
            if dropped:
                self.stats['total_dropped'] += 1
            else:
                target_agent.receive_message(message, delay, dropped)
                self.stats['total_received'] += 1
                if delay > 0:
                    self.stats['total_delayed'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.stats['total_delayed'] > 0:
            delay_records = [r for r in self.message_history if r['delay'] > 0 and not r['dropped']]
            if delay_records:
                self.stats['avg_delay'] = sum(r['delay'] for r in delay_records) / len(delay_records)
        
        return self.stats.copy()
    
    def reset(self):
        """重置模拟器"""
        for agent in self.agents.values():
            agent.received_messages.clear()
            agent.sent_messages.clear()
        
        self.message_history.clear()
        self.disturbances.clear()
        self.stats = {
            'total_sent': 0,
            'total_received': 0,
            'total_dropped': 0,
            'total_delayed': 0,
            'avg_delay': 0
        }

# 初始化仿真器
if 'network_simulator' not in st.session_state:
    st.session_state.network_simulator = NetworkDisturbanceSimulator()

# 页面标题
st.title("🌐 网络扰动测试系统")
st.markdown("---")

# 创建主布局
col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ 网络扰动配置")
    
    # 配置文件信息
    with st.expander("📋 配置文件信息", expanded=False):
        st.info(f"**配置来源**: {st.session_state.config_source}")
        if st.session_state.config_source != "默认配置":
            st.success(f"✅ 配置文件路径: {st.session_state.config_source}")
        else:
            st.warning("⚠️ 未找到配置文件，使用内置默认值")
        
        if st.button("🔄 重新加载配置文件"):
            st.session_state.config, st.session_state.config_source = load_config_file()
            st.rerun()
    
    # 预设配置选择
    st.subheader("🎯 预设配置")
    presets = list(config.get('presets', {}).keys())
    presets.insert(0, "自定义配置")
    
    selected_preset = st.selectbox(
        "选择预设配置方案",
        options=presets,
        index=0,
        help="选择预设配置方案，或使用'自定义配置'手动设置参数"
    )
    
    # 应用预设配置
    if selected_preset != "自定义配置" and selected_preset in config.get('presets', {}):
        preset_config = config['presets'][selected_preset]
        st.info(f"🎯 已选择预设: {selected_preset}")
        
        # 显示预设配置概要
        if 'network_delay' in preset_config:
            delay_cfg = preset_config['network_delay']
            st.markdown(f"**网络延迟**: {delay_cfg.get('base_delay', 0)}±{delay_cfg.get('jitter', 0)}ms, 丢包率: {delay_cfg.get('packet_loss', 0):.2%}")
        if 'packet_loss' in preset_config:
            loss_cfg = preset_config['packet_loss']
            st.markdown(f"**数据包丢失**: {loss_cfg.get('loss_rate', 0):.2%}, 突发概率: {loss_cfg.get('burst_probability', 0):.2%}")
    
    st.divider()
    
    # 代理配置（从配置文件获取默认值）
    st.subheader("🤖 测试环境配置")
    test_env = config.get('test_environment', {})
    
    agent_count = st.number_input(
        "测试代理数量", 
        min_value=2, max_value=8, 
        value=test_env.get('agent_count', 4), 
        step=1,
        help="参与网络通信测试的代理数量"
    )
    
    # 消息配置
    message_count = st.number_input(
        "发送消息数量", 
        min_value=10, max_value=200, 
        value=test_env.get('message_count', 50), 
        step=10,
        help="测试期间发送的消息总数"
    )
    
    message_interval = st.slider(
        "消息间隔 (秒)", 
        0.1, 2.0, 
        test_env.get('message_interval', 0.2), 
        0.1,
        help="消息发送之间的时间间隔"
    )
    
    # 扰动类型选择
    st.subheader("🌐 扰动类型配置")
    
    disturbance_tabs = st.tabs(["网络延迟", "数据包丢失", "组合扰动"])
    
    # 扰动配置
    disturbance_configs = {}
    
    with disturbance_tabs[0]:
        st.markdown("**网络延迟扰动** - 模拟网络延迟、抖动和部分丢包")
        
        # 获取配置默认值（考虑预设配置）
        if selected_preset != "自定义配置" and selected_preset in config.get('presets', {}):
            delay_defaults = config['presets'][selected_preset].get('network_delay', {})
            # 合并预设配置和基础配置
            base_delay_config = config.get('network_delay', {})
            delay_defaults = {**base_delay_config, **delay_defaults}
        else:
            delay_defaults = config.get('network_delay', {})
        
        enable_delay = st.checkbox(
            "启用网络延迟扰动", 
            value=delay_defaults.get('enabled', True), 
            key="enable_delay",
            help="启用后将对消息传递添加网络延迟效果"
        )
        
        if enable_delay:
            col_a, col_b = st.columns(2)
            with col_a:
                base_delay = st.number_input(
                    "基础延迟 (ms)", 
                    0, 1000, 
                    delay_defaults.get('base_delay', 200), 
                    10, 
                    key="base_delay",
                    help="网络传输的基础延迟时间"
                )
                jitter = st.number_input(
                    "延迟抖动 (ms)", 
                    0, 500, 
                    delay_defaults.get('jitter', 100), 
                    10, 
                    key="jitter",
                    help="延迟的随机波动范围"
                )
            with col_b:
                delay_packet_loss = st.slider(
                    "丢包率", 
                    0.0, 0.5, 
                    delay_defaults.get('packet_loss', 0.1), 
                    0.01, 
                    key="delay_packet_loss",
                    help="网络延迟扰动导致的额外丢包率"
                )
                delay_mode_options = ["固定", "渐变", "随机"]
                delay_mode_map = {"固定": "fixed", "渐变": "gradual", "随机": "random"}
                reverse_map = {v: k for k, v in delay_mode_map.items()}
                default_mode_display = reverse_map.get(delay_defaults.get('delay_mode', 'fixed'), "固定")
                
                delay_mode = st.selectbox(
                    "延迟模式", 
                    delay_mode_options,
                    index=delay_mode_options.index(default_mode_display),
                    key="delay_mode",
                    help="延迟变化的模式：固定延迟、渐进变化或随机变化"
                )
            
            disturbance_configs['delay'] = {
                'enabled': True,
                'base_delay': base_delay,
                'jitter': jitter,
                'packet_loss': delay_packet_loss,
                'mode': delay_mode_map[delay_mode]
            }
    
    with disturbance_tabs[1]:
        st.markdown("**数据包丢失扰动** - 模拟网络丢包和突发丢失")
        
        # 获取配置默认值（考虑预设配置）
        if selected_preset != "自定义配置" and selected_preset in config.get('presets', {}):
            loss_defaults = config['presets'][selected_preset].get('packet_loss', {})
            # 合并预设配置和基础配置
            base_loss_config = config.get('packet_loss', {})
            loss_defaults = {**base_loss_config, **loss_defaults}
        else:
            loss_defaults = config.get('packet_loss', {})
        
        enable_packet_loss = st.checkbox(
            "启用数据包丢失扰动", 
            value=loss_defaults.get('enabled', False), 
            key="enable_packet_loss",
            help="启用后将模拟网络丢包情况"
        )
        
        if enable_packet_loss:
            col_c, col_d = st.columns(2)
            with col_c:
                loss_rate = st.slider(
                    "基础丢包率", 
                    0.0, 0.8, 
                    loss_defaults.get('loss_rate', 0.3), 
                    0.01, 
                    key="loss_rate",
                    help="正常情况下的数据包丢失率"
                )
                burst_probability = st.slider(
                    "突发丢包概率", 
                    0.0, 0.5, 
                    loss_defaults.get('burst_probability', 0.1), 
                    0.01, 
                    key="burst_probability",
                    help="发生突发性大量丢包的概率"
                )
            with col_d:
                burst_duration = st.number_input(
                    "突发持续时间 (s)", 
                    0.1, 5.0, 
                    loss_defaults.get('burst_duration', 1.0), 
                    0.1, 
                    key="burst_duration",
                    help="突发丢包状态的持续时间"
                )
                recovery_time = st.number_input(
                    "恢复时间 (s)", 
                    0.1, 10.0, 
                    loss_defaults.get('recovery_time', 2.0), 
                    0.1, 
                    key="recovery_time",
                    help="从突发丢包状态恢复到正常状态的时间"
                )
            
            disturbance_configs['packet_loss'] = {
                'enabled': True,
                'loss_rate': loss_rate,
                'burst_probability': burst_probability,
                'burst_duration': burst_duration,
                'recovery_time': recovery_time
            }
    
    with disturbance_tabs[2]:
        st.markdown("**组合扰动** - 同时应用延迟和丢包扰动")
        
        # 获取配置默认值
        combined_defaults = config.get('combined_disturbance', {})
        
        enable_combined = st.checkbox(
            "启用组合扰动", 
            value=combined_defaults.get('enabled', False), 
            key="enable_combined",
            help="同时应用网络延迟和数据包丢失扰动"
        )
        
        if enable_combined:
            st.info("组合扰动将同时应用上述配置的延迟和丢包扰动")
            
            col_e, col_f = st.columns(2)
            with col_e:
                combined_intensity = st.slider(
                    "扰动强度倍数", 
                    0.5, 2.0, 
                    combined_defaults.get('intensity', 1.0), 
                    0.1, 
                    key="combined_intensity",
                    help="扰动效果的强度放大倍数"
                )
            with col_f:
                combined_duration = st.number_input(
                    "扰动持续时间 (s)", 
                    1.0, 20.0, 
                    combined_defaults.get('duration', 8.0), 
                    0.5, 
                    key="combined_duration",
                    help="组合扰动的总持续时间"
                )
            
            disturbance_configs['combined'] = {
                'enabled': True,
                'intensity': combined_intensity,
                'duration': combined_duration
            }
    
    st.divider()
    
    # 配置导出和导入
    with st.expander("💾 配置管理", expanded=False):
        st.subheader("配置文件管理")
        
        col_export, col_import = st.columns(2)
        
        with col_export:
            st.markdown("**导出当前配置**")
            current_full_config = {
                'test_environment': {
                    'agent_count': agent_count,
                    'message_count': message_count, 
                    'message_interval': message_interval
                },
                'network_delay': disturbance_configs.get('delay', {}),
                'packet_loss': disturbance_configs.get('packet_loss', {}),
                'combined_disturbance': disturbance_configs.get('combined', {})
            }
            
            config_yaml = yaml.dump(current_full_config, default_flow_style=False, allow_unicode=True)
            
            st.download_button(
                label="📥 下载配置文件 (YAML)",
                data=config_yaml,
                file_name=f"network_disturbance_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                mime="application/x-yaml",
                help="下载当前配置参数为YAML文件"
            )
        
        with col_import:
            st.markdown("**配置文件位置**")
            st.info(f"📂 配置文件应放置在：\n`{CONFIG_DIR}`")
            st.markdown("**支持的文件名：**\n- `network_disturbance_config.yaml`\n- `network_disturbance_config.yml`")
            
            if st.button("📋 复制配置路径"):
                st.code(str(CONFIG_DIR), language="text")
    
    # 显示扰动摘要
    active_disturbances = [k for k, v in disturbance_configs.items() if v.get('enabled', False)]
    if active_disturbances:
        st.subheader("📊 扰动摘要")
        for dist_type in active_disturbances:
            config = disturbance_configs[dist_type]
            if dist_type == 'delay':
                st.info(f"**网络延迟扰动**\n"
                       f"基础延迟: {config['base_delay']}ms\n"
                       f"抖动: ±{config['jitter']}ms\n"
                       f"丢包率: {config['packet_loss']:.2%}")
            elif dist_type == 'packet_loss':
                st.info(f"**数据包丢失扰动**\n"
                       f"基础丢包率: {config['loss_rate']:.2%}\n"
                       f"突发丢包概率: {config['burst_probability']:.2%}\n"
                       f"突发持续: {config['burst_duration']:.1f}s")
            elif dist_type == 'combined':
                st.info(f"**组合扰动**\n"
                       f"强度倍数: {config['intensity']:.1f}x\n"
                       f"持续时间: {config['duration']:.1f}s")

with col2:
    st.header("📊 测试结果分析")
    
    # 运行测试按钮
    if st.button("🚀 运行网络扰动测试", type="primary", use_container_width=True):
        if not active_disturbances:
            st.warning("请至少启用一种扰动类型后再运行测试")
        else:
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 重置模拟器
            simulator = st.session_state.network_simulator
            simulator.reset()
            
            # 创建代理
            agents = simulator.create_agents(agent_count)
            status_text.text(f"已创建 {len(agents)} 个测试代理")
            progress_bar.progress(0.1)
            
            # 应用扰动配置
            if 'delay' in disturbance_configs and disturbance_configs['delay']['enabled']:
                delay_cfg_runtime = disturbance_configs['delay']
                simulator.apply_delay_disturbance(
                    delay_cfg_runtime['base_delay'], 
                    delay_cfg_runtime['jitter'], 
                    delay_cfg_runtime['packet_loss']
                )
                status_text.text("已配置网络延迟扰动")
            
            if 'packet_loss' in disturbance_configs and disturbance_configs['packet_loss']['enabled']:
                loss_cfg_runtime = disturbance_configs['packet_loss']
                simulator.apply_packet_loss_disturbance(
                    loss_cfg_runtime['loss_rate'],
                    loss_cfg_runtime['burst_probability'],
                    loss_cfg_runtime['burst_duration']
                )
                status_text.text("已配置数据包丢失扰动")
            
            progress_bar.progress(0.2)
            
            # 开始消息传输测试
            status_text.text("开始网络通信测试...")
            
            for i in range(message_count):
                # 随机选择发送代理
                sender = random.choice(agents)
                
                # 发送消息
                simulator.simulate_message_transmission(
                    sender.agent_id,
                    "test/network_communication",
                    f"测试消息 {i+1}/{message_count}"
                )
                
                # 更新进度
                progress = 0.2 + 0.7 * (i + 1) / message_count
                progress_bar.progress(progress)
                
                # 模拟时间间隔
                time.sleep(message_interval * 0.01)  # 加速模拟
            
            # 完成测试
            status_text.text("网络扰动测试完成！正在分析结果...")
            progress_bar.progress(1.0)
            
            # 存储结果
            st.session_state.test_results = {
                'agents': agents,
                'statistics': simulator.get_statistics(),
                'message_history': simulator.message_history,
                'disturbance_configs': disturbance_configs,
                'timestamp': datetime.now()
            }
            
            progress_bar.empty()
            status_text.empty()
            st.success("✅ 网络扰动测试完成！")
    
    # 显示测试结果
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        stats = results['statistics']
        
        # 关键指标展示
        st.subheader("📈 关键性能指标")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("总发送消息", stats['total_sent'], 
                     f"成功率: {(stats['total_received']/max(stats['total_sent']*agent_count-stats['total_sent'], 1)*100):.1f}%")
        
        with col_b:
            st.metric("总接收消息", stats['total_received'],
                     f"丢失: {stats['total_dropped']}")
        
        with col_c:
            loss_rate = stats['total_dropped'] / max(stats['total_sent'] * (agent_count - 1), 1)
            st.metric("实际丢包率", f"{loss_rate:.2%}",
                     f"延迟消息: {stats['total_delayed']}")
        
        with col_d:
            st.metric("平均延迟", f"{stats['avg_delay']*1000:.1f} ms",
                     f"≈ {stats['avg_delay']:.3f} 秒")
        
        # 消息传输时序图
        st.subheader("📊 消息传输分析")
        
        if results['message_history']:
            # 创建时序数据
            history_df = pd.DataFrame(results['message_history'])
            history_df['timestamp_formatted'] = pd.to_datetime(history_df['timestamp'], unit='s')
            history_df['delay_ms'] = history_df['delay'] * 1000
            
            # 创建子图
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=("消息传输状态", "网络延迟分布", "丢包情况统计"),
                row_heights=[0.4, 0.3, 0.3]
            )
            
            # 消息传输状态
            success_msgs = history_df[~history_df['dropped']]
            dropped_msgs = history_df[history_df['dropped']]
            
            if not success_msgs.empty:
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(success_msgs))),
                        y=success_msgs['delay_ms'],
                        mode='markers',
                        name='成功传输',
                        marker=dict(color='green', size=6),
                        text=[f"发送方: {row['sender']}<br>接收方: {row['receiver']}<br>延迟: {row['delay_ms']:.1f}ms" 
                              for _, row in success_msgs.iterrows()],
                        hovertemplate='%{text}<extra></extra>'
                    ),
                    row=1, col=1
                )
            
            if not dropped_msgs.empty:
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(dropped_msgs))),
                        y=[0] * len(dropped_msgs),
                        mode='markers',
                        name='消息丢失',
                        marker=dict(color='red', size=8, symbol='x'),
                        text=[f"发送方: {row['sender']}<br>接收方: {row['receiver']}<br>状态: 丢失" 
                              for _, row in dropped_msgs.iterrows()],
                        hovertemplate='%{text}<extra></extra>'
                    ),
                    row=1, col=1
                )
            
            # 延迟分布直方图
            if not success_msgs.empty:
                fig.add_trace(
                    go.Histogram(
                        x=success_msgs['delay_ms'],
                        nbinsx=20,
                        name='延迟分布',
                        marker_color='blue',
                        opacity=0.7
                    ),
                    row=2, col=1
                )
            
            # 丢包率统计
            agents = results['agents']
            agent_stats = []
            for agent in agents:
                sent = len(agent.sent_messages)
                received = len(agent.received_messages)
                agent_stats.append({
                    'agent': agent.agent_id,
                    'sent': sent,
                    'received': received
                })
            
            agent_df = pd.DataFrame(agent_stats)
            
            fig.add_trace(
                go.Bar(
                    x=agent_df['agent'],
                    y=agent_df['sent'],
                    name='发送消息',
                    marker_color='lightblue',
                    opacity=0.7
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=agent_df['agent'],
                    y=agent_df['received'],
                    name='接收消息',
                    marker_color='lightgreen',
                    opacity=0.7
                ),
                row=3, col=1
            )
            
            # 更新布局
            fig.update_layout(
                title="网络扰动测试详细分析",
                height=800,
                showlegend=True
            )
            
            fig.update_yaxes(title_text="延迟 (ms)", row=1, col=1)
            fig.update_yaxes(title_text="频次", row=2, col=1)
            fig.update_yaxes(title_text="消息数量", row=3, col=1)
            fig.update_xaxes(title_text="代理", row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 详细统计表
            st.subheader("📋 详细统计分析")
            
            # 代理性能统计
            with st.expander("📊 代理性能统计"):
                agent_perf = []
                for agent in agents:
                    received_with_delay = [msg for msg in agent.received_messages if 'actual_delay' in msg]
                    avg_delay = np.mean([msg['actual_delay'] for msg in received_with_delay]) if received_with_delay else 0
                    
                    agent_perf.append({
                        '代理ID': agent.agent_id,
                        '发送消息': len(agent.sent_messages),
                        '接收消息': len(agent.received_messages),
                        '平均接收延迟(ms)': f"{avg_delay*1000:.1f}",
                        '活跃状态': "🟢 正常" if agent.is_active else "🔴 异常"
                    })
                
                st.dataframe(pd.DataFrame(agent_perf), use_container_width=True)
            
            # 扰动效果分析
            with st.expander("🔍 扰动效果分析"):
                for dist_type, dist_cfg in results['disturbance_configs'].items():
                    if dist_cfg.get('enabled', False):
                        if dist_type == 'delay':
                            delayed_msgs = [msg for msg in results['message_history'] 
                                          if msg['delay'] > 0 and not msg['dropped']]
                            avg_delay_effect = np.mean([msg['delay']*1000 for msg in delayed_msgs]) if delayed_msgs else 0
                            st.success(f"**网络延迟扰动效果**\n"
                                     f"- 配置延迟: {dist_cfg['base_delay']}±{dist_cfg['jitter']}ms\n"
                                     f"- 实际平均延迟: {avg_delay_effect:.1f}ms\n"
                                     f"- 延迟消息数: {len(delayed_msgs)}")
                        
                        elif dist_type == 'packet_loss':
                            total_expected = stats['total_sent'] * (agent_count - 1)
                            actual_loss = stats['total_dropped'] / max(total_expected, 1)
                            st.warning(f"**数据包丢失扰动效果**\n"
                                     f"- 配置丢包率: {dist_cfg['loss_rate']:.2%}\n"
                                     f"- 实际丢包率: {actual_loss:.2%}\n"
                                     f"- 丢失消息数: {stats['total_dropped']}")

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 系统信息")
    
    # 配置文件状态
    st.subheader("📋 配置文件状态")
    sidebar_config = st.session_state.config if 'config' in st.session_state else {}
    if st.session_state.config_source != "默认配置":
        st.success("✅ 配置文件已加载")
        st.info(f"**来源**: {st.session_state.config_source}")
        
        # 显示配置文件概要
        if 'presets' in sidebar_config:
            st.markdown(f"**预设方案**: {len(sidebar_config['presets'])} 个")
        
        # 显示配置的默认扰动
        enabled_defaults = []
        if sidebar_config.get('network_delay', {}).get('enabled', False):
            enabled_defaults.append("网络延迟")
        if sidebar_config.get('packet_loss', {}).get('enabled', False):
            enabled_defaults.append("数据包丢失")
        if sidebar_config.get('combined_disturbance', {}).get('enabled', False):
            enabled_defaults.append("组合扰动")
        
        if enabled_defaults:
            st.markdown(f"**默认启用**: {', '.join(enabled_defaults)}")
        
    else:
        st.warning("⚠️ 使用内置默认配置")
        st.info(f"**配置目录**: `{CONFIG_DIR}`\n**文件名**: `network_disturbance_config.yaml`")
    
    # 核心模块状态
    st.subheader("🔧 核心模块状态")
    if NETWORK_LIB_AVAILABLE:
        st.success("✅ enhanced_message_bus")
        st.success("✅ network_disturbance") 
        st.markdown("**运行模式**: 完整功能")
    else:
        st.warning("⚠️ 模拟模式运行")
        st.info("网络模块不可用，使用模拟数据")
        st.markdown("**运行模式**: 演示模式")
    
    # 数据源信息
    st.subheader("📊 数据源说明")
    st.markdown("""
    **配置数据**:
    - 📋 YAML配置文件参数
    - 🎯 预设扰动方案
    - ⚙️ 测试环境配置
    
    **运行时数据**:
    - 📊 消息传递统计
    - ⏱️ 实时通信延迟
    - 📉 丢包率统计
    - 🤖 代理性能指标
    """)
    
    # 业务逻辑说明
    st.subheader("业务逻辑")
    st.markdown("""
    **核心功能：**
    1. 🌐 网络延迟扰动：模拟网络延迟和抖动
    2. 📦 数据包丢失：模拟网络丢包情况
    3. 🔄 组合扰动：多种网络问题同时作用
    4. 🤖 多代理通信：模拟分布式系统通信
    5. 📊 实时监控：统计通信性能指标
    
    **应用场景：**
    - 分布式系统网络性能测试
    - 网络故障影响评估
    - 通信协议鲁棒性验证
    - 网络优化效果评估
    """)
    
    # 操作说明
    with st.expander("📖 操作说明"):
        st.markdown("""
        1. **设置代理数量**：配置参与测试的代理数量
        2. **配置消息参数**：设置发送消息数量和间隔
        3. **选择扰动类型**：启用网络延迟、丢包或组合扰动
        4. **调整扰动参数**：配置延迟、抖动、丢包率等
        5. **运行测试**：开始网络扰动测试
        6. **分析结果**：查看统计数据和可视化分析
        
        **提示：**
        - 延迟扰动适合测试时延敏感应用
        - 丢包扰动适合测试可靠性需求
        - 组合扰动可以模拟复杂网络环境
        - 代理数量影响测试的复杂度
        """)

# 页脚
st.markdown("---")
st.markdown("*基于 `8.test_network_disturbance.py` 的网络扰动测试系统*")
