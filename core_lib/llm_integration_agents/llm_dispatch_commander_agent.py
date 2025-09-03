import json
from core_lib.llm_services.llm_service import call_tongyi_qianwen_api
from .llm_system_builder_agent import LLMSystemBuilderAgent
from .llm_scenario_designer_agent import LLMScenarioDesignerAgent
from .llm_data_analyst_agent import LLMDataAnalystAgent
from .llm_result_analysis_agent import LLMResultAnalysisAgent
# 假设有一个用于运行模拟的函数
# from core_lib.core_engine.testing.simulation_harness import run_simulation_from_config

class LLMDispatchCommanderAgent:
    """
    总指挥官智能体 (CHS-Nexus)，负责解析用户意图、分解任务并委派给专家智能体。
    """
    def __init__(self):
        self.specialized_agents = {
            "LLMSystemBuilderAgent": LLMSystemBuilderAgent(),
            "LLMScenarioDesignerAgent": LLMScenarioDesignerAgent(),
            "LLMDataAnalystAgent": LLMDataAnalystAgent(),
            "LLMResultAnalysisAgent": LLMResultAnalysisAgent(),
        }
        self.state = {}  # 用于在任务步骤之间传递上下文信息
        print("CHS-Nexus 总指挥官已初始化。")

    def get_system_prompt(self):
        return """
你是一个顶级的AI项目经理，代号CHS-Nexus。你的核心任务是理解用户的最终目标，并将其分解为一个由多个步骤组成的、逻辑清晰的JSON执行计划。

你有四位专家下属，每位都有特定的任务领域：
- `LLMSystemBuilderAgent`: **建模工程师**。负责根据用户的描述创建或修改水利模型的结构（components 和 topology）。
- `LLMScenarioDesignerAgent`: **情景设计师**。负责为现有模型创建或修改模拟情景（如洪水过程、设备故障等）。
- `LLMDataAnalystAgent`: **数据问答员**。负责对**已有的**模拟结果文件进行快速、具体的数据查询（例如“最高水位是多少？”）。
- `LLMResultAnalysisAgent`: **控制论分析师**。负责对**已有的**模拟结果文件生成一份系统性的、深度的图文分析报告。

你的输出**必须是**一个符合以下格式的JSON数组字符串，不能包含任何额外的解释或文字：
```json
[
  {
    "step": 1,
    "agent": "AGENT_NAME",
    "prompt": "给这位专家的具体指令"
  },
  {
    "step": 2,
    "agent": "AGENT_NAME",
    "prompt": "..."
  }
]
```
"""

    def run(self, user_prompt: str):
        """
        接收用户的高级指令，生成并执行一个多步骤计划。
        """
        print(f"[Commander]: 接收到高级指令 -> '{user_prompt}'")
        
        # 步骤1: 让大模型生成执行计划
        system_prompt = self.get_system_prompt()
        plan_str = call_tongyi_qianwen_api(user_prompt, system_prompt)
        print(f"[Commander]: 已生成执行计划 -> \n{plan_str}")
        
        try:
            plan = json.loads(plan_str)
        except json.JSONDecodeError:
            print("[Commander]: 错误：大模型返回的计划不是有效的JSON格式。")
            return

        # 步骤2: 按顺序执行计划中的每一步
        for task in sorted(plan, key=lambda x: x['step']):
            agent_name = task.get("agent")
            prompt = task.get("prompt")
            
            if not agent_name or not prompt:
                print(f"[Commander]: 步骤 {task.get('step')} 格式错误，跳过。")
                continue

            if agent_name in self.specialized_agents:
                agent = self.specialized_agents[agent_name]
                print(f"\n--- [步骤 {task['step']}] 正在执行: 调用 {agent_name} ---")
                
                # 准备上下文信息
                context = self.state

                try:
                    # 专家智能体执行任务
                    if agent_name == "LLMSystemBuilderAgent":
                        result = agent.run(user_prompt=prompt)
                    elif agent_name in ["LLMScenarioDesignerAgent", "LLMDataAnalystAgent", "LLMResultAnalysisAgent"]:
                        result = agent.run(user_prompt=prompt, context=context)
                    else:
                        result = agent.run(user_prompt=prompt)
                    
                    # 更新共享状态 (非常重要)
                    if agent_name == "LLMSystemBuilderAgent":
                        self.state['model_config_yaml'] = result
                        print("[Commander]: 状态更新 -> 已保存模型配置。")
                    elif agent_name == "LLMScenarioDesignerAgent":
                        if "SCENARIO_CSV" in result:
                            self.state['scenario_csv_path'] = result.split(":")[1]
                            print(f"[Commander]: 状态更新 -> 已保存情景CSV路径: {self.state['scenario_csv_path']}")
                    # 模拟运行和分析需要基于之前步骤的结果
                    # if agent_name == "SomeSimulationRunner":
                    #     self.state['results_path'] = result['log_path']

                    print(f"--- [步骤 {task['step']}] {agent_name} 执行完毕 ---")

                except Exception as e:
                    print(f"--- [步骤 {task['step']}] {agent_name} 执行失败: {e} ---")
                    break # 一旦某一步失败，就中断整个流程
            else:
                print(f"--- [步骤 {task['step']}] 警告: 计划中的智能体 '{agent_name}' 不存在，已跳过。 ---")
