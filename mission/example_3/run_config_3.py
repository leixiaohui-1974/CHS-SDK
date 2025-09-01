#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 3 - 增强感知智能体演示

这个脚本演示了增强感知智能体的功能，展示了如何实现智能感知和数据处理。
使用统一的仿真运行器，代码简洁易维护。
"""

import subprocess
import sys
from pathlib import Path

def main():
    """主函数"""
    # 获取项目根目录和场景路径
    project_root = Path(__file__).resolve().parent.parent.parent
    scenario_path = Path(__file__).parent / "01_enhanced_perception"
    
    # 构建运行命令
    run_scenario_script = project_root / "run_scenario.py"
    cmd = [sys.executable, str(run_scenario_script), str(scenario_path)]
    
    try:
        # 运行仿真
        print(f"🚀 启动 Mission Example 3 (增强感知智能体) 仿真...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        print(f"\n🎉 Mission Example 3 (增强感知智能体) 仿真成功完成！")
        
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