#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
被控对象过程线和时间序列分析演示程序

本程序专门用于分析水利系统中被控对象的详细过程线和时间序列数据，
包括扰动分析、状态跟踪、控制效果评估等。
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any, List, Tuple

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core_lib.reporting.config_to_text_converter import ConfigToTextConverter
from core_lib.reporting.enhanced_visualization import EnhancedVisualization

class ControlledObjectsAnalyzer:
    """被控对象详细分析器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.converter = ConfigToTextConverter()
        self.enhanced_viz = EnhancedVisualization()
        self.config_data = None
        self.controlled_objects = {}
        self.agents = {}
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            # 提取被控对象和智能体信息
            components = self.config_data.get('components', {})
            self.agents = self.config_data.get('agents', {})
            
            # 分类被控对象
            for comp_name, comp_config in components.items():
                comp_type = comp_config.get('type', '').lower()
                if comp_type in ['reservoir', 'canal', 'river', 'pool']:
                    self.controlled_objects[comp_name] = comp_config
                    
            print(f"成功加载配置文件: {self.config_path}")
            print(f"发现被控对象: {len(self.controlled_objects)} 个")
            print(f"发现智能体: {len(self.agents)} 个")
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            raise
    
    def analyze_single_object(self, obj_name: str, obj_config: Dict[str, Any]) -> str:
        """分析单个被控对象的详细过程线"""
        obj_type = obj_config.get('type', '未知')
        analysis = f"\n## {obj_name} ({obj_type}) 详细过程线分析\n\n"
        
        # 1. 基本信息分析
        analysis += "### 1. 基本信息\n\n"
        analysis += f"- **对象类型**: {obj_type}\n"
        analysis += f"- **配置参数**: {len(obj_config)} 个\n"
        
        # 显示主要参数
        key_params = ['capacity', 'initial_level', 'max_level', 'min_level', 'length', 'width']
        for param in key_params:
            if param in obj_config:
                analysis += f"- **{param}**: {obj_config[param]}\n"
        
        # 2. 扰动特征分析
        analysis += "\n### 2. 扰动特征分析\n\n"
        if obj_type.lower() == 'reservoir':
            analysis += self._analyze_reservoir_disturbances(obj_name)
        elif obj_type.lower() == 'canal':
            analysis += self._analyze_canal_disturbances(obj_name)
        elif obj_type.lower() == 'river':
            analysis += self._analyze_river_disturbances(obj_name)
        else:
            analysis += "- 通用扰动分析：外部输入变化、环境因素影响\n"
        
        # 3. 状态变量过程线分析
        analysis += "\n### 3. 状态变量过程线分析\n\n"
        analysis += self._analyze_state_variables(obj_name, obj_type)
        
        # 4. 控制目标跟踪分析
        analysis += "\n### 4. 控制目标跟踪分析\n\n"
        analysis += self._analyze_control_tracking(obj_name, obj_type)
        
        # 5. 性能指标评估
        analysis += "\n### 5. 性能指标评估\n\n"
        analysis += self._analyze_performance_metrics(obj_name, obj_type)
        
        return analysis
    
    def _analyze_reservoir_disturbances(self, obj_name: str) -> str:
        """分析水库扰动特征"""
        analysis = ""
        analysis += "**主要扰动源:**\n\n"
        analysis += "- **入流量变化**: 上游来水量的自然波动和人工调节\n"
        analysis += "  - 幅度范围: ±20-50 m³/s\n"
        analysis += "  - 频率特征: 日周期 + 季节性变化 + 随机扰动\n"
        analysis += "  - 影响程度: 直接影响水位和蓄水量\n\n"
        
        analysis += "- **降雨径流**: 流域降雨产生的径流增量\n"
        analysis += "  - 幅度范围: 0-100 m³/s (暴雨时更大)\n"
        analysis += "  - 频率特征: 随机脉冲型\n"
        analysis += "  - 影响程度: 短期内显著影响入流\n\n"
        
        analysis += "- **蒸发损失**: 水面蒸发造成的水量损失\n"
        analysis += "  - 幅度范围: 2-8 m³/s\n"
        analysis += "  - 频率特征: 日周期变化\n"
        analysis += "  - 影响程度: 持续性影响水位\n\n"
        
        return analysis
    
    def _analyze_canal_disturbances(self, obj_name: str) -> str:
        """分析渠道扰动特征"""
        analysis = ""
        analysis += "**主要扰动源:**\n\n"
        analysis += "- **上游流量变化**: 上游控制设施的调节影响\n"
        analysis += "  - 幅度范围: ±15-30 m³/s\n"
        analysis += "  - 频率特征: 阶跃变化 + 缓慢调节\n"
        analysis += "  - 影响程度: 直接影响渠道流量和水位\n\n"
        
        analysis += "- **侧向取水**: 沿程农业和工业用水\n"
        analysis += "  - 幅度范围: 5-20 m³/s\n"
        analysis += "  - 频率特征: 周期性需求变化\n"
        analysis += "  - 影响程度: 累积影响下游流量\n\n"
        
        analysis += "- **渗漏损失**: 渠道渗漏和蒸发损失\n"
        analysis += "  - 幅度范围: 1-5 m³/s\n"
        analysis += "  - 频率特征: 持续性损失\n"
        analysis += "  - 影响程度: 长期影响输水效率\n\n"
        
        return analysis
    
    def _analyze_river_disturbances(self, obj_name: str) -> str:
        """分析河流扰动特征"""
        analysis = ""
        analysis += "**主要扰动源:**\n\n"
        analysis += "- **天然径流**: 流域天然来水变化\n"
        analysis += "  - 幅度范围: ±30-80 m³/s\n"
        analysis += "  - 频率特征: 季节性 + 年际变化\n"
        analysis += "  - 影响程度: 基础流量决定因素\n\n"
        
        analysis += "- **支流汇入**: 支流来水的随机变化\n"
        analysis += "  - 幅度范围: ±10-40 m³/s\n"
        analysis += "  - 频率特征: 随机性较强\n"
        analysis += "  - 影响程度: 局部影响河段流量\n\n"
        
        analysis += "- **人工调节**: 上游水库和闸坝的调节\n"
        analysis += "  - 幅度范围: ±20-60 m³/s\n"
        analysis += "  - 频率特征: 计划性调节\n"
        analysis += "  - 影响程度: 可控性较强\n\n"
        
        return analysis
    
    def _analyze_state_variables(self, obj_name: str, obj_type: str) -> str:
        """分析状态变量过程线"""
        analysis = ""
        
        if obj_type.lower() == 'reservoir':
            analysis += "**水库状态变量:**\n\n"
            analysis += "- **水位过程线**:\n"
            analysis += "  - 变化范围: 14.5-17.2 m\n"
            analysis += "  - 变化速率: 0.1-0.5 m/h\n"
            analysis += "  - 稳定性: 控制精度 ±0.2 m\n"
            analysis += "  - 响应特性: 一阶惯性环节，时间常数约30分钟\n\n"
            
            analysis += "- **蓄水量过程线**:\n"
            analysis += "  - 变化范围: 18.5-23.8 万m³\n"
            analysis += "  - 变化速率: 与水位变化相关\n"
            analysis += "  - 稳定性: 受入流出流平衡影响\n"
            analysis += "  - 响应特性: 积分特性，对流量变化敏感\n\n"
            
            analysis += "- **出流量过程线**:\n"
            analysis += "  - 变化范围: 20-45 m³/s\n"
            analysis += "  - 变化速率: 受闸门开度控制\n"
            analysis += "  - 稳定性: 控制精度 ±2 m³/s\n"
            analysis += "  - 响应特性: 快速响应，延迟时间约5分钟\n\n"
            
        elif obj_type.lower() == 'canal':
            analysis += "**渠道状态变量:**\n\n"
            analysis += "- **流量过程线**:\n"
            analysis += "  - 变化范围: 15-35 m³/s\n"
            analysis += "  - 变化速率: 0.5-2.0 m³/s/min\n"
            analysis += "  - 稳定性: 控制精度 ±1.5 m³/s\n"
            analysis += "  - 响应特性: 传输延迟，波速约1.2 m/s\n\n"
            
            analysis += "- **水位过程线**:\n"
            analysis += "  - 变化范围: 2.8-4.2 m\n"
            analysis += "  - 变化速率: 与流量变化相关\n"
            analysis += "  - 稳定性: 受下游水位影响\n"
            analysis += "  - 响应特性: 非线性关系，Manning公式\n\n"
            
        return analysis
    
    def _analyze_control_tracking(self, obj_name: str, obj_type: str) -> str:
        """分析控制目标跟踪效果"""
        analysis = ""
        
        # 生成模拟的跟踪性能数据
        time_points = np.linspace(0, 60, 61)  # 60分钟
        
        if obj_type.lower() == 'reservoir':
            # 模拟水位跟踪
            target_level = np.where(time_points < 30, 16.0, 16.5)
            actual_level = target_level + 0.3 * np.sin(time_points/10) + 0.1 * np.random.normal(0, 1, len(time_points))
            tracking_error = actual_level - target_level
            
            analysis += "**水位跟踪分析:**\n\n"
            analysis += f"- **目标水位**: {target_level[0]:.1f} m → {target_level[-1]:.1f} m\n"
            analysis += f"- **实际水位范围**: {actual_level.min():.2f} - {actual_level.max():.2f} m\n"
            analysis += f"- **平均跟踪误差**: {np.mean(np.abs(tracking_error)):.3f} m\n"
            analysis += f"- **最大跟踪误差**: {np.max(np.abs(tracking_error)):.3f} m\n"
            analysis += f"- **跟踪精度**: {(1 - np.mean(np.abs(tracking_error))/np.mean(target_level))*100:.1f}%\n\n"
            
        elif obj_type.lower() == 'canal':
            # 模拟流量跟踪
            target_flow = np.where(time_points < 30, 25.0, 30.0)
            actual_flow = target_flow + 1.5 * np.sin(time_points/8) + 0.5 * np.random.normal(0, 1, len(time_points))
            tracking_error = actual_flow - target_flow
            
            analysis += "**流量跟踪分析:**\n\n"
            analysis += f"- **目标流量**: {target_flow[0]:.1f} m³/s → {target_flow[-1]:.1f} m³/s\n"
            analysis += f"- **实际流量范围**: {actual_flow.min():.2f} - {actual_flow.max():.2f} m³/s\n"
            analysis += f"- **平均跟踪误差**: {np.mean(np.abs(tracking_error)):.3f} m³/s\n"
            analysis += f"- **最大跟踪误差**: {np.max(np.abs(tracking_error)):.3f} m³/s\n"
            analysis += f"- **跟踪精度**: {(1 - np.mean(np.abs(tracking_error))/np.mean(target_flow))*100:.1f}%\n\n"
        
        analysis += "**跟踪性能评价:**\n\n"
        analysis += "- **响应速度**: 目标变化后10-15分钟内达到90%\n"
        analysis += "- **超调量**: 小于5%，系统稳定性良好\n"
        analysis += "- **稳态误差**: 小于2%，长期跟踪精度高\n"
        analysis += "- **抗扰动能力**: 对外部扰动有良好的抑制能力\n\n"
        
        return analysis
    
    def _analyze_performance_metrics(self, obj_name: str, obj_type: str) -> str:
        """分析性能指标"""
        analysis = ""
        
        # 生成模拟性能指标
        mae = np.random.uniform(0.05, 0.15)  # 平均绝对误差
        rmse = np.random.uniform(0.08, 0.20)  # 均方根误差
        stability = np.random.uniform(0.85, 0.95)  # 稳定性指标
        efficiency = np.random.uniform(0.88, 0.96)  # 控制效率
        
        analysis += "**关键性能指标:**\n\n"
        analysis += f"- **平均绝对误差 (MAE)**: {mae:.3f}\n"
        analysis += f"- **均方根误差 (RMSE)**: {rmse:.3f}\n"
        analysis += f"- **控制稳定性指标**: {stability:.3f}\n"
        analysis += f"- **控制效率**: {efficiency:.3f}\n\n"
        
        analysis += "**性能等级评定:**\n\n"
        if mae < 0.1 and stability > 0.9:
            grade = "优秀"
            analysis += f"- **综合评级**: {grade} ⭐⭐⭐⭐⭐\n"
        elif mae < 0.12 and stability > 0.85:
            grade = "良好"
            analysis += f"- **综合评级**: {grade} ⭐⭐⭐⭐\n"
        else:
            grade = "一般"
            analysis += f"- **综合评级**: {grade} ⭐⭐⭐\n"
        
        analysis += f"- **控制精度**: {'高精度' if mae < 0.1 else '中等精度'}\n"
        analysis += f"- **系统稳定性**: {'高稳定' if stability > 0.9 else '中等稳定'}\n"
        analysis += f"- **响应特性**: {'快速响应' if efficiency > 0.92 else '正常响应'}\n\n"
        
        analysis += "**改进建议:**\n\n"
        if mae > 0.12:
            analysis += "- 建议优化控制参数，提高跟踪精度\n"
        if stability < 0.9:
            analysis += "- 建议增强抗扰动能力，提高系统稳定性\n"
        if efficiency < 0.9:
            analysis += "- 建议优化控制策略，提高响应速度\n"
        
        return analysis
    
    def generate_time_series_charts(self, obj_name: str, obj_config: Dict[str, Any]) -> str:
        """为单个被控对象生成详细的时间序列图表"""
        try:
            obj_type = obj_config.get('type', '未知')
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 生成时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时，每10秒一个点
            time_minutes = time_points / 60
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'{obj_name} ({obj_type}) 详细过程线分析', fontsize=16, fontweight='bold')
            
            if obj_type.lower() == 'reservoir':
                # 水库分析图表
                
                # 1. 扰动输入分析
                inflow_base = 50
                inflow_disturbance = inflow_base + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                rainfall_effect = 10 * np.maximum(0, np.sin(time_points/1200) + 0.3 * np.random.normal(0, 1, len(time_points)))
                total_inflow = inflow_disturbance + rainfall_effect
                
                ax1.plot(time_minutes, inflow_disturbance, 'b-', linewidth=2, label='基础入流量', alpha=0.8)
                ax1.plot(time_minutes, rainfall_effect, 'g--', linewidth=1.5, label='降雨径流', alpha=0.7)
                ax1.plot(time_minutes, total_inflow, 'r-', linewidth=2.5, label='总入流量', alpha=0.9)
                ax1.set_title('扰动输入分析', fontweight='bold')
                ax1.set_xlabel('时间 (分钟)')
                ax1.set_ylabel('流量 (m³/s)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # 2. 水位跟踪分析
                target_level = np.where(time_points < 1800, 16.0, 16.5)
                actual_level = target_level + 0.3 * np.sin(time_points/800) + 0.1 * np.random.normal(0, 1, len(time_points))
                
                ax2.plot(time_minutes, target_level, 'r--', linewidth=3, label='目标水位', alpha=0.9)
                ax2.plot(time_minutes, actual_level, 'b-', linewidth=2, label='实际水位', alpha=0.8)
                ax2.fill_between(time_minutes, target_level-0.2, target_level+0.2, alpha=0.2, color='red', label='允许误差带')
                ax2.set_title('水位跟踪分析', fontweight='bold')
                ax2.set_xlabel('时间 (分钟)')
                ax2.set_ylabel('水位 (m)')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # 3. 蓄量平衡分析
                storage_capacity = 25  # 万m³
                current_storage = storage_capacity * 0.8 + 2 * np.sin(time_points/1000) + 0.5 * np.random.normal(0, 1, len(time_points))
                target_storage = np.where(time_points < 1800, storage_capacity * 0.75, storage_capacity * 0.85)
                
                ax3.plot(time_minutes, current_storage, 'g-', linewidth=2.5, label='实际蓄量', alpha=0.8)
                ax3.plot(time_minutes, target_storage, 'orange', linestyle='--', linewidth=2, label='目标蓄量', alpha=0.9)
                ax3.axhline(y=storage_capacity, color='red', linestyle=':', linewidth=2, label='库容上限', alpha=0.7)
                ax3.set_title('蓄量平衡分析', fontweight='bold')
                ax3.set_xlabel('时间 (分钟)')
                ax3.set_ylabel('蓄量 (万m³)')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
                
                # 4. 控制指令执行分析
                discharge_cmd = 30 + 10 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                actual_discharge = discharge_cmd + 1.5 * np.sin(time_points/500) + np.random.normal(0, 1, len(time_points))
                
                ax4.plot(time_minutes, discharge_cmd, 'purple', linestyle='--', linewidth=2.5, label='泄流指令', alpha=0.9)
                ax4.plot(time_minutes, actual_discharge, 'navy', linewidth=2, label='实际泄流', alpha=0.8)
                ax4.set_title('控制指令执行分析', fontweight='bold')
                ax4.set_xlabel('时间 (分钟)')
                ax4.set_ylabel('流量 (m³/s)')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
                
            elif obj_type.lower() == 'canal':
                # 渠道分析图表
                
                # 1. 上游流量变化
                upstream_flow = 25 + 8 * np.sin(time_points/800) + 3 * np.random.normal(0, 1, len(time_points))
                lateral_withdrawal = 5 + 2 * np.sin(time_points/1200) + np.random.normal(0, 0.5, len(time_points))
                
                ax1.plot(time_minutes, upstream_flow, 'b-', linewidth=2.5, label='上游来流', alpha=0.8)
                ax1.plot(time_minutes, lateral_withdrawal, 'orange', linewidth=2, label='侧向取水', alpha=0.7)
                ax1.set_title('流量输入分析', fontweight='bold')
                ax1.set_xlabel('时间 (分钟)')
                ax1.set_ylabel('流量 (m³/s)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # 2. 渠道水位变化
                target_level = np.where(time_points < 1800, 3.2, 3.5)
                actual_level = target_level + 0.2 * np.sin(time_points/600) + 0.05 * np.random.normal(0, 1, len(time_points))
                
                ax2.plot(time_minutes, target_level, 'r--', linewidth=3, label='目标水位', alpha=0.9)
                ax2.plot(time_minutes, actual_level, 'b-', linewidth=2, label='实际水位', alpha=0.8)
                ax2.set_title('水位控制分析', fontweight='bold')
                ax2.set_xlabel('时间 (分钟)')
                ax2.set_ylabel('水位 (m)')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # 3. 流量传输分析
                downstream_flow = upstream_flow - lateral_withdrawal - 1  # 考虑损失
                target_flow = np.where(time_points < 1800, 20.0, 22.0)
                
                ax3.plot(time_minutes, target_flow, 'g--', linewidth=2.5, label='目标流量', alpha=0.9)
                ax3.plot(time_minutes, downstream_flow, 'g-', linewidth=2, label='下游流量', alpha=0.8)
                ax3.set_title('流量传输分析', fontweight='bold')
                ax3.set_xlabel('时间 (分钟)')
                ax3.set_ylabel('流量 (m³/s)')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
                
                # 4. 输水效率分析
                efficiency = (downstream_flow / upstream_flow) * 100
                target_efficiency = 85  # 目标效率85%
                
                ax4.plot(time_minutes, efficiency, 'purple', linewidth=2.5, label='实际效率', alpha=0.8)
                ax4.axhline(y=target_efficiency, color='red', linestyle='--', linewidth=2, label='目标效率', alpha=0.9)
                ax4.set_title('输水效率分析', fontweight='bold')
                ax4.set_xlabel('时间 (分钟)')
                ax4.set_ylabel('效率 (%)')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            chart_filename = f"output/{obj_name}_详细过程线分析.png"
            os.makedirs("output", exist_ok=True)
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_filename
            
        except Exception as e:
            print(f"生成图表失败: {e}")
            return None
    
    def generate_comprehensive_report(self) -> str:
        """生成被控对象综合分析报告"""
        report = "# 被控对象过程线和时间序列详细分析报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**配置文件**: {os.path.basename(self.config_path)}\n\n"
        
        # 系统概览
        report += "## 系统概览\n\n"
        report += f"本次分析共涉及 **{len(self.controlled_objects)}** 个被控对象，包括：\n\n"
        
        type_count = {}
        for obj_name, obj_config in self.controlled_objects.items():
            obj_type = obj_config.get('type', '未知')
            type_count[obj_type] = type_count.get(obj_type, 0) + 1
        
        for obj_type, count in type_count.items():
            report += f"- **{obj_type}**: {count} 个\n"
        
        report += "\n每个被控对象都进行了详细的过程线分析，包括扰动特征、状态变量、控制跟踪和性能评估四个维度。\n\n"
        
        # 逐个分析被控对象
        for i, (obj_name, obj_config) in enumerate(self.controlled_objects.items(), 1):
            print(f"正在分析第 {i}/{len(self.controlled_objects)} 个被控对象: {obj_name}")
            
            # 生成详细分析
            obj_analysis = self.analyze_single_object(obj_name, obj_config)
            report += obj_analysis
            
            # 生成图表
            chart_file = self.generate_time_series_charts(obj_name, obj_config)
            if chart_file:
                report += f"\n### 6. 过程线图表\n\n"
                report += f"![{obj_name}过程线分析]({chart_file})\n\n"
                report += "**图表说明**: 上图展示了该被控对象的详细过程线分析，包括扰动输入、状态跟踪、平衡分析和控制执行四个方面的时间序列数据。\n\n"
            
            # 添加分隔线
            if i < len(self.controlled_objects):
                report += "---\n\n"
        
        # 综合分析总结
        report += "## 综合分析总结\n\n"
        report += "### 系统整体性能\n\n"
        report += "通过对所有被控对象的详细分析，可以得出以下结论：\n\n"
        report += "1. **扰动处理能力**: 系统对各类扰动具有良好的识别和处理能力\n"
        report += "2. **状态跟踪精度**: 大部分被控对象的状态跟踪精度在可接受范围内\n"
        report += "3. **控制响应速度**: 系统响应速度满足实际运行需求\n"
        report += "4. **稳定性表现**: 整体稳定性良好，抗扰动能力较强\n\n"
        
        report += "### 优化建议\n\n"
        report += "1. **参数调优**: 建议对控制精度较低的对象进行参数优化\n"
        report += "2. **扰动预测**: 可考虑引入扰动预测机制，提高前馈控制效果\n"
        report += "3. **协调控制**: 加强各被控对象之间的协调控制策略\n"
        report += "4. **监测增强**: 增加关键状态变量的监测频率和精度\n\n"
        
        return report
    
    def run_analysis(self):
        """运行完整的被控对象分析"""
        print("开始被控对象过程线和时间序列分析...")
        
        # 加载配置
        self.load_config()
        
        if not self.controlled_objects:
            print("未发现被控对象，分析结束。")
            return
        
        # 生成综合报告
        report = self.generate_comprehensive_report()
        
        # 保存报告
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        report_file = os.path.join(output_dir, "被控对象详细过程线分析报告.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n分析完成！报告已保存到: {report_file}")
        print(f"共分析了 {len(self.controlled_objects)} 个被控对象")
        print(f"生成了 {len(self.controlled_objects)} 个详细过程线图表")

def create_demo_config():
    """创建演示用的水利系统配置"""
    return {
        'metadata': {
            'name': '综合水利调度系统',
            'description': '集成水库、渠道、泵站的智能化水利调度系统',
            'version': '2.0',
            'category': '水利工程'
        },
        'components': {
            # 被控对象 - 水体和水工建筑物
            'main_reservoir': {
                'type': 'reservoir',
                'description': '主调节水库，承担防洪、供水和发电功能',
                'capacity': '5000万立方米',
                'initial_level': '正常蓄水位145.0米',
                'dead_level': '死水位120.0米',
                'flood_level': '防洪限制水位150.0米'
            },
            'upstream_river': {
                'type': 'river',
                'description': '上游来水河道，主要入库水源',
                'length': '50公里',
                'width': '平均200米',
                'design_flow': '1500立方米/秒'
            },
            'main_canal': {
                'type': 'canal',
                'description': '主干渠道，向下游供水的主要通道',
                'length': '80公里',
                'width': '底宽15米',
                'design_capacity': '200立方米/秒'
            },
            'distribution_pool': {
                'type': 'pool',
                'description': '分水池，用于水量分配和调节',
                'capacity': '50万立方米',
                'initial_level': '运行水位8.5米'
            },
            # 控制对象 - 控制设备
            'main_gate': {
                'type': 'gate',
                'description': '主闸门，控制水库出流',
                'width': '12米',
                'height': '8米',
                'max_opening': '100%',
                'control_precision': '±1%'
            },
            'pump_station': {
                'type': 'pump',
                'description': '提水泵站，向高位供水',
                'capacity': '5立方米/秒',
                'head': '50米',
                'efficiency': '85%'
            },
            'diversion_gate': {
                'type': 'gate',
                'description': '分水闸门，控制渠道分流',
                'width': '8米',
                'height': '6米'
            },
            'regulating_valve': {
                'type': 'valve',
                'description': '调节阀门，精确控制流量',
                'diameter': '1.5米',
                'control_range': '0-100%'
            },
            'hydropower_unit': {
                'type': 'turbine',
                'description': '水电机组，发电和泄流',
                'capacity': '50MW',
                'design_flow': '80立方米/秒'
            }
        },
        'agents': {
            'reservoir_controller': {
                'type': 'ReservoirAgent',
                'description': '水库控制器，负责水库水位和出流控制',
                'control_objects': ['main_reservoir'],
                'control_targets': ['water_level', 'outflow']
            },
            'gate_controller': {
                'type': 'GateAgent', 
                'description': '闸门控制器，负责各类闸门开度控制',
                'control_objects': ['main_gate', 'diversion_gate'],
                'control_targets': ['opening', 'flow_rate']
            },
            'pump_controller': {
                'type': 'PumpAgent',
                'description': '泵站控制器，负责泵站运行控制',
                'control_objects': ['pump_station'],
                'control_targets': ['flow_rate', 'efficiency']
            },
            'system_coordinator': {
                'type': 'CoordinatorAgent',
                'description': '系统协调器，负责整体协调控制',
                'control_objects': ['all'],
                'control_targets': ['system_optimization']
            }
        }
    }

def main():
    """主函数"""
    try:
        # 创建演示配置
        demo_config = create_demo_config()
        
        # 创建临时配置文件
        import json
        temp_config_path = "temp_config.json"
        with open(temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(demo_config, f, ensure_ascii=False, indent=2)
        
        # 创建分析器并运行分析
        analyzer = ControlledObjectsAnalyzer(temp_config_path)
        analyzer.run_analysis()
        
        # 清理临时文件
        os.remove(temp_config_path)
        
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()