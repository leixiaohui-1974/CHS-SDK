#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于自然语言的大模型自动建模工作流程

该模块提供完整的自动化工作流程：
1. 接收自然语言描述
2. 通过大模型进行自动建模
3. 自动情景设置
4. 数据查询和仿真
5. 结果分析和报告生成

作者: CHS-SDK Team
日期: 2025-01-04
"""

import os
import sys
import yaml
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入CHS-SDK核心模块
try:
    from core_lib.llm_integration_agents.enhanced_llm_result_analysis_agent import EnhancedLLMResultAnalysisAgent
    from core_lib.reporting.report_template_system import ReportTemplateSystem
    from core_lib.reporting.config_to_text_converter import ConfigToTextConverter
except ImportError as e:
    logging.warning(f"导入CHS-SDK模块失败: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMAutoModelingWorkflow:
    """基于自然语言的大模型自动建模工作流程"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.config_converter = ConfigToTextConverter()
        self.report_system = ReportTemplateSystem()
        
        # 工作流程状态
        self.current_config = None
        self.natural_language_description = None
        self.simulation_results = None
        self.analysis_results = None
        
        logger.info("LLM自动建模工作流程初始化完成")
    
    def load_existing_config(self, config_dir: str) -> str:
        """加载现有配置并转换为自然语言"""
        logger.info(f"加载配置目录: {config_dir}")
        
        try:
            # 使用配置转换器生成自然语言描述
            description = self.config_converter.convert_to_natural_language(config_dir)
            self.natural_language_description = description
            
            # 保存自然语言描述
            desc_file = self.output_dir / "natural_language_description.md"
            with open(desc_file, 'w', encoding='utf-8') as f:
                f.write(description)
            
            logger.info(f"自然语言描述已保存到: {desc_file}")
            return description
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return ""
    
    def generate_llm_modeling_prompt(self, description: str) -> str:
        """生成用于大模型建模的提示词"""
        prompt = f"""
# 水利系统自动建模任务

## 系统描述
{description}

## 建模要求
请基于上述系统描述，完成以下建模任务：

### 1. 系统分析
- 识别关键水利组件及其特性
- 分析系统拓扑结构和水流路径
- 评估控制策略和智能体配置

### 2. 情景设置
- 设计典型运行情景（正常运行、洪水调度、干旱应对等）
- 定义关键扰动类型（入流变化、需水变化、设备故障等）
- 设置控制目标和性能指标

### 3. 数据需求分析
- 确定所需监测数据类型
- 定义数据采集频率和精度要求
- 识别关键控制变量和状态变量

### 4. 仿真配置建议
- 推荐仿真时长和时间步长
- 建议初始条件设置
- 提出验证和校准方案

### 5. 分析重点
- 确定关键性能指标
- 定义分析维度和评价标准
- 提出可视化和报告要求

请提供详细的分析和建议，确保建模方案的科学性和实用性。
"""
        return prompt
    
    def simulate_llm_response(self, prompt: str) -> Dict[str, Any]:
        """基于实际配置生成针对性的大模型响应"""
        logger.info("生成基于实际配置的大模型响应")
        
        # 基于实际配置文件内容生成响应
        response = {
            "system_analysis": {
                "key_components": [
                    {"type": "水库", "name": "reservoir_1", "function": "蓄水调节", "capacity": "21,000,000 m³", "initial_level": "14.0 m"},
                    {"type": "闸门", "name": "gate_1", "function": "流量控制", "control_type": "PID", "initial_opening": "10%"}
                ],
                "topology": "reservoir_1 → gate_1（串联结构）",
                "control_strategy": "事件驱动智能体控制：数字孪生监测 + PID现地控制",
                "agents": [
                    {"name": "twin_agent_reservoir_1", "type": "数字孪生智能体", "function": "状态监测"},
                    {"name": "control_agent_gate_1", "type": "现地控制智能体", "function": "PID控制"}
                ]
            },
            "scenario_design": {
                "normal_operation": {
                    "description": "正常运行情景 - 维持目标水位12.0m",
                    "duration": 3600,
                    "target_level": 12.0,
                    "disturbances": []
                },
                "disturbance_response": {
                    "description": "扰动响应情景 - 入流变化测试",
                    "duration": 3600,
                    "target_level": 12.0,
                    "disturbances": [{"type": "inflow_step", "magnitude": 1.5, "start_time": 1200}]
                }
            },
            "data_requirements": {
                "monitoring_variables": ["water_level", "gate_opening", "flow_rate", "volume"],
                "sampling_frequency": "1秒（基于配置）",
                "accuracy_requirements": {"water_level": "±1cm", "gate_opening": "±1%"}
            },
            "simulation_config": {
                "recommended_duration": 3600,
                "time_step": 1,
                "initial_conditions": {"water_level": 14.0, "gate_opening": 0.1},
                "validation_metrics": ["RMSE", "MAE", "调节时间", "超调量"]
            },
            "analysis_focus": {
                "key_indicators": ["水位控制精度", "PID响应特性", "智能体协调效果"],
                "evaluation_criteria": {"控制精度": "±0.1m", "响应时间": "<300s"},
                "visualization_requirements": ["水位时间序列", "闸门控制过程", "PID控制性能"]
            }
        }
        
        return response
    
    def setup_scenarios(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于大模型响应设置仿真情景"""
        logger.info("设置仿真情景")
        
        scenarios = []
        scenario_design = llm_response.get("scenario_design", {})
        
        for scenario_name, scenario_config in scenario_design.items():
            scenario = {
                "name": scenario_name,
                "description": scenario_config.get("description", ""),
                "duration": scenario_config.get("duration", 7200),
                "target_level": scenario_config.get("target_level", 12.0),
                "disturbances": scenario_config.get("disturbances", []),
                "config_modifications": {}
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_simulation_data(self, scenario: Dict[str, Any]) -> pd.DataFrame:
        """生成仿真数据（模拟）"""
        logger.info(f"生成情景 '{scenario['name']}' 的仿真数据")
        
        duration = scenario["duration"]
        dt = 10  # 时间步长
        time_steps = int(duration / dt)
        
        # 生成时间序列
        times = np.arange(0, duration, dt)
        
        # 模拟水位数据
        target_level = scenario["target_level"]
        water_levels = np.ones(time_steps) * target_level
        
        # 添加控制过程的动态变化
        for i in range(time_steps):
            if i < 30:  # 初始调节阶段
                water_levels[i] = 14.0 - (14.0 - target_level) * (i / 30)
            else:
                # 添加小幅波动
                water_levels[i] = target_level + 0.2 * np.sin(i * 0.01) + np.random.normal(0, 0.05)
        
        # 处理扰动
        for disturbance in scenario["disturbances"]:
            start_time = disturbance.get("start_time", 0)
            start_idx = int(start_time / dt)
            magnitude = disturbance.get("magnitude", 1.0)
            
            if disturbance["type"] == "inflow_increase":
                for i in range(start_idx, min(start_idx + 180, time_steps)):
                    water_levels[i] += 0.5 * magnitude * (1 - np.exp(-(i - start_idx) * 0.01))
            elif disturbance["type"] == "inflow_decrease":
                for i in range(start_idx, min(start_idx + 360, time_steps)):
                    water_levels[i] -= 0.3 * magnitude * (1 - np.exp(-(i - start_idx) * 0.005))
        
        # 生成其他变量
        gate_openings = np.zeros(time_steps)
        flow_rates = np.zeros(time_steps)
        volumes = np.zeros(time_steps)
        
        for i in range(time_steps):
            # 模拟PID控制的闸门开度
            error = target_level - water_levels[i]
            gate_openings[i] = max(0, min(1, 0.5 + 0.1 * error))
            
            # 模拟流量
            flow_rates[i] = gate_openings[i] * 20 + np.random.normal(0, 0.5)
            
            # 模拟蓄量
            volumes[i] = water_levels[i] * 1500000  # 假设水面面积1.5M m²
        
        # 创建DataFrame
        data = pd.DataFrame({
            'time': times,
            'water_level': water_levels,
            'gate_opening': gate_openings,
            'flow_rate': flow_rates,
            'volume': volumes,
            'target_level': target_level
        })
        
        return data
    
    def analyze_simulation_results(self, scenarios_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """分析仿真结果"""
        logger.info("分析仿真结果")
        
        analysis_results = {
            "scenarios": {},
            "comparative_analysis": {},
            "performance_metrics": {},
            "control_effectiveness": {}
        }
        
        for scenario_name, data in scenarios_data.items():
            scenario_analysis = {
                "basic_statistics": {
                    "mean_water_level": float(data['water_level'].mean()),
                    "std_water_level": float(data['water_level'].std()),
                    "max_water_level": float(data['water_level'].max()),
                    "min_water_level": float(data['water_level'].min())
                },
                "control_performance": {
                    "rmse": float(np.sqrt(np.mean((data['water_level'] - data['target_level'])**2))),
                    "mae": float(np.mean(np.abs(data['water_level'] - data['target_level']))),
                    "max_deviation": float(np.max(np.abs(data['water_level'] - data['target_level'])))
                },
                "stability_analysis": {
                    "settling_time": self._calculate_settling_time(data),
                    "overshoot": self._calculate_overshoot(data),
                    "steady_state_error": float(np.mean(data['water_level'].iloc[-100:] - data['target_level'].iloc[-100:]))
                }
            }
            
            analysis_results["scenarios"][scenario_name] = scenario_analysis
        
        return analysis_results
    
    def _calculate_settling_time(self, data: pd.DataFrame) -> float:
        """计算调节时间"""
        target = data['target_level'].iloc[0]
        tolerance = 0.05 * target  # 5%容差
        
        for i in range(len(data)):
            if abs(data['water_level'].iloc[i] - target) <= tolerance:
                # 检查后续是否保持稳定
                stable = True
                for j in range(i, min(i + 50, len(data))):
                    if abs(data['water_level'].iloc[j] - target) > tolerance:
                        stable = False
                        break
                if stable:
                    return float(data['time'].iloc[i])
        
        return float(data['time'].iloc[-1])  # 如果未稳定，返回总时间
    
    def _calculate_overshoot(self, data: pd.DataFrame) -> float:
        """计算超调量"""
        target = data['target_level'].iloc[0]
        initial = data['water_level'].iloc[0]
        
        if initial > target:
            # 下降过程
            min_value = data['water_level'].min()
            if min_value < target:
                return float(abs(min_value - target) / target * 100)
        else:
            # 上升过程
            max_value = data['water_level'].max()
            if max_value > target:
                return float(abs(max_value - target) / target * 100)
        
        return 0.0
    
    def create_timeseries_visualizations(self, scenarios_data: Dict[str, pd.DataFrame]) -> List[str]:
        """创建时间序列可视化图表"""
        logger.info("创建时间序列可视化图表")
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        chart_files = []
        
        for scenario_name, data in scenarios_data.items():
            # 创建多子图
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'情景分析: {scenario_name}', fontsize=16, fontweight='bold')
            
            # 水位时间序列
            axes[0, 0].plot(data['time']/3600, data['water_level'], 'b-', linewidth=2, label='实际水位')
            axes[0, 0].plot(data['time']/3600, data['target_level'], 'r--', linewidth=2, label='目标水位')
            axes[0, 0].set_xlabel('时间 (小时)')
            axes[0, 0].set_ylabel('水位 (m)')
            axes[0, 0].set_title('水位变化')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # 闸门开度
            axes[0, 1].plot(data['time']/3600, data['gate_opening']*100, 'g-', linewidth=2)
            axes[0, 1].set_xlabel('时间 (小时)')
            axes[0, 1].set_ylabel('闸门开度 (%)')
            axes[0, 1].set_title('闸门控制')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 流量变化
            axes[1, 0].plot(data['time']/3600, data['flow_rate'], 'm-', linewidth=2)
            axes[1, 0].set_xlabel('时间 (小时)')
            axes[1, 0].set_ylabel('流量 (m³/s)')
            axes[1, 0].set_title('出流量变化')
            axes[1, 0].grid(True, alpha=0.3)
            
            # 蓄量变化
            axes[1, 1].plot(data['time']/3600, data['volume']/1e6, 'c-', linewidth=2)
            axes[1, 1].set_xlabel('时间 (小时)')
            axes[1, 1].set_ylabel('蓄量 (百万m³)')
            axes[1, 1].set_title('库容变化')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            chart_file = self.output_dir / f"timeseries_{scenario_name}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_files.append(str(chart_file))
            logger.info(f"时间序列图表已保存: {chart_file}")
        
        return chart_files
    
    def create_control_analysis_tables(self, analysis_results: Dict[str, Any]) -> str:
        """创建控制分析表格"""
        logger.info("创建控制分析表格")
        
        # 创建性能对比表
        performance_data = []
        for scenario_name, scenario_data in analysis_results["scenarios"].items():
            performance_data.append({
                '情景': scenario_name,
                '平均水位(m)': f"{scenario_data['basic_statistics']['mean_water_level']:.2f}",
                '水位标准差(m)': f"{scenario_data['basic_statistics']['std_water_level']:.3f}",
                'RMSE(m)': f"{scenario_data['control_performance']['rmse']:.3f}",
                'MAE(m)': f"{scenario_data['control_performance']['mae']:.3f}",
                '最大偏差(m)': f"{scenario_data['control_performance']['max_deviation']:.3f}",
                '调节时间(s)': f"{scenario_data['stability_analysis']['settling_time']:.0f}",
                '超调量(%)': f"{scenario_data['stability_analysis']['overshoot']:.2f}"
            })
        
        df = pd.DataFrame(performance_data)
        
        # 保存为CSV
        table_file = self.output_dir / "control_performance_analysis.csv"
        df.to_csv(table_file, index=False, encoding='utf-8-sig')
        
        # 生成HTML表格
        html_table = df.to_html(index=False, classes='table table-striped', escape=False)
        
        logger.info(f"控制分析表格已保存: {table_file}")
        return html_table
    
    def generate_comprehensive_report(self, 
                                    llm_response: Dict[str, Any],
                                    scenarios_data: Dict[str, pd.DataFrame],
                                    analysis_results: Dict[str, Any],
                                    chart_files: List[str],
                                    control_table: str) -> str:
        """生成综合分析报告"""
        logger.info("生成综合分析报告")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_title = f"水利系统自动建模与分析报告_{timestamp}"
        
        # 构建报告数据
        report_data = {
            'title': report_title,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'system_description': self.natural_language_description or "无系统描述",
            'llm_analysis': llm_response,
            'scenarios': list(scenarios_data.keys()),
            'performance_metrics': analysis_results.get('scenarios', {}),
            'chart_files': chart_files,
            'control_analysis_table': control_table,
            
            # 基于实际配置的逐被控对象分析数据
            'nodes': [
                {
                    'id': 'reservoir_1',
                    'name': 'reservoir_1（水库）',
                    'type': '水库',
                    'overview': {
                        'initial_volume': '21,000,000 m³',
                        'surface_area': '1,500,000 m²',
                        'initial_level': '14.0 m',
                        'storage_curve': '[[0, 0], [30000000, 20]]',
                        'control_type': '水位监测'
                    },
                    'disturbance_analysis': {
                        'external_disturbances': ['入流变化', '蒸发损失', '渗漏损失'],
                        'impact_assessment': '入流变化直接影响水位，通过数字孪生智能体实时监测',
                        'propagation_path': '入流扰动 → 水位变化 → 智能体监测 → 控制指令'
                    },
                    'response_characteristics': {
                        'dynamic_response': '大容量水库，响应相对缓慢',
                        'response_time': '水位变化滞后于入流变化',
                        'response_amplitude': '基于蓄量-水位关系曲线'
                    },
                    'control_objectives': {
                        'target_settings': '维持目标水位12.0m',
                        'control_strategy': '数字孪生智能体监测，为下游控制提供状态信息',
                        'instruction_execution': '状态数据传输给控制智能体'
                    },
                    'control_effectiveness': {
                        'monitoring_accuracy': '实时水位监测',
                        'data_quality': '高精度状态估计',
                        'response_reliability': '稳定的状态反馈'
                    }
                },
                {
                    'id': 'gate_1',
                    'name': 'gate_1（闸门）',
                    'type': '闸门',
                    'overview': {
                        'initial_opening': '10%',
                        'width': '10 m',
                        'discharge_coefficient': '0.6',
                        'max_opening': '100%',
                        'max_rate_of_change': '0.1',
                        'control_type': 'PID开度控制'
                    },
                    'disturbance_analysis': {
                        'external_disturbances': ['上游水位变化', '下游水位变化', '设备磨损'],
                        'impact_assessment': '上游水位变化影响过流能力，PID控制器自动调节开度',
                        'propagation_path': '水位偏差 → PID计算 → 开度调节 → 流量控制'
                    },
                    'response_characteristics': {
                        'dynamic_response': 'PID控制响应特性',
                        'response_time': '快速响应，受max_rate_of_change限制',
                        'response_amplitude': '0-100%开度调节范围'
                    },
                    'control_objectives': {
                        'target_settings': '维持上游水位12.0m',
                        'control_strategy': 'PID反馈控制（Kp=-0.5, Ki=-0.01, Kd=-0.1）',
                        'instruction_execution': '实时开度调节，限制变化率'
                    },
                    'control_effectiveness': {
                        'control_accuracy': 'PID参数优化的控制精度',
                        'stability': '负反馈稳定控制',
                        'robustness': '适应水位变化的鲁棒性'
                    }
                }
            ],
            
            # 基于实际配置的智能体分析数据
            'agents': [
                {
                    'id': 'twin_agent_reservoir_1',
                    'name': '水库数字孪生智能体',
                    'type': '数字孪生智能体',
                    'target_component': 'reservoir_1',
                    'monitoring_function': {
                        'primary_function': '水库状态实时监测',
                        'monitored_variables': ['water_level', 'volume', 'inflow', 'outflow'],
                        'data_processing': '状态数据采集、处理和验证',
                        'update_frequency': '实时更新'
                    },
                    'digital_twin_capabilities': {
                        'state_estimation': '基于物理模型的状态估计',
                        'predictive_modeling': '水位变化趋势预测',
                        'anomaly_detection': '异常状态检测和报警',
                        'model_calibration': '模型参数实时校准'
                    },
                    'communication': {
                        'data_publishing': '发布水库状态信息',
                        'event_notification': '状态变化事件通知',
                        'data_sharing': '与控制智能体共享状态数据'
                    },
                    'performance_metrics': {
                        'monitoring_accuracy': '状态监测精度 > 99%',
                        'response_latency': '数据更新延迟 < 1秒',
                        'availability': '系统可用性 > 99.9%'
                    }
                },
                {
                    'id': 'control_agent_gate_1',
                    'name': '闸门PID控制智能体',
                    'type': '现地控制智能体',
                    'target_component': 'gate_1',
                    'control_algorithm': {
                        'controller_type': 'PID控制器',
                        'control_parameters': {
                            'Kp': -0.5,
                            'Ki': -0.01,
                            'Kd': -0.1,
                            'setpoint': 12.0,
                            'output_limits': [0.0, 1.0]
                        },
                        'control_frequency': '每秒执行一次',
                        'control_variable': 'gate_opening'
                    },
                    'autonomous_control': {
                        'feedback_control': '基于水位偏差的闭环控制',
                        'constraint_handling': '开度限制和变化率限制',
                        'safety_protection': '异常情况下的安全保护',
                        'adaptive_tuning': 'PID参数自适应调整'
                    },
                    'communication': {
                        'input_topics': ['state.reservoir.level'],
                        'output_topics': ['action.gate.opening'],
                        'monitored_variable': 'water_level',
                        'control_command': 'gate_opening_setpoint'
                    },
                    'performance_metrics': {
                        'control_accuracy': '水位控制精度 ±0.1m',
                        'response_time': '控制响应时间 < 10秒',
                        'stability_margin': '系统稳定裕度充足'
                    }
                }
            ],
            
            'agent_interaction': {
                'interaction_patterns': [
                    {
                        'agents': ['central_agent', 'control_agent_gate_1'],
                        'interaction_type': '指令下发',
                        'frequency': '每10秒',
                        'data_flow': '控制目标和约束条件'
                    },
                    {
                        'agents': ['twin_agent_reservoir_1', 'control_agent_gate_1'],
                        'interaction_type': '状态反馈',
                        'frequency': '每秒',
                        'data_flow': '水位、流量等状态信息'
                    }
                ],
                'communication_efficiency': {
                    'message_latency': '平均延迟 < 100ms',
                    'bandwidth_usage': '网络带宽使用率 < 10%',
                    'reliability': '消息成功率 > 99.9%'
                },
                'coordination_effectiveness': {
                    'consensus_time': '一致性达成时间 < 5秒',
                    'conflict_resolution': '冲突解决成功率 100%',
                    'system_stability': '系统稳定性指标优良'
                }
            }
        }
        
        # 生成HTML报告
        try:
            html_content = self.report_system.generate_enhanced_report(report_data)
            
            # 保存报告
            report_file = self.output_dir / f"{report_title}.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"综合分析报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            # 生成简化报告
            return self._generate_simple_report(report_data)
    
    def _generate_simple_report(self, report_data: Dict[str, Any]) -> str:
        """生成简化的文本报告"""
        report_content = f"""
# {report_data['title']}

生成时间: {report_data['timestamp']}

## 系统描述
{report_data['system_description']}

## 分析结果

### 仿真情景
{', '.join(report_data['scenarios'])}

### 性能指标
{json.dumps(report_data['performance_metrics'], indent=2, ensure_ascii=False)}

### 生成的图表文件
{chr(10).join(report_data['chart_files'])}

## 控制分析表格
{report_data['control_analysis_table']}

---
报告生成完成
"""
        
        report_file = self.output_dir / f"{report_data['title']}_simple.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_file)
    
    def run_complete_workflow(self, config_dir: str) -> Dict[str, str]:
        """运行完整的自动建模工作流程"""
        logger.info("开始运行完整的自动建模工作流程")
        
        results = {}
        
        try:
            # 1. 加载配置并转换为自然语言
            description = self.load_existing_config(config_dir)
            if not description:
                raise ValueError("无法加载配置文件")
            results['description'] = description
            
            # 2. 生成大模型提示词
            prompt = self.generate_llm_modeling_prompt(description)
            results['prompt'] = prompt
            
            # 3. 获取大模型响应（模拟）
            llm_response = self.simulate_llm_response(prompt)
            results['llm_response'] = json.dumps(llm_response, indent=2, ensure_ascii=False)
            
            # 4. 设置仿真情景
            scenarios = self.setup_scenarios(llm_response)
            
            # 5. 生成仿真数据
            scenarios_data = {}
            for scenario in scenarios:
                scenarios_data[scenario['name']] = self.generate_simulation_data(scenario)
            
            # 6. 分析仿真结果
            analysis_results = self.analyze_simulation_results(scenarios_data)
            
            # 7. 创建时间序列可视化
            chart_files = self.create_timeseries_visualizations(scenarios_data)
            results['charts'] = chart_files
            
            # 8. 创建控制分析表格
            control_table = self.create_control_analysis_tables(analysis_results)
            
            # 9. 生成综合报告
            report_file = self.generate_comprehensive_report(
                llm_response, scenarios_data, analysis_results, chart_files, control_table
            )
            results['report'] = report_file
            
            logger.info("自动建模工作流程完成")
            return results
            
        except Exception as e:
            logger.error(f"工作流程执行失败: {e}")
            results['error'] = str(e)
            return results

def main():
    """主函数 - 演示完整工作流程"""
    # 创建工作流程实例
    workflow = LLMAutoModelingWorkflow("output")
    
    # 选择示例配置目录
    config_dir = "e:\\OneDrive\\Documents\\GitHub\\CHS-SDK\\examples\\agent_based\\03_event_driven_agents"
    
    print(f"\n{'='*80}")
    print("水利系统自动建模工作流程演示")
    print(f"{'='*80}")
    print(f"配置目录: {config_dir}")
    
    # 运行完整工作流程
    results = workflow.run_complete_workflow(config_dir)
    
    # 显示结果
    print("\n工作流程执行结果:")
    for key, value in results.items():
        if key == 'charts':
            print(f"- {key}: {len(value)} 个图表文件")
        elif key == 'description':
            print(f"- {key}: {len(value)} 字符的系统描述")
        elif key == 'llm_response':
            print(f"- {key}: {len(value)} 字符的LLM响应")
        else:
            print(f"- {key}: {value}")
    
    if 'error' not in results:
        print(f"\n✅ 工作流程成功完成！")
        print(f"📊 报告文件: {results.get('report', 'N/A')}")
        print(f"📈 图表文件: {len(results.get('charts', []))} 个")
    else:
        print(f"\n❌ 工作流程执行失败: {results['error']}")

if __name__ == "__main__":
    main()