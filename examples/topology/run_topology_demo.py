#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水利系统拓扑仿真演示脚本
基于CHS-SDK核心库的完整仿真案例

系统组成：
- 上游水库 -> 渠道1 -> 分水口1 -> 渠道2 -> 管道1 -> 闸门1 -> 渠道3 -> 下游水库
"""

import os
import sys
import yaml
import numpy as np
from pathlib import Path

# 添加核心库路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入核心库
from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def load_configuration():
    """加载配置文件"""
    print("=== 加载配置文件 ===")
    
    config_dir = Path(__file__).parent
    
    # 检查配置文件是否存在
    config_files = {
        'config': config_dir / 'config.yml',
        'components': config_dir / 'components.yml',
        'topology': config_dir / 'topology.yml',
        'agents': config_dir / 'agents.yml'
    }
    
    for name, file_path in config_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        print(f"✓ {name}: {file_path}")
    
    return str(config_dir)

def create_simulation_components(scenario_path):
    """创建仿真组件"""
    print("\n=== 创建仿真组件 ===")
    
    try:
        # 创建YAML仿真加载器
        loader = YamlSimulationLoader(scenario_path)
        print("✓ YAML仿真加载器创建完成")
        
        # 加载完整仿真
        harness = loader.load()
        print("✓ 仿真加载完成")
        
        # 获取组件信息
        components = getattr(loader, 'component_instances', {})
        message_bus = getattr(loader, 'message_bus', None)
        
        print(f"✓ 成功加载 {len(components)} 个组件:")
        for name, component in components.items():
            print(f"  - {name}: {component.__class__.__name__}")
        
        return harness, components, message_bus
        
    except Exception as e:
        print(f"✗ 创建仿真组件失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def run_simulation(harness):
    """运行仿真"""
    print("\n=== 开始仿真 ===")
    
    try:
        # 运行MAS仿真
        print("正在运行多智能体仿真...")
        harness.run_mas_simulation()
        
        print("✓ 仿真运行完成")
        
        # 获取仿真历史数据
        history = getattr(harness, 'history', [])
        print(f"✓ 仿真历史包含 {len(history)} 个时间步")
        
        return history
        
    except Exception as e:
        print(f"✗ 仿真运行失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def analyze_results(results):
    """分析和展示仿真结果"""
    print("\n=== 仿真结果分析 ===")
    
    if not results:
        print("⚠ 没有仿真结果可供分析")
        return
    
    print(f"仿真历史记录数量: {len(results)}")
    
    # 如果有历史记录，分析最后的状态
    if hasattr(results[-1] if results else None, 'get'):
        # 分析最后一个时间步的结果
        final_step = results[-1]
        current_time = final_step.get('current_time', 0)
        component_states = final_step.get('component_states', {})
        
        print(f"最终仿真时间: {current_time} 秒 ({current_time/3600:.2f} 小时)")
        print(f"组件状态数量: {len(component_states)}")
        
        # 显示关键组件状态
        key_components = ['Upstream_Reservoir', 'Channel_1', 'Gate_1', 'Channel_3', 'Downstream_Reservoir']
        
        print("\n关键组件最终状态:")
        for comp_name in key_components:
            if comp_name in component_states:
                state = component_states[comp_name]
                print(f"  {comp_name}:")
                
                # 显示水位信息
                if 'water_level' in state:
                    print(f"    水位: {state['water_level']:.3f} m")
                
                # 显示流量信息
                if 'outflow' in state:
                    print(f"    出流: {state['outflow']:.3f} m³/s")
                
                # 显示闸门开度
                if 'opening' in state:
                    print(f"    开度: {state['opening']:.3f}")
                
                # 显示库容
                if 'volume' in state:
                    print(f"    库容: {state['volume']:.1f} m³")
    else:
        print("✓ 仿真已完成，但结果格式与预期不同")
        print("可能的原因: 使用了不同的仿真执行模式")

def save_results(results, output_dir=None):
    """保存仿真结果"""
    print("\n=== 保存仿真结果 ===")
    
    if output_dir is None:
        output_dir = Path(__file__).parent / "simulation_output"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 保存为JSON格式
        import json
        output_file = output_dir / "topology_simulation_results.json"
        
        # 转换numpy数组为列表以便JSON序列化
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        converted_results = convert_numpy(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 结果已保存到: {output_file}")
        
        # 创建简单的CSV报告
        csv_file = output_dir / "key_metrics.csv"
        create_csv_report(results, csv_file)
        print(f"✓ 关键指标已保存到: {csv_file}")
        
    except Exception as e:
        print(f"⚠ 保存结果时出错: {e}")

def create_csv_report(results, csv_file):
    """创建CSV格式的关键指标报告"""
    import csv
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 写入标题行
        headers = ['时间(s)', '上游水库水位(m)', '渠道1水位(m)', '闸门1开度', 
                  '渠道3水位(m)', '下游水库水位(m)', '闸门1流量(m³/s)']
        writer.writerow(headers)
        
        # 写入数据行
        for step in results:
            current_time = step.get('current_time', 0)
            states = step.get('component_states', {})
            
            row = [current_time]
            
            # 提取关键指标
            components = ['Upstream_Reservoir', 'Channel_1', 'Gate_1', 'Channel_3', 'Downstream_Reservoir']
            metrics = ['water_level', 'water_level', 'opening', 'water_level', 'water_level']
            
            for comp, metric in zip(components, metrics):
                if comp in states and metric in states[comp]:
                    row.append(states[comp][metric])
                else:
                    row.append('')
            
            # 添加闸门流量
            if 'Gate_1' in states and 'outflow' in states['Gate_1']:
                row.append(states['Gate_1']['outflow'])
            else:
                row.append('')
            
            writer.writerow(row)

def main():
    """主函数"""
    print("CHS-SDK 水利系统拓扑仿真演示")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        scenario_path = load_configuration()
        
        # 2. 创建仿真组件
        harness, components, message_bus = create_simulation_components(scenario_path)
        
        # 3. 运行仿真
        results = run_simulation(harness)
        
        # 4. 分析结果
        analyze_results(results)
        
        # 5. 保存结果
        save_results(results)
        
        print("\n" + "=" * 50)
        print("✓ 仿真演示完成！")
        
    except Exception as e:
        print(f"\n✗ 仿真演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)