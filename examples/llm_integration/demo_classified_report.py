#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示分类报告生成功能
展示控制对象和被控对象的分类管理
"""

import sys
import os
# 添加core_lib/reporting目录到路径
reporting_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_lib', 'reporting')
sys.path.append(reporting_path)

from config_to_text_converter import ConfigToTextConverter
import json

def create_demo_config():
    """创建演示配置"""
    config = {
        "metadata": {
            "name": "智能水利系统分类演示",
            "version": "1.0",
            "description": "展示控制对象和被控对象的分类管理功能",
            "author": "CHS-SDK",
            "created_date": "2024-01-15"
        },
        "components": {
            # 被控对象
            "main_reservoir": {
                "type": "reservoir",
                "capacity": 50000000,
                "normal_level": 16.0,
                "flood_level": 18.5,
                "dead_level": 12.0,
                "description": "主水库，用于调节水量和防洪"
            },
            "upstream_river": {
                "type": "river",
                "length": 15000,
                "width": 120,
                "slope": 0.0008,
                "description": "上游河道，连接水库和闸门"
            },
            "distribution_canal": {
                "type": "canal",
                "length": 8000,
                "width": 50,
                "design_flow": 25,
                "description": "配水渠道，向下游供水"
            },
            "regulation_pond": {
                "type": "pond",
                "capacity": 500000,
                "normal_level": 8.0,
                "description": "调蓄池，用于短期调节"
            },
            # 控制对象
            "main_gate": {
                "type": "gate",
                "width": 8.0,
                "height": 6.0,
                "max_opening": 1.0,
                "control_type": "automatic",
                "description": "主闸门，控制水库出流"
            },
            "pump_station": {
                "type": "pump",
                "capacity": 15.0,
                "head": 25.0,
                "efficiency": 0.85,
                "description": "泵站，用于提升水位"
            },
            "control_valve": {
                "type": "valve",
                "diameter": 1.2,
                "pressure_rating": 16,
                "control_type": "electric",
                "description": "控制阀门，精确调节流量"
            },
            "hydropower_station": {
                "type": "hydropower",
                "capacity": 50,
                "turbine_type": "francis",
                "efficiency": 0.92,
                "description": "水电站，发电并调节流量"
            }
        },
        "agents": {
            "reservoir_controller": {
                "type": "PIDController",
                "target_component": "main_reservoir",
                "control_variable": "water_level",
                "setpoint": 16.0,
                "parameters": {
                    "kp": 1.2,
                    "ki": 0.3,
                    "kd": 0.1
                }
            },
            "gate_controller": {
                "type": "FuzzyController",
                "target_component": "main_gate",
                "control_variable": "opening",
                "parameters": {
                    "rules": 15,
                    "membership_functions": 5
                }
            },
            "pump_controller": {
                "type": "AdaptiveController",
                "target_component": "pump_station",
                "control_variable": "flow_rate",
                "parameters": {
                    "adaptation_rate": 0.05,
                    "learning_factor": 0.8
                }
            }
        },
        "topology": {
            "connections": [
                {"from": "upstream_river", "to": "main_reservoir", "type": "inflow"},
                {"from": "main_reservoir", "to": "main_gate", "type": "control"},
                {"from": "main_gate", "to": "distribution_canal", "type": "outflow"},
                {"from": "distribution_canal", "to": "pump_station", "type": "flow"},
                {"from": "pump_station", "to": "regulation_pond", "type": "pumped_flow"},
                {"from": "regulation_pond", "to": "control_valve", "type": "control"},
                {"from": "main_reservoir", "to": "hydropower_station", "type": "power_flow"}
            ]
        },
        "simulation": {
            "duration": 3600,
            "time_step": 10,
            "solver": "runge_kutta_4",
            "output_interval": 60
        },
        "analysis": {
            "metrics": ["water_level", "flow_rate", "control_error", "energy_consumption"],
            "visualization": {
                "charts": ["time_series", "phase_plot", "control_performance"],
                "export_format": ["png", "svg"]
            }
        }
    }
    return config

def main():
    """主函数"""
    print("开始生成分类报告演示...")
    
    # 创建配置
    config = create_demo_config()
    
    # 创建转换器
    converter = ConfigToTextConverter()
    
    # 生成报告
    try:
        # 创建临时目录并保存YAML配置文件
        import tempfile
        import yaml
        
        temp_dir = tempfile.mkdtemp()
        temp_config_file = os.path.join(temp_dir, 'unified_config.yaml')
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        # 使用正确的方法名
        report = converter.convert_to_natural_language(temp_dir)
        
        # 清理临时文件和目录
        os.unlink(temp_config_file)
        os.rmdir(temp_dir)
        
        # 保存报告
        output_file = "classified_report_demo.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"报告已生成并保存到: {output_file}")
        print(f"报告长度: {len(report)} 字符")
        
        # 显示报告的主要部分
        lines = report.split('\n')
        print("\n=== 报告结构概览 ===")
        for i, line in enumerate(lines[:50]):  # 显示前50行
            if line.startswith('#'):
                print(f"第{i+1}行: {line}")
        
        print("\n=== 分类统计 ===")
        controlled_count = report.count('被控对象')
        control_count = report.count('控制对象')
        print(f"被控对象提及次数: {controlled_count}")
        print(f"控制对象提及次数: {control_count}")
        
        if '被控对象时间序列分析' in report:
            print("✓ 被控对象分析部分已生成")
        if '控制对象时间序列分析' in report:
            print("✓ 控制对象分析部分已生成")
        if '被控对象时间序列数据表' in report:
            print("✓ 被控对象数据表已生成")
        if '控制对象时间序列数据表' in report:
            print("✓ 控制对象数据表已生成")
        
        print("\n演示完成！")
        
    except Exception as e:
        print(f"报告生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()