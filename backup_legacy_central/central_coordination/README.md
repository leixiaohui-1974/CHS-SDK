# Central Coordination Module 中央协调模块

## 🎯 模块定位
**基础设施层** - 为中央智能体提供通信、协调和基础服务

## 📁 模块结构

```
central_coordination/
├── communication/          # 通信基础设施
│   ├── message_bus.py     # 消息总线 (核心)
│   ├── topic_manager.py   # 主题管理
│   └── protocol.py        # 通信协议定义
│
├── coordination/          # 协调基础设施  
│   ├── coordinator_base.py    # 协调器基类
│   ├── state_aggregator.py   # 状态聚合器
│   └── decision_dispatcher.py # 决策分发器
│
├── services/              # 基础服务
│   ├── anomaly_detector.py   # 异常检测服务
│   ├── forecasting_service.py # 预测服务
│   └── monitoring_service.py  # 监控服务
│
└── interfaces/            # 接口定义
    ├── central_agent_interface.py  # 中央智能体接口
    ├── coordination_interface.py   # 协调接口
    └── service_interface.py        # 服务接口
```

## 🔧 设计原则

1. **单一职责**: 每个模块只负责一个核心功能
2. **依赖倒置**: 定义接口，具体实现在 central_agents 中
3. **开放封闭**: 对扩展开放，对修改封闭
4. **松耦合**: 通过接口和消息总线解耦

## 📋 功能职责

### Communication 通信层
- 消息发布/订阅机制
- 主题路由和管理
- 通信协议标准化

### Coordination 协调层  
- 状态信息聚合
- 决策结果分发
- 协调流程管理

### Services 服务层
- 可复用的基础服务
- 异常检测、预测、监控等
- 服务发现和注册

### Interfaces 接口层
- 标准化接口定义
- 协议契约规范
- 类型定义和约束

## 🚀 使用方式

```python
from core_lib.central_coordination.communication import MessageBus
from core_lib.central_coordination.interfaces import CentralAgentInterface

# 使用基础设施构建具体的中央智能体
class MyCentralAgent(CentralAgentInterface):
    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        # 使用基础设施...
```