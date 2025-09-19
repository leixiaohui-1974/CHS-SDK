# -*- coding: utf-8 -*-
"""
配置加载器

用于加载和合并YAML配置文件，支持变量引用和替换，
消除硬编码问题，提升配置的可维护性和通用性。

核心功能：
1. 加载config_constants.yml常量配置
2. 处理其他YAML文件中的变量引用（${config_constants.path.to.value}格式）
3. 验证配置的完整性和合理性
4. 支持物理模型参数的合理性检查

遵循规范：
- 禁止魔数、硬编码及隐式默认值
- 物理模型的合理性
- 通用性设计，不针对特定案例
"""

import yaml
import re
import logging
from pathlib import Path
from typing import Dict, Any, Union, List
import copy

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """配置错误异常类"""
    pass

class PhysicalModelValidator:
    """物理模型参数验证器"""
    
    # 物理参数合理性范围
    PHYSICAL_CONSTRAINTS = {
        'water_level_m': {'min': 0.0, 'max': 1000.0, 'unit': '米'},
        'pressure_mpa': {'min': 0.0, 'max': 10.0, 'unit': 'MPa'},
        'flow_rate_m3s': {'min': 0.0, 'max': 1000.0, 'unit': 'm³/s'},
        'gate_opening': {'min': 0.0, 'max': 1.0, 'unit': '无量纲'},
        'valve_setting': {'min': 0.0, 'max': 1.0, 'unit': '无量纲'},
        'pid_gain': {'min': -10.0, 'max': 10.0, 'unit': '无量纲'},
        'time_hours': {'min': 0.0, 'max': 8760.0, 'unit': '小时'},  # 最大1年
        'discharge_coefficient': {'min': 0.1, 'max': 1.0, 'unit': '无量纲'},
        'surface_area_m2': {'min': 1.0, 'max': 1e10, 'unit': 'm²'},
        'diameter_m': {'min': 0.1, 'max': 10.0, 'unit': '米'},
        'length_m': {'min': 1.0, 'max': 200000.0, 'unit': '米'},
        'width_m': {'min': 0.1, 'max': 50.0, 'unit': '米'}
    }
    
    @classmethod
    def validate_parameter(cls, param_name: str, value: float, context: str = "") -> bool:
        """
        验证单个物理参数的合理性
        
        Args:
            param_name: 参数名称
            value: 参数值
            context: 上下文信息（用于错误报告）
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigurationError: 当参数不合理时
        """
        # 查找匹配的约束条件
        constraint_key = None
        for key in cls.PHYSICAL_CONSTRAINTS:
            if key in param_name.lower() or param_name.lower().endswith(key.split('_')[-1]):
                constraint_key = key
                break
        
        if constraint_key:
            constraint = cls.PHYSICAL_CONSTRAINTS[constraint_key]
            if not (constraint['min'] <= value <= constraint['max']):
                raise ConfigurationError(
                    f"物理参数不合理 - {param_name}={value} {constraint['unit']} "
                    f"(合理范围: {constraint['min']}-{constraint['max']} {constraint['unit']}) "
                    f"上下文: {context}"
                )
        else:
            logger.warning(f"未找到参数 {param_name} 的物理约束条件，跳过验证")
        
        return True
    
    @classmethod  
    def validate_pid_parameters(cls, pid_config: Dict[str, Any], controller_id: str = "") -> bool:
        """
        验证PID控制器参数的合理性
        
        Args:
            pid_config: PID配置字典
            controller_id: 控制器ID（用于错误报告）
            
        Returns:
            bool: 验证是否通过
        """
        required_params = ['Kp', 'Ki', 'Kd', 'setpoint']
        optional_params = ['min_output', 'max_output']
        
        # 检查必需参数
        for param in required_params:
            if param not in pid_config:
                raise ConfigurationError(f"PID控制器 {controller_id} 缺少必需参数: {param}")
        
        # 验证PID增益参数
        for gain in ['Kp', 'Ki', 'Kd']:
            cls.validate_parameter(f"pid_{gain.lower()}", pid_config[gain], f"PID控制器 {controller_id}")
        
        # 验证输出限制
        if 'min_output' in pid_config and 'max_output' in pid_config:
            min_out = pid_config['min_output']
            max_out = pid_config['max_output']
            if min_out >= max_out:
                raise ConfigurationError(
                    f"PID控制器 {controller_id} 输出限制不合理: min_output({min_out}) >= max_output({max_out})"
                )
        
        return True

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        初始化配置加载器
        
        Args:
            base_dir: 配置文件基础目录
        """
        self.base_dir = Path(base_dir)
        self.constants_cache = None
        self.validator = PhysicalModelValidator()
        
    def load_constants(self, constants_file: str = "config_constants.yml") -> Dict[str, Any]:
        """
        加载常量配置文件
        
        Args:
            constants_file: 常量配置文件名
            
        Returns:
            Dict: 常量配置字典
        """
        if self.constants_cache is not None:
            return self.constants_cache
            
        constants_path = self.base_dir / constants_file
        if not constants_path.exists():
            raise ConfigurationError(f"常量配置文件不存在: {constants_path}")
        
        try:
            with open(constants_path, 'r', encoding='utf-8') as f:
                self.constants_cache = yaml.safe_load(f)
            
            logger.info(f"成功加载常量配置: {constants_path}")
            self._validate_constants()
            return self.constants_cache
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"解析常量配置文件失败: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载常量配置文件失败: {e}")
    
    def _validate_constants(self):
        """验证常量配置的合理性"""
        if not self.constants_cache:
            return
        
        # 验证PID控制器参数
        if 'pid_controllers' in self.constants_cache:
            for controller_id, config in self.constants_cache['pid_controllers'].items():
                self.validator.validate_pid_parameters(config, controller_id)
        
        # 验证应急处理参数
        if 'emergency_control' in self.constants_cache:
            emergency_config = self.constants_cache['emergency_control']
            if 'pressure_threshold_mpa' in emergency_config:
                self.validator.validate_parameter(
                    'pressure_mpa', 
                    emergency_config['pressure_threshold_mpa'],
                    '应急处理压力阈值'
                )
        
        # 验证中央调度参数
        if 'central_dispatcher' in self.constants_cache:
            dispatcher_config = self.constants_cache['central_dispatcher']
            if 'terminal_pool' in dispatcher_config:
                pool_config = dispatcher_config['terminal_pool']
                for param in ['low_level_m', 'high_level_m']:
                    if param in pool_config:
                        self.validator.validate_parameter(
                            'water_level_m',
                            pool_config[param],
                            f'中央调度器 {param}'
                        )
        
        logger.info("常量配置验证通过")
    
    def _resolve_reference(self, ref_path: str) -> Any:
        """
        解析配置引用路径
        
        Args:
            ref_path: 引用路径，如 "config_constants.pid_controllers.taoriver_gate.Kp"
            
        Returns:
            Any: 引用的值
        """
        if not ref_path.startswith('config_constants.'):
            raise ConfigurationError(f"不支持的引用格式: {ref_path}")
        
        path_parts = ref_path.split('.')[1:]  # 去掉 'config_constants' 前缀
        current = self.constants_cache
        
        try:
            for part in path_parts:
                current = current[part]
            return current
        except (KeyError, TypeError) as e:
            raise ConfigurationError(f"无法解析引用路径: {ref_path}, 错误: {e}")
    
    def _substitute_variables(self, config: Any) -> Any:
        """
        递归替换配置中的变量引用
        
        Args:
            config: 配置对象（可能包含变量引用）
            
        Returns:
            Any: 替换后的配置对象
        """
        if isinstance(config, dict):
            result = {}
            for key, value in config.items():
                result[key] = self._substitute_variables(value)
            return result
        elif isinstance(config, list):
            return [self._substitute_variables(item) for item in config]
        elif isinstance(config, str):
            # 查找变量引用模式 ${config_constants.path.to.value}
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, config)
            
            if matches:
                result = config
                for match in matches:
                    ref_value = self._resolve_reference(match)
                    result = result.replace(f'${{{match}}}', str(ref_value))
                
                # 尝试转换为适当的类型
                try:
                    # 如果结果是纯数字，转换为float或int
                    if result.replace('.', '').replace('-', '').isdigit():
                        return float(result) if '.' in result else int(result)
                    return result
                except ValueError:
                    return result
            else:
                return config
        else:
            return config
    
    def load_config_with_substitution(self, config_file: str) -> Dict[str, Any]:
        """
        加载配置文件并执行变量替换
        
        Args:
            config_file: 配置文件名
            
        Returns:
            Dict: 处理后的配置字典
        """
        # 确保常量已加载
        self.load_constants()
        
        config_path = self.base_dir / config_file
        if not config_path.exists():
            raise ConfigurationError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            
            # 执行变量替换
            processed_config = self._substitute_variables(raw_config)
            
            logger.info(f"成功加载并处理配置文件: {config_path}")
            return processed_config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"解析配置文件失败: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {e}")
    
    def get_merged_config(self, config_files: List[str]) -> Dict[str, Any]:
        """
        加载并合并多个配置文件
        
        Args:
            config_files: 配置文件名列表
            
        Returns:
            Dict: 合并后的配置字典
        """
        merged_config = {}
        
        for config_file in config_files:
            config = self.load_config_with_substitution(config_file)
            
            # 深度合并配置
            self._deep_merge(merged_config, config)
        
        return merged_config
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        深度合并两个字典
        
        Args:
            target: 目标字典（会被修改）
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

# 便利函数
def load_scenario_config(scenario_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    加载场景的完整配置
    
    Args:
        scenario_dir: 场景目录路径
        
    Returns:
        Dict: 完整的场景配置
    """
    loader = ConfigLoader(scenario_dir)
    
    # 标准配置文件列表（按加载顺序）
    config_files = [
        "components.yml",
        "agents.yml"
    ]
    
    # 过滤存在的配置文件
    existing_files = []
    for config_file in config_files:
        if (Path(scenario_dir) / config_file).exists():
            existing_files.append(config_file)
    
    if not existing_files:
        raise ConfigurationError(f"在目录 {scenario_dir} 中未找到任何配置文件")
    
    return loader.get_merged_config(existing_files)

def validate_scenario_config(config: Dict[str, Any]) -> bool:
    """
    验证场景配置的完整性和合理性
    
    Args:
        config: 场景配置字典
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        ConfigurationError: 当配置不合理时
    """
    validator = PhysicalModelValidator()
    
    # 验证组件配置
    if 'components' in config:
        for component in config['components']:
            component_id = component.get('id', '未知组件')
            
            # 验证初始状态参数
            if 'initial_state' in component:
                for param, value in component['initial_state'].items():
                    if isinstance(value, (int, float)):
                        validator.validate_parameter(param, value, f"组件 {component_id}")
            
            # 验证参数
            if 'parameters' in component:
                for param, value in