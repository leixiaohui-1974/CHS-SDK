#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK完整知识库构建器

该脚本用于系统性地扫描和索引整个CHS-SDK项目，
生成全面的知识库，为智能体开发提供增强检索支持。
"""

import os
import sys
import json
import yaml
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_lib.knowledge.knowledge_base import KnowledgeBase
from core_lib.knowledge.knowledge_indexer import KnowledgeIndexer

class ComprehensiveKnowledgeBuilder:
    """完整知识库构建器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.knowledge_base_dir = self.project_root / "knowledge_base"
        self.knowledge_base_dir.mkdir(exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.knowledge_base_dir / "build.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化知识库组件
        self.knowledge_base = None
        self.indexer = None
        
        # 扫描统计
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "categories": {},
            "start_time": None,
            "end_time": None
        }
        
        # 文件类型分类
        self.file_categories = {
            "python": [".py"],
            "yaml": [".yml", ".yaml"],
            "json": [".json"],
            "markdown": [".md"],
            "text": [".txt", ".rst"],
            "config": [".cfg", ".ini", ".conf"],
            "docker": ["Dockerfile", ".dockerignore"],
            "shell": [".sh", ".bat", ".ps1"],
            "web": [".html", ".css", ".js", ".ts", ".tsx", ".vue"]
        }
        
        # 忽略的目录和文件
        self.ignore_patterns = {
            "directories": {
                ".git", ".github", "__pycache__", ".pytest_cache",
                "node_modules", ".vscode", ".idea", "dist", "build",
                ".chs_cache", "logs", "output", "plots", "uploads"
            },
            "files": {
                ".gitignore", ".env", ".env.example", ".env.production",
                "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll",
                "*.log", "*.db", "*.sqlite", "*.sqlite3"
            }
        }
    
    async def initialize_knowledge_base(self):
        """初始化知识库"""
        try:
            # 创建知识库配置
            config = {
                "storage": {
                    "type": "file",
                    "path": str(self.knowledge_base_dir / "data")
                },
                "indexing": {
                    "enabled": True,
                    "batch_size": 100,
                    "max_file_size": 10 * 1024 * 1024  # 10MB
                },
                "semantic_search": {
                    "enabled": True,
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            }
            
            # 保存配置
            config_path = self.knowledge_base_dir / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 初始化知识库
            self.knowledge_base = KnowledgeBase(str(self.project_root), config)
            self.indexer = KnowledgeIndexer(str(self.project_root), config)
            
            self.logger.info("知识库初始化完成")
            
        except Exception as e:
            self.logger.error(f"知识库初始化失败: {e}")
            raise
    
    def should_ignore(self, path: Path) -> bool:
        """检查是否应该忽略该路径"""
        # 检查目录
        if path.is_dir():
            return path.name in self.ignore_patterns["directories"]
        
        # 检查文件
        if path.name in self.ignore_patterns["files"]:
            return True
        
        # 检查文件扩展名
        for pattern in self.ignore_patterns["files"]:
            if pattern.startswith("*") and path.name.endswith(pattern[1:]):
                return True
        
        return False
    
    def categorize_file(self, file_path: Path) -> str:
        """对文件进行分类"""
        suffix = file_path.suffix.lower()
        name = file_path.name
        
        for category, extensions in self.file_categories.items():
            if suffix in extensions or name in extensions:
                return category
        
        return "other"
    
    def scan_project_files(self) -> List[Path]:
        """扫描项目文件"""
        files = []
        
        def scan_directory(directory: Path):
            try:
                for item in directory.iterdir():
                    if self.should_ignore(item):
                        continue
                    
                    if item.is_file():
                        files.append(item)
                        self.stats["total_files"] += 1
                        
                        # 统计文件类型
                        category = self.categorize_file(item)
                        self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
                        
                    elif item.is_dir():
                        scan_directory(item)
                        
            except PermissionError:
                self.logger.warning(f"无权限访问目录: {directory}")
            except Exception as e:
                self.logger.error(f"扫描目录失败 {directory}: {e}")
        
        self.logger.info("开始扫描项目文件...")
        scan_directory(self.project_root)
        self.logger.info(f"扫描完成，共发现 {self.stats['total_files']} 个文件")
        
        return files
    
    async def process_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        try:
            # 检查文件大小
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                self.logger.warning(f"文件过大，跳过: {file_path}")
                return False
            
            # 使用索引器处理文件
            await self.indexer.index_file(str(file_path))
            
            self.stats["processed_files"] += 1
            
            if self.stats["processed_files"] % 50 == 0:
                self.logger.info(f"已处理 {self.stats['processed_files']} / {self.stats['total_files']} 个文件")
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理文件失败 {file_path}: {e}")
            self.stats["failed_files"] += 1
            return False
    
    async def build_knowledge_base(self):
        """构建完整知识库"""
        self.stats["start_time"] = datetime.now()
        
        try:
            # 初始化知识库
            await self.initialize_knowledge_base()
            
            # 扫描项目文件
            files = self.scan_project_files()
            
            # 处理文件
            self.logger.info("开始处理文件...")
            
            # 批量处理文件
            batch_size = 10
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                tasks = [self.process_file(file_path) for file_path in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # 构建索引
            self.logger.info("构建知识库索引...")
            await self.indexer.build_index()
            
            self.stats["end_time"] = datetime.now()
            
            # 保存统计信息
            await self.save_build_stats()
            
            self.logger.info("知识库构建完成！")
            
        except Exception as e:
            self.logger.error(f"知识库构建失败: {e}")
            raise
    
    async def save_build_stats(self):
        """保存构建统计信息"""
        try:
            duration = self.stats["end_time"] - self.stats["start_time"]
            
            stats_report = {
                "build_info": {
                    "start_time": self.stats["start_time"].isoformat(),
                    "end_time": self.stats["end_time"].isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "project_root": str(self.project_root)
                },
                "file_statistics": {
                    "total_files": self.stats["total_files"],
                    "processed_files": self.stats["processed_files"],
                    "failed_files": self.stats["failed_files"],
                    "success_rate": (self.stats["processed_files"] / self.stats["total_files"]) * 100 if self.stats["total_files"] > 0 else 0
                },
                "file_categories": self.stats["categories"]
            }
            
            # 保存统计报告
            stats_path = self.knowledge_base_dir / "build_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats_report, f, indent=2, ensure_ascii=False)
            
            # 打印摘要
            self.print_build_summary(stats_report)
            
        except Exception as e:
            self.logger.error(f"保存统计信息失败: {e}")
    
    def print_build_summary(self, stats: Dict[str, Any]):
        """打印构建摘要"""
        print("\n" + "="*60)
        print("CHS-SDK 知识库构建完成")
        print("="*60)
        print(f"项目路径: {stats['build_info']['project_root']}")
        print(f"构建时间: {stats['build_info']['duration_seconds']:.2f} 秒")
        print(f"总文件数: {stats['file_statistics']['total_files']}")
        print(f"成功处理: {stats['file_statistics']['processed_files']}")
        print(f"处理失败: {stats['file_statistics']['failed_files']}")
        print(f"成功率: {stats['file_statistics']['success_rate']:.2f}%")
        print("\n文件类型分布:")
        for category, count in stats['file_categories'].items():
            print(f"  {category}: {count} 个文件")
        print("="*60)

async def main():
    """主函数"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    builder = ComprehensiveKnowledgeBuilder(project_root)
    
    try:
        await builder.build_knowledge_base()
        print("\n知识库构建成功！可以开始使用增强检索功能。")
        
    except Exception as e:
        print(f"\n知识库构建失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())