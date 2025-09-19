#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置处理和验证脚本

用于测试配置加载器功能，验证配置文件的正确性，
并生成处理后的完整配置文件供仿真系统使用。

功能：
1. 加载和验证config_constants.yml
2. 处理agents.yml和components.yml中的变量引用
3. 生成最终的配置文件
4. 执行物理模型参数合理性检查

使用方法:
    python config_processor.py
"""

import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 获取当前目录
        current_dir = Path(__file__).parent
        
        logger.info("=== 引绰济辽工程配置处理器 ===")
        logger.info(f"工作目录: {current_dir}")
        
        # 导入配置加载器
        from config_loader import ConfigLoader, load_scenario_config, validate_scenario_config
        
        # 创建配置加载器
        loader = ConfigLoader(current_dir)
        
        # 1. 加载常量配置
        logger.info("\n1. 加载常量配置...")
        constants = loader.load_constants()
        logger.info(f"加载了 {len(constants)} 个配置节")
        
        # 显示PID控制器配置
        if 'pid_controllers' in constants:
            logger.info(f"PID控制器配置: {len(constants['pid_controllers'])} 个控制器")
            for controller_id in constants['pid_controllers']:
                logger.info(f"  - {controller_id}")
        
        # 2. 加载并处理agents.yml
        logger.info("\n2. 处理agents.yml配置...")
        agents_config = loader.load_config_with_substitution("agents.yml")
        
        if 'controllers' in agents_config:
            logger.info(f"处理了 {len(agents_config['controllers'])} 个控制器配置")
            
            # 验证PID参数替换是否成功
            for controller in agents_config['controllers'][:2]:  # 显示前两个
                controller_id = controller['id']
                config = controller['config']
                logger.info(f"  {controller_id}: Kp={config['Kp']}, setpoint={config['setpoint']}")
        
        if 'agents' in agents_config:
            logger.info(f"处理了 {len(agents_config['agents'])} 个智能体配置")
        
        # 3. 加载并处理components.yml
        logger.info("\n3. 处理components.yml配置...")
        components_config = loader.load_config_with_substitution("components.yml")
        
        if 'components' in components_config:
            logger.info(f"处理了 {len(components_config['components'])} 个组件配置")
        
        # 4. 生成合并配置
        logger.info("\n4. 生成合并配置...")
        full_config = loader.get_merged_config(["components.yml", "agents.yml"])
        
        # 5. 验证配置合理性
        logger.info("\n5. 验证配置合理性...")
        validate_scenario_config(full_config)
        logger.info("✅ 配置验证通过！")
        
        # 6. 保存处理后的配置（可选）
        save_processed = True
        if save_processed:
            import yaml
            
            output_files = {
                "processed_agents.yml": agents_config,
                "processed_components.yml": components_config,
                "merged_config.yml": full_config
            }
            
            for filename, config_data in output_files.items():
                output_path = current_dir / filename
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, indent=2)
                logger.info(f"保存处理后的配置: {output_path}")
        
        # 7. 显示配置摘要
        logger.info("\n=== 配置处理完成 ===")
        logger.info("配置摘要:")
        logger.info(f"  - 组件数量: {len(full_config.get('components', []))}")
        logger.info(f"  - 控制器数量: {len(full_config.get('controllers', []))}")
        logger.info(f"  - 智能体数量: {len(full_config.get('agents', []))}")
        
        # 检查是否所有硬编码都已消除
        logger.info("\n检查硬编码消除情况:")
        
        # 示例：检查PID参数是否都来自配置常量
        pid_params_from_constants = 0
        total_pid_params = 0
        
        for controller in full_config.get('controllers', []):
            if controller.get('class') == 'PIDController':
                config = controller.get('config', {})
                for param in ['Kp', 'Ki', 'Kd', 'setpoint']:
                    if param in config:
                        total_pid_params += 1
                        # 这里简单检查值是否为数值类型（表示已被替换）
                        if isinstance(config[param], (int, float)):
                            pid_params_from_constants += 1
        
        if total_pid_params > 0:
            success_rate = (pid_params_from_constants / total_pid_params) * 100
            logger.info(f"  PID参数配置化率: {success_rate:.1f}% ({pid_params_from_constants}/{total_pid_params})")
        
        logger.info("✅ 配置处理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置处理失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)