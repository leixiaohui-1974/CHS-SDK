import json
from core_lib.llm_services.llm_service import call_tongyi_qianwen_api
from core_lib.analysis.analytics_tools import (
    get_controlled_components, 
    get_causal_variables,
    plot_analysis_chart,
    get_data_subset_as_json
)

class LLMResultAnalysisAgent:
    """控制论分析师智能体。"""
    
    def get_system_prompt(self):
        return """
你是一位顶尖的水系统控制论分析专家。你的任务是基于提供的模拟数据，分析关键变量之间的因果关系，并生成一段简洁、专业、符合控制论思想的分析摘要。
严格遵循以下“扰动-响应-控制”的分析框架：
1. **识别扰动**: 首先描述扰动变量（Disturbances）的变化。
2. **描述响应**: 接着描述状态变量（States）如何响应这个扰动。
3. **解释控制**: 最后，解释控制系统是如何应对这种变化的。
你的输出**必须且只能**是一段自然语言的分析文本。
"""

    def _analyze_correlation_with_llm(self, component_id: str, variables_data: dict, results_df_json: str) -> str:
        prompt = (
            f"请为组件 '{component_id}' 分析以下变量之间的因果关系：\n\n"
            f" - **扰动变量**: {variables_data.get('disturbances', [])}\n"
            f" - **状态变量**: {variables_data.get('states', [])}\n"
            f" - **控制变量**: {variables_data.get('controls', [])}\n\n"
            f"以下是相关的时序数据（JSON格式）：\n{results_df_json}\n\n"
            f"请根据以上信息生成分析摘要。"
        )
        system_prompt = self.get_system_prompt()
        return call_tongyi_qianwen_api(prompt, system_prompt)

    def run(self, user_prompt: str, context: dict) -> str:
        """执行结果分析任务。"""
        print(f"[LLMResultAnalysisAgent]: 已接收任务 -> {user_prompt}")
        results_path = context.get('results_path')
        if not results_path:
            raise ValueError("上下文中必须提供 'results_path'")
        final_report = [f"# 模拟结果分析报告 ({results_path})\n"]
        try:
            controlled_components = get_controlled_components(results_path)
            for i, component_id in enumerate(controlled_components):
                final_report.append(f"\n## 分析章节：组件 `{component_id}`\n")
                causal_vars = get_causal_variables(component_id=component_id, results_path=results_path)
                
                all_vars_for_llm = causal_vars.get('disturbances', []) + causal_vars.get('states', []) + causal_vars.get('controls', [])
                relevant_df_json = get_data_subset_as_json(results_path, all_vars_for_llm)
                
                analysis_summary = self._analyze_correlation_with_llm(component_id, causal_vars, relevant_df_json)
                final_report.append("### 控制论分析摘要\n")
                final_report.append(analysis_summary)
                
                chart_path = plot_analysis_chart(
                    variables=causal_vars, 
                    results_path=results_path,
                    title=f"{component_id}_扰动_响应_控制分析图"
                )
                final_report.append("\n### 可视化图表\n")
                final_report.append(f"![{component_id} 分析图]({chart_path})\n")
            return "\n".join(final_report)
        except Exception as e:
            raise RuntimeError(f"结果分析失败: {e}")