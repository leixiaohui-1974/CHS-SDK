"""
配置验证器
为不同类型的智能体提供配置验证功能
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging


class ConfigValidator(ABC):
    """配置验证器基类"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        pass


class MPCAgentConfigValidator(ConfigValidator):
    """MPC智能体配置验证器"""
    
    REQUIRED_FIELDS = [
        'prediction_horizon',
        'control_horizon', 
        'time_step',
        'control_targets',
        'target_water_levels'
    ]
    
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []
        
        # 检查必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # 检查数值范围
        if 'prediction_horizon' in config:
            if not isinstance(config['prediction_horizon'], int) or config['prediction_horizon'] <= 0:
                errors.append("prediction_horizon must be a positive integer")
        
        if 'control_horizon' in config:
            if not isinstance(config['control_horizon'], int) or config['control_horizon'] <= 0:
                errors.append("control_horizon must be a positive integer")
        
        if 'time_step' in config:
            if not isinstance(config['time_step'], (int, float)) or config['time_step'] <= 0:
                errors.append("time_step must be a positive number")
        
        return len(errors) == 0, errors


class PerceptionAgentConfigValidator(ConfigValidator):
    """感知智能体配置验证器"""
    
    REQUIRED_FIELDS = [
        'monitored_components',
        'update_interval'
    ]
    
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        if 'monitored_components' in config:
            if not isinstance(config['monitored_components'], list):
                errors.append("monitored_components must be a list")
        
        return len(errors) == 0, errors


# 验证器注册表
VALIDATORS = {
    'mpc': MPCAgentConfigValidator(),
    'perception': PerceptionAgentConfigValidator(),
}


def validate_agent_config(agent_type: str, config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证智能体配置
    
    Args:
        agent_type: 智能体类型
        config: 配置字典
        
    Returns:
        tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    validator = VALIDATORS.get(agent_type)
    if not validator:
        return True, []  # 没有验证器则认为有效
    
    return validator.validate(config)
