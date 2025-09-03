# 增强消息总线使用指南

## 概述

增强消息总线 (EnhancedMessageBus) 是CHS-SDK中的核心通信组件，提供了高性能、可靠的消息传递机制。它支持异步消息处理、消息持久化、优先级队列、消息过滤等高级功能。

## 核心特性

### 1. 异步消息处理
- 非阻塞消息发送和接收
- 支持高并发场景
- 自动负载均衡

### 2. 消息持久化
- 可选的消息持久化存储
- 支持消息重放和恢复
- 防止消息丢失

### 3. 优先级队列
- 支持消息优先级设置
- 高优先级消息优先处理
- 灵活的优先级策略

### 4. 消息过滤
- 基于主题的消息过滤
- 自定义过滤规则
- 减少不必要的消息处理

## 基本使用

### 1. 创建消息总线

```python
from core_lib.core.enhanced_message_bus import EnhancedMessageBus

# 创建基础消息总线
bus = EnhancedMessageBus()

# 创建带配置的消息总线
bus = EnhancedMessageBus(
    max_queue_size=10000,
    enable_persistence=True,
    persistence_file="messages.db",
    enable_priority=True,
    worker_threads=4
)
```

### 2. 消息发送

```python
# 发送简单消息
bus.send_message(
    topic="water_level",
    data={"level": 5.2, "timestamp": time.time()},
    sender="sensor_1"
)

# 发送优先级消息
bus.send_message(
    topic="emergency",
    data={"type": "flood_warning", "severity": "high"},
    sender="monitoring_system",
    priority=1  # 高优先级
)

# 异步发送消息
await bus.send_message_async(
    topic="control_command",
    data={"action": "open_gate", "percentage": 50},
    sender="controller"
)
```

### 3. 消息订阅

```python
# 订阅消息主题
def handle_water_level(message):
    level = message.data["level"]
    print(f"水位更新: {level}m")

bus.subscribe("water_level", handle_water_level)

# 使用装饰器订阅
@bus.subscriber("emergency")
def handle_emergency(message):
    print(f"紧急事件: {message.data}")

# 异步消息处理
@bus.async_subscriber("control_command")
async def handle_control_command(message):
    action = message.data["action"]
    await execute_action(action)
```

### 4. 消息过滤

```python
# 基于发送者过滤
bus.subscribe(
    topic="sensor_data",
    handler=process_sensor_data,
    filter_func=lambda msg: msg.sender.startswith("sensor_")
)

# 基于数据内容过滤
bus.subscribe(
    topic="alerts",
    handler=handle_critical_alerts,
    filter_func=lambda msg: msg.data.get("severity") == "critical"
)

# 自定义过滤器类
class TemperatureFilter:
    def __init__(self, min_temp, max_temp):
        self.min_temp = min_temp
        self.max_temp = max_temp
    
    def __call__(self, message):
        temp = message.data.get("temperature")
        return temp is not None and self.min_temp <= temp <= self.max_temp

bus.subscribe(
    topic="temperature",
    handler=handle_temperature,
    filter_func=TemperatureFilter(0, 100)
)
```

## 高级功能

### 1. 消息持久化

```python
# 启用持久化
bus = EnhancedMessageBus(
    enable_persistence=True,
    persistence_file="simulation_messages.db",
    persistence_batch_size=100
)

# 消息重放
bus.replay_messages(
    topic="sensor_data",
    start_time=start_timestamp,
    end_time=end_timestamp,
    handler=replay_handler
)

# 获取历史消息
history = bus.get_message_history(
    topic="control_commands",
    limit=100
)
```

### 2. 消息路由

```python
# 设置消息路由规则
bus.add_route(
    source_topic="raw_sensor_data",
    target_topic="processed_sensor_data",
    transformer=lambda msg: {
        "processed_value": msg.data["raw_value"] * 1.5,
        "timestamp": msg.timestamp
    }
)

# 条件路由
bus.add_conditional_route(
    source_topic="sensor_readings",
    condition=lambda msg: msg.data["value"] > 10,
    target_topic="high_value_alerts"
)
```

### 3. 消息聚合

```python
# 时间窗口聚合
bus.add_aggregator(
    topic="sensor_data",
    window_size=60,  # 60秒窗口
    aggregation_func=lambda messages: {
        "average": sum(m.data["value"] for m in messages) / len(messages),
        "count": len(messages)
    },
    output_topic="sensor_data_aggregated"
)

# 计数聚合
bus.add_count_aggregator(
    topic="events",
    count_threshold=10,
    output_topic="event_batches"
)
```

### 4. 错误处理和重试

```python
# 设置错误处理器
def error_handler(message, exception):
    print(f"处理消息失败: {message.topic}, 错误: {exception}")
    # 可以选择重新发送或记录错误

bus.set_error_handler(error_handler)

# 配置重试策略
bus.configure_retry(
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0
)

# 死信队列
bus.configure_dead_letter_queue(
    topic="failed_messages",
    max_failures=5
)
```

## 性能优化

### 1. 批量处理

```python
# 启用批量处理
bus.configure_batching(
    batch_size=50,
    batch_timeout=1.0  # 1秒超时
)

# 批量发送消息
messages = [
    {"topic": "data", "data": {"value": i}}
    for i in range(100)
]
bus.send_batch(messages)
```

### 2. 连接池

```python
# 配置连接池
bus.configure_connection_pool(
    pool_size=10,
    max_connections=50,
    connection_timeout=30
)
```

### 3. 内存管理

```python
# 配置内存限制
bus.configure_memory_management(
    max_memory_mb=512,
    cleanup_interval=300,  # 5分钟清理一次
    message_ttl=3600       # 消息1小时过期
)
```

## 监控和调试

### 1. 性能指标

```python
# 获取性能统计
stats = bus.get_statistics()
print(f"消息发送数: {stats['messages_sent']}")
print(f"消息接收数: {stats['messages_received']}")
print(f"平均延迟: {stats['average_latency']}ms")
print(f"队列大小: {stats['queue_size']}")

# 实时监控
bus.enable_monitoring(
    metrics_interval=10,  # 10秒输出一次指标
    log_slow_messages=True,
    slow_threshold=100    # 100ms阈值
)
```

### 2. 调试工具

```python
# 启用调试模式
bus.enable_debug_mode(
    log_all_messages=True,
    trace_message_flow=True,
    dump_failed_messages=True
)

# 消息追踪
bus.trace_message(
    message_id="msg_123",
    callback=lambda trace: print(f"消息轨迹: {trace}")
)

# 健康检查
health = bus.health_check()
if not health['healthy']:
    print(f"消息总线异常: {health['issues']}")
```

## 集成示例

### 1. 在智能体中使用

```python
from core_lib.local_agents.base_agent import BaseAgent

class SensorAgent(BaseAgent):
    def __init__(self, agent_id, message_bus):
        super().__init__(agent_id)
        self.message_bus = message_bus
        
        # 订阅控制命令
        self.message_bus.subscribe(
            "control_commands",
            self.handle_control_command
        )
    
    def sense(self, current_time):
        # 发送传感器数据
        sensor_data = self.read_sensor()
        self.message_bus.send_message(
            topic="sensor_data",
            data=sensor_data,
            sender=self.agent_id
        )
    
    def handle_control_command(self, message):
        command = message.data
        self.execute_command(command)
```

### 2. 在仿真框架中使用

```python
from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness

# 创建带消息总线的仿真框架
bus = EnhancedMessageBus(enable_persistence=True)
harness = EnhancedSimulationHarness(
    components=[reservoir, gate],
    agents=[sensor_agent, control_agent],
    message_bus=bus
)

# 监控仿真消息
@bus.subscriber("simulation_events")
def log_simulation_events(message):
    print(f"仿真事件: {message.data}")

# 运行仿真
harness.run_simulation(simulation_time=100.0)

# 分析消息历史
history = bus.get_message_history("sensor_data")
analyze_sensor_data(history)
```

## 配置参考

### 完整配置示例

```python
config = {
    # 基础配置
    "max_queue_size": 10000,
    "worker_threads": 4,
    "enable_async": True,
    
    # 持久化配置
    "enable_persistence": True,
    "persistence_file": "messages.db",
    "persistence_batch_size": 100,
    
    # 优先级配置
    "enable_priority": True,
    "priority_levels": 5,
    
    # 性能配置
    "batch_size": 50,
    "batch_timeout": 1.0,
    "connection_pool_size": 10,
    
    # 内存管理
    "max_memory_mb": 512,
    "cleanup_interval": 300,
    "message_ttl": 3600,
    
    # 监控配置
    "enable_monitoring": True,
    "metrics_interval": 10,
    "log_slow_messages": True,
    "slow_threshold": 100
}

bus = EnhancedMessageBus(**config)
```

## 最佳实践

### 1. 主题命名
- 使用层次化命名：`system.component.metric`
- 避免过于宽泛的主题名
- 使用一致的命名约定

### 2. 消息设计
- 保持消息结构简单
- 包含必要的元数据（时间戳、发送者等）
- 避免在消息中传递大量数据

### 3. 错误处理
- 总是设置错误处理器
- 实现适当的重试策略
- 监控死信队列

### 4. 性能优化
- 根据负载调整工作线程数
- 使用批量处理减少开销
- 定期清理过期消息

## 故障排除

### 常见问题

1. **消息丢失**
   - 启用持久化
   - 检查队列大小限制
   - 验证错误处理逻辑

2. **性能问题**
   - 增加工作线程数
   - 启用批量处理
   - 优化消息过滤器

3. **内存泄漏**
   - 配置消息TTL
   - 启用定期清理
   - 监控内存使用

更多详细信息请参考源代码中的文档字符串和示例代码。