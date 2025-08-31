# -*- coding: utf-8 -*-

import os
import pandas as pd
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.llm_integration_agents import (
    LLMSystemBuilderAgent,
    LLMScenarioDesignerAgent,
    LLMDispatchCommanderAgent,
    LLMDataAnalystAgent,
)

def demonstrate_system_builder():
    """Demonstrates Role 1: System Architect & Builder."""
    print("\n" + "="*50)
    print("演示角色一：系统构建师 (System Architect & Builder)")
    print("="*50)

    # 1. 初始化一个临时的消息总线和构建师Agent
    temp_bus = MessageBus()
    builder_agent = LLMSystemBuilderAgent('llm_builder', temp_bus)

    # 2. 提供自然语言描述
    description = "Create a system with a reservoir that feeds a river channel through a controllable gate."
    
    # 3. 命令Agent生成配置
    configs = builder_agent.build_system_from_description(description)

    # 4. 打印结果
    print("\n--- [结果] 生成的YAML配置 ---")
    for name, content in configs.items():
        print(f"\n# {name.capitalize()}.yml")
        print(content)
    print("--- [演示结束] ---\n")


def demonstrate_scenario_designer():
    """Demonstrates Role 2: Scenario Designer."""
    print("\n" + "="*50)
    print("演示角色二：情景设计师 (Scenario Designer)")
    print("="*50)

    # 1. 初始化Agent
    temp_bus = MessageBus()
    designer_agent = LLMScenarioDesignerAgent('llm_designer', temp_bus)

    # 2. 提供自然语言情景描述
    description = "At timestep 100, fail pump_1 by setting its status to 0. Then at timestep 200, start a heavy rainfall event with an intensity of 50."
    
    # 3. 命令Agent生成情景脚本
    scenario_yaml = designer_agent.design_scenario_from_description(description)
    
    # 4. 打印结果
    print("\n--- [结果] 生成的场景YAML脚本 ---")
    print(scenario_yaml)
    print("--- [演示结束] ---\n")


def demonstrate_dispatch_commander():
    """Demonstrates Role 3: Intelligent Dispatch Commander."""
    print("\n" + "="*50)
    print("演示角色三：智能调度指挥官 (Intelligent Dispatch Commander)")
    print("="*50)
    
    # 1. 设置一个真实的消息总线，模拟系统正在运行
    message_bus = MessageBus()
    
    # 2. 定义中央调度器的ID并初始化LLM指挥官
    dispatcher_id = 'central_dispatcher_agent'
    commander_agent = LLMDispatchCommanderAgent('llm_commander', message_bus, dispatcher_id)
    
    # 3. 模拟中央调度器，订阅LLM指挥官将要发布的结构化指令
    received_command = None
    def dispatcher_listener(topic, payload):
        nonlocal received_command
        print(f"\n[模拟的中央调度器] 接收到指令！主题: '{topic}', 载荷: {payload}")
        received_command = payload

    message_bus.subscribe(commander_agent.dispatcher_control_topic, dispatcher_listener)
    
    # 4. 模拟用户通过UI或其他接口发送自然语言指令
    nl_command = "The upstream is flooding, prioritize flood control for reservoir_1 immediately!"
    print(f"[模拟用户输入] 发布自然语言指令: '{nl_command}' 到主题 '{commander_agent.command_topic}'")
    message_bus.publish(commander_agent.command_topic, {'text': nl_command})

    # 5. 验证结果
    print("\n--- [结果] ---")
    if received_command and received_command['mode'] == 'emergency':
        print("成功！LLM指挥官正确解析了自然语言指令，并向中央调度器发送了结构化的应急模式指令。")
    else:
        print("失败！未能正确接收或解析指令。")
    print("--- [演示结束] ---\n")


def demonstrate_data_analyst():
    """Demonstrates Role 4: Data Analyst & Diagnostic Expert."""
    print("\n" + "="*50)
    print("演示角色四：数据分析师与诊断专家 (Data Analyst & Diagnostic Expert)")
    print("="*50)
    
    # 1. 创建一个模拟的日志文件
    log_data = {
        'time': range(0, 500, 10),
        'reservoir_1.water_level': [140 + (i/100) + (-1)**i * 0.2 for i in range(50)],
        'gate_1.opening': [0.5 - (i/100)*0.1 for i in range(50)],
    }
    # 在第35个采样点（时间350）制造一个异常
    log_data['reservoir_1.water_level'][35] = 145.5 

    log_df = pd.DataFrame(log_data)
    log_path = 'temp_simulation_log.csv'
    log_df.to_csv(log_path, index=False)
    print(f"创建了模拟日志文件: '{log_path}'")

    # 2. 初始化分析师Agent
    analyst_agent = LLMDataAnalystAgent('llm_analyst')
    
    # 3. 提出一个分析问题
    query = "Why did the water level of reservoir_1 exceed the limit?"
    
    # 4. 获取分析报告
    report = analyst_agent.analyze_results(log_path, query)
    
    # 5. 打印结果
    print("\n--- [结果] LLM生成的分析报告 ---")
    print(report)
    
    # 6. 清理临时文件
    os.remove(log_path)
    print(f"\n清理临时文件: '{log_path}'")
    print("--- [演示结束] ---\n")


if __name__ == '__main__':
    demonstrate_system_builder()
    demonstrate_scenario_designer()
    demonstrate_dispatch_commander()
    demonstrate_data_analyst()
