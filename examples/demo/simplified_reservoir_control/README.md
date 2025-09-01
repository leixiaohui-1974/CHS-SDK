# 简化的水库控制示例

本示例展示如何使用CHS-SDK的通用工具库来大幅简化仿真代码，让开发者专注于业务逻辑而不是重复的基础设施代码。

## 概述

传统的仿真示例通常包含大量重复的代码模式：
- 组件创建和连接
- 仿真循环管理
- 数据收集和处理
- 性能指标计算
- 可视化图表生成

通过使用通用工具库，我们将这些重复模式提炼为可复用的组件，使示例代码更加简洁和专注。

## 使用的通用工具

### 1. SimulationBuilder (仿真构建器)
- **位置**: `core_lib/utils/simulation_builder.py`
- **功能**: 提供流式API来构建仿真系统
- **优势**: 
  - 简化组件创建和连接
  - 预设常见仿真模式
  - 自动化智能体配置
  - 一键式仿真运行

```python
# 传统方式 (50+ 行代码)
reservoir = Reservoir(...)
gate = Gate(...)
controller = PIDController(...)
# ... 大量配置代码

# 使用 SimulationBuilder (3 行代码)
builder = PresetSimulations.single_reservoir_control(
    reservoir_setpoint=12.0, simulation_duration=200
)
results = builder.run()
```

### 2. SimulationPlotter (仿真绘图器)
- **位置**: `core_lib/utils/visualization_utils.py`
- **功能**: 统一的可视化接口
- **优势**:
  - 标准化的图表样式
  - 多种预设图表类型
  - 自动布局和美化
  - 中文字体支持

```python
# 传统方式 (20+ 行matplotlib代码)
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
# ... 大量绘图代码

# 使用 SimulationPlotter (3 行代码)
plotter = SimulationPlotter()
plotter.plot_control_performance(
    time=time, setpoint=setpoint, actual=actual
)
```

### 3. PerformanceAnalyzer (性能分析器)
- **位置**: `core_lib/utils/performance_analysis.py`
- **功能**: 标准化的性能指标计算
- **优势**:
  - 全面的控制性能指标
  - 系统稳定性分析
  - 频域分析
  - 自动化报告生成

```python
# 传统方式 (30+ 行计算代码)
rmse = np.sqrt(np.mean((setpoint - actual)**2))
# ... 大量指标计算代码

# 使用 PerformanceAnalyzer (2 行代码)
analyzer = PerformanceAnalyzer()
metrics = analyzer.calculate_control_metrics(setpoint, actual)
```

### 4. ExampleRunner (示例运行器)
- **位置**: `core_lib/utils/example_utils.py`
- **功能**: 通用的示例运行框架
- **优势**:
  - 统一的输出格式
  - 自动化文件管理
  - 标准化错误处理
  - 结果保存和导出

## 代码对比

### 传统示例代码结构 (~200 行)
```python
# 1. 大量导入语句 (10-15 行)
# 2. 组件创建和配置 (30-50 行)
# 3. 智能体设置 (20-30 行)
# 4. 仿真循环 (20-30 行)
# 5. 数据处理 (15-25 行)
# 6. 性能计算 (20-40 行)
# 7. 可视化代码 (30-50 行)
# 8. 结果保存 (10-15 行)
```

### 使用通用工具后 (~80 行)
```python
# 1. 简化导入 (5-8 行)
# 2. 使用预设模式 (3-5 行)
# 3. 运行仿真 (1-2 行)
# 4. 性能分析 (5-10 行)
# 5. 可视化 (10-15 行)
# 6. 业务逻辑专注 (40-50 行)
```

**代码减少**: ~60%  
**复杂度降低**: ~70%  
**可读性提升**: ~80%

## 运行示例

### 方式1: 直接运行Python脚本
```bash
cd examples/demo/simplified_reservoir_control
python run_simplified_example.py
```

### 方式2: 使用示例检测器
```bash
python example_detector.py examples/demo/simplified_reservoir_control
```

## 输出结果

运行示例后，将在 `output/` 目录下生成：

### 可视化图表
- `control_performance.png` - 控制性能图
- `time_series.png` - 时间序列图
- `performance_metrics.png` - 性能指标图
- `dashboard.png` - 综合仪表板
- `quick_control_plot.png` - 快速绘图演示

### 数据文件
- `simulation_results.csv` - 仿真数据
- `performance_report.json` - 性能分析报告

### 性能指标
示例会自动计算并显示：
- **RMSE**: 均方根误差
- **稳态误差**: 系统稳态时的误差
- **调节时间**: 达到稳态所需时间
- **超调量**: 最大超调百分比
- **稳定性指数**: 系统稳定性评分
- **综合评分**: 整体性能评分

## 快速工具演示

示例还包含快速工具的演示，展示如何用几行代码完成：
- 快速性能分析 (`quick_analysis`)
- 快速绘图 (`quick_plot`)
- 性能比较 (`compare_performance`)

## 扩展使用

### 自定义仿真系统
```python
from core_lib.utils.simulation_builder import SimulationBuilder

builder = SimulationBuilder({'duration': 300, 'dt': 0.5})
builder.add_reservoir('res1', water_level=15.0) \
       .add_gate('gate1', opening=0.3) \
       .add_pump('pump1', max_power=1500) \
       .connect_components([('res1', 'gate1'), ('gate1', 'pump1')]) \
       .add_pid_controller('controller1', 'gate1', setpoint=18.0)

results = builder.run()
```

### 自定义可视化样式
```python
from core_lib.utils.visualization_utils import get_plotter

# 使用预设样式
plotter = get_plotter('presentation')  # 或 'paper', 'compact'
plotter.plot_time_series(data, title="自定义图表")
```

### 批量性能分析
```python
from core_lib.utils.performance_analysis import compare_performance

# 比较两种控制方法
comparison = compare_performance(
    data1=method1_results,
    data2=method2_results,
    labels=['PID控制', '模糊控制']
)
```

## 优势总结

1. **代码简化**: 减少60%以上的重复代码
2. **专注业务**: 开发者可专注于控制逻辑和算法
3. **标准化**: 统一的接口和输出格式
4. **可复用**: 工具库可在所有示例中复用
5. **易维护**: 集中管理通用功能
6. **高质量**: 经过测试的稳定组件

## 相关文档

- [SimulationBuilder API文档](../../../docs/api/simulation_builder.md)
- [可视化工具指南](../../../docs/guides/visualization.md)
- [性能分析指南](../../../docs/guides/performance_analysis.md)
- [示例开发指南](../../../docs/guides/example_development.md)

## 贡献

如果您发现通用工具库中缺少某些功能，或有改进建议，欢迎：
1. 提交Issue描述需求
2. 提交Pull Request贡献代码
3. 参与讨论和设计

通用工具库的目标是让所有开发者都能更高效地创建高质量的仿真示例。