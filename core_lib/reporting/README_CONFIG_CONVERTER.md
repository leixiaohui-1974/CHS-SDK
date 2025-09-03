# 配置文件到自然语言转换器

## 概述

`config_to_text_converter.py` 是一个通用的配置文件转换工具，能够将YAML格式的水利系统配置文件转换为易于阅读的自然语言描述，并支持生成Markdown和HTML两种格式的输出文件。

## 功能特性

- **多格式输出**：支持Markdown (.md) 和HTML (.html) 两种输出格式
- **智能解析**：自动识别和解析水利系统组件、智能体、拓扑结构等配置
- **美观样式**：HTML输出包含专业的CSS样式，便于浏览和展示
- **中文友好**：完全支持中文描述，适合国内水利系统项目
- **通用性强**：可处理各种类型的水利系统配置文件

## 安装依赖

在使用转换器之前，请确保安装了必要的依赖包：

```bash
pip install -r requirements.txt
```

依赖包包括：
- `markdown>=3.4.0` - Markdown到HTML转换
- `jinja2>=3.1.0` - HTML模板渲染
- `pyyaml>=6.0` - YAML文件解析

## 使用方法

### 1. 作为独立程序使用

```bash
python config_to_text_converter.py
```

### 2. 作为模块导入使用

```python
from core_lib.reporting.config_to_text_converter import ConfigToTextConverter

# 创建转换器实例
converter = ConfigToTextConverter()

# 转换配置文件
config_dir = "path/to/your/config/directory"
description = converter.convert_to_natural_language(config_dir)

# 保存为Markdown和HTML格式
output_path = "output/description"
converter.save_description(description, output_path, format='both')
```

### 3. 自定义输出格式

```python
# 只生成Markdown格式
converter.save_description(description, output_path, format='markdown')

# 只生成HTML格式
converter.save_description(description, output_path, format='html')

# 同时生成两种格式（默认）
converter.save_description(description, output_path, format='both')
```

## 支持的配置文件结构

转换器能够识别和处理以下配置文件结构：

### 1. 系统元数据
```yaml
metadata:
  name: "系统名称"
  description: "系统描述"
  version: "1.0"
  category: "agent_based"
```

### 2. 水利组件
```yaml
components:
  reservoir_1:
    type: Reservoir
    initial_state:
      volume: 21000000
      water_level: 14.0
    parameters:
      surface_area: 1500000
```

### 3. 系统拓扑
```yaml
topology:
  connections:
    - upstream: reservoir_1
      downstream: gate_1
```

### 4. 智能体配置
```yaml
agents:
  control_agent_gate_1:
    type: LocalControlAgent
    controller:
      type: PIDController
      parameters:
        Kp: -0.5
        Ki: -0.01
        Kd: -0.1
```

### 5. 仿真和分析配置
```yaml
simulation:
  duration: 300
  time_step: 1.0

analysis:
  target_water_level: 12.0
  generate_report: true
```

## 输出示例

### Markdown格式输出
转换器会生成结构化的Markdown文档，包含：
- 系统概述
- 水利系统组件详细描述
- 系统拓扑结构
- 智能体控制系统
- 仿真和分析配置
- 系统总结

### HTML格式输出
HTML输出包含：
- 专业的CSS样式设计
- 响应式布局
- 颜色编码的不同部分
- 时间戳信息
- 易于打印和分享的格式

## 自定义和扩展

### 1. 添加新的组件类型

在 `__init__` 方法中的 `component_descriptions` 字典中添加新的组件类型：

```python
self.component_descriptions = {
    'Reservoir': '水库',
    'Gate': '闸门',
    'YourNewComponent': '您的新组件',  # 添加新类型
    # ...
}
```

### 2. 自定义HTML样式

修改 `html_template` 中的CSS样式来自定义HTML输出的外观。

### 3. 添加新的描述方法

可以添加新的方法来处理特定的配置部分：

```python
def describe_your_section(self, your_config: Dict[str, Any]) -> str:
    """描述您的配置部分"""
    # 实现您的描述逻辑
    return description
```

## 注意事项

1. **文件编码**：确保YAML配置文件使用UTF-8编码
2. **路径问题**：使用绝对路径或相对于当前工作目录的正确路径
3. **依赖安装**：确保所有依赖包都已正确安装
4. **配置格式**：配置文件应遵循标准的YAML格式

## 故障排除

### 常见问题

1. **配置目录不存在**
   - 检查配置文件路径是否正确
   - 确保目录存在且包含YAML文件

2. **依赖包缺失**
   - 运行 `pip install -r requirements.txt` 安装依赖

3. **YAML解析错误**
   - 检查YAML文件格式是否正确
   - 确保缩进和语法符合YAML标准

4. **编码问题**
   - 确保文件使用UTF-8编码保存

## 版本历史

- **v1.0** (2025-01-04)
  - 初始版本
  - 支持Markdown和HTML输出
  - 基本的配置文件解析功能

## 贡献

欢迎提交问题报告和功能请求。如需贡献代码，请遵循项目的代码规范。

## 许可证

本项目遵循CHS-SDK的许可证条款。