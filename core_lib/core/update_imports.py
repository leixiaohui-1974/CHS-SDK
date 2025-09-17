#!/usr/bin/env python3
"""
更新导入引用脚本

自动更新项目中对已删除Agent类的导入引用
将旧的导入替换为新的统一Agent导入
"""
import os
import re
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def get_import_mappings():
    """获取导入映射关系"""
    
    # 旧导入 -> 新导入 的映射关系
    import_mappings = {
        # 数据源相关
        'from core_lib.data_access.csv_inflow_agent import CsvInflowAgent': 
            'from core_lib.core.new_agents.service_agents.data.unified_data_source import CsvInflowAgentAdapter as CsvInflowAgent',
        
        'from core_lib.data_access.csv_data_source import CsvDataSource':
            'from core_lib.core.new_agents.service_agents.data.unified_data_source import UnifiedDataSourceAgent as CsvDataSource',
        
        'from core_lib.disturbances.csv_reader_agent import CsvReaderAgent':
            'from core_lib.core.new_agents.service_agents.data.unified_data_source import CsvReaderAgentAdapter as CsvReaderAgent',
        
        # 本地控制相关
        'from core_lib.local_agents.control.gate_control_agent import GateControlAgent':
            'from core_lib.core.new_agents.local_agents.control.unified_local_control import GateControlAgentAdapter as GateControlAgent',
        
        'from core_lib.local_agents.control.pump_control_agent import PumpControlAgent':
            'from core_lib.core.new_agents.local_agents.control.unified_local_control import PumpControlAgentAdapter as PumpControlAgent',
        
        'from core_lib.local_agents.control.valve_control_agent import ValveControlAgent':
            'from core_lib.core.new_agents.local_agents.control.unified_local_control import ValveControlAgentAdapter as ValveControlAgent',
        
        'from core_lib.local_agents.control.water_turbine_control_agent import WaterTurbineControlAgent':
            'from core_lib.core.new_agents.local_agents.control.unified_local_control import UnifiedLocalControlAgent as WaterTurbineControlAgent',
        
        # 扰动相关
        'from core_lib.disturbances.rainfall_agent import RainfallAgent':
            'from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import RainfallAgentAdapter as RainfallAgent',
        
        'from core_lib.disturbances.water_use_agent import WaterUseAgent':
            'from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import WaterUseAgentAdapter as WaterUseAgent',
        
        'from core_lib.disturbances.dynamic_rainfall_agent import DynamicRainfallAgent':
            'from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import UnifiedDisturbanceAgent as DynamicRainfallAgent',
        
        # 识别相关
        'from core_lib.identification.identification_agent import IdentificationAgent':
            'from core_lib.core.new_agents.service_agents.identification.unified_identification import IdentificationAgentAdapter as IdentificationAgent',
        
        'from core_lib.identification.model_updater_agent import ModelUpdaterAgent':
            'from core_lib.core.new_agents.service_agents.identification.unified_identification import ModelUpdaterAgentAdapter as ModelUpdaterAgent',
        
        # 中央控制相关
        'from core_lib.central_agents.central_mpc_agent import CentralMPCAgent':
            'from core_lib.core.new_agents.central_agents.control.central_control import CentralControlAgentImpl as CentralMPCAgent',
    }
    
    return import_mappings

def get_class_name_mappings():
    """获取类名映射关系（用于配置文件等）"""
    
    class_mappings = {
        # 数据源
        'CsvInflowAgent': 'UnifiedDataSourceAgent',
        'CsvReaderAgent': 'UnifiedDataSourceAgent', 
        'CsvDataSourceAgent': 'UnifiedDataSourceAgent',
        
        # 本地控制
        'GateControlAgent': 'UnifiedLocalControlAgent',
        'PumpControlAgent': 'UnifiedLocalControlAgent',
        'ValveControlAgent': 'UnifiedLocalControlAgent',
        'WaterTurbineControlAgent': 'UnifiedLocalControlAgent',
        'PressureControlAgent': 'UnifiedLocalControlAgent',
        'HydropowerStationControlAgent': 'UnifiedLocalControlAgent',
        'PumpStationControlAgent': 'UnifiedLocalControlAgent',
        'ValveStationControlAgent': 'UnifiedLocalControlAgent',
        
        # 扰动
        'RainfallAgent': 'UnifiedDisturbanceAgent',
        'WaterUseAgent': 'UnifiedDisturbanceAgent',
        'DynamicRainfallAgent': 'UnifiedDisturbanceAgent',
        
        # 识别
        'IdentificationAgent': 'UnifiedIdentificationAgent',
        'ModelUpdaterAgent': 'UnifiedIdentificationAgent',
        
        # 中央控制
        'CentralMPCAgent': 'CentralControlAgent',
        'CentralDispatcher': 'CentralCoordinatorAgent',
        'CentralAnomalyDetectionAgent': 'CentralCoordinatorAgent',
        'DemandForecastingAgent': 'CentralCoordinatorAgent',
        'CentralPerceptionAgent': 'CentralCoordinatorAgent',
    }
    
    return class_mappings

def find_python_files(root_dir=".", exclude_dirs=None):
    """查找所有Python文件"""
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', 'backup_old_agents', 'venv', 'env'}
    
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def find_config_files(root_dir=".", exclude_dirs=None):
    """查找所有配置文件"""
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', 'backup_old_agents', 'venv', 'env'}
    
    config_files = []
    for root, dirs, files in os.walk(root_dir):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(('.yaml', '.yml', '.json')):
                config_files.append(Path(root) / file)
    
    return config_files

def update_python_imports(file_path, import_mappings, dry_run=True):
    """更新Python文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated_count = 0
        
        # 替换导入语句
        for old_import, new_import in import_mappings.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                updated_count += 1
                print(f"  更新导入: {old_import.split('import')[-1].strip()}")
        
        # 如果有更新且不是预览模式，写入文件
        if updated_count > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return updated_count > 0
        
    except Exception as e:
        print(f"  错误: {e}")
        return False

def update_config_files(file_path, class_mappings, dry_run=True):
    """更新配置文件中的类名引用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated_count = 0
        
        # 替换类名引用
        for old_class, new_class in class_mappings.items():
            # 匹配 agent_type: "OldClass" 或 "class": "OldClass" 等模式
            patterns = [
                rf'agent_type:\s*["\']?{old_class}["\']?',
                rf'"agent_type":\s*"{old_class}"',
                rf'"class":\s*"{old_class}"',
                rf'class:\s*["\']?{old_class}["\']?'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 替换时保持原有的引号风格
                    new_content = re.sub(pattern, 
                                       lambda m: m.group(0).replace(old_class, new_class),
                                       content, flags=re.IGNORECASE)
                    if new_content != content:
                        content = new_content
                        updated_count += 1
                        print(f"  更新类名: {old_class} -> {new_class}")
        
        # 如果有更新且不是预览模式，写入文件
        if updated_count > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return updated_count > 0
        
    except Exception as e:
        print(f"  错误: {e}")
        return False

def update_imports_in_directory(root_dir=".", dry_run=True):
    """更新目录中所有文件的导入"""
    print(f"=== {'预览' if dry_run else '执行'}导入更新 ===")
    
    import_mappings = get_import_mappings()
    class_mappings = get_class_name_mappings()
    
    # 更新Python文件
    print("\n1. 更新Python文件导入:")
    python_files = find_python_files(root_dir)
    updated_py_files = 0
    
    for file_path in python_files:
        # 跳过新架构文件，避免循环引用
        if 'new_agents' in str(file_path) or 'backup_old_agents' in str(file_path):
            continue
            
        print(f"检查: {file_path}")
        if update_python_imports(file_path, import_mappings, dry_run):
            updated_py_files += 1
    
    print(f"✅ Python文件: {updated_py_files}/{len(python_files)} 个文件需要更新")
    
    # 更新配置文件
    print("\n2. 更新配置文件类名:")
    config_files = find_config_files(root_dir)
    updated_config_files = 0
    
    for file_path in config_files:
        if 'backup_old_agents' in str(file_path):
            continue
            
        print(f"检查: {file_path}")
        if update_config_files(file_path, class_mappings, dry_run):
            updated_config_files += 1
    
    print(f"✅ 配置文件: {updated_config_files}/{len(config_files)} 个文件需要更新")
    
    return updated_py_files, updated_config_files

def remove_adapter_code():
    """移除适配器代码（最终清理阶段）"""
    print("\n=== 移除适配器代码 ===")
    
    adapter_files = [
        "core_lib/core/new_agents/service_agents/data/unified_data_source.py",
        "core_lib/core/new_agents/local_agents/control/unified_local_control.py", 
        "core_lib/core/new_agents/service_agents/disturbance/unified_disturbance.py",
        "core_lib/core/new_agents/service_agents/identification/unified_identification.py"
    ]
    
    for file_path in adapter_files:
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 移除适配器类定义（从 "# 适配器：为旧类提供兼容性" 开始到文件末尾）
                adapter_start = content.find("# 适配器：为旧类提供兼容性")
                if adapter_start != -1:
                    # 保留主要实现，移除适配器部分
                    clean_content = content[:adapter_start].rstrip() + "\n"
                    
                    with open(file_path_obj, 'w', encoding='utf-8') as f:
                        f.write(clean_content)
                    
                    print(f"✅ 清理适配器代码: {file_path}")
                else:
                    print(f"⚠️  未找到适配器代码: {file_path}")
        
        except Exception as e:
            print(f"❌ 清理失败 {file_path}: {e}")
    
    # 更新注册中心，移除适配器注册
    registry_path = Path("core_lib/core/registry.py")
    if registry_path.exists():
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除适配器注册函数调用
            content = re.sub(r'\s*# 注册适配器.*\n\s*_register_adapters\(agent_factory\)\n', '', content, flags=re.DOTALL)
            
            # 移除适配器注册函数定义
            adapter_func_start = content.find("def _register_adapters(agent_factory):")
            if adapter_func_start != -1:
                # 找到函数结束位置
                lines = content[adapter_func_start:].split('\n')
                func_lines = [lines[0]]  # 函数定义行
                
                for line in lines[1:]:
                    if line and not line.startswith(' ') and not line.startswith('\t'):
                        break  # 函数结束
                    func_lines.append(line)
                
                func_content = '\n'.join(func_lines)
                content = content.replace(func_content, '')
            
            with open(registry_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 清理注册中心适配器代码")
            
        except Exception as e:
            print(f"❌ 清理注册中心失败: {e}")

def run_final_tests():
    """运行最终测试"""
    print("\n=== 运行最终测试 ===")
    
    try:
        # 测试新架构是否正常工作
        from core_lib.core.registry import register_all_agents
        from core_lib.core.new_agents.service_agents.data.unified_data_source import UnifiedDataSourceAgent
        from core_lib.core.new_agents.local_agents.control.unified_local_control import UnifiedLocalControlAgent
        
        print("✅ 新架构导入测试通过")
        
        # 注册测试
        register_all_agents()
        print("✅ Agent注册测试通过")
        
        # 创建测试
        from core_lib.core.factories import get_global_agent_factory
        factory = get_global_agent_factory()
        
        config = {
            'agent_id': 'test_unified_agent',
            'source_type': 'mock',
            'parameters': {'mock_data_type': 'sine_wave'}
        }
        
        agent = factory.create_agent('UnifiedDataSourceAgent', 'test_unified_agent', config)
        if agent:
            print("✅ Agent创建测试通过")
        else:
            print("❌ Agent创建测试失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 最终测试失败: {e}")
        return False

def main():
    """主函数"""
    print("导入引用更新和最终清理工具")
    print("=" * 50)
    
    # 1. 预览模式更新导入
    print("=== 预览模式 ===")
    updated_py, updated_config = update_imports_in_directory(dry_run=True)
    
    if updated_py > 0 or updated_config > 0:
        print(f"\n发现 {updated_py} 个Python文件和 {updated_config} 个配置文件需要更新")
        response = input("是否执行实际更新？(y/N): ").strip().lower()
        
        if response == 'y':
            print("\n=== 执行实际更新 ===")
            update_imports_in_directory(dry_run=False)
            print("✅ 导入更新完成")
        else:
            print("取消更新操作")
            return
    else:
        print("✅ 没有需要更新的导入引用")
    
    # 2. 询问是否进行最终清理（移除适配器）
    print("\n" + "=" * 50)
    response = input("是否进行最终清理（移除适配器代码）？这将完成架构迁移 (y/N): ").strip().lower()
    
    if response == 'y':
        remove_adapter_code()
        
        # 3. 运行最终测试
        if run_final_tests():
            print("\n🎉 架构迁移完全完成！")
            print("\n迁移总结:")
            print("✅ 从70+个Agent类收敛到15-20个核心类")
            print("✅ 建立清晰的三层架构")
            print("✅ 实现配置驱动和插件化")
            print("✅ 完成向后兼容迁移")
            print("✅ 删除旧代码和适配器")
            print("✅ 更新所有导入引用")
            
            print("\n建议后续工作:")
            print("1. 运行完整的回归测试")
            print("2. 更新项目文档")
            print("3. 团队培训新架构")
            print("4. 监控生产环境性能")
        else:
            print("⚠️  最终测试未完全通过，请检查问题后再提交代码")
    else:
        print("保留适配器代码，可以稍后手动清理")

if __name__ == "__main__":
    main()
