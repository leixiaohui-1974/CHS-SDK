# CHS-SDK 后端架构文档

## 概述

CHS-SDK 后端采用 FastAPI 框架构建，提供高性能的 RESTful API 和 WebSocket 服务，支持水利系统仿真、多智能体协调和实时监控功能。

## 目录结构

```
api/
├── auth/                    # 认证授权模块
├── core/                    # 核心功能模块
├── database/                # 数据库操作模块
├── middleware/              # 中间件
├── models/                  # 数据模型
├── routes/                  # API 路由
├── services/                # 业务服务
├── startup/                 # 启动配置
├── websocket/               # WebSocket 连接管理
├── config.py                # 配置文件
├── server.py                # 服务器入口
└── requirements.txt         # 依赖包列表
```

## 核心模块详解

### 1. 认证授权模块 (auth/)

#### 文件说明
- `authentication.py`: 用户认证逻辑
- `authorization.py`: 权限控制逻辑
- `dependencies.py`: 认证依赖注入
- `models.py`: 认证相关数据模型
- `password.py`: 密码加密和验证

#### 主要功能
- JWT Token 认证
- 基于角色的访问控制 (RBAC)
- 密码安全策略
- 会话管理

### 2. 核心功能模块 (core/)

#### 文件说明
- `cache.py`: 缓存管理基础功能
- `cache_manager.py`: 高级缓存管理器
- `database_optimization.py`: 数据库性能优化
- `load_balancer.py`: 负载均衡器
- `performance_monitor.py`: 性能监控
- `simulation_engine.py`: 仿真引擎核心

#### 主要功能
- Redis 缓存集成
- 数据库连接池管理
- 请求负载均衡
- 实时性能监控
- 仿真任务调度

### 3. 数据库模块 (database/)

#### 文件说明
- `database.py`: 数据库连接和配置
- `models.py`: SQLAlchemy 数据模型
- `crud.py`: 数据库 CRUD 操作
- `migrations.py`: 数据库迁移脚本

#### 主要功能
- SQLite/PostgreSQL 支持
- 异步数据库操作
- 数据模型定义
- 自动化迁移

### 4. API 路由模块 (routes/)

#### 路由文件说明
- `auth.py`: 认证相关 API
- `simulation.py`: 仿真管理 API
- `scenario.py`: 场景配置 API
- `analysis.py`: 数据分析 API
- `monitoring.py`: 监控数据 API
- `websocket.py`: WebSocket 连接 API
- `batch.py`: 批处理任务 API
- `validator.py`: 数据验证 API
- `configurator.py`: 配置管理 API
- `performance.py`: 性能监控 API
- `aliyun.py`: 阿里云集成 API
- `runner.py`: 任务执行 API

#### API 设计原则
- RESTful 设计规范
- 统一的响应格式
- 完整的错误处理
- 请求参数验证
- API 版本控制

### 5. 数据模型模块 (models/)

#### 文件说明
- `api_models.py`: API 请求/响应模型
- `simulation_models.py`: 仿真相关模型
- `websocket_models.py`: WebSocket 消息模型

#### 模型设计
- Pydantic 数据验证
- 类型注解支持
- 自动文档生成
- 序列化/反序列化

### 6. 业务服务模块 (services/)

#### 文件说明
- `aliyun_service.py`: 阿里云服务集成
- `websocket_monitor.py`: WebSocket 监控服务

#### 服务特性
- 业务逻辑封装
- 第三方服务集成
- 异步任务处理
- 错误恢复机制

### 7. WebSocket 模块 (websocket/)

#### 文件说明
- `connection_manager.py`: 连接管理器

#### 功能特性
- 实时数据推送
- 连接状态管理
- 消息广播
- 断线重连

## 配置管理

### 环境配置
- 开发环境: `.env`
- 生产环境: `.env.production`
- 阿里云环境: `.env.aliyun`

### 配置项说明
```python
# 数据库配置
DATABASE_URL = "sqlite:///./simulation.db"

# Redis 配置
REDIS_URL = "redis://localhost:6379"

# JWT 配置
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS 配置
CORS_ORIGINS = ["http://localhost:3000"]

# 性能配置
MAX_WORKERS = 4
REQUEST_TIMEOUT = 30
```

## 部署架构

### 单机部署
```
┌─────────────────┐
│   Nginx         │  # 反向代理
└─────────────────┘
         │
┌─────────────────┐
│   FastAPI       │  # API 服务
└─────────────────┘
         │
┌─────────────────┐
│   SQLite/PG     │  # 数据库
└─────────────────┘
```

### 集群部署
```
┌─────────────────┐
│   Load Balancer │  # 负载均衡
└─────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼───┐
│ API-1 │ │ API-2 │  # API 实例
└───────┘ └───────┘
    │         │
    └────┬────┘
┌─────────▼───────┐
│   PostgreSQL    │  # 共享数据库
└─────────────────┘
```

## 性能优化

### 1. 数据库优化
- 连接池配置
- 查询索引优化
- 批量操作
- 读写分离

### 2. 缓存策略
- Redis 缓存
- 内存缓存
- 查询结果缓存
- 静态资源缓存

### 3. 异步处理
- 异步 I/O 操作
- 后台任务队列
- 并发请求处理
- 非阻塞操作

## 监控和日志

### 监控指标
- API 响应时间
- 请求成功率
- 系统资源使用
- 数据库性能

### 日志管理
- 结构化日志
- 日志级别控制
- 日志轮转
- 错误追踪

## 安全措施

### 1. 认证安全
- JWT Token 验证
- 密码强度要求
- 会话超时控制
- 多因素认证

### 2. 数据安全
- 数据加密传输
- 敏感数据脱敏
- SQL 注入防护
- XSS 攻击防护

### 3. 网络安全
- HTTPS 强制
- CORS 策略
- 请求频率限制
- IP 白名单

## 开发指南

### 1. 环境搭建
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn api.server:app --reload

# 运行测试
pytest tests/
```

### 2. 代码规范
- PEP 8 代码风格
- 类型注解
- 文档字符串
- 单元测试覆盖

### 3. API 开发流程
1. 定义数据模型
2. 实现路由处理器
3. 添加认证授权
4. 编写单元测试
5. 更新 API 文档

## 故障排查

### 常见问题
1. **数据库连接失败**
   - 检查数据库配置
   - 验证连接字符串
   - 确认数据库服务状态

2. **认证失败**
   - 检查 JWT 配置
   - 验证 Token 有效性
   - 确认用户权限

3. **性能问题**
   - 检查数据库查询
   - 分析缓存命中率
   - 监控系统资源

### 调试工具
- FastAPI 自动文档: `/docs`
- 健康检查: `/health`
- 性能监控: `/metrics`
- 日志查看: `logs/` 目录

## 扩展开发

### 添加新的 API 端点
1. 在 `models/` 中定义数据模型
2. 在 `routes/` 中创建路由文件
3. 在 `services/` 中实现业务逻辑
4. 添加相应的测试用例

### 集成第三方服务
1. 在 `services/` 中创建服务类
2. 配置相关环境变量
3. 实现错误处理和重试机制
4. 添加监控和日志

## 版本更新

### 更新流程
1. 代码审查
2. 测试验证
3. 数据库迁移
4. 灰度发布
5. 全量部署

### 回滚策略
1. 代码回滚
2. 数据库回滚
3. 配置回滚
4. 服务重启

---

本文档将随着项目发展持续更新，如有疑问请联系开发团队。