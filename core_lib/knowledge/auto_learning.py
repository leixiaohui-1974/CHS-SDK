#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 知识库自动学习系统

该模块实现了自动监控项目代码变更并更新知识库的功能，包括：
- 文件系统监控
- 代码变更检测
- 增量索引更新
- 智能学习机制
- 版本控制集成
"""

import os
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
import git
import yaml
import logging
from concurrent.futures import ThreadPoolExecutor

from .knowledge_indexer import KnowledgeIndexer
from .semantic_search import SemanticSearchEngine
from .recommendation_engine import RecommendationEngine


@dataclass
class FileChangeEvent:
    """文件变更事件"""
    file_path: str
    event_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    

@dataclass
class LearningStats:
    """学习统计信息"""
    total_files_monitored: int = 0
    files_processed: int = 0
    files_indexed: int = 0
    files_failed: int = 0
    last_update: Optional[datetime] = None
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class CHSFileSystemHandler(FileSystemEventHandler):
    """CHS-SDK 文件系统事件处理器"""
    
    def __init__(self, auto_learner: 'AutoLearningSystem'):
        super().__init__()
        self.auto_learner = auto_learner
        self.logger = logging.getLogger(__name__)
        
    def on_modified(self, event):
        if not event.is_directory:
            self.auto_learner.queue_file_change(event.src_path, 'modified')
            
    def on_created(self, event):
        if not event.is_directory:
            self.auto_learner.queue_file_change(event.src_path, 'created')
            
    def on_deleted(self, event):
        if not event.is_directory:
            self.auto_learner.queue_file_change(event.src_path, 'deleted')


class AutoLearningSystem:
    """CHS-SDK 知识库自动学习系统"""
    
    def __init__(self, 
                 project_root: str,
                 knowledge_indexer: KnowledgeIndexer,
                 semantic_search: SemanticSearchEngine,
                 recommendation_engine: RecommendationEngine,
                 config_path: Optional[str] = None):
        """
        初始化自动学习系统
        
        Args:
            project_root: 项目根目录
            knowledge_indexer: 知识索引器
            semantic_search: 语义搜索引擎
            recommendation_engine: 推荐引擎
            config_path: 配置文件路径
        """
        self.project_root = Path(project_root)
        self.knowledge_indexer = knowledge_indexer
        self.semantic_search = semantic_search
        self.recommendation_engine = recommendation_engine
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.logger = logging.getLogger(__name__)
        self.observer = Observer()
        self.handler = CHSFileSystemHandler(self)
        
        # 文件变更队列和处理
        self.change_queue: List[FileChangeEvent] = []
        self.queue_lock = threading.Lock()
        self.processing_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # 文件哈希缓存
        self.file_hashes: Dict[str, str] = {}
        self.hash_cache_file = self.project_root / '.chs_cache' / 'file_hashes.yaml'
        
        # 统计信息
        self.stats = LearningStats()
        
        # Git 集成
        self.git_repo = None
        try:
            self.git_repo = git.Repo(self.project_root)
        except git.InvalidGitRepositoryError:
            self.logger.warning("项目不是Git仓库，将跳过Git集成功能")
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4))
        
        # 加载文件哈希缓存
        self._load_file_hashes()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        default_config = {
            'monitor_patterns': ['*.py', '*.yml', '*.yaml', '*.md', '*.txt', '*.json'],
            'ignore_patterns': ['__pycache__', '.git', '.vscode', 'node_modules', '*.pyc'],
            'batch_size': 10,
            'processing_interval': 5.0,  # 秒
            'debounce_time': 2.0,  # 秒
            'max_workers': 4,
            'enable_git_integration': True,
            'auto_commit_changes': False,
            'learning_threshold': 0.1,  # 相似度阈值
            'max_file_size': 10 * 1024 * 1024,  # 10MB
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
                
        return default_config
    
    def _load_file_hashes(self):
        """加载文件哈希缓存"""
        if self.hash_cache_file.exists():
            try:
                with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                    self.file_hashes = yaml.safe_load(f) or {}
            except Exception as e:
                self.logger.error(f"加载文件哈希缓存失败: {e}")
                self.file_hashes = {}
    
    def _save_file_hashes(self):
        """保存文件哈希缓存"""
        try:
            self.hash_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.file_hashes, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"保存文件哈希缓存失败: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """判断是否应该监控该文件"""
        path = Path(file_path)
        
        # 检查文件大小
        try:
            if path.stat().st_size > self.config['max_file_size']:
                return False
        except OSError:
            return False
        
        # 检查文件模式
        file_name = path.name
        file_ext = path.suffix
        
        # 检查忽略模式
        for pattern in self.config['ignore_patterns']:
            if pattern in str(path) or file_name.startswith(pattern):
                return False
        
        # 检查监控模式
        for pattern in self.config['monitor_patterns']:
            if pattern.startswith('*.'):
                if file_ext == pattern[1:]:
                    return True
            elif pattern in file_name:
                return True
        
        return False
    
    def start_monitoring(self):
        """开始监控文件系统"""
        if self.is_running:
            self.logger.warning("自动学习系统已在运行")
            return
        
        self.logger.info("启动CHS-SDK知识库自动学习系统")
        
        # 设置文件系统监控
        self.observer.schedule(self.handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        # 启动处理线程
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._process_changes_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # 执行初始扫描
        self._initial_scan()
        
        self.logger.info("自动学习系统启动完成")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            return
        
        self.logger.info("停止自动学习系统")
        
        self.is_running = False
        self.observer.stop()
        self.observer.join()
        
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        
        self.executor.shutdown(wait=True)
        self._save_file_hashes()
        
        self.logger.info("自动学习系统已停止")
    
    def queue_file_change(self, file_path: str, event_type: str):
        """将文件变更加入队列"""
        if not self._should_monitor_file(file_path):
            return
        
        # 计算文件哈希
        file_hash = None
        file_size = None
        
        if event_type != 'deleted':
            file_hash = self._calculate_file_hash(file_path)
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                pass
        
        # 检查是否真的发生了变更
        if event_type == 'modified':
            old_hash = self.file_hashes.get(file_path)
            if old_hash == file_hash:
                return  # 文件内容未变更
        
        event = FileChangeEvent(
            file_path=file_path,
            event_type=event_type,
            timestamp=datetime.now(),
            file_hash=file_hash,
            file_size=file_size
        )
        
        with self.queue_lock:
            self.change_queue.append(event)
        
        self.logger.debug(f"文件变更已加入队列: {file_path} ({event_type})")
    
    def _process_changes_loop(self):
        """处理变更的主循环"""
        while self.is_running:
            try:
                self._process_pending_changes()
                time.sleep(self.config['processing_interval'])
            except Exception as e:
                self.logger.error(f"处理变更时发生错误: {e}")
                time.sleep(5)
    
    def _process_pending_changes(self):
        """处理待处理的变更"""
        with self.queue_lock:
            if not self.change_queue:
                return
            
            # 获取待处理的变更
            changes_to_process = self.change_queue[:self.config['batch_size']]
            self.change_queue = self.change_queue[self.config['batch_size']:]
        
        if not changes_to_process:
            return
        
        # 去重和防抖
        debounced_changes = self._debounce_changes(changes_to_process)
        
        # 批量处理
        start_time = time.time()
        futures = []
        
        for change in debounced_changes:
            future = self.executor.submit(self._process_single_change, change)
            futures.append(future)
        
        # 等待所有任务完成
        for future in futures:
            try:
                future.result(timeout=30)
            except Exception as e:
                self.logger.error(f"处理文件变更失败: {e}")
                self.stats.files_failed += 1
                self.stats.errors.append(str(e))
        
        # 更新统计信息
        self.stats.files_processed += len(debounced_changes)
        self.stats.processing_time += time.time() - start_time
        self.stats.last_update = datetime.now()
        
        # 保存哈希缓存
        self._save_file_hashes()
        
        self.logger.info(f"处理了 {len(debounced_changes)} 个文件变更")
    
    def _debounce_changes(self, changes: List[FileChangeEvent]) -> List[FileChangeEvent]:
        """去重和防抖处理"""
        # 按文件路径分组
        file_changes: Dict[str, List[FileChangeEvent]] = {}
        for change in changes:
            if change.file_path not in file_changes:
                file_changes[change.file_path] = []
            file_changes[change.file_path].append(change)
        
        # 对每个文件只保留最新的变更
        debounced = []
        current_time = datetime.now()
        
        for file_path, file_change_list in file_changes.items():
            # 按时间排序
            file_change_list.sort(key=lambda x: x.timestamp)
            latest_change = file_change_list[-1]
            
            # 检查防抖时间
            time_diff = (current_time - latest_change.timestamp).total_seconds()
            if time_diff >= self.config['debounce_time']:
                debounced.append(latest_change)
        
        return debounced
    
    def _process_single_change(self, change: FileChangeEvent):
        """处理单个文件变更"""
        try:
            if change.event_type == 'deleted':
                self._handle_file_deletion(change)
            else:
                self._handle_file_update(change)
                
        except Exception as e:
            self.logger.error(f"处理文件变更失败 {change.file_path}: {e}")
            raise
    
    def _handle_file_deletion(self, change: FileChangeEvent):
        """处理文件删除"""
        # 从索引中移除
        self.knowledge_indexer.remove_file(change.file_path)
        
        # 从语义搜索中移除
        self.semantic_search.remove_document(change.file_path)
        
        # 从哈希缓存中移除
        if change.file_path in self.file_hashes:
            del self.file_hashes[change.file_path]
        
        self.logger.info(f"已从知识库中移除文件: {change.file_path}")
    
    def _handle_file_update(self, change: FileChangeEvent):
        """处理文件更新或创建"""
        # 更新哈希缓存
        if change.file_hash:
            self.file_hashes[change.file_path] = change.file_hash
        
        # 重新索引文件
        try:
            self.knowledge_indexer.index_file(change.file_path)
            self.stats.files_indexed += 1
            
            # 更新语义搜索索引
            self._update_semantic_index(change.file_path)
            
            # 更新推荐系统
            self._update_recommendations(change.file_path)
            
            self.logger.info(f"已更新知识库索引: {change.file_path}")
            
        except Exception as e:
            self.logger.error(f"索引文件失败 {change.file_path}: {e}")
            raise
    
    def _update_semantic_index(self, file_path: str):
        """更新语义搜索索引"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加到语义搜索
            self.semantic_search.add_document(
                doc_id=file_path,
                content=content,
                metadata={
                    'file_path': file_path,
                    'file_type': Path(file_path).suffix,
                    'last_modified': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"更新语义索引失败 {file_path}: {e}")
    
    def _update_recommendations(self, file_path: str):
        """更新推荐系统"""
        try:
            # 分析文件类型和内容
            file_type = self._analyze_file_type(file_path)
            
            # 根据文件类型更新推荐
            if file_type == 'agent':
                self.recommendation_engine.update_agent_registry()
            elif file_type == 'config':
                self.recommendation_engine.update_config_templates()
            
        except Exception as e:
            self.logger.error(f"更新推荐系统失败 {file_path}: {e}")
    
    def _analyze_file_type(self, file_path: str) -> str:
        """分析文件类型"""
        path = Path(file_path)
        
        # 基于路径判断
        if 'agents' in path.parts:
            return 'agent'
        elif 'config' in path.parts or path.suffix in ['.yml', '.yaml']:
            return 'config'
        elif path.suffix == '.md':
            return 'documentation'
        elif path.suffix == '.py':
            return 'code'
        else:
            return 'other'
    
    def _initial_scan(self):
        """执行初始扫描"""
        self.logger.info("开始初始扫描项目文件")
        
        scan_count = 0
        for root, dirs, files in os.walk(self.project_root):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.config['ignore_patterns'])]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self._should_monitor_file(file_path):
                    # 检查文件是否需要更新
                    current_hash = self._calculate_file_hash(file_path)
                    cached_hash = self.file_hashes.get(file_path)
                    
                    if current_hash != cached_hash:
                        self.queue_file_change(file_path, 'modified')
                        scan_count += 1
        
        self.stats.total_files_monitored = scan_count
        self.logger.info(f"初始扫描完成，发现 {scan_count} 个需要更新的文件")
    
    def force_rebuild_index(self):
        """强制重建整个索引"""
        self.logger.info("开始强制重建知识库索引")
        
        try:
            # 清空现有索引
            self.knowledge_indexer.clear_index()
            self.semantic_search.clear_index()
            
            # 重新扫描所有文件
            self.file_hashes.clear()
            self._initial_scan()
            
            self.logger.info("知识库索引重建完成")
            
        except Exception as e:
            self.logger.error(f"重建索引失败: {e}")
            raise
    
    def get_learning_stats(self) -> LearningStats:
        """获取学习统计信息"""
        return self.stats
    
    def get_git_changes(self, since_commit: Optional[str] = None) -> List[str]:
        """获取Git变更的文件列表"""
        if not self.git_repo:
            return []
        
        try:
            if since_commit:
                # 获取指定提交以来的变更
                diff = self.git_repo.git.diff('--name-only', since_commit, 'HEAD')
            else:
                # 获取未提交的变更
                diff = self.git_repo.git.diff('--name-only', 'HEAD')
            
            changed_files = []
            for line in diff.split('\n'):
                if line.strip():
                    file_path = os.path.join(self.project_root, line.strip())
                    if os.path.exists(file_path) and self._should_monitor_file(file_path):
                        changed_files.append(file_path)
            
            return changed_files
            
        except Exception as e:
            self.logger.error(f"获取Git变更失败: {e}")
            return []
    
    def sync_with_git(self, since_commit: Optional[str] = None):
        """与Git同步，处理变更的文件"""
        changed_files = self.get_git_changes(since_commit)
        
        for file_path in changed_files:
            self.queue_file_change(file_path, 'modified')
        
        self.logger.info(f"已同步 {len(changed_files)} 个Git变更文件")
    
    def __enter__(self):
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring()


def create_auto_learning_system(project_root: str, 
                               knowledge_base_config: Optional[str] = None) -> AutoLearningSystem:
    """创建自动学习系统实例"""
    from .knowledge_base import KnowledgeBase
    import yaml
    
    # 加载配置
    config = None
    if knowledge_base_config and Path(knowledge_base_config).exists():
        try:
            with open(knowledge_base_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load config from {knowledge_base_config}: {e}")
    
    # 创建知识库实例
    kb = KnowledgeBase(project_root, config)
    
    # 创建自动学习系统
    auto_learner = AutoLearningSystem(
        project_root=project_root,
        knowledge_indexer=kb.indexer,
        semantic_search=kb.search_engine,
        recommendation_engine=kb.recommendation_engine,
        config_path=knowledge_base_config
    )
    
    return auto_learner


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动自动学习系统
    with create_auto_learning_system(project_path) as auto_learner:
        print("CHS-SDK 自动学习系统已启动，按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(1)
                stats = auto_learner.get_learning_stats()
                if stats.last_update:
                    print(f"\r已处理: {stats.files_processed} 个文件, 索引: {stats.files_indexed} 个文件", end="")
        except KeyboardInterrupt:
            print("\n正在停止自动学习系统...")