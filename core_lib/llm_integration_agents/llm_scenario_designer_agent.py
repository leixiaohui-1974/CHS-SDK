import pandas as pd
import os
import json
from core_lib.llm_services.llm_service import call_tongyi_qianwen_api

class LLMScenarioDesignerAgent:
    """情景设计师智能体"""

    def get_system_prompt(self):
        return """
你是一名专业的水利工程情景设计师。你的任务是根据用户的自然语言描述，创建一个用于模拟的事件（event）场景。
你的输出必须遵循以下两种格式之一：

1.  **对于简单的流量或水位过程**，生成一个CSV文件的内容。第一列必须是'time'（表示从模拟开始的时间，单位为小时），后续列的命名规则必须是`组件ID.变量名`，例如`res1.inflow`。
2.  **对于瞬时事件**，生成一个YAML格式的`events`配置块。

你必须理解并使用以下核心概念定义来定位操作对象：
* **被控对象 (Controlled Objects)**: 包括: `RiverChannel`, `Pipe`, `Canal`, `Reservoir`, `Lake`, `Pond`。
* **控制对象 (Controlling Objects)**: 包括: `GateStation`, `PumpStation`, `ValveStation`, `HydropowerStation`。
* **组件ID**: 你必须从用户提供的上下文中识别出正确的组件ID。

在决定输出格式时，优先选择生成CSV格式。只有当用户明确要求开关、故障等瞬时动作时，才生成YAML `events`块。
你的输出**必须且只能**是CSV内容或YAML `events`块，不能包含任何额外的解释或文字。
"""
    
    def run(self, user_prompt: str, context: dict) -> str:
        print(f"[LLMScenarioDesignerAgent]: 已接收任务 -> {user_prompt}")
        model_context = context.get("model_config", {})
        
        full_prompt = (
            f"这是当前的模型结构信息，请在此基础上设计情景：\n"
            f"```json\n{json.dumps(model_context, indent=2)}\n```\n\n"
            f"用户的具体情景设计需求如下：\n'{user_prompt}'"
        )
        
        system_prompt = self.get_system_prompt()
        
        try:
            llm_output = call_tongyi_qianwen_api(full_prompt, system_prompt)
            print("[LLMScenarioDesignerAgent]: 已从大模型获取情景数据。")

            # 判断输出是CSV还是YAML
            if 'time,'.lower() in llm_output.lower() or ',' in llm_output.split('\n')[0]:
                print("[LLMScenarioDesignerAgent]: 检测到输出为CSV格式。正在保存为文件...")
                output_dir = "./output/scenarios"
                os.makedirs(output_dir, exist_ok=True)
                file_path = os.path.join(output_dir, "scenario_data.csv")
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(llm_output)
                print(f"[LLMScenarioDesignerAgent]: 情景数据已保存至: {file_path}")
                return f"SCENARIO_CSV:{file_path}"
            else:
                print("[LLMScenarioDesignerAgent]: 检测到输出为YAML events块。")
                return llm_output

        except Exception as e:
            error_message = f"情景设计失败：{e}"
            print(f"[LLMScenarioDesignerAgent]: {error_message}")
            raise RuntimeError(error_message)
