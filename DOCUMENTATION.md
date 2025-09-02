# CHS-SDK 文档索引

## 概述

本文档提供 CHS-SDK (Cyber-Hydraulic System Software Development Kit) 项目的完整文档索引。CHS-SDK 是一个用于水利系统仿真和控制的综合性软件开发工具包，支持多智能体协同、实时监控和高性能仿真。

## 📚 文档结构

### 🏗️ 架构文档

#### [后端架构文档](./backend_architecture.md)
- 系统架构概述
- 目录结构详解
- 核心模块说明
- 配置管理
- 部署架构
- 性能优化
- 安全措施

#### [API 参考文档](./docs/api_reference.md)
- REST API 端点
- WebSocket API
- 认证授权
- 请求/响应格式
- 错误处理
- 快速开始指南

### 🧪 测试文档

#### [测试指南](./testing_guide.md)
- 测试策略和分类
- 测试工具和框架
- 测试配置管理
- 性能测试详解
- 安全测试详解
- 持续集成测试

#### [测试目录说明](./tests/README.md)
- 测试目录结构
- 运行测试方法
- 测试数据管理
- 调试和故障排查
- 测试最佳实践

### 👨‍💻 开发文档

#### [开发者指南](./docs/developer_guide.md)
- 环境搭建
- 快速开始
- 开发规范
- 代码结构
- 调试技巧

#### [示例文档](./examples/README.md)
- 基础示例
- 高级用例
- 最佳实践
- 常见问题

## 🚀 快速导航

### 新手入门

1. **环境搭建**: 参考 [开发者指南 - 快速开始](./docs/developer_guide.md#快速开始)
2. **API 使用**: 查看 [API 参考 - 快速开始](./docs/api_reference.md#快速开始)
3. **运行示例**: 浏览 [示例目录](./examples/)
4. **运行测试**: 参考 [测试目录说明](./tests/README.md#运行测试)

### 开发者资源

1. **架构理解**: 阅读 [后端架构文档](./backend_architecture.md)
2. **API 开发**: 参考 [API 参考文档](./docs/api_reference.md)
3. **测试开发**: 查看 [测试指南](./testing_guide.md)
4. **代码规范**: 参考 [开发者指南](./docs/developer_guide.md)

### 运维人员

1. **部署架构**: 参考 [后端架构 - 部署架构](./backend_architecture.md#部署架构)
2. **监控配置**: 查看 [后端架构 - 监控和日志](./backend_architecture.md#监控和日志)
3. **性能优化**: 参考 [后端架构 - 性能优化](./backend_architecture.md#性能优化)
4. **故障排查**: 查看 [后端架构 - 故障排查](./backend_architecture.md#故障排查)

## 📁 项目结构概览

```
CHS-SDK/
├── 📄 DOCUMENTATION.md              # 本文档 - 文档索引
├── 📄 backend_architecture.md       # 后端架构详细文档
├── 📄 testing_guide.md             # 测试策略和指南
├── 📁 api/                         # 后端 API 服务
│   ├── 📁 auth/                    # 认证授权模块
│   ├── 📁 core/                    # 核心功能模块
│   ├── 📁 database/                # 数据库模块
│   ├── 📁 middleware/              # 中间件
│   ├── 📁 models/                  # 数据模型
│   ├── 📁 routes/                  # API 路由
│   ├── 📁 services/                # 业务服务
│   ├── 📁 startup/                 # 启动配置
│   ├── 📁 websocket/               # WebSocket 服务
│   ├── 📄 config.py               # 配置文件
│   ├── 📄 requirements.txt        # Python 依赖
│   └── 📄 server.py               # 服务器入口
├── 📁 core_lib/                    # 核心库
│   ├── 📁 agents/                  # 智能体模块
│   ├── 📁 components/              # 组件模块
│   ├── 📁 simulation/              # 仿真模块
│   └── 📁 utils/                   # 工具模块
├── 📁 tests/                       # 测试套件
│   ├── 📄 README.md               # 测试目录说明
│   ├── 📁 e2e/                    # 端到端测试
│   ├── 📁 performance/            # 性能测试
│   ├── 📁 security/               # 安全测试
│   ├── 📁 test_data/              # 测试数据
│   └── 📄 test_*.py               # 各类测试文件
├── 📁 examples/                    # 示例代码
│   ├── 📄 README.md               # 示例说明
│   └── 📁 mission_example_*/       # 具体示例
├── 📁 docs/                        # 文档目录
│   ├── 📄 api_reference.md        # API 参考
│   ├── 📄 developer_guide.md      # 开发者指南
│   └── 📁 images/                 # 文档图片
└── 📁 frontend/                    # 前端应用 (如果存在)
```

## 🔧 核心功能模块

### 智能体系统
- **中央智能体**: 调度、MPC控制、感知
- **本地智能体**: CSV数据处理、应急响应、水库感知、阀门控制
- **智能体通信**: 消息传递、状态同步、协同决策

### 仿真引擎
- **水力仿真**: 水库、管网、阀门建模
- **实时仿真**: 高频率状态更新
- **批处理仿真**: 大规模场景分析

### API 服务
- **REST API**: 标准HTTP接口
- **WebSocket**: 实时数据推送
- **认证系统**: JWT令牌认证
- **监控接口**: 系统状态监控

### 数据管理
- **SQLite数据库**: 轻量级数据存储
- **CSV数据处理**: 批量数据导入
- **实时数据流**: 传感器数据接入

## 📊 测试覆盖

### 测试类型
- ✅ **单元测试**: 组件级功能验证
- ✅ **集成测试**: 模块间协作测试
- ✅ **性能测试**: 负载和压力测试
- ✅ **安全测试**: 认证和输入验证
- ✅ **端到端测试**: 完整工作流验证

### 测试工具
- **pytest**: 主要测试框架
- **locust**: 性能和负载测试
- **websocket-client**: WebSocket测试
- **requests**: HTTP API测试

## 🛠️ 开发工具

### 后端技术栈
- **Python 3.8+**: 主要编程语言
- **FastAPI**: Web框架
- **SQLAlchemy**: ORM框架
- **Pydantic**: 数据验证
- **uvicorn**: ASGI服务器

### 开发工具
- **pytest**: 测试框架
- **black**: 代码格式化
- **flake8**: 代码检查
- **mypy**: 类型检查

## 📈 性能指标

### 系统性能
- **API响应时间**: < 100ms (P95)
- **WebSocket延迟**: < 50ms
- **仿真频率**: 1000+ steps/second
- **并发连接**: 100+ WebSocket连接

### 测试覆盖率
- **代码覆盖率**: > 80%
- **API覆盖率**: 100%
- **智能体覆盖率**: > 90%

## 🔒 安全特性

### 认证授权
- JWT令牌认证
- 角色基础访问控制
- API密钥管理

### 数据安全
- 输入验证和清理
- SQL注入防护
- XSS攻击防护
- CORS配置

## 🚀 部署选项

### 本地开发
```bash
# 启动开发服务器
cd api
python server.py
```

### 生产部署
```bash
# 使用 uvicorn
uvicorn api.server:app --host 0.0.0.0 --port 8000

# 使用 Docker
docker build -t chs-sdk .
docker run -p 8000:8000 chs-sdk
```

### 云部署
- **AWS**: EC2, ECS, Lambda
- **Azure**: App Service, Container Instances
- **GCP**: Cloud Run, Compute Engine

## 📞 支持和贡献

### 获取帮助
- 📖 查看相关文档
- 🐛 提交 Issue
- 💬 参与讨论

### 贡献代码
1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 提交 Pull Request

### 文档贡献
1. 改进现有文档
2. 添加示例代码
3. 翻译文档
4. 报告文档问题

## 📝 更新日志

### 最新更新
- ✅ 完成后端架构文档
- ✅ 完成测试指南文档
- ✅ 完成API参考文档
- ✅ 完成测试目录说明
- ✅ 创建文档索引

### 计划更新
- 🔄 前端架构文档
- 🔄 部署指南文档
- 🔄 监控运维文档
- 🔄 故障排查手册

---

**CHS-SDK 开发团队**  
最后更新: 2024年1月

> 💡 **提示**: 本文档会持续更新，建议定期查看最新版本。如有疑问或建议，欢迎提交 Issue 或 Pull Request。