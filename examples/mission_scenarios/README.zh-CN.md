# 数据驱动的仿真场景

该目录包含由YAML配置文件定义的独立仿真场景。这种数据驱动的方法允许在不更改核心仿真代码的情况下，快速开发和测试不同的系统配置。

## 运行场景

本目录中的所有场景支持四种不同的运行方式，提供从简单到复杂的多层次仿真体验：

### 方式一：硬编码方式

```bash
# 交互式选择场景
python run_hardcoded.py

# 直接指定场景编号
python run_hardcoded.py 1  # 引绰济辽工程仿真
```

**特点**:
- 参数直接在代码中定义
- 代码逻辑清晰，适合学习和理解
- 快速测试和演示
- 完整集成调试工具和性能监控

**适用场景**: 学习代码逻辑、快速原型验证、教学演示

### 方式二：场景运行方式

```bash
# 交互式选择场景
python run_scenario.py

# 直接指定场景编号
python run_scenario.py 1  # 引绰济辽工程仿真
```

**特点**:
- 使用传统的多配置文件方式（agents.yml、components.yml、config.yml等）
- 支持交互式场景选择
- 每个场景独立配置
- 灵活的参数调整

**适用场景**: 传统配置管理、多场景对比测试、标准仿真流程

### 方式三：统一场景运行方式

```bash
# 交互式选择场景
python run_unified_scenario.py

# 直接指定场景编号
python run_unified_scenario.py 1  # 引绰济辽工程仿真
```

**特点**:
- 使用统一配置文件（universal_config.yml）
- 简化的配置管理
- 支持交互式场景选择
- 自动配置文件查找和回退机制

**适用场景**: 简化配置管理、标准化仿真流程、批量场景运行

### 方式四：通用配置运行方式（推荐）

```bash
# 交互式选择场景
python run_universal_config.py

# 直接指定场景编号
python run_universal_config.py 1  # 引绰济辽工程仿真
```

**特点**:
- 使用最完整的通用配置文件（universal_config.yml）
- 支持所有高级功能（调试、性能监控、可视化等）
- 智能错误处理和恢复
- 自动验证和结果分析
- 配置文件验证和优化建议
- 生成详细的分析报告和性能统计

**适用场景**: 生产环境、完整功能测试、性能分析、专业仿真

### 传统运行方式（兼容性）

每个场景也可以使用位于项目根目录下的通用 `run_scenario.py` 脚本来执行。您必须将要运行的特定场景目录的路径作为命令行参数传递。

例如，要运行 `yinchuojiliao` 场景，请从项目的根目录执行以下命令：

```bash
python run_scenario.py mission/scenarios/yinchuojiliao
```

仿真完成后，输出数据将作为 `output.yml` 保存在相应的场景目录中。

## 场景目录结构

每个场景必须是一个包含以下四个YAML文件的目录：

- `config.yml`: 定义全局仿真参数。
- `components.yml`: 定义所有物理组件（例如，水库、管道）。
- `topology.yml`: 定义物理组件之间的连接。
- `agents.yml`: 定义所有的软件代理和控制器。
- `data/` (可选): 用于存放任何补充数据文件（例如CSV格式的入流数据）的目录。

### `config.yml`

该文件指定了仿真运行的总体设置。

**结构:**
```yaml
simulation:
  duration: 168  # 仿真总时长（小时）
  dt: 1.0      # 每次迭代的时间步长（小时）
```

### `components.yml`

该文件定义了仿真中的每个物理对象。

**结构:**
```yaml
components:
  - id: my_component_id          # 组件的唯一标识符
    class: Reservoir             # 组件模型的Python类名
    initial_state:               # 组件的初始状态
      water_level: 350.0
      # ... 其他状态变量
    parameters:                  # 组件的固定物理参数
      surface_area: 5.0e+7
      # ... 其他参数
```

### `topology.yml`

该文件以有向图的形式定义了物理组件之间的连接方式。

**结构:**
```yaml
connections:
  - upstream: component_id_1     # 上游组件的ID
    downstream: component_id_2   # 下游组件的ID
  # ... 更多连接
```

### `agents.yml`

该文件定义了系统的所有“大脑”：代理和简单控制器。

**结构:**
该文件有两个主键：`controllers` 和 `agents`。

- **`controllers`**: 用于由仿真工具直接连接的简单控制器（如PID）。
  ```yaml
  controllers:
    - id: my_pid_controller
      class: PIDController
      controlled_id: gate_to_control   # 被控组件的ID
      observed_id: reservoir_to_watch  # 观测组件的ID
      observation_key: water_level     # 用作输入的状态变量
      config:                          # 控制器构造函数的参数
        Kp: -0.1
        Ki: -0.01
        # ... 其他PID参数
  ```

- **`agents`**: 用于参与主代理仿真循环的更复杂的代理。
  ```yaml
  agents:
    - id: my_digital_twin
      class: DigitalTwinAgent
      config:
        simulated_object_id: component_to_twin # 该代理所对应的孪生组件的ID
        state_topic: "state/my_topic"          # 用于发布状态的消息总线主题

    - id: my_csv_reader
      class: CsvInflowAgent
      config:
        target_component_id: reservoir_to_fill # 接收输入的组件
        csv_file: data/inflow_data.csv         # 数据文件的路径（相对于场景目录）
        time_column: time_hr
        data_column: inflow_m3s
  ```
每个代理的 `config` 块包含其构造函数所需的特定参数。YAML加载器会根据其 `class` 动态构建代理。
