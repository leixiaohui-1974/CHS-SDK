#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制对象过程线和时间序列详细分析演示程序

本程序用于详细分析水利系统中控制对象的过程线和时间序列数据，
包括控制目标、控制指令、执行器状态、控制误差和性能评估。

作者: AI Assistant
创建时间: 2025-09-04
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import tempfile

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ControlObjectsAnalyzer:
    """
    控制对象过程线和时间序列分析器
    
    用于分析水利系统中控制对象的详细过程线数据，
    包括控制目标跟踪、指令执行、状态监测和性能评估。
    """
    
    def __init__(self, config_path: str):
        """
        初始化分析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.control_objects = self._extract_control_objects()
        self.agents = self._extract_agents()
        
        # 创建输出目录
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"成功加载配置文件: {config_path}")
        print(f"发现控制对象: {len(self.control_objects)} 个")
        print(f"发现智能体: {len(self.agents)} 个")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"无法加载配置文件 {self.config_path}: {e}")
    
    def _extract_control_objects(self) -> List[Dict[str, Any]]:
        """提取控制对象信息"""
        control_objects = []
        
        # 从组件中提取控制对象（闸门、泵站等）
        components = self.config.get('components', [])
        for comp in components:
            comp_type = comp.get('type', '')
            if comp_type in ['gate', 'pump', 'valve', 'turbine']:
                control_objects.append(comp)
        
        return control_objects
    
    def _extract_agents(self) -> List[Dict[str, Any]]:
        """提取智能体信息"""
        return self.config.get('agents', [])
    
    def analyze_single_control_object(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个控制对象的详细过程线
        
        Args:
            control_obj: 控制对象配置
            
        Returns:
            分析结果字典
        """
        obj_id = control_obj.get('id', 'unknown')
        obj_type = control_obj.get('type', 'unknown')
        
        # 1. 基本信息分析
        basic_info = self._analyze_basic_info(control_obj)
        
        # 2. 控制目标分析
        control_targets = self._analyze_control_targets(control_obj)
        
        # 3. 控制指令分析
        control_commands = self._analyze_control_commands(control_obj)
        
        # 4. 执行器状态分析
        actuator_status = self._analyze_actuator_status(control_obj)
        
        # 5. 控制误差分析
        control_errors = self._analyze_control_errors(control_obj)
        
        # 6. 性能指标评估
        performance_metrics = self._evaluate_performance(control_obj)
        
        # 7. 生成过程线图表
        chart_path = self._generate_control_chart(control_obj)
        
        return {
            'id': obj_id,
            'type': obj_type,
            'basic_info': basic_info,
            'control_targets': control_targets,
            'control_commands': control_commands,
            'actuator_status': actuator_status,
            'control_errors': control_errors,
            'performance_metrics': performance_metrics,
            'chart_path': chart_path
        }
    
    def _analyze_basic_info(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """分析控制对象基本信息"""
        obj_type = control_obj.get('type', 'unknown')
        params = control_obj.get('parameters', {})
        
        info = {
            'type': obj_type,
            'param_count': len(params),
            'key_params': {}
        }
        
        # 根据类型提取关键参数
        if obj_type == 'gate':
            info['key_params'] = {
                'max_opening': params.get('max_opening', '100%'),
                'response_time': params.get('response_time', '2分钟'),
                'control_precision': params.get('control_precision', '±1%')
            }
        elif obj_type == 'pump':
            info['key_params'] = {
                'rated_flow': params.get('rated_flow', '50 m³/s'),
                'rated_head': params.get('rated_head', '20 m'),
                'efficiency': params.get('efficiency', '85%')
            }
        elif obj_type == 'valve':
            info['key_params'] = {
                'diameter': params.get('diameter', '1.5 m'),
                'pressure_rating': params.get('pressure_rating', '1.6 MPa'),
                'flow_coefficient': params.get('flow_coefficient', '0.8')
            }
        
        return info
    
    def _analyze_control_targets(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """分析控制目标"""
        obj_type = control_obj.get('type', 'unknown')
        
        # 模拟控制目标数据
        targets = {
            'target_type': '',
            'target_range': '',
            'setpoint_changes': [],
            'tracking_requirements': {}
        }
        
        if obj_type == 'gate':
            targets.update({
                'target_type': '开度控制',
                'target_range': '0-100%',
                'setpoint_changes': [
                    {'time': '00:00', 'target': '30%', 'reason': '夜间低流量'},
                    {'time': '06:00', 'target': '60%', 'reason': '晨峰用水'},
                    {'time': '12:00', 'target': '80%', 'reason': '日间高峰'},
                    {'time': '18:00', 'target': '50%', 'reason': '晚峰调节'},
                    {'time': '22:00', 'target': '35%', 'reason': '夜间回落'}
                ],
                'tracking_requirements': {
                    'precision': '±2%',
                    'response_time': '< 3分钟',
                    'stability': '±1%'
                }
            })
        elif obj_type == 'pump':
            targets.update({
                'target_type': '流量控制',
                'target_range': '0-50 m³/s',
                'setpoint_changes': [
                    {'time': '00:00', 'target': '15 m³/s', 'reason': '夜间基础流量'},
                    {'time': '06:00', 'target': '35 m³/s', 'reason': '晨峰供水'},
                    {'time': '12:00', 'target': '45 m³/s', 'reason': '日间高峰'},
                    {'time': '18:00', 'target': '30 m³/s', 'reason': '晚峰调节'},
                    {'time': '22:00', 'target': '20 m³/s', 'reason': '夜间回落'}
                ],
                'tracking_requirements': {
                    'precision': '±5%',
                    'response_time': '< 5分钟',
                    'stability': '±2%'
                }
            })
        
        return targets
    
    def _analyze_control_commands(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """分析控制指令"""
        obj_type = control_obj.get('type', 'unknown')
        
        commands = {
            'command_type': '',
            'command_range': '',
            'command_frequency': '',
            'command_characteristics': {}
        }
        
        if obj_type == 'gate':
            commands.update({
                'command_type': '开度指令',
                'command_range': '0-100%',
                'command_frequency': '每10秒更新',
                'command_characteristics': {
                    'typical_step': '2-5%',
                    'max_rate': '10%/分钟',
                    'dead_zone': '±0.5%',
                    'hysteresis': '1%'
                }
            })
        elif obj_type == 'pump':
            commands.update({
                'command_type': '转速指令',
                'command_range': '0-1500 rpm',
                'command_frequency': '每5秒更新',
                'command_characteristics': {
                    'typical_step': '50-100 rpm',
                    'max_rate': '200 rpm/分钟',
                    'dead_zone': '±10 rpm',
                    'hysteresis': '20 rpm'
                }
            })
        
        return commands
    
    def _analyze_actuator_status(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行器状态"""
        obj_type = control_obj.get('type', 'unknown')
        
        status = {
            'status_variables': [],
            'health_indicators': {},
            'fault_detection': {}
        }
        
        if obj_type == 'gate':
            status.update({
                'status_variables': [
                    {'name': '实际开度', 'unit': '%', 'range': '0-100'},
                    {'name': '驱动力矩', 'unit': 'N·m', 'range': '0-5000'},
                    {'name': '位置反馈', 'unit': 'mm', 'range': '0-2000'},
                    {'name': '电机电流', 'unit': 'A', 'range': '0-50'}
                ],
                'health_indicators': {
                    'mechanical_wear': '正常',
                    'electrical_status': '良好',
                    'lubrication': '充足',
                    'vibration_level': '低'
                },
                'fault_detection': {
                    'position_error': '< 2%',
                    'overcurrent': '未检测到',
                    'mechanical_jam': '无',
                    'communication': '正常'
                }
            })
        elif obj_type == 'pump':
            status.update({
                'status_variables': [
                    {'name': '实际转速', 'unit': 'rpm', 'range': '0-1500'},
                    {'name': '出口压力', 'unit': 'MPa', 'range': '0-2.5'},
                    {'name': '电机功率', 'unit': 'kW', 'range': '0-200'},
                    {'name': '轴承温度', 'unit': '°C', 'range': '20-80'}
                ],
                'health_indicators': {
                    'pump_efficiency': '85%',
                    'bearing_condition': '良好',
                    'seal_status': '正常',
                    'vibration_level': '低'
                },
                'fault_detection': {
                    'cavitation': '未检测到',
                    'overheating': '无',
                    'imbalance': '正常',
                    'seal_leakage': '无'
                }
            })
        
        return status
    
    def _analyze_control_errors(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """分析控制误差"""
        # 模拟控制误差数据
        np.random.seed(42)
        
        # 生成24小时的误差数据
        time_points = 144  # 10分钟间隔
        errors = np.random.normal(0, 0.5, time_points)  # 正态分布误差
        
        # 添加一些系统性偏差
        trend = 0.1 * np.sin(np.linspace(0, 4*np.pi, time_points))
        errors += trend
        
        error_analysis = {
            'mean_error': float(np.mean(errors)),
            'std_error': float(np.std(errors)),
            'max_error': float(np.max(np.abs(errors))),
            'rms_error': float(np.sqrt(np.mean(errors**2))),
            'error_distribution': {
                'within_1_sigma': float(np.sum(np.abs(errors) < np.std(errors)) / len(errors) * 100),
                'within_2_sigma': float(np.sum(np.abs(errors) < 2*np.std(errors)) / len(errors) * 100),
                'outliers': float(np.sum(np.abs(errors) > 3*np.std(errors)) / len(errors) * 100)
            },
            'error_trends': {
                'systematic_bias': '轻微正偏',
                'periodic_component': '存在日周期',
                'random_component': '正常范围',
                'drift_tendency': '稳定'
            }
        }
        
        return error_analysis
    
    def _evaluate_performance(self, control_obj: Dict[str, Any]) -> Dict[str, Any]:
        """评估控制性能"""
        obj_type = control_obj.get('type', 'unknown')
        
        # 模拟性能指标
        np.random.seed(hash(control_obj.get('id', '')) % 2**32)
        
        base_performance = {
            'mae': np.random.uniform(0.05, 0.15),
            'rmse': np.random.uniform(0.08, 0.20),
            'stability_index': np.random.uniform(0.85, 0.95),
            'efficiency': np.random.uniform(0.88, 0.96)
        }
        
        # 根据类型调整性能
        if obj_type == 'gate':
            performance_rating = self._rate_performance(base_performance['efficiency'])
            recommendations = self._generate_gate_recommendations(base_performance)
        elif obj_type == 'pump':
            performance_rating = self._rate_performance(base_performance['efficiency'])
            recommendations = self._generate_pump_recommendations(base_performance)
        else:
            performance_rating = self._rate_performance(base_performance['efficiency'])
            recommendations = ['建议优化控制参数', '建议增强监测能力']
        
        return {
            'metrics': base_performance,
            'rating': performance_rating,
            'recommendations': recommendations
        }
    
    def _rate_performance(self, efficiency: float) -> Dict[str, str]:
        """评级性能"""
        if efficiency >= 0.95:
            return {
                'overall': '优秀 ⭐⭐⭐⭐⭐',
                'precision': '高精度',
                'stability': '高稳定',
                'response': '快速响应'
            }
        elif efficiency >= 0.90:
            return {
                'overall': '良好 ⭐⭐⭐⭐',
                'precision': '高精度',
                'stability': '中等稳定',
                'response': '正常响应'
            }
        elif efficiency >= 0.85:
            return {
                'overall': '一般 ⭐⭐⭐',
                'precision': '中等精度',
                'stability': '中等稳定',
                'response': '正常响应'
            }
        else:
            return {
                'overall': '需改进 ⭐⭐',
                'precision': '低精度',
                'stability': '低稳定',
                'response': '响应较慢'
            }
    
    def _generate_gate_recommendations(self, performance: Dict[str, float]) -> List[str]:
        """生成闸门控制建议"""
        recommendations = []
        
        if performance['mae'] > 0.10:
            recommendations.append('建议调整PID参数，提高控制精度')
        if performance['stability_index'] < 0.90:
            recommendations.append('建议增强抗扰动能力，提高系统稳定性')
        if performance['efficiency'] < 0.90:
            recommendations.append('建议优化控制策略，提高响应速度')
        
        if not recommendations:
            recommendations.append('控制性能良好，建议保持当前参数设置')
        
        return recommendations
    
    def _generate_pump_recommendations(self, performance: Dict[str, float]) -> List[str]:
        """生成泵站控制建议"""
        recommendations = []
        
        if performance['mae'] > 0.12:
            recommendations.append('建议优化变频控制策略，提高流量控制精度')
        if performance['stability_index'] < 0.88:
            recommendations.append('建议增强系统阻尼，减少振荡')
        if performance['efficiency'] < 0.92:
            recommendations.append('建议优化运行工况，提高泵站效率')
        
        if not recommendations:
            recommendations.append('泵站运行状态良好，建议定期维护保养')
        
        return recommendations
    
    def _generate_control_chart(self, control_obj: Dict[str, Any]) -> str:
        """生成控制对象过程线图表"""
        obj_id = control_obj.get('id', 'unknown')
        obj_type = control_obj.get('type', 'unknown')
        
        # 生成时间序列数据
        time_points = 144  # 24小时，10分钟间隔
        time_hours = np.linspace(0, 24, time_points)
        
        # 设置随机种子确保可重现性
        np.random.seed(hash(obj_id) % 2**32)
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{obj_id} ({obj_type}) 控制过程线分析', fontsize=16, fontweight='bold')
        
        # 子图1: 控制目标与实际值对比
        ax1 = axes[0, 0]
        if obj_type == 'gate':
            target = 50 + 20 * np.sin(2*np.pi*time_hours/24) + 10 * np.sin(2*np.pi*time_hours/12)
            actual = target + np.random.normal(0, 2, time_points)
            ax1.plot(time_hours, target, 'r-', linewidth=2, label='目标开度')
            ax1.plot(time_hours, actual, 'b-', linewidth=1.5, label='实际开度')
            ax1.set_ylabel('开度 (%)')
            ax1.set_title('开度控制跟踪')
        elif obj_type == 'pump':
            target = 30 + 15 * np.sin(2*np.pi*time_hours/24) + 5 * np.sin(2*np.pi*time_hours/8)
            actual = target + np.random.normal(0, 1.5, time_points)
            ax1.plot(time_hours, target, 'r-', linewidth=2, label='目标流量')
            ax1.plot(time_hours, actual, 'b-', linewidth=1.5, label='实际流量')
            ax1.set_ylabel('流量 (m³/s)')
            ax1.set_title('流量控制跟踪')
        else:
            # 默认情况
            target = 50 + 20 * np.sin(2*np.pi*time_hours/24)
            actual = target + np.random.normal(0, 2, time_points)
            ax1.plot(time_hours, target, 'r-', linewidth=2, label='目标值')
            ax1.plot(time_hours, actual, 'b-', linewidth=1.5, label='实际值')
            ax1.set_ylabel('控制量')
            ax1.set_title('控制跟踪')
        
        ax1.set_xlabel('时间 (小时)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 子图2: 控制指令
        ax2 = axes[0, 1]
        if obj_type == 'gate':
            command = target + np.random.normal(0, 1, time_points)
            ax2.plot(time_hours, command, 'g-', linewidth=1.5, label='开度指令')
            ax2.set_ylabel('指令值 (%)')
            ax2.set_title('控制指令输出')
        elif obj_type == 'pump':
            command = 1000 + 300 * (target / 50)  # 转速指令
            command += np.random.normal(0, 20, time_points)
            ax2.plot(time_hours, command, 'g-', linewidth=1.5, label='转速指令')
            ax2.set_ylabel('转速 (rpm)')
            ax2.set_title('控制指令输出')
        else:
            # 默认情况
            command = target + np.random.normal(0, 1, time_points)
            ax2.plot(time_hours, command, 'g-', linewidth=1.5, label='控制指令')
            ax2.set_ylabel('指令值')
            ax2.set_title('控制指令输出')
        
        ax2.set_xlabel('时间 (小时)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 子图3: 控制误差
        ax3 = axes[1, 0]
        error = actual - target  # 计算控制误差
        
        ax3.plot(time_hours, error, 'orange', linewidth=1.5, label='控制误差')
        ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax3.fill_between(time_hours, error, alpha=0.3, color='orange')
        ax3.set_xlabel('时间 (小时)')
        ax3.set_ylabel('误差')
        ax3.set_title('控制误差过程线')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 子图4: 执行器状态
        ax4 = axes[1, 1]
        if obj_type == 'gate':
            motor_current = 20 + 10 * np.abs(np.diff(np.concatenate([[target[0]], target]))) + np.random.normal(0, 2, time_points)
            ax4.plot(time_hours, motor_current, 'purple', linewidth=1.5, label='电机电流')
            ax4.set_ylabel('电流 (A)')
            ax4.set_title('执行器状态监测')
        elif obj_type == 'pump':
            power = 100 + 50 * (actual / 50) + np.random.normal(0, 5, time_points)
            ax4.plot(time_hours, power, 'purple', linewidth=1.5, label='电机功率')
            ax4.set_ylabel('功率 (kW)')
            ax4.set_title('执行器状态监测')
        else:
            # 默认情况
            status_value = 50 + 20 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 3, time_points)
            ax4.plot(time_hours, status_value, 'purple', linewidth=1.5, label='状态监测')
            ax4.set_ylabel('状态值')
            ax4.set_title('执行器状态监测')
        
        ax4.set_xlabel('时间 (小时)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        chart_filename = os.path.join(self.output_dir, f'{obj_id}_控制过程线分析.png')
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_filename
    
    def generate_comprehensive_report(self) -> str:
        """生成综合分析报告"""
        report_lines = []
        
        # 报告头部
        report_lines.extend([
            "# 控制对象过程线和时间序列详细分析报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**配置文件**: {os.path.basename(self.config_path)}",
            ""
        ])
        
        # 系统概览
        type_counts = {}
        for obj in self.control_objects:
            obj_type = obj.get('type', 'unknown')
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        report_lines.extend([
            "## 系统概览",
            "",
            f"本次分析共涉及 **{len(self.control_objects)}** 个控制对象，包括：",
            ""
        ])
        
        for obj_type, count in type_counts.items():
            type_name = {
                'gate': '闸门',
                'pump': '泵站', 
                'valve': '阀门',
                'turbine': '水轮机'
            }.get(obj_type, obj_type)
            report_lines.append(f"- **{obj_type}**: {count} 个")
        
        report_lines.extend([
            "",
            "每个控制对象都进行了详细的过程线分析，包括控制目标、控制指令、执行器状态、控制误差和性能评估五个维度。",
            "",
            ""
        ])
        
        # 逐个分析控制对象
        for i, control_obj in enumerate(self.control_objects, 1):
            print(f"正在分析第 {i}/{len(self.control_objects)} 个控制对象: {control_obj.get('id', 'unknown')}")
            
            analysis_result = self.analyze_single_control_object(control_obj)
            
            # 添加到报告
            report_lines.extend(self._format_control_analysis(analysis_result))
            report_lines.append("---")
            report_lines.append("")
        
        # 综合分析总结
        report_lines.extend(self._generate_summary())
        
        # 保存报告
        report_path = os.path.join(self.output_dir, "控制对象详细过程线分析报告.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return report_path
    
    def _format_control_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        """格式化单个控制对象的分析结果"""
        lines = []
        
        obj_id = analysis['id']
        obj_type = analysis['type']
        basic_info = analysis['basic_info']
        control_targets = analysis['control_targets']
        control_commands = analysis['control_commands']
        actuator_status = analysis['actuator_status']
        control_errors = analysis['control_errors']
        performance = analysis['performance_metrics']
        
        type_name = {
            'gate': '闸门',
            'pump': '泵站',
            'valve': '阀门', 
            'turbine': '水轮机'
        }.get(obj_type, obj_type)
        
        lines.extend([
            f"## {obj_id} ({type_name}) 详细过程线分析",
            "",
            "### 1. 基本信息",
            "",
            f"- **对象类型**: {obj_type}",
            f"- **配置参数**: {basic_info['param_count']} 个"
        ])
        
        # 添加关键参数
        for key, value in basic_info['key_params'].items():
            param_name = {
                'max_opening': '最大开度',
                'response_time': '响应时间',
                'control_precision': '控制精度',
                'rated_flow': '额定流量',
                'rated_head': '额定扬程',
                'efficiency': '效率',
                'diameter': '直径',
                'pressure_rating': '压力等级',
                'flow_coefficient': '流量系数'
            }.get(key, key)
            lines.append(f"- **{param_name}**: {value}")
        
        lines.extend([
            "",
            "### 2. 控制目标分析",
            "",
            f"**控制类型**: {control_targets['target_type']}",
            "",
            f"**目标范围**: {control_targets['target_range']}",
            "",
            "**设定值变化**:",
            ""
        ])
        
        for change in control_targets['setpoint_changes']:
            lines.append(f"- **{change['time']}**: {change['target']} ({change['reason']})")
        
        lines.extend([
            "",
            "**跟踪要求**:",
            ""
        ])
        
        for key, value in control_targets['tracking_requirements'].items():
            req_name = {
                'precision': '控制精度',
                'response_time': '响应时间',
                'stability': '稳定性'
            }.get(key, key)
            lines.append(f"- **{req_name}**: {value}")
        
        lines.extend([
            "",
            "### 3. 控制指令分析",
            "",
            f"**指令类型**: {control_commands['command_type']}",
            "",
            f"**指令范围**: {control_commands['command_range']}",
            "",
            f"**更新频率**: {control_commands['command_frequency']}",
            "",
            "**指令特征**:",
            ""
        ])
        
        for key, value in control_commands['command_characteristics'].items():
            char_name = {
                'typical_step': '典型步长',
                'max_rate': '最大变化率',
                'dead_zone': '死区',
                'hysteresis': '回滞'
            }.get(key, key)
            lines.append(f"- **{char_name}**: {value}")
        
        lines.extend([
            "",
            "### 4. 执行器状态分析",
            "",
            "**状态变量**:",
            ""
        ])
        
        for var in actuator_status['status_variables']:
            lines.append(f"- **{var['name']}**: {var['range']} {var['unit']}")
        
        lines.extend([
            "",
            "**健康指标**:",
            ""
        ])
        
        for key, value in actuator_status['health_indicators'].items():
            health_name = {
                'mechanical_wear': '机械磨损',
                'electrical_status': '电气状态',
                'lubrication': '润滑状态',
                'vibration_level': '振动水平',
                'pump_efficiency': '泵效率',
                'bearing_condition': '轴承状态',
                'seal_status': '密封状态'
            }.get(key, key)
            lines.append(f"- **{health_name}**: {value}")
        
        lines.extend([
            "",
            "**故障检测**:",
            ""
        ])
        
        for key, value in actuator_status['fault_detection'].items():
            fault_name = {
                'position_error': '位置误差',
                'overcurrent': '过电流',
                'mechanical_jam': '机械卡阻',
                'communication': '通信状态',
                'cavitation': '汽蚀',
                'overheating': '过热',
                'imbalance': '不平衡',
                'seal_leakage': '密封泄漏'
            }.get(key, key)
            lines.append(f"- **{fault_name}**: {value}")
        
        lines.extend([
            "",
            "### 5. 控制误差分析",
            "",
            "**误差统计**:",
            "",
            f"- **平均误差**: {control_errors['mean_error']:.3f}",
            f"- **标准差**: {control_errors['std_error']:.3f}",
            f"- **最大误差**: {control_errors['max_error']:.3f}",
            f"- **均方根误差**: {control_errors['rms_error']:.3f}",
            "",
            "**误差分布**:",
            "",
            f"- **1σ范围内**: {control_errors['error_distribution']['within_1_sigma']:.1f}%",
            f"- **2σ范围内**: {control_errors['error_distribution']['within_2_sigma']:.1f}%",
            f"- **异常值**: {control_errors['error_distribution']['outliers']:.1f}%",
            "",
            "**误差趋势**:",
            ""
        ])
        
        for key, value in control_errors['error_trends'].items():
            trend_name = {
                'systematic_bias': '系统偏差',
                'periodic_component': '周期成分',
                'random_component': '随机成分',
                'drift_tendency': '漂移趋势'
            }.get(key, key)
            lines.append(f"- **{trend_name}**: {value}")
        
        lines.extend([
            "",
            "### 6. 性能指标评估",
            "",
            "**关键性能指标**:",
            "",
            f"- **平均绝对误差 (MAE)**: {performance['metrics']['mae']:.3f}",
            f"- **均方根误差 (RMSE)**: {performance['metrics']['rmse']:.3f}",
            f"- **控制稳定性指标**: {performance['metrics']['stability_index']:.3f}",
            f"- **控制效率**: {performance['metrics']['efficiency']:.3f}",
            "",
            "**性能等级评定**:",
            "",
            f"- **综合评级**: {performance['rating']['overall']}",
            f"- **控制精度**: {performance['rating']['precision']}",
            f"- **系统稳定性**: {performance['rating']['stability']}",
            f"- **响应特性**: {performance['rating']['response']}",
            "",
            "**改进建议**:",
            ""
        ])
        
        for rec in performance['recommendations']:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "### 7. 过程线图表",
            "",
            f"![{obj_id}控制过程线分析]({analysis['chart_path']})",
            "",
            "**图表说明**: 上图展示了该控制对象的详细过程线分析，包括控制目标跟踪、控制指令输出、控制误差过程线和执行器状态监测四个方面的时间序列数据。",
            ""
        ])
        
        return lines
    
    def _generate_summary(self) -> List[str]:
        """生成综合分析总结"""
        lines = [
            "## 综合分析总结",
            "",
            "### 系统整体性能",
            "",
            "通过对所有控制对象的详细分析，可以得出以下结论：",
            "",
            "1. **控制精度**: 大部分控制对象的控制精度满足设计要求",
            "2. **响应速度**: 系统响应速度符合实际运行需求",
            "3. **稳定性表现**: 整体稳定性良好，抗扰动能力较强",
            "4. **执行器状态**: 执行器运行状态正常，健康指标良好",
            "",
            "### 优化建议",
            "",
            "1. **参数调优**: 建议对控制精度较低的对象进行PID参数优化",
            "2. **预测控制**: 可考虑引入模型预测控制，提高控制性能",
            "3. **故障预警**: 加强执行器健康监测，建立故障预警机制",
            "4. **协调控制**: 优化多个控制对象之间的协调控制策略",
            "5. **维护计划**: 制定定期维护计划，确保设备长期稳定运行"
        ]
        
        return lines

def create_demo_config():
    """创建演示配置"""
    return {
        "metadata": {
            "name": "智能水利调度系统",
            "version": "2.0",
            "description": "基于多智能体的水利系统智能调度与控制"
        },
        "components": [
            {
                "id": "main_gate",
                "type": "gate",
                "parameters": {
                    "max_opening": "100%",
                    "response_time": "2分钟",
                    "control_precision": "±1%",
                    "location": "主渠道入口",
                    "rated_flow": "80 m³/s",
                    "gate_type": "平板闸门"
                }
            },
            {
                "id": "pump_station_1",
                "type": "pump",
                "parameters": {
                    "rated_flow": "50 m³/s",
                    "rated_head": "20 m",
                    "efficiency": "85%",
                    "pump_count": 3,
                    "control_mode": "变频调速"
                }
            },
            {
                "id": "control_valve_1",
                "type": "valve",
                "parameters": {
                    "diameter": "1.5 m",
                    "pressure_rating": "1.6 MPa",
                    "flow_coefficient": "0.8",
                    "valve_type": "蝶阀"
                }
            },
            {
                "id": "turbine_1",
                "type": "turbine",
                "parameters": {
                    "rated_power": "10 MW",
                    "rated_head": "50 m",
                    "rated_flow": "25 m³/s",
                    "efficiency": "90%"
                }
            }
        ],
        "agents": [
            {
                "id": "gate_controller",
                "type": "PIDController",
                "target_component": "main_gate"
            },
            {
                "id": "pump_controller",
                "type": "AdvancedController", 
                "target_component": "pump_station_1"
            },
            {
                "id": "valve_controller",
                "type": "PIDController",
                "target_component": "control_valve_1"
            },
            {
                "id": "turbine_controller",
                "type": "OptimalController",
                "target_component": "turbine_1"
            }
        ]
    }

def main():
    """主函数"""
    print("开始控制对象过程线和时间序列分析...")
    
    # 创建模拟配置
    config = create_demo_config()
    
    # 创建临时配置文件
    temp_config_path = "temp_config.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    try:
        # 创建分析器
        analyzer = ControlObjectsAnalyzer(temp_config_path)
        
        # 生成综合报告
        report_path = analyzer.generate_comprehensive_report()
        
        print(f"\n分析完成！报告已保存到: {report_path}")
        print(f"共分析了 {len(analyzer.control_objects)} 个控制对象")
        print(f"生成了 {len(analyzer.control_objects)} 个详细过程线图表")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

if __name__ == "__main__":
    main()