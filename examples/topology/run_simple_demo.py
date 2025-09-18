#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的水利系统拓扑仿真脚本
基于CHS-SDK核心库的基础仿真案例

如果主脚本遇到问题，请使用此备用脚本
"""

import os
import sys
import yaml
from pathlib import Path

# 添加核心库路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

def load_yaml_file(file_path):
    """加载YAML文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 失败: {e}")
        return None

def simple_simulation():
    """简单的仿真演示"""
    print("=== 简化仿真演示 ===")
    
    config_dir = Path(__file__).parent
    
    # 加载配置文件
    config = load_yaml_file(config_dir / 'config.yml')
    components = load_yaml_file(config_dir / 'components.yml')
    topology = load_yaml_file(config_dir / 'topology.yml')
    agents = load_yaml_file(config_dir / 'agents.yml')
    
    if not all([config, components, topology, agents]):
        print("✗ 配置文件加载失败")
        return False
    
    print("✓ 配置文件加载成功")
    
    # 显示配置信息
    sim_config = config.get('simulation', {})
    print(f"仿真名称: {sim_config.get('name', '未知')}")
    print(f"仿真描述: {sim_config.get('description', '无描述')}")
    print(f"开始时间: {sim_config.get('start_time', 0)} 秒")
    print(f"结束时间: {sim_config.get('end_time', 0)} 秒")
    print(f"时间步长: {sim_config.get('time_step', 0)} 秒")
    
    # 显示组件信息
    comp_list = components.get('components', [])
    print(f"\\n组件数量: {len(comp_list)}")
    for comp in comp_list:
        comp_id = comp.get('id', '未知')
        comp_class = comp.get('class', '未知')
        print(f"  - {comp_id}: {comp_class}")
    
    # 显示拓扑连接
    topo_connections = topology.get('topology', {}).get('connections', [])
    print(f"\\n拓扑连接数量: {len(topo_connections)}")
    for conn in topo_connections:
        upstream = conn.get('upstream', '未知')
        downstream = conn.get('downstream', '未知')
        conn_type = conn.get('connection_type', '未知')
        print(f"  {upstream} -> {downstream} ({conn_type})")
    
    # 显示智能体信息
    agent_list = agents.get('agents', [])
    print(f"\\n智能体数量: {len(agent_list)}")
    for agent in agent_list:
        agent_id = agent.get('id', '未知')
        agent_class = agent.get('class', '未知')
        print(f"  - {agent_id}: {agent_class}")
    
    print("\\n=== 配置验证完成 ===")
    print("配置文件格式正确，可以尝试运行完整仿真")
    
    return True

def run_enhanced_simulation():
    """尝试运行增强仿真"""
    print("\\n=== 尝试运行增强仿真 ===")
    
    try:
        # 尝试导入增强配置加载器
        from core_lib.config.enhanced_yaml_loader import load_universal_config
        
        config_dir = Path(__file__).parent
        
        # 检查是否有通用配置文件
        universal_config_files = [
            config_dir / 'universal_config.yml',
            config_dir.parent.parent / 'core_lib' / 'config' / 'example_universal_config.yml'
        ]
        
        config_file = None
        for f in universal_config_files:
            if f.exists():
                config_file = f
                break
        
        if config_file:
            print(f"找到通用配置文件: {config_file}")
            
            # 加载并运行增强仿真
            builder = load_universal_config(str(config_file), str(config_dir))
            results = builder.run_enhanced_simulation()
            
            print("✓ 增强仿真运行成功")
            return True
        else:
            print("未找到通用配置文件，跳过增强仿真")
            return False
            
    except ImportError as e:
        print(f"增强配置加载器不可用: {e}")
        return False
    except Exception as e:
        print(f"增强仿真运行失败: {e}")
        return False

def run_basic_yaml_simulation():
    """尝试运行基础YAML仿真"""
    print("\\n=== 尝试运行基础YAML仿真 ===")
    
    try:
        from core_lib.io.yaml_loader import YamlSimulationLoader
        
        config_dir = Path(__file__).parent
        
        # 创建YAML仿真加载器
        loader = YamlSimulationLoader(str(config_dir))
        print("✓ YAML仿真加载器创建成功")
        
        # 加载仿真
        harness = loader.load()
        print("✓ 仿真配置加载成功")
        
        # 尝试运行仿真
        print("正在运行仿真...")
        harness.run_mas_simulation()
        print("✓ 仿真运行完成")
        
        return True
        
    except ImportError as e:
        print(f"YAML仿真加载器不可用: {e}")
        return False
    except Exception as e:
        print(f"基础仿真运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("CHS-SDK 简化水利系统拓扑仿真")
    print("=" * 50)
    
    success = False
    
    # 1. 基础配置验证
    if simple_simulation():
        print("\\n✓ 配置验证通过")
        
        # 2. 尝试运行增强仿真
        if run_enhanced_simulation():
            success = True
        
        # 3. 如果增强仿真失败，尝试基础仿真
        elif run_basic_yaml_simulation():
            success = True
        
        else:
            print("\\n所有仿真方法都失败了")
            print("可能的原因:")
            print("1. 缺少必要的依赖包")
            print("2. 配置文件格式问题")
            print("3. 核心库路径问题")
            print("\\n建议:")
            print("1. 检查requirements.txt中的依赖是否已安装")
            print("2. 确认配置文件格式正确")
            print("3. 检查核心库导入路径")
    
    else:
        print("\\n✗ 配置验证失败")
    
    print("\\n" + "=" * 50)
    if success:
        print("✓ 仿真演示完成！")
        return 0
    else:
        print("✗ 仿真演示失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)