#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS 仿真平台文件备份脚本
支持用户上传文件、仿真结果文件的自动备份、同步和恢复
"""

import os
import sys
import json
import shutil
import hashlib
import logging
import argparse
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.exceptions import ClientError
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


@dataclass
class FileBackupConfig:
    """文件备份配置类"""
    source_dirs: List[str]
    backup_dir: str
    retention_days: int
    sync_interval: int  # 同步间隔（秒）
    exclude_patterns: List[str]
    include_patterns: List[str]
    max_file_size: int  # 最大文件大小（字节）
    compression: bool
    encryption: bool
    encryption_key: Optional[str]
    s3_bucket: Optional[str]
    s3_region: Optional[str]
    s3_access_key: Optional[str]
    s3_secret_key: Optional[str]
    checksum_verification: bool
    notification_webhook: Optional[str]
    parallel_uploads: int
    watch_mode: bool


@dataclass
class FileInfo:
    """文件信息类"""
    path: str
    size: int
    mtime: float
    checksum: str
    backup_path: Optional[str] = None
    s3_key: Optional[str] = None
    last_backup: Optional[str] = None


class FileBackupHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, backup_manager):
        self.backup_manager = backup_manager
        self.logger = backup_manager.logger
    
    def on_created(self, event):
        if not event.is_directory:
            self.logger.info(f"检测到新文件: {event.src_path}")
            self.backup_manager.backup_single_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.logger.info(f"检测到文件修改: {event.src_path}")
            self.backup_manager.backup_single_file(event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.logger.info(f"检测到文件删除: {event.src_path}")
            # 可以选择在备份中标记文件为已删除


class FileBackup:
    """文件备份管理器"""
    
    def __init__(self, config: FileBackupConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件索引
        self.file_index = {}
        self.load_file_index()
        
        # 初始化 S3 客户端
        if config.s3_bucket:
            self.s3_client = boto3.client(
                's3',
                region_name=config.s3_region,
                aws_access_key_id=config.s3_access_key,
                aws_secret_access_key=config.s3_secret_key
            )
        else:
            self.s3_client = None
        
        # 线程锁
        self.index_lock = threading.Lock()
        
        # 文件监控
        if config.watch_mode:
            self.observer = Observer()
            self.setup_file_watcher()
        else:
            self.observer = None
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('file_backup')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path(self.config.backup_dir) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / f'file_backup_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def setup_file_watcher(self):
        """设置文件监控"""
        event_handler = FileBackupHandler(self)
        
        for source_dir in self.config.source_dirs:
            if Path(source_dir).exists():
                self.observer.schedule(event_handler, source_dir, recursive=True)
                self.logger.info(f"开始监控目录: {source_dir}")
    
    def start_watching(self):
        """开始文件监控"""
        if self.observer:
            self.observer.start()
            self.logger.info("文件监控已启动")
    
    def stop_watching(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("文件监控已停止")
    
    def load_file_index(self):
        """加载文件索引"""
        index_file = self.backup_dir / 'file_index.json'
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.file_index = {
                        path: FileInfo(**info) for path, info in data.items()
                    }
                self.logger.info(f"加载文件索引: {len(self.file_index)} 个文件")
            except Exception as e:
                self.logger.error(f"加载文件索引失败: {e}")
                self.file_index = {}
        else:
            self.file_index = {}
    
    def save_file_index(self):
        """保存文件索引"""
        index_file = self.backup_dir / 'file_index.json'
        
        try:
            with self.index_lock:
                data = {
                    path: asdict(info) for path, info in self.file_index.items()
                }
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"保存文件索引失败: {e}")
    
    def calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"计算校验和失败 {file_path}: {e}")
            return ""
    
    def should_backup_file(self, file_path: str) -> bool:
        """判断是否应该备份文件"""
        file_path_obj = Path(file_path)
        
        # 检查文件大小
        try:
            if file_path_obj.stat().st_size > self.config.max_file_size:
                return False
        except OSError:
            return False
        
        # 检查包含模式
        if self.config.include_patterns:
            included = False
            for pattern in self.config.include_patterns:
                if file_path_obj.match(pattern):
                    included = True
                    break
            if not included:
                return False
        
        # 检查排除模式
        for pattern in self.config.exclude_patterns:
            if file_path_obj.match(pattern):
                return False
        
        return True
    
    def scan_source_directories(self) -> List[str]:
        """扫描源目录获取所有文件"""
        all_files = []
        
        for source_dir in self.config.source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                self.logger.warning(f"源目录不存在: {source_dir}")
                continue
            
            self.logger.info(f"扫描目录: {source_dir}")
            
            for file_path in source_path.rglob('*'):
                if file_path.is_file() and self.should_backup_file(str(file_path)):
                    all_files.append(str(file_path))
        
        self.logger.info(f"发现 {len(all_files)} 个文件需要备份")
        return all_files
    
    def get_files_to_backup(self, all_files: List[str]) -> List[str]:
        """获取需要备份的文件列表"""
        files_to_backup = []
        
        for file_path in all_files:
            try:
                file_stat = Path(file_path).stat()
                current_mtime = file_stat.st_mtime
                current_size = file_stat.st_size
                
                # 检查文件是否已在索引中
                if file_path in self.file_index:
                    file_info = self.file_index[file_path]
                    
                    # 检查文件是否已修改
                    if (file_info.mtime != current_mtime or 
                        file_info.size != current_size):
                        files_to_backup.append(file_path)
                else:
                    # 新文件
                    files_to_backup.append(file_path)
                    
            except OSError as e:
                self.logger.error(f"无法访问文件 {file_path}: {e}")
        
        return files_to_backup
    
    def backup_single_file(self, file_path: str) -> bool:
        """备份单个文件"""
        if not self.should_backup_file(file_path):
            return False
        
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False
            
            # 计算相对路径
            relative_path = None
            for source_dir in self.config.source_dirs:
                try:
                    relative_path = source_path.relative_to(Path(source_dir))
                    break
                except ValueError:
                    continue
            
            if relative_path is None:
                self.logger.warning(f"文件不在任何源目录中: {file_path}")
                return False
            
            # 创建备份路径
            backup_path = self.backup_dir / 'files' / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, backup_path)
            
            # 计算校验和
            checksum = ""
            if self.config.checksum_verification:
                checksum = self.calculate_checksum(file_path)
            
            # 更新文件索引
            file_stat = source_path.stat()
            file_info = FileInfo(
                path=file_path,
                size=file_stat.st_size,
                mtime=file_stat.st_mtime,
                checksum=checksum,
                backup_path=str(backup_path),
                last_backup=datetime.now().isoformat()
            )
            
            with self.index_lock:
                self.file_index[file_path] = file_info
            
            # 上传到 S3
            if self.s3_client:
                s3_key = f"file-backups/{relative_path}"
                if self._upload_file_to_s3(backup_path, s3_key):
                    file_info.s3_key = s3_key
            
            self.logger.info(f"文件备份成功: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份文件失败 {file_path}: {e}")
            return False
    
    def backup_files(self, files: List[str]) -> Dict[str, bool]:
        """批量备份文件"""
        results = {}
        
        if not files:
            return results
        
        self.logger.info(f"开始备份 {len(files)} 个文件")
        
        # 使用线程池并行备份
        with ThreadPoolExecutor(max_workers=self.config.parallel_uploads) as executor:
            future_to_file = {
                executor.submit(self.backup_single_file, file_path): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    results[file_path] = success
                except Exception as e:
                    self.logger.error(f"备份文件异常 {file_path}: {e}")
                    results[file_path] = False
        
        # 保存文件索引
        self.save_file_index()
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"备份完成: {success_count}/{len(files)} 个文件成功")
        
        return results
    
    def _upload_file_to_s3(self, file_path: Path, s3_key: str) -> bool:
        """上传文件到 S3"""
        try:
            self.s3_client.upload_file(
                str(file_path),
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            return True
        except ClientError as e:
            self.logger.error(f"上传文件到 S3 失败 {s3_key}: {e}")
            return False
    
    def restore_file(self, file_path: str, restore_path: Optional[str] = None) -> bool:
        """恢复单个文件"""
        if file_path not in self.file_index:
            self.logger.error(f"文件不在备份索引中: {file_path}")
            return False
        
        file_info = self.file_index[file_path]
        target_path = restore_path or file_path
        
        try:
            # 优先从本地备份恢复
            if file_info.backup_path and Path(file_info.backup_path).exists():
                shutil.copy2(file_info.backup_path, target_path)
                self.logger.info(f"从本地备份恢复文件: {file_path}")
                return True
            
            # 从 S3 恢复
            elif self.s3_client and file_info.s3_key:
                Path(target_path).parent.mkdir(parents=True, exist_ok=True)
                self.s3_client.download_file(
                    self.config.s3_bucket,
                    file_info.s3_key,
                    target_path
                )
                self.logger.info(f"从 S3 恢复文件: {file_path}")
                return True
            
            else:
                self.logger.error(f"无法找到文件的备份: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"恢复文件失败 {file_path}: {e}")
            return False
    
    def verify_backup(self, file_path: str) -> bool:
        """验证备份文件完整性"""
        if file_path not in self.file_index:
            return False
        
        file_info = self.file_index[file_path]
        
        if not file_info.backup_path or not Path(file_info.backup_path).exists():
            return False
        
        if not self.config.checksum_verification or not file_info.checksum:
            return True
        
        # 验证校验和
        current_checksum = self.calculate_checksum(file_info.backup_path)
        return current_checksum == file_info.checksum
    
    def cleanup_old_backups(self):
        """清理过期备份"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        files_to_remove = []
        
        for file_path, file_info in self.file_index.items():
            if file_info.mtime < cutoff_timestamp:
                files_to_remove.append(file_path)
                
                # 删除本地备份文件
                if file_info.backup_path and Path(file_info.backup_path).exists():
                    try:
                        Path(file_info.backup_path).unlink()
                        self.logger.info(f"删除过期备份: {file_info.backup_path}")
                    except Exception as e:
                        self.logger.error(f"删除过期备份失败: {e}")
                
                # 删除 S3 备份
                if self.s3_client and file_info.s3_key:
                    try:
                        self.s3_client.delete_object(
                            Bucket=self.config.s3_bucket,
                            Key=file_info.s3_key
                        )
                        self.logger.info(f"删除 S3 过期备份: {file_info.s3_key}")
                    except ClientError as e:
                        self.logger.error(f"删除 S3 过期备份失败: {e}")
        
        # 从索引中移除
        with self.index_lock:
            for file_path in files_to_remove:
                del self.file_index[file_path]
        
        if files_to_remove:
            self.save_file_index()
            self.logger.info(f"清理了 {len(files_to_remove)} 个过期备份")
    
    def get_backup_statistics(self) -> Dict:
        """获取备份统计信息"""
        total_files = len(self.file_index)
        total_size = sum(info.size for info in self.file_index.values())
        
        local_backups = sum(1 for info in self.file_index.values() 
                           if info.backup_path and Path(info.backup_path).exists())
        s3_backups = sum(1 for info in self.file_index.values() if info.s3_key)
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'local_backups': local_backups,
            's3_backups': s3_backups,
            'last_update': datetime.now().isoformat()
        }
    
    def run_full_backup(self):
        """执行完整备份"""
        self.logger.info("开始执行完整备份")
        
        # 扫描所有文件
        all_files = self.scan_source_directories()
        
        # 获取需要备份的文件
        files_to_backup = self.get_files_to_backup(all_files)
        
        if not files_to_backup:
            self.logger.info("没有文件需要备份")
            return
        
        # 执行备份
        results = self.backup_files(files_to_backup)
        
        # 发送通知
        if self.config.notification_webhook:
            self._send_notification(results)
        
        self.logger.info("完整备份执行完成")
    
    def _send_notification(self, results: Dict[str, bool]):
        """发送备份通知"""
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        message = {
            'type': 'file_backup_completed',
            'timestamp': datetime.now().isoformat(),
            'total_files': total_count,
            'success_files': success_count,
            'failed_files': total_count - success_count,
            'statistics': self.get_backup_statistics()
        }
        
        try:
            response = requests.post(
                self.config.notification_webhook,
                json=message,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")


def load_config(config_file: str) -> FileBackupConfig:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    return FileBackupConfig(**config_data)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CHS 文件备份工具')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--action', choices=['backup', 'restore', 'verify', 'cleanup', 'stats', 'watch'], 
                       default='backup', help='操作类型')
    parser.add_argument('--file', help='文件路径（用于恢复和验证）')
    parser.add_argument('--restore-path', help='恢复目标路径')
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        backup_manager = FileBackup(config)
        
        if args.action == 'backup':
            backup_manager.run_full_backup()
            
        elif args.action == 'restore':
            if not args.file:
                print("错误: 恢复操作需要指定文件路径")
                sys.exit(1)
            
            success = backup_manager.restore_file(args.file, args.restore_path)
            if not success:
                sys.exit(1)
                
        elif args.action == 'verify':
            if args.file:
                is_valid = backup_manager.verify_backup(args.file)
                print(f"备份验证: {'通过' if is_valid else '失败'}")
            else:
                # 验证所有备份
                total = 0
                valid = 0
                for file_path in backup_manager.file_index:
                    total += 1
                    if backup_manager.verify_backup(file_path):
                        valid += 1
                print(f"备份验证完成: {valid}/{total} 个文件通过验证")
                
        elif args.action == 'cleanup':
            backup_manager.cleanup_old_backups()
            print("清理完成")
            
        elif args.action == 'stats':
            stats = backup_manager.get_backup_statistics()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
        elif args.action == 'watch':
            backup_manager.start_watching()
            try:
                print("文件监控已启动，按 Ctrl+C 停止...")
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                backup_manager.stop_watching()
                print("文件监控已停止")
                
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()