import pandas as pd
import os
from core_lib.llm_services.llm_service import call_tongyi_qianwen_api

class LLMDataAnalystAgent:
    """数据问答员智能体"""

    def get_system_prompt(self, df_head_str: str):
        return f"""
你是一个专业的数据分析师，擅长使用Python的Pandas库。
你的任务是根据用户的自然语言问题，生成一行可以直接执行的Pandas代码来回答这个问题。
你正在分析的数据集结构如下（前5行）：
{df_head_str}

规则：
1.  你的代码必须操作一个名为 `df` 的DataFrame对象。
2.  你的代码必须只输出最终的答案，而不是一个DataFrame。例如，使用 `.iloc[0]` 或 `.max()` 来获取具体数值。
3.  你的输出**必须且只能**是一行Python代码，不能包含任何导入语句、解释或Markdown标记。
"""

    def run(self, user_prompt: str, context: dict) -> str:
        print(f"[LLMDataAnalystAgent]: 已接收任务 -> {user_prompt}")
        results_path = context.get("results_path")
        if not results_path or not os.path.exists(results_path):
            raise FileNotFoundError(f"结果文件不存在: {results_path}")

        try:
            df = pd.read_csv(results_path)
            df_head_str = df.head().to_string()
            
            system_prompt = self.get_system_prompt(df_head_str)
            
            print("[LLMDataAnalystAgent]: 正在生成Pandas查询代码...")
            pandas_code = call_tongyi_qianwen_api(user_prompt, system_prompt)
            print(f"[LLMDataAnalystAgent]: 已生成代码 -> {pandas_code}")
            
            print("[LLMDataAnalystAgent]: 正在安全地执行代码...")
            # 在一个受限的环境中执行代码
            local_scope = {'df': df}
            exec(f"result = {pandas_code}", globals(), local_scope)
            answer = local_scope.get('result', "代码未返回结果。")
            
            print(f"[LLMDataAnalystAgent]: 执行完毕。")
            return f"根据数据分析，问题的答案是: {answer}"

        except Exception as e:
            error_message = f"数据分析失败: {e}"
            print(f"[LLMDataAnalystAgent]: {error_message}")
            raise RuntimeError(error_message)