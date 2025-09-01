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

import sys
import os
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

def run_universal_config_from_file(config_path, debug_mode=False, performance_monitor=False, 
                                  show_progress=True, show_summary=True, enable_validation=True):
    """从通用配置文件运行场景"""
    import logging
    import yaml
    logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise ValueError(f"配置文件不存在: {config_path}")
    
    # 尝试加载universal_config.yml格式
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"加载通用配置: {config_path.name}")
    
    # 如果是universal_config格式，使用简化的加载方式
    if 'simulation' in config and 'components' in config:
        # 这是universal_config格式，需要特殊处理
        logging.info("检测到universal_config格式，使用简化加载器")
        # 暂时返回模拟结果
        return {
            'status': 'completed', 
            'message': 'Universal config format detected but not fully implemented',
            'debug_enabled': debug_mode,
            'performance_monitor': performance_monitor
        }
    else:
        # 标准多文件格式
        scenario_dir = config_path.parent
        loader = SimulationBuilder(scenario_path=str(scenario_dir))
        harness = loader.load()
        
        logging.info("开始仿真运行...")
        results = harness.run_mas_simulation()
        logging.info("仿真运行完成")
        
        return results

UNIFIED_SCENARIO_AVAILABLE = True

class ExamplesUniversalConfigRunner:
    """Examples目录通用配置运行器"""
    
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
        """运行指定示例"""
        if example_key not in self.examples:
            print(f"错误：未找到示例 '{example_key}'")
            return False
        
        example = self.examples[example_key]
        print(f"\n=== 运行示例：{example['name']} ===")
        print(f"描述：{example['description']}")
        print(f"类别：{example['category']}")
        print(f"配置文件：{example['config_path']} ({example['config_type']})")
        
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
            
            # 根据配置类型选择运行方式
            results = None
            
            if example['config_type'] == 'universal':
                # 使用通用配置运行器
                try:
                    results = run_universal_config_from_file(
                        config_path=str(config_path),
                        debug=self.debug_mode,
                        performance_monitor=self.performance_monitor,
                        visualization=self.visualization_enabled,
                        validation=self.validation_enabled
                    )
                except Exception as e:
                    print(f"通用配置运行失败: {e}")
                    if UNIFIED_SCENARIO_AVAILABLE:
                        print("尝试使用统一场景运行器...")
                        results = run_unified_scenario_from_config(
                            config_path=str(config_path),
                            debug=self.debug_mode,
                            performance_monitor=self.performance_monitor
                        )
                    else:
                        raise
            else:
                # 对于传统配置文件，优先尝试统一场景运行器
                if UNIFIED_SCENARIO_AVAILABLE:
                    print("注意：使用传统配置文件，将通过统一场景运行器运行")
                    results = run_unified_scenario_from_config(
                        config_path=str(config_path),
                        debug=self.debug_mode,
                        performance_monitor=self.performance_monitor,
                        legacy_mode=True
                    )
                else:
                    print("错误：传统配置文件需要统一场景运行器支持")
                    return False
            
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
                
                if self.validation_enabled:
                    self._show_validation_results(results)
            
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
            cpu_percent = process.cpu_percent()
            print(f"内存使用：{memory_mb:.1f}MB")
            print(f"CPU使用率：{cpu_percent:.1f}%")
        except ImportError:
            pass
        
        # 显示结果统计
        if isinstance(results, dict):
            data_points = sum(len(v) if isinstance(v, list) else 1 for v in results.values())
            print(f"数据点总数：{data_points}")
    
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
                elif isinstance(values, dict):
                    print(f"{key}: 字典类型, {len(values)}个键")
                else:
                    print(f"{key}: {type(values).__name__}类型")
        else:
            print(f"结果类型：{type(results)}")
    
    def _show_validation_results(self, results):
        """显示验证结果"""
        print("\n=== 验证结果 ===")
        
        # 检查基本数据完整性
        if isinstance(results, dict):
            if 'time' in results:
                time_data = results['time']
                if len(time_data) > 0:
                    print(f"✓ 时间序列完整: {len(time_data)}个时间点")
                    print(f"  时间范围: {min(time_data):.1f} - {max(time_data):.1f}")
                else:
                    print("✗ 时间序列为空")
            
            # 检查数值稳定性
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
                        if cv < 1.0:  # 变异系数小于1认为相对稳定
                            stable_count += 1
                    except:
                        pass
            
            if numeric_keys:
                print(f"✓ 数值稳定性: {stable_count}/{len(numeric_keys)}个变量相对稳定")
        
        print("验证完成")
    
    def show_menu(self):
        """显示交互式菜单"""
        print("\n=== CHS-SDK Examples 通用配置运行器 ===")
        print("\n可用示例：")
        
        if not self.examples:
            print("未找到任何可用的示例配置文件")
            return None
        
        # 按类别和优先级分组显示
        categories = {}
        for key, example in self.examples.items():
            category = example['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example))
        
        # 按优先级排序（通用配置优先）
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
        
        print(f"\n  {index}. 启用调试模式 {'✓' if self.debug_mode else '✗'}")
        print(f"  {index+1}. 启用性能监控 {'✓' if self.performance_monitor else '✗'}")
        print(f"  {index+2}. 启用可视化 {'✓' if self.visualization_enabled else '✗'}")
        print(f"  {index+3}. 启用验证 {'✓' if self.validation_enabled else '✗'}")
        print(f"  {index+4}. 刷新示例列表")
        print(f"  {index+5}. 退出")
        
        print("\n图例：🔧=通用配置文件, ⚙️=传统配置文件, ⭐=推荐")
        
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
                    self.visualization_enabled = not self.visualization_enabled
                    status = "启用" if self.visualization_enabled else "禁用"
                    print(f"可视化已{status}")
                elif choice == str(index+3):
                    self.validation_enabled = not self.validation_enabled
                    status = "启用" if self.validation_enabled else "禁用"
                    print(f"验证已{status}")
                elif choice == str(index+4):
                    print("正在刷新示例列表...")
                    self.examples = self._discover_examples()
                    return "refresh"
                elif choice == str(index+5):
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
            return
        
        for key, example in self.examples.items():
            config_exists = "✓" if Path(example['config_path']).exists() else "✗"
            config_type = example['config_type']
            priority = "⭐" if example['priority'] >= 3 else ""
            print(f"  {key}: {example['name']} - {example['description']} [{config_type}] [{config_exists}] {priority}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CHS-SDK Examples 通用配置运行器")
    parser.add_argument("--example", "-e", help="要运行的示例名称")
    parser.add_argument("--debug", "-d", action="store_true", help="启用调试模式")
    parser.add_argument("--performance", "-p", action="store_true", help="启用性能监控")
    parser.add_argument("--visualization", "-v", action="store_true", help="启用可视化")
    parser.add_argument("--validation", "-val", action="store_true", help="启用验证")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用示例")
    
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