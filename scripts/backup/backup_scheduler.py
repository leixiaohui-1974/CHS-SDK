#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS 仿真平台备份调度器
支持定时备份、增量备份、备份策略管理等功能
"""

import os
import sys
import json
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor


@dataclass
class BackupJob:
    """备份任务配置"""
    name: str
    type: str  # database, files, full
    schedule: str  # cron-like schedule
    config_file: str
    enabled: bool
    retention_policy: str
    priority: int
    max_runtime: int  # 最大运行时间（秒）
    notification_on_success: bool
    notification_on_failure: bool
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    next_run: Optional[str] = None


@dataclass
class BackupSchedulerConfig:
    """备份调度器配置"""
    jobs: List[BackupJob]
    max_concurrent_jobs: int
    log_level: str
    log_file: str
    notification_webhook: Optional[str]
    health_check_port: int
    metrics_enabled: bool
    cleanup_enabled: bool
    cleanup_schedule: str


class BackupScheduler:
    """备份调度器"""
    
    def __init__(self, config: BackupSchedulerConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.running_jobs = {}
        self.job_stats = {}
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_jobs)
        self.shutdown_event = threading.Event()
        
        # 初始化任务统计
        for job in config.jobs:
            self.job_stats[job.name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'last_duration': 0,
                'average_duration': 0
            }
        
        # 设置调度
        self._setup_schedules()
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('backup_scheduler')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 创建日志目录
        log_file = Path(self.config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file)
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
    
    def _setup_schedules(self):
        """设置调度任务"""
        for job in self.config.jobs:
            if not job.enabled:
                continue
            
            # 解析调度表达式
            if job.schedule == 'daily':
                schedule.every().day.at("02:00").do(self._run_job, job)
            elif job.schedule == 'weekly':
                schedule.every().sunday.at("01:00").do(self._run_job, job)
            elif job.schedule == 'hourly':
                schedule.every().hour.do(self._run_job, job)
            elif job.schedule.startswith('every '):
                # 解析 "every 6 hours" 格式
                parts = job.schedule.split()
                if len(parts) == 3:
                    interval = int(parts[1])
                    unit = parts[2]
                    
                    if unit == 'hours':
                        schedule.every(interval).hours.do(self._run_job, job)
                    elif unit == 'minutes':
                        schedule.every(interval).minutes.do(self._run_job, job)
                    elif unit == 'days':
                        schedule.every(interval).days.do(self._run_job, job)
            elif ':' in job.schedule:
                # 解析 "HH:MM" 格式
                schedule.every().day.at(job.schedule).do(self._run_job, job)
            
            self.logger.info(f"已设置备份任务调度: {job.name} - {job.schedule}")
        
        # 设置清理任务
        if self.config.cleanup_enabled:
            if self.config.cleanup_schedule == 'daily':
                schedule.every().day.at("04:00").do(self._run_cleanup)
            elif self.config.cleanup_schedule == 'weekly':
                schedule.every().sunday.at("03:00").do(self._run_cleanup)
    
    def _run_job(self, job: BackupJob):
        """运行备份任务"""
        if job.name in self.running_jobs:
            self.logger.warning(f"任务 {job.name} 正在运行，跳过此次调度")
            return
        
        self.logger.info(f"开始执行备份任务: {job.name}")
        
        # 提交任务到线程池
        future = self.executor.submit(self._execute_backup_job, job)
        self.running_jobs[job.name] = {
            'future': future,
            'start_time': datetime.now(),
            'job': job
        }
        
        # 设置超时检查
        threading.Timer(
            job.max_runtime,
            self._check_job_timeout,
            args=[job.name]
        ).start()
    
    def _execute_backup_job(self, job: BackupJob) -> bool:
        """执行备份任务"""
        start_time = datetime.now()
        success = False
        error_msg = None
        
        try:
            # 根据任务类型执行不同的备份脚本
            if job.type == 'database':
                cmd = [
                    sys.executable,
                    'scripts/backup/database_backup.py',
                    '--config', job.config_file,
                    '--action', 'backup'
                ]
            elif job.type == 'files':
                cmd = [
                    sys.executable,
                    'scripts/backup/file_backup.py',
                    '--config', job.config_file,
                    '--action', 'backup'
                ]
            elif job.type == 'full':
                # 执行完整备份（数据库 + 文件）
                success = self._run_full_backup(job)
                return success
            else:
                raise ValueError(f"未知的备份类型: {job.type}")
            
            # 执行备份命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=job.max_runtime
            )
            
            if result.returncode == 0:
                success = True
                self.logger.info(f"备份任务 {job.name} 执行成功")
            else:
                error_msg = result.stderr
                self.logger.error(f"备份任务 {job.name} 执行失败: {error_msg}")
                
        except subprocess.TimeoutExpired:
            error_msg = "备份任务超时"
            self.logger.error(f"备份任务 {job.name} 超时")
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"备份任务 {job.name} 执行异常: {e}")
        finally:
            # 更新任务状态
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            job.last_run = start_time.isoformat()
            job.last_status = 'success' if success else 'failed'
            
            # 更新统计信息
            stats = self.job_stats[job.name]
            stats['total_runs'] += 1
            stats['last_duration'] = duration
            
            if success:
                stats['successful_runs'] += 1
            else:
                stats['failed_runs'] += 1
            
            # 计算平均持续时间
            stats['average_duration'] = (
                (stats['average_duration'] * (stats['total_runs'] - 1) + duration) /
                stats['total_runs']
            )
            
            # 从运行中任务列表移除
            if job.name in self.running_jobs:
                del self.running_jobs[job.name]
            
            # 发送通知
            if (success and job.notification_on_success) or \
               (not success and job.notification_on_failure):
                self._send_job_notification(job, success, duration, error_msg)
        
        return success
    
    def _run_full_backup(self, job: BackupJob) -> bool:
        """执行完整备份"""
        success = True
        
        # 先执行数据库备份
        db_cmd = [
            sys.executable,
            'scripts/backup/database_backup.py',
            '--config', 'config/backup/database_backup.json',
            '--action', 'backup'
        ]
        
        try:
            result = subprocess.run(
                db_cmd,
                capture_output=True,
                text=True,
                timeout=job.max_runtime // 2
            )
            
            if result.returncode != 0:
                self.logger.error(f"数据库备份失败: {result.stderr}")
                success = False
        except Exception as e:
            self.logger.error(f"数据库备份异常: {e}")
            success = False
        
        # 再执行文件备份
        if success:
            file_cmd = [
                sys.executable,
                'scripts/backup/file_backup.py',
                '--config', 'config/backup/file_backup.json',
                '--action', 'backup'
            ]
            
            try:
                result = subprocess.run(
                    file_cmd,
                    capture_output=True,
                    text=True,
                    timeout=job.max_runtime // 2
                )
                
                if result.returncode != 0:
                    self.logger.error(f"文件备份失败: {result.stderr}")
                    success = False
            except Exception as e:
                self.logger.error(f"文件备份异常: {e}")
                success = False
        
        return success
    
    def _check_job_timeout(self, job_name: str):
        """检查任务超时"""
        if job_name in self.running_jobs:
            job_info = self.running_jobs[job_name]
            runtime = datetime.now() - job_info['start_time']
            
            if runtime.total_seconds() > job_info['job'].max_runtime:
                self.logger.warning(f"任务 {job_name} 运行超时，尝试取消")
                job_info['future'].cancel()
    
    def _run_cleanup(self):
        """运行清理任务"""
        self.logger.info("开始执行备份清理任务")
        
        try:
            # 清理数据库备份
            db_cleanup_cmd = [
                sys.executable,
                'scripts/backup/database_backup.py',
                '--config', 'config/backup/database_backup.json',
                '--action', 'cleanup'
            ]
            
            subprocess.run(db_cleanup_cmd, check=True)
            
            # 清理文件备份
            file_cleanup_cmd = [
                sys.executable,
                'scripts/backup/file_backup.py',
                '--config', 'config/backup/file_backup.json',
                '--action', 'cleanup'
            ]
            
            subprocess.run(file_cleanup_cmd, check=True)
            
            self.logger.info("备份清理任务执行完成")
            
        except Exception as e:
            self.logger.error(f"备份清理任务执行失败: {e}")
    
    def _send_job_notification(self, job: BackupJob, success: bool, 
                              duration: float, error_msg: Optional[str] = None):
        """发送任务通知"""
        if not self.config.notification_webhook:
            return
        
        message = {
            'type': 'backup_job_completed',
            'timestamp': datetime.now().isoformat(),
            'job_name': job.name,
            'job_type': job.type,
            'success': success,
            'duration': duration,
            'error_message': error_msg,
            'statistics': self.job_stats[job.name]
        }
        
        try:
            response = requests.post(
                self.config.notification_webhook,
                json=message,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"发送任务通知失败: {e}")
    
    def get_job_status(self) -> Dict:
        """获取任务状态"""
        status = {
            'running_jobs': {},
            'job_statistics': self.job_stats,
            'next_scheduled_jobs': [],
            'scheduler_uptime': datetime.now().isoformat()
        }
        
        # 运行中的任务
        for job_name, job_info in self.running_jobs.items():
            runtime = datetime.now() - job_info['start_time']
            status['running_jobs'][job_name] = {
                'start_time': job_info['start_time'].isoformat(),
                'runtime_seconds': runtime.total_seconds(),
                'job_type': job_info['job'].type
            }
        
        # 下次调度的任务
        for job in schedule.jobs:
            status['next_scheduled_jobs'].append({
                'job_func': str(job.job_func),
                'next_run': job.next_run.isoformat() if job.next_run else None
            })
        
        return status
    
    def run_job_manually(self, job_name: str) -> bool:
        """手动运行任务"""
        job = None
        for j in self.config.jobs:
            if j.name == job_name:
                job = j
                break
        
        if not job:
            self.logger.error(f"未找到任务: {job_name}")
            return False
        
        if job_name in self.running_jobs:
            self.logger.warning(f"任务 {job_name} 正在运行")
            return False
        
        self.logger.info(f"手动执行任务: {job_name}")
        self._run_job(job)
        return True
    
    def enable_job(self, job_name: str) -> bool:
        """启用任务"""
        for job in self.config.jobs:
            if job.name == job_name:
                job.enabled = True
                self.logger.info(f"已启用任务: {job_name}")
                return True
        return False
    
    def disable_job(self, job_name: str) -> bool:
        """禁用任务"""
        for job in self.config.jobs:
            if job.name == job_name:
                job.enabled = False
                self.logger.info(f"已禁用任务: {job_name}")
                return True
        return False
    
    def start(self):
        """启动调度器"""
        self.logger.info("备份调度器启动")
        
        while not self.shutdown_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                time.sleep(5)
        
        self.shutdown()
    
    def shutdown(self):
        """关闭调度器"""
        self.logger.info("正在关闭备份调度器...")
        
        # 设置关闭事件
        self.shutdown_event.set()
        
        # 等待运行中的任务完成
        for job_name, job_info in self.running_jobs.items():
            self.logger.info(f"等待任务 {job_name} 完成...")
            try:
                job_info['future'].result(timeout=30)
            except Exception as e:
                self.logger.error(f"等待任务 {job_name} 完成时发生错误: {e}")
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        self.logger.info("备份调度器已关闭")


def load_config(config_file: str) -> BackupSchedulerConfig:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 转换任务配置
    jobs = [BackupJob(**job_data) for job_data in config_data['jobs']]
    config_data['jobs'] = jobs
    
    return BackupSchedulerConfig(**config_data)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHS 备份调度器')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--action', choices=['start', 'status', 'run', 'enable', 'disable'], 
                       default='start', help='操作类型')
    parser.add_argument('--job', help='任务名称（用于 run、enable、disable 操作）')
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        scheduler = BackupScheduler(config)
        
        if args.action == 'start':
            scheduler.start()
        elif args.action == 'status':
            status = scheduler.get_job_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        elif args.action == 'run':
            if not args.job:
                print("错误: run 操作需要指定任务名称")
                sys.exit(1)
            success = scheduler.run_job_manually(args.job)
            if not success:
                sys.exit(1)
        elif args.action == 'enable':
            if not args.job:
                print("错误: enable 操作需要指定任务名称")
                sys.exit(1)
            success = scheduler.enable_job(args.job)
            if not success:
                sys.exit(1)
        elif args.action == 'disable':
            if not args.job:
                print("错误: disable 操作需要指定任务名称")
                sys.exit(1)
            success = scheduler.disable_job(args.job)
            if not success:
                sys.exit(1)
                
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()