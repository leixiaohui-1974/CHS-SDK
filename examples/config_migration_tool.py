#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件迁移工具 - CHS-SDK

本工具帮助用户在不同配置文件格式之间进行转换：
- 传统多配置文件 ↔ 统一配置文件
- 传统多配置文件 ↔ 通用配置文件
- 统一配置文件 ↔ 通用配置文件

使用方式：
1. 交互式模式：python config_migration_tool.py
2. 命令行模式：python config_migration_tool.py --source <源路径> --target <目标格式> --output <输出路径>
"""

# 设置环境变量强制使用UTF-8编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType
except ImportError as e:
    print(f"错误：无法导入统一配置管理器: {e}")
    print("请确保已正确安装CHS-SDK并设置了Python路径")
    sys.exit(1)

class ConfigMigrationTool:
    """配置文件迁移工具"""
    
    def __init__(self):
        self.config_manager = UnifiedConfigManager()
        self.supported_conversions = {
            ConfigType.TRADITIONAL_MULTI: [ConfigType.UNIFIED_SINGLE, ConfigType.UNIVERSAL_CONFIG],
            ConfigType.UNIFIED_SINGLE: [ConfigType.TRADITIONAL_MULTI, ConfigType.UNIVERSAL_CONFIG],
            ConfigType.UNIVERSAL_CONFIG: [ConfigType.TRADITIONAL_MULTI, ConfigType.UNIFIED_SINGLE]
        }
    
    def migrate_config(self, source_path: str, target_format: str, output_path: str, 
                      dry_run: bool = False) -> Dict[str, Any]:
        """
        迁移配置文件
        
        Args:
            source_path: 源配置路径
            target_format: 目标格式 (traditional_multi, unified_single, universal_config)
            output_path: 输出路径
            dry_run: 是否为试运行（不实际写入文件）
            
        Returns:
            Dict: 迁移结果
        """
        # 解析路径
        source = Path(source_path)
        if not source.exists():
            raise ValueError(f"源路径不存在: {source}")
        
        # 检测源配置类型
        source_config = self.config_manager.detect_config_type(source)
        if source_config.config_type == ConfigType.UNKNOWN:
            raise ValueError(f"无法识别源配置类型: {source}")
        
        # 验证目标格式
        try:
            target_type = ConfigType(target_format)
        except ValueError:
            raise ValueError(f"无效的目标格式: {target_format}")
        
        # 检查是否支持转换
        if target_type not in self.supported_conversions.get(source_config.config_type, []):
            raise ValueError(
                f"不支持从 {source_config.config_type.value} 转换到 {target_type.value}"
            )
        
        # 如果源格式和目标格式相同，直接复制
        if source_config.config_type == target_type:
            print(f"⚠️  源格式和目标格式相同 ({target_type.value})，将直接复制文件")
            return self._copy_config(source, output_path, dry_run)
        
        print(f"🔄 开始迁移: {source_config.config_type.value} → {target_type.value}")
        print(f"📁 源路径: {source}")
        print(f"📁 目标路径: {output_path}")
        
        # 加载源配置
        source_data = self.config_manager.load_config(source_config)
        
        # 转换配置
        if not dry_run:
            converted_config = self.config_manager.convert_config(
                source_config, target_type, Path(output_path)
            )
            print(f"✅ 迁移完成！文件已保存到: {converted_config.config_files.get('unified', output_path)}")
        else:
            # 试运行模式：模拟转换过程
            print(f"🔍 试运行模式 - 转换成功，但未写入文件")
            print(f"📋 转换后的配置预览:")
            self._preview_config(source_data, target_type)
        
        return {
            'status': 'success',
            'source_type': source_config.config_type.value,
            'target_type': target_type.value,
            'source_path': str(source),
            'output_path': output_path,
            'dry_run': dry_run,
            'source_data': source_data
        }
    
    def _copy_config(self, source: Path, output_path: str, dry_run: bool) -> Dict[str, Any]:
        """复制配置文件"""
        import shutil
        
        output = Path(output_path)
        
        if not dry_run:
            if source.is_file():
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
            else:
                shutil.copytree(source, output, dirs_exist_ok=True)
            print(f"✅ 文件已复制到: {output}")
        else:
            print(f"🔍 试运行模式 - 将复制到: {output}")
        
        return {
            'status': 'copied',
            'source_path': str(source),
            'output_path': output_path,
            'dry_run': dry_run
        }
    
    def _save_converted_config(self, data: Dict[str, Any], target_type: ConfigType, 
                              output_path: str) -> None:
        """保存转换后的配置"""
        import yaml
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        if target_type == ConfigType.TRADITIONAL_MULTI:
            # 保存为多个文件
            for filename, content in data.items():
                file_path = output / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
        else:
            # 保存为单个文件
            filename = 'universal_config.yml' if target_type == ConfigType.UNIVERSAL_CONFIG else 'unified_config.yml'
            file_path = output / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def _preview_config(self, data: Dict[str, Any], target_type: ConfigType) -> None:
        """预览转换后的配置"""
        import yaml
        
        if target_type == ConfigType.TRADITIONAL_MULTI:
            for filename, content in data.items():
                print(f"\n📄 {filename}:")
                print(yaml.dump(content, default_flow_style=False, allow_unicode=True)[:500] + "...")
        else:
            print(yaml.dump(data, default_flow_style=False, allow_unicode=True)[:1000] + "...")
    
    def show_supported_conversions(self) -> None:
        """显示支持的转换类型"""
        print("\n=== 支持的配置格式转换 ===")
        print("\n📋 配置格式说明:")
        print("  • traditional_multi  - 传统多配置文件 (config.yml, components.yml, topology.yml, agents.yml)")
        print("  • unified_single     - 统一配置文件 (单个YAML文件包含所有配置)")
        print("  • universal_config   - 通用配置文件 (universal_config.yml)")
        
        print("\n🔄 支持的转换路径:")
        for source_type, target_types in self.supported_conversions.items():
            for target_type in target_types:
                print(f"  {source_type.value} → {target_type.value}")
    
    def show_interactive_menu(self) -> None:
        """显示交互式菜单"""
        print("\n=== CHS-SDK 配置文件迁移工具 ===")
        print("1. 迁移配置文件")
        print("2. 查看支持的转换类型")
        print("3. 试运行（预览转换结果）")
        print("4. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (1-4): ").strip()
                
                if choice == '1':
                    self._interactive_migrate()
                elif choice == '2':
                    self.show_supported_conversions()
                elif choice == '3':
                    self._interactive_migrate(dry_run=True)
                elif choice == '4':
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1-4")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
    
    def _interactive_migrate(self, dry_run: bool = False) -> None:
        """交互式迁移"""
        mode_text = "试运行" if dry_run else "迁移"
        print(f"\n=== {mode_text}配置文件 ===")
        
        # 获取源路径
        source_path = input("请输入源配置路径: ").strip()
        if not source_path:
            print("❌ 源路径不能为空")
            return
        
        # 检测源配置类型
        try:
            source = Path(source_path)
            source_config = self.config_manager.detect_config_type(source)
            print(f"📋 检测到源配置类型: {source_config.config_type.value}")
            print(f"📝 描述: {source_config.description}")
        except Exception as e:
            print(f"❌ 无法检测源配置: {e}")
            return
        
        # 显示可用的目标格式
        available_targets = self.supported_conversions.get(source_config.config_type, [])
        if not available_targets:
            print(f"❌ 不支持从 {source_config.config_type.value} 进行转换")
            return
        
        print(f"\n📋 可用的目标格式:")
        for i, target_type in enumerate(available_targets, 1):
            print(f"  {i}. {target_type.value}")
        
        # 选择目标格式
        try:
            choice = int(input("\n请选择目标格式 (输入数字): ").strip())
            if 1 <= choice <= len(available_targets):
                target_type = available_targets[choice - 1]
            else:
                print("❌ 无效选择")
                return
        except ValueError:
            print("❌ 请输入有效数字")
            return
        
        # 获取输出路径
        if not dry_run:
            output_path = input("请输入输出路径: ").strip()
            if not output_path:
                print("❌ 输出路径不能为空")
                return
        else:
            output_path = "preview_only"
        
        # 执行迁移
        try:
            result = self.migrate_config(
                source_path, target_type.value, output_path, dry_run=dry_run
            )
            print(f"\n✅ {mode_text}成功！")
        except Exception as e:
            print(f"❌ {mode_text}失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CHS-SDK 配置文件迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python config_migration_tool.py
  python config_migration_tool.py --source examples/agent_based/06_centralized_emergency_override --target unified_single --output converted/unified_config.yml
  python config_migration_tool.py --source examples/mission_example_3/01_enhanced_perception --target traditional_multi --output converted/traditional/ --dry-run
        """
    )
    
    parser.add_argument('--source', '-s', help='源配置路径')
    parser.add_argument('--target', '-t', 
                       choices=['traditional_multi', 'unified_single', 'universal_config'],
                       help='目标配置格式')
    parser.add_argument('--output', '-o', help='输出路径')
    parser.add_argument('--dry-run', action='store_true', help='试运行（不实际写入文件）')
    parser.add_argument('--help-formats', action='store_true', help='显示支持的格式转换')
    
    args = parser.parse_args()
    
    tool = ConfigMigrationTool()
    
    if args.help_formats:
        tool.show_supported_conversions()
        return
    
    if args.source and args.target and args.output:
        # 命令行模式
        try:
            result = tool.migrate_config(args.source, args.target, args.output, args.dry_run)
            print(f"\n✅ 迁移成功！")
            if args.dry_run:
                print("🔍 这是试运行，未实际写入文件")
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            sys.exit(1)
    else:
        # 交互式模式
        tool.show_interactive_menu()

if __name__ == "__main__":
    main()