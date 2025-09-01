#!/usr/bin/env python3
"""
调试系统使用示例

演示如何使用通用调试系统进行开发和调试，包括：
- 日志管理
- 调试数据收集
- 日志分析
- 仪表板监控
"""

import time
import random
import tempfile
from pathlib import Path
from typing import Dict, Any

# 导入调试系统组件
from .log_manager import setup_logging, get_logger
from .debug_collector import get_collector_manager, collect_debug_data
from .log_analyzer import get_analysis_engine
from .debug_dashboard import get_dashboard_manager


class ExampleSimulation:
    """示例仿真类，用于演示调试系统的使用"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger()
        self.step_count = 0
        self.performance_data = []
        self.error_count = 0
        
        # 记录初始化日志
        self.logger.info(
            f"仿真 '{name}' 初始化完成",
            "simulation",
            simulation_name=name
        )
    
    def run_step(self) -> Dict[str, Any]:
        """运行一个仿真步骤"""
        self.step_count += 1
        
        # 记录步骤开始
        self.logger.debug(
            f"开始执行步骤 {self.step_count}",
            "simulation",
            step=self.step_count,
            simulation_name=self.name
        )
        
        # 模拟计算时间
        start_time = time.time()
        
        # 模拟一些计算工作
        result = self._simulate_computation()
        
        # 计算性能指标
        execution_time = time.time() - start_time
        self.performance_data.append(execution_time)
        
        # 收集调试数据
        collect_debug_data(
            'performance_metric',
            'step_execution_time',
            execution_time,
            {
                'step': self.step_count,
                'simulation_name': self.name,
                'result_value': result['value']
            }
        )
        
        # 记录步骤完成
        self.logger.info(
            f"步骤 {self.step_count} 完成，耗时 {execution_time:.3f}s",
            "simulation",
            step=self.step_count,
            execution_time=execution_time,
            result_value=result['value']
        )
        
        return result
    
    def _simulate_computation(self) -> Dict[str, Any]:
        """模拟计算过程"""
        # 随机生成一些结果
        value = random.uniform(0, 100)
        
        # 模拟偶发错误
        if random.random() < 0.1:  # 10% 概率出现错误
            self.error_count += 1
            error_msg = f"计算错误 #{self.error_count}"
            
            self.logger.error(
                error_msg,
                "simulation",
                step=self.step_count,
                error_count=self.error_count
            )
            
            # 收集错误信息
            collect_debug_data(
                'error',
                'computation_error',
                error_msg,
                {
                    'step': self.step_count,
                    'error_count': self.error_count,
                    'simulation_name': self.name
                }
            )
            
            # 模拟错误恢复
            time.sleep(0.1)
            value = random.uniform(0, 50)  # 错误情况下返回较小值
        
        # 模拟偶发警告
        elif random.random() < 0.2:  # 20% 概率出现警告
            self.logger.warning(
                f"计算结果异常: {value:.2f}",
                "simulation",
                step=self.step_count,
                value=value
            )
        
        # 模拟计算延迟
        time.sleep(random.uniform(0.01, 0.1))
        
        return {
            'value': value,
            'step': self.step_count,
            'timestamp': time.time()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取仿真统计信息"""
        if not self.performance_data:
            return {}
        
        avg_time = sum(self.performance_data) / len(self.performance_data)
        max_time = max(self.performance_data)
        min_time = min(self.performance_data)
        
        stats = {
            'total_steps': self.step_count,
            'error_count': self.error_count,
            'avg_execution_time': avg_time,
            'max_execution_time': max_time,
            'min_execution_time': min_time,
            'error_rate': self.error_count / self.step_count if self.step_count > 0 else 0
        }
        
        # 记录统计信息
        self.logger.info(
            f"仿真统计: 总步数={stats['total_steps']}, 错误数={stats['error_count']}, 平均耗时={avg_time:.3f}s",
            "simulation",
            **stats
        )
        
        return stats


def setup_debug_environment(session_id: str = None) -> Path:
    """设置调试环境"""
    if session_id is None:
        session_id = f"debug_example_{int(time.time())}"
    
    # 创建临时目录用于存储日志
    temp_dir = Path(tempfile.mkdtemp(prefix="debug_example_"))
    
    # 配置日志系统
    log_config = {
        'session_id': session_id,
        'console': {
            'enabled': True,
            'level': 'INFO',
            'format': '[{timestamp}] {level} - {logger}: {message}'
        },
        'file': {
            'enabled': True,
            'path': temp_dir / f'{session_id}.log',
            'level': 'DEBUG',
            'max_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 3
        },
        'database': {
            'enabled': True,
            'path': temp_dir / f'{session_id}.db',
            'table_name': 'debug_logs'
        }
    }
    
    setup_logging(log_config)
    
    # 启动调试数据收集器
    collector_manager = get_collector_manager(session_id)
    collector_manager.start_auto_collect(interval=2.0)
    
    logger = get_logger()
    logger.info(
        f"调试环境已设置，会话ID: {session_id}",
        "debug_system",
        session_id=session_id,
        log_dir=str(temp_dir)
    )
    
    return temp_dir


def run_basic_example():
    """运行基础调试示例"""
    print("🔍 运行基础调试示例...")
    
    # 设置调试环境
    log_dir = setup_debug_environment("basic_example")
    logger = get_logger()
    
    try:
        # 创建示例仿真
        simulation = ExampleSimulation("基础示例仿真")
        
        # 运行仿真步骤
        for i in range(10):
            result = simulation.run_step()
            
            # 记录一些额外的调试信息
            collect_debug_data(
                'simulation_state',
                'current_step',
                i + 1,
                {
                    'simulation_name': simulation.name,
                    'result_value': result['value']
                }
            )
            
            time.sleep(0.5)  # 模拟实际工作间隔
        
        # 获取统计信息
        stats = simulation.get_statistics()
        
        # 记录完成信息
        logger.info(
            "基础示例完成",
            "debug_example",
            **stats
        )
        
        print(f"✅ 基础示例完成，日志保存在: {log_dir}")
        
    except Exception as e:
        logger.error(
            f"基础示例执行失败: {e}",
            "debug_example",
            error_type=type(e).__name__
        )
        raise
    
    finally:
        # 清理资源
        get_collector_manager().close()


def run_dashboard_example():
    """运行仪表板示例"""
    print("🖥️ 运行仪表板示例...")
    
    # 设置调试环境
    log_dir = setup_debug_environment("dashboard_example")
    logger = get_logger()
    
    # 启动仪表板
    dashboard_manager = get_dashboard_manager()
    
    try:
        # 启动Web仪表板
        url = dashboard_manager.start_web_dashboard(port=8080, open_browser=False)
        print(f"🌐 Web仪表板已启动: {url}")
        
        # 启动命令行仪表板
        dashboard_manager.start_console_dashboard(update_interval=2.0)
        print("📟 命令行仪表板已启动")
        
        # 创建多个仿真实例
        simulations = [
            ExampleSimulation(f"仿真_{i+1}")
            for i in range(3)
        ]
        
        # 并行运行仿真
        print("🚀 开始运行仿真...")
        for step in range(20):
            for sim in simulations:
                result = sim.run_step()
                
                # 收集更多调试数据
                collect_debug_data(
                    'multi_simulation',
                    f'{sim.name}_result',
                    result['value'],
                    {
                        'step': step + 1,
                        'simulation_count': len(simulations)
                    }
                )
            
            # 记录整体进度
            logger.info(
                f"所有仿真完成步骤 {step + 1}",
                "multi_simulation",
                step=step + 1,
                simulation_count=len(simulations)
            )
            
            time.sleep(1.0)
        
        # 获取所有仿真的统计信息
        all_stats = {}
        for sim in simulations:
            all_stats[sim.name] = sim.get_statistics()
        
        logger.info(
            "仪表板示例完成",
            "debug_example",
            simulation_stats=all_stats
        )
        
        print(f"✅ 仪表板示例完成")
        print(f"🌐 Web仪表板: {url}")
        print(f"📁 日志目录: {log_dir}")
        print("\n💡 提示: Web仪表板将继续运行，可以在浏览器中查看实时数据")
        print("按 Ctrl+C 停止所有服务")
        
        # 保持运行以便查看仪表板
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务...")
    
    except Exception as e:
        logger.error(
            f"仪表板示例执行失败: {e}",
            "debug_example",
            error_type=type(e).__name__
        )
        raise
    
    finally:
        # 清理资源
        dashboard_manager.stop_all()
        get_collector_manager().close()


def run_analysis_example():
    """运行日志分析示例"""
    print("📊 运行日志分析示例...")
    
    # 设置调试环境
    log_dir = setup_debug_environment("analysis_example")
    logger = get_logger()
    
    try:
        # 创建仿真并生成大量日志数据
        simulation = ExampleSimulation("分析示例仿真")
        
        print("📝 生成日志数据...")
        for i in range(50):
            result = simulation.run_step()
            
            # 模拟不同类型的事件
            if i % 10 == 0:
                logger.warning(
                    f"性能警告: 步骤 {i} 执行时间较长",
                    "performance",
                    step=i,
                    execution_time=result.get('execution_time', 0)
                )
            
            if i % 15 == 0:
                collect_debug_data(
                    'system_resource',
                    'memory_usage',
                    random.uniform(50, 90),
                    {'step': i, 'unit': 'percent'}
                )
            
            time.sleep(0.1)  # 快速生成数据
        
        print("🔍 开始日志分析...")
        
        # 获取分析引擎
        analysis_engine = get_analysis_engine()
        
        # 分析日志文件
        log_file = log_dir / "analysis_example.log"
        if log_file.exists():
            print(f"📄 分析日志文件: {log_file}")
            
            # 运行各种分析
            pattern_results = analysis_engine.analyze_file(
                str(log_file),
                ['pattern']
            )
            
            anomaly_results = analysis_engine.analyze_file(
                str(log_file),
                ['anomaly']
            )
            
            performance_results = analysis_engine.analyze_file(
                str(log_file),
                ['performance']
            )
            
            error_results = analysis_engine.analyze_file(
                str(log_file),
                ['error']
            )
            
            # 显示分析结果
            all_results = pattern_results + anomaly_results + performance_results + error_results
            
            print(f"\n📊 分析结果 ({len(all_results)} 项):")
            for result in all_results:
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠',
                    'critical': '🔴'
                }.get(result.severity, '⚪')
                
                print(f"  {severity_emoji} [{result.analysis_type}] {result.title}")
                print(f"      {result.description}")
                print(f"      置信度: {result.confidence:.1%}")
                print()
            
            # 生成分析报告
            report = analysis_engine.generate_report(all_results)
            report_file = log_dir / "analysis_report.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"📋 分析报告已保存: {report_file}")
        
        # 分析数据库日志
        db_file = log_dir / "analysis_example.db"
        if db_file.exists():
            print(f"\n🗄️ 分析数据库日志: {db_file}")
            
            db_results = analysis_engine.analyze_database(
                str(db_file),
                'debug_logs',
                ['trend', 'error']
            )
            
            print(f"📈 数据库分析结果 ({len(db_results)} 项):")
            for result in db_results:
                print(f"  • {result.title}: {result.description}")
        
        logger.info(
            "日志分析示例完成",
            "debug_example",
            total_analysis_results=len(all_results) if 'all_results' in locals() else 0
        )
        
        print(f"✅ 日志分析示例完成，结果保存在: {log_dir}")
        
    except Exception as e:
        logger.error(
            f"日志分析示例执行失败: {e}",
            "debug_example",
            error_type=type(e).__name__
        )
        raise
    
    finally:
        # 清理资源
        get_collector_manager().close()


def run_integration_example():
    """运行完整集成示例"""
    print("🔧 运行完整集成示例...")
    
    # 设置调试环境
    log_dir = setup_debug_environment("integration_example")
    logger = get_logger()
    
    # 启动所有调试组件
    dashboard_manager = get_dashboard_manager()
    analysis_engine = get_analysis_engine()
    
    try:
        # 启动仪表板
        url = dashboard_manager.start_web_dashboard(port=8081, open_browser=False)
        print(f"🌐 Web仪表板: {url}")
        
        # 创建复杂仿真场景
        simulations = {
            'water_system': ExampleSimulation('水利系统仿真'),
            'power_grid': ExampleSimulation('电网仿真'),
            'traffic_flow': ExampleSimulation('交通流仿真')
        }
        
        print("🚀 开始集成仿真...")
        
        # 运行集成仿真
        for cycle in range(15):
            cycle_start = time.time()
            
            # 并行运行所有仿真
            cycle_results = {}
            for name, sim in simulations.items():
                result = sim.run_step()
                cycle_results[name] = result
                
                # 收集系统级调试数据
                collect_debug_data(
                    'system_integration',
                    f'{name}_cycle_result',
                    result['value'],
                    {
                        'cycle': cycle + 1,
                        'system_type': name,
                        'total_systems': len(simulations)
                    }
                )
            
            cycle_time = time.time() - cycle_start
            
            # 记录周期完成
            logger.info(
                f"集成仿真周期 {cycle + 1} 完成，耗时 {cycle_time:.3f}s",
                "integration",
                cycle=cycle + 1,
                cycle_time=cycle_time,
                results=cycle_results
            )
            
            # 模拟系统间交互
            if cycle % 5 == 0:
                logger.info(
                    f"系统同步检查点 {cycle // 5 + 1}",
                    "integration",
                    checkpoint=cycle // 5 + 1,
                    active_systems=list(simulations.keys())
                )
            
            time.sleep(1.0)
        
        print("\n📊 执行实时分析...")
        
        # 实时分析最近的日志
        log_file = log_dir / "integration_example.log"
        if log_file.exists():
            recent_results = analysis_engine.analyze_file(
                str(log_file),
                ['performance', 'trend']
            )
            
            print(f"🔍 实时分析发现 {len(recent_results)} 个问题:")
            for result in recent_results[-5:]:  # 显示最近5个结果
                print(f"  • {result.title}")
        
        # 获取所有系统统计
        all_stats = {}
        for name, sim in simulations.items():
            all_stats[name] = sim.get_statistics()
        
        # 记录集成完成
        logger.info(
            "集成示例完成",
            "debug_example",
            systems=list(simulations.keys()),
            total_cycles=15,
            system_stats=all_stats
        )
        
        print(f"✅ 集成示例完成")
        print(f"🌐 Web仪表板: {url}")
        print(f"📁 日志目录: {log_dir}")
        print("\n💡 可以在Web仪表板中查看完整的调试信息")
        
        # 保持运行一段时间以便查看结果
        print("\n⏳ 保持运行30秒以便查看仪表板...")
        time.sleep(30)
        
    except Exception as e:
        logger.error(
            f"集成示例执行失败: {e}",
            "debug_example",
            error_type=type(e).__name__
        )
        raise
    
    finally:
        # 清理资源
        dashboard_manager.stop_all()
        get_collector_manager().close()


def main():
    """主函数 - 运行所有示例"""
    print("🔍 通用调试系统示例")
    print("=" * 50)
    
    examples = {
        '1': ('基础调试示例', run_basic_example),
        '2': ('仪表板示例', run_dashboard_example),
        '3': ('日志分析示例', run_analysis_example),
        '4': ('完整集成示例', run_integration_example)
    }
    
    print("\n可用示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    print("  a. 运行所有示例")
    print("  q. 退出")
    
    while True:
        choice = input("\n请选择要运行的示例 (1-4, a, q): ").strip().lower()
        
        if choice == 'q':
            print("👋 再见!")
            break
        elif choice == 'a':
            print("🚀 运行所有示例...")
            for name, func in examples.values():
                print(f"\n{'='*20} {name} {'='*20}")
                try:
                    func()
                except Exception as e:
                    print(f"❌ {name} 执行失败: {e}")
                print(f"{'='*50}")
            print("\n✅ 所有示例执行完成!")
            break
        elif choice in examples:
            name, func = examples[choice]
            print(f"\n🚀 运行 {name}...")
            try:
                func()
                print(f"\n✅ {name} 执行完成!")
            except Exception as e:
                print(f"\n❌ {name} 执行失败: {e}")
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    main()