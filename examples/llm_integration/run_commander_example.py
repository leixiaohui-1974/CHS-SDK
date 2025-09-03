import os
import sys

# --- 添加项目根目录到Python路径 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core_lib.llm_integration_agents.llm_dispatch_commander_agent import LLMDispatchCommanderAgent

def run_complex_task():
    """
    演示如何使用总指挥官智能体来处理一个复杂的多步骤任务。
    """
    # 实例化总指挥官
    commander = LLMDispatchCommanderAgent()
    
    # 用户提出的高级、模糊、多步骤的需求
    complex_prompt = """
    你好，请帮我完成以下工作：
    1. 首先，帮我建一个模型：一个叫'big_reservoir'的水库，通过一个叫'main_gate'的闸门连接到一个叫'main_canal'的渠道。
    2. 然后，为这个模型设计一个洪水场景：让'big_reservoir'的入流在10小时内从50m³/s线性增长到800m³/s。
    3. （注意：模拟运行和结果分析步骤在此脚本中为注释状态，因为它们需要一个真实的模拟器函数。）
    """
    
    # 将任务交给总指挥官，它将自动进行任务分解和执行
    commander.run(complex_prompt)

if __name__ == "__main__":
    run_complex_task()
