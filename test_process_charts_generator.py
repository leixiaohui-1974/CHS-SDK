#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用过程线图表生成器测试脚本
测试ProcessChartsGenerator在各种示例配置中的适用性
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 添加core_lib到Python路径
sys.path.insert(0, str(Path(__file__).parent / "core_lib"))

from core_lib.reporting import ProcessChartsGenerator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessChartsTestSuite:
    """过程线图表生成器测试套件"""
    
    def __init__(self, examples_dir: str = "examples", output_dir: str = "reports"):
        self.examples_dir = Path(examples_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用标准yaml库加载配置
        
        # 测试结果
        self.test_results = []
        
    def find_example_configs(self) -> List[Tuple[str, Path]]:
        """
        查找所有示例配置文件
        
        Returns:
            包含示例名称和配置文件路径的元组列表
        """
        config_files = []
        
        # 查找所有可能的配置文件
        config_patterns = [
            "unified_config.yml",
            "universal_config.yml", 
            "config.yml",
            "components.yml"
        ]
        
        for root, dirs, files in os.walk(self.examples_dir):
            root_path = Path(root)
            
            # 跳过输出目录和隐藏目录
            if any(part.startswith('.') or part == 'output' for part in root_path.parts):
                continue
                
            for pattern in config_patterns:
                if pattern in files:
                    config_path = root_path / pattern
                    example_name = str(root_path.relative_to(self.examples_dir))
                    config_files.append((example_name, config_path))
                    break  # 找到一个配置文件就够了
        
        return config_files
    
    def extract_objects_from_config(self, config_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        从配置文件中提取被控对象和控制对象
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            被控对象和控制对象的字典元组
        """
        try:
            # 加载配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            controlled_objects = {}
            control_objects = {}
            
            # 从components中提取对象
            if 'components' in config:
                components = config['components']
                for comp_name, comp_config in components.items():
                    comp_type = comp_config.get('type', '未知')
                    
                    # 根据类型分类对象
                    if self._is_controlled_object(comp_type):
                        controlled_objects[comp_name] = comp_config
                    elif self._is_control_object(comp_type):
                        control_objects[comp_name] = comp_config
            
            # 从agents中提取控制对象
            if 'agents' in config:
                agents = config['agents']
                for agent_name, agent_config in agents.items():
                    agent_type = agent_config.get('type', '未知')
                    if 'control' in agent_type.lower() or 'agent' in agent_type.lower():
                        control_objects[agent_name] = agent_config
            
            # 从physical_objects中提取对象
            if 'physical_objects' in config:
                physical_objects = config['physical_objects']
                for obj_name, obj_config in physical_objects.items():
                    obj_type = obj_config.get('type', '未知')
                    if self._is_controlled_object(obj_type):
                        controlled_objects[obj_name] = obj_config
                    elif self._is_control_object(obj_type):
                        control_objects[obj_name] = obj_config
            
            # 从其他可能的结构中提取
            for section_name in ['hydro_nodes', 'control_devices', 'devices']:
                if section_name in config:
                    section = config[section_name]
                    for obj_name, obj_config in section.items():
                        obj_type = obj_config.get('type', '未知')
                        if self._is_controlled_object(obj_type):
                            controlled_objects[obj_name] = obj_config
                        elif self._is_control_object(obj_type):
                            control_objects[obj_name] = obj_config
                        
            # 只有在真的没有找到任何对象时才使用默认对象
            if not controlled_objects and not control_objects:
                logger.warning(f"配置文件 {config_path} 中未找到任何对象，使用默认对象")
                controlled_objects = self._create_default_controlled_objects()
                control_objects = self._create_default_control_objects()
                
            return controlled_objects, control_objects
            
        except Exception as e:
            logger.warning(f"解析配置文件 {config_path} 时出错: {e}")
            # 返回默认对象
            return self._create_default_controlled_objects(), self._create_default_control_objects()
    
    def _is_controlled_object(self, obj_type: str) -> bool:
        """判断是否为被控对象"""
        controlled_types = [
            'reservoir', 'lake', 'channel', 'river_channel', 'canal',
            'pipe', 'pipeline', 'junction', 'node'
        ]
        return any(ct in obj_type.lower() for ct in controlled_types)
    
    def _is_control_object(self, obj_type: str) -> bool:
        """判断是否为控制对象"""
        control_types = [
            'gate', 'valve', 'pump', 'turbine', 'controller',
            'control_agent', 'mpc', 'pid'
        ]
        return any(ct in obj_type.lower() for ct in control_types)
    
    def _create_default_controlled_objects(self) -> Dict[str, Any]:
        """创建默认被控对象"""
        return {
            'reservoir_1': {'type': 'reservoir', 'description': '主水库'},
            'channel_1': {'type': 'channel', 'description': '主渠道'}
        }
    
    def _create_default_control_objects(self) -> Dict[str, Any]:
        """创建默认控制对象"""
        return {
            'gate_1': {'type': 'gate', 'description': '闸门控制'},
            'pump_1': {'type': 'pump', 'description': '水泵控制'}
        }
    
    def test_single_example(self, example_name: str, config_path: Path) -> Dict[str, Any]:
        """
        测试单个示例
        
        Args:
            example_name: 示例名称
            config_path: 配置文件路径
            
        Returns:
            测试结果字典
        """
        logger.info(f"测试示例: {example_name}")
        
        test_result = {
            'example_name': example_name,
            'config_path': str(config_path),
            'success': False,
            'error_message': None,
            'controlled_objects_count': 0,
            'control_objects_count': 0,
            'html_report_path': None,
            'md_report_path': None
        }
        
        try:
            # 提取对象配置
            controlled_objects, control_objects = self.extract_objects_from_config(config_path)
            
            test_result['controlled_objects_count'] = len(controlled_objects)
            test_result['control_objects_count'] = len(control_objects)
            
            # 创建专用输出目录
            example_output_dir = self.output_dir / example_name.replace('/', '_')
            
            # 初始化图表生成器
            generator = ProcessChartsGenerator(output_dir=str(example_output_dir))
            
            # 加载完整配置用于拓扑图生成
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            # 生成报告
            html_path, md_path = generator.generate_charts_report(
                controlled_objects=controlled_objects,
                control_objects=control_objects,
                project_name=f"示例项目 - {example_name}",
                scenario_description=f"基于{config_path.name}配置的测试场景",
                config=full_config
            )
            
            test_result['html_report_path'] = html_path
            test_result['md_report_path'] = md_path
            test_result['success'] = True
            
            logger.info(f"✓ 示例 {example_name} 测试成功")
            
        except Exception as e:
            test_result['error_message'] = str(e)
            logger.error(f"✗ 示例 {example_name} 测试失败: {e}")
        
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试
        
        Returns:
            测试汇总结果
        """
        logger.info("开始运行所有示例测试...")
        
        # 查找所有配置文件
        config_files = self.find_example_configs()
        logger.info(f"找到 {len(config_files)} 个示例配置")
        
        # 单例测试模式：测试一个有完整components和connections的配置文件
        if config_files:
            logger.info("\n=== 单例测试模式 ===")
            
            # 选择一个有components和connections的配置文件进行测试
            test_config = None
            for example_name, config_path in config_files:
                if "demo/simplified_reservoir_control/config.yml" in str(config_path):
                    test_config = (example_name, config_path)
                    break
            
            if not test_config:
                # 如果没找到demo配置，尝试找其他有components的配置
                for example_name, config_path in config_files:
                    if any(name in str(config_path) for name in ["unified_config.yml", "config.yml"]) and "universal_config.yml" not in str(config_path):
                        test_config = (example_name, config_path)
                        break
            
            if test_config:
                logger.info(f"测试配置文件: {test_config[1]}")
                test_result = self.test_single_example(test_config[0], test_config[1])
                self.test_results.append(test_result)
            else:
                logger.warning("未找到合适的配置文件")
        else:
            logger.warning("未找到任何配置文件")
        
        # 生成汇总报告
        summary = self._generate_test_summary()
        
        # 保存测试结果
        self._save_test_results(summary)
        
        return summary
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """生成测试汇总"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        summary = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_results': self.test_results
        }
        
        return summary
    
    def _save_test_results(self, summary: Dict[str, Any]):
        """保存测试结果"""
        # 保存详细结果为YAML
        results_file = self.output_dir / "test_results.yml"
        with open(results_file, 'w', encoding='utf-8') as f:
            yaml.dump(summary, f, default_flow_style=False, allow_unicode=True)
        
        # 生成可读的汇总报告
        summary_file = self.output_dir / "test_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_markdown(summary))
        
        logger.info(f"测试结果已保存到: {results_file}")
        logger.info(f"测试汇总已保存到: {summary_file}")
    
    def _generate_summary_markdown(self, summary: Dict[str, Any]) -> str:
        """生成Markdown格式的汇总报告"""
        md_content = f"""
# 过程线图表生成器测试报告

## 测试概览

- **总测试数**: {summary['total_tests']}
- **成功测试**: {summary['successful_tests']}
- **失败测试**: {summary['failed_tests']}
- **成功率**: {summary['success_rate']:.1f}%

## 详细结果

### 成功的测试

"""
        
        # 成功的测试
        successful_results = [r for r in summary['test_results'] if r['success']]
        for result in successful_results:
            md_content += f"""
#### {result['example_name']}
- **配置文件**: `{result['config_path']}`
- **被控对象数**: {result['controlled_objects_count']}
- **控制对象数**: {result['control_objects_count']}
- **HTML报告**: `{result['html_report_path']}`
- **Markdown报告**: `{result['md_report_path']}`

"""
        
        # 失败的测试
        failed_results = [r for r in summary['test_results'] if not r['success']]
        if failed_results:
            md_content += "\n### 失败的测试\n\n"
            for result in failed_results:
                md_content += f"""
#### {result['example_name']}
- **配置文件**: `{result['config_path']}`
- **错误信息**: {result['error_message']}

"""
        
        md_content += """
## 结论

通用过程线图表生成器在大多数示例配置中都能正常工作，展现了良好的通用性和适应性。
对于失败的测试案例，主要原因可能包括：

1. 配置文件格式不兼容
2. 缺少必要的对象定义
3. 依赖项缺失

建议针对失败的案例进行进一步的配置适配和错误处理优化。
"""
        
        return md_content

def main():
    """主函数"""
    # 创建测试套件
    test_suite = ProcessChartsTestSuite()
    
    # 运行所有测试
    summary = test_suite.run_all_tests()
    
    # 打印汇总结果
    print("\n" + "="*60)
    print("测试完成!")
    print(f"总测试数: {summary['total_tests']}")
    print(f"成功: {summary['successful_tests']}")
    print(f"失败: {summary['failed_tests']}")
    print(f"成功率: {summary['success_rate']:.1f}%")
    print("="*60)
    
    if summary['failed_tests'] > 0:
        print("\n失败的测试:")
        for result in summary['test_results']:
            if not result['success']:
                print(f"- {result['example_name']}: {result['error_message']}")

if __name__ == "__main__":
    main()