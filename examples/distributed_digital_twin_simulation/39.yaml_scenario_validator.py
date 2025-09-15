#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML场景验证器

本模块用于验证所有YAML配置文件的正确性，包括：
1. 语法验证
2. 结构验证
3. 内容完整性检查
4. 场景可执行性验证
"""

import os
import sys
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YAMLScenarioValidator:
    """YAML场景验证器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path('.')
        self.validation_results = []
        self.error_count = 0
        self.warning_count = 0
        
    def validate_all_yaml_files(self) -> Dict[str, Any]:
        """验证所有YAML文件"""
        logger.info("开始YAML场景验证")
        start_time = datetime.now()
        
        # 查找所有YAML文件
        yaml_files = self._find_yaml_files()
        logger.info(f"找到 {len(yaml_files)} 个YAML文件")
        
        # 验证每个文件
        for yaml_file in yaml_files:
            self._validate_single_file(yaml_file)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成验证报告
        report = {
            'validation_timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'total_files': len(yaml_files),
            'files_validated': len(self.validation_results),
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'overall_status': 'passed' if self.error_count == 0 else 'failed',
            'validation_results': self.validation_results
        }
        
        # 保存验证报告
        self._save_validation_report(report)
        
        logger.info(f"YAML验证完成，耗时: {duration:.2f}秒")
        logger.info(f"总计: {len(yaml_files)} 个文件，错误: {self.error_count}，警告: {self.warning_count}")
        
        return report
    
    def _find_yaml_files(self) -> List[Path]:
        """查找所有YAML文件"""
        yaml_files = []
        
        # 搜索模式
        patterns = ['*.yml', '*.yaml']
        
        for pattern in patterns:
            # 在当前目录及子目录中搜索
            yaml_files.extend(self.base_dir.rglob(pattern))
        
        # 排除某些目录
        excluded_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv'}
        
        filtered_files = []
        for file_path in yaml_files:
            # 检查是否在排除目录中
            if not any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    def _validate_single_file(self, file_path: Path):
        """验证单个YAML文件"""
        logger.info(f"验证文件: {file_path}")
        
        result = {
            'file_path': str(file_path),
            'relative_path': str(file_path.relative_to(self.base_dir)),
            'file_size': file_path.stat().st_size,
            'validation_status': 'unknown',
            'errors': [],
            'warnings': [],
            'content_summary': {}
        }
        
        try:
            # 1. 语法验证
            content = self._validate_syntax(file_path, result)
            
            if content is not None:
                # 2. 结构验证
                self._validate_structure(content, result)
                
                # 3. 内容验证
                self._validate_content(content, result, file_path)
                
                # 4. 场景特定验证
                self._validate_scenario_specific(content, result, file_path)
            
            # 确定验证状态
            if result['errors']:
                result['validation_status'] = 'failed'
                self.error_count += len(result['errors'])
            elif result['warnings']:
                result['validation_status'] = 'passed_with_warnings'
                self.warning_count += len(result['warnings'])
            else:
                result['validation_status'] = 'passed'
                
        except Exception as e:
            result['validation_status'] = 'error'
            result['errors'].append(f"验证过程中发生异常: {str(e)}")
            self.error_count += 1
            logger.error(f"验证文件 {file_path} 时发生异常: {e}")
        
        self.validation_results.append(result)
    
    def _validate_syntax(self, file_path: Path, result: Dict) -> Optional[Any]:
        """验证YAML语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            if content is None:
                result['warnings'].append("文件为空或只包含注释")
            
            return content
            
        except yaml.YAMLError as e:
            result['errors'].append(f"YAML语法错误: {str(e)}")
            return None
        except UnicodeDecodeError as e:
            result['errors'].append(f"文件编码错误: {str(e)}")
            return None
        except Exception as e:
            result['errors'].append(f"读取文件时发生错误: {str(e)}")
            return None
    
    def _validate_structure(self, content: Any, result: Dict):
        """验证YAML结构"""
        if content is None:
            return
        
        # 记录内容摘要
        if isinstance(content, dict):
            result['content_summary']['type'] = 'dictionary'
            result['content_summary']['keys'] = list(content.keys())
            result['content_summary']['key_count'] = len(content.keys())
        elif isinstance(content, list):
            result['content_summary']['type'] = 'list'
            result['content_summary']['item_count'] = len(content)
        else:
            result['content_summary']['type'] = type(content).__name__
    
    def _validate_content(self, content: Any, result: Dict, file_path: Path):
        """验证内容完整性"""
        if not isinstance(content, dict):
            return
        
        # 检查常见的必需字段
        filename = file_path.name.lower()
        
        if 'config' in filename:
            self._validate_config_content(content, result)
        elif 'agent' in filename:
            self._validate_agent_content(content, result)
        elif 'component' in filename:
            self._validate_component_content(content, result)
        elif 'topology' in filename:
            self._validate_topology_content(content, result)
        elif 'disturbance' in filename or file_path.parent.name == 'disturbance_scenarios':
            self._validate_disturbance_content(content, result)
    
    def _validate_config_content(self, content: Dict, result: Dict):
        """验证配置文件内容"""
        required_fields = ['simulation', 'solver', 'system_architecture']
        
        for field in required_fields:
            if field not in content:
                result['warnings'].append(f"配置文件缺少推荐字段: {field}")
        
        # 检查仿真配置
        if 'simulation' in content:
            sim_config = content['simulation']
            if isinstance(sim_config, dict):
                if 'start_time' not in sim_config:
                    result['warnings'].append("仿真配置缺少start_time")
                if 'end_time' not in sim_config:
                    result['warnings'].append("仿真配置缺少end_time")
                if 'dt' not in sim_config:
                    result['warnings'].append("仿真配置缺少dt（时间步长）")
    
    def _validate_agent_content(self, content: Dict, result: Dict):
        """验证智能体配置内容"""
        if 'agents' in content:
            agents = content['agents']
            if isinstance(agents, list):
                for i, agent in enumerate(agents):
                    if not isinstance(agent, dict):
                        result['errors'].append(f"智能体 {i} 配置格式错误")
                        continue
                    
                    # 检查id字段（必需）
                    if 'id' not in agent:
                        result['errors'].append(f"智能体 {i} 缺少id字段")
                    
                    # 检查class字段（必需）
                    if 'class' not in agent:
                        result['errors'].append(f"智能体 {i} 缺少class字段")
                    
                    # 检查config字段（推荐）
                    if 'config' not in agent:
                        result['warnings'].append(f"智能体 {i} 建议包含config字段")
                    
                    # 兼容性检查：如果使用了旧的name/type字段
                    if 'name' in agent and 'id' not in agent:
                        result['warnings'].append(f"智能体 {i} 使用了旧的name字段，建议使用id字段")
                    if 'type' in agent and 'class' not in agent:
                        result['warnings'].append(f"智能体 {i} 使用了旧的type字段，建议使用class字段")
    
    def _validate_component_content(self, content: Dict, result: Dict):
        """验证组件配置内容"""
        if 'components' in content:
            components = content['components']
            if isinstance(components, list):
                for i, component in enumerate(components):
                    if not isinstance(component, dict):
                        result['errors'].append(f"组件 {i} 配置格式错误")
                        continue
                    
                    # 检查id字段（必需）
                    if 'id' not in component:
                        result['errors'].append(f"组件 {i} 缺少id字段")
                    
                    # 检查class字段（必需）
                    if 'class' not in component:
                        result['errors'].append(f"组件 {i} 缺少class字段")
                    
                    # 检查initial_state字段（推荐）
                    if 'initial_state' not in component:
                        result['warnings'].append(f"组件 {i} 建议包含initial_state字段")
                    
                    # 检查parameters字段（推荐）
                    if 'parameters' not in component:
                        result['warnings'].append(f"组件 {i} 建议包含parameters字段")
                    
                    # 兼容性检查：如果使用了旧的name/type字段
                    if 'name' in component and 'id' not in component:
                        result['warnings'].append(f"组件 {i} 使用了旧的name字段，建议使用id字段")
                    if 'type' in component and 'class' not in component:
                        result['warnings'].append(f"组件 {i} 使用了旧的type字段，建议使用class字段")
    
    def _validate_topology_content(self, content: Dict, result: Dict):
        """验证拓扑配置内容"""
        if 'topology' in content:
            topology = content['topology']
            if isinstance(topology, dict):
                if 'nodes' not in topology:
                    result['warnings'].append("拓扑配置缺少nodes字段")
                if 'connections' not in topology:
                    result['warnings'].append("拓扑配置缺少connections字段")
    
    def _validate_disturbance_content(self, content: Dict, result: Dict):
        """验证扰动场景内容"""
        # 检查扰动场景的基本结构
        if 'disturbance' in content:
            disturbance = content['disturbance']
            if isinstance(disturbance, dict):
                required_fields = ['type', 'target', 'parameters']
                for field in required_fields:
                    if field not in disturbance:
                        result['errors'].append(f"扰动配置缺少必需字段: {field}")
        
        elif 'disturbances' in content:
            disturbances = content['disturbances']
            if isinstance(disturbances, list):
                for i, dist in enumerate(disturbances):
                    if not isinstance(dist, dict):
                        result['errors'].append(f"扰动 {i} 配置格式错误")
                        continue
                    
                    if 'type' not in dist:
                        result['errors'].append(f"扰动 {i} 缺少type字段")
    
    def _validate_scenario_specific(self, content: Any, result: Dict, file_path: Path):
        """场景特定验证"""
        # 根据文件名或路径进行特定验证
        filename = file_path.name.lower()
        
        # 检查扰动场景文件
        if file_path.parent.name == 'disturbance_scenarios' or 'disturbance' in filename:
            self._validate_disturbance_scenario(content, result, filename)
    
    def _validate_disturbance_scenario(self, content: Any, result: Dict, filename: str):
        """验证扰动场景"""
        if not isinstance(content, dict):
            result['errors'].append("扰动场景文件应该是字典格式")
            return
        
        # 根据文件名检查特定的扰动类型
        if 'actuator' in filename:
            self._check_actuator_disturbance(content, result)
        elif 'sensor' in filename:
            self._check_sensor_disturbance(content, result)
        elif 'inflow' in filename or 'flow' in filename:
            self._check_flow_disturbance(content, result)
        elif 'network' in filename:
            self._check_network_disturbance(content, result)
    
    def _check_actuator_disturbance(self, content: Dict, result: Dict):
        """检查执行器扰动配置"""
        if 'disturbance' in content:
            dist = content['disturbance']
            if 'parameters' in dist:
                params = dist['parameters']
                if 'failure_type' not in params:
                    result['warnings'].append("执行器扰动建议包含failure_type参数")
    
    def _check_sensor_disturbance(self, content: Dict, result: Dict):
        """检查传感器扰动配置"""
        if 'disturbance' in content:
            dist = content['disturbance']
            if 'parameters' in dist:
                params = dist['parameters']
                if 'noise_level' not in params:
                    result['warnings'].append("传感器扰动建议包含noise_level参数")
    
    def _check_flow_disturbance(self, content: Dict, result: Dict):
        """检查流量扰动配置"""
        if 'disturbance' in content:
            dist = content['disturbance']
            if 'parameters' in dist:
                params = dist['parameters']
                if 'target_flow' not in params and 'flow_change' not in params:
                    result['warnings'].append("流量扰动建议包含target_flow或flow_change参数")
    
    def _check_network_disturbance(self, content: Dict, result: Dict):
        """检查网络扰动配置"""
        if 'disturbance' in content:
            dist = content['disturbance']
            if 'parameters' in dist:
                params = dist['parameters']
                if 'packet_loss_rate' not in params and 'latency' not in params:
                    result['warnings'].append("网络扰动建议包含packet_loss_rate或latency参数")
    
    def _save_validation_report(self, report: Dict[str, Any]):
        """保存验证报告"""
        output_dir = Path('yaml_validation_output')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'yaml_validation_report_{timestamp}.json'
        
        with open(output_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"验证报告已保存到: {output_dir / filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """打印验证摘要"""
        print("\n" + "="*60)
        print("YAML场景验证摘要")
        print("="*60)
        print(f"验证时间: {report['validation_timestamp']}")
        print(f"验证耗时: {report['duration_seconds']:.2f}秒")
        print(f"总文件数: {report['total_files']}")
        print(f"验证文件数: {report['files_validated']}")
        print(f"错误数量: {report['error_count']}")
        print(f"警告数量: {report['warning_count']}")
        print(f"总体状态: {report['overall_status']}")
        print("="*60)
        
        # 显示详细结果
        if report['validation_results']:
            print("\n文件验证详情:")
            for result in report['validation_results']:
                status_icon = {
                    'passed': '✅',
                    'passed_with_warnings': '⚠️',
                    'failed': '❌',
                    'error': '💥'
                }.get(result['validation_status'], '❓')
                
                print(f"{status_icon} {result['relative_path']} - {result['validation_status']}")
                
                if result['errors']:
                    for error in result['errors']:
                        print(f"   ❌ {error}")
                
                if result['warnings']:
                    for warning in result['warnings']:
                        print(f"   ⚠️ {warning}")

def main():
    """主函数"""
    validator = YAMLScenarioValidator()
    report = validator.validate_all_yaml_files()
    validator.print_summary(report)
    
    # 返回适当的退出代码
    return 0 if report['error_count'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())