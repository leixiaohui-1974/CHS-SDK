# CHS-SDK 知识库系统

## 🚀 快速开始

CHS-SDK知识库是一个智能文档检索和推荐系统，支持语义搜索、关键词搜索和混合搜索功能。

### 1. 构建知识库

首次使用前，需要构建完整的知识库索引：

```bash
# 构建完整知识库（推荐）
python build_complete_knowledge_base.py

# 或者运行测试验证
python test_knowledge_base.py
```

### 2. 快速演示

```bash
# 运行快速演示（无交互）
python quick_demo_knowledge_base.py

# 运行完整演示（包含交互模式）
python demo_knowledge_base_usage.py

# 直接进入交互模式
python demo_knowledge_base_usage.py --interactive
```

## 📚 基本使用

### Python API

```python
import asyncio
from pathlib import Path
from core_lib.knowledge.knowledge_base import KnowledgeBase

async def search_example():
    # 初始化知识库
    project_root = Path.cwd()
    kb = KnowledgeBase(str(project_root))
    await kb.initialize()
    
    try:
        # 语义搜索
        results = await kb.search(
            "如何配置水利仿真参数", 
            search_type="semantic", 
            top_k=5
        )
        
        # 关键词搜索
        results = await kb.search(
            "agent", 
            search_type="keyword", 
            top_k=5
        )
        
        # 混合搜索（推荐）
        results = await kb.search(
            "智能体配置", 
            search_type="hybrid", 
            top_k=5
        )
        
        # 按类型过滤搜索
        results = await kb.search(
            "class", 
            search_type="keyword", 
            filters={"doc_type": "code"}, 
            top_k=5
        )
        
        # 获取推荐
        recommendations = await kb.get_recommendations(
            {"query": "水位控制", "current_file": "controller.py"}, 
            "agent"
        )
        
        # 处理搜索结果
        for result in results:
            print(f"标题: {result.get('title', 'N/A')}")
            print(f"文件: {result.get('file_path', 'N/A')}")
            print(f"相关度: {result.get('score', 0):.3f}")
            print(f"内容: {result.get('content', '')[:200]}...")
            print("-" * 50)
    
    finally:
        await kb.cleanup()

# 运行示例
asyncio.run(search_example())
```

## 🔍 搜索类型

### 1. 语义搜索 (semantic)
- **适用场景**: 概念性查询、自然语言问题
- **优势**: 理解查询意图，找到语义相关的内容
- **示例**: "如何配置水利仿真参数"、"智能体的工作原理"

### 2. 关键词搜索 (keyword)
- **适用场景**: 精确匹配、查找特定术语
- **优势**: 快速准确，适合已知关键词
- **示例**: "agent"、"config"、"simulation"

### 3. 混合搜索 (hybrid)
- **适用场景**: 日常使用，平衡精度和召回率
- **优势**: 结合语义和关键词搜索的优势
- **推荐**: 大多数情况下的最佳选择

## 🎯 高级功能

### 类型过滤

```python
# 搜索代码文件
results = await kb.search(
    "class definition", 
    filters={"doc_type": "code"}
)

# 搜索配置文件
results = await kb.search(
    "parameters", 
    filters={"doc_type": "config"}
)

# 搜索文档文件
results = await kb.search(
    "user guide", 
    filters={"doc_type": "documentation"}
)
```

### 智能推荐

```python
# 基于当前上下文获取推荐
context = {
    "query": "当前查询",
    "current_file": "当前文件路径",
    "project_type": "项目类型"
}

recommendations = await kb.get_recommendations(context, "agent")
```

### 统计信息

```python
# 获取知识库统计
stats = kb.get_statistics()
print(f"知识库状态: {stats['is_initialized']}")
print(f"最后更新: {stats['last_update']}")
print(f"项目根目录: {stats['project_root']}")
```

## 🔧 维护和更新

### 增量更新

```bash
# 启动自动学习系统（监控文件变化）
python demo_auto_learning.py
```

### 手动重建

```bash
# 完全重建知识库
python build_complete_knowledge_base.py
```

## 📁 支持的文件类型

- **代码文件**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`
- **配置文件**: `.yaml`, `.yml`, `.json`, `.xml`, `.ini`, `.toml`
- **文档文件**: `.md`, `.txt`, `.rst`, `.doc`, `.docx`
- **数据文件**: `.csv`, `.sql`

## ⚙️ 配置选项

知识库支持多种配置选项，可以通过配置文件或初始化参数设置：

```python
config = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "vector_db_type": "faiss",
    "search_top_k": 10,
    "recommendation_threshold": 0.7,
    "supported_file_types": [".py", ".yml", ".md"],
    "exclude_dirs": ["__pycache__", ".git", "node_modules"]
}

kb = KnowledgeBase(project_root, config=config)
```

## 🐛 故障排除

### 常见问题

1. **知识库初始化失败**
   ```bash
   # 重新构建知识库
   python build_complete_knowledge_base.py
   ```

2. **搜索结果为空**
   - 确认知识库已正确构建
   - 尝试不同的搜索类型
   - 检查查询关键词是否存在

3. **性能问题**
   - 调整 `search_top_k` 参数
   - 使用类型过滤缩小搜索范围
   - 考虑增量更新而非全量重建

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
kb = KnowledgeBase(project_root, config={"debug": True})
```

## 📖 相关文档

- [详细使用指南](knowledge_base_usage_guide.md)
- [API参考文档](docs/api_reference.md)
- [开发者指南](docs/developer_guide.md)

## 🎯 最佳实践

1. **查询优化**
   - 使用具体、描述性的查询词
   - 优先选择混合搜索
   - 利用类型过滤提高精度

2. **性能优化**
   - 定期运行增量更新
   - 监控知识库大小和性能
   - 根据使用情况调整配置

3. **集成建议**
   - 在IDE插件中集成搜索功能
   - 实现搜索历史和收藏功能
   - 提供用户反馈机制

---

**CHS-SDK知识库** - 让代码和文档检索更智能！ 🚀