#!/usr/bin/env python3
"""
PID Control Comparison Simulation

This script demonstrates different PID control strategies and their performance comparison
following CHS-SDK standards and three core principles:
1. No magic numbers, hardcoding, or implicit defaults
2. Physical model rationality
3. Generic solutions rather than case-specific implementations
"""

import sys
import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import YamlSimulationLoader

# 配置常量类 - 遵循禁止魔数规范
class SimulationConfig:
    """仿真配置常量类 - 管理所有仿真相关参数"""
    # 控制器设定点
    CANAL_1_SETPOINT = 5.0    # 渠道1水位设定点 (m)
    CANAL_2_SETPOINT = 4.5    # 渠道2水位设定点 (m) 
    CANAL_3_SETPOINT = 4.0    # 渠道3水位设定点 (m)
    
    # 文件命名常量
    RESULTS_FILE_PREFIX = "results_"
    RESULTS_FILE_SUFFIX = ".csv"
    PLOT_FILENAME = "pid_comparison_results.png"
    BACKUP_SUFFIX = ".bak"
    
    # 数据列名常量
    TIME_COLUMN = "time"
    WATER_LEVEL_SUFFIX = "_water_level"
    OPENING_SUFFIX = "_opening"
    
class PlotConfig:
    """绘图配置常量类 - 管理可视化相关参数"""
    FIGURE_SIZE = (18, 12)
    TITLE_FONT_SIZE = 16
    GRID_ALPHA = 0.3
    
    # 绘图样式
    PLOT_STYLE = 'seaborn-v0_8'  # 修复deprecated样式名称
    LINE_STYLES = ['-', '--', ':']
    
    # 颜色配置
    SETPOINT_COLOR = 'gray'
    SETPOINT_COLOR_ALT = 'black'
    SETPOINT_LINESTYLE = '--'
    SETPOINT_LINESTYLE_ALT = ':'
    
    # 图例和标签
    LEGEND_LOCATION = 'upper right'
    WATER_LEVEL_YLABEL = 'Water Level (m)'
    GATE_OPENING_YLABEL = 'Gate Opening (0-1)'
    TIME_XLABEL = 'Time (s)'
    
    # 图表标题
    WATER_LEVEL_TITLE = 'Canal Water Levels Comparison'
    GATE_OPENING_TITLE = 'Gate Openings Comparison'
    
    # 文件名常量
    PLOT_FILENAME = "pid_comparison_results.png"
    
class ScenarioConfig:
    """场景配置常量类 - 管理控制策略配置"""
    # 控制策略定义
    SCENARIOS = {
        "local_upstream": ["gate1_local_controller", "gate2_local_controller"],
        "distant_downstream": ["gate1_distant_controller", "gate2_distant_controller"],
        "mixed_control": ["gate1_mixed_controller", "gate2_mixed_controller"]
    }
    
    # 组件名称常量
    CANAL_COMPONENTS = ['canal_1', 'canal_2', 'canal_3']
    GATE_COMPONENTS = ['gate_1', 'gate_2']
    
    # 场景显示名称映射
    SCENARIO_DISPLAY_NAMES = {
        "local_upstream": "Local Upstream",
        "distant_downstream": "Distant Downstream", 
        "mixed_control": "Mixed Control"
    }
    
    # 文件操作常量
    TEMP_AGENTS_FILENAME = "temp_agents.yml"

def run_scenario(scenario_name: str, agent_ids: List[str], config_path: str) -> bool:
    """
    Runs a single simulation scenario and saves the results.
    
    Args:
        scenario_name: 场景名称
        agent_ids: 代理ID列表
        config_path: 配置文件路径
        
    Returns:
        是否成功执行
    """
    print(f"--- Running Scenario: {scenario_name} ---")
    
    config_path_obj = Path(config_path)
    agents_file = config_path_obj / 'agents.yml'
    temp_agents_file = config_path_obj / ScenarioConfig.TEMP_AGENTS_FILENAME
    backup_agents_file = config_path_obj / f'agents.yml{SimulationConfig.BACKUP_SUFFIX}'
    
    try:
        # 创建临时代理配置文件
        if not _create_scenario_agents_config(agents_file, temp_agents_file, agent_ids):
            print(f"Error: Failed to create scenario configuration for {scenario_name}")
            return False
            
        # 备份和替换原始配置文件
        if not _backup_and_replace_agents_config(agents_file, backup_agents_file, temp_agents_file):
            print(f"Error: Failed to setup agent configuration for {scenario_name}")
            return False
        
        # 加载和运行仿真
        if not _execute_simulation(config_path, scenario_name):
            print(f"Error: Simulation failed for {scenario_name}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error in scenario {scenario_name}: {e}")
        return False
        
    finally:
        # 清理临时文件
        _cleanup_temp_files(agents_file, backup_agents_file, temp_agents_file)

def _create_scenario_agents_config(agents_file: Path, temp_agents_file: Path, 
                                 agent_ids: List[str]) -> bool:
    """为当前场景创建临时代理配置文件"""
    try:
        with open(agents_file, 'r', encoding='utf-8') as f:
            all_agents_config = yaml.safe_load(f)
            
        scenario_agents_config = {
            'agents': [agent for agent in all_agents_config['agents'] 
                      if agent['id'] in agent_ids]
        }
        
        with open(temp_agents_file, 'w', encoding='utf-8') as f:
            yaml.dump(scenario_agents_config, f)
            
        return True
        
    except Exception as e:
        print(f"Error creating scenario config: {e}")
        return False

def _backup_and_replace_agents_config(agents_file: Path, backup_file: Path, 
                                    temp_file: Path) -> bool:
    """备份原始配置并替换为场景配置"""
    try:
        # 备份原始文件
        agents_file.rename(backup_file)
        # 使用临时文件替换
        temp_file.rename(agents_file)
        return True
        
    except Exception as e:
        print(f"Error managing config files: {e}")
        return False

def _execute_simulation(config_path: str, scenario_name: str) -> bool:
    """执行仿真并保存结果"""
    try:
        # 加载和运行仿真
        loader = YamlSimulationLoader(scenario_path=config_path)
        harness = loader.load()
        harness.run_mas_simulation()
        
        # 处理和保存结果
        return _save_simulation_results(harness.history, config_path, scenario_name)
        
    except Exception as e:
        print(f"Error executing simulation: {e}")
        return False

def _save_simulation_results(history: List[Dict[str, Any]], config_path: str, 
                           scenario_name: str) -> bool:
    """保存仿真结果到CSV文件"""
    try:
        if not history:
            print(f"Warning: No history recorded for scenario {scenario_name}")
            return False
            
        # 将嵌套数据转换为平坦结构
        flat_data = []
        for step_data in history:
            row = {SimulationConfig.TIME_COLUMN: step_data[SimulationConfig.TIME_COLUMN]}
            for comp_id, state in step_data.items():
                if comp_id != SimulationConfig.TIME_COLUMN:
                    for key, value in state.items():
                        row[f"{comp_id}_{key}"] = value
            flat_data.append(row)
            
        # 保存为CSV
        df = pd.DataFrame(flat_data)
        output_filename = f"{SimulationConfig.RESULTS_FILE_PREFIX}{scenario_name}{SimulationConfig.RESULTS_FILE_SUFFIX}"
        output_path = Path(config_path) / output_filename
        df.to_csv(output_path, index=False)
        
        print(f"Results for {scenario_name} saved to {output_filename}")
        return True
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return False

def _cleanup_temp_files(agents_file: Path, backup_file: Path, temp_file: Path):
    """清理临时文件并恢复原始配置"""
    try:
        # 恢复原始文件
        if agents_file.exists():
            agents_file.rename(temp_file)  # 先重命名为临时文件
        if backup_file.exists():
            backup_file.rename(agents_file)  # 恢复原始文件
        # 删除临时文件
        if temp_file.exists():
            temp_file.unlink()
            
    except Exception as e:
        print(f"Warning: Error cleaning up temp files: {e}")


def plot_results(scenarios: List[str], config_path: str) -> bool:
    """
    绘制所有场景的结果对比图
    
    Args:
        scenarios: 场景名称列表
        config_path: 配置文件路径
        
    Returns:
        是否成功生成图表
    """
    try:
        # 设置绘图样式 - 使用配置常量
        plt.style.use(PlotConfig.PLOT_STYLE)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PlotConfig.FIGURE_SIZE, sharex=True)

        # 生成颜色序列 - 避免直接使用cm.viridis
        num_scenarios = len(scenarios)
        color_indices = np.linspace(0, 1, num_scenarios * 2)
        viridis_cmap = plt.get_cmap('viridis')
        colors = [viridis_cmap(idx) for idx in color_indices]
        
        successfully_plotted = False
        
        for i, scenario_name in enumerate(scenarios):
            result_file = _get_result_filename(config_path, scenario_name)
            
            if not Path(result_file).exists():
                print(f"Warning: Results file not found for scenario: {scenario_name}")
                continue
                
            try:
                df = pd.read_csv(result_file)
                _plot_scenario_data(ax1, ax2, df, scenario_name, i, colors)
                successfully_plotted = True
                
            except Exception as e:
                print(f"Error plotting scenario {scenario_name}: {e}")
                continue

        if not successfully_plotted:
            print("Error: No scenarios were successfully plotted")
            return False
            
        # 添加设定点线条 - 使用配置常量
        _add_setpoint_lines(ax1)
        
        # 配置图表 - 使用配置常量
        _configure_plot_axes(ax1, ax2)
        
        # 保存图表
        return _save_plot(fig, config_path)
        
    except Exception as e:
        print(f"Error generating comparison plot: {e}")
        return False
        
def _get_result_filename(config_path: str, scenario_name: str) -> str:
    """获取结果文件名"""
    filename = f"{SimulationConfig.RESULTS_FILE_PREFIX}{scenario_name}{SimulationConfig.RESULTS_FILE_SUFFIX}"
    return str(Path(config_path) / filename)

def _plot_scenario_data(ax1, ax2, df: pd.DataFrame, scenario_name: str, 
                       scenario_index: int, colors: List) -> None:
    """绘制单个场景的数据"""
    display_name = ScenarioConfig.SCENARIO_DISPLAY_NAMES.get(scenario_name, scenario_name)
    line_style = PlotConfig.LINE_STYLES[scenario_index % len(PlotConfig.LINE_STYLES)]
    
    # 绘制水位数据
    for j, canal in enumerate(ScenarioConfig.CANAL_COMPONENTS):
        water_level_col = f"{canal}{SimulationConfig.WATER_LEVEL_SUFFIX}"
        if water_level_col in df.columns:
            color = colors[scenario_index * 2 + (j % 2)]
            label = f"{canal.replace('_', ' ').title()} ({display_name})"
            ax1.plot(df[SimulationConfig.TIME_COLUMN], df[water_level_col], 
                    label=label, linestyle=line_style, color=color)
    
    # 绘制闸门开度数据
    for j, gate in enumerate(ScenarioConfig.GATE_COMPONENTS):
        opening_col = f"{gate}{SimulationConfig.OPENING_SUFFIX}"
        if opening_col in df.columns:
            color = colors[scenario_index * 2 + j]
            label = f"{gate.replace('_', ' ').title()} ({display_name})"
            ax2.plot(df[SimulationConfig.TIME_COLUMN], df[opening_col], 
                    label=label, linestyle=line_style, color=color)

def _add_setpoint_lines(ax1) -> None:
    """添加设定点线条"""
    setpoints = [
        (SimulationConfig.CANAL_1_SETPOINT, f'Setpoint Canal 1 ({SimulationConfig.CANAL_1_SETPOINT}m)'),
        (SimulationConfig.CANAL_2_SETPOINT, f'Setpoint Canal 2 ({SimulationConfig.CANAL_2_SETPOINT}m)'),
        (SimulationConfig.CANAL_3_SETPOINT, f'Setpoint Canal 3 ({SimulationConfig.CANAL_3_SETPOINT}m)')
    ]
    
    colors = [PlotConfig.SETPOINT_COLOR, PlotConfig.SETPOINT_COLOR_ALT, PlotConfig.SETPOINT_COLOR]
    linestyles = [PlotConfig.SETPOINT_LINESTYLE, PlotConfig.SETPOINT_LINESTYLE, PlotConfig.SETPOINT_LINESTYLE_ALT]
    
    for i, (setpoint, label) in enumerate(setpoints):
        ax1.axhline(y=setpoint, color=colors[i], linestyle=linestyles[i], label=label)
        
def _configure_plot_axes(ax1, ax2) -> None:
    """配置图表坐标轴"""
    # 配置水位图
    ax1.set_title(PlotConfig.WATER_LEVEL_TITLE, fontsize=PlotConfig.TITLE_FONT_SIZE)
    ax1.set_ylabel(PlotConfig.WATER_LEVEL_YLABEL)
    ax1.legend(loc=PlotConfig.LEGEND_LOCATION)
    ax1.grid(True, alpha=PlotConfig.GRID_ALPHA)
    
    # 配置闸门开度图
    ax2.set_title(PlotConfig.GATE_OPENING_TITLE, fontsize=PlotConfig.TITLE_FONT_SIZE)
    ax2.set_ylabel(PlotConfig.GATE_OPENING_YLABEL)
    ax2.set_xlabel(PlotConfig.TIME_XLABEL)
    ax2.legend(loc=PlotConfig.LEGEND_LOCATION)
    ax2.grid(True, alpha=PlotConfig.GRID_ALPHA)
    
def _save_plot(fig, config_path: str) -> bool:
    """保存图表文件"""
    try:
        plt.tight_layout()
        plot_path = Path(config_path) / PlotConfig.PLOT_FILENAME
        fig.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)  # 释放内存
        print(f"Comparison plot saved to {plot_path}")
        return True
        
    except Exception as e:
        print(f"Error saving plot: {e}")
        return False


def main() -> bool:
    """
    主函数：运行所有PID控制比较场景并生成对比图表
    
    Returns:
        是否成功执行所有场景
    """
    try:
        print("=== PID Control Comparison Simulation ===")
        print("Following three core principles:")
        print("1. No magic numbers, hardcoding, or implicit defaults")
        print("2. Physical model rationality")
        print("3. Generic solutions rather than case-specific implementations")
        print()
        
        # 获取配置路径
        config_path = os.path.dirname(__file__)
        
        # 验证配置目录
        if not _validate_config_directory(config_path):
            print("Error: Invalid configuration directory")
            return False
        
        # 执行所有场景 - 使用配置常量
        successful_scenarios = []
        failed_scenarios = []
        
        for scenario_name, agent_ids in ScenarioConfig.SCENARIOS.items():
            print(f"\n--- Processing Scenario: {scenario_name} ---")
            
            if run_scenario(scenario_name, agent_ids, config_path):
                successful_scenarios.append(scenario_name)
                print(f"✓ Scenario {scenario_name} completed successfully")
            else:
                failed_scenarios.append(scenario_name)
                print(f"✗ Scenario {scenario_name} failed")
        
        # 报告执行结果
        _report_execution_summary(successful_scenarios, failed_scenarios)
        
        # 生成对比图表
        if successful_scenarios:
            print("\n--- Generating Comparison Plot ---")
            if plot_results(successful_scenarios, config_path):
                print("✓ Comparison plot generated successfully")
            else:
                print("✗ Failed to generate comparison plot")
                return False
        else:
            print("Warning: No successful scenarios to plot")
            return False
            
        print("\n=== PID Control Comparison Completed ===")
        return len(failed_scenarios) == 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return False
        
def _validate_config_directory(config_path: str) -> bool:
    """验证配置目录是否有效"""
    try:
        config_dir = Path(config_path)
        if not config_dir.exists():
            print(f"Error: Configuration directory does not exist: {config_path}")
            return False
            
        # 检查必要的配置文件
        agents_file = config_dir / 'agents.yml'
        if not agents_file.exists():
            print(f"Error: agents.yml not found in {config_path}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error validating config directory: {e}")
        return False
        
def _report_execution_summary(successful_scenarios: List[str], 
                             failed_scenarios: List[str]) -> None:
    """报告执行结果摘要"""
    total_scenarios = len(successful_scenarios) + len(failed_scenarios)
    
    print(f"\n--- Execution Summary ---")
    print(f"Total scenarios: {total_scenarios}")
    print(f"Successful: {len(successful_scenarios)}")
    print(f"Failed: {len(failed_scenarios)}")
    
    if successful_scenarios:
        print(f"Successful scenarios: {', '.join(successful_scenarios)}")
        
    if failed_scenarios:
        print(f"Failed scenarios: {', '.join(failed_scenarios)}")


if __name__ == "__main__":
    main()
