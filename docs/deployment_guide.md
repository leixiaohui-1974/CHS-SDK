# CHS仿真平台部署指南

## 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [环境准备](#环境准备)
4. [本地开发部署](#本地开发部署)
5. [Docker部署](#docker部署)
6. [Kubernetes部署](#kubernetes部署)
7. [生产环境部署](#生产环境部署)
8. [监控和日志](#监控和日志)
9. [备份和恢复](#备份和恢复)
10. [故障排除](#故障排除)
11. [性能优化](#性能优化)
12. [安全配置](#安全配置)

## 概述

### 部署架构

CHS仿真平台采用微服务架构，支持多种部署方式：

- **本地开发**: 适用于开发和测试
- **Docker Compose**: 适用于小规模部署和演示
- **Kubernetes**: 适用于生产环境和大规模部署
- **云原生**: 支持AWS、Azure、GCP等云平台

### 部署策略

- **蓝绿部署**: 零停机时间部署
- **滚动更新**: 渐进式更新
- **金丝雀发布**: 风险控制发布
- **A/B测试**: 功能验证发布

## 系统要求

### 最小配置

#### 开发环境
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **网络**: 100Mbps

#### 生产环境
- **CPU**: 16核心
- **内存**: 32GB RAM
- **存储**: 500GB SSD
- **网络**: 1Gbps

### 推荐配置

#### 高性能生产环境
- **CPU**: 32核心
- **内存**: 128GB RAM
- **存储**: 2TB NVMe SSD
- **网络**: 10Gbps
- **GPU**: NVIDIA Tesla V100 (可选)

### 软件要求

#### 基础软件
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.24+
- **Helm**: 3.8+

#### 数据库
- **PostgreSQL**: 14+
- **Redis**: 7.0+
- **Elasticsearch**: 8.0+
- **InfluxDB**: 2.0+

#### 存储
- **MinIO**: 2023+
- **NFS**: 4.0+ (可选)
- **Ceph**: 16+ (可选)

## 环境准备

### 1. 系统初始化

```bash
#!/bin/bash
# 系统初始化脚本

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 配置时区
sudo timedatectl set-timezone Asia/Shanghai

# 配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp

# 优化内核参数
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
echo 'fs.file-max=65536' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

echo "系统初始化完成"
```

### 2. Docker安装

```bash
#!/bin/bash
# Docker安装脚本

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker compose version

echo "Docker安装完成"
```

### 3. Kubernetes安装

```bash
#!/bin/bash
# Kubernetes安装脚本 (使用kubeadm)

# 禁用swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# 安装容器运行时
sudo apt update
sudo apt install -y containerd

# 配置containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

# 添加Kubernetes仓库
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# 安装kubeadm、kubelet、kubectl
sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# 启动kubelet
sudo systemctl enable kubelet

echo "Kubernetes组件安装完成"
```

## 本地开发部署

### 1. 克隆代码

```bash
# 克隆项目代码
git clone https://github.com/your-org/chs-platform.git
cd chs-platform

# 检出开发分支
git checkout develop
```

### 2. 环境配置

```bash
# 复制环境配置文件
cp .env.example .env.local

# 编辑配置文件
vim .env.local
```

**.env.local示例**:

```bash
# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://chs_user:chs_password@localhost:5432/chs_dev
REDIS_URL=redis://localhost:6379/0

# 存储配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=chs-dev

# 认证配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
```

### 3. 启动开发环境

```bash
# 启动基础服务
docker compose -f docker-compose.dev.yml up -d postgres redis minio

# 等待服务启动
sleep 30

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端服务 (新终端)
cd frontend
npm install
npm run dev
```

### 4. 验证部署

```bash
# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:3000

# 检查数据库连接
psql postgresql://chs_user:chs_password@localhost:5432/chs_dev -c "SELECT version();"

# 检查Redis连接
redis-cli ping

# 检查MinIO连接
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local
```

## Docker部署

### 1. 构建镜像

```bash
# 构建后端镜像
docker build -t chs-platform/api:latest -f backend/Dockerfile backend/

# 构建前端镜像
docker build -t chs-platform/frontend:latest -f frontend/Dockerfile frontend/

# 验证镜像
docker images | grep chs-platform
```

### 2. Docker Compose部署

**docker-compose.prod.yml**:

```yaml
version: '3.8'

services:
  # 数据库服务
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chs_production
      POSTGRES_USER: chs_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chs_user -d chs_production"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 对象存储
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # API服务
  api:
    image: chs-platform/api:latest
    environment:
      APP_ENV: production
      DATABASE_URL: postgresql://chs_user:${POSTGRES_PASSWORD}@postgres:5432/chs_production
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  # 前端服务
  frontend:
    image: chs-platform/frontend:latest
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_WS_URL: ws://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  default:
    driver: bridge
```

### 3. 启动生产环境

```bash
# 设置环境变量
export POSTGRES_PASSWORD=your-secure-password
export REDIS_PASSWORD=your-redis-password
export MINIO_ACCESS_KEY=your-minio-access-key
export MINIO_SECRET_KEY=your-minio-secret-key
export JWT_SECRET_KEY=your-jwt-secret-key

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

## Kubernetes部署

### 1. 创建命名空间

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chs-platform
  labels:
    name: chs-platform
    environment: production
```

### 2. 配置Secret

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: chs-secrets
  namespace: chs-platform
type: Opaque
data:
  postgres-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  minio-access-key: <base64-encoded-access-key>
  minio-secret-key: <base64-encoded-secret-key>
  jwt-secret-key: <base64-encoded-jwt-secret>
```

### 3. 配置ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chs-config
  namespace: chs-platform
data:
  app-env: "production"
  log-level: "INFO"
  database-host: "postgres-service"
  database-name: "chs_production"
  redis-host: "redis-service"
  minio-endpoint: "minio-service:9000"
  minio-bucket: "chs-production"
```

### 4. 部署数据库

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: chs-platform
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "chs_production"
        - name: POSTGRES_USER
          value: "chs_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: chs-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - chs_user
            - -d
            - chs_production
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - chs_user
            - -d
            - chs_production
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: chs-platform
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### 5. 部署API服务

```yaml
# api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chs-api
  namespace: chs-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: chs-api
  template:
    metadata:
      labels:
        app: chs-api
    spec:
      containers:
      - name: api
        image: chs-platform/api:v1.0.0
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: chs-config
              key: app-env
        - name: DATABASE_URL
          value: "postgresql://chs_user:$(POSTGRES_PASSWORD)@$(DATABASE_HOST):5432/$(DATABASE_NAME)"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: chs-secrets
              key: postgres-password
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: chs-config
              key: database-host
        - name: DATABASE_NAME
          valueFrom:
            configMapKeyRef:
              name: chs-config
              key: database-name
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: chs-api-service
  namespace: chs-platform
spec:
  selector:
    app: chs-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chs-api-hpa
  namespace: chs-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chs-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 6. 配置Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chs-ingress
  namespace: chs-platform
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - api.chs-platform.com
    - app.chs-platform.com
    secretName: chs-tls-secret
  rules:
  - host: api.chs-platform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chs-api-service
            port:
              number: 80
  - host: app.chs-platform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chs-frontend-service
            port:
              number: 80
```

### 7. 部署脚本

```bash
#!/bin/bash
# deploy.sh - Kubernetes部署脚本

set -e

# 配置变量
NAMESPACE="chs-platform"
IMAGE_TAG="v1.0.0"

echo "开始部署CHS仿真平台到Kubernetes..."

# 创建命名空间
echo "创建命名空间..."
kubectl apply -f k8s/namespace.yaml

# 创建Secret
echo "创建Secret..."
kubectl apply -f k8s/secrets.yaml

# 创建ConfigMap
echo "创建ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# 部署数据库
echo "部署PostgreSQL..."
kubectl apply -f k8s/postgres.yaml

# 等待数据库就绪
echo "等待PostgreSQL就绪..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

# 部署Redis
echo "部署Redis..."
kubectl apply -f k8s/redis.yaml

# 等待Redis就绪
echo "等待Redis就绪..."
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

# 部署MinIO
echo "部署MinIO..."
kubectl apply -f k8s/minio.yaml

# 等待MinIO就绪
echo "等待MinIO就绪..."
kubectl wait --for=condition=ready pod -l app=minio -n $NAMESPACE --timeout=300s

# 初始化数据库
echo "初始化数据库..."
kubectl run db-init --image=chs-platform/db-init:$IMAGE_TAG --rm -i --restart=Never -n $NAMESPACE

# 部署API服务
echo "部署API服务..."
kubectl apply -f k8s/api.yaml

# 等待API服务就绪
echo "等待API服务就绪..."
kubectl wait --for=condition=ready pod -l app=chs-api -n $NAMESPACE --timeout=300s

# 部署前端服务
echo "部署前端服务..."
kubectl apply -f k8s/frontend.yaml

# 等待前端服务就绪
echo "等待前端服务就绪..."
kubectl wait --for=condition=ready pod -l app=chs-frontend -n $NAMESPACE --timeout=300s

# 配置Ingress
echo "配置Ingress..."
kubectl apply -f k8s/ingress.yaml

# 验证部署
echo "验证部署状态..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

echo "部署完成！"
echo "API地址: https://api.chs-platform.com"
echo "前端地址: https://app.chs-platform.com"
```

## 生产环境部署

### 1. 高可用配置

#### 数据库高可用

```yaml
# postgres-ha.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: chs-platform
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
  
  bootstrap:
    initdb:
      database: chs_production
      owner: chs_user
      secret:
        name: postgres-credentials
  
  storage:
    size: 500Gi
    storageClass: fast-ssd
  
  monitoring:
    enabled: true
  
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: "s3://chs-backups/postgres"
      s3Credentials:
        accessKeyId:
          name: backup-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-credentials
          key: SECRET_ACCESS_KEY
      wal:
        retention: "5d"
      data:
        retention: "30d"
```

#### Redis高可用

```yaml
# redis-ha.yaml
apiVersion: databases.spotahome.com/v1
kind: RedisFailover
metadata:
  name: redis-cluster
  namespace: chs-platform
spec:
  sentinel:
    replicas: 3
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
  redis:
    replicas: 3
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
    storage:
      persistentVolumeClaim:
        metadata:
          name: redis-storage
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 50Gi
          storageClassName: fast-ssd
  auth:
    secretPath: redis-auth
```

### 2. 负载均衡配置

```yaml
# load-balancer.yaml
apiVersion: v1
kind: Service
metadata:
  name: chs-api-lb
  namespace: chs-platform
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: http
spec:
  type: LoadBalancer
  selector:
    app: chs-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 300
```

### 3. 自动扩缩容

```yaml
# vertical-pod-autoscaler.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: chs-api-vpa
  namespace: chs-platform
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chs-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

## 监控和日志

### 1. Prometheus监控

```yaml
# prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
  namespace: chs-platform
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      team: chs-platform
  ruleSelector:
    matchLabels:
      team: chs-platform
  resources:
    requests:
      memory: 400Mi
      cpu: 100m
    limits:
      memory: 2Gi
      cpu: 1000m
  retention: 30d
  storage:
    volumeClaimTemplate:
      spec:
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
  alerting:
    alertmanagers:
    - namespace: chs-platform
      name: alertmanager-main
      port: web
```

### 2. Grafana仪表板

```yaml
# grafana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: chs-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:9.3.0
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-credentials
              key: admin-password
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel,grafana-worldmap-panel"
        ports:
        - containerPort: 3000
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
        - name: grafana-config
          mountPath: /etc/grafana/grafana.ini
          subPath: grafana.ini
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc
      - name: grafana-config
        configMap:
          name: grafana-config
```

### 3. ELK日志聚合

```yaml
# elasticsearch.yaml
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: elasticsearch
  namespace: chs-platform
spec:
  version: 8.6.0
  nodeSets:
  - name: default
    count: 3
    config:
      node.store.allow_mmap: false
      xpack.security.enabled: true
      xpack.security.transport.ssl.enabled: true
      xpack.security.http.ssl.enabled: true
    podTemplate:
      spec:
        containers:
        - name: elasticsearch
          resources:
            requests:
              memory: 2Gi
              cpu: 500m
            limits:
              memory: 4Gi
              cpu: 1000m
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 200Gi
        storageClassName: fast-ssd
```

## 备份和恢复

### 1. 数据库备份

```bash
#!/bin/bash
# backup-database.sh

set -e

# 配置变量
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="chs_production_${DATE}.sql"
S3_BUCKET="chs-backups"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行数据库备份
echo "开始备份数据库..."
kubectl exec -n chs-platform postgres-0 -- pg_dump -U chs_user -d chs_production > $BACKUP_DIR/$BACKUP_FILE

# 压缩备份文件
echo "压缩备份文件..."
gzip $BACKUP_DIR/$BACKUP_FILE

# 上传到S3
echo "上传备份到S3..."
aws s3 cp $BACKUP_DIR/${BACKUP_FILE}.gz s3://$S3_BUCKET/postgres/

# 清理本地文件
rm $BACKUP_DIR/${BACKUP_FILE}.gz

# 清理旧备份 (保留30天)
aws s3 ls s3://$S3_BUCKET/postgres/ | while read -r line; do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "30 days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    if [[ $fileName != "" ]]; then
      aws s3 rm s3://$S3_BUCKET/postgres/$fileName
      echo "删除旧备份: $fileName"
    fi
  fi
done

echo "数据库备份完成: ${BACKUP_FILE}.gz"
```

### 2. 应用数据备份

```bash
#!/bin/bash
# backup-application.sh

set -e

# 配置变量
NAMESPACE="chs-platform"
BACKUP_DIR="/backups/application"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="chs-backups"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份Kubernetes配置
echo "备份Kubernetes配置..."
kubectl get all -n $NAMESPACE -o yaml > $BACKUP_DIR/k8s-config-${DATE}.yaml
kubectl get configmaps -n $NAMESPACE -o yaml > $BACKUP_DIR/configmaps-${DATE}.yaml
kubectl get secrets -n $NAMESPACE -o yaml > $BACKUP_DIR/secrets-${DATE}.yaml

# 备份持久卷数据
echo "备份MinIO数据..."
kubectl exec -n $NAMESPACE minio-0 -- tar czf - /data | gzip > $BACKUP_DIR/minio-data-${DATE}.tar.gz

# 创建备份清单
echo "创建备份清单..."
cat > $BACKUP_DIR/backup-manifest-${DATE}.txt << EOF
备份时间: $(date)
备份版本: $(kubectl get deployment chs-api -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
Kubernetes配置: k8s-config-${DATE}.yaml
ConfigMaps: configmaps-${DATE}.yaml
Secrets: secrets-${DATE}.yaml
MinIO数据: minio-data-${DATE}.tar.gz
EOF

# 压缩所有备份文件
echo "压缩备份文件..."
tar czf $BACKUP_DIR/chs-platform-backup-${DATE}.tar.gz -C $BACKUP_DIR .

# 上传到S3
echo "上传备份到S3..."
aws s3 cp $BACKUP_DIR/chs-platform-backup-${DATE}.tar.gz s3://$S3_BUCKET/application/

# 清理本地文件
rm -rf $BACKUP_DIR/*

echo "应用备份完成: chs-platform-backup-${DATE}.tar.gz"
```

### 3. 恢复脚本

```bash
#!/bin/bash
# restore.sh

set -e

# 参数检查
if [ $# -ne 1 ]; then
    echo "用法: $0 <backup-date>"
    echo "示例: $0 20240120_143000"
    exit 1
fi

BACKUP_DATE=$1
NAMESPACE="chs-platform"
RESTORE_DIR="/restore"
S3_BUCKET="chs-backups"

echo "开始恢复CHS平台 (备份日期: $BACKUP_DATE)..."

# 创建恢复目录
mkdir -p $RESTORE_DIR

# 下载备份文件
echo "下载备份文件..."
aws s3 cp s3://$S3_BUCKET/application/chs-platform-backup-${BACKUP_DATE}.tar.gz $RESTORE_DIR/
aws s3 cp s3://$S3_BUCKET/postgres/chs_production_${BACKUP_DATE}.sql.gz $RESTORE_DIR/

# 解压备份文件
echo "解压备份文件..."
tar xzf $RESTORE_DIR/chs-platform-backup-${BACKUP_DATE}.tar.gz -C $RESTORE_DIR/
gunzip $RESTORE_DIR/chs_production_${BACKUP_DATE}.sql.gz

# 停止应用服务
echo "停止应用服务..."
kubectl scale deployment chs-api --replicas=0 -n $NAMESPACE
kubectl scale deployment chs-frontend --replicas=0 -n $NAMESPACE

# 恢复数据库
echo "恢复数据库..."
kubectl exec -i -n $NAMESPACE postgres-0 -- psql -U chs_user -d chs_production < $RESTORE_DIR/chs_production_${BACKUP_DATE}.sql

# 恢复MinIO数据
echo "恢复MinIO数据..."
kubectl exec -i -n $NAMESPACE minio-0 -- tar xzf - -C / < $RESTORE_DIR/minio-data-${BACKUP_DATE}.tar.gz

# 重启服务
echo "重启服务..."
kubectl rollout restart deployment/chs-api -n $NAMESPACE
kubectl rollout restart deployment/chs-frontend -n $NAMESPACE

# 等待服务就绪
echo "等待服务就绪..."
kubectl rollout status deployment/chs-api -n $NAMESPACE
kubectl rollout status deployment/chs-frontend -n $NAMESPACE

# 验证恢复
echo "验证恢复状态..."
kubectl get pods -n $NAMESPACE

# 清理恢复文件
rm -rf $RESTORE_DIR

echo "恢复完成！"
```

## 故障排除

### 1. 常见问题诊断

```bash
#!/bin/bash
# diagnose.sh - 故障诊断脚本

NAMESPACE="chs-platform"

echo "=== CHS平台故障诊断 ==="
echo "时间: $(date)"
echo

# 检查Pod状态
echo "1. 检查Pod状态:"
kubectl get pods -n $NAMESPACE
echo

# 检查服务状态
echo "2. 检查服务状态:"
kubectl get services -n $NAMESPACE
echo

# 检查Ingress状态
echo "3. 检查Ingress状态:"
kubectl get ingress -n $NAMESPACE
echo

# 检查资源使用情况
echo "4. 检查资源使用情况:"
kubectl top pods -n $NAMESPACE
echo

# 检查事件
echo "5. 检查最近事件:"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
echo

# 检查API服务日志
echo "6. API服务日志 (最近50行):"
kubectl logs -n $NAMESPACE -l app=chs-api --tail=50
echo

# 检查数据库连接
echo "7. 检查数据库连接:"
kubectl exec -n $NAMESPACE postgres-0 -- pg_isready -U chs_user -d chs_production
echo

# 检查Redis连接
echo "8. 检查Redis连接:"
kubectl exec -n $NAMESPACE redis-0 -- redis-cli ping
echo

# 检查MinIO连接
echo "9. 检查MinIO连接:"
kubectl exec -n $NAMESPACE minio-0 -- curl -f http://localhost:9000/minio/health/live
echo

# 检查磁盘空间
echo "10. 检查磁盘空间:"
kubectl exec -n $NAMESPACE postgres-0 -- df -h
echo

echo "=== 诊断完成 ==="
```

### 2. 性能问题排查

```bash
#!/bin/bash
# performance-check.sh

NAMESPACE="chs-platform"

echo "=== 性能问题排查 ==="

# 检查CPU使用率
echo "1. CPU使用率:"
kubectl top pods -n $NAMESPACE --sort-by=cpu
echo

# 检查内存使用率
echo "2. 内存使用率:"
kubectl top pods -n $NAMESPACE --sort-by=memory
echo

# 检查数据库性能
echo "3. 数据库性能:"
kubectl exec -n $NAMESPACE postgres-0 -- psql -U chs_user -d chs_production -c "
  SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
  FROM pg_stat_statements 
  ORDER BY total_time DESC 
  LIMIT 10;
"
echo

# 检查慢查询
echo "4. 慢查询日志:"
kubectl exec -n $NAMESPACE postgres-0 -- tail -20 /var/log/postgresql/postgresql-*.log | grep "slow query"
echo

# 检查Redis性能
echo "5. Redis性能:"
kubectl exec -n $NAMESPACE redis-0 -- redis-cli info stats
echo

# 检查网络延迟
echo "6. 网络延迟测试:"
kubectl run network-test --image=busybox --rm -i --restart=Never -n $NAMESPACE -- ping -c 5 chs-api-service
echo

echo "=== 排查完成 ==="
```

## 性能优化

### 1. 数据库优化

```sql
-- database-optimization.sql
-- 数据库性能优化配置

-- 创建索引
CREATE INDEX CONCURRENTLY idx_simulations_user_id ON simulations(user_id);
CREATE INDEX CONCURRENTLY idx_simulations_status ON simulations(status);
CREATE INDEX CONCURRENTLY idx_simulations_created_at ON simulations(created_at);
CREATE INDEX CONCURRENTLY idx_simulation_results_sim_id ON simulation_results(simulation_id);
CREATE INDEX CONCURRENTLY idx_files_user_id ON files(user_id);
CREATE INDEX CONCURRENTLY idx_files_type ON files(file_type);

-- 分区表设置
CREATE TABLE simulation_logs_y2024m01 PARTITION OF simulation_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE simulation_logs_y2024m02 PARTITION OF simulation_logs
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 统计信息更新
ANALYZE;

-- 清理无用数据
VACUUM ANALYZE;
```

### 2. 缓存优化

```python
# cache-optimization.py
# 缓存优化配置

from redis import Redis
from typing import Optional, Any
import json
import pickle

class OptimizedCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1小时
    
    async def get_or_set(self, 
                        key: str, 
                        fetch_func: callable, 
                        ttl: Optional[int] = None) -> Any:
        """
        获取缓存或设置缓存
        """
        # 尝试从缓存获取
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 缓存未命中，获取数据
        value = await fetch_func()
        
        # 设置缓存
        await self.set(key, value, ttl or self.default_ttl)
        
        return value
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        """
        try:
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"缓存获取失败: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        设置缓存值
        """
        try:
            data = pickle.dumps(value)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """
        批量删除匹配模式的缓存
        """
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# 缓存策略配置
CACHE_STRATEGIES = {
    'user_info': {'ttl': 1800, 'pattern': 'user:*'},
    'simulation_list': {'ttl': 300, 'pattern': 'sim_list:*'},
    'simulation_status': {'ttl': 60, 'pattern': 'sim_status:*'},
    'file_metadata': {'ttl': 3600, 'pattern': 'file:*'},
    'system_config': {'ttl': 7200, 'pattern': 'config:*'}
}
```

### 3. 应用优化

```python
# app-optimization.py
# 应用性能优化

from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
from typing import List

# 连接池优化
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 异步任务优化
class TaskManager:
    def __init__(self):
        self.task_queue = asyncio.Queue(maxsize=1000)
        self.workers = []
        self.running = False
    
    async def start_workers(self, worker_count: int = 5):
        """
        启动工作进程
        """
        self.running = True
        for i in range(worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop_workers(self):
        """
        停止工作进程
        """
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, name: str):
        """
        工作进程
        """
        while self.running:
            try:
                task_func, args, kwargs = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
                await task_func(*args, **kwargs)
                self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"任务执行失败 ({name}): {e}")
    
    async def submit_task(self, func, *args, **kwargs):
        """
        提交任务
        """
        await self.task_queue.put((func, args, kwargs))

# 批量操作优化
class BatchProcessor:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_items = []
    
    async def add_item(self, item):
        """
        添加待处理项
        """
        self.pending_items.append(item)
        if len(self.pending_items) >= self.batch_size:
            await self.flush()
    
    async def flush(self):
        """
        批量处理
        """
        if not self.pending_items:
            return
        
        items = self.pending_items.copy()
        self.pending_items.clear()
        
        await self._process_batch(items)
    
    async def _process_batch(self, items: List):
        """
        批量处理逻辑
        """
        # 实现具体的批量处理逻辑
        pass
```

## 安全配置

### 1. 网络安全

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chs-network-policy
  namespace: chs-platform
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: chs-platform
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: chs-platform
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
    - protocol: TCP
      port: 9000
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
```

### 2. Pod安全策略

```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: chs-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 3. RBAC配置

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chs-service-account
  namespace: chs-platform
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: chs-platform
  name: chs-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: chs-role-binding
  namespace: chs-platform
subjects:
- kind: ServiceAccount
  name: chs-service-account
  namespace: chs-platform
roleRef:
  kind: Role
  name: chs-role
  apiGroup: rbac.authorization.k8s.io
```

---

**文档版本**: v1.0.0  
**创建时间**: 2024年1月20日  
**维护团队**: CHS平台运维团队  
**审核状态**: 已审核

> 本部署指南提供了CHS仿真平台在不同环境下的完整部署方案，包括开发、测试和生产环境的配置。请根据实际需求选择合适的部署方式，并严格按照安全要求进行配置。