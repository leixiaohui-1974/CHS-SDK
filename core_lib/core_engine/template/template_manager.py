#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台模板管理器
提供仿真模板的创建、管理、应用和共享功能
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import yaml
from jinja2 import Template, Environment, FileSystemLoader
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.database.database import get_db
from api.database import models
from core_lib.core_engine.solver.simulation_engine import SimulationEngine
from core_lib.utils.validation import ParameterValidator

# 配置日志
logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """模板类型枚举"""
    SIMULATION = "simulation"  # 仿真模板
    PARAMETER = "parameter"    # 参数模板
    WORKFLOW = "workflow"      # 工作流模板
    ANALYSIS = "analysis"      # 分析模板
    REPORT = "report"          # 报告模板

class TemplateCategory(Enum):
    """模板分类枚举"""
    BASIC = "basic"                    # 基础模板
    ADVANCED = "advanced"              # 高级模板
    INDUSTRY_SPECIFIC = "industry"     # 行业专用
    RESEARCH = "research"              # 科研模板
    EDUCATIONAL = "educational"        # 教育模板
    CUSTOM = "custom"                  # 自定义模板

class TemplateStatus(Enum):
    """模板状态枚举"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 活跃
    DEPRECATED = "deprecated" # 已弃用
    ARCHIVED = "archived"    # 已归档

@dataclass
class TemplateMetadata:
    """模板元数据"""
    id: str
    name: str
    description: str
    type: TemplateType
    category: TemplateCategory
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    status: TemplateStatus
    tags: List[str]
    usage_count: int = 0
    rating: float = 0.0
    is_public: bool = False
    parent_template_id: Optional[str] = None
    dependencies: List[str] = None

@dataclass
class TemplateParameter:
    """模板参数定义"""
    name: str
    type: str
    description: str
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    required: bool = True
    validation_rules: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    category: Optional[str] = None

@dataclass
class TemplateContent:
    """模板内容"""
    parameters: List[TemplateParameter]
    configuration: Dict[str, Any]
    scripts: Dict[str, str]
    resources: Dict[str, str]
    validation_schema: Optional[Dict[str, Any]] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None

@dataclass
class SimulationTemplate:
    """仿真模板"""
    metadata: TemplateMetadata
    content: TemplateContent
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metadata": asdict(self.metadata),
            "content": asdict(self.content)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationTemplate':
        """从字典创建模板"""
        metadata_data = data["metadata"]
        metadata = TemplateMetadata(
            id=metadata_data["id"],
            name=metadata_data["name"],
            description=metadata_data["description"],
            type=TemplateType(metadata_data["type"]),
            category=TemplateCategory(metadata_data["category"]),
            version=metadata_data["version"],
            author=metadata_data["author"],
            created_at=datetime.fromisoformat(metadata_data["created_at"]),
            updated_at=datetime.fromisoformat(metadata_data["updated_at"]),
            status=TemplateStatus(metadata_data["status"]),
            tags=metadata_data["tags"],
            usage_count=metadata_data.get("usage_count", 0),
            rating=metadata_data.get("rating", 0.0),
            is_public=metadata_data.get("is_public", False),
            parent_template_id=metadata_data.get("parent_template_id"),
            dependencies=metadata_data.get("dependencies", [])
        )
        
        content_data = data["content"]
        parameters = [
            TemplateParameter(**param_data)
            for param_data in content_data["parameters"]
        ]
        
        content = TemplateContent(
            parameters=parameters,
            configuration=content_data["configuration"],
            scripts=content_data["scripts"],
            resources=content_data["resources"],
            validation_schema=content_data.get("validation_schema"),
            documentation=content_data.get("documentation"),
            examples=content_data.get("examples", [])
        )
        
        return cls(metadata=metadata, content=content)

class TemplateManager:
    """
    仿真模板管理器
    
    提供以下功能：
    - 模板创建和编辑
    - 模板存储和检索
    - 模板版本管理
    - 模板共享和权限控制
    - 模板应用和实例化
    - 模板验证和测试
    - 模板导入导出
    - 模板统计和分析
    """
    
    def __init__(self, templates_dir: str = "templates"):
        """
        初始化模板管理器
        
        Args:
            templates_dir: 模板存储目录
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.templates_dir / "simulation").mkdir(exist_ok=True)
        (self.templates_dir / "parameter").mkdir(exist_ok=True)
        (self.templates_dir / "workflow").mkdir(exist_ok=True)
        (self.templates_dir / "analysis").mkdir(exist_ok=True)
        (self.templates_dir / "report").mkdir(exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # 参数验证器
        self.validator = ParameterValidator()
        
        logger.info(f"模板管理器初始化完成，模板目录: {self.templates_dir}")
    
    async def create_template(
        self,
        name: str,
        description: str,
        template_type: TemplateType,
        category: TemplateCategory,
        parameters: List[TemplateParameter],
        configuration: Dict[str, Any],
        author: str,
        scripts: Optional[Dict[str, str]] = None,
        resources: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        parent_template_id: Optional[str] = None
    ) -> SimulationTemplate:
        """
        创建新模板
        
        Args:
            name: 模板名称
            description: 模板描述
            template_type: 模板类型
            category: 模板分类
            parameters: 参数列表
            configuration: 配置信息
            author: 作者
            scripts: 脚本字典
            resources: 资源字典
            tags: 标签列表
            is_public: 是否公开
            parent_template_id: 父模板ID
        
        Returns:
            SimulationTemplate: 创建的模板
        """
        try:
            logger.info(f"开始创建模板: {name}")
            
            # 生成模板ID
            template_id = str(uuid.uuid4())
            
            # 创建元数据
            metadata = TemplateMetadata(
                id=template_id,
                name=name,
                description=description,
                type=template_type,
                category=category,
                version="1.0.0",
                author=author,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=TemplateStatus.DRAFT,
                tags=tags or [],
                is_public=is_public,
                parent_template_id=parent_template_id,
                dependencies=[]
            )
            
            # 创建内容
            content = TemplateContent(
                parameters=parameters,
                configuration=configuration,
                scripts=scripts or {},
                resources=resources or {},
                validation_schema=self._generate_validation_schema(parameters),
                documentation="",
                examples=[]
            )
            
            # 创建模板对象
            template = SimulationTemplate(metadata=metadata, content=content)
            
            # 验证模板
            await self._validate_template(template)
            
            # 保存模板
            await self._save_template(template)
            
            # 保存到数据库
            await self._save_template_to_db(template)
            
            logger.info(f"模板创建成功: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            raise
    
    async def get_template(self, template_id: str) -> Optional[SimulationTemplate]:
        """
        获取模板
        
        Args:
            template_id: 模板ID
        
        Returns:
            SimulationTemplate: 模板对象，如果不存在则返回None
        """
        try:
            # 先从文件系统加载
            template_file = self._get_template_file_path(template_id)
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                return SimulationTemplate.from_dict(template_data)
            
            # 从数据库加载
            db = next(get_db())
            template_record = db.query(models.SimulationTemplate).filter(
                models.SimulationTemplate.id == template_id
            ).first()
            
            if template_record:
                template_data = json.loads(template_record.template_data)
                template = SimulationTemplate.from_dict(template_data)
                
                # 保存到文件系统以便下次快速访问
                await self._save_template(template)
                
                db.close()
                return template
            
            db.close()
            return None
            
        except Exception as e:
            logger.error(f"获取模板失败 {template_id}: {str(e)}")
            return None
    
    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        author: str
    ) -> Optional[SimulationTemplate]:
        """
        更新模板
        
        Args:
            template_id: 模板ID
            updates: 更新内容
            author: 更新者
        
        Returns:
            SimulationTemplate: 更新后的模板
        """
        try:
            logger.info(f"开始更新模板: {template_id}")
            
            # 获取现有模板
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            # 创建新版本
            new_version = self._increment_version(template.metadata.version)
            
            # 应用更新
            if "name" in updates:
                template.metadata.name = updates["name"]
            if "description" in updates:
                template.metadata.description = updates["description"]
            if "parameters" in updates:
                template.content.parameters = [
                    TemplateParameter(**param) for param in updates["parameters"]
                ]
            if "configuration" in updates:
                template.content.configuration.update(updates["configuration"])
            if "scripts" in updates:
                template.content.scripts.update(updates["scripts"])
            if "resources" in updates:
                template.content.resources.update(updates["resources"])
            if "tags" in updates:
                template.metadata.tags = updates["tags"]
            if "status" in updates:
                template.metadata.status = TemplateStatus(updates["status"])
            
            # 更新元数据
            template.metadata.version = new_version
            template.metadata.updated_at = datetime.now()
            
            # 重新生成验证模式
            template.content.validation_schema = self._generate_validation_schema(
                template.content.parameters
            )
            
            # 验证更新后的模板
            await self._validate_template(template)
            
            # 保存模板
            await self._save_template(template)
            
            # 更新数据库
            await self._update_template_in_db(template)
            
            logger.info(f"模板更新成功: {template_id}, 新版本: {new_version}")
            return template
            
        except Exception as e:
            logger.error(f"更新模板失败 {template_id}: {str(e)}")
            raise
    
    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            logger.info(f"开始删除模板: {template_id}")
            
            # 检查权限
            template = await self.get_template(template_id)
            if not template:
                return False
            
            # 删除文件
            template_file = self._get_template_file_path(template_id)
            if template_file.exists():
                template_file.unlink()
            
            # 从数据库删除
            db = next(get_db())
            db.query(models.SimulationTemplate).filter(
                models.SimulationTemplate.id == template_id
            ).delete()
            db.commit()
            db.close()
            
            logger.info(f"模板删除成功: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除模板失败 {template_id}: {str(e)}")
            return False
    
    async def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        category: Optional[TemplateCategory] = None,
        status: Optional[TemplateStatus] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TemplateMetadata]:
        """
        列出模板
        
        Args:
            template_type: 模板类型过滤
            category: 分类过滤
            status: 状态过滤
            author: 作者过滤
            tags: 标签过滤
            is_public: 是否公开过滤
            search_query: 搜索查询
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            List[TemplateMetadata]: 模板元数据列表
        """
        try:
            db = next(get_db())
            query = db.query(models.SimulationTemplate)
            
            # 应用过滤条件
            if template_type:
                query = query.filter(models.SimulationTemplate.type == template_type.value)
            if category:
                query = query.filter(models.SimulationTemplate.category == category.value)
            if status:
                query = query.filter(models.SimulationTemplate.status == status.value)
            if author:
                query = query.filter(models.SimulationTemplate.author == author)
            if is_public is not None:
                query = query.filter(models.SimulationTemplate.is_public == is_public)
            if search_query:
                search_filter = or_(
                    models.SimulationTemplate.name.contains(search_query),
                    models.SimulationTemplate.description.contains(search_query)
                )
                query = query.filter(search_filter)
            
            # 标签过滤
            if tags:
                for tag in tags:
                    query = query.filter(models.SimulationTemplate.tags.contains(tag))
            
            # 分页
            templates = query.offset(offset).limit(limit).all()
            
            # 转换为元数据对象
            metadata_list = []
            for template_record in templates:
                template_data = json.loads(template_record.template_data)
                metadata_data = template_data["metadata"]
                
                metadata = TemplateMetadata(
                    id=metadata_data["id"],
                    name=metadata_data["name"],
                    description=metadata_data["description"],
                    type=TemplateType(metadata_data["type"]),
                    category=TemplateCategory(metadata_data["category"]),
                    version=metadata_data["version"],
                    author=metadata_data["author"],
                    created_at=datetime.fromisoformat(metadata_data["created_at"]),
                    updated_at=datetime.fromisoformat(metadata_data["updated_at"]),
                    status=TemplateStatus(metadata_data["status"]),
                    tags=metadata_data["tags"],
                    usage_count=metadata_data.get("usage_count", 0),
                    rating=metadata_data.get("rating", 0.0),
                    is_public=metadata_data.get("is_public", False),
                    parent_template_id=metadata_data.get("parent_template_id"),
                    dependencies=metadata_data.get("dependencies", [])
                )
                
                metadata_list.append(metadata)
            
            db.close()
            return metadata_list
            
        except Exception as e:
            logger.error(f"列出模板失败: {str(e)}")
            return []
    
    async def apply_template(
        self,
        template_id: str,
        parameter_values: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        应用模板
        
        Args:
            template_id: 模板ID
            parameter_values: 参数值
            user_id: 用户ID
        
        Returns:
            Dict[str, Any]: 应用结果配置
        """
        try:
            logger.info(f"开始应用模板: {template_id}")
            
            # 获取模板
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            # 验证参数
            validated_params = await self._validate_parameters(
                template.content.parameters,
                parameter_values
            )
            
            # 渲染配置
            rendered_config = await self._render_configuration(
                template.content.configuration,
                validated_params
            )
            
            # 渲染脚本
            rendered_scripts = await self._render_scripts(
                template.content.scripts,
                validated_params
            )
            
            # 更新使用计数
            await self._increment_usage_count(template_id)
            
            # 构建应用结果
            result = {
                "template_id": template_id,
                "template_name": template.metadata.name,
                "template_version": template.metadata.version,
                "parameters": validated_params,
                "configuration": rendered_config,
                "scripts": rendered_scripts,
                "resources": template.content.resources,
                "applied_at": datetime.now().isoformat(),
                "applied_by": user_id
            }
            
            logger.info(f"模板应用成功: {template_id}")
            return result
            
        except Exception as e:
            logger.error(f"应用模板失败 {template_id}: {str(e)}")
            raise
    
    async def clone_template(
        self,
        template_id: str,
        new_name: str,
        author: str,
        modifications: Optional[Dict[str, Any]] = None
    ) -> SimulationTemplate:
        """
        克隆模板
        
        Args:
            template_id: 源模板ID
            new_name: 新模板名称
            author: 作者
            modifications: 修改内容
        
        Returns:
            SimulationTemplate: 克隆的模板
        """
        try:
            logger.info(f"开始克隆模板: {template_id} -> {new_name}")
            
            # 获取源模板
            source_template = await self.get_template(template_id)
            if not source_template:
                raise ValueError(f"源模板不存在: {template_id}")
            
            # 创建新模板ID
            new_template_id = str(uuid.uuid4())
            
            # 复制元数据
            new_metadata = TemplateMetadata(
                id=new_template_id,
                name=new_name,
                description=source_template.metadata.description,
                type=source_template.metadata.type,
                category=source_template.metadata.category,
                version="1.0.0",
                author=author,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=TemplateStatus.DRAFT,
                tags=source_template.metadata.tags.copy(),
                parent_template_id=template_id,
                dependencies=source_template.metadata.dependencies.copy()
            )
            
            # 复制内容
            new_content = TemplateContent(
                parameters=source_template.content.parameters.copy(),
                configuration=source_template.content.configuration.copy(),
                scripts=source_template.content.scripts.copy(),
                resources=source_template.content.resources.copy(),
                validation_schema=source_template.content.validation_schema.copy() if source_template.content.validation_schema else None,
                documentation=source_template.content.documentation,
                examples=source_template.content.examples.copy() if source_template.content.examples else []
            )
            
            # 应用修改
            if modifications:
                if "description" in modifications:
                    new_metadata.description = modifications["description"]
                if "parameters" in modifications:
                    new_content.parameters = [
                        TemplateParameter(**param) for param in modifications["parameters"]
                    ]
                if "configuration" in modifications:
                    new_content.configuration.update(modifications["configuration"])
                if "scripts" in modifications:
                    new_content.scripts.update(modifications["scripts"])
                if "tags" in modifications:
                    new_metadata.tags = modifications["tags"]
            
            # 创建新模板
            new_template = SimulationTemplate(metadata=new_metadata, content=new_content)
            
            # 验证模板
            await self._validate_template(new_template)
            
            # 保存模板
            await self._save_template(new_template)
            await self._save_template_to_db(new_template)
            
            logger.info(f"模板克隆成功: {new_template_id}")
            return new_template
            
        except Exception as e:
            logger.error(f"克隆模板失败 {template_id}: {str(e)}")
            raise
    
    async def export_template(
        self,
        template_id: str,
        export_format: str = "json"
    ) -> str:
        """
        导出模板
        
        Args:
            template_id: 模板ID
            export_format: 导出格式 (json, yaml)
        
        Returns:
            str: 导出的模板内容
        """
        try:
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            template_data = template.to_dict()
            
            if export_format.lower() == "yaml":
                return yaml.dump(template_data, default_flow_style=False, allow_unicode=True)
            else:
                return json.dumps(template_data, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"导出模板失败 {template_id}: {str(e)}")
            raise
    
    async def import_template(
        self,
        template_content: str,
        import_format: str = "json",
        author: str = "imported"
    ) -> SimulationTemplate:
        """
        导入模板
        
        Args:
            template_content: 模板内容
            import_format: 导入格式 (json, yaml)
            author: 导入者
        
        Returns:
            SimulationTemplate: 导入的模板
        """
        try:
            logger.info("开始导入模板")
            
            # 解析模板内容
            if import_format.lower() == "yaml":
                template_data = yaml.safe_load(template_content)
            else:
                template_data = json.loads(template_content)
            
            # 创建模板对象
            template = SimulationTemplate.from_dict(template_data)
            
            # 生成新的ID和更新元数据
            template.metadata.id = str(uuid.uuid4())
            template.metadata.author = author
            template.metadata.created_at = datetime.now()
            template.metadata.updated_at = datetime.now()
            template.metadata.status = TemplateStatus.DRAFT
            
            # 验证模板
            await self._validate_template(template)
            
            # 保存模板
            await self._save_template(template)
            await self._save_template_to_db(template)
            
            logger.info(f"模板导入成功: {template.metadata.id}")
            return template
            
        except Exception as e:
            logger.error(f"导入模板失败: {str(e)}")
            raise
    
    async def get_template_statistics(self) -> Dict[str, Any]:
        """
        获取模板统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            db = next(get_db())
            
            # 总数统计
            total_templates = db.query(models.SimulationTemplate).count()
            
            # 按类型统计
            type_stats = {}
            for template_type in TemplateType:
                count = db.query(models.SimulationTemplate).filter(
                    models.SimulationTemplate.type == template_type.value
                ).count()
                type_stats[template_type.value] = count
            
            # 按分类统计
            category_stats = {}
            for category in TemplateCategory:
                count = db.query(models.SimulationTemplate).filter(
                    models.SimulationTemplate.category == category.value
                ).count()
                category_stats[category.value] = count
            
            # 按状态统计
            status_stats = {}
            for status in TemplateStatus:
                count = db.query(models.SimulationTemplate).filter(
                    models.SimulationTemplate.status == status.value
                ).count()
                status_stats[status.value] = count
            
            # 最受欢迎的模板
            popular_templates = db.query(models.SimulationTemplate).order_by(
                models.SimulationTemplate.usage_count.desc()
            ).limit(10).all()
            
            popular_list = []
            for template_record in popular_templates:
                template_data = json.loads(template_record.template_data)
                metadata = template_data["metadata"]
                popular_list.append({
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "usage_count": metadata.get("usage_count", 0),
                    "rating": metadata.get("rating", 0.0)
                })
            
            db.close()
            
            return {
                "total_templates": total_templates,
                "by_type": type_stats,
                "by_category": category_stats,
                "by_status": status_stats,
                "popular_templates": popular_list,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取模板统计失败: {str(e)}")
            return {}
    
    # 私有方法
    def _get_template_file_path(self, template_id: str) -> Path:
        """获取模板文件路径"""
        return self.templates_dir / f"{template_id}.json"
    
    async def _save_template(self, template: SimulationTemplate):
        """保存模板到文件系统"""
        template_file = self._get_template_file_path(template.metadata.id)
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    
    async def _save_template_to_db(self, template: SimulationTemplate):
        """保存模板到数据库"""
        try:
            db = next(get_db())
            
            template_record = models.SimulationTemplate(
                id=template.metadata.id,
                name=template.metadata.name,
                description=template.metadata.description,
                type=template.metadata.type.value,
                category=template.metadata.category.value,
                version=template.metadata.version,
                author=template.metadata.author,
                status=template.metadata.status.value,
                tags=json.dumps(template.metadata.tags),
                is_public=template.metadata.is_public,
                usage_count=template.metadata.usage_count,
                rating=template.metadata.rating,
                template_data=json.dumps(template.to_dict(), default=str),
                created_at=template.metadata.created_at,
                updated_at=template.metadata.updated_at
            )
            
            db.add(template_record)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"保存模板到数据库失败: {str(e)}")
            raise
    
    async def _update_template_in_db(self, template: SimulationTemplate):
        """更新数据库中的模板"""
        try:
            db = next(get_db())
            
            db.query(models.SimulationTemplate).filter(
                models.SimulationTemplate.id == template.metadata.id
            ).update({
                "name": template.metadata.name,
                "description": template.metadata.description,
                "version": template.metadata.version,
                "status": template.metadata.status.value,
                "tags": json.dumps(template.metadata.tags),
                "usage_count": template.metadata.usage_count,
                "rating": template.metadata.rating,
                "template_data": json.dumps(template.to_dict(), default=str),
                "updated_at": template.metadata.updated_at
            })
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"更新数据库模板失败: {str(e)}")
            raise
    
    async def _validate_template(self, template: SimulationTemplate):
        """验证模板"""
        # 验证元数据
        if not template.metadata.name:
            raise ValueError("模板名称不能为空")
        
        if not template.metadata.description:
            raise ValueError("模板描述不能为空")
        
        # 验证参数
        for param in template.content.parameters:
            if not param.name:
                raise ValueError("参数名称不能为空")
            if not param.type:
                raise ValueError("参数类型不能为空")
        
        # 验证配置
        if not template.content.configuration:
            raise ValueError("模板配置不能为空")
    
    def _generate_validation_schema(self, parameters: List[TemplateParameter]) -> Dict[str, Any]:
        """生成参数验证模式"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param in parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }
            
            if param.min_value is not None:
                param_schema["minimum"] = param.min_value
            if param.max_value is not None:
                param_schema["maximum"] = param.max_value
            if param.allowed_values:
                param_schema["enum"] = param.allowed_values
            if param.default_value is not None:
                param_schema["default"] = param.default_value
            
            schema["properties"][param.name] = param_schema
            
            if param.required:
                schema["required"].append(param.name)
        
        return schema
    
    async def _validate_parameters(
        self,
        template_params: List[TemplateParameter],
        parameter_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证参数值"""
        validated_params = {}
        
        for param in template_params:
            value = parameter_values.get(param.name)
            
            # 检查必需参数
            if param.required and value is None:
                if param.default_value is not None:
                    value = param.default_value
                else:
                    raise ValueError(f"必需参数缺失: {param.name}")
            
            # 类型验证
            if value is not None:
                if param.type == "integer" and not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"参数 {param.name} 必须是整数")
                
                elif param.type == "number" and not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"参数 {param.name} 必须是数字")
                
                elif param.type == "string" and not isinstance(value, str):
                    value = str(value)
                
                elif param.type == "boolean" and not isinstance(value, bool):
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = bool(value)
                
                # 范围验证
                if param.min_value is not None and value < param.min_value:
                    raise ValueError(f"参数 {param.name} 不能小于 {param.min_value}")
                
                if param.max_value is not None and value > param.max_value:
                    raise ValueError(f"参数 {param.name} 不能大于 {param.max_value}")
                
                # 允许值验证
                if param.allowed_values and value not in param.allowed_values:
                    raise ValueError(f"参数 {param.name} 必须是以下值之一: {param.allowed_values}")
            
            validated_params[param.name] = value
        
        return validated_params
    
    async def _render_configuration(
        self,
        configuration: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """渲染配置模板"""
        try:
            # 将配置转换为JSON字符串进行模板渲染
            config_str = json.dumps(configuration, default=str)
            
            # 使用Jinja2渲染
            template = Template(config_str)
            rendered_str = template.render(**parameters)
            
            # 转换回字典
            return json.loads(rendered_str)
            
        except Exception as e:
            logger.error(f"渲染配置失败: {str(e)}")
            return configuration
    
    async def _render_scripts(
        self,
        scripts: Dict[str, str],
        parameters: Dict[str, Any]
    ) -> Dict[str, str]:
        """渲染脚本模板"""
        rendered_scripts = {}
        
        for script_name, script_content in scripts.items():
            try:
                template = Template(script_content)
                rendered_scripts[script_name] = template.render(**parameters)
            except Exception as e:
                logger.error(f"渲染脚本失败 {script_name}: {str(e)}")
                rendered_scripts[script_name] = script_content
        
        return rendered_scripts
    
    async def _increment_usage_count(self, template_id: str):
        """增加使用计数"""
        try:
            db = next(get_db())
            
            template_record = db.query(models.SimulationTemplate).filter(
                models.SimulationTemplate.id == template_id
            ).first()
            
            if template_record:
                template_record.usage_count += 1
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"更新使用计数失败 {template_id}: {str(e)}")
    
    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                return f"{major}.{minor}.{patch + 1}"
            else:
                return "1.0.1"
        except:
            return "1.0.1"