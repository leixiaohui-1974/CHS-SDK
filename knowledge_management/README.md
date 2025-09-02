# CHS-SDK 知识库管理

本目录包含了CHS-SDK项目中所有与知识库相关的代码、文档、测试和工具。

## 目录结构

```
knowledge_management/
├── README.md              # 本文件，说明目录结构和使用方法
├── scripts/               # 知识库构建和管理脚本
├── tests/                 # 知识库功能测试文件
├── docs/                  # 知识库相关文档
├── demos/                 # 知识库使用演示和示例
└── tools/                 # 知识库调试和诊断工具
```

## 各目录详细说明

### 📁 scripts/ - 构建和管理脚本

- **build_complete_knowledge_base.py** - 完整知识库构建脚本
- **force_rebuild_knowledge_base.py** - 强制重建知识库索引
- **debug_faiss_search.py** - FAISS搜索调试脚本
- **debug_knowledge_indexer.py** - 知识索引器调试脚本
- **fix_recommendation_engine.py** - 推荐引擎修复脚本
- **fix_search_threshold.py** - 搜索阈值修复脚本

### 🧪 tests/ - 功能测试

- **test_knowledge_base.py** - 知识库核心功能测试
- **test_knowledge_base_demo.py** - 知识库演示测试
- **test_agent_search.py** - 智能体搜索功能测试
- **test_auto_learning.py** - 自动学习系统测试
- **test_recommendation_engine.py** - 推荐引擎测试
- **final_recommendation_test.py** - 推荐功能最终测试
- **interactive_knowledge_test.py** - 交互式知识库测试工具

### 📚 docs/ - 文档

- **README_KNOWLEDGE_BASE.md** - 知识库系统总览
- **knowledge_base_usage_guide.md** - 详细使用指南

### 🎯 demos/ - 演示和示例

- **demo_knowledge_base_usage.py** - 知识库使用演示
- **quick_demo_knowledge_base.py** - 快速演示脚本
- **demo_auto_learning.py** - 自动学习系统演示

### 🔧 tools/ - 调试和诊断工具

- **diagnose_search_issues.py** - 搜索问题诊断工具
- **debug_recommendation_scoring.py** - 推荐评分调试工具
- **debug_semantic_search.py** - 语义搜索调试工具

## 快速开始

### 1. 构建知识库

```bash
# 首次构建完整知识库
python knowledge_management/scripts/build_complete_knowledge_base.py

# 或强制重建（如果遇到问题）
python knowledge_management/scripts/force_rebuild_knowledge_base.py
```

### 2. 测试知识库功能

```bash
# 运行完整功能测试
python knowledge_management/tests/test_knowledge_base.py

# 交互式测试（推荐）
python knowledge_management/tests/interactive_knowledge_test.py
```

### 3. 快速演示

```bash
# 快速演示主要功能
python knowledge_management/demos/quick_demo_knowledge_base.py

# 详细使用演示
python knowledge_management/demos/demo_knowledge_base_usage.py
```

## 故障排除

如果遇到问题，可以使用以下诊断工具：

```bash
# 诊断搜索问题
python knowledge_management/tools/diagnose_search_issues.py

# 调试语义搜索
python knowledge_management/tools/debug_semantic_search.py

# 调试推荐评分
python knowledge_management/tools/debug_recommendation_scoring.py
```

## 相关文档

- [知识库系统总览](docs/README_KNOWLEDGE_BASE.md)
- [详细使用指南](docs/knowledge_base_usage_guide.md)
- [CHS-SDK主文档](../docs/)

## 注意事项

1. **首次使用**：请先运行构建脚本创建知识库索引
2. **性能优化**：大型项目建议使用增量更新而非全量重建
3. **调试模式**：遇到问题时可启用调试模式获取详细日志
4. **定期维护**：建议定期运行测试脚本验证知识库功能

---

**CHS-SDK知识库管理** - 让代码和文档检索更智能！ 🚀