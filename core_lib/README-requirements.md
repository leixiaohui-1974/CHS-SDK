# Core Library Requirements

本目录包含了 `core_lib` 模块的依赖包配置文件。

## 文件说明

### 📦 requirements.txt
**完整依赖包** - 包含所有功能模块所需的依赖包
- 适用于生产环境
- 包含所有核心功能、可选功能和扩展功能
- 文件较大，安装时间较长

### ⚡ requirements-minimal.txt  
**最小依赖包** - 仅包含运行核心功能必需的依赖包
- 适用于轻量级部署
- 仅包含核心数值计算、数据库、验证等基础功能
- 文件较小，安装快速

### 🛠️ requirements-dev.txt
**开发依赖包** - 包含开发和测试所需的所有工具
- 适用于开发环境
- 包含代码质量工具、测试框架、文档生成等
- 基于 `requirements.txt`，添加开发工具

## 安装方式

### 生产环境
```bash
# 安装完整依赖
pip install -r requirements.txt

# 或安装最小依赖
pip install -r requirements-minimal.txt
```

### 开发环境
```bash
# 安装开发依赖（包含所有工具）
pip install -r requirements-dev.txt
```

### 虚拟环境推荐
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 依赖包分类

### 核心依赖
- **数值计算**: numpy, pandas, scipy
- **数据库**: sqlalchemy, alembic
- **数据验证**: pydantic
- **机器学习**: scikit-learn

### 可视化
- **基础绘图**: matplotlib, seaborn
- **高级可视化**: plotly, bokeh (可选)

### 文件处理
- **模板引擎**: jinja2
- **配置文件**: pyyaml, toml
- **Excel处理**: openpyxl
- **PDF生成**: reportlab

### 开发工具
- **代码格式化**: black, isort
- **代码检查**: flake8, mypy
- **测试框架**: pytest, pytest-cov
- **文档生成**: sphinx, mkdocs

### 可选功能
- **Web框架**: fastapi, uvicorn
- **缓存**: redis
- **AI/ML**: transformers, torch
- **向量数据库**: faiss, chromadb

## 版本兼容性

- **Python**: >= 3.8
- **主要依赖**: 使用稳定版本，避免过新或过旧的版本
- **兼容性**: 所有依赖包都经过兼容性测试

## 故障排除

### 常见问题

1. **安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 使用国内镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

2. **版本冲突**
   ```bash
   # 查看已安装包
   pip list
   
   # 卸载冲突包
   pip uninstall package_name
   
   # 重新安装
   pip install -r requirements.txt
   ```

3. **权限问题**
   ```bash
   # 使用用户安装
   pip install --user -r requirements.txt
   ```

### 性能优化

1. **使用conda** (推荐)
   ```bash
   conda install numpy pandas scipy matplotlib
   pip install -r requirements.txt
   ```

2. **预编译包**
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

## 更新说明

- 定期更新依赖包版本
- 新增功能时更新requirements文件
- 保持向后兼容性
- 测试新版本兼容性

## 贡献指南

修改requirements文件时请：
1. 更新版本号
2. 测试兼容性
3. 更新文档
4. 提交PR说明变更原因
