#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件驱动的仿真运行脚本模板

这个模板展示了如何使用统一的仿真运行器来执行基于YAML配置文件的仿真。
只需要几行代码就可以运行复杂的仿真场景。

使用方法：
1. 复制这个模板到你的示例目录
2. 修改config_file变量指向你的配置文件
3. 根据需要调整其他参数
4. 运行脚本
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
    # 配置文件路径（相对于当前脚本的路径）
    config_file = Path(__file__).parent / "config.yml"
    
    # 运行仿真
    result = run_simulation_from_config(
        config_path=str(config_file),
        show_progress=True,    # 显示仿真进度
        show_summary=True      # 显示仿真总结
    )
    
    # 可以在这里添加自定义的后处理逻辑
    if result['success']:
        print(f"\n🎉 仿真成功完成！")
        # 例如：保存特定的结果数据、生成图表等
    else:
        print(f"\n❌ 仿真失败: {result.get('error', '未知错误')}")
        sys.exit(1)

if __name__ == "__main__":
    main()