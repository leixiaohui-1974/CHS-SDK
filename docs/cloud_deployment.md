# CHS-SDK 云原生部署指南

本文档详细介绍了如何将 CHS-SDK 部署到云原生环境，包括 Docker 容器化、Kubernetes 编排和阿里云集成。

## 目录

- [概述](#概述)
- [Docker 部署](#docker-部署)
- [Kubernetes 部署](#kubernetes-部署)
- [阿里云部署](#阿里云部署)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

## 概述

CHS-SDK 支持多种云原生部署方式：

- **Docker Compose**: 适用于开发和测试环境
- **Kubernetes**: 适用于生产环境的容器编排
- **阿里云**: 集成阿里云服务的完整解决方案

### 架构组件

- **API 服务**: FastAPI 应用，提供 REST API 和 WebSocket 服务
- **数据库**: PostgreSQL 数据库
- **缓存**: Redis 缓存服务
- **监控**: Prometheus + Grafana 监控栈
- **日志**: ELK Stack 日志管理
- **负载均衡**: Nginx 反向代理

## Docker 部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存

### 快速开始

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd CHS-SDK
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置必要的环境变量
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **验证部署**
   ```bash
   curl http://localhost:8000/api/monitor/health
   ```

### 服务配置

#### API 服务
- **端口**: 8000
- **健康检查**: `/api/monitor/health`
- **WebSocket**: `/ws/monitor`

#### 数据库
- **端口**: 5432
- **数据库**: chs_sdk
- **持久化**: `postgres_data` 卷

#### Redis
- **端口**: 6379
- **持久化**: `redis_data` 卷

### 环境变量配置

```bash
# 应用配置
APP_NAME=CHS-SDK
APP_VERSION=1.0.0
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://chs_user:chs_password@postgres:5432/chs_sdk

# Redis 配置
REDIS_URL=redis://redis:6379/0

# WebSocket 监控
WEBSOCKET_MONITOR_ENABLED=true
MONITOR_INTERVAL=1.0
MAX_HISTORY_SIZE=1000
```

## Kubernetes 部署

### 前置要求

- Kubernetes 1.20+
- kubectl 配置正确
- 至少 8GB 可用内存
- 持久卷支持

### 部署步骤

1. **创建命名空间**
   ```bash
   kubectl apply -f k8s/aliyun-deployment.yaml
   ```

2. **验证部署**
   ```bash
   kubectl get pods -n chs-sdk
   kubectl get services -n chs-sdk
   ```

3. **访问服务**
   ```bash
   kubectl port-forward -n chs-sdk service/chs-api 8000:8000
   ```

### 资源配置

#### API 服务
- **副本数**: 3
- **CPU 请求**: 500m
- **内存请求**: 1Gi
- **CPU 限制**: 2
- **内存限制**: 4Gi

#### 数据库
- **副本数**: 1
- **存储**: 20Gi PVC
- **CPU 请求**: 1
- **内存请求**: 2Gi

#### 自动扩缩容
- **最小副本**: 2
- **最大副本**: 10
- **CPU 阈值**: 70%
- **内存阈值**: 80%

### 配置管理

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chs-config
  namespace: chs-sdk
data:
  APP_NAME: "CHS-SDK"
  DEBUG: "false"
  WEBSOCKET_MONITOR_ENABLED: "true"
  MONITOR_INTERVAL: "1.0"
```

## 阿里云部署

### 前置要求

- 阿里云账号
- 已配置 AccessKey
- 阿里云 CLI 工具
- Docker 镜像仓库

### 环境配置

1. **配置阿里云环境变量**
   ```bash
   cp .env.aliyun .env
   # 编辑 .env 文件，填入实际的阿里云配置
   ```

2. **阿里云服务配置**
   ```bash
   # ECS 实例
   ALIYUN_ECS_INSTANCE_TYPE=ecs.c6.large
   ALIYUN_ECS_IMAGE_ID=centos_7_9_x64_20G_alibase_20210318.vhd
   
   # RDS 数据库
   ALIYUN_RDS_INSTANCE_CLASS=rds.mysql.s2.large
   ALIYUN_RDS_ENGINE=MySQL
   ALIYUN_RDS_ENGINE_VERSION=8.0
   
   # SLB 负载均衡
   ALIYUN_SLB_INSTANCE_SPEC=slb.s2.small
   ```

### 自动化部署

1. **运行部署脚本**
   ```bash
   chmod +x scripts/deploy_aliyun.sh
   ./scripts/deploy_aliyun.sh
   ```

2. **部署流程**
   - 构建 Docker 镜像
   - 推送到阿里云容器镜像服务
   - 创建 ECS 实例
   - 配置 RDS 数据库
   - 设置 SLB 负载均衡
   - 部署应用服务

### 阿里云服务集成

#### ECS 实例管理
```python
from api.services.aliyun_service import get_aliyun_service

# 获取实例列表
service = get_aliyun_service()
instances = await service.list_instances()

# 创建新实例
instance_id = await service.create_instance(
    instance_type="ecs.c6.large",
    image_id="centos_7_9_x64_20G_alibase_20210318.vhd"
)
```

#### OSS 对象存储
```python
from api.services.aliyun_service import get_aliyun_oss_service

# 上传文件
oss_service = get_aliyun_oss_service()
result = await oss_service.upload_file(
    bucket_name="chs-sdk-storage",
    object_name="data/simulation_result.json",
    file_path="/tmp/result.json"
)
```

## 监控和日志

### Prometheus 监控

- **访问地址**: http://localhost:9090
- **指标收集**: API 性能、系统资源、业务指标
- **告警规则**: CPU、内存、磁盘使用率

### Grafana 可视化

- **访问地址**: http://localhost:3000
- **默认账号**: admin/admin
- **仪表板**: 系统监控、应用性能、业务指标

### ELK 日志管理

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **日志收集**: 应用日志、系统日志、访问日志

### WebSocket 实时监控

```javascript
// 连接 WebSocket 监控
const ws = new WebSocket('ws://localhost:8000/ws/monitor');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('监控数据:', data);
};
```

## 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看容器日志
docker-compose logs api

# 检查容器状态
docker-compose ps
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres
```

#### 3. Redis 连接失败
```bash
# 测试 Redis 连接
docker-compose exec redis redis-cli ping

# 查看 Redis 日志
docker-compose logs redis
```

#### 4. Kubernetes Pod 异常
```bash
# 查看 Pod 状态
kubectl get pods -n chs-sdk

# 查看 Pod 日志
kubectl logs -n chs-sdk deployment/chs-api

# 描述 Pod 详情
kubectl describe pod -n chs-sdk <pod-name>
```

### 性能优化

#### 1. 资源调优
- 根据实际负载调整 CPU 和内存限制
- 配置合适的副本数量
- 使用 HPA 自动扩缩容

#### 2. 数据库优化
- 配置连接池
- 优化查询语句
- 设置合适的索引

#### 3. 缓存策略
- 使用 Redis 缓存热点数据
- 配置合适的过期时间
- 实现缓存预热

### 安全配置

#### 1. 网络安全
- 配置防火墙规则
- 使用 HTTPS/TLS 加密
- 限制访问来源

#### 2. 认证授权
- 配置 JWT 认证
- 实现 RBAC 权限控制
- 定期轮换密钥

#### 3. 数据安全
- 加密敏感数据
- 定期备份数据
- 配置访问审计

## 维护和更新

### 版本更新

1. **构建新镜像**
   ```bash
   docker build -t chs-sdk:v1.1.0 .
   ```

2. **滚动更新**
   ```bash
   kubectl set image deployment/chs-api -n chs-sdk chs-api=chs-sdk:v1.1.0
   ```

3. **验证更新**
   ```bash
   kubectl rollout status deployment/chs-api -n chs-sdk
   ```

### 备份恢复

1. **数据库备份**
   ```bash
   kubectl exec -n chs-sdk deployment/postgres -- pg_dump -U chs_user chs_sdk > backup.sql
   ```

2. **配置备份**
   ```bash
   kubectl get configmap -n chs-sdk -o yaml > configmap-backup.yaml
   ```

### 监控告警

配置 Prometheus 告警规则，及时发现和处理问题：

```yaml
groups:
- name: chs-sdk-alerts
  rules:
  - alert: HighCPUUsage
    expr: cpu_usage_percent > 80
    for: 5m
    annotations:
      summary: "CPU 使用率过高"
      description: "{{ $labels.instance }} CPU 使用率超过 80%"
```

## 联系支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的 GitHub Issues
3. 联系技术支持团队

---

**注意**: 本文档会随着项目更新而持续维护，请定期查看最新版本。