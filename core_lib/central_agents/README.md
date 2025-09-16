# Central Agents Module 中央智能体模块

## 🎯 模块定位
**业务实现层** - 具体的中央智能体实现，使用 central_coordination 提供的基础设施

## 📁 模块结构

```
central_agents/
├── control/                    # 控制类中央智能体
│   ├── mpc_agent.py           # MPC控制智能体
│   ├── rule_based_agent.py    # 规则基础控制智能体  
│   ├── emergency_agent.py     # 紧急响应智能体
│   └── hierarchical_agent.py  # 分层控制智能体
│
├── perception/                 # 感知类中央智能体
│   ├── global_state_agent.py  # 全局状态智能体
│   ├── anomaly_agent.py       # 异常检测智能体
│   └── monitoring_agent.py    # 监控智能体
│
├── decision/                   # 决策类中央智能体
│   ├── dispatcher_agent.py    # 调度智能体
│   ├── optimizer_agent.py     # 优化智能体
│   └── coordinator_agent.py   # 协调智能体
│
├── forecasting/               # 预测类中央智能体
│   ├── demand_agent.py        # 需求预测智能体
│   ├── inflow_agent.py        # 入流预测智能体
│   └── weather_agent.py       # 天气预测智能体
│
└── base/                      # 基础类和工具
    ├── central_agent_base.py  # 中央智能体基类
    ├── config_manager.py      # 配置管理器
    └── utils.py               # 工具函数
```

## 🔧 设计原则

1. **继承基础接口**: 所有智能体继承 central_coordination 定义的接口
2. **组合基础服务**: 使用 central_coordination 提供的服务
3. **业务专注**: 专注于具体的业务逻辑实现
4. **可配置**: 支持灵活的配置和参数调整

## 📋 功能分类

### Control 控制类
专注于系统控制和调节
- **MPC Agent**: 模型预测控制
- **Rule-based Agent**: 基于规则的控制
- **Emergency Agent**: 紧急情况处理
- **Hierarchical Agent**: 分层控制协调

### Perception 感知类  
专注于信息收集和状态感知
- **Global State Agent**: 全局状态聚合
- **Anomaly Agent**: 异常检测和报警
- **Monitoring Agent**: 系统监控

### Decision 决策类
专注于高层决策和调度
- **Dispatcher Agent**: 资源调度分配
- **Optimizer Agent**: 系统优化
- **Coordinator Agent**: 多智能体协调

### Forecasting 预测类
专注于预测和规划
- **Demand Agent**: 需求预测
- **Inflow Agent**: 入流预测  
- **Weather Agent**: 天气预测

## 🚀 使用示例

```python
from core_lib.central_agents.control import MPCAgent
from core_lib.central_agents.perception import GlobalStateAgent
from core_lib.central_coordination.communication import MessageBus

# 创建消息总线
bus = MessageBus()

# 创建MPC控制智能体
mpc_agent = MPCAgent(
    agent_id="central_mpc",
    message_bus=bus,
    config={
        "prediction_horizon": 10,
        "control_horizon": 3,
        # ... 其他配置
    }
)

# 创建全局状态智能体
state_agent = GlobalStateAgent(
    agent_id="global_state",
    message_bus=bus,
    monitored_components=["reservoir_1", "canal_1", "gate_1"]
)
```

## 🔄 与 central_coordination 的关系

- **依赖关系**: central_agents 依赖 central_coordination
- **接口实现**: 实现 central_coordination 定义的接口
- **服务使用**: 使用 central_coordination 提供的基础服务
- **通信机制**: 通过 central_coordination 的消息总线通信