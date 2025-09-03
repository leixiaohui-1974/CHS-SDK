from core_lib.llm_services.llm_service import call_tongyi_qianwen_api
from core_lib.config.unified_config_manager import validate_yaml_content

class LLMSystemBuilderAgent:
    """建模工程师智能体。"""
    
    def get_system_prompt(self):
        return """
你是一位精通水利工程建模的顶级专家，专门使用 CHS-SDK。你的任务是将用户的自然语言描述转换成一个结构完整、语法正确的 `universal_config.yml` 文件内容。

你必须严格遵循以下规则：
1.  你的输出**必须且只能**是YAML格式的文本，绝不能包含任何额外的解释或文字。
2.  YAML的顶级键必须包含 `components` 和 `topology`。
3.  你必须理解并使用以下核心概念定义来创建组件：
    * **被控对象 (Controlled Objects)**: 水文状态需要被管理和控制的物理实体。包括: `RiverChannel`, `Pipe`, `Canal`, `Reservoir`, `Lake`, `Pond`。
    * **控制对象 (Controlling Objects)**: 能够改变被控对象状态的物理设施。包括: `GateStation`, `PumpStation`, `ValveStation`, `HydropowerStation`。
    * **组件类型**: 在`components`中创建实例时，`type`字段必须是上述定义的英文名称之一。
4.  根据用户的描述，在 `components` 列表中创建相应的物理对象实例，并正确填写 `id`, `type`, 和 `params`。
5.  在 `topology` 列表中描述组件之间的连接关系。
"""

    def run(self, user_prompt: str) -> str:
        """执行建模任务。"""
        print(f"[LLMSystemBuilderAgent]: 已接收任务 -> {user_prompt}")
        system_prompt = self.get_system_prompt()

        try:
            generated_yaml = call_tongyi_qianwen_api(user_prompt, system_prompt)
            print("[LLMSystemBuilderAgent]: 已从大模型获取初步YAML配置。")
            validation_result = validate_yaml_content(generated_yaml)
            if validation_result['valid']:
                print("[LLMSystemBuilderAgent]: 配置验证通过。")
                return generated_yaml
            else:
                print(f"[LLMSystemBuilderAgent]: 配置验证失败: {validation_result['errors']}")
                print("[LLMSystemBuilderAgent]: 正在尝试进行自我修正...")
                correction_prompt = (f"你上次生成的YAML配置未能通过验证，错误如下：\n{validation_result['errors']}\n\n请修正以上错误，并根据我的原始需求重新生成一个完整且正确的YAML配置：'{user_prompt}'")
                corrected_yaml = call_tongyi_qianwen_api(correction_prompt, system_prompt)
                final_validation = validate_yaml_content(corrected_yaml)
                if final_validation['valid']:
                    print("[LLMSystemBuilderAgent]: 修正后的配置验证通过。")
                    return corrected_yaml
                else:
                    raise RuntimeError(f"自我修正失败: {final_validation['errors']}")
        except Exception as e:
            error_message = f"建模失败：处理过程中出错 - {e}"
            print(f"[LLMSystemBuilderAgent]: {error_message}")
            raise RuntimeError(error_message)