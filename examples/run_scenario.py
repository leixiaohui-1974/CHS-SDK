#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景运行脚本 - Examples目录

本脚本通过调用根目录的run_scenario模块来运行各种仿真示例，
使用传统的多配置文件方式（config.yml, components.yml, topology.yml, agents.yml）。

支持的示例类型：
- 智能体示例（agent_based）
- 渠道模型示例（canal_model）
- 非智能体示例（non_agent_based）
- 参数辨识示例（identification）
- 演示示例（demo）

运行方式：
1. 命令行参数：python run_scenario.py --example <example_name>
2. 交互式菜单：python run_scenario.py
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
    print(f"错误：无法导入CHS-SDK模块: {e}")
    print("请确保已正确安装CHS-SDK并设置了Python路径")
    sys.exit(1)

def run_scenario_from_config(scenario_path, agents_file="agents.yml"):
    """从配置文件运行场景"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    scenario_path = Path(scenario_path)
    if not scenario_path.is_dir():
        raise ValueError(f"场景路径不是有效目录: {scenario_path}")
    
    logging.info(f"加载场景: {scenario_path.name}")
    loader = SimulationBuilder(scenario_path=str(scenario_path), agents_file=agents_file)
    harness = loader.load()
    
    logging.info("开始仿真运行...")
    results = harness.run_mas_simulation()
    logging.info("仿真运行完成")
    
    return results

class ExamplesScenarioRunner:
    """Examples目录场景运行器"""
    
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
            "mission_scenarios": "Mission Scenario Examples",
            "mission_data": "Mission Shared Data Files"
        }
        
        for category, category_name in categories.items():
            category_path = self.examples_dir / category
            if not category_path.exists():
                continue
            
            for example_dir in category_path.iterdir():
                if not example_dir.is_dir():
                    continue
                
                # 检查是否有配置文件
                config_file = example_dir / "config.yml"
                if config_file.exists():
                    example_key = f"{category}_{example_dir.name}"
                    examples[example_key] = {
                        "name": example_dir.name.replace("_", " ").title(),
                        "description": f"{category_name} - {example_dir.name}",
                        "category": category,
                        "path": str(example_dir.relative_to(self.examples_dir)),
                        "config_path": str(config_file)
                    }
        
        # 手动添加一些特殊示例
        special_examples = {
            "getting_started": {
                "name": "入门示例",
                "description": "基础水库-闸门系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/01_getting_started",
                "config_path": str(self.examples_dir / "non_agent_based/01_getting_started/config.yml")
            },
            "multi_component": {
                "name": "多组件系统",
                "description": "复杂多组件水利系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/02_multi_component_systems",
                "config_path": str(self.examples_dir / "non_agent_based/02_multi_component_systems/config.yml")
            },
            "event_driven_agents": {
                "name": "事件驱动智能体",
                "description": "基于事件的智能体控制系统",
                "category": "agent_based",
                "path": "agent_based/03_event_driven_agents",
                "config_path": str(self.examples_dir / "agent_based/03_event_driven_agents/config.yml")
            },
            "canal_pid_control": {
                "name": "渠道PID控制",
                "description": "渠道系统PID控制对比",
                "category": "canal_model",
                "path": "canal_model/canal_pid_control",
                "config_path": str(self.examples_dir / "canal_model/canal_pid_control/config.yml")
            },
            "reservoir_identification": {
                "name": "水库参数辨识",
                "description": "水库库容曲线参数辨识",
                "category": "identification",
                "path": "identification/01_reservoir_storage_curve",
                "config_path": str(self.examples_dir / "identification/01_reservoir_storage_curve/config.yml")
            }
        }
        
        # 只添加实际存在配置文件的示例
        for key, example in special_examples.items():
            if Path(example["config_path"]).exists():
                examples[key] = example
        
        return examples
    
    def run_example(self, example_key):
        """运行指定示例"""
        if example_key not in self.examples:
            print(f"错误：未找到示例 '{example_key}'")
            return False
        
        example = self.examples[example_key]
        print(f"\n=== 运行示例：{example['name']} ===")
        print(f"描述：{example['description']}")
        print(f"类别：{example['category']}")
        print(f"配置文件：{example['config_path']}")
        
        # 检查配置文件是否存在
        config_path = Path(example['config_path'])
        if not config_path.exists():
            print(f"错误：配置文件不存在: {config_path}")
            return False
        
        try:
            start_time = time.time()
            
            # 切换到示例目录
            example_dir = self.examples_dir / example['path']
            original_cwd = os.getcwd()
            os.chdir(str(example_dir))
            
            print(f"\n工作目录：{example_dir}")
            print("开始仿真...")
            
            # 调用run_scenario模块
            results = run_scenario_from_config(
                scenario_path=str(example_dir)
            )
            
            # 恢复原工作目录
            os.chdir(original_cwd)
            
            # 性能统计
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n=== 仿真完成 ===")
            print(f"执行时间：{execution_time:.2f}秒")
            
            if results and isinstance(results, dict):
                if 'time' in results:
                    print(f"仿真步数：{len(results['time'])}")
                
                if self.performance_monitor:
                    self._show_performance_stats(results, execution_time)
                
                if self.debug_mode:
                    self._show_debug_info(results)
            
            return True
            
        except Exception as e:
            # 确保恢复工作目录
            os.chdir(original_cwd)
            print(f"错误：运行示例时发生异常: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False
    
    def _show_performance_stats(self, results, execution_time):
        """显示性能统计信息"""
        print("\n=== 性能统计 ===")
        print(f"总执行时间：{execution_time:.3f}秒")
        
        if 'time' in results:
            sim_time = len(results['time'])
            print(f"仿真步数：{sim_time}")
            if sim_time > 0:
                print(f"平均每步耗时：{execution_time/sim_time*1000:.2f}毫秒")
        
        # 内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"内存使用：{memory_mb:.1f}MB")
        except ImportError:
            pass
    
    def _show_debug_info(self, results):
        """显示调试信息"""
        print("\n=== 调试信息 ===")
        if isinstance(results, dict):
            print(f"结果键值：{list(results.keys())}")
            
            for key, values in results.items():
                if isinstance(values, list) and len(values) > 0:
                    if all(isinstance(v, (int, float)) for v in values):
                        print(f"{key}: {len(values)}个数据点, 范围[{min(values):.3f}, {max(values):.3f}]")
                    else:
                        print(f"{key}: {len(values)}个数据点")
        else:
            print(f"结果类型：{type(results)}")
    
    def show_menu(self):
        """显示交互式菜单"""
        print("\n=== CHS-SDK Examples 场景运行器 ===")
        print("\n可用示例：")
        
        if not self.examples:
            print("未找到任何可用的示例配置文件")
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
                print(f"  {index}. {example['name']} - {example['description']}")
                key_map[str(index)] = key
                index += 1
        
        print(f"\n  {index}. 启用调试模式")
        print(f"  {index+1}. 启用性能监控")
        print(f"  {index+2}. 刷新示例列表")
        print(f"  {index+3}. 退出")
        
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
                    print("无效选择，请重新输入")
            except KeyboardInterrupt:
                print("\n用户取消操作")
                return None
    
    def list_examples(self):
        """列出所有可用示例"""
        print("\n可用示例：")
        if not self.examples:
            print("未找到任何可用的示例配置文件")
            return {}
        
        for key, example in self.examples.items():
            config_exists = "✓" if Path(example['config_path']).exists() else "✗"
            print(f"  {key}: {example['name']} - {example['description']} [{config_exists}]")
        
        return self.examples

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CHS-SDK Examples 场景运行器")
    parser.add_argument("--example", "-e", help="要运行的示例名称")
    parser.add_argument("--debug", "-d", action="store_true", help="启用调试模式")
    parser.add_argument("--performance", "-p", action="store_true", help="启用性能监控")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用示例")
    
    args = parser.parse_args()
    
    runner = ExamplesScenarioRunner()
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
                print("再见！")
                break
            elif example_key == "refresh":
                continue
            
            success = runner.run_example(example_key)
            if not success:
                continue
            
            # 询问是否继续
            try:
                continue_choice = input("\n是否继续运行其他示例？(y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '是']:
                    break
            except KeyboardInterrupt:
                print("\n再见！")
                break

if __name__ == "__main__":
    main()