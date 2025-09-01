#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 5 - 水轮机和泄洪闸仿真演示

这个脚本演示了水轮机和泄洪闸的仿真功能，展示了如何实现复杂水利系统的建模。
使用统一的仿真运行器，代码简洁易维护。
"""

import subprocess
import sys
from pathlib import Path

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # 解析命令行参数，确定运行哪个子例子
    example_type = "5.1"  # 默认运行5.1
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
    
    # 映射例子类型到目录名
    example_dirs = {
        "5.1": "01_turbine_gate_simulation",
        "5.2": "02_multi_unit_coordination", 
        "5.3": "03_economic_dispatch",
        "5.4": "04_gate_scheduling"
    }
    
    if example_type not in example_dirs:
        print(f"❌ 无效的例子类型: {example_type}")
        print(f"可选值: {', '.join(example_dirs.keys())}")
        sys.exit(1)
    
    # 构建场景路径
    scenario_path = Path(__file__).parent / example_dirs[example_type]
    
    # 构建运行命令
    run_scenario_script = project_root / "run_scenario.py"
    cmd = [sys.executable, str(run_scenario_script), str(scenario_path)]
    
    try:
        # 运行仿真
        print(f"🚀 启动 Mission Example {example_type} 仿真...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        print(f"\n🎉 Mission Example {example_type} 仿真成功完成！")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 仿真失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()