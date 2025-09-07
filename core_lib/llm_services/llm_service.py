import os
from http import HTTPStatus
import dashscope
import warnings
from .llm_config import TONGYI_API_KEY

# 设置API密钥（如果可用）
if TONGYI_API_KEY:
    dashscope.api_key = TONGYI_API_KEY
else:
    warnings.warn("通义千问API密钥未设置。LLM相关功能将无法使用。")

def call_tongyi_qianwen_api(prompt: str, system_prompt: str = None, model: str = 'qwen-turbo') -> str:
    """调用通义千问大模型的API。"""
    print(f"--- 正在向通义千问 ({model}) 发送API请求... ---")
    
    # 如果有系统提示词，将其与用户提示词合并
    if system_prompt:
        full_prompt = f"系统提示：{system_prompt}\n\n用户输入：{prompt}"
    else:
        full_prompt = prompt
    
    try:
        response = dashscope.Generation.call(
            model=model,
            prompt=full_prompt
        )
        if response.status_code == HTTPStatus.OK:
            print("--- API请求成功 ---")
            llm_output = response.output['text']
            if llm_output.strip().startswith("```") and llm_output.strip().endswith("```"):
                lines = llm_output.strip().split('\n')
                llm_output = '\n'.join(lines[1:-1])
            return llm_output.strip()
        else:
            error_message = f"调用通义千问API失败: {response.code} - {response.message}"
            print(error_message)
            raise Exception(error_message)
    except Exception as e:
        print(f"调用API时发生异常: {e}")
        raise