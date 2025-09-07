# 泵站控制系统示例 (Pump Control System Examples)

本文件夹包含了完整的泵站控制系统示例，展示了如何使用CHS-SDK进行水泵的建模、控制和仿真。

## 📁 文件夹结构

```
pump_control_system/
├── basic_examples/          # 基础示例
│   └── basic_pump_station.py
├── advanced_examples/       # 高级示例
│   ├── refactored_pump_station.py
│   └── pump_station_with_common_agents.py
├── notebooks/               # Jupyter笔记本
│   └── pump_model_tutorial.ipynb
├── docs/                    # 文档
│   ├── README.md
│   └── pump_model_documentation.md
└── README.md               # 本文件
```

## 🚀 快速开始

### 1. 基础示例
```bash
cd basic_examples
python basic_pump_station.py
```

### 2. 高级示例
```bash
cd advanced_examples
python refactored_pump_station.py
python pump_station_with_common_agents.py
```

### 3. 交互式学习
```bash
cd notebooks
jupyter notebook pump_model_tutorial.ipynb
```

## 📚 示例说明

### 基础示例 (Basic Examples)
- **basic_pump_station.py**: 展示基本的泵站控制逻辑，包含多水泵协同控制

### 高级示例 (Advanced Examples)
- **refactored_pump_station.py**: 使用SimulationBuilder重构的泵站控制
- **pump_station_with_common_agents.py**: 使用通用智能体的泵站控制

### 笔记本 (Notebooks)
- **pump_model_tutorial.ipynb**: 水泵模型的详细教程和可视化

## 🔧 技术特性

- **多水泵协同控制**: 展示如何控制多个水泵机组
- **需求响应**: 根据流量需求动态调整水泵运行
- **功率管理**: 考虑水泵的功率消耗
- **可视化**: 提供完整的仿真结果可视化

## 📖 相关文档

- [水泵模型文档](docs/pump_model_documentation.md)
- [原始README](docs/README.md)

## ⚠️ 注意事项

1. 确保已安装所有依赖包
2. 从项目根目录运行示例
3. 所有示例都需要 `end_time` 参数（不再有默认值）
