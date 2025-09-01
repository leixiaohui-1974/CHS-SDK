# CHS仿真平台备份恢复系统

## 概述

CHS仿真平台备份恢复系统提供了完整的数据保护和灾难恢复解决方案，包括：

- **自动化备份调度**：支持定时备份、增量备份和完整备份
- **数据库备份**：PostgreSQL数据库的自动备份和恢复
- **文件备份**：用户上传文件和仿真结果的备份同步
- **灾难恢复**：系统完整恢复和数据迁移
- **云存储集成**：支持S3兼容的对象存储
- **加密和压缩**：数据安全和存储优化
- **监控和告警**：备份状态监控和失败通知

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   备份调度器     │    │   数据库备份     │    │   文件备份       │
│  (Scheduler)    │    │  (Database)     │    │   (Files)       │
│                 │    │                 │    │                 │
│ - 任务调度       │    │ - PostgreSQL    │    │ - 用户文件       │
│ - 状态监控       │    │ - 增量备份       │    │ - 仿真结果       │
│ - 通知发送       │    │ - 压缩加密       │    │ - 实时同步       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   灾难恢复       │
                    │  (Recovery)     │
                    │                 │
                    │ - 系统恢复       │
                    │ - 数据迁移       │
                    │ - 服务重建       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   云存储         │
                    │   (S3/MinIO)    │
                    │                 │
                    │ - 远程备份       │
                    │ - 长期存储       │
                    │ - 多地域复制     │
                    └─────────────────┘
```

## 快速开始

### 1. 环境准备

确保已安装以下依赖：
- Docker 和 Docker Compose
- PostgreSQL 客户端工具
- Python 3.11+

### 2. 配置环境变量

复制并编辑环境变量文件：

```bash
cp .env.example .env
```

必需的环境变量：

```bash
# 数据库配置
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=chs_platform
POSTGRES_USER=chs_user

# S3存储配置（可选）
S3_BACKUP_BUCKET=chs-backups
S3_REGION=us-east-1
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_ENDPOINT=https://s3.amazonaws.com

# 通知配置（可选）
BACKUP_NOTIFICATION_WEBHOOK=https://your-webhook-url
```

### 3. 启动备份系统

使用启动脚本：

```bash
# 启动完整备份系统
./scripts/backup/start_backup_system.sh start

# 查看服务状态
./scripts/backup/start_backup_system.sh status

# 查看日志
./scripts/backup/start_backup_system.sh logs
```

或使用Docker Compose：

```bash
# 启动备份调度器
docker-compose -f docker-compose.backup.yml up -d backup-scheduler

# 查看服务状态
docker-compose -f docker-compose.backup.yml ps
```

## 配置说明

### 备份调度器配置

配置文件：`config/backup/scheduler_config.json`

```json
{
  "jobs": [
    {
      "name": "daily_database_backup",
      "type": "database",
      "schedule": "02:00",
      "config_file": "config/backup/database_backup.json",
      "enabled": true,
      "retention_policy": "30_days",
      "priority": 1
    }
  ],
  "max_concurrent_jobs": 2,
  "log_level": "INFO"
}
```

支持的调度格式：
- `"02:00"` - 每天凌晨2点
- `"every 6 hours"` - 每6小时
- `"weekly"` - 每周
- `"monthly"` - 每月

### 数据库备份配置

配置文件：`config/backup/database_backup.json`

```json
{
  "database": {
    "host": "${POSTGRES_HOST}",
    "port": 5432,
    "database": "${POSTGRES_DB}",
    "username": "${POSTGRES_USER}",
    "password": "${POSTGRES_PASSWORD}"
  },
  "backup_directory": "/app/backups/database",
  "retention_days": 30,
  "compression": {
    "enabled": true,
    "algorithm": "gzip",
    "level": 6
  },
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM"
  }
}
```

### 文件备份配置

配置文件：`config/backup/file_backup.json`

```json
{
  "source_directories": [
    "/app/data/uploads",
    "/app/data/simulation_results"
  ],
  "backup_directory": "/app/backups/files",
  "sync_interval": 3600,
  "exclude_patterns": [
    "*.tmp",
    "*.log",
    "*/.git/*"
  ]
}
```

## 使用指南

### 手动执行备份

```bash
# 数据库备份
./scripts/backup/start_backup_system.sh backup db

# 文件备份
./scripts/backup/start_backup_system.sh backup files

# 完整备份
./scripts/backup/start_backup_system.sh backup full
```

### 数据恢复

```bash
# 恢复数据库
python scripts/backup/database_backup.py \
  --config config/backup/database_backup.json \
  --restore /path/to/backup.sql.gz

# 恢复文件
python scripts/backup/file_backup.py \
  --config config/backup/file_backup.json \
  --restore /path/to/backup

# 灾难恢复
python scripts/backup/disaster_recovery.py \
  --config config/backup/disaster_recovery.yaml \
  --recover --backup-path /path/to/full/backup
```

### 备份验证

```bash
# 验证数据库备份
python scripts/backup/database_backup.py \
  --config config/backup/database_backup.json \
  --verify /path/to/backup.sql.gz

# 验证文件备份
python scripts/backup/file_backup.py \
  --config config/backup/file_backup.json \
  --verify /path/to/backup
```

## 监控和告警

### 健康检查

备份调度器提供健康检查端点：

```bash
# 检查服务状态
curl http://localhost:8080/health

# 获取备份统计
curl http://localhost:8080/stats

# 查看任务状态
curl http://localhost:8080/jobs
```

### 日志监控

日志文件位置：
- 备份调度器：`/app/logs/backup_scheduler.log`
- 数据库备份：`/app/logs/database_backup.log`
- 文件备份：`/app/logs/file_backup.log`
- 灾难恢复：`/app/logs/disaster_recovery.log`

### 通知配置

支持多种通知方式：

```json
{
  "notification": {
    "webhook": "https://your-webhook-url",
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "from_email": "backup@chs-platform.com",
      "to_emails": ["admin@chs-platform.com"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#backups"
    }
  }
}
```

## 故障排除

### 常见问题

1. **备份失败**
   ```bash
   # 检查日志
   docker-compose -f docker-compose.backup.yml logs backup-scheduler
   
   # 检查磁盘空间
   df -h
   
   # 检查数据库连接
   docker-compose -f docker-compose.backup.yml exec backup-scheduler \
     pg_isready -h postgres -p 5432
   ```

2. **S3上传失败**
   ```bash
   # 检查S3配置
   docker-compose -f docker-compose.backup.yml exec backup-scheduler \
     python -c "import boto3; print(boto3.client('s3').list_buckets())"
   ```

3. **恢复失败**
   ```bash
   # 检查备份文件完整性
   python scripts/backup/database_backup.py \
     --config config/backup/database_backup.json \
     --verify /path/to/backup.sql.gz
   ```

### 性能优化

1. **并行备份**
   - 调整 `max_concurrent_jobs` 参数
   - 使用 `parallel_uploads` 加速S3上传

2. **压缩优化**
   - 调整压缩级别平衡速度和大小
   - 对大文件使用流式压缩

3. **网络优化**
   - 设置 `bandwidth_limit_mbps` 限制带宽使用
   - 使用 `multipart_upload` 提高大文件上传效率

## 安全考虑

1. **加密**
   - 所有备份文件都使用AES-256-GCM加密
   - 加密密钥存储在安全位置
   - 定期轮换加密密钥

2. **访问控制**
   - 备份文件权限限制
   - S3存储桶访问策略
   - 审计日志记录

3. **网络安全**
   - 使用HTTPS传输
   - VPN或专线连接云存储
   - 防火墙规则配置

## 最佳实践

1. **备份策略**
   - 3-2-1备份原则：3份副本，2种介质，1份异地
   - 定期测试恢复流程
   - 监控备份成功率和完整性

2. **存储管理**
   - 合理设置保留策略
   - 定期清理过期备份
   - 监控存储使用量

3. **灾难恢复**
   - 制定详细的恢复计划
   - 定期进行恢复演练
   - 文档化恢复流程

## API参考

### 备份调度器API

```bash
# 获取所有任务状态
GET /api/jobs

# 手动运行任务
POST /api/jobs/{job_name}/run

# 启用/禁用任务
PUT /api/jobs/{job_name}/enable
PUT /api/jobs/{job_name}/disable

# 获取备份统计
GET /api/stats

# 健康检查
GET /health
```

### 响应示例

```json
{
  "jobs": [
    {
      "name": "daily_database_backup",
      "status": "completed",
      "last_run": "2024-01-15T02:00:00Z",
      "next_run": "2024-01-16T02:00:00Z",
      "success_rate": 0.95
    }
  ],
  "stats": {
    "total_backups": 150,
    "successful_backups": 143,
    "failed_backups": 7,
    "total_size": "2.5GB",
    "last_backup": "2024-01-15T02:00:00Z"
  }
}
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 支持

如有问题或建议，请提交Issue或联系开发团队。