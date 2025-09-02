#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用配置运行脚本 - Examples目录

本脚本通过调用根目录的run_universal_config模块来运行各种仿真示例，
优先使用universal_config.yml作为统一配置文件，集成调试、性能监控、
可视化等高级功能。

支持的示例类型：
- 智能体示例（agent_based）
- 渠道模型示例（canal_model）
- 非智能体示例（non_agent_based）
- 参数辨识示例（identification）
- 演示示例（demo）

运行方式：
1. 命令行参数：python run_universal_config.py --example <example_name>
2. 交互式菜单：python run_universal_config.py
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
    from core_lib.io.yaml_loader import SimulationBuilder
    from core_lib.io.yaml_writer import save_history_to_yaml
except ImportError as e:
    print(f"Error: Unable to import CHS-SDK module: {e}")
    print("Please ensure CHS-SDK is properly installed and Python path is set")
    sys.exit(1)

# 设置统一场景运行器可用性标志
UNIFIED_SCENARIO_AVAILABLE = False

def run_universal_config_from_file(config_path, debug_mode=False, performance_monitor=False, 
                                  show_progress=True, show_summary=True, enable_validation=True):
    """Run scenario from universal configuration file"""
    import logging
    import yaml
    logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise ValueError(f"Configuration file does not exist: {config_path}")
    
    # Try to load universal_config.yml format
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"Loading universal configuration: {config_path.name}")
    
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
                time_step = sim_config.get('time_step', sim_config.get('dt', 1.0))
                
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
        loader = SimulationBuilder(scenario_path=str(scenario_dir))
        harness = loader.load()
        
        logging.info("Starting simulation run...")
        results = harness.run_mas_simulation()
        logging.info("Simulation run completed")
        
        return results

UNIFIED_SCENARIO_AVAILABLE = True

class ExamplesUniversalConfigRunner:
    """Examples directory universal configuration runner"""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.examples = self._discover_examples()
        self.debug_mode = False
        self.performance_monitor = False
        self.visualization_enabled = False
        self.validation_enabled = False
    
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
            "mission_scenarios": "Mission场景示例 - 引绰济辽工程仿真",
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
                priority = 0
                
                if universal_config.exists():
                    config_path = universal_config
                    config_type = "universal"
                    priority = 3
                elif config_file.exists():
                    config_path = config_file
                    config_type = "traditional"
                    priority = 1
                
                if config_path:
                    example_key = f"{category}_{example_dir.name}"
                    examples[example_key] = {
                        "name": example_dir.name.replace("_", " ").title(),
                        "description": f"{category_name} - {example_dir.name}",
                        "category": category,
                        "path": str(example_dir.relative_to(self.examples_dir)),
                        "config_path": str(config_path),
                        "config_type": config_type,
                        "priority": priority
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
            "complex_networks": {
                "name": "复杂网络",
                "description": "分支网络系统仿真",
                "category": "agent_based",
                "path": "agent_based/05_complex_networks"
            },
            "pump_station": {
                "name": "泵站控制",
                "description": "泵站智能控制系统",
                "category": "agent_based",
                "path": "agent_based/08_pump_station_control"
            },
            "canal_pid_control": {
                "name": "渠道PID控制",
                "description": "渠道系统PID控制对比",
                "category": "canal_model",
                "path": "canal_model/canal_pid_control"
            },
            "canal_mpc_control": {
                "name": "渠道MPC控制",
                "description": "渠道系统MPC与PID控制",
                "category": "canal_model",
                "path": "canal_model/canal_mpc_pid_control"
            },
            "reservoir_identification": {
                "name": "水库参数辨识",
                "description": "水库库容曲线参数辨识",
                "category": "identification",
                "path": "identification/01_reservoir_storage_curve"
            },
            "simplified_demo": {
                "name": "简化演示",
                "description": "简化水库控制演示",
                "category": "demo",
                "path": "demo/simplified_reservoir_control"
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
            priority = 0
            
            if universal_config.exists():
                config_path = universal_config
                config_type = "universal"
                priority = 3
            elif config_file.exists():
                config_path = config_file
                config_type = "traditional"
                priority = 1
            
            if config_path:
                example["config_path"] = str(config_path)
                example["config_type"] = config_type
                example["priority"] = priority
                examples[key] = example
        
        return examples
    
    def run_example(self, example_key):
        """Run specified example"""
        if example_key not in self.examples:
            print(f"Error: Example '{example_key}' not found")
            return False
        
        example = self.examples[example_key]
        print(f"\n=== Running Example: {example['name']} ===")
        print(f"Description: {example['description']}")
        print(f"Category: {example['category']}")
        print(f"Configuration file: {example['config_path']} ({example['config_type']})")
        
        # Check if configuration file exists
        config_path = Path(example['config_path'])
        if not config_path.exists():
            print(f"Error: Configuration file does not exist: {config_path}")
            return False
        
        try:
            start_time = time.time()
            
            # Switch to example directory
            example_dir = self.examples_dir / example['path']
            original_cwd = os.getcwd()
            os.chdir(str(example_dir))
            
            print(f"\nWorking directory: {example_dir}")
            print("Starting simulation...")
            
            # Select running method based on configuration type
            results = None
            
            # Use universal configuration runner uniformly
            results = run_universal_config_from_file(
                config_path=str(config_path),
                debug_mode=self.debug_mode,
                performance_monitor=self.performance_monitor
            )
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            # Performance statistics
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n=== Simulation Completed ===")
            print(f"Execution time: {execution_time:.2f}s")
            
            if results and isinstance(results, dict):
                if 'time' in results:
                    print(f"Simulation steps: {len(results['time'])}")
                
                if self.performance_monitor:
                    self._show_performance_stats(results, execution_time)
                
                if self.debug_mode:
                    self._show_debug_info(results)
                
                if self.validation_enabled:
                    self._show_validation_results(results)
            
            return True
            
        except Exception as e:
            # Ensure working directory is restored
            os.chdir(original_cwd)
            print(f"Error: Exception occurred while running example: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False
    
    def _show_performance_stats(self, results, execution_time):
        """Show performance statistics"""
        print("\n=== Performance Statistics ===")
        print(f"Total execution time: {execution_time:.3f}s")
        
        if 'time' in results:
            sim_time = len(results['time'])
            print(f"Simulation steps: {sim_time}")
            if sim_time > 0:
                print(f"Average time per step: {execution_time/sim_time*1000:.2f}ms")
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            print(f"Memory usage: {memory_mb:.1f}MB")
            print(f"CPU usage: {cpu_percent:.1f}%")
        except ImportError:
            pass
        
        # Show result statistics
        if isinstance(results, dict):
            data_points = sum(len(v) if isinstance(v, list) else 1 for v in results.values())
            print(f"Total data points: {data_points}")
    
    def _show_debug_info(self, results):
        """Show debug information"""
        print("\n=== Debug Information ===")
        if isinstance(results, dict):
            print(f"Result keys: {list(results.keys())}")
            
            for key, values in results.items():
                if isinstance(values, list) and len(values) > 0:
                    if all(isinstance(v, (int, float)) for v in values):
                        print(f"{key}: {len(values)} data points, range[{min(values):.3f}, {max(values):.3f}]")
                    else:
                        print(f"{key}: {len(values)} data points")
                elif isinstance(values, dict):
                    print(f"{key}: dict type, {len(values)} keys")
                else:
                    print(f"{key}: {type(values).__name__} type")
        else:
            print(f"Result type: {type(results)}")
    
    def _show_validation_results(self, results):
        """Show validation results"""
        print("\n=== Validation Results ===")
        
        # Check basic data integrity
        if isinstance(results, dict):
            if 'time' in results:
                time_data = results['time']
                if len(time_data) > 0:
                    print(f"✓ Time series complete: {len(time_data)} time points")
                    print(f"  Time range: {min(time_data):.1f} - {max(time_data):.1f}")
                else:
                    print("✗ Time series is empty")
            
            # Check numerical stability
            numeric_keys = [k for k, v in results.items() 
                          if isinstance(v, list) and len(v) > 0 
                          and all(isinstance(x, (int, float)) for x in v)]
            
            stable_count = 0
            for key in numeric_keys:
                values = results[key]
                if len(values) > 1:
                    import statistics
                    try:
                        std_dev = statistics.stdev(values)
                        mean_val = statistics.mean(values)
                        cv = std_dev / abs(mean_val) if mean_val != 0 else float('inf')
                        if cv < 1.0:  # Coefficient of variation < 1 considered relatively stable
                            stable_count += 1
                    except:
                        pass
            
            if numeric_keys:
                print(f"✓ Numerical stability: {stable_count}/{len(numeric_keys)} variables relatively stable")
        
        print("Validation completed")
    
    def show_menu(self):
        """Show interactive menu"""
        print("\n=== CHS-SDK Examples Universal Configuration Runner ===")
        print("\nAvailable examples:")
        
        if not self.examples:
            print("No available example configuration files found")
            return None
        
        # Group by category and priority
        categories = {}
        for key, example in self.examples.items():
            category = example['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example))
        
        # Sort by priority (universal configuration first)
        for category in categories:
            categories[category].sort(key=lambda x: x[1]['priority'], reverse=True)
        
        index = 1
        key_map = {}
        
        for category, examples in categories.items():
            print(f"\n{category.upper()}:")
            for key, example in examples:
                if example['config_type'] == 'universal':
                    config_symbol = "🔧"
                else:
                    config_symbol = "⚙️"
                
                priority_symbol = "⭐" if example['priority'] >= 3 else ""
                print(f"  {index}. {example['name']} - {example['description']} {config_symbol}{priority_symbol}")
                key_map[str(index)] = key
                index += 1
        
        print(f"\n  {index}. Enable debug mode {'✓' if self.debug_mode else '✗'}")
        print(f"  {index+1}. Enable performance monitoring {'✓' if self.performance_monitor else '✗'}")
        print(f"  {index+2}. Enable visualization {'✓' if self.visualization_enabled else '✗'}")
        print(f"  {index+3}. Enable validation {'✓' if self.validation_enabled else '✗'}")
        print(f"  {index+4}. Refresh example list")
        print(f"  {index+5}. Exit")
        
        print("\nLegend: 🔧=Universal config file, ⚙️=Traditional config file, ⭐=Recommended")
        
        while True:
            try:
                choice = input("\nPlease select an example to run (enter number): ").strip()
                
                if choice in key_map:
                    return key_map[choice]
                elif choice == str(index):
                    self.debug_mode = not self.debug_mode
                    status = "enabled" if self.debug_mode else "disabled"
                    print(f"Debug mode {status}")
                elif choice == str(index+1):
                    self.performance_monitor = not self.performance_monitor
                    status = "enabled" if self.performance_monitor else "disabled"
                    print(f"Performance monitoring {status}")
                elif choice == str(index+2):
                    self.visualization_enabled = not self.visualization_enabled
                    status = "enabled" if self.visualization_enabled else "disabled"
                    print(f"Visualization {status}")
                elif choice == str(index+3):
                    self.validation_enabled = not self.validation_enabled
                    status = "enabled" if self.validation_enabled else "disabled"
                    print(f"Validation {status}")
                elif choice == str(index+4):
                    print("Refreshing example list...")
                    self.examples = self._discover_examples()
                    return "refresh"
                elif choice == str(index+5):
                    return None
                else:
                    print("Invalid selection, please try again")
            except KeyboardInterrupt:
                print("\nUser cancelled operation")
                return None
    
    def list_examples(self):
        """List all available examples"""
        print("\nAvailable examples:")
        if not self.examples:
            print("No available example configuration files found")
            return
        
        for key, example in self.examples.items():
            config_exists = "✓" if Path(example['config_path']).exists() else "✗"
            config_type = example['config_type']
            priority = "⭐" if example['priority'] >= 3 else ""
            print(f"  {key}: {example['name']} - {example['description']} [{config_type}] [{config_exists}] {priority}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="CHS-SDK Examples Universal Configuration Runner")
    parser.add_argument("--example", "-e", help="Name of the example to run")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    parser.add_argument("--performance", "-p", action="store_true", help="Enable performance monitoring")
    parser.add_argument("--visualization", "-v", action="store_true", help="Enable visualization")
    parser.add_argument("--validation", "-val", action="store_true", help="Enable validation")
    parser.add_argument("--list", "-l", action="store_true", help="List all available examples")
    
    args = parser.parse_args()
    
    runner = ExamplesUniversalConfigRunner()
    runner.debug_mode = args.debug
    runner.performance_monitor = args.performance
    runner.visualization_enabled = args.visualization
    runner.validation_enabled = args.validation
    
    if args.list:
        runner.list_examples()
        return
    
    if args.example:
        # Command line mode
        success = runner.run_example(args.example)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
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
            
            # Ask whether to continue
            try:
                continue_choice = input("\nContinue running other examples? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    break
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main()