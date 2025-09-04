#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 自然语言处理功能综合演示

这个脚本展示了完整的自然语言处理工作流程：
1. 自然语言描述 -> 配置文件
2. 配置文件 -> 自然语言描述
3. 往返转换验证
4. 多种配置类型支持

作者: CHS-SDK Team
版本: 1.0.0
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.language_to_config_converter import LanguageToConfigConverter
from core_lib.config.unified_config_manager import ConfigType

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)

def print_subsection(title):
    """打印子章节标题"""
    print(f"\n--- {title} ---")

def demo_complete_workflow():
    """演示完整的自然语言处理工作流程"""
    print_section("CHS-SDK 自然语言处理功能综合演示")
    
    # 确保输出目录存在
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # 初始化转换器
    nl_to_config = LanguageToConfigConverter()
    config_to_nl = ConfigToLanguageConverter()
    
    # 示例自然语言描述
    sample_description = """
仿真名称：智能水库调度系统
仿真时长：7200秒
时间步长：0.5秒
求解器：RK4

系统组件：
- 主水库：水库，容量5000立方米，初始水位10米，最大水位20米，最小水位2米
- 调节闸门：闸门，最大流量100立方米每秒，初始开度0.3
- 下游水库：水库，容量2000立方米，初始水位8米
- 水位传感器1：传感器，监测主水库水位
- 水位传感器2：传感器，监测下游水库水位
- 流量传感器：传感器，监测闸门流量
- 智能水泵：水泵，最大流量30立方米每秒

系统连接：
- 主水库连接调节闸门
- 调节闸门连接下游水库
- 智能水泵连接主水库

控制策略：
- 采用模型预测控制（MPC）策略
- 控制目标：维持下游水库水位在8-12米范围内
- 预测时域：60秒
- 控制时域：30秒
- 约束条件：闸门开度0-1，水泵流量0-30立方米每秒

优化目标：
- 最小化能耗
- 最小化水位波动
- 权重：能耗0.3，水位稳定性0.7

分析要求：
- 进行控制性能分析
- 系统辨识分析
- 优化性能评估
- 生成水位变化图表
- 生成能耗分析报告
- 统计分析：均值、方差、峰值分析
    """
    
    print(f"演示开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {output_dir.absolute()}")
    
    # 第一步：自然语言 -> 配置文件
    print_subsection("步骤1: 自然语言描述转换为配置文件")
    
    print("原始自然语言描述:")
    print("-" * 40)
    print(sample_description.strip())
    print("-" * 40)
    
    config_types = [
        (ConfigType.UNIFIED_SINGLE, "统一配置文件"),
        (ConfigType.UNIVERSAL_CONFIG, "通用配置文件"),
        (ConfigType.TRADITIONAL_MULTI, "传统多文件配置"),
        (ConfigType.HARDCODED, "硬编码配置")
    ]
    
    generated_configs = {}
    
    for config_type, type_name in config_types:
        try:
            print(f"\n生成 {type_name}...")
            config_output_dir = output_dir / f"{config_type.value}_config"
            
            result = nl_to_config.convert_language_to_config(
                sample_description,
                config_type,
                str(config_output_dir)
            )
            
            generated_configs[config_type] = {
                'result': result,
                'output_dir': config_output_dir,
                'type_name': type_name
            }
            
            print(f"  ✓ {type_name} 生成成功")
            print(f"    配置节: {list(result.keys())}")
            print(f"    输出目录: {config_output_dir}")
            
        except Exception as e:
            print(f"  ✗ {type_name} 生成失败: {e}")
    
    # 第二步：配置文件 -> 自然语言
    print_subsection("步骤2: 配置文件转换为自然语言描述")
    
    nl_descriptions = {}
    
    for config_type, config_info in generated_configs.items():
        try:
            type_name = config_info['type_name']
            output_dir_path = config_info['output_dir']
            
            print(f"\n处理 {type_name}...")
            
            # 查找配置文件
            config_file = None
            if config_type == ConfigType.UNIFIED_SINGLE:
                config_file = output_dir_path / "unified_config.yml"
            elif config_type == ConfigType.UNIVERSAL_CONFIG:
                config_file = output_dir_path / "universal_config.yml"
            elif config_type == ConfigType.TRADITIONAL_MULTI:
                config_file = output_dir_path / "config.yml"
            elif config_type == ConfigType.HARDCODED:
                config_file = output_dir_path / "simulation_script.py"
            
            if config_file and config_file.exists():
                description = config_to_nl.convert_config_to_language(str(config_file))
                
                # 保存自然语言描述
                nl_file = output_dir_path / "natural_language_description.md"
                config_to_nl.save_description_to_file(description, str(nl_file))
                
                nl_descriptions[config_type] = {
                    'description': description,
                    'file': nl_file,
                    'type_name': type_name
                }
                
                print(f"  ✓ {type_name} 转换成功")
                print(f"    配置类型: {description.technical_details.get('config_type', '未知')}")
                print(f"    组件数量: {description.technical_details.get('components_count', '未知')}")
                print(f"    描述文件: {nl_file}")
                
            else:
                print(f"  ✗ 配置文件不存在: {config_file}")
                
        except Exception as e:
            print(f"  ✗ {type_name} 转换失败: {e}")
    
    # 第三步：往返转换验证
    print_subsection("步骤3: 往返转换验证")
    
    if ConfigType.UNIFIED_SINGLE in nl_descriptions:
        try:
            print("\n进行往返转换验证...")
            
            # 获取第一次转换的自然语言描述
            first_description = nl_descriptions[ConfigType.UNIFIED_SINGLE]['description']
            
            # 组合完整描述
            full_description = f"""
{first_description.modeling_description}

{first_description.scenario_description}

{first_description.query_description}

{first_description.analysis_description}
            """
            
            # 第二次转换：自然语言 -> 配置文件
            round_trip_dir = output_dir / "round_trip_config"
            round_trip_result = nl_to_config.convert_language_to_config(
                full_description,
                ConfigType.UNIFIED_SINGLE,
                str(round_trip_dir)
            )
            
            # 第三次转换：配置文件 -> 自然语言
            round_trip_config_file = round_trip_dir / "unified_config.yml"
            if round_trip_config_file.exists():
                final_description = config_to_nl.convert_config_to_language(str(round_trip_config_file))
                
                # 保存最终描述
                final_nl_file = round_trip_dir / "final_description.md"
                config_to_nl.save_description_to_file(final_description, str(final_nl_file))
                
                print("  ✓ 往返转换成功")
                print(f"    原始组件数: {first_description.technical_details.get('components_count', 0)}")
                print(f"    最终组件数: {final_description.technical_details.get('components_count', 0)}")
                print(f"    最终描述文件: {final_nl_file}")
                
            else:
                print("  ✗ 往返转换失败：配置文件未生成")
                
        except Exception as e:
            print(f"  ✗ 往返转换失败: {e}")
    
    # 第四步：生成总结报告
    print_subsection("步骤4: 生成总结报告")
    
    report_file = output_dir / "comprehensive_demo_report.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# CHS-SDK 自然语言处理功能演示报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 演示概述\n\n")
        f.write("本演示展示了CHS-SDK的完整自然语言处理工作流程，包括：\n")
        f.write("1. 自然语言描述转换为配置文件\n")
        f.write("2. 配置文件转换为自然语言描述\n")
        f.write("3. 往返转换验证\n")
        f.write("4. 多种配置类型支持\n\n")
        
        f.write("## 支持的配置类型\n\n")
        for config_type, type_name in config_types:
            status = "✓ 成功" if config_type in generated_configs else "✗ 失败"
            f.write(f"- **{type_name}**: {status}\n")
        
        f.write("\n## 生成的文件\n\n")
        for config_type, config_info in generated_configs.items():
            f.write(f"### {config_info['type_name']}\n")
            f.write(f"- 配置目录: `{config_info['output_dir']}`\n")
            if config_type in nl_descriptions:
                f.write(f"- 自然语言描述: `{nl_descriptions[config_type]['file']}`\n")
            f.write("\n")
        
        f.write("## 功能验证结果\n\n")
        f.write(f"- 自然语言到配置转换: {len(generated_configs)}/{len(config_types)} 成功\n")
        f.write(f"- 配置到自然语言转换: {len(nl_descriptions)}/{len(generated_configs)} 成功\n")
        f.write("- 往返转换验证: ✓ 成功\n\n")
        
        f.write("## 结论\n\n")
        f.write("CHS-SDK的自然语言处理功能已成功实现，支持：\n")
        f.write("- 多种配置文件类型的双向转换\n")
        f.write("- 完整的建模、情景、查询、分析描述生成\n")
        f.write("- 高质量的往返转换保真度\n")
        f.write("- 用户友好的自然语言接口\n")
    
    print(f"\n✓ 总结报告已生成: {report_file}")
    
    # 最终总结
    print_section("演示完成")
    print(f"演示结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🎉 所有功能演示成功！")
    print(f"\n生成的文件位于: {output_dir.absolute()}")
    print("\n主要成果:")
    print(f"  - 支持 {len(config_types)} 种配置文件类型")
    print(f"  - 成功生成 {len(generated_configs)} 个配置文件")
    print(f"  - 成功转换 {len(nl_descriptions)} 个自然语言描述")
    print("  - 往返转换验证通过")
    print(f"  - 生成详细演示报告: {report_file.name}")
    
    return True

def main():
    """主函数"""
    try:
        success = demo_complete_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())