#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 自动学习系统启动脚本

该脚本用于启动和管理CHS-SDK知识库自动学习系统，支持：
- 启动/停止自动学习服务
- 配置管理
- 状态监控
- 手动触发学习
- 系统诊断
"""

import os
import sys
import time
import signal
import argparse
import threading
from pathlib import Path
from datetime import datetime
import yaml
import logging
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.knowledge.auto_learning import create_auto_learning_system, AutoLearningSystem
    from core_lib.knowledge.knowledge_base import KnowledgeBase
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖: pip install -r core_lib/knowledge/requirements.txt")
    sys.exit(1)


class AutoLearningManager:
    """自动学习系统管理器"""
    
    def __init__(self, project_root: str, config_path: Optional[str] = None):
        self.project_root = Path(project_root)
        self.config_path = config_path or self.project_root / "core_lib" / "knowledge" / "auto_learning_config.yml"
        self.auto_learner: Optional[AutoLearningSystem] = None
        self.is_running = False
        self.logger = self._setup_logging()
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "auto_learning.log"
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # 配置根日志器
        logger = logging.getLogger('chs_auto_learning')
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"接收到信号 {signum}，正在停止自动学习系统...")
        self.stop()
        sys.exit(0)
    
    def load_config(self) -> dict:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self.logger.info(f"已加载配置文件: {self.config_path}")
                return config
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return {}
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def start(self, daemon: bool = False) -> bool:
        """启动自动学习系统"""
        if self.is_running:
            self.logger.warning("自动学习系统已在运行")
            return False
        
        try:
            self.logger.info("正在启动CHS-SDK自动学习系统...")
            
            # 创建自动学习系统
            self.auto_learner = create_auto_learning_system(
                project_root=str(self.project_root),
                knowledge_base_config=str(self.config_path) if self.config_path.exists() else None
            )
            
            # 启动监控
            self.auto_learner.start_monitoring()
            self.is_running = True
            
            self.logger.info("自动学习系统启动成功")
            
            if daemon:
                self._run_daemon()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动自动学习系统失败: {e}")
            return False
    
    def stop(self) -> bool:
        """停止自动学习系统"""
        if not self.is_running:
            self.logger.warning("自动学习系统未在运行")
            return False
        
        try:
            self.logger.info("正在停止自动学习系统...")
            
            if self.auto_learner:
                self.auto_learner.stop_monitoring()
                self.auto_learner = None
            
            self.is_running = False
            self.logger.info("自动学习系统已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止自动学习系统失败: {e}")
            return False
    
    def restart(self) -> bool:
        """重启自动学习系统"""
        self.logger.info("正在重启自动学习系统...")
        
        if self.is_running:
            self.stop()
            time.sleep(2)
        
        return self.start()
    
    def status(self) -> dict:
        """获取系统状态"""
        status_info = {
            'running': self.is_running,
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'config_path': str(self.config_path),
            'config_exists': self.config_path.exists()
        }
        
        if self.auto_learner and self.is_running:
            try:
                stats = self.auto_learner.get_learning_stats()
                status_info.update({
                    'stats': {
                        'total_files_monitored': stats.total_files_monitored,
                        'files_processed': stats.files_processed,
                        'files_indexed': stats.files_indexed,
                        'files_failed': stats.files_failed,
                        'last_update': stats.last_update.isoformat() if stats.last_update else None,
                        'processing_time': stats.processing_time,
                        'error_count': len(stats.errors)
                    }
                })
            except Exception as e:
                status_info['stats_error'] = str(e)
        
        return status_info
    
    def force_rebuild(self) -> bool:
        """强制重建知识库索引"""
        if not self.is_running or not self.auto_learner:
            self.logger.error("自动学习系统未运行，无法执行重建操作")
            return False
        
        try:
            self.logger.info("开始强制重建知识库索引...")
            self.auto_learner.force_rebuild_index()
            self.logger.info("知识库索引重建完成")
            return True
        except Exception as e:
            self.logger.error(f"重建索引失败: {e}")
            return False
    
    def sync_git(self, since_commit: Optional[str] = None) -> bool:
        """同步Git变更"""
        if not self.is_running or not self.auto_learner:
            self.logger.error("自动学习系统未运行，无法执行Git同步")
            return False
        
        try:
            self.logger.info("开始同步Git变更...")
            self.auto_learner.sync_with_git(since_commit)
            self.logger.info("Git同步完成")
            return True
        except Exception as e:
            self.logger.error(f"Git同步失败: {e}")
            return False
    
    def diagnose(self) -> dict:
        """系统诊断"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'project_root_exists': self.project_root.exists(),
                'config_file_exists': self.config_path.exists()
            },
            'dependencies': {},
            'directories': {},
            'permissions': {},
            'issues': []
        }
        
        # 检查依赖
        required_packages = {
            'watchdog': 'watchdog',
            'faiss-cpu': 'faiss',
            'sentence-transformers': 'sentence_transformers',
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'pyyaml': 'yaml',
            'gitpython': 'git'
        }
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                diagnosis['dependencies'][package_name] = 'installed'
            except ImportError:
                diagnosis['dependencies'][package_name] = 'missing'
                diagnosis['issues'].append(f"缺少依赖包: {package_name}")
        
        # 检查目录结构
        required_dirs = [
            'core_lib/knowledge',
            'logs',
            'scenarios',
            'agents'
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            diagnosis['directories'][dir_path] = {
                'exists': full_path.exists(),
                'is_directory': full_path.is_dir() if full_path.exists() else False,
                'readable': os.access(full_path, os.R_OK) if full_path.exists() else False,
                'writable': os.access(full_path, os.W_OK) if full_path.exists() else False
            }
            
            if not full_path.exists():
                diagnosis['issues'].append(f"目录不存在: {dir_path}")
        
        # 检查文件权限
        important_files = [
            'core_lib/knowledge/auto_learning.py',
            'core_lib/knowledge/knowledge_base.py'
        ]
        
        for file_path in important_files:
            full_path = self.project_root / file_path
            diagnosis['permissions'][file_path] = {
                'exists': full_path.exists(),
                'readable': os.access(full_path, os.R_OK) if full_path.exists() else False,
                'executable': os.access(full_path, os.X_OK) if full_path.exists() else False
            }
            
            if not full_path.exists():
                diagnosis['issues'].append(f"重要文件不存在: {file_path}")
        
        return diagnosis
    
    def _run_daemon(self):
        """以守护进程模式运行"""
        self.logger.info("自动学习系统正在以守护进程模式运行...")
        
        try:
            while self.is_running:
                time.sleep(10)
                
                # 定期输出状态信息
                if self.auto_learner:
                    stats = self.auto_learner.get_learning_stats()
                    if stats.last_update:
                        self.logger.info(
                            f"状态更新 - 已处理: {stats.files_processed} 个文件, "
                            f"索引: {stats.files_indexed} 个文件, "
                            f"失败: {stats.files_failed} 个文件"
                        )
                        
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号，正在停止...")
        finally:
            self.stop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CHS-SDK 自动学习系统管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_auto_learning.py start --daemon          # 启动守护进程
  python start_auto_learning.py stop                    # 停止服务
  python start_auto_learning.py restart                 # 重启服务
  python start_auto_learning.py status                  # 查看状态
  python start_auto_learning.py rebuild                 # 重建索引
  python start_auto_learning.py sync-git               # 同步Git变更
  python start_auto_learning.py diagnose               # 系统诊断
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'rebuild', 'sync-git', 'diagnose'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        '--project-root',
        default='.',
        help='项目根目录路径（默认: 当前目录）'
    )
    
    parser.add_argument(
        '--config',
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='以守护进程模式运行（仅适用于start命令）'
    )
    
    parser.add_argument(
        '--since-commit',
        help='Git同步起始提交（仅适用于sync-git命令）'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建管理器
    manager = AutoLearningManager(
        project_root=args.project_root,
        config_path=args.config
    )
    
    # 执行命令
    try:
        if args.command == 'start':
            success = manager.start(daemon=args.daemon)
            sys.exit(0 if success else 1)
            
        elif args.command == 'stop':
            success = manager.stop()
            sys.exit(0 if success else 1)
            
        elif args.command == 'restart':
            success = manager.restart()
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            status = manager.status()
            print("=== CHS-SDK 自动学习系统状态 ===")
            print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
            print(f"项目根目录: {status['project_root']}")
            print(f"配置文件: {status['config_path']}")
            print(f"配置文件存在: {'是' if status['config_exists'] else '否'}")
            print(f"检查时间: {status['timestamp']}")
            
            if 'stats' in status:
                stats = status['stats']
                print("\n=== 统计信息 ===")
                print(f"监控文件数: {stats['total_files_monitored']}")
                print(f"已处理文件: {stats['files_processed']}")
                print(f"已索引文件: {stats['files_indexed']}")
                print(f"失败文件数: {stats['files_failed']}")
                print(f"最后更新: {stats['last_update'] or '无'}")
                print(f"处理时间: {stats['processing_time']:.2f} 秒")
                print(f"错误数量: {stats['error_count']}")
            
            sys.exit(0)
            
        elif args.command == 'rebuild':
            success = manager.force_rebuild()
            print("索引重建" + ("成功" if success else "失败"))
            sys.exit(0 if success else 1)
            
        elif args.command == 'sync-git':
            success = manager.sync_git(args.since_commit)
            print("Git同步" + ("成功" if success else "失败"))
            sys.exit(0 if success else 1)
            
        elif args.command == 'diagnose':
            diagnosis = manager.diagnose()
            print("=== CHS-SDK 自动学习系统诊断 ===")
            print(f"诊断时间: {diagnosis['timestamp']}")
            
            print("\n=== 系统信息 ===")
            for key, value in diagnosis['system_info'].items():
                print(f"{key}: {value}")
            
            print("\n=== 依赖检查 ===")
            for package, status in diagnosis['dependencies'].items():
                status_text = "✓" if status == 'installed' else "✗"
                print(f"{status_text} {package}: {status}")
            
            print("\n=== 目录检查 ===")
            for dir_path, info in diagnosis['directories'].items():
                status_text = "✓" if info['exists'] and info['is_directory'] else "✗"
                print(f"{status_text} {dir_path}: 存在={info['exists']}, 可读={info['readable']}, 可写={info['writable']}")
            
            if diagnosis['issues']:
                print("\n=== 发现的问题 ===")
                for issue in diagnosis['issues']:
                    print(f"⚠ {issue}")
            else:
                print("\n✓ 未发现问题")
            
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"执行命令时发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()