# -*- coding: utf-8 -*-
"""
Validation and Diagnosis Routes for MCP Service

实现ValidatorAgent的核心功能：
- 静态配置验证
- 动态运行诊断
- 错误分析和修复建议
- 配置文件语法检查
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import uuid
import logging
import asyncio
import json
import yaml
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import tempfile
from enum import Enum
import traceback
import re

# 导入现有的配置检查工具
from core_lib.config_validator import ConfigValidator
from core_lib.models.universal_config import UniversalConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/validator", tags=["validation"])

# 验证状态枚举
class ValidationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

# 错误严重程度枚举
class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# 验证类型枚举
class ValidationType(str, Enum):
    SYNTAX = "syntax"
    SCHEMA = "schema"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    COMPREHENSIVE = "comprehensive"

# 验证任务存储
validation_store: Dict[str, Dict[str, Any]] = {}

# Pydantic模型定义
class ValidationRequest(BaseModel):
    """验证请求"""
    session_id: str
    config_content: Optional[str] = None  # YAML配置内容
    config_file_path: Optional[str] = None  # 配置文件路径
    validation_type: ValidationType = ValidationType.COMPREHENSIVE
    strict_mode: bool = False  # 严格模式
    custom_rules: Optional[List[str]] = None  # 自定义验证规则

class DiagnosisRequest(BaseModel):
    """诊断请求"""
    run_id: str
    error_log: Optional[str] = None  # 错误日志
    traceback_info: Optional[str] = None  # 堆栈跟踪信息
    config_content: Optional[str] = None  # 相关配置内容
    include_suggestions: bool = True  # 是否包含修复建议

class ValidationError(BaseModel):
    """验证错误"""
    error_id: str
    severity: ErrorSeverity
    category: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    field_path: Optional[str] = None
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None

class ValidationResult(BaseModel):
    """验证结果"""
    validation_id: str
    session_id: str
    status: ValidationStatus
    validation_type: ValidationType
    started_at: str
    completed_at: Optional[str] = None
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    summary: Optional[str] = None
    is_valid: bool = False
    confidence_score: Optional[float] = None

class DiagnosisResult(BaseModel):
    """诊断结果"""
    diagnosis_id: str
    run_id: str
    status: str
    root_cause: Optional[str] = None
    error_analysis: Optional[str] = None
    suggestions: List[str] = []
    fix_steps: List[str] = []
    related_config: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    created_at: str

class ValidatorAgent:
    """验证与诊断智能体 - 质量保证工程师和系统医生"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.temp_dir = Path(tempfile.gettempdir()) / "chs_sdk_validation"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 初始化配置验证器
        self.config_validator = ConfigValidator()
        
        # 常见错误模式
        self.error_patterns = {
            "yaml_syntax": [
                r"yaml\.scanner\.ScannerError",
                r"yaml\.parser\.ParserError",
                r"yaml\.constructor\.ConstructorError"
            ],
            "missing_field": [
                r"KeyError: '([^']+)'",
                r"Missing required field: ([^\n]+)",
                r"Field '([^']+)' is required"
            ],
            "type_error": [
                r"TypeError: ([^\n]+)",
                r"Expected ([^,]+), got ([^\n]+)",
                r"Invalid type for field '([^']+)'"
            ],
            "value_error": [
                r"ValueError: ([^\n]+)",
                r"Invalid value for field '([^']+)'",
                r"Value must be ([^\n]+)"
            ],
            "connection_error": [
                r"Connection error: ([^\n]+)",
                r"Component '([^']+)' not found",
                r"Invalid connection between ([^\n]+)"
            ]
        }
    
    async def validate_config(self, request: ValidationRequest) -> ValidationResult:
        """
        验证配置文件
        
        Args:
            request: 验证请求
            
        Returns:
            ValidationResult: 验证结果
        """
        validation_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting validation {validation_id} for session {request.session_id}")
            
            # 初始化验证记录
            validation_store[validation_id] = {
                "validation_id": validation_id,
                "session_id": request.session_id,
                "status": ValidationStatus.PENDING,
                "validation_type": request.validation_type,
                "started_at": datetime.now().isoformat(),
                "errors": [],
                "warnings": [],
                "is_valid": False
            }
            
            # 异步启动验证进程
            asyncio.create_task(self._run_validation_process(validation_id, request))
            
            return ValidationResult(
                validation_id=validation_id,
                session_id=request.session_id,
                status=ValidationStatus.PENDING,
                validation_type=request.validation_type,
                started_at=validation_store[validation_id]["started_at"]
            )
            
        except Exception as e:
            logger.error(f"Error starting validation: {str(e)}")
            return ValidationResult(
                validation_id=validation_id,
                session_id=request.session_id,
                status=ValidationStatus.FAILED,
                validation_type=request.validation_type,
                started_at=datetime.now().isoformat(),
                errors=[ValidationError(
                    error_id=str(uuid.uuid4()),
                    severity=ErrorSeverity.CRITICAL,
                    category="system",
                    message=f"验证启动失败: {str(e)}"
                )]
            )
    
    async def _run_validation_process(self, validation_id: str, request: ValidationRequest):
        """
        异步运行验证进程
        
        Args:
            validation_id: 验证任务ID
            request: 验证请求
        """
        try:
            validation_data = validation_store[validation_id]
            validation_data["status"] = ValidationStatus.RUNNING
            
            logger.info(f"Running validation process {validation_id}")
            
            # 获取配置内容
            config_content = await self._get_config_content(request)
            
            errors = []
            warnings = []
            
            # 1. 语法验证
            if request.validation_type in [ValidationType.SYNTAX, ValidationType.COMPREHENSIVE]:
                syntax_errors = await self._validate_syntax(config_content)
                errors.extend(syntax_errors)
            
            # 2. Schema验证
            if request.validation_type in [ValidationType.SCHEMA, ValidationType.COMPREHENSIVE]:
                schema_errors, schema_warnings = await self._validate_schema(config_content)
                errors.extend(schema_errors)
                warnings.extend(schema_warnings)
            
            # 3. 语义验证
            if request.validation_type in [ValidationType.SEMANTIC, ValidationType.COMPREHENSIVE]:
                semantic_errors, semantic_warnings = await self._validate_semantics(config_content)
                errors.extend(semantic_errors)
                warnings.extend(semantic_warnings)
            
            # 4. 运行时验证（调用config_check.py）
            if request.validation_type in [ValidationType.RUNTIME, ValidationType.COMPREHENSIVE]:
                runtime_errors, runtime_warnings = await self._validate_runtime(config_content, request.session_id)
                errors.extend(runtime_errors)
                warnings.extend(runtime_warnings)
            
            # 5. 自定义规则验证
            if request.custom_rules:
                custom_errors = await self._validate_custom_rules(config_content, request.custom_rules)
                errors.extend(custom_errors)
            
            # 确定验证状态
            critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
            major_errors = [e for e in errors if e.severity == ErrorSeverity.ERROR]
            
            if critical_errors:
                status = ValidationStatus.FAILED
                is_valid = False
            elif major_errors:
                status = ValidationStatus.FAILED if request.strict_mode else ValidationStatus.WARNING
                is_valid = not request.strict_mode
            elif warnings:
                status = ValidationStatus.WARNING
                is_valid = True
            else:
                status = ValidationStatus.PASSED
                is_valid = True
            
            # 生成摘要
            summary = self._generate_validation_summary(errors, warnings, is_valid)
            
            # 计算置信度分数
            confidence_score = self._calculate_confidence_score(errors, warnings)
            
            # 更新验证结果
            validation_data.update({
                "status": status,
                "completed_at": datetime.now().isoformat(),
                "errors": [e.dict() for e in errors],
                "warnings": [w.dict() for w in warnings],
                "is_valid": is_valid,
                "summary": summary,
                "confidence_score": confidence_score
            })
            
            logger.info(f"Validation {validation_id} completed with status: {status}")
            
        except Exception as e:
            logger.error(f"Error in validation process {validation_id}: {str(e)}")
            validation_store[validation_id].update({
                "status": ValidationStatus.FAILED,
                "errors": [{
                    "error_id": str(uuid.uuid4()),
                    "severity": ErrorSeverity.CRITICAL,
                    "category": "system",
                    "message": f"验证过程异常: {str(e)}"
                }]
            })
    
    async def _get_config_content(self, request: ValidationRequest) -> str:
        """
        获取配置内容
        
        Args:
            request: 验证请求
            
        Returns:
            str: 配置内容
        """
        if request.config_content:
            return request.config_content
        
        if request.config_file_path:
            config_path = Path(request.config_file_path)
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {request.config_file_path}")
            
            return config_path.read_text(encoding='utf-8')
        
        # 尝试从scenario存储中获取
        from api.routes.scenario import scenario_store
        
        if request.session_id in scenario_store:
            scenario_data = scenario_store[request.session_id]
            if "current_config" in scenario_data:
                return scenario_data["current_config"]
        
        raise ValueError("未提供配置内容或文件路径")
    
    async def _validate_syntax(self, config_content: str) -> List[ValidationError]:
        """
        验证YAML语法
        
        Args:
            config_content: 配置内容
            
        Returns:
            List[ValidationError]: 语法错误列表
        """
        errors = []
        
        try:
            # 尝试解析YAML
            yaml.safe_load(config_content)
            logger.info("YAML syntax validation passed")
            
        except yaml.YAMLError as e:
            error_msg = str(e)
            line_number = None
            column_number = None
            
            # 尝试提取行号和列号
            if hasattr(e, 'problem_mark'):
                line_number = e.problem_mark.line + 1
                column_number = e.problem_mark.column + 1
            
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.CRITICAL,
                category="syntax",
                message=f"YAML语法错误: {error_msg}",
                line_number=line_number,
                column_number=column_number,
                suggestion="请检查YAML语法，确保缩进正确，引号匹配"
            ))
            
        except Exception as e:
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.ERROR,
                category="syntax",
                message=f"配置解析错误: {str(e)}",
                suggestion="请检查配置文件格式是否正确"
            ))
        
        return errors
    
    async def _validate_schema(self, config_content: str) -> tuple[List[ValidationError], List[ValidationError]]:
        """
        验证配置Schema
        
        Args:
            config_content: 配置内容
            
        Returns:
            tuple: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        try:
            # 解析YAML
            config_data = yaml.safe_load(config_content)
            
            if not isinstance(config_data, dict):
                errors.append(ValidationError(
                    error_id=str(uuid.uuid4()),
                    severity=ErrorSeverity.CRITICAL,
                    category="schema",
                    message="配置文件根节点必须是字典类型",
                    suggestion="请确保配置文件以键值对形式组织"
                ))
                return errors, warnings
            
            # 使用Pydantic模型验证
            try:
                universal_config = UniversalConfig(**config_data)
                logger.info("Schema validation passed")
                
            except Exception as e:
                error_msg = str(e)
                
                # 解析Pydantic错误
                if "validation error" in error_msg.lower():
                    # 尝试解析字段路径和错误信息
                    field_errors = self._parse_pydantic_errors(error_msg)
                    errors.extend(field_errors)
                else:
                    errors.append(ValidationError(
                        error_id=str(uuid.uuid4()),
                        severity=ErrorSeverity.ERROR,
                        category="schema",
                        message=f"Schema验证失败: {error_msg}",
                        suggestion="请检查配置字段是否符合要求的数据类型和格式"
                    ))
            
            # 检查必需字段
            required_fields = ["simulation", "components"]
            for field in required_fields:
                if field not in config_data:
                    errors.append(ValidationError(
                        error_id=str(uuid.uuid4()),
                        severity=ErrorSeverity.ERROR,
                        category="schema",
                        message=f"缺少必需字段: {field}",
                        field_path=field,
                        suggestion=f"请添加 {field} 字段到配置文件中"
                    ))
            
            # 检查推荐字段
            recommended_fields = ["metadata", "connections"]
            for field in recommended_fields:
                if field not in config_data:
                    warnings.append(ValidationError(
                        error_id=str(uuid.uuid4()),
                        severity=ErrorSeverity.WARNING,
                        category="schema",
                        message=f"建议添加字段: {field}",
                        field_path=field,
                        suggestion=f"添加 {field} 字段可以提供更完整的配置信息"
                    ))
            
        except yaml.YAMLError:
            # YAML语法错误已在语法验证中处理
            pass
        except Exception as e:
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.ERROR,
                category="schema",
                message=f"Schema验证异常: {str(e)}",
                suggestion="请检查配置文件结构是否正确"
            ))
        
        return errors, warnings
    
    def _parse_pydantic_errors(self, error_msg: str) -> List[ValidationError]:
        """
        解析Pydantic验证错误
        
        Args:
            error_msg: 错误消息
            
        Returns:
            List[ValidationError]: 解析后的错误列表
        """
        errors = []
        
        try:
            # 简单的错误解析逻辑
            lines = error_msg.split('\n')
            for line in lines:
                if 'field required' in line.lower():
                    # 提取字段名
                    field_match = re.search(r"field '([^']+)' required", line)
                    if field_match:
                        field_name = field_match.group(1)
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="schema",
                            message=f"必需字段缺失: {field_name}",
                            field_path=field_name,
                            suggestion=f"请添加字段 {field_name}"
                        ))
                
                elif 'invalid type' in line.lower():
                    errors.append(ValidationError(
                        error_id=str(uuid.uuid4()),
                        severity=ErrorSeverity.ERROR,
                        category="schema",
                        message=f"数据类型错误: {line}",
                        suggestion="请检查字段的数据类型是否正确"
                    ))
        
        except Exception as e:
            logger.error(f"Error parsing Pydantic errors: {str(e)}")
        
        return errors
    
    async def _validate_semantics(self, config_content: str) -> tuple[List[ValidationError], List[ValidationError]]:
        """
        验证配置语义
        
        Args:
            config_content: 配置内容
            
        Returns:
            tuple: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        try:
            config_data = yaml.safe_load(config_content)
            
            # 检查组件连接的有效性
            if "components" in config_data and "connections" in config_data:
                component_names = set(config_data["components"].keys())
                connections = config_data["connections"]
                
                for connection in connections:
                    if "from" in connection and connection["from"] not in component_names:
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="semantic",
                            message=f"连接引用了不存在的组件: {connection['from']}",
                            field_path="connections",
                            suggestion=f"请确保组件 {connection['from']} 在 components 中定义"
                        ))
                    
                    if "to" in connection and connection["to"] not in component_names:
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="semantic",
                            message=f"连接引用了不存在的组件: {connection['to']}",
                            field_path="connections",
                            suggestion=f"请确保组件 {connection['to']} 在 components 中定义"
                        ))
            
            # 检查组件类型的合理性
            if "components" in config_data:
                valid_component_types = ["Reservoir", "Gate", "RiverChannel", "Sensor", "Controller"]
                
                for comp_name, comp_config in config_data["components"].items():
                    if "type" in comp_config:
                        comp_type = comp_config["type"]
                        if comp_type not in valid_component_types:
                            warnings.append(ValidationError(
                                error_id=str(uuid.uuid4()),
                                severity=ErrorSeverity.WARNING,
                                category="semantic",
                                message=f"未知的组件类型: {comp_type} (组件: {comp_name})",
                                field_path=f"components.{comp_name}.type",
                                suggestion=f"建议使用标准组件类型: {', '.join(valid_component_types)}"
                            ))
            
            # 检查仿真参数的合理性
            if "simulation" in config_data:
                sim_config = config_data["simulation"]
                
                # 检查时间步长
                if "time_step" in sim_config:
                    time_step = sim_config["time_step"]
                    if isinstance(time_step, (int, float)) and time_step <= 0:
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="semantic",
                            message="时间步长必须大于0",
                            field_path="simulation.time_step",
                            suggestion="请设置一个正数作为时间步长"
                        ))
                
                # 检查仿真时长
                if "duration" in sim_config:
                    duration = sim_config["duration"]
                    if isinstance(duration, (int, float)) and duration <= 0:
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="semantic",
                            message="仿真时长必须大于0",
                            field_path="simulation.duration",
                            suggestion="请设置一个正数作为仿真时长"
                        ))
            
        except Exception as e:
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.ERROR,
                category="semantic",
                message=f"语义验证异常: {str(e)}",
                suggestion="请检查配置文件的逻辑一致性"
            ))
        
        return errors, warnings
    
    async def _validate_runtime(self, config_content: str, session_id: str) -> tuple[List[ValidationError], List[ValidationError]]:
        """
        运行时验证（调用config_check.py）
        
        Args:
            config_content: 配置内容
            session_id: 会话ID
            
        Returns:
            tuple: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        try:
            # 保存临时配置文件
            temp_config_file = self.temp_dir / f"temp_config_{session_id}.yml"
            temp_config_file.write_text(config_content, encoding='utf-8')
            
            # 调用config_check.py脚本
            script_path = self.base_path / "examples" / "config_check.py"
            
            if not script_path.exists():
                warnings.append(ValidationError(
                    error_id=str(uuid.uuid4()),
                    severity=ErrorSeverity.WARNING,
                    category="runtime",
                    message="运行时验证脚本不存在，跳过运行时验证",
                    suggestion="请确保 examples/config_check.py 文件存在"
                ))
                return errors, warnings
            
            # 执行验证脚本
            cmd = [sys.executable, str(script_path), str(temp_config_file)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_path
            )
            
            stdout, stderr = await process.communicate()
            
            # 解析验证结果
            if process.returncode == 0:
                # 验证通过
                logger.info("Runtime validation passed")
                output = stdout.decode('utf-8')
                if "warning" in output.lower():
                    # 提取警告信息
                    warning_lines = [line for line in output.split('\n') if 'warning' in line.lower()]
                    for warning_line in warning_lines:
                        warnings.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.WARNING,
                            category="runtime",
                            message=f"运行时警告: {warning_line.strip()}",
                            suggestion="请检查相关配置项"
                        ))
            else:
                # 验证失败
                error_output = stderr.decode('utf-8') or stdout.decode('utf-8')
                
                # 解析错误信息
                runtime_errors = self._parse_runtime_errors(error_output)
                errors.extend(runtime_errors)
            
            # 清理临时文件
            if temp_config_file.exists():
                temp_config_file.unlink()
            
        except Exception as e:
            logger.error(f"Error in runtime validation: {str(e)}")
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.ERROR,
                category="runtime",
                message=f"运行时验证异常: {str(e)}",
                suggestion="请检查配置文件是否可以正常加载和运行"
            ))
        
        return errors, warnings
    
    def _parse_runtime_errors(self, error_output: str) -> List[ValidationError]:
        """
        解析运行时错误
        
        Args:
            error_output: 错误输出
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors = []
        
        try:
            lines = error_output.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配不同类型的错误
                error_matched = False
                
                for error_type, patterns in self.error_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append(ValidationError(
                                error_id=str(uuid.uuid4()),
                                severity=ErrorSeverity.ERROR,
                                category="runtime",
                                message=f"{error_type}: {line}",
                                suggestion=self._get_error_suggestion(error_type)
                            ))
                            error_matched = True
                            break
                    
                    if error_matched:
                        break
                
                # 如果没有匹配到特定模式，添加通用错误
                if not error_matched and any(keyword in line.lower() for keyword in ['error', 'exception', 'failed']):
                    errors.append(ValidationError(
                        error_id=str(uuid.uuid4()),
                        severity=ErrorSeverity.ERROR,
                        category="runtime",
                        message=f"运行时错误: {line}",
                        suggestion="请检查配置文件的运行时兼容性"
                    ))
        
        except Exception as e:
            logger.error(f"Error parsing runtime errors: {str(e)}")
        
        return errors
    
    def _get_error_suggestion(self, error_type: str) -> str:
        """
        获取错误建议
        
        Args:
            error_type: 错误类型
            
        Returns:
            str: 建议信息
        """
        suggestions = {
            "yaml_syntax": "请检查YAML语法，确保缩进和引号正确",
            "missing_field": "请添加缺失的必需字段",
            "type_error": "请检查字段的数据类型是否正确",
            "value_error": "请检查字段值是否在有效范围内",
            "connection_error": "请检查组件连接配置是否正确"
        }
        
        return suggestions.get(error_type, "请检查相关配置项")
    
    async def _validate_custom_rules(self, config_content: str, custom_rules: List[str]) -> List[ValidationError]:
        """
        验证自定义规则
        
        Args:
            config_content: 配置内容
            custom_rules: 自定义规则列表
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors = []
        
        try:
            config_data = yaml.safe_load(config_content)
            
            for rule in custom_rules:
                # 简单的规则验证逻辑
                if rule.startswith("require_field:"):
                    field_path = rule.split(":", 1)[1].strip()
                    if not self._check_field_exists(config_data, field_path):
                        errors.append(ValidationError(
                            error_id=str(uuid.uuid4()),
                            severity=ErrorSeverity.ERROR,
                            category="custom",
                            message=f"自定义规则违反: 缺少字段 {field_path}",
                            field_path=field_path,
                            suggestion=f"请添加字段 {field_path}"
                        ))
                
                elif rule.startswith("min_components:"):
                    min_count = int(rule.split(":", 1)[1].strip())
                    if "components" in config_data:
                        actual_count = len(config_data["components"])
                        if actual_count < min_count:
                            errors.append(ValidationError(
                                error_id=str(uuid.uuid4()),
                                severity=ErrorSeverity.WARNING,
                                category="custom",
                                message=f"组件数量不足: 需要至少 {min_count} 个，实际 {actual_count} 个",
                                suggestion=f"请添加更多组件，至少需要 {min_count} 个"
                            ))
        
        except Exception as e:
            logger.error(f"Error validating custom rules: {str(e)}")
            errors.append(ValidationError(
                error_id=str(uuid.uuid4()),
                severity=ErrorSeverity.ERROR,
                category="custom",
                message=f"自定义规则验证异常: {str(e)}",
                suggestion="请检查自定义规则的格式是否正确"
            ))
        
        return errors
    
    def _check_field_exists(self, data: Dict[str, Any], field_path: str) -> bool:
        """
        检查字段是否存在
        
        Args:
            data: 数据字典
            field_path: 字段路径（如 "simulation.time_step"）
            
        Returns:
            bool: 字段是否存在
        """
        try:
            keys = field_path.split(".")
            current = data
            
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return False
                current = current[key]
            
            return True
        
        except Exception:
            return False
    
    def _generate_validation_summary(self, errors: List[ValidationError], 
                                   warnings: List[ValidationError], is_valid: bool) -> str:
        """
        生成验证摘要
        
        Args:
            errors: 错误列表
            warnings: 警告列表
            is_valid: 是否有效
            
        Returns:
            str: 验证摘要
        """
        if is_valid and not warnings:
            return "配置验证通过，未发现问题"
        
        summary_parts = []
        
        if errors:
            critical_count = len([e for e in errors if e.severity == ErrorSeverity.CRITICAL])
            error_count = len([e for e in errors if e.severity == ErrorSeverity.ERROR])
            
            if critical_count > 0:
                summary_parts.append(f"{critical_count} 个严重错误")
            if error_count > 0:
                summary_parts.append(f"{error_count} 个错误")
        
        if warnings:
            summary_parts.append(f"{len(warnings)} 个警告")
        
        if is_valid:
            return f"配置基本有效，但存在 {', '.join(summary_parts)}"
        else:
            return f"配置验证失败，发现 {', '.join(summary_parts)}"
    
    def _calculate_confidence_score(self, errors: List[ValidationError], 
                                  warnings: List[ValidationError]) -> float:
        """
        计算置信度分数
        
        Args:
            errors: 错误列表
            warnings: 警告列表
            
        Returns:
            float: 置信度分数 (0.0 - 1.0)
        """
        if not errors and not warnings:
            return 1.0
        
        # 计算扣分
        penalty = 0.0
        
        for error in errors:
            if error.severity == ErrorSeverity.CRITICAL:
                penalty += 0.3
            elif error.severity == ErrorSeverity.ERROR:
                penalty += 0.2
        
        for warning in warnings:
            penalty += 0.05
        
        # 确保分数在0-1范围内
        score = max(0.0, 1.0 - penalty)
        return round(score, 2)
    
    async def diagnose_error(self, request: DiagnosisRequest) -> DiagnosisResult:
        """
        诊断运行时错误
        
        Args:
            request: 诊断请求
            
        Returns:
            DiagnosisResult: 诊断结果
        """
        diagnosis_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting diagnosis {diagnosis_id} for run {request.run_id}")
            
            # 分析错误日志
            root_cause = await self._analyze_error_log(request.error_log, request.traceback_info)
            
            # 生成错误分析
            error_analysis = await self._generate_error_analysis(request.error_log, request.config_content)
            
            # 生成修复建议
            suggestions = await self._generate_fix_suggestions(root_cause, request.config_content)
            
            # 生成修复步骤
            fix_steps = await self._generate_fix_steps(root_cause, suggestions)
            
            # 计算置信度
            confidence_score = self._calculate_diagnosis_confidence(root_cause, error_analysis)
            
            return DiagnosisResult(
                diagnosis_id=diagnosis_id,
                run_id=request.run_id,
                status="completed",
                root_cause=root_cause,
                error_analysis=error_analysis,
                suggestions=suggestions,
                fix_steps=fix_steps,
                confidence_score=confidence_score,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in diagnosis: {str(e)}")
            return DiagnosisResult(
                diagnosis_id=diagnosis_id,
                run_id=request.run_id,
                status="failed",
                error_analysis=f"诊断过程异常: {str(e)}",
                suggestions=["请检查错误日志的完整性"],
                fix_steps=["请提供更详细的错误信息"],
                created_at=datetime.now().isoformat()
            )
    
    async def _analyze_error_log(self, error_log: Optional[str], 
                               traceback_info: Optional[str]) -> Optional[str]:
        """
        分析错误日志
        
        Args:
            error_log: 错误日志
            traceback_info: 堆栈跟踪信息
            
        Returns:
            Optional[str]: 根本原因
        """
        try:
            if not error_log and not traceback_info:
                return "未提供错误信息"
            
            combined_log = f"{error_log or ''}\n{traceback_info or ''}"
            
            # 匹配常见错误模式
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, combined_log, re.IGNORECASE):
                        return f"{error_type}: {self._extract_error_details(combined_log, pattern)}"
            
            # 如果没有匹配到特定模式，返回通用分析
            if "KeyError" in combined_log:
                return "配置文件缺少必需的字段或键"
            elif "TypeError" in combined_log:
                return "数据类型不匹配或方法调用错误"
            elif "ValueError" in combined_log:
                return "字段值不在有效范围内或格式错误"
            elif "FileNotFoundError" in combined_log:
                return "找不到必需的文件或路径"
            elif "ImportError" in combined_log:
                return "缺少必需的Python模块或依赖"
            else:
                return "未知错误类型，需要进一步分析"
        
        except Exception as e:
            logger.error(f"Error analyzing error log: {str(e)}")
            return f"错误日志分析异常: {str(e)}"
    
    def _extract_error_details(self, log: str, pattern: str) -> str:
        """
        提取错误详情
        
        Args:
            log: 日志内容
            pattern: 匹配模式
            
        Returns:
            str: 错误详情
        """
        try:
            match = re.search(pattern, log, re.IGNORECASE)
            if match:
                return match.group(0)
            return "详情提取失败"
        except Exception:
            return "详情提取异常"
    
    async def _generate_error_analysis(self, error_log: Optional[str], 
                                     config_content: Optional[str]) -> str:
        """
        生成错误分析
        
        Args:
            error_log: 错误日志
            config_content: 配置内容
            
        Returns:
            str: 错误分析
        """
        try:
            analysis_parts = []
            
            if error_log:
                # 分析错误严重程度
                if any(keyword in error_log.lower() for keyword in ['critical', 'fatal', 'exception']):
                    analysis_parts.append("这是一个严重错误，会导致仿真无法正常运行")
                elif any(keyword in error_log.lower() for keyword in ['warning', 'warn']):
                    analysis_parts.append("这是一个警告，可能影响仿真结果的准确性")
                
                # 分析错误来源
                if 'config' in error_log.lower():
                    analysis_parts.append("错误来源于配置文件")
                elif 'simulation' in error_log.lower():
                    analysis_parts.append("错误发生在仿真运行过程中")
                elif 'component' in error_log.lower():
                    analysis_parts.append("错误与组件配置或运行相关")
            
            if config_content:
                # 分析配置复杂度
                try:
                    config_data = yaml.safe_load(config_content)
                    if isinstance(config_data, dict):
                        component_count = len(config_data.get("components", {}))
                        if component_count > 10:
                            analysis_parts.append("配置较为复杂，包含多个组件")
                        elif component_count == 0:
                            analysis_parts.append("配置中未定义任何组件")
                except Exception:
                    analysis_parts.append("配置文件格式可能存在问题")
            
            if not analysis_parts:
                return "需要更多信息进行详细分析"
            
            return "。".join(analysis_parts) + "。"
        
        except Exception as e:
            logger.error(f"Error generating error analysis: {str(e)}")
            return f"错误分析生成异常: {str(e)}"
    
    async def _generate_fix_suggestions(self, root_cause: Optional[str], 
                                      config_content: Optional[str]) -> List[str]:
        """
        生成修复建议
        
        Args:
            root_cause: 根本原因
            config_content: 配置内容
            
        Returns:
            List[str]: 修复建议列表
        """
        suggestions = []
        
        try:
            if not root_cause:
                return ["请提供更详细的错误信息以获得针对性建议"]
            
            # 基于根本原因生成建议
            if "yaml_syntax" in root_cause.lower():
                suggestions.extend([
                    "检查YAML文件的缩进是否正确（使用空格而非制表符）",
                    "确保所有引号和括号都正确匹配",
                    "验证特殊字符是否需要引号包围"
                ])
            
            elif "missing_field" in root_cause.lower():
                suggestions.extend([
                    "检查配置文件是否包含所有必需字段",
                    "参考配置模板确保字段名称正确",
                    "验证字段的层级结构是否正确"
                ])
            
            elif "type_error" in root_cause.lower():
                suggestions.extend([
                    "检查字段的数据类型是否符合要求",
                    "确保数值字段使用数字而非字符串",
                    "验证布尔字段使用true/false而非其他值"
                ])
            
            elif "connection_error" in root_cause.lower():
                suggestions.extend([
                    "检查组件连接中引用的组件名称是否存在",
                    "验证连接的方向和类型是否正确",
                    "确保连接的组件类型兼容"
                ])
            
            elif "keyerror" in root_cause.lower():
                suggestions.extend([
                    "添加缺失的配置字段",
                    "检查字段名称的拼写是否正确",
                    "确保配置结构完整"
                ])
            
            elif "valueerror" in root_cause.lower():
                suggestions.extend([
                    "检查字段值是否在有效范围内",
                    "确保数值参数为正数（如时间步长、持续时间等）",
                    "验证枚举字段使用的是有效选项"
                ])
            
            else:
                # 通用建议
                suggestions.extend([
                    "检查配置文件的语法和格式",
                    "验证所有必需字段都已正确配置",
                    "确保组件定义和连接配置正确",
                    "检查仿真参数是否合理"
                ])
            
            # 基于配置内容添加特定建议
            if config_content:
                try:
                    config_data = yaml.safe_load(config_content)
                    if isinstance(config_data, dict):
                        if "components" not in config_data:
                            suggestions.append("添加 components 字段定义系统组件")
                        if "simulation" not in config_data:
                            suggestions.append("添加 simulation 字段定义仿真参数")
                except Exception:
                    suggestions.append("修复配置文件的YAML语法错误")
        
        except Exception as e:
            logger.error(f"Error generating fix suggestions: {str(e)}")
            suggestions = ["建议检查配置文件和错误日志，寻求技术支持"]
        
        return suggestions[:10]  # 限制建议数量
    
    async def _generate_fix_steps(self, root_cause: Optional[str], 
                                suggestions: List[str]) -> List[str]:
        """
        生成修复步骤
        
        Args:
            root_cause: 根本原因
            suggestions: 修复建议
            
        Returns:
            List[str]: 修复步骤列表
        """
        steps = []
        
        try:
            # 通用修复步骤
            steps.extend([
                "1. 备份当前配置文件",
                "2. 仔细阅读错误信息，定位问题所在"
            ])
            
            # 基于根本原因添加特定步骤
            if root_cause and "yaml_syntax" in root_cause.lower():
                steps.extend([
                    "3. 使用YAML验证工具检查语法",
                    "4. 修复缩进和引号问题",
                    "5. 重新验证YAML格式"
                ])
            
            elif root_cause and "missing_field" in root_cause.lower():
                steps.extend([
                    "3. 对照配置模板检查缺失字段",
                    "4. 添加必需的字段和默认值",
                    "5. 验证字段层级结构"
                ])
            
            else:
                # 通用步骤
                steps.extend([
                    "3. 根据建议逐项检查和修复问题",
                    "4. 使用配置验证工具验证修改",
                    "5. 进行小规模测试验证修复效果"
                ])
            
            steps.extend([
                "6. 重新运行仿真验证问题是否解决",
                "7. 如问题仍存在，请查看详细日志或寻求技术支持"
            ])
        
        except Exception as e:
            logger.error(f"Error generating fix steps: {str(e)}")
            steps = [
                "1. 备份配置文件",
                "2. 检查错误日志",
                "3. 根据建议修复问题",
                "4. 重新测试"
            ]
        
        return steps
    
    def _calculate_diagnosis_confidence(self, root_cause: Optional[str], 
                                      error_analysis: str) -> float:
        """
        计算诊断置信度
        
        Args:
            root_cause: 根本原因
            error_analysis: 错误分析
            
        Returns:
            float: 置信度分数 (0.0 - 1.0)
        """
        try:
            confidence = 0.5  # 基础置信度
            
            # 如果能识别具体的错误类型，提高置信度
            if root_cause and any(error_type in root_cause.lower() 
                                for error_type in self.error_patterns.keys()):
                confidence += 0.3
            
            # 如果有详细的错误分析，提高置信度
            if error_analysis and len(error_analysis) > 50:
                confidence += 0.2
            
            # 确保置信度在合理范围内
            return min(1.0, max(0.1, confidence))
        
        except Exception:
            return 0.5

# 实例化智能体
validator_agent = ValidatorAgent()

# API路由定义
@router.post("/validate", response_model=ValidationResult)
async def validate_config(request: ValidationRequest):
    """
    验证配置文件
    
    对配置文件进行语法、Schema、语义和运行时验证
    """
    try:
        result = await validator_agent.validate_config(request)
        
        logger.info(f"Started validation {result.validation_id} for session {request.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error validating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{validation_id}")
async def get_validation_status(validation_id: str):
    """
    获取验证状态
    
    返回指定验证任务的当前状态和结果
    """
    try:
        if validation_id not in validation_store:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        validation_data = validation_store[validation_id]
        
        return JSONResponse(content={
            "validation_id": validation_id,
            "status": validation_data["status"],
            "started_at": validation_data["started_at"],
            "completed_at": validation_data.get("completed_at"),
            "is_valid": validation_data.get("is_valid", False),
            "error_count": len(validation_data.get("errors", [])),
            "warning_count": len(validation_data.get("warnings", [])),
            "summary": validation_data.get("summary"),
            "confidence_score": validation_data.get("confidence_score")
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{validation_id}")
async def get_validation_results(validation_id: str):
    """
    获取验证结果
    
    返回完整的验证结果，包括所有错误和警告
    """
    try:
        if validation_id not in validation_store:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        validation_data = validation_store[validation_id]
        
        if validation_data["status"] not in [ValidationStatus.PASSED, ValidationStatus.FAILED, ValidationStatus.WARNING]:
            raise HTTPException(status_code=400, detail="Validation not completed")
        
        return JSONResponse(content={
            "validation_id": validation_id,
            "status": validation_data["status"],
            "is_valid": validation_data["is_valid"],
            "errors": validation_data["errors"],
            "warnings": validation_data["warnings"],
            "summary": validation_data["summary"],
            "confidence_score": validation_data["confidence_score"],
            "completed_at": validation_data["completed_at"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diagnose", response_model=DiagnosisResult)
async def diagnose_error(request: DiagnosisRequest):
    """
    诊断运行时错误
    
    分析错误日志并提供修复建议
    """
    try:
        result = await validator_agent.diagnose_error(request)
        
        logger.info(f"Completed diagnosis {result.diagnosis_id} for run {request.run_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error diagnosing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_validations():
    """
    列出所有验证任务
    
    返回当前系统中的所有验证任务状态
    """
    try:
        validations = []
        for validation_id, data in validation_store.items():
            validations.append({
                "validation_id": validation_id,
                "session_id": data["session_id"],
                "status": data["status"],
                "validation_type": data["validation_type"],
                "started_at": data["started_at"],
                "completed_at": data.get("completed_at"),
                "is_valid": data.get("is_valid", False),
                "error_count": len(data.get("errors", [])),
                "warning_count": len(data.get("warnings", []))
            })
        
        return JSONResponse(content={"validations": validations})
        
    except Exception as e:
        logger.error(f"Error listing validations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup/{validation_id}")
async def cleanup_validation(validation_id: str):
    """
    清理验证任务
    
    删除验证任务记录和临时文件
    """
    try:
        if validation_id not in validation_store:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        # 删除记录
        del validation_store[validation_id]
        
        # 清理临时文件
        temp_files = list(validator_agent.temp_dir.glob(f"*{validation_id}*"))
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
        
        logger.info(f"Cleaned up validation {validation_id}")
        return JSONResponse(content={"message": "Validation cleaned up successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))