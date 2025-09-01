#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1.4 - 数字孪生智能体演示

这个脚本演示了数字孪生智能体的功能，展示了如何实现物理系统的数字化镜像。
使用统一的仿真运行器，代码简洁易维护。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一仿真运行器
from run_unified_scenario import run_simulation_from_config

def main():
    """主函数"""
    # 配置文件路径
    config_file = Path(__file__).parent / "config_1_4.yml"
    
    # 运行仿真
    result = run_simulation_from_config(
        config_path=str(config_file),
        show_progress=True,
        show_summary=True
    )
    
    # 处理仿真结果
    if result['success']:
        print(f"\n🎉 Mission Example 1.4 (数字孪生智能体) 仿真成功完成！")
        print(f"📊 执行时间: {result['execution_time']:.2f}秒")
    else:
        print(f"\n❌ 仿真失败: {result.get('error', '未知错误')}")
        sys.exit(1)

if __name__ == "__main__":
    main()