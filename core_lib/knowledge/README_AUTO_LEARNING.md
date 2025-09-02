# CHS-SDK 知识库自动学习系统

## 概述

CHS-SDK 知识库自动学习系统是一个智能的代码监控和学习工具，能够自动监控项目文件变更，实时更新知识库索引，并为大模型和IDE插件提供最新的代码上下文信息。

## 核心功能

### 🔍 实时文件监控
- **文件系统监控**: 使用 `watchdog` 库实时监控项目文件变更
- **智能过滤**: 支持自定义文件模式匹配和忽略规则
- **防抖处理**: 避免频繁变更触发多次处理
- **批量处理**: 高效的批量文件处理机制

### 🧠 智能学习机制
- **增量索引**: 只处理变更的文件，提高效率
- **语义分析**: 自动分析代码语义并更新搜索索引
- **类型识别**: 智能识别智能体、配置、文档等不同类型文件
- **相似度计算**: 基于内容相似度判断变更重要性

### 🔄 Git 集成
- **变更同步**: 自动同步Git提交的文件变更
- **分支监控**: 支持多分支监控
- **提交分析**: 分析提交历史中的文件变更
- **自动提交**: 可选的自动提交知识库更新

### 📊 性能优化
- **多线程处理**: 并行处理多个文件变更
- **缓存机制**: 文件哈希缓存避免重复处理
- **内存管理**: 智能内存管理和垃圾回收
- **资源限制**: 可配置的CPU和内存使用限制

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    自动学习系统架构                          │
├─────────────────────────────────────────────────────────────┤
│  文件系统监控层                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 文件监控器   │  │ 变更检测器   │  │ 防抖处理器   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  智能处理层                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 类型分析器   │  │ 内容解析器   │  │ 相似度计算   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  知识库更新层                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 索引更新器   │  │ 搜索引擎     │  │ 推荐系统     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  集成接口层                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Git 集成     │  │ IDE 接口     │  │ API 服务     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
cd core_lib/knowledge
pip install -r requirements.txt
```

### 2. 基础使用

```python
from core_lib.knowledge.auto_learning import create_auto_learning_system

# 创建自动学习系统
auto_learner = create_auto_learning_system(
    project_root="/path/to/your/project"
)

# 启动监控
with auto_learner:
    print("自动学习系统正在运行...")
    # 系统会自动监控文件变更并更新知识库
    time.sleep(60)  # 运行1分钟
```

### 3. 使用启动脚本

```bash
# 启动自动学习系统
python scripts/start_auto_learning.py start --daemon

# 查看状态
python scripts/start_auto_learning.py status

# 停止系统
python scripts/start_auto_learning.py stop

# 强制重建索引
python scripts/start_auto_learning.py rebuild

# 同步Git变更
python scripts/start_auto_learning.py sync-git

# 系统诊断
python scripts/start_auto_learning.py diagnose
```

### 4. 集成到知识库

```python
from core_lib.knowledge.knowledge_base import KnowledgeBase

# 创建启用自动学习的知识库
kb = KnowledgeBase(
    project_root="/path/to/project",
    config_path="knowledge_config.yml"  # 确保配置中启用了auto_learning
)

# 初始化（会自动启动学习系统）
await kb.initialize()

# 知识库会自动学习项目变更
# 使用搜索功能时会获得最新的代码信息
results = await kb.semantic_search("智能体配置")
```

## 配置选项

### 基础配置

```yaml
# auto_learning_config.yml
base:
  enabled: true
  learning_mode: "realtime"  # realtime, batch, scheduled
  log_level: "INFO"

file_monitoring:
  monitor_patterns:
    - "*.py"
    - "*.yml"
    - "*.yaml"
    - "*.md"
    - "*.txt"
    - "*.json"
  
  ignore_patterns:
    - "__pycache__"
    - ".git"
    - ".vscode"
    - "node_modules"
    - "*.pyc"
  
  max_file_size: 10485760  # 10MB
```

### 处理配置

```yaml
change_processing:
  batch_size: 10
  processing_interval: 5.0
  debounce_time: 2.0
  max_workers: 4
  processing_timeout: 30
  max_retries: 3
```

### Git 集成配置

```yaml
git_integration:
  enabled: true
  auto_commit: false
  monitored_branches: ["main", "master", "develop"]
  sync_interval: 300  # 5分钟
  ignore_commit_patterns:
    - "^Merge"
    - "^Revert"
```

### 智能学习配置

```yaml
intelligent_learning:
  enable_smart_analysis: true
  similarity_threshold: 0.1
  
  learning_weights:
    code_changes: 1.0
    config_changes: 0.8
    doc_changes: 0.6
    test_changes: 0.7
  
  auto_classification:
    agents:
      patterns: ["**/agents/**", "**/agent_*.py"]
      weight: 1.0
    configs:
      patterns: ["**/config/**", "*.yml", "*.yaml"]
      weight: 0.8
```

## API 接口

### AutoLearningSystem 类

```python
class AutoLearningSystem:
    def __init__(self, project_root, knowledge_indexer, semantic_search, recommendation_engine)
    def start_monitoring(self) -> None
    def stop_monitoring(self) -> None
    def queue_file_change(self, file_path: str, event_type: str) -> None
    def force_rebuild_index(self) -> None
    def sync_with_git(self, since_commit: Optional[str] = None) -> None
    def get_learning_stats(self) -> LearningStats
    def get_git_changes(self, since_commit: Optional[str] = None) -> List[str]
```

### 统计信息

```python
@dataclass
class LearningStats:
    total_files_monitored: int
    files_processed: int
    files_indexed: int
    files_failed: int
    last_update: Optional[datetime]
    processing_time: float
    errors: List[str]
```

## 使用场景

### 1. 开发环境集成

在开发过程中，自动学习系统可以：
- 实时监控代码变更
- 自动更新智能体定义
- 保持配置模板最新
- 为IDE提供最新的代码补全信息

### 2. CI/CD 集成

在持续集成流程中：
- 自动同步代码库变更
- 更新知识库索引
- 生成变更报告
- 验证配置一致性

### 3. 团队协作

在团队开发中：
- 共享最新的代码知识
- 自动发现新的智能体
- 同步配置变更
- 维护文档一致性

### 4. 大模型训练

为大模型提供：
- 最新的代码上下文
- 实时的API文档
- 动态的配置示例
- 智能的代码推荐

## 性能优化

### 1. 文件过滤优化

```python
# 优化文件监控模式
monitor_patterns = [
    "*.py",      # Python 代码
    "*.yml",     # YAML 配置
    "*.md"       # 文档文件
]

# 忽略不重要的文件
ignore_patterns = [
    "__pycache__",
    ".git",
    "*.pyc",
    "*.log",
    "node_modules"
]
```

### 2. 批处理优化

```python
# 调整批处理参数
processing_config = {
    'batch_size': 20,           # 增加批处理大小
    'processing_interval': 3.0, # 减少处理间隔
    'debounce_time': 1.0,      # 减少防抖时间
    'max_workers': 8           # 增加工作线程
}
```

### 3. 内存优化

```python
# 配置内存限制
performance_config = {
    'memory_limit': 1024,      # 1GB 内存限制
    'auto_gc': True,           # 启用自动垃圾回收
    'gc_interval': 300,        # 5分钟GC间隔
    'cache_size': 1000         # 缓存大小
}
```

## 故障排除

### 常见问题

1. **文件监控不工作**
   - 检查文件权限
   - 验证监控模式配置
   - 查看日志文件

2. **处理速度慢**
   - 增加工作线程数
   - 优化文件过滤规则
   - 检查磁盘I/O性能

3. **内存使用过高**
   - 减少批处理大小
   - 启用自动垃圾回收
   - 限制缓存大小

4. **Git集成失败**
   - 检查Git仓库状态
   - 验证分支权限
   - 查看Git配置

### 调试模式

```python
# 启用调试模式
debug_config = {
    'enabled': True,
    'verbose_logging': True,
    'enable_profiling': True,
    'collect_stats': True
}

# 查看详细日志
import logging
logging.getLogger('chs_auto_learning').setLevel(logging.DEBUG)
```

### 诊断工具

```bash
# 运行系统诊断
python scripts/start_auto_learning.py diagnose

# 检查依赖
python -c "import watchdog, git, yaml; print('所有依赖已安装')"

# 验证配置
python -c "from core_lib.knowledge.auto_learning import AutoLearningSystem; print('配置有效')"
```

## 扩展开发

### 自定义文件处理器

```python
class CustomFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if self.should_process(event.src_path):
            # 自定义处理逻辑
            self.process_file(event.src_path)
    
    def should_process(self, file_path):
        # 自定义过滤逻辑
        return file_path.endswith('.custom')
    
    def process_file(self, file_path):
        # 自定义文件处理
        pass
```

### 自定义学习策略

```python
class CustomLearningStrategy:
    def analyze_change(self, file_path, content):
        # 自定义变更分析
        importance = self.calculate_importance(content)
        return importance
    
    def calculate_importance(self, content):
        # 自定义重要性计算
        return 1.0 if 'class' in content else 0.5
```

### 集成外部工具

```python
# Elasticsearch 集成
class ElasticsearchIntegration:
    def index_document(self, doc_id, content, metadata):
        # 索引到 Elasticsearch
        pass

# Redis 缓存集成
class RedisCache:
    def get_cached_result(self, key):
        # 从 Redis 获取缓存
        pass
    
    def set_cached_result(self, key, value, ttl=3600):
        # 设置 Redis 缓存
        pass
```

## 最佳实践

### 1. 配置优化
- 根据项目大小调整批处理参数
- 合理设置文件过滤规则
- 启用适当的缓存机制

### 2. 监控策略
- 定期检查系统状态
- 监控资源使用情况
- 设置合适的日志级别

### 3. 团队协作
- 统一配置文件
- 共享忽略规则
- 建立变更通知机制

### 4. 安全考虑
- 避免监控敏感文件
- 设置文件权限检查
- 启用路径遍历保护

## 版本历史

- **v1.0.0**: 初始版本，基础文件监控和索引更新
- **v1.1.0**: 添加Git集成和智能学习功能
- **v1.2.0**: 性能优化和批处理改进
- **v1.3.0**: 添加配置管理和诊断工具

## 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建 Pull Request
5. 等待代码审查

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目仓库: https://github.com/your-org/CHS-SDK
- 问题反馈: https://github.com/your-org/CHS-SDK/issues
- 邮箱: support@chs-sdk.org

---

*CHS-SDK 自动学习系统 - 让知识库始终保持最新状态* 🚀