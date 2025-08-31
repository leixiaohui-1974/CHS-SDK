#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS 仿真平台数据库备份脚本
支持 PostgreSQL 数据库的自动备份、压缩、加密和远程存储
"""

import os
import sys
import json
import gzip
import shutil
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@dataclass
class BackupConfig:
    """备份配置类"""
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    backup_dir: str
    retention_days: int
    compression: bool
    encryption: bool
    encryption_key: Optional[str]
    s3_bucket: Optional[str]
    s3_region: Optional[str]
    s3_access_key: Optional[str]
    s3_secret_key: Optional[str]
    notification_webhook: Optional[str]


class DatabaseBackup:
    """数据库备份管理器"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化加密器
        if config.encryption and config.encryption_key:
            self.cipher = Fernet(config.encryption_key.encode())
        else:
            self.cipher = None
            
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
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('database_backup')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path(self.config.backup_dir) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / f'backup_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            conn.close()
            self.logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def create_backup(self, backup_type: str = 'full') -> Optional[str]:
        """创建数据库备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{self.config.db_name}_{backup_type}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            self.logger.info(f"开始创建 {backup_type} 备份: {backup_filename}")
            
            # 构建 pg_dump 命令
            cmd = [
                'pg_dump',
                f'--host={self.config.db_host}',
                f'--port={self.config.db_port}',
                f'--username={self.config.db_user}',
                f'--dbname={self.config.db_name}',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_path}'
            ]
            
            # 根据备份类型添加参数
            if backup_type == 'schema':
                cmd.append('--schema-only')
            elif backup_type == 'data':
                cmd.append('--data-only')
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            # 执行备份命令
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode != 0:
                self.logger.error(f"备份失败: {result.stderr}")
                return None
            
            self.logger.info(f"备份创建成功: {backup_path}")
            
            # 压缩备份文件
            if self.config.compression:
                compressed_path = self._compress_backup(backup_path)
                if compressed_path:
                    backup_path.unlink()  # 删除原始文件
                    backup_path = compressed_path
            
            # 加密备份文件
            if self.config.encryption and self.cipher:
                encrypted_path = self._encrypt_backup(backup_path)
                if encrypted_path:
                    backup_path.unlink()  # 删除原始文件
                    backup_path = encrypted_path
            
            # 上传到 S3
            if self.s3_client:
                self._upload_to_s3(backup_path)
            
            # 记录备份信息
            self._record_backup_info(backup_path, backup_type)
            
            return str(backup_path)
            
        except subprocess.TimeoutExpired:
            self.logger.error("备份超时")
            return None
        except Exception as e:
            self.logger.error(f"备份过程中发生错误: {e}")
            return None
    
    def _compress_backup(self, backup_path: Path) -> Optional[Path]:
        """压缩备份文件"""
        try:
            compressed_path = backup_path.with_suffix(backup_path.suffix + '.gz')
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            self.logger.info(f"备份文件压缩完成: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"压缩备份文件失败: {e}")
            return None
    
    def _encrypt_backup(self, backup_path: Path) -> Optional[Path]:
        """加密备份文件"""
        try:
            encrypted_path = backup_path.with_suffix(backup_path.suffix + '.enc')
            
            with open(backup_path, 'rb') as f_in:
                data = f_in.read()
                encrypted_data = self.cipher.encrypt(data)
                
            with open(encrypted_path, 'wb') as f_out:
                f_out.write(encrypted_data)
            
            self.logger.info(f"备份文件加密完成: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            self.logger.error(f"加密备份文件失败: {e}")
            return None
    
    def _upload_to_s3(self, backup_path: Path) -> bool:
        """上传备份到 S3"""
        try:
            s3_key = f"database-backups/{backup_path.name}"
            
            self.s3_client.upload_file(
                str(backup_path),
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            self.logger.info(f"备份文件已上传到 S3: s3://{self.config.s3_bucket}/{s3_key}")
            return True
            
        except ClientError as e:
            self.logger.error(f"上传到 S3 失败: {e}")
            return False
    
    def _record_backup_info(self, backup_path: Path, backup_type: str):
        """记录备份信息"""
        info_file = self.backup_dir / 'backup_info.json'
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'filename': backup_path.name,
            'path': str(backup_path),
            'type': backup_type,
            'size': backup_path.stat().st_size,
            'compressed': self.config.compression,
            'encrypted': self.config.encryption,
            's3_uploaded': bool(self.s3_client)
        }
        
        # 读取现有信息
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                all_backups = json.load(f)
        else:
            all_backups = []
        
        # 添加新备份信息
        all_backups.append(backup_info)
        
        # 保存信息
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(all_backups, f, indent=2, ensure_ascii=False)
    
    def cleanup_old_backups(self):
        """清理过期备份"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        try:
            # 清理本地备份
            for backup_file in self.backup_dir.glob('*.sql*'):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    self.logger.info(f"删除过期备份: {backup_file}")
            
            # 清理 S3 备份
            if self.s3_client:
                self._cleanup_s3_backups(cutoff_date)
                
        except Exception as e:
            self.logger.error(f"清理过期备份失败: {e}")
    
    def _cleanup_s3_backups(self, cutoff_date: datetime):
        """清理 S3 中的过期备份"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix='database-backups/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.config.s3_bucket,
                            Key=obj['Key']
                        )
                        self.logger.info(f"删除 S3 过期备份: {obj['Key']}")
                        
        except ClientError as e:
            self.logger.error(f"清理 S3 过期备份失败: {e}")
    
    def restore_backup(self, backup_path: str, target_db: Optional[str] = None) -> bool:
        """恢复数据库备份"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            self.logger.error(f"备份文件不存在: {backup_path}")
            return False
        
        try:
            # 解密文件（如果需要）
            if backup_file.suffix == '.enc':
                backup_file = self._decrypt_backup(backup_file)
                if not backup_file:
                    return False
            
            # 解压文件（如果需要）
            if backup_file.suffix == '.gz':
                backup_file = self._decompress_backup(backup_file)
                if not backup_file:
                    return False
            
            # 执行恢复
            db_name = target_db or self.config.db_name
            
            cmd = [
                'psql',
                f'--host={self.config.db_host}',
                f'--port={self.config.db_port}',
                f'--username={self.config.db_user}',
                f'--dbname={db_name}',
                f'--file={backup_file}'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"恢复失败: {result.stderr}")
                return False
            
            self.logger.info(f"数据库恢复成功: {db_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复过程中发生错误: {e}")
            return False
    
    def _decrypt_backup(self, encrypted_path: Path) -> Optional[Path]:
        """解密备份文件"""
        if not self.cipher:
            self.logger.error("未配置加密密钥")
            return None
        
        try:
            decrypted_path = encrypted_path.with_suffix('')
            
            with open(encrypted_path, 'rb') as f_in:
                encrypted_data = f_in.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(decrypted_path, 'wb') as f_out:
                f_out.write(decrypted_data)
            
            return decrypted_path
            
        except Exception as e:
            self.logger.error(f"解密备份文件失败: {e}")
            return None
    
    def _decompress_backup(self, compressed_path: Path) -> Optional[Path]:
        """解压备份文件"""
        try:
            decompressed_path = compressed_path.with_suffix('')
            
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
            
        except Exception as e:
            self.logger.error(f"解压备份文件失败: {e}")
            return None
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        info_file = self.backup_dir / 'backup_info.json'
        
        if not info_file.exists():
            return []
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取备份信息失败: {e}")
            return []
    
    def verify_backup(self, backup_path: str) -> bool:
        """验证备份文件完整性"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return False
        
        try:
            # 简单的文件完整性检查
            if backup_file.suffix == '.sql':
                with open(backup_file, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # 读取前1KB
                    return 'PostgreSQL database dump' in content
            
            return True
            
        except Exception:
            return False


def load_config(config_file: str) -> BackupConfig:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    return BackupConfig(**config_data)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CHS 数据库备份工具')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--action', choices=['backup', 'restore', 'list', 'cleanup', 'verify'], 
                       default='backup', help='操作类型')
    parser.add_argument('--type', choices=['full', 'schema', 'data'], 
                       default='full', help='备份类型')
    parser.add_argument('--file', help='备份文件路径（用于恢复和验证）')
    parser.add_argument('--target-db', help='目标数据库名称（用于恢复）')
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        backup_manager = DatabaseBackup(config)
        
        if args.action == 'backup':
            if not backup_manager.test_connection():
                sys.exit(1)
            
            backup_path = backup_manager.create_backup(args.type)
            if backup_path:
                print(f"备份成功: {backup_path}")
            else:
                sys.exit(1)
                
        elif args.action == 'restore':
            if not args.file:
                print("错误: 恢复操作需要指定备份文件")
                sys.exit(1)
            
            success = backup_manager.restore_backup(args.file, args.target_db)
            if not success:
                sys.exit(1)
                
        elif args.action == 'list':
            backups = backup_manager.list_backups()
            for backup in backups:
                print(f"{backup['timestamp']} - {backup['filename']} ({backup['type']})")
                
        elif args.action == 'cleanup':
            backup_manager.cleanup_old_backups()
            print("清理完成")
            
        elif args.action == 'verify':
            if not args.file:
                print("错误: 验证操作需要指定备份文件")
                sys.exit(1)
            
            is_valid = backup_manager.verify_backup(args.file)
            print(f"备份文件验证: {'通过' if is_valid else '失败'}")
            if not is_valid:
                sys.exit(1)
                
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()