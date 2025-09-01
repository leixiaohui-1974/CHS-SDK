#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1.3 - 故障容错场景

这个脚本演示了故障检测和容错控制系统的仿真。
包含主备系统切换和应急处理机制。
"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    # 场景目录路径 - 指向03_fault_tolerance子目录
    scenario_dir = Path(__file__).parent / "03_fault_tolerance"
    
    # 根目录的run_scenario.py路径
    run_scenario_script = project_root / "run_scenario.py"
    
    print(f"🚀 运行 Mission Example 1.3 - 故障容错场景")
    print(f"📁 场景目录: {scenario_dir}")
    
    try:
        # 调用run_scenario.py
        result = subprocess.run([
            sys.executable, 
            str(run_scenario_script), 
            str(scenario_dir)
        ], capture_output=True, text=True, check=True)
        
        print(result.stdout)
        print(f"\n🎉 Mission Example 1.3 仿真成功完成！")
        
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