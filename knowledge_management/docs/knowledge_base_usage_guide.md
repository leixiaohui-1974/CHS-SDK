# CHS-SDK 知识库使用指南

## 概述

CHS-SDK 知识库是一个智能化的文档检索和推荐系统，基于语义搜索技术，能够快速定位项目中的智能体定义、配置模式、API文档等关键信息。

## 功能特性

### 🔍 多种搜索模式
- **语义搜索**：基于内容语义理解的智能搜索
- **关键词搜索**：传统的关键词匹配搜索
- **混合搜索**：结合语义和关键词的综合搜索

### 📚 支持的文档类型
- Python 代码文件（智能体定义、API接口）
- Markdown 文档（架构设计、使用指南）
- YAML 配置文件（场景配置、系统参数）
- 文本文件（说明文档、日志模板）

### 🤖 智能推荐
- 基于上下文的智能体推荐
- 配置模板智能匹配
- 相关文档自动关联

## 快速开始

### 1. 初始化知识库

```python
from core_lib.knowledge.knowledge_base import KnowledgeBase
import asyncio

async def init_knowledge_base():
    # 创建知识库实例
    kb = KnowledgeBase(project_root="/path/to/CHS-SDK")
    
    # 初始化（首次运行会自动构建索引）
    success = await kb.initialize()
    
    if success:
        print("知识库初始化成功！")
    else:
        print("知识库初始化失败")
    
    return kb

# 运行初始化
kb = asyncio.run(init_knowledge_base())
```

### 2. 基本搜索

```python
# 语义搜索 - 推荐用于概念性查询
results = await kb.search(
    query="智能体架构设计",
    search_type="semantic",
    top_k=5
)

# 关键词搜索 - 适用于精确匹配
results = await kb.search(
    query="WaterReservoirAgent",
    search_type="keyword",
    top_k=5
)

# 混合搜索 - 平衡语义理解和精确匹配
results = await kb.search(
    query="洪水控制配置",
    search_type="hybrid",
    top_k=5
)
```

### 3. 高级搜索（带过滤器）

```python
# 按文档类型过滤
results = await kb.search(
    query="agent configuration",
    search_type="semantic",
    filters={
        "doc_type": "agent_definition",
        "file_type": "python"
    },
    top_k=10
)

# 按标签过滤
results = await kb.search(
    query="水库控制",
    search_type="hybrid",
    filters={
        "tags": ["agent", "control"]
    },
    top_k=5
)
```

## 搜索结果格式

每个搜索结果包含以下信息：

```python
{
    "content": "文档内容",
    "title": "文档标题",
    "score": 0.85,  # 相似度分数 (0-1)
    "metadata": {
        "id": 123,
        "file_path": "agents/water_system/reservoir_agent.py",
        "doc_type": "agent_definition",
        "file_type": "python",
        "tags": ["agent", "water_system", "control"],
        "created_at": "2025-09-02T20:26:20.400485",
        "section_title": "WaterReservoirAgent类定义"
    }
}
```

## 智能推荐系统

### 获取智能体推荐

```python
# 基于当前上下文推荐相关智能体
recommendations = await kb.get_recommendations(
    context={
        "current_agent": "WaterReservoirAgent",
        "scenario": "flood_control",
        "task_type": "water_level_control"
    },
    recommendation_type="agent"
)
```

### 获取配置推荐

```python
# 推荐相关配置模板
config_recommendations = await kb.get_recommendations(
    context={
        "agent_type": "LocalControlAgent",
        "domain": "water_system"
    },
    recommendation_type="configuration"
)
```

## 知识库维护

### 手动重建索引

```python
# 强制重建整个知识库索引
await kb.initialize(force_rebuild=True)
```

### 增量更新

```python
# 检查文件变更并增量更新
await kb.update_index()
```

### 索引单个文件

```python
from pathlib import Path

# 索引新添加的文件
file_path = Path("agents/new_agent.py")
await kb.index_file(file_path)
```

## 配置参数

知识库的行为可以通过 `core_lib/knowledge/knowledge_config.yml` 进行配置：

```yaml
# 搜索参数
search_parameters:
  default_top_k: 10          # 默认返回结果数
  max_top_k: 50             # 最大返回结果数
  similarity_threshold: 0.1  # 相似度阈值
  hybrid_weights:
    semantic: 0.7           # 语义搜索权重
    keyword: 0.3            # 关键词搜索权重

# 文本嵌入模型
embedding_model:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  cache_dir: "models/embeddings"

# 索引配置
knowledge_indexer:
  supported_file_types: [".py", ".md", ".yml", ".yaml", ".txt"]
  exclude_directories: ["__pycache__", ".git", "node_modules"]
```

## 性能优化建议

### 1. 搜索策略选择
- **精确查找**：使用关键词搜索
- **概念理解**：使用语义搜索
- **综合查询**：使用混合搜索

### 2. 结果数量控制
```python
# 对于快速预览，使用较小的 top_k
quick_results = await kb.search(query, top_k=3)

# 对于详细分析，使用较大的 top_k
detailed_results = await kb.search(query, top_k=20)
```

### 3. 过滤器使用
```python
# 使用过滤器缩小搜索范围，提高性能
filtered_results = await kb.search(
    query="control algorithm",
    filters={"file_type": "python", "doc_type": "agent_definition"},
    top_k=10
)
```

## 故障排除

### 搜索无结果
1. 检查知识库是否已初始化
2. 确认搜索查询的语言和术语
3. 尝试降低相似度阈值
4. 使用不同的搜索类型

### 性能问题
1. 减少 `top_k` 参数值
2. 使用更具体的过滤器
3. 考虑重建索引以优化性能

### 索引问题
```python
# 检查知识库统计信息
stats = kb.get_statistics()
print(f"总文档数: {stats.get('total_documents', 0)}")
print(f"索引状态: {stats.get('index_status', 'unknown')}")

# 强制重建索引
if stats.get('total_documents', 0) == 0:
    await kb.initialize(force_rebuild=True)
```

## 最佳实践

### 1. 查询优化
- 使用具体而清晰的查询词
- 结合领域专业术语
- 适当使用英文和中文混合查询

### 2. 结果处理
```python
# 处理搜索结果的最佳实践
results = await kb.search("水位控制算法")

for result in results:
    # 检查相似度分数
    if result['score'] > 0.3:
        print(f"标题: {result['title']}")
        print(f"文件: {result['metadata']['file_path']}")
        print(f"相似度: {result['score']:.3f}")
        print(f"内容预览: {result['content'][:200]}...\n")
```

### 3. 定期维护
```python
# 建议的维护脚本
async def maintain_knowledge_base():
    kb = KnowledgeBase(project_root=".")
    
    # 检查是否需要更新
    stats = kb.get_statistics()
    last_update = stats.get('last_indexed')
    
    # 如果超过24小时未更新，执行增量更新
    if should_update(last_update):
        await kb.update_index()
        print("知识库已更新")
```

## API 参考

### KnowledgeBase 类

#### 主要方法
- `initialize(force_rebuild=False)`: 初始化知识库
- `search(query, search_type, filters, top_k)`: 搜索文档
- `get_recommendations(context, recommendation_type)`: 获取推荐
- `update_index(incremental=True)`: 更新索引
- `get_statistics()`: 获取统计信息
- `cleanup()`: 清理资源

#### 搜索类型
- `"semantic"`: 语义搜索
- `"keyword"`: 关键词搜索
- `"hybrid"`: 混合搜索

#### 文档类型
- `"agent_definition"`: 智能体定义
- `"configuration"`: 配置文件
- `"documentation"`: 文档说明
- `"api_reference"`: API参考
- `"code_example"`: 代码示例

## 扩展开发

### 自定义文档处理器

```python
from core_lib.knowledge.knowledge_indexer import KnowledgeIndexer

class CustomIndexer(KnowledgeIndexer):
    async def _process_custom_file(self, file_path, relative_path):
        # 实现自定义文件类型的处理逻辑
        documents = []
        # ... 处理逻辑
        return documents
```

### 自定义搜索过滤器

```python
# 扩展搜索过滤器
custom_filters = {
    "complexity_level": "advanced",
    "last_modified": "2025-01-01",
    "author": "system"
}

results = await kb.search(
    query="复杂控制算法",
    filters=custom_filters
)
```

---

## 联系支持

如果在使用过程中遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 检查配置文件设置
3. 参考故障排除部分
4. 提交 Issue 到项目仓库

---

*最后更新: 2025-09-02*

## 概述

CHS-SDK知识库是一个智能文档检索和推荐系统，支持语义搜索、关键词搜索和混合搜索功能。系统已成功索引了4510个文档，涵盖代码文件、配置文件、文档等多种类型。

## 主要功能

### 1. 语义搜索
基于深度学习的语义理解，能够理解查询意图并返回相关文档。

### 2. 关键词搜索
传统的关键词匹配搜索，适用于精确查找特定术语。

### 3. 混合搜索
结合语义搜索和关键词搜索的优势，提供更全面的搜索结果。

### 4. 智能推荐
基于用户查询历史和文档相似性的智能推荐功能。

## 使用方法

### 基本使用

```python
from core_lib.knowledge.knowledge_base import KnowledgeBase

# 初始化知识库
kb = KnowledgeBase()

# 语义搜索
results = kb.search("如何配置水利仿真参数", search_type="semantic")

# 关键词搜索
results = kb.search("reservoir", search_type="keyword")

# 混合搜索（推荐）
results = kb.search("智能体配置", search_type="hybrid")

# 查看搜索结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"文件: {result['file_path']}")
    print(f"相关度: {result['score']:.3f}")
    print(f"内容摘要: {result['content'][:200]}...")
    print("-" * 50)
```

### 高级功能

#### 1. 获取推荐文档
```python
# 基于查询获取推荐
recommendations = kb.get_recommendations("水位控制算法")

# 基于文档ID获取相似文档
similar_docs = kb.get_recommendations(doc_id="specific_doc_id")
```

#### 2. 获取统计信息
```python
# 获取知识库统计
stats = kb.get_stats()
print(f"总文档数: {stats['total_documents']}")
print(f"文件类型分布: {stats['file_types']}")
```

#### 3. 按类型搜索
```python
# 搜索特定类型的文档
code_results = kb.search("函数定义", doc_type="code")
config_results = kb.search("参数配置", doc_type="config")
doc_results = kb.search("使用说明", doc_type="documentation")
```

## 测试脚本

项目提供了完整的测试脚本来验证知识库功能：

```bash
# 运行知识库测试
python test_knowledge_base.py
```

测试脚本会验证以下功能：
- 知识库初始化
- 语义搜索功能
- 关键词搜索功能
- 混合搜索功能
- 推荐功能
- 特定领域查询

## 知识库构建

### 完整构建
```bash
# 构建完整知识库
python build_complete_knowledge_base.py
```

### 增量更新
```bash
# 自动学习和增量更新
python demo_auto_learning.py
```

## 支持的文件类型

知识库支持以下文件类型：
- **代码文件**: .py, .js, .ts, .java, .cpp, .c, .h
- **配置文件**: .yaml, .yml, .json, .xml, .ini, .toml
- **文档文件**: .md, .txt, .rst, .doc, .docx
- **数据文件**: .csv, .sql

## 配置选项

知识库支持多种配置选项：

```python
# 自定义配置
config = {
    "semantic_search": True,  # 启用语义搜索
    "keyword_search": True,   # 启用关键词搜索
    "auto_update": True,      # 启用自动更新
    "max_results": 10,        # 最大搜索结果数
    "similarity_threshold": 0.5  # 相似度阈值
}

kb = KnowledgeBase(config=config)
```

## 性能优化

### 1. 索引优化
- 知识库使用向量索引加速语义搜索
- 支持增量索引更新，避免全量重建

### 2. 缓存机制
- 搜索结果缓存，提高重复查询性能
- 文档嵌入向量缓存，减少计算开销

### 3. 并行处理
- 支持多线程文档处理
- 批量向量计算优化

## 故障排除

### 常见问题

1. **知识库初始化失败**
   - 检查 `knowledge_base/config.json` 文件是否存在
   - 运行 `build_complete_knowledge_base.py` 重新构建

2. **搜索结果为空**
   - 确认知识库已正确构建
   - 检查查询关键词是否存在于文档中
   - 尝试使用不同的搜索类型

3. **性能问题**
   - 检查文档数量是否过大
   - 考虑调整相似度阈值
   - 使用更具体的查询词

### 调试模式

```python
# 启用调试模式
kb = KnowledgeBase(debug=True)

# 查看详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 最佳实践

1. **查询优化**
   - 使用具体、描述性的查询词
   - 结合多种搜索类型获得最佳结果
   - 利用文档类型过滤缩小搜索范围

2. **维护建议**
   - 定期运行增量更新
   - 监控知识库性能指标
   - 根据使用情况调整配置参数

3. **集成建议**
   - 在应用中集成搜索API
   - 实现用户查询历史记录
   - 提供搜索结果反馈机制

## 扩展功能

知识库系统支持以下扩展：
- 自定义文档处理器
- 插件式搜索引擎
- 外部数据源集成
- RESTful API接口

通过这些功能，CHS-SDK知识库为开发者提供了强大的文档检索和知识管理能力。