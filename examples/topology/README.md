# 水利系统拓扑仿真演示

这个目录包含了基于CHS-SDK核心库的完整水利系统仿真案例，展示了一个包含水库、渠道、闸门、管道等组件的复杂水利系统。

## 系统组成

```
上游水库 -> 渠道1 -> 分水口1 -> 渠道2 -> 管道1 -> 闸门1 -> 渠道3 -> 下游水库
```

## 文件说明

- `config.yml` - 主配置文件，包含仿真参数和系统设置
- `components.yml` - 物理组件定义，包括水库、渠道、闸门等
- `topology.yml` - 系统拓扑连接关系
- `agents.yml` - 智能体配置，包括传感器、执行器和控制器
- `run_topology_demo.py` - 主仿真脚本
- `run_simple_demo.py` - 简化仿真脚本（备用）

## 运行方法

### 方法1：使用主仿真脚本（推荐）

```bash
cd examples/topology
python run_topology_demo.py
```

### 方法2：使用简化脚本（如果主脚本有问题）

```bash
cd examples/topology
python run_simple_demo.py
```

### 方法3：使用项目根目录的运行脚本

```bash
# 从项目根目录运行
python run_scenario.py examples/topology
```

## 预期输出

运行成功后，您将看到：

1. **配置加载过程**：显示各配置文件的加载状态
2. **组件创建过程**：显示各物理组件和智能体的创建情况
3. **仿真运行过程**：显示仿真的执行进度
4. **结果分析**：显示关键组件的最终状态
5. **文件输出**：
   - `simulation_output/topology_simulation_results.json` - 完整仿真结果
   - `simulation_output/key_metrics.csv` - 关键指标CSV报告

## 关键组件说明

### 物理组件
- **Upstream_Reservoir**: 上游水库，提供系统入流
- **Channel_1/2/3**: 明渠段，使用积分延迟模型
- **Diversion_1**: 分水口，可控制分流量
- **Pipe_1**: 倒虹吸管道，使用Darcy-Weisbach公式
- **Gate_1**: 节制闸，可控制闸门开度
- **Downstream_Reservoir**: 下游水库，系统出口

### 智能体
- **PhysicalIOAgent**: 物理输入输出智能体，负责传感器数据采集和执行器控制
- **ScenarioAgent**: 场景智能体，执行预定义的仿真场景
- **StructuredControlAgent**: 结构化控制智能体，实现PID控制

## 仿真参数

- **仿真时长**: 7200秒（2小时）
- **时间步长**: 900秒（15分钟）
- **开始时间**: 0秒

## 故障排除

如果遇到问题，请检查：

1. **依赖安装**：确保安装了所有必要的Python包
   ```bash
   pip install -r requirements.txt
   pip install -r api/requirements.txt
   ```

2. **路径设置**：确保从正确的目录运行脚本

3. **配置文件**：检查YAML配置文件格式是否正确

4. **权限问题**：确保有写入输出目录的权限

## 配置修改

### 修改仿真时间
编辑 `config.yml` 中的时间参数：
```yaml
simulation:
  start_time: 0.0
  end_time: 7200.0    # 修改此值
  time_step: 900.0    # 修改此值
```

### 修改组件参数
编辑 `components.yml` 中对应组件的参数，例如：
```yaml
- id: Gate_1
  class: Gate
  parameters:
    discharge_coefficient: 0.7919242  # 修改流量系数
    width: 11                         # 修改闸门宽度
```

### 添加扰动场景
编辑 `agents.yml` 中的场景智能体配置：
```yaml
- id: scenario_agent
  config:
    scenario_script:
      - time: 3600      # 1小时后
        topic: 'disturbance/diversion_1'
        message:
          outflow: 10.0 # 增加分水流量
```

## 输出解读

### 关键指标
- **水位变化**：各组件的水位随时间变化情况
- **流量分布**：系统中各点的流量分配
- **控制效果**：闸门控制对水位的调节效果

### 系统性能
- **稳定性**：系统是否达到稳定状态
- **响应速度**：对扰动的响应时间
- **控制精度**：水位控制的精确程度

## 扩展建议

1. **增加监控点**：在更多位置添加传感器
2. **优化控制策略**：调整PID参数或使用其他控制算法
3. **增加扰动类型**：添加更多类型的系统扰动
4. **可视化输出**：添加图表生成功能
5. **参数优化**：使用优化算法调整系统参数

## 技术支持

如果遇到技术问题，请：
1. 检查控制台输出的错误信息
2. 查看项目文档和API说明
3. 确认配置文件符合项目规范
4. 验证核心库版本兼容性