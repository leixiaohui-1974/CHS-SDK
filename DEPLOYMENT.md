# CHS Simulation Platform - Deployment Guide

本指南提供了 CHS 仿真平台的完整部署说明，包括开发环境和生产环境的部署方式。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)
- [安全注意事项](#安全注意事项)

## 系统要求

### 最低要求
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+

### 推荐配置（生产环境）
- **CPU**: 4+ 核心
- **内存**: 8GB+ RAM
- **存储**: 100GB+ SSD
- **网络**: 稳定的互联网连接

### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+ (用于开发)
- **Node.js**: 18+ (用于前端开发)

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd CHS-SDK
```

### 2. 配置环境变量
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件（重要：修改默认密码和密钥）
nano .env
```

### 3. 启动服务
```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 4. 验证部署
```bash
# 运行部署验证脚本
python scripts/validate_deployment.py

# 检查 API 健康状态
curl http://localhost:8000/health
```

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Node.js** (v18+)
- **Python** (v3.11+)
- **kubectl** (v1.25+)
- **Helm** (v3.10+) - Optional but recommended

### Cloud Requirements

- **Kubernetes Cluster** (v1.25+)
- **Container Registry** (GitHub Container Registry, AWS ECR, etc.)
- **Persistent Storage** (AWS EBS, GCP Persistent Disk, etc.)
- **Load Balancer** (AWS ALB, GCP Load Balancer, etc.)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/CHS-SDK.git
cd CHS-SDK
```

### 2. Environment Configuration

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your specific configuration:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chs_simulation

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# External URLs
CORS_ORIGINS=http://localhost:3000
```

## Local Development

### Quick Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Setup

#### Backend Setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Development URLs

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## Docker Deployment

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api
```

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale api=3
```

### Environment-Specific Configurations

#### Staging
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

#### Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes Cluster**: Ensure you have a running Kubernetes cluster
2. **kubectl**: Configured to connect to your cluster
3. **Container Registry**: Push images to a registry accessible by your cluster

### Quick Deployment

Use the provided deployment script:

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh --environment staging --tag v1.0.0

# Deploy to production
./scripts/deploy.sh --environment production --tag v1.0.0

# Dry run (see what would be deployed)
./scripts/deploy.sh --environment production --tag v1.0.0 --dry-run
```

### Manual Deployment

#### 1. Create Namespaces

```bash
kubectl apply -f k8s/namespace.yaml
```

#### 2. Deploy Configuration

```bash
# Update secrets with your values
kubectl apply -f k8s/configmap.yaml
```

#### 3. Deploy Storage

```bash
kubectl apply -f k8s/storage.yaml
```

#### 4. Deploy Applications

```bash
# Update image tags in deployment.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

#### 5. Deploy Ingress (Production only)

```bash
kubectl apply -f k8s/ingress.yaml
```

#### 6. Run Database Migrations

```bash
# Get API pod name
API_POD=$(kubectl get pods -l app=chs-simulation-api -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec $API_POD -- python -m alembic upgrade head
```

### Scaling

```bash
# Scale API pods
kubectl scale deployment chs-simulation-api --replicas=5

# Scale frontend pods
kubectl scale deployment chs-simulation-frontend --replicas=3
```

### Health Checks

```bash
# Check pod status
kubectl get pods

# Check service endpoints
kubectl get endpoints

# Check ingress
kubectl get ingress
```

## CI/CD Pipeline

### GitHub Actions

The repository includes a comprehensive CI/CD pipeline (`.github/workflows/ci-cd.yml`) that:

1. **Runs Tests**: Frontend and backend tests
2. **Security Scanning**: Vulnerability scanning with Trivy
3. **Builds Images**: Multi-platform Docker images
4. **Deploys**: Automatic deployment to staging/production
5. **E2E Tests**: End-to-end testing
6. **Performance Tests**: Load and stress testing

### Pipeline Triggers

- **Push to `main`**: Deploys to production
- **Push to `develop`**: Deploys to staging
- **Pull Requests**: Runs tests and security scans
- **Releases**: Creates tagged deployments

### Required Secrets

Configure these secrets in your GitHub repository:

```bash
# Container Registry
GHCR_TOKEN=your_github_token

# Kubernetes
KUBE_CONFIG=base64_encoded_kubeconfig

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook

# Environment Variables
PRODUCTION_DATABASE_URL=your_production_db_url
PRODUCTION_SECRET_KEY=your_production_secret
```

## Monitoring and Logging

### Prometheus Metrics

The application exposes metrics at `/metrics` endpoint:

```bash
# Access metrics
curl http://localhost:8000/metrics
```

### Grafana Dashboards

Import the provided Grafana dashboards from `monitoring/grafana/dashboards/`.

### Log Aggregation

Logs are structured in JSON format and can be collected using:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd** + **Elasticsearch**
- **Prometheus** + **Loki** + **Grafana**

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
kubectl exec -it deployment/postgres -- psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# Check database logs
kubectl logs deployment/postgres
```

#### 2. Redis Connection Issues

```bash
# Test Redis connectivity
kubectl exec -it deployment/redis -- redis-cli ping

# Check Redis logs
kubectl logs deployment/redis
```

#### 3. Image Pull Issues

```bash
# Check image pull secrets
kubectl get secrets

# Describe pod for detailed error
kubectl describe pod <pod-name>
```

#### 4. Ingress Issues

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress chs-simulation-ingress
```

### Debug Commands

```bash
# Get all resources
kubectl get all

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top pods
kubectl top nodes

# Access pod shell
kubectl exec -it <pod-name> -- /bin/bash

# Port forward for debugging
kubectl port-forward service/chs-simulation-api-service 8000:8000
```

### Performance Tuning

#### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('chs_simulation'));
```

#### Redis Optimization

```bash
# Check Redis memory usage
redis-cli info memory

# Check Redis performance
redis-cli --latency-history
```

#### Application Optimization

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health

# Monitor resource usage
docker stats
```

### Backup and Recovery

#### Database Backup

```bash
# Create backup
kubectl exec deployment/postgres -- pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Restore backup
kubectl exec -i deployment/postgres -- psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

#### Volume Backup

```bash
# Create volume snapshot (AWS EBS)
aws ec2 create-snapshot --volume-id vol-xxxxxxxxx --description "CHS Simulation Backup"
```

### Security Considerations

1. **Secrets Management**: Use Kubernetes secrets or external secret managers
2. **Network Policies**: Implement network segmentation
3. **RBAC**: Configure role-based access control
4. **Image Scanning**: Regularly scan container images for vulnerabilities
5. **SSL/TLS**: Use HTTPS for all external communications
6. **Authentication**: Implement strong authentication mechanisms

### Support

For additional support:

1. Check the [GitHub Issues](https://github.com/your-org/CHS-SDK/issues)
2. Review application logs
3. Contact the development team
4. Consult the API documentation at `/docs`

---

**Note**: Replace `your-org` and other placeholder values with your actual organization and configuration details.