#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水利系统详细描述演示
展示如何使用文字详细描述水利系统的基本情况，并对被控对象和控制对象进行分析
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'core_lib'))

from core_lib.reporting.config_to_text_converter import ConfigToTextConverter
from datetime import datetime

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
                'design_capacity': '800立方米/秒'
            },
            'distribution_pond': {
                'type': 'pond',
                'description': '分水池，用于水量分配和调节',
                'area': '5000平方米',
                'depth': '平均深度3.5米',
                'volume': '1.75万立方米'
            },
            
            # 控制对象 - 调控设备
            'main_gate': {
                'type': 'gate',
                'description': '水库主闸门，控制出库流量',
                'max_opening': '8.0米',
                'control_type': '电动',
                'design_discharge': '2000立方米/秒',
                'gate_count': '3孔'
            },
            'pump_station_1': {
                'type': 'pump',
                'description': '一级泵站，提升灌区供水',
                'capacity': '50立方米/秒',
                'head': '25米',
                'pump_count': '4台',
                'power': '单台功率2500kW'
            },
            'diversion_gate': {
                'type': 'gate',
                'description': '分水闸门，控制渠道分流',
                'max_opening': '3.0米',
                'control_type': '液压',
                'design_discharge': '300立方米/秒'
            },
            'regulation_valve': {
                'type': 'valve',
                'description': '调节阀门，精确控制管道流量',
                'diameter': 'DN1200',
                'pressure_rating': 'PN16',
                'control_accuracy': '±2%'
            },
            'hydropower_unit': {
                'type': 'hydropower',
                'description': '水电机组，发电兼顾下泄流量调节',
                'capacity': '50MW',
                'efficiency': '92%',
                'turbine_type': '混流式',
                'unit_count': '2台'
            }
        },
        'agents': {
            'reservoir_controller': {
                'type': 'digital_twin_agent',
                'description': '水库数字孪生控制智能体',
                'control_targets': ['main_reservoir'],
                'control_objectives': ['水位控制', '防洪调度', '供水保障']
            },
            'gate_controller': {
                'type': 'local_control_agent', 
                'description': '闸门现地控制智能体',
                'control_targets': ['main_gate', 'diversion_gate'],
                'control_objectives': ['流量调节', '水位维持']
            },
            'pump_controller': {
                'type': 'pump_control_agent',
                'description': '泵站控制智能体',
                'control_targets': ['pump_station_1'],
                'control_objectives': ['供水保障', '能耗优化']
            },
            'system_coordinator': {
                'type': 'coordination_agent',
                'description': '系统协调智能体',
                'control_targets': ['全系统'],
                'control_objectives': ['整体优化', '应急响应']
            }
        },
        'topology': {
            'connections': [
                {'from': 'upstream_river', 'to': 'main_reservoir', 'type': '自然流入'},
                {'from': 'main_reservoir', 'to': 'main_gate', 'type': '控制出流'},
                {'from': 'main_gate', 'to': 'main_canal', 'type': '渠道输水'},
                {'from': 'main_canal', 'to': 'distribution_pond', 'type': '渠道供水'},
                {'from': 'distribution_pond', 'to': 'pump_station_1', 'type': '泵站取水'},
                {'from': 'main_reservoir', 'to': 'hydropower_unit', 'type': '发电引水'},
                {'from': 'hydropower_unit', 'to': 'main_canal', 'type': '尾水排放'},
                {'from': 'main_canal', 'to': 'diversion_gate', 'type': '分流控制'},
                {'from': 'diversion_gate', 'to': 'regulation_valve', 'type': '管道输水'}
            ]
        },
        'simulation': {
            'duration': 86400,  # 24小时
            'time_step': 300,   # 5分钟
            'solver': 'runge_kutta_4',
            'output_interval': 900  # 15分钟输出一次
        }
    }

def main():
    """主函数"""
    print("=== 水利系统详细描述演示 ===")
    
    # 创建配置转换器
    converter = ConfigToTextConverter()
    
    # 创建演示配置
    config = create_demo_config()
    
    # 生成详细系统描述
    print("\n正在生成水利系统详细描述...")
    
    # 1. 生成系统整体描述
    system_description = converter.generate_detailed_system_description(config)
    
    # 2. 分类组件
    components = config.get('components', {})
    controlled_objects = {}
    control_objects = {}
    
    for comp_name, comp_config in components.items():
        comp_type = comp_config.get('type', '未知').lower()
        if comp_type in ['reservoir', 'river', 'canal', 'pipe', 'lake', 'pond']:
            controlled_objects[comp_name] = comp_config
        elif comp_type in ['gate', 'pump', 'valve', 'hydropower']:
            control_objects[comp_name] = comp_config
    
    # 3. 生成被控对象详细描述
    controlled_description = converter.describe_controlled_objects_detail(controlled_objects)
    
    # 4. 生成控制对象详细描述
    control_description = converter.describe_control_objects_detail(control_objects)
    
    # 5. 生成智能体描述
    agents_description = "### 智能体控制系统\n\n"
    agents_description += "智能体系统采用分层分布式架构，实现水利系统的智能化调度：\n\n"
    
    agents = config.get('agents', {})
    for i, (agent_name, agent_config) in enumerate(agents.items(), 1):
        agent_type = agent_config.get('type', '未知')
        agent_desc = agent_config.get('description', '无描述')
        control_targets = agent_config.get('control_targets', [])
        control_objectives = agent_config.get('control_objectives', [])
        
        agents_description += f"**{i}. {agent_name}** ({agent_type})\n"
        agents_description += f"   - 功能描述：{agent_desc}\n"
        agents_description += f"   - 控制对象：{', '.join(control_targets)}\n"
        agents_description += f"   - 控制目标：{', '.join(control_objectives)}\n\n"
    
    # 6. 组合完整报告
    full_report = f"""
# 水利系统详细分析报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{system_description}

{controlled_description}

{control_description}

{agents_description}

## 系统运行特征分析

### 控制策略
本水利系统采用多智能体协同控制策略，通过数字孪生技术和现地控制相结合的方式，实现：

1. **预测性控制**：基于水文预报和需水预测，提前制定调度方案
2. **实时响应控制**：根据实时监测数据，动态调整控制参数
3. **协同优化控制**：多个智能体协同工作，实现全局最优
4. **应急处置控制**：在异常情况下快速响应，确保系统安全

### 性能指标
- **响应时间**：控制指令响应时间 < 30秒
- **控制精度**：水位控制精度 ±5cm，流量控制精度 ±3%
- **系统可靠性**：年可用率 > 99.5%
- **能耗效率**：泵站综合效率 > 85%

### 监测体系
系统建立了完善的监测体系，实现对关键参数的实时监控：

- **水位监测**：水库、渠道、池塘等关键节点水位
- **流量监测**：各控制断面的实时流量
- **设备状态监测**：闸门开度、泵站运行状态、阀门位置
- **水质监测**：主要供水点的水质参数
- **气象监测**：降雨、蒸发等气象要素

## 总结

本水利系统通过先进的智能化控制技术，实现了水资源的高效调配和精确控制。系统具有响应快速、控制精确、运行可靠的特点，能够满足防洪、供水、发电等多重需求，为区域水安全提供了有力保障。
"""
    
    # 保存报告
    output_file = "水利系统详细描述报告.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print(f"\n✅ 详细描述报告已生成：{output_file}")
    print(f"\n📊 报告统计：")
    print(f"   - 被控对象：{len(controlled_objects)} 个")
    print(f"   - 控制对象：{len(control_objects)} 个")
    print(f"   - 智能体：{len(agents)} 个")
    print(f"   - 连接关系：{len(config.get('topology', {}).get('connections', []))} 条")
    
    # 显示部分报告内容
    print("\n📋 报告预览：")
    print("=" * 50)
    print(full_report[:1000] + "...")
    print("=" * 50)
    
if __name__ == "__main__":
    main()