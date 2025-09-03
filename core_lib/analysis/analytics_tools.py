import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import re
from typing import List, Dict, Set

# --- 为保存图表设置输出目录 ---
CHART_OUTPUT_DIR = "./output/charts"
if not os.path.exists(CHART_OUTPUT_DIR):
    os.makedirs(CHART_OUTPUT_DIR)

def get_controlled_components(results_path: str) -> List[str]:
    """
    从模拟结果文件中识别出所有被直接控制的物理组件ID。
    该函数通过查找列名中包含 'command' 或 'control_signal' 的模式来识别被控对象。

    Args:
        results_path (str): 模拟结果CSV文件的路径。

    Returns:
        List[str]: 一个包含被控组件ID的排序列表。
    """
    if not os.path.exists(results_path):
        print(f"警告: 结果文件 '{results_path}' 不存在，无法识别被控组件。")
        return []
        
    try:
        # 只读取表头以提高效率
        df_header = pd.read_csv(results_path, nrows=0)
        controlled_components: Set[str] = set()
        
        # 正则表达式查找包含 'command' 或 'control_signal' 的列
        # 它会捕获点号之前的部分作为组件ID
        control_pattern = re.compile(r"(\w+)\.(?:\w+_)?(?:command|control_signal)")
        
        for col in df_header.columns:
            match = control_pattern.match(col)
            if match:
                component_id = match.group(1)
                # 避免将 'agent' 本身误认为是被控的物理组件
                if 'agent' not in component_id:
                    controlled_components.add(component_id)
                    
        return sorted(list(controlled_components))
    except Exception as e:
        print(f"读取或解析结果文件 '{results_path}' 时出错: {e}")
        return []

def get_causal_variables(component_id: str, results_path: str) -> Dict[str, List[str]]:
    """
    对于给定的被控组件，自动识别与其相关的扰动、状态和控制变量。

    Args:
        component_id (str): 需要分析的组件ID。
        results_path (str): 模拟结果CSV文件的路径。

    Returns:
        Dict[str, List[str]]: 包含'disturbances', 'states', 'controls'键的字典。
    """
    if not os.path.exists(results_path):
        return {"disturbances": [], "states": [], "controls": []}
        
    df_header = pd.read_csv(results_path, nrows=0)
    all_columns = df_header.columns
    
    causal_map: Dict[str, List[str]] = {
        "disturbances": [],
        "states": [],
        "controls": []
    }
    
    # 基于命名约定的简化规则来识别变量类型
    for col in all_columns:
        # 首先检查列是否与当前组件相关
        if col.startswith(component_id + '.'):
            if 'inflow' in col:
                causal_map["disturbances"].append(col)
            elif 'water_level' in col or 'flow' in col or 'pressure' in col:
                causal_map["states"].append(col)
            elif 'command' in col:
                causal_map["controls"].append(col)
    
    # 补充查找可能与此组件相关的外部控制信号（例如来自上层Agent）
    for col in all_columns:
         if 'control_signal' in col and component_id in col:
              causal_map["controls"].append(col)

    return causal_map

def get_data_subset_as_json(results_path: str, columns: List[str]) -> str:
    """
    从结果CSV文件中读取指定的列，并将其转换为JSON字符串格式。

    Args:
        results_path (str): 模拟结果CSV文件的路径。
        columns (List[str]): 需要提取的列名列表。

    Returns:
        str: 包含所选数据的JSON字符串。
    """
    if not os.path.exists(results_path):
        return json.dumps([{"error": f"文件未找到: {results_path}"}])
        
    try:
        df = pd.read_csv(results_path)
        # 筛选出实际存在的列，避免因列名不存在而报错
        existing_columns = [col for col in columns if col in df.columns]
        if not existing_columns:
            return json.dumps([{"warning": "在结果文件中未找到任何请求的列。"}])
            
        subset_df = df[existing_columns]
        # orient='records' 生成 [{col: value}, {col: value}, ...] 的格式，适合LLM处理
        return subset_df.to_json(orient='records', indent=2)
    except Exception as e:
        return json.dumps([{"error": f"处理CSV文件时失败: {e}"}])

def plot_analysis_chart(variables: dict, results_path: str, title: str) -> str:
    """
    将扰动、状态和控制变量绘制在一张多Y轴的图表上。

    Args:
        variables (dict): 包含'disturbances', 'states', 'controls'列表的字典。
        results_path (str): 模拟结果CSV文件的路径。
        title (str): 图表的标题。

    Returns:
        str: 生成图表的文件路径。
    """
    if not os.path.exists(results_path):
        print(f"警告: 结果文件 '{results_path}' 不存在，无法绘图。")
        return ""

    df = pd.read_csv(results_path)
    
    fig, ax1 = plt.subplots(figsize=(18, 8))
    
    # 定义一组颜色
    colors = plt.cm.get_cmap('tab10').colors
    color_index = 0
    
    ax1.set_xlabel('时间步 (Time Step)')
    ax1.set_title(title, fontsize=16)

    # 绘制状态变量 (主Y轴)
    ax1.set_ylabel('状态 (States)', color=colors[color_index])
    for var in variables.get('states', []):
        if var in df.columns:
            ax1.plot(df.index, df[var], label=f'状态: {var}', color=colors[color_index])
    ax1.tick_params(axis='y', labelcolor=colors[color_index])
    color_index += 1
    
    axes = [ax1]

    # 绘制控制变量 (第二Y轴)
    if variables.get('controls'):
        ax2 = ax1.twinx()
        ax2.set_ylabel('控制 (Controls)', color=colors[color_index])
        for var in variables.get('controls', []):
            if var in df.columns:
                ax2.plot(df.index, df[var], label=f'控制: {var}', color=colors[color_index], linestyle='--')
        ax2.tick_params(axis='y', labelcolor=colors[color_index])
        axes.append(ax2)
        color_index += 1

    # 绘制扰动变量 (第三Y轴)
    if variables.get('disturbances'):
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.set_ylabel('扰动 (Disturbances)', color=colors[color_index])
        for var in variables.get('disturbances', []):
             if var in df.columns:
                ax3.plot(df.index, df[var], label=f'扰动: {var}', color=colors[color_index], linestyle=':')
        ax3.tick_params(axis='y', labelcolor=colors[color_index])
        axes.append(ax3)

    # 统一图例
    lines, labels = [], []
    for ax in axes:
        ax_lines, ax_labels = ax.get_legend_handles_labels()
        lines.extend(ax_lines)
        labels.extend(ax_labels)
    ax1.legend(lines, labels, loc='upper left')

    fig.tight_layout()
    
    # 安全地创建文件名并保存图表
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title) # 移除不安全的文件名字符
    chart_filename = f"{safe_title}.png"
    chart_path = os.path.join(CHART_OUTPUT_DIR, chart_filename)
    plt.savefig(chart_path)
    plt.close(fig)
    
    return chart_path

