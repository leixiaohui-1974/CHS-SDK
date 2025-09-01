# CHS-SDK 通用配置文件系统

## 概述

CHS-SDK 通用配置文件系统提供了一个标准化、可扩展的配置管理解决方案，支持仿真、调试、性能分析、可视化、日志记录等多种功能的统一配置。

## 特性

- **标准化配置**: 与 `component`、`topology`、`agents` 等配置保持一致的结构
- **模块化设计**: 每个功能模块可独立启用/禁用
- **扩展性强**: 基于 `SimulationBuilder` 类扩展，兼容现有系统
- **功能丰富**: 支持调试、性能监控、可视化、分析、日志等多种功能
- **环境适配**: 支持开发、测试、生产等不同环境配置

## 文件结构

```
core_lib/config/
├── universal_config_template.yml    # 通用配置模板
├── example_universal_config.yml     # 示例配置文件
├── enhanced_yaml_loader.py          # 增强的配置加载器
├── enhanced_visualization.py        # 增强的可视化模块
└── README.md                        # 使用说明文档
```

## 快速开始

### 1. 基本使用

```python
from core_lib.config.enhanced_yaml_loader import load_universal_config

# 加载配置文件
builder = load_universal_config('core_lib/config/example_universal_config.yml')

# 运行增强仿真
results = builder.run_enhanced_simulation()
print(f"仿真结果: {results}")
```

### 2. 自定义配置

```python
from core_lib.config.enhanced_yaml_loader import EnhancedSimulationBuilder

# 创建增强构建器
builder = EnhancedSimulationBuilder(scenario_path='path/to/scenario')

# 加载自定义配置
builder.load_enhanced_config('my_config.yml')

# 构建仿真
simulation = builder.build_simulation()
```

## 配置文件结构

### 主要配置节

| 配置节 | 描述 | 必需 |
|--------|------|------|
| `simulation` | 仿真基础配置 | ✓ |
| `debug` | 调试功能配置 | ✗ |
| `performance` | 性能监控配置 | ✗ |
| `visualization` | 可视化配置 | ✗ |
| `output` | 数据输出配置 | ✗ |
| `analysis` | 分析功能配置 | ✗ |
| `logging` | 日志记录配置 | ✗ |
| `error_handling` | 错误处理配置 | ✗ |
| `caching` | 缓存管理配置 | ✗ |
| `network` | 网络配置 | ✗ |
| `security` | 安全配置 | ✗ |
| `extensions` | 扩展配置 | ✗ |
| `environment` | 环境配置 | ✗ |

### 仿真配置 (simulation)

```yaml
simulation:
  name: "仿真名称"
  description: "仿真描述"
  version: "1.0.0"
  author: "作者"
  created_date: "2024-01-22"
  
  # 时间配置
  time:
    start_time: 0.0      # 开始时间
    end_time: 100.0      # 结束时间
    time_step: 0.1       # 时间步长
    units: "seconds"     # 时间单位
    output_interval: 1.0 # 输出间隔
    
  # 求解器配置
  solver:
    type: "runge_kutta"  # 求解器类型
    order: 4             # 求解器阶数
    tolerance: 1e-6      # 容差
    max_iterations: 1000 # 最大迭代次数
    adaptive_step: false # 自适应步长
    
  # 并行计算配置
  parallel:
    enabled: false       # 是否启用并行
    num_processes: 2     # 进程数
    chunk_size: 50       # 块大小
    backend: "multiprocessing" # 后端类型
```

### 调试配置 (debug)

```yaml
debug:
  enabled: true                    # 启用调试
  session_id: "debug_session"      # 调试会话ID
  log_level: "INFO"                # 日志级别
  log_file: "logs/debug.log"       # 日志文件
  debug_mode: "development"        # 调试模式
  
  # 数据收集配置
  data_collection:
    enabled: true                  # 启用数据收集
    interval: 2.0                  # 收集间隔
    variables: ["var1", "var2"]    # 收集变量
    save_to_file: true             # 保存到文件
    file_path: "debug_data.json"   # 文件路径
    max_file_size: "50MB"          # 最大文件大小
    rotation: true                 # 文件轮转
  
  # 调试仪表板配置
  dashboard:
    enabled: true                  # 启用仪表板
    theme: "dark"                  # 主题
    
    # Web仪表板
    web_dashboard:
      enabled: true                # 启用Web仪表板
      port: 8080                   # 端口
      host: "localhost"            # 主机
      auto_open_browser: false     # 自动打开浏览器
      refresh_rate: 1.0            # 刷新率
      
    # 控制台仪表板
    console_dashboard:
      enabled: false               # 启用控制台仪表板
      update_interval: 3.0         # 更新间隔
      display_format: "table"      # 显示格式
```

### 性能监控配置 (performance)

```yaml
performance:
  enabled: true                    # 启用性能监控
  track_timing: true               # 跟踪时间
  track_memory: true               # 跟踪内存
  track_cpu: true                  # 跟踪CPU
  track_io: false                  # 跟踪IO
  track_network: false             # 跟踪网络
  
  # 性能指标收集
  metrics:
    enabled: true                  # 启用指标收集
    collection_interval: 1.0       # 收集间隔
    save_to_file: true             # 保存到文件
    metrics_file: "metrics.json"   # 指标文件
    buffer_size: 500               # 缓冲区大小
    compression: false             # 压缩
    
  # 性能分析
  analysis:
    enabled: true                  # 启用分析
    generate_report: true          # 生成报告
    report_format: "html"          # 报告格式
    auto_analysis: true            # 自动分析
    threshold_alerts: true         # 阈值警报
    
  # 性能优化
  optimization:
    auto_tune: false               # 自动调优
    cache_enabled: true            # 启用缓存
    memory_limit: "1GB"            # 内存限制
    cpu_limit: 70                  # CPU限制
    gc_optimization: true          # 垃圾回收优化
    
  # 性能阈值
  thresholds:
    max_execution_time: 5.0        # 最大执行时间
    max_memory_usage: 512          # 最大内存使用
    max_cpu_usage: 80              # 最大CPU使用
```

### 可视化配置 (visualization)

```yaml
visualization:
  enabled: true                    # 启用可视化
  theme: "modern"                  # 主题
  color_scheme: "auto"             # 颜色方案
  
  # 实时可视化
  real_time:
    enabled: false                 # 启用实时可视化
    update_interval: 1.0           # 更新间隔
    max_points: 500                # 最大点数
    auto_scale: true               # 自动缩放
    smooth_animation: true         # 平滑动画
    
  # 结果可视化
  plots:
    enabled: true                  # 启用图表
    save_plots: true               # 保存图表
    output_directory: "plots/"     # 输出目录
    format: ["png", "svg"]         # 格式
    dpi: 300                       # DPI
    style: "seaborn"               # 样式
    figsize: [12, 8]               # 图形大小
    font_size: 12                  # 字体大小
    grid: true                     # 网格
    legend: true                   # 图例
    
    # 图表配置
    charts:
      - type: "time_series"         # 时间序列图
        title: "时间序列"
        variables: ["var1", "var2"]
        filename: "time_series"
        subplot_layout: [2, 1]
        
      - type: "control_performance" # 控制性能图
        title: "控制性能"
        variables: ["setpoint", "output"]
        filename: "control_perf"
        include_error: true
        
      - type: "dashboard"           # 仪表板
        title: "系统仪表板"
        filename: "dashboard"
        layout: "grid"
        
      - type: "histogram"           # 直方图
        title: "数据分布"
        filename: "histogram"
        bins: 30
```

### 数据输出配置 (output)

```yaml
output:
  enabled: true                    # 启用输出
  save_history: true               # 保存历史
  history_file: "history.json"     # 历史文件
  output_directory: "results/"     # 输出目录
  
  # 输出格式
  formats:
    json: true                     # JSON格式
    csv: true                      # CSV格式
    hdf5: false                    # HDF5格式
    pickle: false                  # Pickle格式
    parquet: false                 # Parquet格式
    excel: false                   # Excel格式
    
  # 输出内容
  content:
    all_variables: true            # 所有变量
    selected_variables: []         # 选定变量
    metadata: true                 # 元数据
    timestamps: true               # 时间戳
    system_info: true              # 系统信息
    configuration: true            # 配置信息
    
  # 历史数据保存
  history:
    enabled: true                  # 启用历史保存
    save_format: ["json", "csv"]   # 保存格式
    filename_prefix: "results"     # 文件名前缀
    
  # 结果验证
  validation:
    enabled: true                  # 启用验证
    expected_results: {}           # 期望结果
    tolerance: 0.05                # 容差
```

### 分析配置 (analysis)

```yaml
analysis:
  enabled: true                    # 启用分析
  auto_analysis: true              # 自动分析
  analysis_interval: 10.0          # 分析间隔
  
  # 控制性能分析
  control_performance:
    enabled: true                  # 启用控制性能分析
    calculate_metrics: true        # 计算指标
    stability_analysis: true       # 稳定性分析
    frequency_analysis: false      # 频域分析
    settling_time: true            # 调节时间
    overshoot: true                # 超调量
    steady_state_error: true       # 稳态误差
    
  # 系统识别
  system_identification:
    enabled: false                 # 启用系统识别
    method: "least_squares"        # 方法
    model_order: 2                 # 模型阶数
    validation_split: 0.3          # 验证分割
    
  # 统计分析
  statistical:
    enabled: true                  # 启用统计分析
    descriptive_stats: true        # 描述性统计
    correlation_analysis: true     # 相关性分析
    trend_analysis: true           # 趋势分析
    outlier_detection: true        # 异常检测
    distribution_analysis: true    # 分布分析
    
  # 信号处理
  signal_processing:
    enabled: false                 # 启用信号处理
    filtering: false               # 滤波
    fft_analysis: false            # FFT分析
    spectral_analysis: false       # 频谱分析
    
  # 机器学习分析
  machine_learning:
    enabled: false                 # 启用机器学习
    anomaly_detection: false       # 异常检测
    pattern_recognition: false     # 模式识别
    predictive_modeling: false     # 预测建模
    
  # 报告生成
  reporting:
    enabled: true                  # 启用报告
    auto_report: true              # 自动报告
    report_format: "markdown"      # 报告格式
    report_file: "analysis.md"     # 报告文件
    include_plots: true            # 包含图表
    detailed_analysis: true        # 详细分析
```

### 日志配置 (logging)

```yaml
logging:
  enabled: true                    # 启用日志
  log_directory: "logs/"           # 日志目录
  
  # 日志级别配置
  levels:
    root: "INFO"                   # 根日志级别
    simulation: "INFO"             # 仿真日志级别
    agents: "INFO"                 # 智能体日志级别
    components: "DEBUG"            # 组件日志级别
    performance: "INFO"            # 性能日志级别
    error: "ERROR"                 # 错误日志级别
    
  # 日志输出配置
  handlers:
    console:
      enabled: true                # 启用控制台输出
      level: "INFO"                # 控制台级别
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      colored: true                # 彩色输出
      
    file:
      enabled: true                # 启用文件输出
      level: "DEBUG"               # 文件级别
      filename: "simulation.log"   # 文件名
      max_size: "10MB"             # 最大大小
      backup_count: 5              # 备份数量
      encoding: "utf-8"            # 编码
      
    structured:
      enabled: false               # 启用结构化日志
      level: "INFO"                # 结构化级别
      filename: "structured.json"  # 结构化文件
      
    error_file:
      enabled: true                # 启用错误文件
      level: "ERROR"               # 错误级别
      filename: "errors.log"       # 错误文件
      max_size: "5MB"              # 最大大小
      backup_count: 3              # 备份数量
      
    performance_file:
      enabled: true                # 启用性能文件
      level: "INFO"                # 性能级别
      filename: "performance.log"  # 性能文件
      max_size: "20MB"             # 最大大小
      backup_count: 10             # 备份数量
```

### 错误处理配置 (error_handling)

```yaml
error_handling:
  enabled: true                    # 启用错误处理
  error_policy: "strict"           # 错误策略
  
  # 异常处理
  exception_handling:
    continue_on_error: false       # 错误时继续
    log_exceptions: true           # 记录异常
    exception_file: "exceptions.log" # 异常文件
    stack_trace: true              # 堆栈跟踪
    exception_details: true        # 异常详情
    
  # 错误恢复
  recovery:
    enabled: false                 # 启用恢复
    max_retries: 2                 # 最大重试
    retry_delay: 1.0               # 重试延迟
    exponential_backoff: true      # 指数退避
    recovery_strategies: []        # 恢复策略
    
  # 错误分类
  classification:
    enabled: true                  # 启用分类
    critical_errors: ["ComponentFailure", "SolverDivergence"]
    recoverable_errors: ["TemporaryNetworkError"]
    ignored_errors: ["MinorWarning"]
    
  # 错误通知
  notifications:
    enabled: false                 # 启用通知
    email: false                   # 邮件通知
    webhook: false                 # Webhook通知
    slack: false                   # Slack通知
    threshold: "ERROR"             # 通知阈值
    
  # 错误报告
  reporting:
    enabled: true                  # 启用报告
    generate_error_report: true    # 生成错误报告
    error_report_file: "errors.md" # 错误报告文件
    auto_report: true              # 自动报告
    include_context: true          # 包含上下文
```

### 环境配置 (environment)

```yaml
environment:
  current: "development"           # 当前环境
  auto_detect: true                # 自动检测
  
  # 开发环境配置
  development:
    debug: true                    # 调试模式
    verbose_logging: true          # 详细日志
    auto_reload: false             # 自动重载
    hot_reload: false              # 热重载
    profiling: true                # 性能分析
    
  # 生产环境配置
  production:
    debug: false                   # 调试模式
    optimize_performance: true     # 性能优化
    minimal_logging: true          # 最小日志
    compression: true              # 压缩
    monitoring: true               # 监控
    
  # 测试环境配置
  testing:
    mock_external_services: true   # 模拟外部服务
    deterministic_random: true     # 确定性随机
    fast_execution: true           # 快速执行
    test_data_isolation: true      # 测试数据隔离
    coverage_tracking: true        # 覆盖率跟踪
    
  # 环境变量
  variables:
    custom_vars:
      SIMULATION_MODE: "water_control"
      LOG_LEVEL: "INFO"
    override_config: false         # 覆盖配置
    
  # 资源限制
  resources:
    memory_limit: "1GB"            # 内存限制
    cpu_limit: "auto"              # CPU限制
    disk_limit: "auto"             # 磁盘限制
    
  # 部署配置
  deployment:
    containerized: false           # 容器化
    cloud_platform: "none"         # 云平台
    scaling: "manual"              # 扩展方式
```

## 高级功能

### 1. 自定义扩展

```python
class CustomSimulationBuilder(EnhancedSimulationBuilder):
    def _setup_custom_features(self):
        """设置自定义功能"""
        # 添加自定义功能逻辑
        pass
        
    def _setup_enhanced_features(self):
        super()._setup_enhanced_features()
        self._setup_custom_features()
```

### 2. 配置验证

```python
def validate_config(config):
    """验证配置文件"""
    required_sections = ['simulation']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"缺少必需的配置节: {section}")
    return True
```

### 3. 动态配置更新

```python
# 运行时更新配置
builder.enhanced_config['debug']['enabled'] = False
builder._setup_enhanced_features()  # 重新设置功能
```

## 最佳实践

### 1. 配置文件组织

- 使用有意义的文件名和目录结构
- 为不同环境创建不同的配置文件
- 使用配置模板减少重复

### 2. 性能优化

- 只启用需要的功能模块
- 合理设置缓冲区大小和收集间隔
- 在生产环境中禁用调试功能

### 3. 错误处理

- 设置合适的错误策略
- 配置错误分类和通知
- 定期检查错误日志

### 4. 日志管理

- 设置合适的日志级别
- 配置日志轮转避免磁盘空间问题
- 使用结构化日志便于分析

## 故障排除

### 常见问题

1. **配置文件加载失败**
   - 检查文件路径是否正确
   - 验证YAML语法是否正确
   - 确保文件编码为UTF-8

2. **功能模块未启用**
   - 检查对应配置节的`enabled`字段
   - 验证依赖项是否安装
   - 查看日志文件获取详细信息

3. **性能问题**
   - 调整收集间隔和缓冲区大小
   - 禁用不必要的功能模块
   - 检查资源限制设置

### 调试技巧

1. **启用详细日志**
   ```yaml
   logging:
     levels:
       root: "DEBUG"
   ```

2. **使用调试仪表板**
   ```yaml
   debug:
     dashboard:
       web_dashboard:
         enabled: true
         port: 8080
   ```

3. **检查配置加载**
   ```python
   print(builder.enhanced_config)
   ```

## 版本历史

- **v1.0.0** (2024-01-22): 初始版本
  - 基础配置文件结构
  - 增强的SimulationBuilder
  - 调试、性能、可视化等功能模块

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

- 项目主页: [CHS-SDK](https://github.com/your-org/CHS-SDK)
- 问题反馈: [Issues](https://github.com/your-org/CHS-SDK/issues)
- 邮箱: support@chs-sdk.org