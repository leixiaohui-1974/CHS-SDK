# 执行器和传感器干扰分析 - Debug版本

## 快速开始

### 1. 测试环境
```bash
python test_app.py
```

### 2. 启动应用
```bash
python start_app.py
```

### 3. 手动启动
```bash
streamlit run actuator_sensor_disturbance_streamlit.py
```

## 功能特性

### 🎲 示例数据生成
- 点击侧边栏的"生成示例数据"按钮
- 自动生成包含3个闸门的模拟数据
- 支持下载CSV格式的示例数据

### 📊 数据分析
- **执行器分析**: 开度稳定性、响应速度、噪声特征
- **传感器分析**: 测量精度、精密度、噪声水平
- **交互式图表**: 使用Plotly创建可交互的可视化

### 🔧 错误处理
- 自动检测数据格式问题
- 处理NaN值和编码问题
- 提供详细的错误信息和建议

## 数据格式要求

### 必需的列名
- `time`: 时间序列
- `Gate_1_opening`: 1号闸门开度
- `Gate_1_upstream_level`: 1号闸门上游水位
- `Gate_2_opening`: 2号闸门开度
- `Gate_2_upstream_level`: 2号闸门上游水位
- `Gate_3_opening`: 3号闸门开度
- `Gate_3_upstream_level`: 3号闸门上游水位

### 数据要求
- CSV格式
- 数值型数据
- 支持UTF-8、GBK、Latin-1编码

## 故障排除

### 常见问题

1. **依赖包缺失**
   ```bash
   pip install streamlit pandas numpy matplotlib scipy plotly
   ```

2. **端口被占用**
   ```bash
   streamlit run actuator_sensor_disturbance_streamlit.py --server.port 8502
   ```

3. **数据加载失败**
   - 检查CSV文件格式
   - 确保包含必需的列
   - 检查数据编码

### 调试模式

启用详细日志：
```bash
streamlit run actuator_sensor_disturbance_streamlit.py --logger.level debug
```

## 文件说明

- `actuator_sensor_disturbance_streamlit.py`: 主应用文件
- `start_app.py`: 简化启动脚本
- `test_app.py`: 功能测试脚本
- `simple_flow_diagram.md`: 业务流程图
- `requirements_streamlit.txt`: 依赖包列表
- `README_DEBUG.md`: 本说明文件

## 开发说明

### 代码结构
```
ActuatorSensorDisturbanceAnalyzer
├── __init__()                    # 初始化
├── generate_sample_data()        # 生成示例数据
├── load_data()                   # 加载数据
├── extract_disturbance_features() # 提取特征
├── create_actuator_plots()       # 创建执行器图表
├── create_sensor_plots()         # 创建传感器图表
└── create_comparison_plots()     # 创建对比图表
```

### 主要改进
1. **错误处理**: 添加了完善的异常处理
2. **数据验证**: 检查数据完整性和格式
3. **用户反馈**: 添加进度条和状态提示
4. **示例数据**: 内置示例数据生成功能
5. **编码支持**: 支持多种文件编码格式

## 联系支持

如有问题，请检查：
1. 运行 `python test_app.py` 查看测试结果
2. 查看控制台错误信息
3. 检查数据文件格式
