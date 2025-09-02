#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数字孪生与优化控制仿真案例运行脚本

本脚本用于启动分布式数字孪生与优化控制仿真案例。
该案例展示了一个完整的分布式智能体系统，包括：
- 物理本体仿真层
- 分布式感知智能体层
- 控制智能体层
- 中心感知与MPC层
- 扰动智能体层
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入CHS-SDK核心模块
from core_lib.io.yaml_loader import SimulationBuilder

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("=== 分布式数字孪生与优化控制仿真案例启动 ===")
        
        # 获取当前目录作为场景路径
        scenario_path = Path(__file__).parent
        logger.info(f"场景路径: {scenario_path}")
        
        # 创建SimulationBuilder
        logger.info("正在创建SimulationBuilder...")
        builder = SimulationBuilder(scenario_path=str(scenario_path))
        logger.info("SimulationBuilder创建完成")
        
        # 加载仿真配置和组件
        logger.info("正在加载仿真配置和组件...")
        harness = builder.load()
        logger.info("仿真配置和组件加载完成")
        
        # 运行仿真
        logger.info("开始运行多智能体仿真...")
        result = harness.run_mas_simulation()
        logger.info("多智能体仿真完成")
        
        # 输出结果
        logger.info(f"仿真结果: {len(harness.history)} 个时间步")
        logger.info(f"组件数量: {len(harness.components)}")
        logger.info(f"智能体数量: {len(harness.agents)}")
        logger.info(f"控制器数量: {len(harness.controllers)}")
        logger.info("仿真成功完成!")
        
        return result
        
    except Exception as e:
        logger.error(f"仿真运行失败: {e}")
        logger.exception("详细错误信息:")
        raise

if __name__ == "__main__":
    main()