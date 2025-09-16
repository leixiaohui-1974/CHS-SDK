# CHS-SDK Agent架构重构计划

## 问题分析

### 当前问题
1. **Agent数量过多**：70+ 个agent类分散在6个模块中
2. **职责重叠**：相似功能在多处实现（如CSV读取）
3. **层次混乱**：central_agents 和 central_coordination 边界不清
4. **抽象不足**：缺乏统一的基类和设计模式

### 架构问题
- 违反DRY原则：多个CSV相关agent
- 单一职责原则混乱：一些agent承担多种职责
- 层次划分不清：控制逻辑分散在不同层级

## 重构目标

### 设计原则
1. **单一职责**：每个agent只负责一种核心功能
2. **层次清晰**：Local → Central → Service 三层架构
3. **可复用性**：通过配置而非继承实现差异化
4. **可扩展性**：插件化架构支持新功能

### 目标架构

```
core_lib/
├── agents/
│   ├── base/
│   │   ├── agent.py              # 基础Agent接口
│   │   ├── local_agent.py        # 本地Agent基类  
│   │   ├── central_agent.py      # 中央Agent基类
│   │   └── service_agent.py      # 服务Agent基类
│   │
│   ├── local/                    # 本地智能体 (现local_agents)
│   │   ├── perception/
│   │   │   └── perception_agent.py       # 统一感知agent
│   │   ├── control/
│   │   │   ├── control_agent.py          # 统一控制agent
│   │   │   └── strategies/               # 控制策略插件
│   │   └── utility/
│   │       └── utility_agent.py          # 工具agent
│   │
│   ├── central/                  # 中央智能体
│   │   ├── coordination/
│   │   │   ├── coordinator_agent.py      # 协调agent
│   │   │   └── dispatcher_agent.py       # 调度agent
│   │   ├── control/
│   │   │   └── mpc_agent.py              # 中央MPC控制
│   │   └── monitoring/
│   │       └── monitor_agent.py          # 监控agent
│   │
│   └── services/                 # 服务智能体 (新增)
│       ├── data/
│       │   └── data_source_agent.py      # 统一数据源
│       ├── disturbance/
│       │   └── disturbance_agent.py      # 统一扰动
│       └── analysis/
│           └── identification_agent.py   # 参数识别
```

## 重构步骤

### Phase 1: 创建新的基类架构
1. 重新设计Agent基类层次
2. 定义清晰的接口协议
3. 建立配置驱动的agent工厂

### Phase 2: 合并相似功能
1. **数据源统一**: 合并所有CSV/数据相关agent
   - CsvReaderAgent + CsvInflowAgent + CsvDataSourceAgent → DataSourceAgent
2. **控制器统一**: 标准化所有控制agent
   - GateControlAgent, PumpControlAgent, ValveControlAgent → ControlAgent(device_type)
3. **扰动统一**: 合并扰动相关agent
   - RainfallAgent, WaterUseAgent, DynamicRainfallAgent → DisturbanceAgent(disturbance_type)

### Phase 3: 重构现有agent
1. 迁移local_agents到新架构
2. 整合central_coordination到central_agents
3. 创建services层

### Phase 4: 优化和清理
1. 删除重复代码
2. 更新配置文件
3. 更新文档和示例

## 具体实现

### 1. 统一控制Agent
```python
class ControlAgent(LocalAgent):
    """统一本地控制智能体"""
    
    def __init__(self, device_type: DeviceType, control_strategy: str, **config):
        self.device_type = device_type  # GATE, PUMP, VALVE, TURBINE
        self.strategy = self._load_strategy(control_strategy)  # PID, MPC, ADAPTIVE
        # 通过配置而非继承实现不同设备的控制逻辑
```

### 2. 统一数据源Agent
```python
class DataSourceAgent(ServiceAgent):
    """统一数据源智能体"""
    
    def __init__(self, source_type: str, **config):
        self.source_type = source_type  # CSV, DB, API, MQTT
        self.reader = self._create_reader(source_type, config)
        # 支持多种数据源类型
```

### 3. 配置驱动的Agent创建
```yaml
# 新的agent配置格式
agents:
  - id: gate_control_01
    type: local.control
    config:
      device_type: gate
      control_strategy: pid
      target_component: gate_01
      
  - id: csv_inflow_data
    type: service.data_source  
    config:
      source_type: csv
      file_path: "data/inflow.csv"
      output_topic: "inflow_data"
```

## 预期收益

### 数量减少
- 从 70+ 个agent类 → 15-20 个核心agent类
- 配置驱动实现功能差异化

### 维护性提升
- 统一的基类和接口
- 清晰的职责划分
- 更好的代码复用

### 扩展性增强
- 插件化的控制策略
- 统一的配置格式
- 模块化的架构设计

## 迁移策略

### 向后兼容
1. 保留旧的agent类作为新agent的wrapper
2. 逐步迁移现有配置文件
3. 提供迁移工具和文档

### 分阶段实施
1. **第一阶段**：建立新架构，保持旧架构可用
2. **第二阶段**：迁移核心功能，标记旧代码为deprecated
3. **第三阶段**：完全移除旧代码，优化新架构