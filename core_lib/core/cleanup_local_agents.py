#!/usr/bin/env python3
"""
清理 local_agents 目录

完全删除 local_agents/ 目录，符合层次化和紧凑的架构目标
"""
import os
import shutil
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def analyze_local_agents():
    """分析 local_agents 目录"""
    print("=== 分析 local_agents 目录 ===")
    
    local_agents_path = Path("core_lib/local_agents")
    if not local_agents_path.exists():
        print("❌ local_agents 目录不存在")
        return False
    
    print(f"\n📁 {local_agents_path} 目录分析:")
    
    subdirs = []
    for item in local_agents_path.iterdir():
        if item.is_dir() and item.name != '__pycache__':
            file_count = len(list(item.rglob("*.py")))
            subdirs.append((item.name, file_count))
            print(f"  📂 {item.name}/: {file_count} 个 Python 文件")
    
    total_files = sum(count for _, count in subdirs)
    print(f"\n📊 总计: {len(subdirs)} 个子目录, {total_files} 个 Python 文件")
    
    return True

def explain_deletion_rationale():
    """解释删除理由"""
    print("\n=== 删除理由分析 ===")
    
    rationale = {
        "架构冗余": [
            "依赖已删除的 central_coordination",
            "使用过时的消息总线接口",
            "与新三层架构不符"
        ],
        "功能重复": [
            "控制功能 → UnifiedLocalControlAgent 已替代",
            "感知功能 → MonitoringAgent 可替代", 
            "工具功能 → 可集成到新架构服务层"
        ],
        "目录状况": [
            "disturbances/, io/, supervisory/ 基本为空",
            "perception/ 依赖已删除组件",
            "control/ 与新架构完全重复"
        ],
        "架构目标": [
            "更层次化：减少目录嵌套",
            "更紧凑：集中到新架构",
            "更清晰：避免新旧并存"
        ]
    }
    
    for category, reasons in rationale.items():
        print(f"\n🎯 {category}:")
        for reason in reasons:
            print(f"   • {reason}")

def backup_local_agents():
    """备份 local_agents 目录"""
    print("\n=== 备份 local_agents 目录 ===")
    
    source = Path("core_lib/local_agents")
    backup_dir = Path("backup_remaining_legacy")
    backup_dir.mkdir(exist_ok=True)
    
    target = backup_dir / "local_agents"
    
    if source.exists():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"✅ 完整备份: {source} → {target}")
        
        # 统计备份内容
        py_files = list(target.rglob("*.py"))
        print(f"📊 备份内容: {len(py_files)} 个 Python 文件")
        
        return True
    else:
        print("❌ 源目录不存在，无法备份")
        return False

def identify_valuable_components():
    """识别有价值的组件"""
    print("\n=== 识别有价值组件 ===")
    
    valuable_components = {
        "预测算法": [
            "prediction/lstm_forecaster.py",
            "prediction/arima_forecaster.py", 
            "prediction/lstm_model.py"
        ],
        "工具组件": [
            "utility/signal_aggregator_agent.py",
            "utility/topic_logger_agent.py"
        ],
        "分析工具": [
            "analysis/performance_analyzer.py"
        ]
    }
    
    print("💎 可能有价值的组件（可考虑迁移到新架构）:")
    for category, files in valuable_components.items():
        print(f"\n  📋 {category}:")
        for file_path in files:
            full_path = Path(f"core_lib/local_agents/{file_path}")
            status = "✅ 存在" if full_path.exists() else "❌ 不存在"
            print(f"    • {file_path} - {status}")
    
    print(f"\n💡 建议: 这些组件可以在未来需要时从备份中提取，")
    print(f"     并重构为新架构的插件或服务组件")

def delete_local_agents():
    """删除 local_agents 目录"""
    print("\n=== 删除 local_agents 目录 ===")
    
    local_agents_path = Path("core_lib/local_agents")
    
    if local_agents_path.exists():
        try:
            shutil.rmtree(local_agents_path)
            print(f"🗑️ 已删除: {local_agents_path}")
            return True
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
    else:
        print(f"⚠️  目录不存在: {local_agents_path}")
        return False

def update_core_lib_structure():
    """更新 core_lib 结构说明"""
    print("\n=== 更新后的 core_lib 结构 ===")
    
    structure = """
📁 core_lib/ (更加层次化和紧凑)
├── core/                     # 🆕 新架构核心
│   ├── new_agents/          # 统一Agent实现
│   ├── monitoring/          # 监控组件
│   ├── event_bus.py         # 事件总线
│   ├── new_interfaces.py    # 统一接口
│   └── factories.py         # 工厂模式
├── models/                  # 数据模型
├── physical_objects/        # 物理对象
├── core_engine/            # 仿真引擎
├── utils/                  # 工具函数
└── 其他核心模块...
"""
    
    print(structure)
    
    print("✅ 优势:")
    print("   • 层次更清晰：核心功能集中在 core/")
    print("   • 结构更紧凑：减少冗余目录")
    print("   • 架构统一：只保留新架构")
    print("   • 维护简化：减少代码分散")

def generate_deletion_report():
    """生成删除报告"""
    print("\n=== 生成删除报告 ===")
    
    report = """# local_agents 目录删除报告

## 🎯 删除目标
实现更层次化、更紧凑的 core_lib 架构

## 📊 删除内容
- **目录**: `core_lib/local_agents/` (完整删除)
- **子目录**: disturbances/, io/, supervisory/, control/, perception/, prediction/, utility/, analysis/, common/
- **备份位置**: `backup_remaining_legacy/local_agents/`

## 🎯 删除理由

### 1. 架构冗余
- 依赖已删除的 `central_coordination` 组件
- 使用过时的消息总线接口
- 与新的三层架构设计不符

### 2. 功能重复
- **控制功能**: 已被 `UnifiedLocalControlAgent` 完全替代
- **感知功能**: 可通过新架构的 `MonitoringAgent` 实现
- **工具功能**: 可集成到新架构的服务层

### 3. 目录状况
- `disturbances/`, `io/`, `supervisory/` 基本为空目录
- `perception/` 依赖已删除的组件，无法正常工作
- `control/` 与新架构功能完全重复

### 4. 符合架构目标
- ✅ **更层次化**: 减少目录嵌套，功能集中
- ✅ **更紧凑**: 避免代码分散，统一到新架构
- ✅ **更清晰**: 消除新旧架构并存的混乱

## 💎 有价值组件（已备份）
如果未来需要，可从备份中提取并重构为新架构组件：
- 预测算法 (LSTM, ARIMA)
- 工具组件 (信号聚合, 日志记录)
- 分析工具 (性能分析)

## 🏗️ 删除后的架构
```
core_lib/
├── core/                 # 🆕 新架构核心 (统一、紧凑)
├── models/               # 数据模型
├── physical_objects/     # 物理对象
├── core_engine/         # 仿真引擎
└── utils/               # 工具函数
```

## ✅ 删除效果
- **代码简化**: 减少维护负担
- **架构统一**: 只保留新架构
- **结构清晰**: 层次化和紧凑化
- **开发效率**: 避免新旧选择困惑

---
*删除时间: 2025年9月16日*
*符合目标: 更层次化、更紧凑的架构*
"""
    
    with open("LOCAL_AGENTS_DELETION_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ 删除报告已保存: LOCAL_AGENTS_DELETION_REPORT.md")

def main():
    """主函数"""
    print("local_agents 目录清理工具")
    print("=" * 50)
    print("🎯 目标: 实现更层次化、更紧凑的架构")
    
    # 1. 分析目录
    if not analyze_local_agents():
        return
    
    # 2. 解释删除理由
    explain_deletion_rationale()
    
    # 3. 识别有价值组件
    identify_valuable_components()
    
    # 4. 询问确认
    print("\n" + "=" * 50)
    print("🤔 基于以上分析，建议完全删除 local_agents/ 目录")
    print("   这将使 core_lib 更加层次化和紧凑")
    response = input("\n是否执行删除？(y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ 取消删除操作")
        return
    
    # 5. 备份
    if not backup_local_agents():
        print("❌ 备份失败，取消删除")
        return
    
    # 6. 执行删除
    if delete_local_agents():
        print("✅ local_agents 目录删除成功！")
        
        # 7. 更新结构说明
        update_core_lib_structure()
        
        # 8. 生成报告
        generate_deletion_report()
        
        print("\n🎉 local_agents 清理完成！")
        print("🏗️  core_lib 现在更加层次化和紧凑")
        
    else:
        print("❌ 删除失败")

if __name__ == "__main__":
    main()
