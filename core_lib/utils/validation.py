#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台参数验证工具
提供参数验证功能
"""

import logging
import numpy as np
from typing import Any, Dict, List, Union

# 配置日志
logger = logging.getLogger(__name__)

class ParameterValidator:
    """参数验证器"""
    
    def __init__(self):
        """初始化参数验证器"""
        logger.info("参数验证器初始化完成")
    
    def validate_parameter(self, name: str, value: Any, param_type: str, **kwargs) -> bool:
        """
        验证单个参数
        
        Args:
            name: 参数名
            value: 参数值
            param_type: 参数类型
            **kwargs: 其他验证选项
            
        Returns:
            bool: 验证是否通过
        """
        try:
            if param_type == "integer":
                if not isinstance(value, int):
                    return False
                if "min_value" in kwargs and value < kwargs["min_value"]:
                    return False
                if "max_value" in kwargs and value > kwargs["max_value"]:
                    return False
                if "allowed_values" in kwargs and value not in kwargs["allowed_values"]:
                    return False
            
            elif param_type == "number":
                if not isinstance(value, (int, float)):
                    return False
                if "min_value" in kwargs and value < kwargs["min_value"]:
                    return False
                if "max_value" in kwargs and value > kwargs["max_value"]:
                    return False
                if "allowed_values" in kwargs and value not in kwargs["allowed_values"]:
                    return False
            
            elif param_type == "string":
                if not isinstance(value, str):
                    return False
                if "min_length" in kwargs and len(value) < kwargs["min_length"]:
                    return False
                if "max_length" in kwargs and len(value) > kwargs["max_length"]:
                    return False
                if "allowed_values" in kwargs and value not in kwargs["allowed_values"]:
                    return False
            
            elif param_type == "array":
                if not isinstance(value, (list, tuple, np.ndarray)):
                    return False
                if "min_length" in kwargs and len(value) < kwargs["min_length"]:
                    return False
                if "max_length" in kwargs and len(value) > kwargs["max_length"]:
                    return False
                if "element_type" in kwargs:
                    element_type = kwargs["element_type"]
                    if not all(isinstance(item, element_type) for item in value):
                        return False
            
            elif param_type == "dict":
                if not isinstance(value, dict):
                    return False
                if "required_keys" in kwargs:
                    required_keys = kwargs["required_keys"]
                    if not all(key in value for key in required_keys):
                        return False
            
            else:
                logger.warning(f"Unknown parameter type: {param_type}")
                return True  # 未知类型默认通过
            
            return True
            
        except Exception as e:
            logger.error(f"参数验证失败 {name}: {str(e)}")
            return False
    
    def validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证参数集合
        
        Args:
            parameters: 参数字典
            schema: 验证模式
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        for param_name, param_schema in schema.get("properties", {}).items():
            if param_name not in parameters:
                if param_schema.get("required", False):
                    results["valid"] = False
                    results["errors"].append(f"必需参数缺失: {param_name}")
                continue
            
            value = parameters[param_name]
            param_type = param_schema.get("type", "string")
            
            if not self.validate_parameter(param_name, value, param_type, **param_schema):
                results["valid"] = False
                results["errors"].append(f"参数验证失败: {param_name}")
        
        return results
        
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置对象
        
        Args:
            config: 配置字典
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查必需的顶层键
        required_sections = ["simulation", "components"]
        for section in required_sections:
            if section not in config:
                results["valid"] = False
                results["errors"].append(f"缺少必需的配置段: {section}")
        
        # 验证仿真配置
        if "simulation" in config:
            sim_config = config["simulation"]
            
            # 验证时间步长
            if "time_step" in sim_config:
                dt = sim_config["time_step"]
                if not isinstance(dt, (int, float)) or dt <= 0:
                    results["valid"] = False
                    results["errors"].append("time_step必须是正数")
            
            # 验证仿真时长
            if "duration" in sim_config:
                duration = sim_config["duration"]
                if not isinstance(duration, (int, float)) or duration <= 0:
                    results["valid"] = False
                    results["errors"].append("duration必须是正数")
        
        return results
    
    def validate_component_config(self, component_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证组件配置
        
        Args:
            component_config: 组件配置字典
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查组件类型
        if "type" not in component_config:
            results["valid"] = False
            results["errors"].append("组件配置必须包含type字段")
        
        # 检查组件ID
        if "id" not in component_config:
            results["valid"] = False
            results["errors"].append("组件配置必须包含id字段")
        
        # 验证参数
        if "parameters" in component_config:
            params = component_config["parameters"]
            if not isinstance(params, dict):
                results["valid"] = False
                results["errors"].append("组件参数必须是字典类型")
        
        return results
