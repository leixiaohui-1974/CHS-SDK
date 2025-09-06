#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台参数验证工具
提供参数验证功能
"""

import logging
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
            
            elif param_type == "boolean":
                if not isinstance(value, bool):
                    return False
            
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
