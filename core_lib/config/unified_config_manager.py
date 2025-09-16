#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理器 - CHS-SDK配置系统核心模块

这个模块提供了一个统一的配置管理接口，用于处理CHS-SDK中的四种不同配置文件格式：
1. 传统多配置文件方式（config.yml, components.yml, topology.yml, agents.yml）
2. 统一配置文件方式（单一YAML文件）
3. 通用配置文件方式（universal_config.yml）
4. 硬编码方式（Python代码直接构建）

主要功能：
- 自动检测配置文件类型
- 提供统一的配置加载接口
- 配置文件验证和格式检查
- 配置格式之间的转换
- 向后兼容性支持

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """配置文件类型枚举"""
    TRADITIONAL_MULTI = "traditional_multi"  # 传统多配置文件
    UNIFIED_SINGLE = "unified_single"        # 统一单配置文件
    UNIVERSAL_CONFIG = "universal_config"    # 通用配置文件
    HARDCODED = "hardcoded"                  # 硬编码方式
    UNKNOWN = "unknown"                      # 未知类型

@dataclass
class ConfigInfo:
    """配置信息数据类"""
    config_type: ConfigType
    config_path: Path
    config_files: Dict[str, Path]  # 配置文件路径映射
    metadata: Dict[str, Any]       # 元数据信息
    description: str               # 配置描述
    
class UnifiedConfigManager:
    """统一配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 定义各种配置文件的标准文件名
        self.traditional_files = {
            'config': 'config.yml',
            'components': 'components.yml', 
            'topology': 'topology.yml',
            'agents': 'agents.yml'
        }
        
        self.unified_patterns = [
            'unified_config.yml',
            'scenario_config.yml',
            'simulation_config.yml',
            'config.yaml'
        ]
        
        self.universal_patterns = [
            'universal_config',  # 支持带版本号的文件，如universal_config_1_2.yml
            'universal_config.yml',
            'universal_config.yaml'
        ]
        
        # 硬编码示例的Python文件模式
        self.hardcoded_patterns = [
            'run.py',
            'main.py',
            'example.py',
            'demo.py'
        ]
    
    def detect_config_type(self, path: Union[str, Path]) -> ConfigInfo:
        """自动检测配置文件类型
        
        Args:
            path: 配置文件或目录路径
            
        Returns:
            ConfigInfo: 配置信息对象
        """
        path = Path(path)
        
        if not path.exists():
            return ConfigInfo(
                config_type=ConfigType.UNKNOWN,
                config_path=path,
                config_files={},
                metadata={},
                description=f"路径不存在: {path}"
            )
        
        # 如果是文件，检测文件类型
        if path.is_file():
            return self._detect_file_type(path)
        
        # 如果是目录，检测目录中的配置文件
        if path.is_dir():
            return self._detect_directory_type(path)
        
        return ConfigInfo(
            config_type=ConfigType.UNKNOWN,
            config_path=path,
            config_files={},
            metadata={},
            description="无法识别的路径类型"
        )
    
    def _detect_file_type(self, file_path: Path) -> ConfigInfo:
        """检测单个文件的配置类型"""
        file_name = file_path.name.lower()
        
        # 检查是否为通用配置文件
        if any(pattern in file_name for pattern in self.universal_patterns):
            return ConfigInfo(
                config_type=ConfigType.UNIVERSAL_CONFIG,
                config_path=file_path.parent,
                config_files={'universal': file_path},
                metadata=self._extract_metadata(file_path),
                description="通用配置文件"
            )
        
        # 检查是否为统一配置文件
        if any(pattern in file_name for pattern in self.unified_patterns):
            return ConfigInfo(
                config_type=ConfigType.UNIFIED_SINGLE,
                config_path=file_path.parent,
                config_files={'unified': file_path},
                metadata=self._extract_metadata(file_path),
                description="统一配置文件"
            )
        
        # 检查是否为传统配置文件之一
        if file_name in self.traditional_files.values():
            return self._detect_directory_type(file_path.parent)
        
        # 检查是否为硬编码Python文件
        if file_path.suffix == '.py' and any(pattern in file_name for pattern in self.hardcoded_patterns):
            return ConfigInfo(
                config_type=ConfigType.HARDCODED,
                config_path=file_path.parent,
                config_files={'python': file_path},
                metadata={'language': 'python'},
                description="硬编码Python脚本"
            )
        
        return ConfigInfo(
            config_type=ConfigType.UNKNOWN,
            config_path=file_path.parent,
            config_files={},
            metadata={},
            description=f"未知文件类型: {file_name}"
        )
    
    def _detect_directory_type(self, dir_path: Path) -> ConfigInfo:
        """检测目录中的配置类型"""
        files_in_dir = [f.name.lower() for f in dir_path.iterdir() if f.is_file()]
        
        # 检查通用配置文件（优先级最高）
        for pattern in self.universal_patterns:
            # 查找匹配的文件
            matching_files = [f for f in files_in_dir if pattern in f]
            if matching_files:
                # 选择第一个匹配的文件
                universal_file = dir_path / matching_files[0]
                return ConfigInfo(
                    config_type=ConfigType.UNIVERSAL_CONFIG,
                    config_path=dir_path,
                    config_files={'universal': universal_file},
                    metadata=self._extract_metadata(universal_file),
                    description="包含通用配置文件的目录"
                )
        
        # 检查传统多配置文件（优先级第二）
        traditional_found = {}
        for key, filename in self.traditional_files.items():
            if filename in files_in_dir:
                traditional_found[key] = dir_path / filename
        
        if len(traditional_found) >= 2:  # 至少需要2个传统配置文件
            metadata = {}
            if 'config' in traditional_found:
                metadata = self._extract_metadata(traditional_found['config'])
            
            return ConfigInfo(
                config_type=ConfigType.TRADITIONAL_MULTI,
                config_path=dir_path,
                config_files=traditional_found,
                metadata=metadata,
                description=f"传统多配置文件 ({len(traditional_found)}个文件)"
            )
        
        # 检查统一配置文件
        for pattern in self.unified_patterns:
            if pattern in files_in_dir:
                unified_file = dir_path / pattern
                return ConfigInfo(
                    config_type=ConfigType.UNIFIED_SINGLE,
                    config_path=dir_path,
                    config_files={'unified': unified_file},
                    metadata=self._extract_metadata(unified_file),
                    description="包含统一配置文件的目录"
                )
        
        # 检查硬编码Python文件
        for pattern in self.hardcoded_patterns:
            if pattern in files_in_dir:
                python_file = dir_path / pattern
                return ConfigInfo(
                    config_type=ConfigType.HARDCODED,
                    config_path=dir_path,
                    config_files={'python': python_file},
                    metadata={'language': 'python'},
                    description="包含硬编码脚本的目录"
                )
        
        return ConfigInfo(
            config_type=ConfigType.UNKNOWN,
            config_path=dir_path,
            config_files={},
            metadata={},
            description="无法识别配置类型的目录"
        )
    
    def _extract_metadata(self, config_file: Path) -> Dict[str, Any]:
        """从配置文件中提取元数据"""
        metadata = {}
        
        try:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if isinstance(data, dict):
                    # 提取常见的元数据字段
                    metadata.update({
                        'description': data.get('description', ''),
                        'version': data.get('version', ''),
                        'author': data.get('author', ''),
                        'run_with': data.get('run_with', ''),
                        'example_type': data.get('example_type', ''),
                        'simulation': data.get('simulation', {})
                    })
                    
                    # 清理空值
                    metadata = {k: v for k, v in metadata.items() if v}
                    
        except Exception as e:
            self.logger.warning(f"无法提取元数据 {config_file}: {e}")
        
        return metadata
    
    def load_config(self, config_info: ConfigInfo) -> Dict[str, Any]:
        """加载配置数据
        
        Args:
            config_info: 配置信息对象
            
        Returns:
            Dict: 加载的配置数据
        """
        if config_info.config_type == ConfigType.TRADITIONAL_MULTI:
            return self._load_traditional_config(config_info)
        elif config_info.config_type == ConfigType.UNIFIED_SINGLE:
            return self._load_unified_config(config_info)
        elif config_info.config_type == ConfigType.UNIVERSAL_CONFIG:
            return self._load_universal_config(config_info)
        elif config_info.config_type == ConfigType.HARDCODED:
            return self._load_hardcoded_config(config_info)
        else:
            raise ValueError(f"不支持的配置类型: {config_info.config_type}")
    
    def _load_traditional_config(self, config_info: ConfigInfo) -> Dict[str, Any]:
        """加载传统多配置文件"""
        config_data = {}
        
        for key, file_path in config_info.config_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    config_data[key] = data
            except Exception as e:
                self.logger.error(f"加载配置文件失败 {file_path}: {e}")
                raise
        
        return config_data
    
    def _load_unified_config(self, config_info: ConfigInfo) -> Dict[str, Any]:
        """加载统一配置文件"""
        unified_file = config_info.config_files['unified']
        
        try:
            with open(unified_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载统一配置文件失败 {unified_file}: {e}")
            raise
    
    def _load_universal_config(self, config_info: ConfigInfo) -> Dict[str, Any]:
        """加载通用配置文件"""
        universal_file = config_info.config_files['universal']
        
        try:
            with open(universal_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 尝试加载同目录下的agents.yml文件
            agents_file = universal_file.parent / 'agents.yml'
            if agents_file.exists():
                try:
                    with open(agents_file, 'r', encoding='utf-8') as f:
                        agents_data = yaml.safe_load(f)
                    if agents_data:
                        # 将智能体配置合并到主配置中
                        if 'agents' not in config_data:
                            config_data['agents'] = agents_data.get('agents', [])
                        self.logger.info(f"已加载智能体配置文件: {agents_file}")
                except Exception as e:
                    self.logger.warning(f"加载智能体配置文件失败 {agents_file}: {e}")
            
            return config_data
        except Exception as e:
            self.logger.error(f"加载通用配置文件失败 {universal_file}: {e}")
            raise
    
    def _load_hardcoded_config(self, config_info: ConfigInfo) -> Dict[str, Any]:
        """加载硬编码配置（返回文件路径信息）"""
        python_file = config_info.config_files['python']
        
        return {
            'python_file': str(python_file),
            'type': 'hardcoded',
            'metadata': config_info.metadata
        }
    

    
    def validate_config(self, config_info: ConfigInfo) -> Tuple[bool, List[str]]:
        """验证配置文件
        
        Args:
            config_info: 配置信息对象
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 检查文件是否存在
            for file_path in config_info.config_files.values():
                if not file_path.exists():
                    errors.append(f"配置文件不存在: {file_path}")
            
            if errors:
                return False, errors
            
            # 尝试加载配置
            config_data = self.load_config(config_info)
            
            # 根据配置类型进行特定验证
            if config_info.config_type == ConfigType.TRADITIONAL_MULTI:
                errors.extend(self._validate_traditional_config(config_data))
            elif config_info.config_type == ConfigType.UNIFIED_SINGLE:
                errors.extend(self._validate_unified_config(config_data))
            elif config_info.config_type == ConfigType.UNIVERSAL_CONFIG:
                errors.extend(self._validate_universal_config(config_data))
            
        except Exception as e:
            errors.append(f"配置验证失败: {e}")
        
        return len(errors) == 0, errors
    
    def _validate_traditional_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证传统多配置文件"""
        errors = []
        
        # 检查必需的配置文件
        required_files = ['config']
        for required in required_files:
            if required not in config_data:
                errors.append(f"缺少必需的配置文件: {required}.yml")
        
        # 验证config.yml的基本结构
        if 'config' in config_data:
            config = config_data['config']
            if not isinstance(config, dict):
                errors.append("config.yml格式错误")
            else:
                # 检查仿真参数
                if 'simulation' in config:
                    sim = config['simulation']
                    if 'end_time' not in sim:
                        errors.append("config.yml缺少simulation.duration参数")
                    if 'dt' not in sim:
                        errors.append("config.yml缺少simulation.dt参数")
        
        return errors
    
    def _validate_unified_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证统一配置文件"""
        errors = []
        
        if not isinstance(config_data, dict):
            errors.append("统一配置文件格式错误")
            return errors
        
        # 检查基本结构
        required_sections = ['simulation']
        for section in required_sections:
            if section not in config_data:
                errors.append(f"统一配置文件缺少{section}部分")
        
        return errors
    
    def _validate_universal_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证通用配置文件"""
        errors = []
        
        if not isinstance(config_data, dict):
            errors.append("通用配置文件格式错误")
            return errors
        
        # 检查基本结构
        if 'simulation' not in config_data:
            errors.append("通用配置文件缺少simulation部分")
        
        return errors
    
    def get_runner_recommendation(self, config_info: ConfigInfo) -> str:
        """获取推荐的运行器
        
        Args:
            config_info: 配置信息对象
            
        Returns:
            str: 推荐的运行器名称
        """
        runner_map = {
            ConfigType.TRADITIONAL_MULTI: "run_scenario.py",
            ConfigType.UNIFIED_SINGLE: "run_unified_scenario.py", 
            ConfigType.UNIVERSAL_CONFIG: "run_universal_config.py",
            ConfigType.HARDCODED: "run_hardcoded.py",
            ConfigType.UNKNOWN: "无法确定"
        }
        
        return runner_map.get(config_info.config_type, "未知")
    
    def list_available_examples(self, examples_dir: Path) -> Dict[ConfigType, List[ConfigInfo]]:
        """列出可用的示例
        
        Args:
            examples_dir: 示例目录路径
            
        Returns:
            Dict: 按配置类型分组的示例列表
        """
        examples_by_type = {
            ConfigType.TRADITIONAL_MULTI: [],
            ConfigType.UNIFIED_SINGLE: [],
            ConfigType.UNIVERSAL_CONFIG: [],
            ConfigType.HARDCODED: []
        }
        
        if not examples_dir.exists():
            return examples_by_type
        
        # 递归搜索示例目录
        for item in examples_dir.rglob('*'):
            if item.is_dir():
                config_info = self.detect_config_type(item)
                if config_info.config_type != ConfigType.UNKNOWN:
                    examples_by_type[config_info.config_type].append(config_info)
        
        return examples_by_type
    
    def convert_config(self, source_config: ConfigInfo, target_type: ConfigType, 
                      output_path: Path) -> ConfigInfo:
        """转换配置格式
        
        Args:
            source_config: 源配置信息
            target_type: 目标配置类型
            output_path: 输出路径
            
        Returns:
            ConfigInfo: 转换后的配置信息
        """
        # 加载源配置
        source_data = self.load_config(source_config)
        
        # 根据目标类型进行转换
        if target_type == ConfigType.UNIFIED_SINGLE:
            return self._convert_to_unified(source_config, source_data, output_path)
        elif target_type == ConfigType.TRADITIONAL_MULTI:
            return self._convert_to_traditional(source_config, source_data, output_path)
        elif target_type == ConfigType.UNIVERSAL_CONFIG:
            return self._convert_to_universal(source_config, source_data, output_path)
        else:
            raise ValueError(f"不支持转换到类型: {target_type}")
    
    def _convert_to_unified(self, source_config: ConfigInfo, source_data: Dict[str, Any], 
                           output_path: Path) -> ConfigInfo:
        """转换为统一配置格式"""
        # 实现转换逻辑
        # 这里是一个简化的实现，实际需要根据具体需求完善
        unified_data = {}
        
        if source_config.config_type == ConfigType.TRADITIONAL_MULTI:
            # 合并传统多配置文件
            unified_data.update(source_data.get('config', {}))
            if 'components' in source_data:
                # 直接使用components数据，而不是嵌套
                components_data = source_data['components'].get('components', source_data['components'])
                # 如果是列表格式，转换为字典格式
                if isinstance(components_data, list):
                    components_dict = {}
                    for i, comp in enumerate(components_data):
                        comp_id = comp.get('id', f'comp_{i}')
                        # 将class字段重命名为type字段
                        if 'class' in comp:
                            comp['type'] = comp.pop('class')
                        components_dict[comp_id] = comp
                    unified_data['components'] = components_dict
                else:
                    unified_data['components'] = components_data
            if 'topology' in source_data:
                # 直接使用topology数据，而不是嵌套
                unified_data['topology'] = source_data['topology'].get('topology', source_data['topology'])
            if 'agents' in source_data:
                # 直接使用agents数据，而不是嵌套
                agents_data = source_data['agents'].get('agents', source_data['agents'])
                # 如果是列表格式，转换为字典格式
                if isinstance(agents_data, list):
                    agents_dict = {}
                    for i, agent in enumerate(agents_data):
                        agent_id = agent.get('id', f'agent_{i}')
                        # 将class字段重命名为type字段
                        if 'class' in agent:
                            agent['type'] = agent.pop('class')
                        agents_dict[agent_id] = agent
                    unified_data['agents'] = agents_dict
                else:
                    unified_data['agents'] = agents_data
        
        # 保存统一配置文件
        if output_path.suffix in ['.yml', '.yaml']:
            # 如果output_path是文件路径
            output_file = output_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # 如果output_path是目录路径
            output_file = output_path / 'unified_config.yml'
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(unified_data, f, default_flow_style=False, allow_unicode=True)
        
        return ConfigInfo(
            config_type=ConfigType.UNIFIED_SINGLE,
            config_path=output_path,
            config_files={'unified': output_file},
            metadata=source_config.metadata,
            description="转换后的统一配置文件"
        )
    
    def _convert_to_traditional(self, source_config: ConfigInfo, source_data: Dict[str, Any], 
                               output_path: Path) -> ConfigInfo:
        """转换为传统多配置文件格式"""
        # 实现转换逻辑
        output_files = {}
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        if source_config.config_type == ConfigType.UNIFIED_SINGLE:
            # 分离统一配置文件
            config_data = {
                'simulation': source_data.get('simulation', {}),
                'description': source_data.get('description', ''),
                'run_with': source_data.get('run_with', 'traditional_multi')
            }
            
            # 保存各个配置文件
            for key, filename in self.traditional_files.items():
                file_path = output_path / filename
                
                if key == 'config':
                    data = config_data
                else:
                    data = source_data.get(key, {})
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                
                output_files[key] = file_path
        
        return ConfigInfo(
            config_type=ConfigType.TRADITIONAL_MULTI,
            config_path=output_path,
            config_files=output_files,
            metadata=source_config.metadata,
            description="转换后的传统多配置文件"
        )
    
    def _convert_to_universal(self, source_config: ConfigInfo, source_data: Dict[str, Any], 
                             output_path: Path) -> ConfigInfo:
        """转换为通用配置文件格式"""
        # 实现转换逻辑
        universal_data = {
            'simulation': source_data.get('simulation', {}),
            'debug': {
                'enabled': True,
                'log_level': 'INFO',
                'log_file': 'simulation.log',
                'session_id': 'auto',
                'data_collection': {
                    'enabled': True,
                    'output_dir': 'output'
                },
                'web_dashboard': {
                    'enabled': False,
                    'port': 8080
                }
            }
        }
        
        # 合并其他数据
        for key in ['components', 'topology', 'agents']:
            if key in source_data:
                universal_data[key] = source_data[key]
        
        # 保存通用配置文件
        output_file = output_path / 'universal_config.yml'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(universal_data, f, default_flow_style=False, allow_unicode=True)
        
        return ConfigInfo(
            config_type=ConfigType.UNIVERSAL_CONFIG,
            config_path=output_path,
            config_files={'universal': output_file},
            metadata=source_config.metadata,
            description="转换后的通用配置文件"
        )


def validate_yaml_content(yaml_content: str) -> Dict[str, Any]:
    """
    验证YAML内容的有效性
    
    Args:
        yaml_content: 要验证的YAML字符串内容
        
    Returns:
        Dict[str, Any]: 验证结果，包含:
            - valid: bool, 是否有效
            - errors: List[str], 错误信息列表
            - warnings: List[str], 警告信息列表（可选）
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    try:
        # 基本YAML语法验证
        if not yaml_content or not yaml_content.strip():
            result['valid'] = False
            result['errors'].append("YAML内容为空")
            return result
            
        # 尝试解析YAML
        parsed_content = yaml.safe_load(yaml_content)
        
        if parsed_content is None:
            result['valid'] = False
            result['errors'].append("YAML解析结果为空")
            return result
            
        # 基本结构验证
        if not isinstance(parsed_content, dict):
            result['warnings'].append("YAML内容不是字典格式，可能不符合配置文件规范")
            
        # 检查常见的配置文件字段
        if isinstance(parsed_content, dict):
            # 检查是否包含基本的配置结构
            common_fields = ['simulation', 'components', 'agents', 'topology', 'disturbances']
            found_fields = [field for field in common_fields if field in parsed_content]
            
            if not found_fields:
                result['warnings'].append("未找到常见的配置字段，请确认这是一个有效的CHS-SDK配置文件")
                
    except yaml.YAMLError as e:
        result['valid'] = False
        result['errors'].append(f"YAML语法错误: {str(e)}")
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"验证过程中发生错误: {str(e)}")
        
    return result