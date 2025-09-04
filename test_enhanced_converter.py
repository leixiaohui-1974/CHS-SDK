#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版自然语言到配置文件转换器

对比LLM、规则和混合三种策略的转换效果
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core_lib.nlp.enhanced_language_to_config_converter import EnhancedLanguageToConfigConverter
from core_lib.config.unified_config_manager import ConfigType


def test_enhanced_converter():
    """测试增强版转换器"""
    print("=" * 60)
    print("测试增强版自然语言到配置文件转换器")
    print("=" * 60)
    
    # 创建转换器
    converter = EnhancedLanguageToConfigConverter()
    
    # 测试用例
    test_cases = [
        {
            "name": "简单水库系统",
            "description": """
建立一个简单的水库调度系统：
- 水库1：Reservoir，容量1000立方米，初始水位50米
- 闸门1：Gate，控制水库出流
- 河道1：Channel，长度5000米
- 仿真时长：3600秒
- 时间步长：1.0秒
- 连接关系：水库1 -> 闸门1 -> 河道1
"""
        },
        {
            "name": "多组件复杂系统",
            "description": """
设计一个复杂的水利调度系统：
系统包含2个水库、3个泵站、1个渠道和2个汇流点。
水库A的容量为5000立方米，水库B的容量为3000立方米。
泵站1功率100kW，泵站2功率150kW，泵站3功率200kW。
渠道长度10公里，汇流点用于连接不同水流。
仿真运行7200秒，时间步长0.5秒。
连接关系：水库A->泵站1->汇流点1，水库B->泵站2->汇流点1，汇流点1->泵站3->渠道->汇流点2
"""
        },
        {
            "name": "英文类名系统",
            "description": """
创建一个使用英文类名的系统：
- reservoir1: core_lib.physical_objects.reservoir.Reservoir
- pump1: core_lib.physical_objects.pump.Pump  
- channel1: core_lib.physical_objects.channel.Channel
- junction1: core_lib.physical_objects.junction.Junction
仿真时长1800秒，时间步长2.0秒
连接：reservoir1->pump1->channel1->junction1
"""
        }
    ]
    
    # 测试每个用例
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['name']}")
        print("-" * 40)
        
        case_results = {}
        
        # 测试三种策略
        strategies = ['llm', 'rule', 'hybrid']
        
        for strategy in strategies:
            print(f"\n策略: {strategy.upper()}")
            
            try:
                start_time = time.time()
                
                # 执行转换
                result = converter.convert_language_to_config(
                    test_case['description'],
                    ConfigType.UNIVERSAL_CONFIG,
                    f"test_output/enhanced_{strategy}_{i}",
                    strategy
                )
                
                end_time = time.time()
                
                # 评估质量
                quality = converter.evaluate_conversion_quality(
                    test_case['description'], 
                    result.config_data
                )
                
                case_results[strategy] = {
                    'success': True,
                    'confidence_score': result.confidence_score,
                    'llm_contribution': result.llm_contribution,
                    'rule_contribution': result.rule_contribution,
                    'validation_errors': result.validation_errors,
                    'improvements': result.improvements,
                    'quality_metrics': quality,
                    'execution_time': end_time - start_time,
                    'config_data': result.config_data
                }
                
                print(f"  ✓ 转换成功")
                print(f"  置信度: {result.confidence_score:.2f}")
                print(f"  LLM贡献: {result.llm_contribution:.2f}")
                print(f"  规则贡献: {result.rule_contribution:.2f}")
                print(f"  总体质量: {quality['overall']:.2f}")
                print(f"  执行时间: {end_time - start_time:.2f}秒")
                
                if result.improvements:
                    print(f"  改进: {len(result.improvements)}项")
                
                if result.validation_errors:
                    print(f"  ✗ 验证错误: {len(result.validation_errors)}项")
                    for error in result.validation_errors[:2]:  # 只显示前2个错误
                        print(f"    - {error}")
                
            except Exception as e:
                case_results[strategy] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': 0
                }
                print(f"  ✗ 转换失败: {e}")
        
        results.append({
            'test_case': test_case['name'],
            'results': case_results
        })
    
    # 生成对比报告
    print("\n" + "=" * 60)
    print("转换策略对比报告")
    print("=" * 60)
    
    # 统计成功率
    strategy_stats = {'llm': [], 'rule': [], 'hybrid': []}
    
    for result in results:
        for strategy in ['llm', 'rule', 'hybrid']:
            if strategy in result['results']:
                strategy_stats[strategy].append(result['results'][strategy])
    
    print("\n策略性能对比:")
    print(f"{'策略':<10} {'成功率':<10} {'平均置信度':<12} {'平均质量':<10} {'平均时间':<10}")
    print("-" * 60)
    
    for strategy in ['llm', 'rule', 'hybrid']:
        stats = strategy_stats[strategy]
        if stats:
            success_rate = sum(1 for s in stats if s['success']) / len(stats)
            
            successful_stats = [s for s in stats if s['success']]
            if successful_stats:
                avg_confidence = sum(s['confidence_score'] for s in successful_stats) / len(successful_stats)
                avg_quality = sum(s['quality_metrics']['overall'] for s in successful_stats) / len(successful_stats)
                avg_time = sum(s['execution_time'] for s in successful_stats) / len(successful_stats)
            else:
                avg_confidence = avg_quality = avg_time = 0
            
            print(f"{strategy.upper():<10} {success_rate:<10.2f} {avg_confidence:<12.2f} {avg_quality:<10.2f} {avg_time:<10.2f}s")
    
    # 详细质量分析
    print("\n详细质量分析:")
    for i, result in enumerate(results, 1):
        print(f"\n测试用例 {i}: {result['test_case']}")
        
        for strategy in ['llm', 'rule', 'hybrid']:
            if strategy in result['results'] and result['results'][strategy]['success']:
                r = result['results'][strategy]
                q = r['quality_metrics']
                print(f"  {strategy.upper()}: 完整性={q['completeness']:.2f}, 准确性={q['accuracy']:.2f}, 一致性={q['consistency']:.2f}")
    
    # 保存详细结果
    output_file = "test_output/enhanced_converter_comparison.json"
    os.makedirs("test_output", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n详细结果已保存到: {output_file}")
    
    # 推荐最佳策略
    print("\n推荐策略:")
    
    hybrid_stats = strategy_stats['hybrid']
    if hybrid_stats and all(s['success'] for s in hybrid_stats):
        avg_hybrid_quality = sum(s['quality_metrics']['overall'] for s in hybrid_stats) / len(hybrid_stats)
        avg_hybrid_confidence = sum(s['confidence_score'] for s in hybrid_stats) / len(hybrid_stats)
        
        if avg_hybrid_quality >= 0.7 and avg_hybrid_confidence >= 0.8:
            print("  推荐使用 HYBRID 策略 - 质量高且稳定")
        elif avg_hybrid_quality >= 0.6:
            print("  推荐使用 HYBRID 策略 - 质量良好")
        else:
            print("  建议根据具体场景选择策略")
    else:
        print("  建议根据具体场景选择策略")
    
    return True


def test_specific_case():
    """测试特定用例"""
    print("\n" + "=" * 60)
    print("测试特定复杂用例")
    print("=" * 60)
    
    converter = EnhancedLanguageToConfigConverter()
    
    # 复杂的水利系统描述
    complex_description = """
设计一个智能水利调度系统：

系统组成：
1. 上游水库（reservoir_upstream）：容量10000立方米，初始水位80米
2. 中游水库（reservoir_middle）：容量8000立方米，初始水位60米  
3. 下游水库（reservoir_downstream）：容量6000立方米，初始水位40米
4. 主泵站（pump_main）：功率500kW，流量50立方米/秒
5. 辅助泵站（pump_aux）：功率300kW，流量30立方米/秒
6. 主渠道（canal_main）：长度15公里，宽度10米
7. 支渠道（canal_branch）：长度8公里，宽度6米
8. 调节闸门（gate_control）：开度可调，最大流量100立方米/秒
9. 汇流点1（junction_1）：连接上游和中游
10. 汇流点2（junction_2）：连接中游和下游

连接关系：
- 上游水库 -> 主泵站 -> 汇流点1
- 汇流点1 -> 中游水库 -> 调节闸门 -> 主渠道 -> 汇流点2
- 汇流点2 -> 下游水库
- 中游水库 -> 辅助泵站 -> 支渠道 -> 汇流点2

仿真参数：
- 仿真名称：智能水利调度系统测试
- 仿真时长：7200秒（2小时）
- 时间步长：0.5秒
- 求解器：rk4

控制策略：
- 使用PID控制器控制泵站流量
- 使用模糊控制器控制闸门开度
"""
    
    print("测试复杂系统描述...")
    
    try:
        # 使用混合策略
        result = converter.convert_language_to_config(
            complex_description,
            ConfigType.UNIVERSAL_CONFIG,
            "test_output/complex_system",
            'hybrid'
        )
        
        print(f"\n转换结果:")
        print(f"  置信度: {result.confidence_score:.2f}")
        print(f"  LLM贡献: {result.llm_contribution:.2f}")
        print(f"  规则贡献: {result.rule_contribution:.2f}")
        
        # 评估质量
        quality = converter.evaluate_conversion_quality(complex_description, result.config_data)
        print(f"\n质量评估:")
        print(f"  完整性: {quality['completeness']:.2f}")
        print(f"  准确性: {quality['accuracy']:.2f}")
        print(f"  一致性: {quality['consistency']:.2f}")
        print(f"  总体质量: {quality['overall']:.2f}")
        
        # 分析生成的配置
        config = result.config_data
        
        print(f"\n配置分析:")
        if 'simulation' in config:
            sim = config['simulation']
            print(f"  仿真配置: 时长={sim.get('duration', 'N/A')}s, 步长={sim.get('dt', sim.get('time_step', 'N/A'))}s")
        
        if 'components' in config:
            components = config['components']
            if isinstance(components, dict) and 'components' in components:
                comp_list = components['components']
            elif isinstance(components, list):
                comp_list = components
            else:
                comp_list = []
            
            print(f"  组件数量: {len(comp_list)}")
            
            # 统计组件类型
            comp_types = {}
            for comp in comp_list:
                comp_type = comp.get('type', 'Unknown')
                comp_types[comp_type] = comp_types.get(comp_type, 0) + 1
            
            print(f"  组件类型分布: {comp_types}")
        
        if 'topology' in config:
            topology = config['topology']
            print(f"  连接数量: {len(topology)}")
        
        if result.improvements:
            print(f"\n改进措施 ({len(result.improvements)}项):")
            for improvement in result.improvements:
                print(f"  - {improvement}")
        
        if result.validation_errors:
            print(f"\n验证错误 ({len(result.validation_errors)}项):")
            for error in result.validation_errors:
                print(f"  - {error}")
        
        print(f"\n配置文件已保存到: test_output/complex_system/")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("增强版自然语言到配置文件转换器测试")
    
    # 基础对比测试
    success1 = test_enhanced_converter()
    
    # 复杂用例测试
    success2 = test_specific_case()
    
    print("\n" + "=" * 60)
    print(f"测试完成！基础测试: {'通过' if success1 else '失败'}, 复杂测试: {'通过' if success2 else '失败'}")
    print("=" * 60)
    
    sys.exit(0 if (success1 and success2) else 1)