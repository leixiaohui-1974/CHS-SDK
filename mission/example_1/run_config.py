#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1 - 配置文件驱动版本

这个脚本演示了如何使用配置文件来驱动物理模型仿真。
使用统一的仿真运行器，只需几行代码就能运行复杂的仿真场景。

主要特点：
1. 使用 YAML 配置文件定义物理组件和仿真参数
2. 基于统一仿真运行器，代码简洁易维护
3. 提供清晰的性能统计和结果验证
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import subprocess

def main():
    """主函数"""
    # 场景目录路径 - 指向01_basic_simulation子目录
    scenario_dir = Path(__file__).parent / "01_basic_simulation"
    
    # 根目录的run_scenario.py路径
    run_scenario_script = project_root / "run_scenario.py"
    
    print(f"🚀 运行 Mission Example 1 - 基础仿真场景")
    print(f"📁 场景目录: {scenario_dir}")
    
    try:
        # 调用run_scenario.py
        result = subprocess.run([
            sys.executable, 
            str(run_scenario_script), 
            str(scenario_dir)
        ], capture_output=True, text=True, check=True)
        
        print(result.stdout)
        print(f"\n🎉 Mission Example 1 仿真成功完成！")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 仿真失败:")
        print(f"错误代码: {e.returncode}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()