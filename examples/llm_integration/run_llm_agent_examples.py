import os
import sys
import json

# --- 添加项目根目录到Python路径 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core_lib.llm_integration_agents.llm_system_builder_agent import LLMSystemBuilderAgent
from core_lib.llm_integration_agents.llm_scenario_designer_agent import LLMScenarioDesignerAgent
from core_lib.llm_integration_agents.llm_data_analyst_agent import LLMDataAnalystAgent
from core_lib.llm_integration_agents.llm_result_analysis_agent import LLMResultAnalysisAgent

class CHS_Nexus_Commander:
    """CHS-Nexus 总指挥官的模拟实现。"""
    def __init__(self):
        self.agents = {
            "LLMSystemBuilderAgent": LLMSystemBuilderAgent(),
            "LLMScenarioDesignerAgent": LLMScenarioDesignerAgent(),
            "LLMDataAnalystAgent": LLMDataAnalystAgent(),
            "LLMResultAnalysisAgent": LLMResultAnalysisAgent(),
        }
        print("CHS-Nexus 总指挥官已上线。")

    def delegate_task(self, agent_name: str, user_prompt: str, context: dict = None):
        """模拟任务委派功能。"""
        if agent_name not in self.agents:
            raise ValueError(f"错误：未知智能体 '{agent_name}'。")
        agent = self.agents[agent_name]
        print(f"\n================ 任务开始：委派给 {agent_name} ================")
        try:
            result = agent.run(user_prompt=user_prompt, context=context) if context else agent.run(user_prompt=user_prompt)
            print(f"\n--- {agent_name} 执行结果 ---\n{result}")
            print(f"================ 任务结束：{agent_name} 已完成 ================\n")
            return result
        except Exception as e:
            print(f"在执行 '{agent_name}' 任务时发生错误: {e}")
            return None

def setup_test_files():
    """创建用于演示的虚拟文件"""
    # 创建虚拟结果文件
    results_file = "./output/simulation_log.csv"
    os.makedirs("./output", exist_ok=True)
    with open(results_file, "w") as f:
        f.write("time,res1.water_level,res1.inflow,gate1.opening_command\n")
        f.write("0,150.0,100,0.5\n")
        f.write("1,150.1,120,0.6\n")
        f.write("2,150.3,150,0.7\n")
        f.write("3,150.2,130,0.65\n")
    print(f"已创建虚拟结果文件: {results_file}")
    return results_file

if __name__ == "__main__":
    nexus_commander = CHS_Nexus_Commander()
    
    # 准备演示文件
    results_file_path = setup_test_files()
    
    # --- 运行所有示例 ---

    # 1. 建模工程师
    print("\n--- 演示1: 调用建模工程师 ---")
    builder_prompt = "创建一个水利系统，包含一个名为res1的水库和一个下游渠道chan1。水库通过一个ID为gate1的闸门与渠道相连。"
    model_yaml = nexus_commander.delegate_task("LLMSystemBuilderAgent", builder_prompt)
    
    # 2. 情景设计师
    print("\n--- 演示2: 调用情景设计师 ---")
    scenario_prompt = "为水库res1设计一个洪水情景。在模拟开始后，让res1的入流在5个小时内从100线性增加到500。"
    # 假设我们已经有了模型配置，可以从上一步获取，这里为简化直接构造
    model_config_context = {
        "model_config": {
            "components": [{"id": "res1", "type": "Reservoir"}, {"id": "chan1", "type": "Canal"}]
        }
    }
    nexus_commander.delegate_task("LLMScenarioDesignerAgent", scenario_prompt, context=model_config_context)

    # 3. 数据问答员
    print("\n--- 演示3: 调用数据问答员 ---")
    data_analyst_prompt = "res1水库的最高水位是多少？"
    data_context = {"results_path": results_file_path}
    nexus_commander.delegate_task("LLMDataAnalystAgent", data_analyst_prompt, context=data_context)

    # 4. 控制论分析师
    print("\n--- 演示4: 调用控制论分析师 ---")
    analysis_prompt = "请为这个模拟结果生成一份完整的控制性能分析报告。"
    nexus_commander.delegate_task("LLMResultAnalysisAgent", analysis_prompt, context=data_context)
