# -*- coding: utf-8 -*-

"""
容错仿真场景运行脚本

修复了Windows系统下的GBK编码问题
"""
import logging
import sys
import os
import subprocess
from pathlib import Path

# Add the project root to the Python path to allow imports from core_lib
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.io.yaml_writer import save_history_to_yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """
    运行容错仿真场景
    """
    scenario_path = Path(__file__).parent
    agents_file = "agents.yml"
    
    logging.info(f"📁 场景目录: {scenario_path}")
    logging.info(f"--- 启动容错仿真场景 ---")

    try:
        # 设置环境变量确保UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # Initialize the loader with the path and the specified agents file
        logging.info(f"正在从 {scenario_path} 加载场景，使用代理文件: {agents_file}")
        loader = YamlSimulationLoader(scenario_path=str(scenario_path), agents_file=agents_file)

        # Load the simulation harness
        harness = loader.load()

        # Run the simulation
        logging.info("开始运行MAS仿真...")
        harness.run_mas_simulation()
        logging.info("仿真运行完成.")

        # Process and save results
        history = harness.history
        logging.info(f"仿真生成了 {len(history)} 步历史数据.")

        # Create a unique output file name based on the agents file
        output_filename = f"output_{Path(agents_file).stem}.yml"
        output_path = scenario_path / output_filename
        save_history_to_yaml(history, str(output_path))
        
        logging.info(f"✅ 仿真结果已保存到: {output_path}")
        
    except UnicodeDecodeError as e:
        logging.error(f"❌ 编码错误: {e}")
        logging.error("提示: 请确保所有配置文件使用UTF-8编码保存")
    except Exception as e:
        logging.error(f"❌ 仿真运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()