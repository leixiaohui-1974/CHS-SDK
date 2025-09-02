# -*- coding: utf-8 -*-
"""
Knowledge Indexer for CHS-SDK Knowledge Base
知识索引器模块

Scans project files and builds searchable knowledge index
for agents, configurations, documentation, and code examples.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from datetime import datetime
import re
import ast
import yaml


class KnowledgeIndexer:
    """
    知识索引器
    
    扫描CHS-SDK项目文件，提取智能体定义、配置模式、
    API文档等信息，构建可搜索的知识库索引。
    """
    
    def __init__(self, project_root: Path, config: Dict[str, Any], semantic_search=None):
        """
        初始化知识索引器
        
        Args:
            project_root: 项目根目录
            config: 配置参数
            semantic_search: 语义搜索引擎实例
        """
        self.project_root = Path(project_root)
        self.config = config
        self.logger = logging.getLogger("CHS-SDK.KnowledgeIndexer")
        
        # 语义搜索引擎
        self.semantic_search = semantic_search
        
        # 配置参数
        self.supported_file_types = config.get("supported_file_types", [".py", ".yml", ".yaml", ".md", ".txt"])
        self.exclude_dirs = config.get("exclude_dirs", ["__pycache__", ".git", "node_modules", "venv"])
        self.batch_size = config.get("index_batch_size", 100)
        
        # 特定路径
        self.agent_registry_path = self.project_root / config.get("agent_registry_path", "core_lib")
        self.config_templates_path = self.project_root / config.get("config_templates_path", "scenarios/templates")
        self.documentation_path = self.project_root / config.get("documentation_path", "docs")
        
        # 索引数据
        self.indexed_files = {}
        self.agent_definitions = {}
        self.config_schemas = {}
        self.documentation_index = {}
        self.code_examples = {}
        
        # 文件变更追踪
        self.file_hashes = {}
        self.last_scan_time = None
        
        # 存储路径
        self.kb_path = self.project_root / "knowledge_base"
        self.kb_path.mkdir(exist_ok=True)
        
        self.index_metadata_file = self.kb_path / "index_metadata.json"
        self.file_hashes_file = self.kb_path / "file_hashes.json"
    
    async def build_index(self, force_rebuild: bool = False) -> bool:
        """
        构建知识库索引
        
        Args:
            force_rebuild: 是否强制重建索引
            
        Returns:
            bool: 构建是否成功
        """
        try:
            self.logger.info("Starting knowledge index build...")
            
            # 加载现有文件哈希
            if not force_rebuild:
                await self._load_file_hashes()
            
            # 扫描项目文件
            changed_files = await self._scan_project_files()
            
            if not changed_files and not force_rebuild:
                self.logger.info("No file changes detected, skipping index rebuild")
                return True
            
            self.logger.info(f"Processing {len(changed_files)} changed files...")
            
            # 处理变更的文件
            documents = []
            for file_path in changed_files:
                file_documents = await self._process_file(file_path)
                documents.extend(file_documents)
            
            # 保存索引元数据
            await self._save_index_metadata(documents)
            
            # 将文档添加到语义搜索引擎
            if self.semantic_search and documents:
                await self._add_documents_to_search_engine(documents)
            
            # 保存文件哈希
            await self._save_file_hashes()
            
            self.last_scan_time = datetime.now()
            
            self.logger.info(f"Knowledge index build completed. Processed {len(documents)} documents.")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to build knowledge index: {str(e)}")
            return False
    
    async def update_index(self, incremental: bool = True) -> bool:
        """
        更新知识库索引
        
        Args:
            incremental: 是否增量更新
            
        Returns:
            bool: 更新是否成功
        """
        return await self.build_index(force_rebuild=not incremental)
    
    async def index_file(self, file_path: Path) -> bool:
        """
        索引单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 索引是否成功
        """
        try:
            self.logger.debug(f"Indexing file: {file_path}")
            
            # 检查文件是否存在
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            # 检查文件类型
            if file_path.suffix not in self.supported_file_types:
                self.logger.debug(f"Unsupported file type: {file_path.suffix}")
                return False
            
            # 处理文件
            documents = await self._process_file(file_path)
            
            if documents:
                # 保存索引元数据
                await self._save_index_metadata(documents)
                
                # 将文档添加到语义搜索引擎
                if self.semantic_search:
                    await self._add_documents_to_search_engine(documents)
                
                # 更新文件哈希
                relative_path = file_path.relative_to(self.project_root)
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                self.file_hashes[str(relative_path)] = file_hash
                
                await self._save_file_hashes()
                
                self.logger.debug(f"Successfully indexed file: {file_path}")
                return True
            else:
                self.logger.debug(f"No documents extracted from file: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to index file {file_path}: {str(e)}")
            return False
    
    async def _scan_project_files(self) -> List[Path]:
        """扫描项目文件，返回变更的文件列表"""
        changed_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # 检查文件类型
                if file_path.suffix not in self.supported_file_types:
                    continue
                
                # 检查文件是否变更
                if await self._is_file_changed(file_path):
                    changed_files.append(file_path)
        
        return changed_files
    
    async def _is_file_changed(self, file_path: Path) -> bool:
        """检查文件是否变更"""
        try:
            # 计算文件哈希
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # 检查是否与之前的哈希不同
            file_key = str(file_path.relative_to(self.project_root))
            if file_key in self.file_hashes:
                return self.file_hashes[file_key] != file_hash
            
            # 新文件
            self.file_hashes[file_key] = file_hash
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to check file hash for {file_path}: {str(e)}")
            return True  # 出错时假设文件已变更
    
    async def _process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理单个文件，提取知识信息"""
        documents = []
        
        try:
            file_suffix = file_path.suffix.lower()
            relative_path = file_path.relative_to(self.project_root)
            
            if file_suffix == ".py":
                documents.extend(await self._process_python_file(file_path, relative_path))
            elif file_suffix in [".yml", ".yaml"]:
                documents.extend(await self._process_yaml_file(file_path, relative_path))
            elif file_suffix == ".md":
                documents.extend(await self._process_markdown_file(file_path, relative_path))
            elif file_suffix == ".txt":
                documents.extend(await self._process_text_file(file_path, relative_path))
            
        except Exception as e:
            self.logger.warning(f"Failed to process file {file_path}: {str(e)}")
        
        return documents
    
    async def _process_python_file(self, file_path: Path, relative_path: Path) -> List[Dict[str, Any]]:
        """处理Python文件，提取智能体定义和API信息"""
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            tree = ast.parse(content)
            
            # 提取类定义（可能是智能体）
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = await self._extract_class_info(node, content, file_path, relative_path)
                    if class_info:
                        documents.append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = await self._extract_function_info(node, content, file_path, relative_path)
                    if func_info:
                        documents.append(func_info)
            
            # 提取模块级文档
            module_doc = ast.get_docstring(tree)
            if module_doc:
                doc_info = {
                    'content': module_doc,
                    'title': f"Module: {relative_path.stem}",
                    'doc_type': 'module_documentation',
                    'file_path': str(relative_path),
                    'tags': ['python', 'module', 'documentation'],
                    'metadata': {
                        'file_type': 'python',
                        'module_name': relative_path.stem,
                        'package': str(relative_path.parent).replace('/', '.').replace('\\', '.')
                    }
                }
                documents.append(doc_info)
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in Python file {file_path}: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Failed to process Python file {file_path}: {str(e)}")
        
        return documents
    
    async def _extract_class_info(self, node: ast.ClassDef, content: str, file_path: Path, relative_path: Path) -> Optional[Dict[str, Any]]:
        """提取类信息（特别是智能体类）"""
        class_name = node.name
        docstring = ast.get_docstring(node)
        
        # 检查是否是智能体类
        is_agent = self._is_agent_class(node, class_name)
        
        # 提取构造函数参数
        init_params = self._extract_init_params(node)
        
        # 提取基类
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)
        
        # 构建文档
        content_parts = []
        if docstring:
            content_parts.append(f"类文档: {docstring}")
        
        content_parts.append(f"类名: {class_name}")
        
        if base_classes:
            content_parts.append(f"继承自: {', '.join(base_classes)}")
        
        if init_params:
            content_parts.append(f"构造参数: {', '.join(init_params)}")
        
        # 提取方法信息
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = ast.get_docstring(item)
                methods.append({
                    'name': item.name,
                    'docstring': method_doc,
                    'args': [arg.arg for arg in item.args.args]
                })
        
        if methods:
            method_info = [f"{m['name']}({', '.join(m['args'])})" for m in methods]
            content_parts.append(f"方法: {', '.join(method_info)}")
        
        doc_type = 'agent_definition' if is_agent else 'class_definition'
        tags = ['python', 'class']
        if is_agent:
            tags.extend(['agent', 'chs-sdk'])
        
        return {
            'content': '\n'.join(content_parts),
            'title': f"{'Agent' if is_agent else 'Class'}: {class_name}",
            'doc_type': doc_type,
            'file_path': str(relative_path),
            'tags': tags,
            'metadata': {
                'file_type': 'python',
                'class_name': class_name,
                'is_agent': is_agent,
                'base_classes': base_classes,
                'init_params': init_params,
                'methods': methods,
                'line_number': node.lineno
            }
        }
    
    async def _extract_function_info(self, node: ast.FunctionDef, content: str, file_path: Path, relative_path: Path) -> Optional[Dict[str, Any]]:
        """提取函数信息"""
        func_name = node.name
        docstring = ast.get_docstring(node)
        
        if not docstring or func_name.startswith('_'):  # 跳过私有函数和无文档函数
            return None
        
        # 提取参数信息
        args = [arg.arg for arg in node.args.args]
        
        content_parts = [
            f"函数文档: {docstring}",
            f"函数名: {func_name}",
            f"参数: {', '.join(args)}"
        ]
        
        return {
            'content': '\n'.join(content_parts),
            'title': f"Function: {func_name}",
            'doc_type': 'function_definition',
            'file_path': str(relative_path),
            'tags': ['python', 'function', 'api'],
            'metadata': {
                'file_type': 'python',
                'function_name': func_name,
                'args': args,
                'line_number': node.lineno
            }
        }
    
    def _is_agent_class(self, node: ast.ClassDef, class_name: str) -> bool:
        """判断是否是智能体类"""
        # 基于类名判断
        if 'agent' in class_name.lower():
            return True
        
        # 基于基类判断
        for base in node.bases:
            if isinstance(base, ast.Name) and 'agent' in base.id.lower():
                return True
            elif isinstance(base, ast.Attribute) and 'agent' in base.attr.lower():
                return True
        
        return False
    
    def _extract_init_params(self, node: ast.ClassDef) -> List[str]:
        """提取构造函数参数"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                return [arg.arg for arg in item.args.args if arg.arg != 'self']
        return []
    
    async def _process_yaml_file(self, file_path: Path, relative_path: Path) -> List[Dict[str, Any]]:
        """处理YAML配置文件"""
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            if not yaml_content:
                return documents
            
            # 判断YAML文件类型
            doc_type = self._determine_yaml_type(yaml_content, relative_path)
            
            # 提取配置信息
            content_parts = []
            
            if isinstance(yaml_content, dict):
                # 提取主要配置项
                for key, value in yaml_content.items():
                    if isinstance(value, (str, int, float, bool)):
                        content_parts.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        content_parts.append(f"{key}: [{len(value)} items]")
                    elif isinstance(value, dict):
                        content_parts.append(f"{key}: {{{len(value)} properties}}")
            
            # 特殊处理智能体配置
            if doc_type == 'agent_configuration':
                agent_info = self._extract_agent_config_info(yaml_content)
                if agent_info:
                    content_parts.extend(agent_info)
            
            # 特殊处理场景配置
            elif doc_type == 'scenario_configuration':
                scenario_info = self._extract_scenario_config_info(yaml_content)
                if scenario_info:
                    content_parts.extend(scenario_info)
            
            tags = ['yaml', 'configuration']
            if 'agent' in str(relative_path).lower():
                tags.append('agent')
            if 'scenario' in str(relative_path).lower():
                tags.append('scenario')
            
            document = {
                'content': '\n'.join(content_parts),
                'title': f"Config: {relative_path.stem}",
                'doc_type': doc_type,
                'file_path': str(relative_path),
                'tags': tags,
                'metadata': {
                    'file_type': 'yaml',
                    'config_name': relative_path.stem,
                    'config_structure': self._analyze_yaml_structure(yaml_content)
                }
            }
            documents.append(document)
            
        except yaml.YAMLError as e:
            self.logger.warning(f"YAML parsing error in {file_path}: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Failed to process YAML file {file_path}: {str(e)}")
        
        return documents
    
    def _determine_yaml_type(self, yaml_content: Any, relative_path: Path) -> str:
        """确定YAML文件类型"""
        path_str = str(relative_path).lower()
        
        if 'agent' in path_str:
            return 'agent_configuration'
        elif 'scenario' in path_str:
            return 'scenario_configuration'
        elif 'template' in path_str:
            return 'template_configuration'
        elif isinstance(yaml_content, dict):
            # 基于内容判断
            if 'agents' in yaml_content or any('agent' in str(k).lower() for k in yaml_content.keys()):
                return 'agent_configuration'
            elif 'scenario' in yaml_content or 'scenarios' in yaml_content:
                return 'scenario_configuration'
        
        return 'general_configuration'
    
    def _extract_agent_config_info(self, yaml_content: Dict) -> List[str]:
        """提取智能体配置信息"""
        info = []
        
        if 'agents' in yaml_content:
            agents = yaml_content['agents']
            if isinstance(agents, dict):
                for agent_name, agent_config in agents.items():
                    info.append(f"智能体: {agent_name}")
                    if isinstance(agent_config, dict):
                        if 'type' in agent_config:
                            info.append(f"  类型: {agent_config['type']}")
                        if 'parameters' in agent_config:
                            params = agent_config['parameters']
                            if isinstance(params, dict):
                                info.append(f"  参数: {', '.join(params.keys())}")
        
        return info
    
    def _extract_scenario_config_info(self, yaml_content: Dict) -> List[str]:
        """提取场景配置信息"""
        info = []
        
        if 'scenario' in yaml_content:
            scenario = yaml_content['scenario']
            if isinstance(scenario, dict):
                if 'name' in scenario:
                    info.append(f"场景名称: {scenario['name']}")
                if 'description' in scenario:
                    info.append(f"场景描述: {scenario['description']}")
                if 'agents' in scenario:
                    agents = scenario['agents']
                    if isinstance(agents, list):
                        info.append(f"包含智能体: {', '.join(agents)}")
        
        return info
    
    def _analyze_yaml_structure(self, yaml_content: Any) -> Dict[str, Any]:
        """分析YAML结构"""
        if isinstance(yaml_content, dict):
            return {
                'type': 'object',
                'keys': list(yaml_content.keys()),
                'depth': self._calculate_dict_depth(yaml_content)
            }
        elif isinstance(yaml_content, list):
            return {
                'type': 'array',
                'length': len(yaml_content),
                'item_types': list(set(type(item).__name__ for item in yaml_content))
            }
        else:
            return {
                'type': type(yaml_content).__name__,
                'value': str(yaml_content)[:100]  # 限制长度
            }
    
    def _calculate_dict_depth(self, d: Dict, current_depth: int = 1) -> int:
        """计算字典嵌套深度"""
        if not isinstance(d, dict) or not d:
            return current_depth
        
        max_depth = current_depth
        for value in d.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    async def _process_markdown_file(self, file_path: Path, relative_path: Path) -> List[Dict[str, Any]]:
        """处理Markdown文档文件"""
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题和章节
            sections = self._extract_markdown_sections(content)
            
            for section in sections:
                document = {
                    'content': section['content'],
                    'title': section['title'] or f"Documentation: {relative_path.stem}",
                    'doc_type': 'documentation',
                    'file_path': str(relative_path),
                    'tags': ['markdown', 'documentation'],
                    'metadata': {
                        'file_type': 'markdown',
                        'section_level': section['level'],
                        'section_title': section['title']
                    }
                }
                documents.append(document)
            
        except Exception as e:
            self.logger.warning(f"Failed to process Markdown file {file_path}: {str(e)}")
        
        return documents
    
    def _extract_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """提取Markdown章节"""
        sections = []
        lines = content.split('\n')
        
        current_section = {'title': None, 'content': [], 'level': 0}
        
        for line in lines:
            # 检查是否是标题
            if line.startswith('#'):
                # 保存当前章节
                if current_section['content']:
                    current_section['content'] = '\n'.join(current_section['content']).strip()
                    if current_section['content']:
                        sections.append(current_section.copy())
                
                # 开始新章节
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = {
                    'title': title,
                    'content': [],
                    'level': level
                }
            else:
                current_section['content'].append(line)
        
        # 添加最后一个章节
        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content']).strip()
            if current_section['content']:
                sections.append(current_section)
        
        return sections
    
    async def _process_text_file(self, file_path: Path, relative_path: Path) -> List[Dict[str, Any]]:
        """处理文本文件"""
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content:
                document = {
                    'content': content,
                    'title': f"Text: {relative_path.stem}",
                    'doc_type': 'text_document',
                    'file_path': str(relative_path),
                    'tags': ['text', 'document'],
                    'metadata': {
                        'file_type': 'text',
                        'file_size': len(content),
                        'line_count': len(content.split('\n'))
                    }
                }
                documents.append(document)
            
        except Exception as e:
            self.logger.warning(f"Failed to process text file {file_path}: {str(e)}")
        
        return documents
    
    async def _save_index_metadata(self, documents: List[Dict[str, Any]]):
        """保存索引元数据"""
        try:
            metadata = {
                'last_indexed': datetime.now().isoformat(),
                'total_documents': len(documents),
                'document_types': {},
                'file_types': {},
                'tags': set()
            }
            
            # 统计文档类型和标签
            for doc in documents:
                doc_type = doc.get('doc_type', 'unknown')
                metadata['document_types'][doc_type] = metadata['document_types'].get(doc_type, 0) + 1
                
                file_type = doc.get('metadata', {}).get('file_type', 'unknown')
                metadata['file_types'][file_type] = metadata['file_types'].get(file_type, 0) + 1
                
                tags = doc.get('tags', [])
                metadata['tags'].update(tags)
            
            # 转换set为list以便JSON序列化
            metadata['tags'] = list(metadata['tags'])
            
            with open(self.index_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Saved index metadata: {len(documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to save index metadata: {str(e)}")
    
    async def _load_file_hashes(self):
        """加载文件哈希"""
        if self.file_hashes_file.exists():
            try:
                with open(self.file_hashes_file, 'r', encoding='utf-8') as f:
                    self.file_hashes = json.load(f)
                self.logger.debug(f"Loaded {len(self.file_hashes)} file hashes")
            except Exception as e:
                self.logger.warning(f"Failed to load file hashes: {str(e)}")
                self.file_hashes = {}
        else:
            self.file_hashes = {}
    
    async def _save_file_hashes(self):
        """保存文件哈希"""
        try:
            with open(self.file_hashes_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_hashes, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved {len(self.file_hashes)} file hashes")
        except Exception as e:
            self.logger.error(f"Failed to save file hashes: {str(e)}")
    
    async def _add_documents_to_search_engine(self, documents: List[Dict[str, Any]]):
        """将文档添加到语义搜索引擎"""
        try:
            if not self.semantic_search:
                return
            
            # 转换文档格式以匹配语义搜索引擎的期望格式
            formatted_docs = []
            for doc in documents:
                formatted_doc = {
                    'content': doc['content'],
                    'title': doc['title'],
                    'doc_type': doc['doc_type'],
                    'file_path': doc['file_path'],
                    'tags': doc['tags'],
                    'metadata': doc.get('metadata', {})
                }
                formatted_docs.append(formatted_doc)
            
            # 批量添加文档到搜索引擎
            await self.semantic_search.add_documents(formatted_docs)
            
            self.logger.debug(f"Added {len(documents)} documents to semantic search engine")
            
        except Exception as e:
            self.logger.error(f"Failed to add documents to search engine: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引器统计信息"""
        stats = {
            'project_root': str(self.project_root),
            'supported_file_types': self.supported_file_types,
            'exclude_dirs': self.exclude_dirs,
            'tracked_files': len(self.file_hashes),
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None
        }
        
        # 加载索引元数据
        if self.index_metadata_file.exists():
            try:
                with open(self.index_metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                stats.update(metadata)
            except Exception:
                pass
        
        return stats
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up knowledge indexer...")
        
        # 保存当前状态
        await self._save_file_hashes()
        
        # 清理内存
        self.indexed_files.clear()
        self.agent_definitions.clear()
        self.config_schemas.clear()
        self.documentation_index.clear()
        self.code_examples.clear()
        self.file_hashes.clear()