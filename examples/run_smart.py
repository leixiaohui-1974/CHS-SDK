#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能运行器 - CHS-SDK统一入口

这个脚本提供了一个智能的统一入口来运行任何CHS-SDK仿真示例，
无论使用哪种配置文件格式。它会自动检测配置类型并选择最合适的运行方式。

支持的配置类型：
1. 传统多配置文件方式（config.yml, components.yml, topology.yml, agents.yml）
2. 统一配置文件方式（单一YAML文件）
3. 通用配置文件方式（universal_config.yml）
4. 硬编码方式（Python代码直接构建）

使用方式：
1. 自动检测并运行：python run_smart.py <path_to_example>
2. 指定配置类型：python run_smart.py <path_to_example> --type <config_type>
3. 列出所有示例：python run_smart.py --list
4. 交互式菜单：python run_smart.py

示例：
  python run_smart.py agent_based/06_centralized_emergency_override
  python run_smart.py mission_example_3/01_enhanced_perception
  python run_smart.py canal_model/canal_pid_control
  python run_smart.py --list
"""

# 设置环境变量强制使用UTF-8编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

import sys
import argparse
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType, ConfigInfo
except ImportError as e:
    print(f"错误：无法导入统一配置管理器: {e}")
    print("请确保已正确安装CHS-SDK并设置了Python路径")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartRunner:
    """智能运行器类"""
    
    def __init__(self):
        """初始化智能运行器"""
        self.config_manager = UnifiedConfigManager()
        self.examples_dir = Path(__file__).parent
        self.project_root = Path(__file__).parent.parent
        
        # 运行器映射
        self.runners = {
            ConfigType.TRADITIONAL_MULTI: self._run_traditional,
            ConfigType.UNIFIED_SINGLE: self._run_unified,
            ConfigType.UNIVERSAL_CONFIG: self._run_universal,
            ConfigType.HARDCODED: self._run_hardcoded
        }
    
    def run_example(self, example_path: str, config_type: Optional[str] = None, 
                   debug: bool = False, **kwargs) -> Dict[str, Any]:
        """运行示例
        
        Args:
            example_path: 示例路径
            config_type: 强制指定的配置类型
            debug: 是否启用调试模式
            **kwargs: 其他参数
            
        Returns:
            Dict: 运行结果
        """
        # 解析路径
        path = self._resolve_path(example_path)
        if not path.exists():
            raise ValueError(f"示例路径不存在: {path}")
        
        # 检测配置类型
        if config_type:
            # 如果指定了配置类型，验证其有效性
            try:
                forced_type = ConfigType(config_type)
                config_info = ConfigInfo(
                    config_type=forced_type,
                    config_path=path,
                    config_files={},
                    metadata={},
                    description=f"强制指定为 {config_type}"
                )
            except ValueError:
                raise ValueError(f"无效的配置类型: {config_type}")
        else:
            # 自动检测配置类型
            config_info = self.config_manager.detect_config_type(path)
        
        if config_info.config_type == ConfigType.UNKNOWN:
            raise ValueError(f"无法识别的配置类型: {path}")
        
        # 显示检测结果
        print(f"\n=== 智能运行器 - CHS-SDK ===")
        print(f"示例路径: {path}")
        print(f"配置类型: {config_info.config_type.value}")
        print(f"描述: {config_info.description}")
        print(f"推荐运行器: {self.config_manager.get_runner_recommendation(config_info)}")
        print("=" * 50)
        
        # 运行示例
        start_time = time.time()
        try:
            runner_func = self.runners[config_info.config_type]
            result = runner_func(config_info, debug=debug, **kwargs)
            
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            result['config_info'] = config_info
            
            print(f"\n✅ 仿真完成！执行时间: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"\n❌ 仿真失败！执行时间: {execution_time:.2f}秒")
            print(f"错误信息: {e}")
            raise
    
    def _resolve_path(self, example_path: str) -> Path:
        """解析示例路径"""
        path = Path(example_path)
        
        # 如果是绝对路径，直接使用
        if path.is_absolute():
            return path
        
        # 如果是相对路径，尝试在examples目录下查找
        examples_path = self.examples_dir / path
        if examples_path.exists():
            return examples_path
        
        # 尝试在项目根目录下查找
        root_path = self.project_root / path
        if root_path.exists():
            return root_path
        
        # 返回原始路径（可能不存在，让后续处理）
        return path
    
    def _run_traditional(self, config_info: ConfigInfo, **kwargs) -> Dict[str, Any]:
        """运行传统多配置文件方式"""
        print("使用传统多配置文件运行器...")
        
        # 导入并运行传统运行器
        try:
            from examples.run_scenario import ExamplesScenarioRunner
            
            runner = ExamplesScenarioRunner()
            
            # 构建示例键名
            example_key = self._build_example_key(config_info.config_path)
            
            # 运行示例
            result = runner.run_example(example_key)
            return {
                'status': 'success',
                'runner_type': 'traditional_multi',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"传统运行器执行失败: {e}")
            raise
    
    def _run_unified(self, config_info: ConfigInfo, **kwargs) -> Dict[str, Any]:
        """运行统一配置文件方式"""
        print("使用统一配置文件运行器...")
        
        try:
            from run_unified_scenario import run_simulation_from_config
            
            # 获取配置文件路径
            config_file = config_info.config_files.get('unified')
            if not config_file:
                raise ValueError("未找到统一配置文件")
            
            # 运行仿真
            result = run_simulation_from_config(
                str(config_file),
                show_progress=kwargs.get('show_progress', True),
                show_summary=kwargs.get('show_summary', True)
            )
            
            return {
                'status': 'success',
                'runner_type': 'unified_single',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"统一运行器执行失败: {e}")
            raise
    
    def _run_universal(self, config_info: ConfigInfo, **kwargs) -> Dict[str, Any]:
        """运行通用配置文件方式"""
        print("使用通用配置文件运行器...")
        
        try:
            from examples.run_universal_config import ExamplesUniversalConfigRunner
            
            runner = ExamplesUniversalConfigRunner()
            
            # 构建示例键名
            example_key = self._build_example_key(config_info.config_path)
            
            # 运行示例
            result = runner.run_example(example_key)
            return {
                'status': 'success',
                'runner_type': 'universal_config',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"通用运行器执行失败: {e}")
            raise
    
    def _run_hardcoded(self, config_info: ConfigInfo, **kwargs) -> Dict[str, Any]:
        """运行硬编码方式"""
        print("使用硬编码运行器...")
        
        try:
            from examples.run_hardcoded import ExamplesHardcodedRunner
            
            runner = ExamplesHardcodedRunner()
            
            # 构建示例键名
            example_key = self._build_example_key(config_info.config_path)
            
            # 运行示例
            result = runner.run_example(example_key)
            return {
                'status': 'success',
                'runner_type': 'hardcoded',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"硬编码运行器执行失败: {e}")
            raise
    
    def _build_example_key(self, example_path: Path) -> str:
        """构建示例键名"""
        # 获取相对于examples目录的路径
        try:
            rel_path = example_path.relative_to(self.examples_dir)
            path_str = str(rel_path).replace('\\', '/').replace('\\', '/')
            
            # 硬编码示例的特殊映射
            hardcoded_mapping = {
                'watertank/02_parameter_identification': 'reservoir_identification',
                'non_agent_based/01_getting_started': 'getting_started',
                'non_agent_based/02_multi_component_systems': 'multi_component',
                'agent_based/03_event_driven_agents': 'event_driven_agents',
                'agent_based/04_hierarchical_control': 'hierarchical_control',
                'agent_based/05_complex_networks': 'complex_networks',
                'agent_based/08_pump_station_control': 'pump_station',
                'agent_based/09_hydropower_plant': 'hydropower_plant',
                'canal_model/canal_pid_control': 'canal_pid_control',
                'canal_model/canal_mpc_pid_control': 'canal_mpc_control',
                'identification/01_reservoir_storage_curve': 'reservoir_identification',
                'demo/simplified_reservoir_control': 'simplified_demo',
                'mission_example_1': 'mission_example_1',
                'mission_example_2': 'mission_example_2',
                'mission_example_3': 'mission_example_3',
                'mission_example_5': 'mission_example_5',
                'mission_scenarios': 'mission_scenarios'
            }
            
            # 检查是否有硬编码映射
            if path_str in hardcoded_mapping:
                return hardcoded_mapping[path_str]
            
            # 对于传统和通用配置，使用路径格式
            return path_str.replace('/', '_')
            
        except ValueError:
            # 如果不在examples目录下，使用目录名
            return example_path.name
    
    def list_examples(self) -> None:
        """列出所有可用的示例"""
        print("\n=== CHS-SDK 可用示例列表 ===")
        
        examples_by_type = self.config_manager.list_available_examples(self.examples_dir)
        
        for config_type, examples in examples_by_type.items():
            if examples:
                print(f"\n📁 {config_type.value.upper()} ({len(examples)}个示例):")
                print("-" * 50)
                
                for i, config_info in enumerate(examples, 1):
                    rel_path = config_info.config_path.relative_to(self.examples_dir)
                    print(f"  {i:2d}. {rel_path}")
                    print(f"      {config_info.description}")
                    if config_info.metadata.get('description'):
                        print(f"      📝 {config_info.metadata['description']}")
                    print()
        
        print("\n💡 使用方式:")
        print("  python run_smart.py <示例路径>")
        print("  例如: python run_smart.py agent_based/06_centralized_emergency_override")
    
    def show_interactive_menu(self) -> None:
        """显示交互式菜单"""
        print("\n=== CHS-SDK 智能运行器 - 交互式菜单 ===")
        print("1. 列出所有示例")
        print("2. 选择示例运行")
        print("3. 手动输入示例路径")
        print("4. 配置类型说明")
        print("5. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (1-5): ").strip()
                
                if choice == '1':
                    self.list_examples()
                elif choice == '2':
                    self._select_and_run_example()
                elif choice == '3':
                    example_path = input("请输入示例路径: ").strip()
                    if example_path:
                        try:
                            self.run_example(example_path)
                        except Exception as e:
                            print(f"运行失败: {e}")
                elif choice == '4':
                    self._show_config_types_help()
                elif choice == '5':
                    print("再见！")
                    break
                else:
                    print("无效选择，请输入1-5")
                    
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except EOFError:
                print("\n\n再见！")
                break
    
    def _select_and_run_example(self) -> None:
        """选择并运行示例"""
        print("\n=== 选择要运行的示例 ===")
        
        # 获取所有示例
        examples_by_type = self.config_manager.list_available_examples(self.examples_dir)
        
        # 创建示例列表
        all_examples = []
        for config_type, examples in examples_by_type.items():
            for example in examples:
                all_examples.append((config_type, example))
        
        if not all_examples:
            print("未找到任何示例")
            return
        
        # 按配置类型分组显示
        current_type = None
        example_index = 1
        
        for config_type, example in all_examples:
            if config_type != current_type:
                current_type = config_type
                print(f"\n📁 {config_type.value.upper()}:")
                print("-" * 50)
            
            rel_path = example.config_path.relative_to(self.examples_dir)
            print(f"  {example_index:2d}. {rel_path}")
            if example.description:
                print(f"      {example.description}")
            example_index += 1
        
        print(f"\n💡 共找到 {len(all_examples)} 个示例")
        
        # 让用户选择
        while True:
            try:
                choice = input(f"\n请选择要运行的示例 (1-{len(all_examples)}) 或输入 'q' 返回主菜单: ").strip()
                
                if choice.lower() == 'q':
                    return
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(all_examples):
                        config_type, selected_example = all_examples[index]
                        rel_path = selected_example.config_path.relative_to(self.examples_dir)
                        
                        print(f"\n🚀 正在运行示例: {rel_path}")
                        print(f"📋 配置类型: {config_type.value}")
                        print(f"📝 描述: {selected_example.description}")
                        print("-" * 60)
                        
                        try:
                            result = self.run_example(str(rel_path))
                            print(f"\n✅ 示例运行完成！")
                            if result.get('status') == 'success':
                                print(f"🎯 运行器类型: {result.get('runner_type', 'unknown')}")
                        except Exception as e:
                            print(f"\n❌ 运行失败: {e}")
                        
                        # 询问是否继续选择其他示例
                        continue_choice = input("\n是否继续选择其他示例？(y/n): ").strip().lower()
                        if continue_choice != 'y':
                            return
                    else:
                        print(f"无效选择，请输入1-{len(all_examples)}")
                except ValueError:
                    print("请输入有效的数字")
                    
            except KeyboardInterrupt:
                print("\n操作已取消")
                return
            except EOFError:
                print("\n操作已取消")
                return
    
    def _show_config_types_help(self) -> None:
        """显示配置类型说明"""
        print("\n=== CHS-SDK 配置类型说明 ===")
        print()
        print("🔧 1. 传统多配置文件方式 (Traditional Multi-Config)")
        print("   - 使用多个分离的YAML文件")
        print("   - 文件: config.yml, components.yml, topology.yml, agents.yml")
        print("   - 适合: 复杂项目，团队协作，模块化开发")
        print("   - 运行器: run_scenario.py")
        print()
        print("📄 2. 统一配置文件方式 (Unified Single Config)")
        print("   - 使用单一YAML文件包含所有配置")
        print("   - 文件: unified_config.yml, scenario_config.yml等")
        print("   - 适合: 中等复杂度项目，快速原型开发")
        print("   - 运行器: run_unified_scenario.py")
        print()
        print("🌟 3. 通用配置文件方式 (Universal Config)")
        print("   - 使用增强的配置文件，包含调试、监控等高级功能")
        print("   - 文件: universal_config.yml")
        print("   - 适合: 生产环境，需要完整功能的项目")
        print("   - 运行器: run_universal_config.py")
        print()
        print("💻 4. 硬编码方式 (Hardcoded)")
        print("   - 直接在Python代码中构建仿真")
        print("   - 文件: Python脚本")
        print("   - 适合: 快速测试，算法验证，教学演示")
        print("   - 运行器: run_hardcoded.py")
        print()
        print("💡 智能运行器会自动检测配置类型并选择最合适的运行方式！")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CHS-SDK智能运行器 - 自动检测配置类型并运行仿真示例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_smart.py agent_based/06_centralized_emergency_override
  python run_smart.py mission_example_3/01_enhanced_perception
  python run_smart.py --list
  python run_smart.py --help-config
        """
    )
    
    parser.add_argument(
        'example_path',
        nargs='?',
        help='示例路径（相对于examples目录或绝对路径）'
    )
    
    parser.add_argument(
        '--type',
        choices=['traditional_multi', 'unified_single', 'universal_config', 'hardcoded'],
        help='强制指定配置类型'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用示例'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--help-config',
        action='store_true',
        help='显示配置类型说明'
    )
    
    args = parser.parse_args()
    
    # 创建智能运行器
    runner = SmartRunner()
    
    try:
        if args.help_config:
            runner._show_config_types_help()
        elif args.list:
            runner.list_examples()
        elif args.example_path:
            runner.run_example(
                args.example_path,
                config_type=args.type,
                debug=args.debug
            )
        else:
            # 显示交互式菜单
            runner.show_interactive_menu()
            
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"运行失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()