#!/usr/bin/env python3
"""
调试仪表板

提供实时调试信息的可视化界面，包括：
- Web界面仪表板
- 命令行界面
- 实时数据监控
- 交互式分析工具
"""

import json
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import asdict
from collections import deque, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import socket

from .log_manager import LogRecord, get_logger
from .debug_collector import DebugData, get_collector_manager
from .log_analyzer import AnalysisResult, get_analysis_engine


class DashboardData:
    """仪表板数据管理"""
    
    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.logs: deque = deque(maxlen=max_records)
        self.debug_data: deque = deque(maxlen=max_records)
        self.analysis_results: deque = deque(maxlen=100)
        self.system_stats: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.lock = threading.Lock()
    
    def add_log(self, log: LogRecord):
        """添加日志记录"""
        with self.lock:
            self.logs.append(log)
    
    def add_debug_data(self, data: DebugData):
        """添加调试数据"""
        with self.lock:
            self.debug_data.append(data)
            
            # 更新性能指标
            if data.data_type in ['performance_metric', 'system_resource']:
                try:
                    value = float(data.value)
                    self.performance_metrics[data.name].append({
                        'timestamp': data.timestamp,
                        'value': value
                    })
                except (ValueError, TypeError):
                    pass
    
    def add_analysis_result(self, result: AnalysisResult):
        """添加分析结果"""
        with self.lock:
            self.analysis_results.append(result)
    
    def update_system_stats(self, stats: Dict[str, Any]):
        """更新系统统计信息"""
        with self.lock:
            self.system_stats.update(stats)
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        with self.lock:
            logs = list(self.logs)[-limit:]
            return [asdict(log) for log in logs]
    
    def get_recent_debug_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的调试数据"""
        with self.lock:
            data = list(self.debug_data)[-limit:]
            return [asdict(d) for d in data]
    
    def get_analysis_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取分析结果"""
        with self.lock:
            results = list(self.analysis_results)[-limit:]
            return [result.to_dict() for result in results]
    
    def get_performance_data(self, metric_name: str = None) -> Dict[str, Any]:
        """获取性能数据"""
        with self.lock:
            if metric_name:
                return {
                    metric_name: list(self.performance_metrics.get(metric_name, []))
                }
            else:
                return {
                    name: list(data) for name, data in self.performance_metrics.items()
                }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        with self.lock:
            # 统计日志级别分布
            log_levels = defaultdict(int)
            for log in self.logs:
                log_levels[log.level] += 1
            
            # 统计分析结果严重程度
            severity_dist = defaultdict(int)
            for result in self.analysis_results:
                severity_dist[result.severity] += 1
            
            return {
                'total_logs': len(self.logs),
                'total_debug_data': len(self.debug_data),
                'total_analysis_results': len(self.analysis_results),
                'log_level_distribution': dict(log_levels),
                'severity_distribution': dict(severity_dist),
                'system_stats': self.system_stats.copy(),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }


class WebDashboardHandler(BaseHTTPRequestHandler):
    """Web仪表板HTTP处理器"""
    
    def __init__(self, *args, dashboard_data: DashboardData = None, **kwargs):
        self.dashboard_data = dashboard_data
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/' or path == '/index.html':
            self._serve_dashboard_html()
        elif path == '/api/summary':
            self._serve_json(self.dashboard_data.get_summary())
        elif path == '/api/logs':
            limit = int(query_params.get('limit', [50])[0])
            self._serve_json(self.dashboard_data.get_recent_logs(limit))
        elif path == '/api/debug_data':
            limit = int(query_params.get('limit', [50])[0])
            self._serve_json(self.dashboard_data.get_recent_debug_data(limit))
        elif path == '/api/analysis':
            limit = int(query_params.get('limit', [20])[0])
            self._serve_json(self.dashboard_data.get_analysis_results(limit))
        elif path == '/api/performance':
            metric = query_params.get('metric', [None])[0]
            self._serve_json(self.dashboard_data.get_performance_data(metric))
        elif path.startswith('/static/'):
            self._serve_static_file(path)
        else:
            self._send_404()
    
    def _serve_dashboard_html(self):
        """提供仪表板HTML页面"""
        html_content = self._get_dashboard_html()
        self._send_response(200, html_content, 'text/html')
    
    def _serve_json(self, data: Any):
        """提供JSON响应"""
        json_content = json.dumps(data, ensure_ascii=False, default=str)
        self._send_response(200, json_content, 'application/json')
    
    def _serve_static_file(self, path: str):
        """提供静态文件"""
        # 简单的静态文件服务（实际应用中应该使用专门的静态文件服务器）
        self._send_404()
    
    def _send_response(self, status_code: int, content: str, content_type: str):
        """发送HTTP响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def _send_404(self):
        """发送404响应"""
        self._send_response(404, 'Not Found', 'text/plain')
    
    def _get_dashboard_html(self) -> str:
        """生成仪表板HTML页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>调试仪表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 300;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-value {
            font-weight: bold;
            color: #333;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-success { background-color: #4CAF50; }
        .status-warning { background-color: #FF9800; }
        .status-error { background-color: #F44336; }
        .status-info { background-color: #2196F3; }
        
        .log-entry {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            border-left: 4px solid #ddd;
        }
        
        .log-entry.error {
            background-color: #ffebee;
            border-left-color: #f44336;
        }
        
        .log-entry.warning {
            background-color: #fff3e0;
            border-left-color: #ff9800;
        }
        
        .log-entry.info {
            background-color: #e3f2fd;
            border-left-color: #2196f3;
        }
        
        .log-entry.debug {
            background-color: #f3e5f5;
            border-left-color: #9c27b0;
        }
        
        .analysis-result {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            border-left: 4px solid #ddd;
        }
        
        .analysis-result.critical {
            background-color: #ffebee;
            border-left-color: #d32f2f;
        }
        
        .analysis-result.high {
            background-color: #fff3e0;
            border-left-color: #f57c00;
        }
        
        .analysis-result.medium {
            background-color: #fff8e1;
            border-left-color: #fbc02d;
        }
        
        .analysis-result.low {
            background-color: #e8f5e8;
            border-left-color: #388e3c;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            transition: opacity 0.2s ease;
        }
        
        .refresh-btn:hover {
            opacity: 0.9;
        }
        
        .auto-refresh {
            margin-left: 1rem;
        }
        
        .auto-refresh input {
            margin-right: 0.5rem;
        }
        
        .chart-container {
            height: 200px;
            margin-top: 1rem;
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        .error-message {
            background-color: #ffebee;
            color: #d32f2f;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 调试仪表板</h1>
        <div style="margin-top: 0.5rem; opacity: 0.9;">
            实时监控系统状态和调试信息
        </div>
    </div>
    
    <div class="container">
        <div style="margin-bottom: 2rem; display: flex; align-items: center;">
            <button class="refresh-btn" onclick="refreshAll()">🔄 刷新数据</button>
            <div class="auto-refresh">
                <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
                <label for="autoRefresh">自动刷新 (5秒)</label>
            </div>
            <div style="margin-left: auto; color: #666;">
                最后更新: <span id="lastUpdate">-</span>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- 系统概览 -->
            <div class="card">
                <h3>📊 系统概览</h3>
                <div id="systemOverview" class="loading">加载中...</div>
            </div>
            
            <!-- 日志统计 -->
            <div class="card">
                <h3>📝 日志统计</h3>
                <div id="logStats" class="loading">加载中...</div>
            </div>
            
            <!-- 分析结果 -->
            <div class="card">
                <h3>🔍 分析结果</h3>
                <div id="analysisStats" class="loading">加载中...</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- 最近日志 -->
            <div class="card">
                <h3>📋 最近日志</h3>
                <div id="recentLogs" class="loading">加载中...</div>
            </div>
            
            <!-- 分析结果详情 -->
            <div class="card">
                <h3>⚠️ 分析结果</h3>
                <div id="analysisResults" class="loading">加载中...</div>
            </div>
        </div>
    </div>
    
    <script>
        let autoRefreshInterval = null;
        
        function formatTimestamp(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN');
        }
        
        function getStatusClass(level) {
            const levelMap = {
                'ERROR': 'error',
                'FATAL': 'error',
                'WARNING': 'warning',
                'INFO': 'info',
                'DEBUG': 'debug',
                'TRACE': 'debug'
            };
            return levelMap[level] || 'info';
        }
        
        function getSeverityClass(severity) {
            return severity.toLowerCase();
        }
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error(`获取数据失败 (${endpoint}):`, error);
                return null;
            }
        }
        
        async function updateSystemOverview() {
            const data = await fetchData('/api/summary');
            const container = document.getElementById('systemOverview');
            
            if (!data) {
                container.innerHTML = '<div class="error-message">获取系统概览失败</div>';
                return;
            }
            
            container.innerHTML = `
                <div class="metric">
                    <span>总日志数</span>
                    <span class="metric-value">${data.total_logs}</span>
                </div>
                <div class="metric">
                    <span>调试数据</span>
                    <span class="metric-value">${data.total_debug_data}</span>
                </div>
                <div class="metric">
                    <span>分析结果</span>
                    <span class="metric-value">${data.total_analysis_results}</span>
                </div>
                <div class="metric">
                    <span>更新时间</span>
                    <span class="metric-value">${formatTimestamp(data.timestamp)}</span>
                </div>
            `;
        }
        
        async function updateLogStats() {
            const data = await fetchData('/api/summary');
            const container = document.getElementById('logStats');
            
            if (!data) {
                container.innerHTML = '<div class="error-message">获取日志统计失败</div>';
                return;
            }
            
            let html = '';
            for (const [level, count] of Object.entries(data.log_level_distribution || {})) {
                const statusClass = getStatusClass(level);
                html += `
                    <div class="metric">
                        <span><span class="status-indicator status-${statusClass}"></span>${level}</span>
                        <span class="metric-value">${count}</span>
                    </div>
                `;
            }
            
            container.innerHTML = html || '<div style="color: #666;">暂无日志数据</div>';
        }
        
        async function updateAnalysisStats() {
            const data = await fetchData('/api/summary');
            const container = document.getElementById('analysisStats');
            
            if (!data) {
                container.innerHTML = '<div class="error-message">获取分析统计失败</div>';
                return;
            }
            
            let html = '';
            for (const [severity, count] of Object.entries(data.severity_distribution || {})) {
                const severityClass = getSeverityClass(severity);
                html += `
                    <div class="metric">
                        <span><span class="status-indicator status-${severityClass === 'critical' ? 'error' : severityClass === 'high' ? 'warning' : 'info'}"></span>${severity}</span>
                        <span class="metric-value">${count}</span>
                    </div>
                `;
            }
            
            container.innerHTML = html || '<div style="color: #666;">暂无分析结果</div>';
        }
        
        async function updateRecentLogs() {
            const data = await fetchData('/api/logs?limit=10');
            const container = document.getElementById('recentLogs');
            
            if (!data) {
                container.innerHTML = '<div class="error-message">获取最近日志失败</div>';
                return;
            }
            
            let html = '';
            for (const log of data.slice(-10)) {
                const levelClass = getStatusClass(log.level);
                const time = new Date(log.timestamp).toLocaleTimeString('zh-CN');
                html += `
                    <div class="log-entry ${levelClass}">
                        <div style="font-weight: bold; margin-bottom: 0.25rem;">
                            [${time}] ${log.level} - ${log.logger}
                        </div>
                        <div>${log.message}</div>
                    </div>
                `;
            }
            
            container.innerHTML = html || '<div style="color: #666;">暂无日志记录</div>';
        }
        
        async function updateAnalysisResults() {
            const data = await fetchData('/api/analysis?limit=5');
            const container = document.getElementById('analysisResults');
            
            if (!data) {
                container.innerHTML = '<div class="error-message">获取分析结果失败</div>';
                return;
            }
            
            let html = '';
            for (const result of data.slice(-5)) {
                const severityClass = getSeverityClass(result.severity);
                const time = new Date(result.timestamp).toLocaleTimeString('zh-CN');
                html += `
                    <div class="analysis-result ${severityClass}">
                        <div style="font-weight: bold; margin-bottom: 0.5rem;">
                            ${result.title}
                        </div>
                        <div style="margin-bottom: 0.5rem; color: #666;">
                            ${result.description}
                        </div>
                        <div style="font-size: 0.9rem; color: #888;">
                            ${time} | 置信度: ${(result.confidence * 100).toFixed(1)}%
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html || '<div style="color: #666;">暂无分析结果</div>';
        }
        
        async function refreshAll() {
            document.getElementById('lastUpdate').textContent = '更新中...';
            
            await Promise.all([
                updateSystemOverview(),
                updateLogStats(),
                updateAnalysisStats(),
                updateRecentLogs(),
                updateAnalysisResults()
            ]);
            
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('zh-CN');
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshAll, 5000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            refreshAll();
            
            // 默认启用自动刷新
            document.getElementById('autoRefresh').checked = true;
            toggleAutoRefresh();
        });
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """禁用默认的日志输出"""
        pass


class WebDashboard:
    """Web仪表板服务器"""
    
    def __init__(self, port: int = 8080, host: str = 'localhost'):
        self.port = port
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.dashboard_data = DashboardData()
        self.running = False
    
    def start(self, open_browser: bool = True):
        """启动Web仪表板"""
        if self.running:
            return
        
        # 找到可用端口
        port = self._find_available_port(self.port)
        
        # 创建处理器类
        def handler_factory(*args, **kwargs):
            return WebDashboardHandler(*args, dashboard_data=self.dashboard_data, **kwargs)
        
        # 创建服务器
        try:
            self.server = HTTPServer((self.host, port), handler_factory)
            self.running = True
            
            # 启动服务器线程
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            url = f"http://{self.host}:{port}"
            get_logger().info(
                f"Web仪表板已启动: {url}",
                "debug_dashboard",
                port=port,
                host=self.host
            )
            
            # 打开浏览器
            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception as e:
                    get_logger().warning(
                        f"无法自动打开浏览器: {e}",
                        "debug_dashboard"
                    )
            
            return url
            
        except Exception as e:
            get_logger().error(
                f"启动Web仪表板失败: {e}",
                "debug_dashboard"
            )
            raise
    
    def stop(self):
        """停止Web仪表板"""
        if not self.running:
            return
        
        self.running = False
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5.0)
        
        get_logger().info("Web仪表板已停止", "debug_dashboard")
    
    def _find_available_port(self, start_port: int) -> int:
        """找到可用端口"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                continue
        
        raise RuntimeError(f"无法找到可用端口 (尝试范围: {start_port}-{start_port + 99})")
    
    def add_log(self, log: LogRecord):
        """添加日志记录"""
        self.dashboard_data.add_log(log)
    
    def add_debug_data(self, data: DebugData):
        """添加调试数据"""
        self.dashboard_data.add_debug_data(data)
    
    def add_analysis_result(self, result: AnalysisResult):
        """添加分析结果"""
        self.dashboard_data.add_analysis_result(result)


class ConsoleDashboard:
    """命令行仪表板"""
    
    def __init__(self):
        self.dashboard_data = DashboardData()
        self.running = False
        self.update_thread: Optional[threading.Thread] = None
    
    def start(self, update_interval: float = 5.0):
        """启动命令行仪表板"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(
            target=self._update_loop,
            args=(update_interval,),
            daemon=True
        )
        self.update_thread.start()
        
        get_logger().info(
            f"命令行仪表板已启动，更新间隔: {update_interval}秒",
            "debug_dashboard"
        )
    
    def stop(self):
        """停止命令行仪表板"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5.0)
        
        get_logger().info("命令行仪表板已停止", "debug_dashboard")
    
    def _update_loop(self, interval: float):
        """更新循环"""
        while self.running:
            try:
                self._display_dashboard()
                time.sleep(interval)
            except Exception as e:
                get_logger().error(
                    f"命令行仪表板更新错误: {e}",
                    "debug_dashboard"
                )
                time.sleep(1.0)
    
    def _display_dashboard(self):
        """显示仪表板"""
        # 清屏（在支持的终端中）
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 获取数据摘要
        summary = self.dashboard_data.get_summary()
        
        # 显示标题
        print("=" * 60)
        print("🔍 调试仪表板")
        print(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 显示系统概览
        print("\n📊 系统概览:")
        print(f"  总日志数: {summary['total_logs']}")
        print(f"  调试数据: {summary['total_debug_data']}")
        print(f"  分析结果: {summary['total_analysis_results']}")
        
        # 显示日志级别分布
        if summary['log_level_distribution']:
            print("\n📝 日志级别分布:")
            for level, count in summary['log_level_distribution'].items():
                emoji = self._get_level_emoji(level)
                print(f"  {emoji} {level}: {count}")
        
        # 显示分析结果严重程度分布
        if summary['severity_distribution']:
            print("\n⚠️ 分析结果严重程度:")
            for severity, count in summary['severity_distribution'].items():
                emoji = self._get_severity_emoji(severity)
                print(f"  {emoji} {severity}: {count}")
        
        # 显示最近的日志
        recent_logs = self.dashboard_data.get_recent_logs(5)
        if recent_logs:
            print("\n📋 最近日志:")
            for log in recent_logs[-5:]:
                timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
                emoji = self._get_level_emoji(log['level'])
                print(f"  {emoji} [{time_str}] {log['level']} - {log['message'][:50]}...")
        
        # 显示最近的分析结果
        analysis_results = self.dashboard_data.get_analysis_results(3)
        if analysis_results:
            print("\n🔍 最近分析结果:")
            for result in analysis_results[-3:]:
                timestamp = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
                emoji = self._get_severity_emoji(result['severity'])
                print(f"  {emoji} [{time_str}] {result['title']}")
                print(f"      {result['description'][:60]}...")
        
        print("\n" + "=" * 60)
        print("💡 提示: 按 Ctrl+C 退出")
    
    def _get_level_emoji(self, level: str) -> str:
        """获取日志级别对应的emoji"""
        emoji_map = {
            'TRACE': '🔍',
            'DEBUG': '🐛',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'FATAL': '💀'
        }
        return emoji_map.get(level, '📝')
    
    def _get_severity_emoji(self, severity: str) -> str:
        """获取严重程度对应的emoji"""
        emoji_map = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        return emoji_map.get(severity, '⚪')
    
    def add_log(self, log: LogRecord):
        """添加日志记录"""
        self.dashboard_data.add_log(log)
    
    def add_debug_data(self, data: DebugData):
        """添加调试数据"""
        self.dashboard_data.add_debug_data(data)
    
    def add_analysis_result(self, result: AnalysisResult):
        """添加分析结果"""
        self.dashboard_data.add_analysis_result(result)


class DashboardManager:
    """仪表板管理器"""
    
    def __init__(self):
        self.web_dashboard: Optional[WebDashboard] = None
        self.console_dashboard: Optional[ConsoleDashboard] = None
        self.data_handlers_registered = False
    
    def start_web_dashboard(self, port: int = 8080, host: str = 'localhost',
                           open_browser: bool = True) -> str:
        """启动Web仪表板"""
        if self.web_dashboard is None:
            self.web_dashboard = WebDashboard(port, host)
        
        url = self.web_dashboard.start(open_browser)
        self._register_data_handlers()
        return url
    
    def start_console_dashboard(self, update_interval: float = 5.0):
        """启动命令行仪表板"""
        if self.console_dashboard is None:
            self.console_dashboard = ConsoleDashboard()
        
        self.console_dashboard.start(update_interval)
        self._register_data_handlers()
    
    def stop_web_dashboard(self):
        """停止Web仪表板"""
        if self.web_dashboard:
            self.web_dashboard.stop()
    
    def stop_console_dashboard(self):
        """停止命令行仪表板"""
        if self.console_dashboard:
            self.console_dashboard.stop()
    
    def stop_all(self):
        """停止所有仪表板"""
        self.stop_web_dashboard()
        self.stop_console_dashboard()
    
    def _register_data_handlers(self):
        """注册数据处理器"""
        if self.data_handlers_registered:
            return
        
        # 注册日志处理器
        from .log_manager import get_logger
        logger = get_logger()
        
        # 注册调试数据处理器
        collector_manager = get_collector_manager()
        collector_manager.add_data_handler(self._handle_debug_data)
        
        # 注册分析结果处理器
        analysis_engine = get_analysis_engine()
        
        self.data_handlers_registered = True
        
        get_logger().info(
            "仪表板数据处理器已注册",
            "debug_dashboard"
        )
    
    def _handle_debug_data(self, data: DebugData):
        """处理调试数据"""
        if self.web_dashboard:
            self.web_dashboard.add_debug_data(data)
        
        if self.console_dashboard:
            self.console_dashboard.add_debug_data(data)
    
    def add_log(self, log: LogRecord):
        """添加日志记录"""
        if self.web_dashboard:
            self.web_dashboard.add_log(log)
        
        if self.console_dashboard:
            self.console_dashboard.add_log(log)
    
    def add_analysis_result(self, result: AnalysisResult):
        """添加分析结果"""
        if self.web_dashboard:
            self.web_dashboard.add_analysis_result(result)
        
        if self.console_dashboard:
            self.console_dashboard.add_analysis_result(result)


# 全局仪表板管理器实例
_global_dashboard_manager: Optional[DashboardManager] = None


def get_dashboard_manager() -> DashboardManager:
    """获取全局仪表板管理器实例"""
    global _global_dashboard_manager
    
    if _global_dashboard_manager is None:
        _global_dashboard_manager = DashboardManager()
    
    return _global_dashboard_manager


# 便捷函数
def start_web_dashboard(port: int = 8080, host: str = 'localhost',
                       open_browser: bool = True) -> str:
    """启动Web仪表板"""
    return get_dashboard_manager().start_web_dashboard(port, host, open_browser)


def start_console_dashboard(update_interval: float = 5.0):
    """启动命令行仪表板"""
    get_dashboard_manager().start_console_dashboard(update_interval)


def stop_all_dashboards():
    """停止所有仪表板"""
    get_dashboard_manager().stop_all()


if __name__ == "__main__":
    # 测试代码
    import tempfile
    from .log_manager import setup_logging
    from .debug_collector import get_collector_manager
    
    # 设置日志
    temp_dir = Path(tempfile.mkdtemp())
    log_config = {
        'session_id': 'test_dashboard_session',
        'console': {'enabled': True, 'level': 'INFO'},
        'file': {
            'enabled': True,
            'path': temp_dir / 'dashboard_test.log',
            'level': 'DEBUG'
        }
    }
    setup_logging(log_config)
    
    # 启动收集器
    collector_manager = get_collector_manager('test_dashboard_session')
    collector_manager.start_auto_collect(2.0)
    
    # 启动仪表板
    dashboard_manager = get_dashboard_manager()
    
    try:
        # 启动Web仪表板
        url = dashboard_manager.start_web_dashboard(port=8080, open_browser=False)
        print(f"Web仪表板已启动: {url}")
        
        # 启动命令行仪表板
        dashboard_manager.start_console_dashboard(update_interval=3.0)
        
        # 生成一些测试数据
        logger = get_logger()
        for i in range(10):
            logger.info(f"测试日志消息 {i}", "test_module", iteration=i)
            if i % 3 == 0:
                logger.warning(f"测试警告消息 {i}", "test_module")
            if i % 5 == 0:
                logger.error(f"测试错误消息 {i}", "test_module")
            
            time.sleep(1)
        
        print("\n测试运行中，按 Ctrl+C 退出...")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止...")
    
    finally:
        # 清理
        dashboard_manager.stop_all()
        collector_manager.close()
        
        print(f"\n测试日志已保存到: {temp_dir / 'dashboard_test.log'}")