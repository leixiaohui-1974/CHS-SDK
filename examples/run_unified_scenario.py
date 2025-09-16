#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一场景运行脚本 - Examples目录

本脚本通过调用根目录的run_unified_scenario模块来运行各种仿真示例，
优先使用universal_config.yml作为统一配置文件。

支持的示例类型：
- 智能体示例（agent_based）
- 渠道模型示例（canal_model）
- 非智能体示例（non_agent_based）
- 参数辨识示例（identification）
- 演示示例（demo）

运行方式：
1. 命令行参数：python run_unified_scenario.py --example <example_name>
2. 交互式菜单：python run_unified_scenario.py
"""

# 设置环境变量强制使用UTF-8编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

import sys
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.io.yaml_loader import YamlSimulationLoader
    from core_lib.io.yaml_writer import save_history_to_yaml
except ImportError as e:
    print(f"错误：无法导入CHS-SDK模块: {e}")
    print("请确保已正确安装CHS-SDK并设置了Python路径")
    sys.exit(1)

def run_unified_scenario_from_config(config_path, show_progress=True, show_summary=True, debug=False, performance_monitor=False, legacy_mode=False):
    """从统一配置文件运行场景"""
    import logging
    import yaml
    logging.basicConfig(level=logging.INFO)
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise ValueError(f"配置文件不存在: {config_path}")
    
    # 尝试加载universal_config.yml格式
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"加载统一配置: {config_path.name}")
    
    # 如果是universal_config格式，使用简化的加载方式
    if 'simulation' in config:
        # 这是universal_config格式，需要特殊处理
        logging.info("检测到universal_config格式，使用统一仿真运行器")
        # 导入并使用统一仿真运行器
        try:
            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from run_unified_scenario import run_simulation_from_config
            results = run_simulation_from_config(
                config_path=str(config_path),
                show_progress=show_progress,
                show_summary=show_summary
            )
            return results
        except ImportError as e:
            # 如果导入失败，尝试使用本地实现
            logging.warning(f"无法导入统一仿真运行器: {e}，使用基础实现")
            # 对于universal_config格式，创建一个简化的仿真运行
            try:
                from core_lib.core_engine.testing.simulation_harness import SimulationHarness
                
                # 获取仿真参数
                sim_config = config.get('simulation', {})
                duration = sim_config.get('end_time', sim_config.get('duration', 100))
                time_step = sim_config.get('time_step', sim_config['time_step'])
                
                # 创建简化的仿真
                harness = SimulationHarness({'duration': duration, 'dt': time_step})
                
                # 运行仿真
                results = harness.run_mas_simulation()
                
                logging.info(f"Universal config simulation completed with {len(results.get('time', []))} steps")
                return {'status': 'completed', 'message': 'Universal config format processed with basic implementation', 'results': results}
            except Exception as basic_e:
                logging.error(f"基础实现也失败: {basic_e}")
                return {'status': 'failed', 'error': f'Both unified and basic implementations failed: {e}, {basic_e}'}
        except Exception as e:
            logging.error(f"运行统一仿真时出错: {e}")
            return {'status': 'failed', 'error': str(e)}
    else:
        # 标准多文件格式
        scenario_dir = config_path.parent
        loader = YamlSimulationLoader(scenario_path=str(scenario_dir))
        harness = loader.load()
        
        logging.info("开始仿真运行...")
        results = harness.run_mas_simulation()
        logging.info("仿真运行完成")
        
        return results

class ExamplesUnifiedScenarioRunner:
    """Examples目录统一场景运行器"""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.examples = self._discover_examples()
        self.debug_mode = False
        self.performance_monitor = False
    
    def _discover_examples(self):
        """自动发现可用的示例"""
        examples = {}
        
        # 扫描各个子目录
        categories = {
            "agent_based": "智能体示例",
            "canal_model": "渠道模型示例", 
            "non_agent_based": "非智能体示例",
            "identification": "参数辨识示例",
            "demo": "演示示例",
            "notebooks": "笔记本示例",
            "llm_integration": "LLM集成示例",
            "watertank_refactored": "重构水箱示例",
            "mission_example_1": "Mission Example 1 - Basic Physics & Advanced Control",
            "mission_example_2": "Mission Example 2 - Closed-loop Control Systems",
            "mission_example_3": "Mission Example 3 - Enhanced Perception Systems",
            "mission_example_5": "Mission Example 5 - Turbine Gate Simulation",
            "mission_scenarios": "Mission场景示例",
            "mission_data": "Mission Shared Data Files"
        }
        
        for category, category_name in categories.items():
            category_path = self.examples_dir / category
            if not category_path.exists():
                continue
            
            for example_dir in category_path.iterdir():
                if not example_dir.is_dir():
                    continue
                
                # 优先查找universal_config.yml，其次是config.yml
                universal_config = example_dir / "universal_config.yml"
                config_file = example_dir / "config.yml"
                
                config_path = None
                config_type = None
                
                if universal_config.exists():
                    config_path = universal_config
                    config_type = "universal"
                elif config_file.exists():
                    config_path = config_file
                    config_type = "traditional"
                
                if config_path:
                    example_key = f"{category}_{example_dir.name}"
                    examples[example_key] = {
                        "name": example_dir.name.replace("_", " ").title(),
                        "description": f"{category_name} - {example_dir.name}",
                        "category": category,
                        "path": str(example_dir.relative_to(self.examples_dir)),
                        "config_path": str(config_path),
                        "config_type": config_type
                    }
        
        # 手动添加一些特殊示例
        special_examples = {
            "getting_started": {
                "name": "入门示例",
                "description": "基础水库-闸门系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/01_getting_started"
            },
            "multi_component": {
                "name": "多组件系统",
                "description": "复杂多组件水利系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/02_multi_component_systems"
            },
            "event_driven_agents": {
                "name": "事件驱动智能体",
                "description": "基于事件的智能体控制系统",
                "category": "agent_based",
                "path": "agent_based/03_event_driven_agents"
            },
            "hierarchical_control": {
                "name": "分层控制",
                "description": "分层分布式控制系统",
                "category": "agent_based",
                "path": "agent_based/04_hierarchical_control"
            },
            "canal_pid_control": {
                "name": "渠道PID控制",
                "description": "渠道系统PID控制对比",
                "category": "canal_model",
                "path": "canal_model/canal_pid_control"
            },
            "reservoir_identification": {
                "name": "水库参数辨识",
                "description": "水库库容曲线参数辨识",
                "category": "identification",
                "path": "identification/01_reservoir_storage_curve"
            }
        }
        
        # 为特殊示例查找配置文件
        for key, example in special_examples.items():
            example_dir = self.examples_dir / example["path"]
            if not example_dir.exists():
                continue
            
            # 优先查找universal_config.yml
            universal_config = example_dir / "universal_config.yml"
            config_file = example_dir / "config.yml"
            
            config_path = None
            config_type = None
            
            if universal_config.exists():
                config_path = universal_config
                config_type = "universal"
            elif config_file.exists():
                config_path = config_file
                config_type = "traditional"
            
            if config_path:
                example["config_path"] = str(config_path)
                example["config_type"] = config_type
                examples[key] = example
        
        return examples
    
    def run_example(self, example_key):
        """运行指定示例"""
        if example_key not in self.examples:
            print(f"Error: Example '{example_key}' not found")
            return False
        
        example = self.examples[example_key]
        print(f"\n=== Running Example: {example['name']} ===")
        print(f"Description: {example['description']}")
        print(f"Category: {example['category']}")
        print(f"Config File: {example['config_path']} ({example['config_type']})")
        
        # 检查配置文件是否存在
        config_path = Path(example['config_path'])
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}")
            return False
        
        try:
            start_time = time.time()
            
            # 切换到示例目录
            example_dir = self.examples_dir / example['path']
            original_cwd = os.getcwd()
            os.chdir(str(example_dir))
            
            print(f"\nWorking Directory: {example_dir}")
            print("Starting simulation...")
            
            # 调用run_unified_scenario模块
            if example['config_type'] == 'universal':
                results = run_unified_scenario_from_config(
                    config_path=str(config_path),
                    debug=self.debug_mode,
                    performance_monitor=self.performance_monitor
                )
            else:
                # 对于传统配置文件，尝试转换为统一格式运行
                print("Note: Using legacy config file, attempting to convert to unified format")
                results = run_unified_scenario_from_config(
                    config_path=str(config_path),
                    debug=self.debug_mode,
                    performance_monitor=self.performance_monitor,
                    legacy_mode=True
                )
            
            # 恢复原工作目录
            os.chdir(original_cwd)
            
            # 性能统计
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n=== Simulation Complete ===")
            print(f"Execution Time: {execution_time:.2f} seconds")
            
            if results and isinstance(results, dict):
                if 'time' in results:
                    print(f"Simulation Steps: {len(results['time'])}")
                
                if self.performance_monitor:
                    self._show_performance_stats(results, execution_time)
                
                if self.debug_mode:
                    self._show_debug_info(results)
            
            return True
            
        except Exception as e:
            # 确保恢复工作目录
            os.chdir(original_cwd)
            print(f"Error: Exception occurred while running example: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False
    
    def _show_performance_stats(self, results, execution_time):
        """显示性能统计信息"""
        print("\n=== Performance Statistics ===")
        print(f"Total Execution Time: {execution_time:.3f} seconds")
        
        if 'time' in results:
            sim_time = len(results['time'])
            print(f"Simulation Steps: {sim_time}")
            if sim_time > 0:
                print(f"Average Time per Step: {execution_time/sim_time*1000:.2f} ms")
        
        # 内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"Memory Usage: {memory_mb:.1f}MB")
        except ImportError:
            pass
    
    def _show_debug_info(self, results):
        """显示调试信息"""
        print("\n=== Debug Information ===")
        if isinstance(results, dict):
            print(f"Result Keys: {list(results.keys())}")
            
            for key, values in results.items():
                if isinstance(values, list) and len(values) > 0:
                    if all(isinstance(v, (int, float)) for v in values):
                        print(f"{key}: {len(values)} data points, range [{min(values):.3f}, {max(values):.3f}]")
                    else:
                        print(f"{key}: {len(values)} data points")
        else:
            print(f"Result Type: {type(results)}")
    
    def show_menu(self):
        """显示交互式菜单"""
        print("\n=== CHS-SDK Examples Unified Scenario Runner ===")
        print("\nAvailable Examples:")
        
        if not self.examples:
            print("No available example configuration files found")
            return None
        
        # 按类别分组显示
        categories = {}
        for key, example in self.examples.items():
            category = example['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example))
        
        index = 1
        key_map = {}
        
        for category, examples in categories.items():
            print(f"\n{category.upper()}:")
            for key, example in examples:
                config_type_symbol = "🔧" if example['config_type'] == 'universal' else "⚙️"
                print(f"  {index}. {example['name']} - {example['description']} {config_type_symbol}")
                key_map[str(index)] = key
                index += 1
        
        print(f"\n  {index}. 启用调试模式")
        print(f"  {index+1}. 启用性能监控")
        print(f"  {index+2}. 刷新示例列表")
        print(f"  {index+3}. 退出")
        
        print("\n图例：🔧=统一配置文件, ⚙️=传统配置文件")
        
        while True:
            try:
                choice = input("\n请选择要运行的示例（输入数字）：").strip()
                
                if choice in key_map:
                    return key_map[choice]
                elif choice == str(index):
                    self.debug_mode = not self.debug_mode
                    status = "启用" if self.debug_mode else "禁用"
                    print(f"调试模式已{status}")
                elif choice == str(index+1):
                    self.performance_monitor = not self.performance_monitor
                    status = "启用" if self.performance_monitor else "禁用"
                    print(f"性能监控已{status}")
                elif choice == str(index+2):
                    print("正在刷新示例列表...")
                    self.examples = self._discover_examples()
                    return "refresh"
                elif choice == str(index+3):
                    return None
                else:
                    print("Invalid selection, please try again")
            except KeyboardInterrupt:
                print("\nUser cancelled operation")
                return None
    
    def list_examples(self):
        """列出所有可用示例"""
        print("\nAvailable Examples:")
        if not self.examples:
            print("No available example configuration files found")
            return
        
        for key, example in self.examples.items():
            config_exists = "✓" if Path(example['config_path']).exists() else "✗"
            config_type = example['config_type']
            print(f"  {key}: {example['name']} - {example['description']} [{config_type}] [{config_exists}]")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CHS-SDK Examples Unified Scenario Runner")
    parser.add_argument("--example", "-e", help="Example name to run")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    parser.add_argument("--performance", "-p", action="store_true", help="Enable performance monitoring")
    parser.add_argument("--list", "-l", action="store_true", help="List all available examples")
    
    args = parser.parse_args()
    
    runner = ExamplesUnifiedScenarioRunner()
    runner.debug_mode = args.debug
    runner.performance_monitor = args.performance
    
    if args.list:
        runner.list_examples()
        return
    
    if args.example:
        # 命令行模式
        success = runner.run_example(args.example)
        sys.exit(0 if success else 1)
    else:
        # 交互式模式
        while True:
            example_key = runner.show_menu()
            if example_key is None:
                print("Goodbye!")
                break
            elif example_key == "refresh":
                continue
            
            success = runner.run_example(example_key)
            if not success:
                continue
            
            # 询问是否继续
            try:
                continue_choice = input("\nContinue running other examples? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    break
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main()