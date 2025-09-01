#!/usr/bin/env python3
"""
日志分析工具

提供智能日志分析功能，包括：
- 模式识别和异常检测
- 性能瓶颈分析
- 错误趋势分析
- 智能报告生成
- 人工和AI辅助分析
"""

import json
import re
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum
import numpy as np
from scipy import stats
import pandas as pd

from .log_manager import LogRecord, get_logger
from .debug_collector import DebugData, DataType


class AnalysisType(Enum):
    """分析类型枚举"""
    PATTERN_DETECTION = "pattern_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ERROR_ANALYSIS = "error_analysis"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"
    CUSTOM = "custom"


class Severity(Enum):
    """严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisResult:
    """分析结果"""
    analysis_type: str
    title: str
    description: str
    severity: str
    confidence: float
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'analysis_type': self.analysis_type,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'data': self.data,
            'recommendations': self.recommendations,
            'affected_components': self.affected_components
        }


class LogAnalyzer:
    """日志分析器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """分析数据（子类实现）"""
        return []
    
    def _create_result(self, analysis_type: AnalysisType, title: str,
                      description: str, severity: Severity,
                      confidence: float, **kwargs) -> AnalysisResult:
        """创建分析结果"""
        return AnalysisResult(
            analysis_type=analysis_type.value,
            title=title,
            description=description,
            severity=severity.value,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            **kwargs
        )


class PatternAnalyzer(LogAnalyzer):
    """模式识别分析器"""
    
    def __init__(self):
        super().__init__("pattern_analyzer")
        self.patterns = {
            'repeated_errors': r'(ERROR|FATAL).*?([A-Za-z]+Error|Exception)',
            'memory_leak': r'memory.*?(leak|increase|grow)',
            'timeout': r'timeout|timed out|time.*?out',
            'connection_issues': r'connection.*?(failed|refused|timeout|lost)',
            'performance_degradation': r'slow|performance|latency|delay'
        }
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """识别日志模式"""
        if not self.enabled:
            return []
        
        results = []
        
        # 提取文本消息
        messages = []
        for item in data:
            if isinstance(item, LogRecord):
                messages.append(item.message)
            elif isinstance(item, DebugData):
                messages.append(str(item.value))
        
        # 检测模式
        for pattern_name, pattern_regex in self.patterns.items():
            matches = []
            for i, message in enumerate(messages):
                if re.search(pattern_regex, message, re.IGNORECASE):
                    matches.append((i, message))
            
            if matches:
                # 计算模式频率
                frequency = len(matches) / len(messages) if messages else 0
                
                # 确定严重程度
                if frequency > 0.1:  # 超过10%
                    severity = Severity.HIGH
                elif frequency > 0.05:  # 超过5%
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW
                
                result = self._create_result(
                    AnalysisType.PATTERN_DETECTION,
                    f"检测到模式: {pattern_name}",
                    f"在 {len(messages)} 条记录中发现 {len(matches)} 次匹配，频率: {frequency:.2%}",
                    severity,
                    min(0.9, frequency * 10),  # 置信度基于频率
                    data={
                        'pattern_name': pattern_name,
                        'pattern_regex': pattern_regex,
                        'matches': len(matches),
                        'total_records': len(messages),
                        'frequency': frequency,
                        'sample_matches': [msg for _, msg in matches[:5]]
                    },
                    recommendations=self._get_pattern_recommendations(pattern_name)
                )
                results.append(result)
        
        return results
    
    def _get_pattern_recommendations(self, pattern_name: str) -> List[str]:
        """获取模式相关的建议"""
        recommendations = {
            'repeated_errors': [
                "检查错误处理逻辑",
                "增加重试机制",
                "优化异常处理流程"
            ],
            'memory_leak': [
                "检查内存使用情况",
                "优化对象生命周期管理",
                "使用内存分析工具"
            ],
            'timeout': [
                "增加超时时间",
                "优化网络配置",
                "检查服务响应性能"
            ],
            'connection_issues': [
                "检查网络连接",
                "优化连接池配置",
                "增加连接重试逻辑"
            ],
            'performance_degradation': [
                "进行性能分析",
                "优化算法和数据结构",
                "检查系统资源使用"
            ]
        }
        return recommendations.get(pattern_name, [])


class AnomalyAnalyzer(LogAnalyzer):
    """异常检测分析器"""
    
    def __init__(self, threshold_multiplier: float = 2.0):
        super().__init__("anomaly_analyzer")
        self.threshold_multiplier = threshold_multiplier
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """检测异常值"""
        if not self.enabled:
            return []
        
        results = []
        
        # 按数据类型分组
        grouped_data = defaultdict(list)
        for item in data:
            if isinstance(item, DebugData):
                if item.data_type in [DataType.PERFORMANCE_METRIC.value, DataType.SYSTEM_RESOURCE.value]:
                    try:
                        value = float(item.value)
                        grouped_data[f"{item.data_type}_{item.name}"].append({
                            'timestamp': item.timestamp,
                            'value': value,
                            'source': item.source
                        })
                    except (ValueError, TypeError):
                        continue
        
        # 检测每个指标的异常
        for metric_name, values in grouped_data.items():
            if len(values) < 10:  # 需要足够的数据点
                continue
            
            numeric_values = [v['value'] for v in values]
            
            # 计算统计信息
            mean_val = statistics.mean(numeric_values)
            std_val = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
            
            if std_val == 0:  # 避免除零错误
                continue
            
            # 检测异常值（使用Z-score方法）
            anomalies = []
            for i, value_info in enumerate(values):
                z_score = abs((value_info['value'] - mean_val) / std_val)
                if z_score > self.threshold_multiplier:
                    anomalies.append({
                        'index': i,
                        'timestamp': value_info['timestamp'],
                        'value': value_info['value'],
                        'z_score': z_score,
                        'source': value_info['source']
                    })
            
            if anomalies:
                # 确定严重程度
                max_z_score = max(a['z_score'] for a in anomalies)
                if max_z_score > 4.0:
                    severity = Severity.CRITICAL
                elif max_z_score > 3.0:
                    severity = Severity.HIGH
                elif max_z_score > 2.5:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW
                
                result = self._create_result(
                    AnalysisType.ANOMALY_DETECTION,
                    f"检测到异常值: {metric_name}",
                    f"在 {len(values)} 个数据点中发现 {len(anomalies)} 个异常值",
                    severity,
                    min(0.95, max_z_score / 5.0),
                    data={
                        'metric_name': metric_name,
                        'total_points': len(values),
                        'anomaly_count': len(anomalies),
                        'mean': mean_val,
                        'std': std_val,
                        'max_z_score': max_z_score,
                        'anomalies': anomalies[:10]  # 只保留前10个异常值
                    },
                    recommendations=[
                        "检查异常时间点的系统状态",
                        "分析异常值的根本原因",
                        "考虑调整监控阈值"
                    ]
                )
                results.append(result)
        
        return results


class PerformanceAnalyzer(LogAnalyzer):
    """性能分析器"""
    
    def __init__(self):
        super().__init__("performance_analyzer")
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """分析性能数据"""
        if not self.enabled:
            return []
        
        results = []
        
        # 收集性能数据
        performance_data = defaultdict(list)
        for item in data:
            if isinstance(item, DebugData) and item.data_type == DataType.PERFORMANCE_METRIC.value:
                try:
                    if isinstance(item.value, dict) and 'duration' in item.metadata:
                        duration = float(item.metadata['duration'])
                        performance_data[item.name].append({
                            'timestamp': item.timestamp,
                            'duration': duration,
                            'status': item.metadata.get('status', 'unknown')
                        })
                except (ValueError, TypeError, KeyError):
                    continue
        
        # 分析每个性能指标
        for metric_name, perf_data in performance_data.items():
            if len(perf_data) < 5:
                continue
            
            durations = [p['duration'] for p in perf_data]
            
            # 计算性能统计
            avg_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            p95_duration = np.percentile(durations, 95)
            p99_duration = np.percentile(durations, 99)
            
            # 检查性能问题
            issues = []
            
            # 检查平均响应时间
            if avg_duration > 1.0:  # 超过1秒
                issues.append("平均响应时间过长")
            
            # 检查最大响应时间
            if max_duration > 5.0:  # 超过5秒
                issues.append("存在极慢的请求")
            
            # 检查P95响应时间
            if p95_duration > 2.0:  # P95超过2秒
                issues.append("95%分位数响应时间过长")
            
            # 检查响应时间变异性
            if len(durations) > 1:
                cv = statistics.stdev(durations) / avg_duration  # 变异系数
                if cv > 1.0:  # 变异系数大于1
                    issues.append("响应时间不稳定")
            
            # 检查错误率
            error_count = sum(1 for p in perf_data if p['status'] == 'error')
            error_rate = error_count / len(perf_data)
            if error_rate > 0.05:  # 错误率超过5%
                issues.append(f"错误率过高: {error_rate:.2%}")
            
            if issues:
                # 确定严重程度
                if len(issues) >= 3 or max_duration > 10.0:
                    severity = Severity.HIGH
                elif len(issues) >= 2 or avg_duration > 2.0:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW
                
                result = self._create_result(
                    AnalysisType.PERFORMANCE_ANALYSIS,
                    f"性能问题: {metric_name}",
                    f"发现 {len(issues)} 个性能问题: {', '.join(issues)}",
                    severity,
                    0.8,
                    data={
                        'metric_name': metric_name,
                        'sample_count': len(perf_data),
                        'avg_duration': avg_duration,
                        'median_duration': median_duration,
                        'max_duration': max_duration,
                        'min_duration': min_duration,
                        'p95_duration': p95_duration,
                        'p99_duration': p99_duration,
                        'error_rate': error_rate,
                        'issues': issues
                    },
                    recommendations=[
                        "优化慢查询和算法",
                        "增加缓存机制",
                        "检查系统资源瓶颈",
                        "优化数据库查询",
                        "考虑异步处理"
                    ]
                )
                results.append(result)
        
        return results


class ErrorAnalyzer(LogAnalyzer):
    """错误分析器"""
    
    def __init__(self):
        super().__init__("error_analyzer")
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """分析错误数据"""
        if not self.enabled:
            return []
        
        results = []
        
        # 收集错误数据
        errors = []
        for item in data:
            if isinstance(item, LogRecord) and item.level in ['ERROR', 'FATAL']:
                errors.append({
                    'timestamp': item.timestamp,
                    'level': item.level,
                    'message': item.message,
                    'logger': item.logger,
                    'exception': item.exception
                })
            elif isinstance(item, DebugData) and item.data_type == DataType.ERROR_INFO.value:
                errors.append({
                    'timestamp': item.timestamp,
                    'type': item.name,
                    'message': str(item.value),
                    'source': item.source
                })
        
        if not errors:
            return results
        
        # 分析错误模式
        error_types = Counter()
        error_sources = Counter()
        error_timeline = defaultdict(int)
        
        for error in errors:
            # 统计错误类型
            if 'type' in error:
                error_types[error['type']] += 1
            elif 'level' in error:
                error_types[error['level']] += 1
            
            # 统计错误来源
            source = error.get('logger') or error.get('source', 'unknown')
            error_sources[source] += 1
            
            # 统计错误时间分布
            try:
                timestamp = datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00'))
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                error_timeline[hour_key] += 1
            except:
                continue
        
        # 分析错误趋势
        total_errors = len(errors)
        
        # 检查错误率
        if total_errors > 10:
            severity = Severity.HIGH
            description = f"检测到大量错误: {total_errors} 个"
        elif total_errors > 5:
            severity = Severity.MEDIUM
            description = f"检测到较多错误: {total_errors} 个"
        else:
            severity = Severity.LOW
            description = f"检测到少量错误: {total_errors} 个"
        
        # 找出最频繁的错误类型
        top_error_types = error_types.most_common(5)
        top_error_sources = error_sources.most_common(5)
        
        result = self._create_result(
            AnalysisType.ERROR_ANALYSIS,
            "错误分析报告",
            description,
            severity,
            0.9,
            data={
                'total_errors': total_errors,
                'top_error_types': top_error_types,
                'top_error_sources': top_error_sources,
                'error_timeline': dict(error_timeline),
                'sample_errors': errors[:5]  # 前5个错误样本
            },
            recommendations=[
                "重点关注频繁出现的错误类型",
                "检查错误集中的组件或模块",
                "分析错误发生的时间模式",
                "改进错误处理和恢复机制"
            ],
            affected_components=[source for source, _ in top_error_sources]
        )
        results.append(result)
        
        return results


class TrendAnalyzer(LogAnalyzer):
    """趋势分析器"""
    
    def __init__(self, min_data_points: int = 20):
        super().__init__("trend_analyzer")
        self.min_data_points = min_data_points
    
    def analyze(self, data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
        """分析数据趋势"""
        if not self.enabled:
            return []
        
        results = []
        
        # 收集时间序列数据
        time_series = defaultdict(list)
        for item in data:
            if isinstance(item, DebugData):
                try:
                    timestamp = datetime.fromisoformat(item.timestamp.replace('Z', '+00:00'))
                    
                    if item.data_type in [DataType.PERFORMANCE_METRIC.value, DataType.SYSTEM_RESOURCE.value]:
                        value = float(item.value)
                        time_series[f"{item.data_type}_{item.name}"].append({
                            'timestamp': timestamp,
                            'value': value
                        })
                except (ValueError, TypeError):
                    continue
        
        # 分析每个时间序列的趋势
        for metric_name, series in time_series.items():
            if len(series) < self.min_data_points:
                continue
            
            # 按时间排序
            series.sort(key=lambda x: x['timestamp'])
            
            # 提取数值
            values = [s['value'] for s in series]
            timestamps = [s['timestamp'] for s in series]
            
            # 计算趋势（线性回归）
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # 判断趋势显著性
            if abs(r_value) > 0.5 and p_value < 0.05:  # 显著趋势
                trend_direction = "上升" if slope > 0 else "下降"
                trend_strength = "强" if abs(r_value) > 0.8 else "中等"
                
                # 确定严重程度
                if abs(r_value) > 0.8 and abs(slope) > statistics.stdev(values) * 0.1:
                    severity = Severity.HIGH
                elif abs(r_value) > 0.6:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW
                
                # 计算变化率
                if len(values) > 1:
                    change_rate = (values[-1] - values[0]) / values[0] * 100
                else:
                    change_rate = 0
                
                result = self._create_result(
                    AnalysisType.TREND_ANALYSIS,
                    f"趋势分析: {metric_name}",
                    f"检测到{trend_strength}{trend_direction}趋势，相关系数: {r_value:.3f}",
                    severity,
                    abs(r_value),
                    data={
                        'metric_name': metric_name,
                        'data_points': len(values),
                        'slope': slope,
                        'r_value': r_value,
                        'p_value': p_value,
                        'trend_direction': trend_direction,
                        'trend_strength': trend_strength,
                        'change_rate': change_rate,
                        'start_value': values[0],
                        'end_value': values[-1],
                        'time_span': str(timestamps[-1] - timestamps[0])
                    },
                    recommendations=self._get_trend_recommendations(slope, metric_name)
                )
                results.append(result)
        
        return results
    
    def _get_trend_recommendations(self, slope: float, metric_name: str) -> List[str]:
        """根据趋势获取建议"""
        recommendations = []
        
        if slope > 0:  # 上升趋势
            if 'memory' in metric_name.lower():
                recommendations.extend([
                    "监控内存使用情况",
                    "检查是否存在内存泄漏",
                    "优化内存管理"
                ])
            elif 'cpu' in metric_name.lower():
                recommendations.extend([
                    "监控CPU使用情况",
                    "优化计算密集型操作",
                    "考虑负载均衡"
                ])
            elif 'error' in metric_name.lower():
                recommendations.extend([
                    "紧急调查错误增长原因",
                    "加强错误监控",
                    "改进错误处理机制"
                ])
            else:
                recommendations.append("监控指标持续增长")
        else:  # 下降趋势
            if 'performance' in metric_name.lower():
                recommendations.extend([
                    "调查性能下降原因",
                    "检查系统资源",
                    "优化关键路径"
                ])
            else:
                recommendations.append("监控指标持续下降")
        
        return recommendations


class LogAnalysisEngine:
    """日志分析引擎"""
    
    def __init__(self):
        self.analyzers: Dict[str, LogAnalyzer] = {}
        self.analysis_history: List[AnalysisResult] = []
        self.max_history = 1000
        
        # 添加默认分析器
        self.add_analyzer(PatternAnalyzer())
        self.add_analyzer(AnomalyAnalyzer())
        self.add_analyzer(PerformanceAnalyzer())
        self.add_analyzer(ErrorAnalyzer())
        self.add_analyzer(TrendAnalyzer())
    
    def add_analyzer(self, analyzer: LogAnalyzer):
        """添加分析器"""
        self.analyzers[analyzer.name] = analyzer
    
    def remove_analyzer(self, name: str):
        """移除分析器"""
        if name in self.analyzers:
            del self.analyzers[name]
    
    def analyze_data(self, data: List[Union[LogRecord, DebugData]],
                    analyzer_names: Optional[List[str]] = None) -> List[AnalysisResult]:
        """分析数据"""
        if not data:
            return []
        
        results = []
        
        # 选择要使用的分析器
        if analyzer_names:
            analyzers = {name: self.analyzers[name] for name in analyzer_names if name in self.analyzers}
        else:
            analyzers = self.analyzers
        
        # 运行分析器
        for analyzer_name, analyzer in analyzers.items():
            if not analyzer.enabled:
                continue
            
            try:
                analyzer_results = analyzer.analyze(data)
                results.extend(analyzer_results)
                
                get_logger().debug(
                    f"分析器 {analyzer_name} 产生了 {len(analyzer_results)} 个结果",
                    "log_analyzer"
                )
            except Exception as e:
                get_logger().error(
                    f"分析器 {analyzer_name} 执行失败: {e}",
                    "log_analyzer"
                )
        
        # 保存到历史记录
        self.analysis_history.extend(results)
        if len(self.analysis_history) > self.max_history:
            self.analysis_history = self.analysis_history[-self.max_history:]
        
        return results
    
    def analyze_log_file(self, file_path: Union[str, Path]) -> List[AnalysisResult]:
        """分析日志文件"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"日志文件不存在: {file_path}")
        
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # 尝试解析JSON格式的日志
                        log_data = json.loads(line)
                        
                        if 'level' in log_data:  # LogRecord格式
                            record = LogRecord(**log_data)
                            data.append(record)
                        elif 'data_type' in log_data:  # DebugData格式
                            debug_data = DebugData(**log_data)
                            data.append(debug_data)
                    except json.JSONDecodeError:
                        # 处理非JSON格式的日志
                        continue
        except Exception as e:
            get_logger().error(f"读取日志文件失败: {e}", "log_analyzer")
            raise
        
        return self.analyze_data(data)
    
    def analyze_database(self, db_path: Union[str, Path], table_name: str = 'logs',
                        limit: int = 10000) -> List[AnalysisResult]:
        """分析数据库中的日志"""
        data = []
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 查询日志记录
            query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT ?"
            cursor.execute(query, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # 尝试构造LogRecord
                try:
                    if 'context' in row_dict and row_dict['context']:
                        row_dict['context'] = json.loads(row_dict['context'])
                    if 'tags' in row_dict and row_dict['tags']:
                        row_dict['tags'] = json.loads(row_dict['tags'])
                    
                    record = LogRecord(**row_dict)
                    data.append(record)
                except Exception:
                    continue
            
            conn.close()
        except Exception as e:
            get_logger().error(f"读取数据库失败: {e}", "log_analyzer")
            raise
        
        return self.analyze_data(data)
    
    def generate_report(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """生成分析报告"""
        if not results:
            return {
                'summary': '没有发现问题',
                'total_issues': 0,
                'severity_distribution': {},
                'analysis_types': {},
                'recommendations': [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        # 统计严重程度分布
        severity_dist = Counter(r.severity for r in results)
        
        # 统计分析类型分布
        type_dist = Counter(r.analysis_type for r in results)
        
        # 收集所有建议
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        # 去重并排序建议
        unique_recommendations = list(set(all_recommendations))
        
        # 找出最严重的问题
        critical_issues = [r for r in results if r.severity == 'critical']
        high_issues = [r for r in results if r.severity == 'high']
        
        # 生成摘要
        if critical_issues:
            summary = f"发现 {len(critical_issues)} 个严重问题需要立即处理"
        elif high_issues:
            summary = f"发现 {len(high_issues)} 个高优先级问题需要关注"
        else:
            summary = f"发现 {len(results)} 个问题，整体状况良好"
        
        return {
            'summary': summary,
            'total_issues': len(results),
            'severity_distribution': dict(severity_dist),
            'analysis_types': dict(type_dist),
            'critical_issues': [r.to_dict() for r in critical_issues],
            'high_priority_issues': [r.to_dict() for r in high_issues[:5]],
            'recommendations': unique_recommendations,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'all_results': [r.to_dict() for r in results]
        }
    
    def get_analysis_history(self, limit: int = None) -> List[AnalysisResult]:
        """获取分析历史"""
        if limit:
            return self.analysis_history[-limit:]
        return self.analysis_history.copy()


# 全局分析引擎实例
_global_analysis_engine: Optional[LogAnalysisEngine] = None


def get_analysis_engine() -> LogAnalysisEngine:
    """获取全局分析引擎实例"""
    global _global_analysis_engine
    
    if _global_analysis_engine is None:
        _global_analysis_engine = LogAnalysisEngine()
    
    return _global_analysis_engine


# 便捷函数
def analyze_logs(data: List[Union[LogRecord, DebugData]]) -> List[AnalysisResult]:
    """分析日志数据"""
    return get_analysis_engine().analyze_data(data)


def analyze_log_file(file_path: Union[str, Path]) -> List[AnalysisResult]:
    """分析日志文件"""
    return get_analysis_engine().analyze_log_file(file_path)


def generate_analysis_report(results: List[AnalysisResult]) -> Dict[str, Any]:
    """生成分析报告"""
    return get_analysis_engine().generate_report(results)


if __name__ == "__main__":
    # 测试代码
    import tempfile
    from .log_manager import setup_logging
    from .debug_collector import get_collector_manager
    
    # 创建测试数据
    test_data = [
        LogRecord(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            level='ERROR',
            logger='test.module',
            message='Connection timeout occurred',
            context={'retry_count': 3},
            tags=['network'],
            session_id='test_session',
            thread_id='main',
            file='test.py',
            line=100,
            function='test_function'
        ),
        DebugData(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            data_type=DataType.PERFORMANCE_METRIC.value,
            source='test_source',
            name='response_time',
            value=2.5,
            metadata={'duration': 2.5, 'status': 'success'}
        )
    ]
    
    # 创建分析引擎
    engine = LogAnalysisEngine()
    
    # 分析数据
    results = engine.analyze_data(test_data)
    
    print(f"分析结果数量: {len(results)}")
    for result in results:
        print(f"- {result.title} ({result.severity})")
        print(f"  {result.description}")
        print(f"  置信度: {result.confidence:.2f}")
        print()
    
    # 生成报告
    report = engine.generate_report(results)
    print("分析报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))