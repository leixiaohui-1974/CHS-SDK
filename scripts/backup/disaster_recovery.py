#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS 仿真平台灾难恢复脚本
支持系统完整恢复、数据迁移、服务重建等功能
"""

import os
import sys
import json
import yaml
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import psycopg2
import redis
import requests
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException


@dataclass
class RecoveryConfig:
    """恢复配置类"""
    # 数据库配置
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    # Redis 配置
    redis_host: str
    redis_port: int
    redis_password: Optional[str]
    
    # 备份路径
    backup_base_dir: str
    
    # Kubernetes 配置
    k8s_config_path: Optional[str]
    k8s_namespace: str
    
    # 服务配置
    services: Dict[str, Any]
    
    # 恢复选项
    recovery_mode: str  # full, partial, data_only
    verify_after_recovery: bool
    notification_webhook: Optional[str]


class DisasterRecovery:
    """灾难恢复管理器"""
    
    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.backup_dir = Path(config.backup_base_dir)
        
        # 初始化 Kubernetes 客户端
        if config.k8s_config_path:
            k8s_config.load_kube_config(config_file=config.k8s_config_path)
            self.k8s_v1 = client.CoreV1Api()
            self.k8s_apps_v1 = client.AppsV1Api()
        else:
            self.k8s_v1 = None
            self.k8s_apps_v1 = None
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('disaster_recovery')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path(self.config.backup_base_dir) / 'recovery_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / f'recovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
    
    def list_available_backups(self) -> Dict[str, List[str]]:
        """列出可用的备份"""
        backups = {
            'database': [],
            'files': [],
            'configs': []
        }
        
        # 数据库备份
        db_backup_dir = self.backup_dir / 'database'
        if db_backup_dir.exists():
            for backup_file in db_backup_dir.glob('*.sql*'):
                backups['database'].append(str(backup_file))
        
        # 文件备份
        file_backup_dir = self.backup_dir / 'files'
        if file_backup_dir.exists():
            backups['files'] = [str(file_backup_dir)]
        
        # 配置备份
        config_backup_dir = self.backup_dir / 'configs'
        if config_backup_dir.exists():
            for config_file in config_backup_dir.glob('*.yaml'):
                backups['configs'].append(str(config_file))
        
        return backups
    
    def validate_backup_integrity(self, backup_path: str) -> bool:
        """验证备份完整性"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            self.logger.error(f"备份文件不存在: {backup_path}")
            return False
        
        # 检查文件大小
        if backup_file.stat().st_size == 0:
            self.logger.error(f"备份文件为空: {backup_path}")
            return False
        
        # 根据文件类型进行特定验证
        if backup_file.suffix == '.sql':
            return self._validate_sql_backup(backup_file)
        elif backup_file.suffix == '.gz':
            return self._validate_compressed_backup(backup_file)
        elif backup_file.suffix == '.yaml':
            return self._validate_yaml_backup(backup_file)
        
        return True
    
    def _validate_sql_backup(self, backup_file: Path) -> bool:
        """验证 SQL 备份文件"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # 读取前1KB
                return 'PostgreSQL database dump' in content
        except Exception as e:
            self.logger.error(f"验证 SQL 备份失败: {e}")
            return False
    
    def _validate_compressed_backup(self, backup_file: Path) -> bool:
        """验证压缩备份文件"""
        try:
            import gzip
            with gzip.open(backup_file, 'rt') as f:
                f.read(1024)  # 尝试读取
            return True
        except Exception as e:
            self.logger.error(f"验证压缩备份失败: {e}")
            return False
    
    def _validate_yaml_backup(self, backup_file: Path) -> bool:
        """验证 YAML 备份文件"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except Exception as e:
            self.logger.error(f"验证 YAML 备份失败: {e}")
            return False
    
    def stop_services(self) -> bool:
        """停止服务"""
        self.logger.info("开始停止服务")
        
        success = True
        
        # 停止 Kubernetes 服务
        if self.k8s_apps_v1:
            success &= self._stop_k8s_services()
        
        # 停止 Docker 服务
        success &= self._stop_docker_services()
        
        return success
    
    def _stop_k8s_services(self) -> bool:
        """停止 Kubernetes 服务"""
        try:
            # 获取所有部署
            deployments = self.k8s_apps_v1.list_namespaced_deployment(
                namespace=self.config.k8s_namespace
            )
            
            for deployment in deployments.items:
                # 缩放到 0 副本
                deployment.spec.replicas = 0
                self.k8s_apps_v1.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=self.config.k8s_namespace,
                    body=deployment
                )
                self.logger.info(f"停止 K8s 部署: {deployment.metadata.name}")
            
            return True
            
        except ApiException as e:
            self.logger.error(f"停止 K8s 服务失败: {e}")
            return False
    
    def _stop_docker_services(self) -> bool:
        """停止 Docker 服务"""
        try:
            # 停止 Docker Compose 服务
            result = subprocess.run(
                ['docker-compose', 'down'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Docker 服务已停止")
                return True
            else:
                self.logger.error(f"停止 Docker 服务失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"停止 Docker 服务异常: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        self.logger.info(f"开始恢复数据库: {backup_path}")
        
        if not self.validate_backup_integrity(backup_path):
            return False
        
        try:
            # 创建新数据库（如果不存在）
            self._create_database_if_not_exists()
            
            # 执行恢复
            cmd = [
                'psql',
                f'--host={self.config.db_host}',
                f'--port={self.config.db_port}',
                f'--username={self.config.db_user}',
                f'--dbname={self.config.db_name}',
                f'--file={backup_path}'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("数据库恢复成功")
                return True
            else:
                self.logger.error(f"数据库恢复失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"数据库恢复异常: {e}")
            return False
    
    def _create_database_if_not_exists(self):
        """创建数据库（如果不存在）"""
        try:
            # 连接到 postgres 数据库
            conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database='postgres',
                user=self.config.db_user,
                password=self.config.db_password
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config.db_name,)
            )
            
            if not cursor.fetchone():
                # 创建数据库
                cursor.execute(f'CREATE DATABASE "{self.config.db_name}"')
                self.logger.info(f"创建数据库: {self.config.db_name}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"创建数据库失败: {e}")
            raise
    
    def restore_files(self, backup_dir: str) -> bool:
        """恢复文件"""
        self.logger.info(f"开始恢复文件: {backup_dir}")
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            self.logger.error(f"备份目录不存在: {backup_dir}")
            return False
        
        try:
            # 恢复用户上传文件
            uploads_backup = backup_path / 'uploads'
            if uploads_backup.exists():
                uploads_target = Path('/app/uploads')
                uploads_target.mkdir(parents=True, exist_ok=True)
                
                for item in uploads_backup.rglob('*'):
                    if item.is_file():
                        relative_path = item.relative_to(uploads_backup)
                        target_file = uploads_target / relative_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                
                self.logger.info("用户文件恢复完成")
            
            # 恢复仿真结果文件
            results_backup = backup_path / 'simulation_results'
            if results_backup.exists():
                results_target = Path('/app/simulation_results')
                results_target.mkdir(parents=True, exist_ok=True)
                
                for item in results_backup.rglob('*'):
                    if item.is_file():
                        relative_path = item.relative_to(results_backup)
                        target_file = results_target / relative_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                
                self.logger.info("仿真结果文件恢复完成")
            
            return True
            
        except Exception as e:
            self.logger.error(f"文件恢复失败: {e}")
            return False
    
    def restore_configurations(self, config_backup_dir: str) -> bool:
        """恢复配置文件"""
        self.logger.info(f"开始恢复配置: {config_backup_dir}")
        
        config_path = Path(config_backup_dir)
        if not config_path.exists():
            self.logger.error(f"配置备份目录不存在: {config_backup_dir}")
            return False
        
        try:
            # 恢复应用配置
            app_config_backup = config_path / 'app_config.yaml'
            if app_config_backup.exists():
                shutil.copy2(app_config_backup, '/app/config/app_config.yaml')
                self.logger.info("应用配置恢复完成")
            
            # 恢复 Kubernetes 配置
            if self.k8s_v1:
                k8s_configs = config_path.glob('k8s_*.yaml')
                for k8s_config_file in k8s_configs:
                    self._restore_k8s_config(k8s_config_file)
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置恢复失败: {e}")
            return False
    
    def _restore_k8s_config(self, config_file: Path):
        """恢复 Kubernetes 配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 根据资源类型应用配置
            kind = config_data.get('kind')
            
            if kind == 'ConfigMap':
                self.k8s_v1.create_namespaced_config_map(
                    namespace=self.config.k8s_namespace,
                    body=config_data
                )
            elif kind == 'Secret':
                self.k8s_v1.create_namespaced_secret(
                    namespace=self.config.k8s_namespace,
                    body=config_data
                )
            
            self.logger.info(f"恢复 K8s 配置: {config_file.name}")
            
        except Exception as e:
            self.logger.error(f"恢复 K8s 配置失败 {config_file}: {e}")
    
    def start_services(self) -> bool:
        """启动服务"""
        self.logger.info("开始启动服务")
        
        success = True
        
        # 启动 Docker 服务
        success &= self._start_docker_services()
        
        # 启动 Kubernetes 服务
        if self.k8s_apps_v1:
            success &= self._start_k8s_services()
        
        return success
    
    def _start_docker_services(self) -> bool:
        """启动 Docker 服务"""
        try:
            # 启动 Docker Compose 服务
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                self.logger.info("Docker 服务已启动")
                return True
            else:
                self.logger.error(f"启动 Docker 服务失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"启动 Docker 服务异常: {e}")
            return False
    
    def _start_k8s_services(self) -> bool:
        """启动 Kubernetes 服务"""
        try:
            # 获取所有部署
            deployments = self.k8s_apps_v1.list_namespaced_deployment(
                namespace=self.config.k8s_namespace
            )
            
            for deployment in deployments.items:
                # 恢复副本数
                original_replicas = deployment.metadata.annotations.get(
                    'original-replicas', '1'
                )
                deployment.spec.replicas = int(original_replicas)
                
                self.k8s_apps_v1.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=self.config.k8s_namespace,
                    body=deployment
                )
                self.logger.info(f"启动 K8s 部署: {deployment.metadata.name}")
            
            return True
            
        except ApiException as e:
            self.logger.error(f"启动 K8s 服务失败: {e}")
            return False
    
    def verify_recovery(self) -> bool:
        """验证恢复结果"""
        self.logger.info("开始验证恢复结果")
        
        success = True
        
        # 验证数据库连接
        success &= self._verify_database()
        
        # 验证 Redis 连接
        success &= self._verify_redis()
        
        # 验证服务健康状态
        success &= self._verify_services()
        
        return success
    
    def _verify_database(self) -> bool:
        """验证数据库"""
        try:
            conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"数据库验证成功，用户数量: {user_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库验证失败: {e}")
            return False
    
    def _verify_redis(self) -> bool:
        """验证 Redis"""
        try:
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                decode_responses=True
            )
            
            r.ping()
            self.logger.info("Redis 验证成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis 验证失败: {e}")
            return False
    
    def _verify_services(self) -> bool:
        """验证服务状态"""
        success = True
        
        for service_name, service_config in self.config.services.items():
            health_url = service_config.get('health_check_url')
            if health_url:
                try:
                    response = requests.get(health_url, timeout=10)
                    if response.status_code == 200:
                        self.logger.info(f"服务 {service_name} 健康检查通过")
                    else:
                        self.logger.error(f"服务 {service_name} 健康检查失败: {response.status_code}")
                        success = False
                except Exception as e:
                    self.logger.error(f"服务 {service_name} 健康检查异常: {e}")
                    success = False
        
        return success
    
    def run_full_recovery(self, database_backup: str, files_backup: str, 
                         configs_backup: str) -> bool:
        """执行完整恢复"""
        self.logger.info("开始执行完整灾难恢复")
        
        try:
            # 1. 停止服务
            if not self.stop_services():
                self.logger.error("停止服务失败")
                return False
            
            # 2. 恢复数据库
            if not self.restore_database(database_backup):
                self.logger.error("数据库恢复失败")
                return False
            
            # 3. 恢复文件
            if not self.restore_files(files_backup):
                self.logger.error("文件恢复失败")
                return False
            
            # 4. 恢复配置
            if not self.restore_configurations(configs_backup):
                self.logger.error("配置恢复失败")
                return False
            
            # 5. 启动服务
            if not self.start_services():
                self.logger.error("启动服务失败")
                return False
            
            # 6. 验证恢复
            if self.config.verify_after_recovery:
                if not self.verify_recovery():
                    self.logger.error("恢复验证失败")
                    return False
            
            self.logger.info("完整灾难恢复成功")
            
            # 发送通知
            if self.config.notification_webhook:
                self._send_recovery_notification(True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"灾难恢复过程中发生异常: {e}")
            
            # 发送失败通知
            if self.config.notification_webhook:
                self._send_recovery_notification(False, str(e))
            
            return False
    
    def _send_recovery_notification(self, success: bool, error_msg: str = None):
        """发送恢复通知"""
        message = {
            'type': 'disaster_recovery_completed',
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error_message': error_msg
        }
        
        try:
            response = requests.post(
                self.config.notification_webhook,
                json=message,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"发送恢复通知失败: {e}")


def load_config(config_file: str) -> RecoveryConfig:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return RecoveryConfig(**config_data)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CHS 灾难恢复工具')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--action', choices=['list', 'verify', 'recover', 'test'], 
                       default='list', help='操作类型')
    parser.add_argument('--database-backup', help='数据库备份文件路径')
    parser.add_argument('--files-backup', help='文件备份目录路径')
    parser.add_argument('--configs-backup', help='配置备份目录路径')
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        recovery_manager = DisasterRecovery(config)
        
        if args.action == 'list':
            backups = recovery_manager.list_available_backups()
            print(json.dumps(backups, indent=2, ensure_ascii=False))
            
        elif args.action == 'verify':
            if args.database_backup:
                is_valid = recovery_manager.validate_backup_integrity(args.database_backup)
                print(f"数据库备份验证: {'通过' if is_valid else '失败'}")
            else:
                print("请指定要验证的备份文件")
                
        elif args.action == 'recover':
            if not all([args.database_backup, args.files_backup, args.configs_backup]):
                print("错误: 完整恢复需要指定所有备份路径")
                sys.exit(1)
            
            success = recovery_manager.run_full_recovery(
                args.database_backup,
                args.files_backup,
                args.configs_backup
            )
            
            if not success:
                sys.exit(1)
                
        elif args.action == 'test':
            # 测试恢复验证功能
            success = recovery_manager.verify_recovery()
            print(f"系统验证: {'通过' if success else '失败'}")
            if not success:
                sys.exit(1)
                
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()