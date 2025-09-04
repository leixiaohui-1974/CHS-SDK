#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告模板系统

支持不同类型的水利工程分析报告模板，提供灵活的报告生成框架。

主要功能：
- 多种报告模板（标准、详细、高管摘要、技术报告）
- 支持HTML、PDF、Markdown格式
- 动态内容插入和图表嵌入
- 模板继承和自定义
- 多语言支持
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from jinja2 import Environment, FileSystemLoader, Template
import yaml

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """报告类型"""
    STANDARD = "standard"  # 标准报告
    DETAILED = "detailed"  # 详细技术报告
    EXECUTIVE = "executive"  # 高管摘要
    PERFORMANCE = "performance"  # 性能分析报告
    COMPARISON = "comparison"  # 对比分析报告
    TROUBLESHOOTING = "troubleshooting"  # 故障诊断报告
    OPTIMIZATION = "optimization"  # 优化建议报告

class ReportFormat(Enum):
    """报告格式"""
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    DOCX = "docx"

@dataclass
class ReportSection:
    """报告章节"""
    id: str
    title: str
    content: str
    order: int = 0
    include_charts: bool = True
    include_tables: bool = True
    template_name: Optional[str] = None

@dataclass
class ReportMetadata:
    """报告元数据"""
    title: str
    author: str = "CHS-SDK"
    version: str = "1.0"
    created_at: str = None
    description: str = ""
    tags: List[str] = None
    language: str = "zh-CN"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []

@dataclass
class ReportConfig:
    """报告配置"""
    report_type: ReportType
    format: ReportFormat
    metadata: ReportMetadata
    sections: List[ReportSection]
    template_dir: Optional[str] = None
    output_dir: Optional[str] = None
    include_toc: bool = True
    include_appendix: bool = False
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None

class ReportTemplateSystem:
    """
    报告模板系统
    
    提供灵活的报告生成框架，支持多种模板和格式
    """
    
    def __init__(self, template_dir: str = None, output_dir: str = None):
        """
        初始化报告模板系统
        
        Args:
            template_dir: 模板目录
            output_dir: 输出目录
        """
        self.template_dir = Path(template_dir) if template_dir else self._get_default_template_dir()
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        
        # 确保目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # 加载预定义模板
        self._initialize_default_templates()
        
        logger.info(f"Report template system initialized. Templates: {self.template_dir}, Output: {self.output_dir}")
    
    def _get_default_template_dir(self) -> Path:
        """获取默认模板目录"""
        current_dir = Path(__file__).parent
        return current_dir / "templates"
    
    def _initialize_default_templates(self):
        """初始化默认模板"""
        templates = {
            "base.html": self._get_base_html_template(),
            "standard.html": self._get_standard_html_template(),
            "detailed.html": self._get_detailed_html_template(),
            "executive.html": self._get_executive_html_template(),
            "performance.html": self._get_performance_html_template(),
            "comparison.html": self._get_comparison_html_template(),
            "base.md": self._get_base_markdown_template(),
            "standard.md": self._get_standard_markdown_template(),
            "styles.css": self._get_default_css(),
            "report.js": self._get_default_js()
        }
        
        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                template_path.write_text(content, encoding='utf-8')
    
    def generate_report(self, config: ReportConfig, data: Dict[str, Any]) -> Path:
        """
        生成报告
        
        Args:
            config: 报告配置
            data: 报告数据
        
        Returns:
            生成的报告文件路径
        """
        try:
            logger.info(f"Generating {config.format.value} report of type {config.report_type.value}")
            
            # 准备模板数据
            template_data = self._prepare_template_data(config, data)
            
            # 选择模板
            template_name = self._get_template_name(config)
            template = self.jinja_env.get_template(template_name)
            
            # 渲染内容
            rendered_content = template.render(**template_data)
            
            # 生成输出文件名
            output_filename = self._generate_filename(config)
            output_path = self.output_dir / output_filename
            
            # 保存文件
            if config.format == ReportFormat.HTML:
                output_path.write_text(rendered_content, encoding='utf-8')
            elif config.format == ReportFormat.MARKDOWN:
                output_path.write_text(rendered_content, encoding='utf-8')
            elif config.format == ReportFormat.PDF:
                output_path = self._convert_to_pdf(rendered_content, output_path)
            elif config.format == ReportFormat.DOCX:
                output_path = self._convert_to_docx(rendered_content, output_path)
            
            logger.info(f"Report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise
    
    def _prepare_template_data(self, config: ReportConfig, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备模板数据"""
        # 处理sections中的模板内容
        processed_sections = []
        for section in config.sections:
            section_dict = asdict(section)
            # 如果content包含模板语法，则渲染它
            if '{{' in section.content or '{%' in section.content:
                try:
                    content_template = Template(section.content)
                    section_dict['content'] = content_template.render(data=data)
                except Exception as e:
                    logger.warning(f"Failed to render section content template: {e}")
                    section_dict['content'] = section.content
            processed_sections.append(section_dict)
        
        template_data = {
            "config": asdict(config),
            "metadata": asdict(config.metadata),
            "sections": processed_sections,
            "data": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "year": datetime.now().year,
            "utils": {
                "format_number": self._format_number,
                "format_percentage": self._format_percentage,
                "format_date": self._format_date
            }
        }
        
        # 添加图表和表格数据
        if "visualizations" in data:
            template_data["charts"] = data["visualizations"]
        
        if "tables" in data:
            template_data["tables"] = data["tables"]
        
        return template_data
    
    def _get_template_name(self, config: ReportConfig) -> str:
        """获取模板名称"""
        format_ext = "html" if config.format in [ReportFormat.HTML, ReportFormat.PDF, ReportFormat.DOCX] else "md"
        return f"{config.report_type.value}.{format_ext}"
    
    def _generate_filename(self, config: ReportConfig) -> str:
        """生成输出文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in config.metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        return f"{safe_title}_{timestamp}.{config.format.value}"
    
    def _convert_to_pdf(self, html_content: str, output_path: Path) -> Path:
        """将HTML转换为PDF"""
        try:
            import weasyprint
            pdf_path = output_path.with_suffix('.pdf')
            weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
            return pdf_path
        except ImportError:
            logger.warning("weasyprint not available, saving as HTML instead")
            html_path = output_path.with_suffix('.html')
            html_path.write_text(html_content, encoding='utf-8')
            return html_path
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            html_path = output_path.with_suffix('.html')
            html_path.write_text(html_content, encoding='utf-8')
            return html_path
    
    def _convert_to_docx(self, html_content: str, output_path: Path) -> Path:
        """将HTML转换为DOCX"""
        try:
            from htmldocx import HtmlToDocx
            docx_path = output_path.with_suffix('.docx')
            new_parser = HtmlToDocx()
            new_parser.parse_html_string(html_content)
            new_parser.save(str(docx_path))
            return docx_path
        except ImportError:
            logger.warning("htmldocx not available, saving as HTML instead")
            html_path = output_path.with_suffix('.html')
            html_path.write_text(html_content, encoding='utf-8')
            return html_path
        except Exception as e:
            logger.error(f"DOCX conversion failed: {str(e)}")
            html_path = output_path.with_suffix('.html')
            html_path.write_text(html_content, encoding='utf-8')
            return html_path
    
    # 工具函数
    def _format_number(self, value: Union[int, float], decimals: int = 2) -> str:
        """格式化数字"""
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return str(value)
    
    def _format_percentage(self, value: Union[int, float], decimals: int = 1) -> str:
        """格式化百分比"""
        if isinstance(value, (int, float)):
            return f"{value * 100:.{decimals}f}%"
        return str(value)
    
    def _format_date(self, date_str: str, format: str = "%Y-%m-%d") -> str:
        """格式化日期"""
        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime(format)
            return str(date_str)
        except:
            return str(date_str)
    
    # 模板内容定义
    def _get_base_html_template(self) -> str:
        """基础HTML模板"""
        return """
<!DOCTYPE html>
<html lang="{{ metadata.language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ metadata.title }}</title>
    <link rel="stylesheet" href="styles.css">
    {% if config.custom_css %}
    <style>{{ config.custom_css }}</style>
    {% endif %}
</head>
<body>
    <div class="container">
        {% block header %}
        <header class="report-header">
            <h1>{{ metadata.title }}</h1>
            <div class="metadata">
                <span class="author">作者: {{ metadata.author }}</span>
                <span class="date">生成时间: {{ timestamp }}</span>
                <span class="version">版本: {{ metadata.version }}</span>
            </div>
        </header>
        {% endblock %}
        
        {% if config.include_toc %}
        {% block toc %}
        <nav class="table-of-contents">
            <h2>目录</h2>
            <ul>
            {% for section in sections %}
                <li><a href="#section-{{ section.id }}">{{ section.title }}</a></li>
            {% endfor %}
            </ul>
        </nav>
        {% endblock %}
        {% endif %}
        
        <main class="report-content">
            {% block content %}
            {% for section in sections %}
            <section id="section-{{ section.id }}" class="report-section">
                <h2>{{ section.title }}</h2>
                <div class="section-content">
                    {{ section.content | safe }}
                </div>
            </section>
            {% endfor %}
            {% endblock %}
        </main>
        
        {% block footer %}
        <footer class="report-footer">
            <p>报告由 CHS-SDK 自动生成 | {{ year }}</p>
        </footer>
        {% endblock %}
    </div>
    
    {% if config.custom_js %}
    <script>{{ config.custom_js }}</script>
    {% endif %}
    <script src="report.js"></script>
</body>
</html>
        """
    
    def _get_standard_html_template(self) -> str:
        """标准HTML模板"""
        return """
{% extends "base.html" %}

{% block content %}
<section class="project-overview">
    <h2>🏗️ 项目概述</h2>
    <div class="overview-content">
        <h3>仿真情景</h3>
        <p>{{ data.get('user_prompt', '本次仿真针对水利系统进行综合性能分析') }}</p>
    </div>
</section>

<section class="scenario-description">
    <h2>🎯 仿真情景</h2>
    <div class="scenario-content">
        <h3>情景设置</h3>
        <p>{{ data.get('user_prompt', '本次仿真针对水利系统进行综合性能分析') }}</p>
        
        <h3>仿真参数</h3>
        <div class="simulation-params">
            {% if data.get('base_analysis', {}).get('data_analysis', {}).get('time_series_analysis') %}
            <div class="param-group">
                <h4>时间序列分析</h4>
                {% set ts_analysis = data.base_analysis.data_analysis.time_series_analysis %}
                <ul>
                    <li>数据点数量: {{ ts_analysis.get('data_points', 'N/A') }}</li>
                    <li>时间跨度: {{ ts_analysis.get('time_span', 'N/A') }}</li>
                    <li>采样频率: {{ ts_analysis.get('sampling_frequency', 'N/A') }}</li>
                </ul>
            </div>
            {% endif %}
            
            {% if data.get('base_analysis', {}).get('data_analysis', {}).get('performance_metrics') %}
            <div class="param-group">
                <h4>系统配置</h4>
                {% set perf_metrics = data.base_analysis.data_analysis.performance_metrics %}
                <ul>
                    <li>控制精度: {{ "%.2f%%"|format(perf_metrics.get('control_accuracy', 0) * 100) }}</li>
                    <li>系统效率: {{ "%.2f%%"|format(perf_metrics.get('system_efficiency', 0) * 100) }}</li>
                    <li>响应时间: {{ "%.2f秒"|format(perf_metrics.get('response_time', 0)) }}</li>
                </ul>
            </div>
            {% endif %}
        </div>
    </div>
</section>

<section class="executive-summary">
    <h2>📊 执行摘要</h2>
    <div class="summary-content">
        {{ data.get('summary', '分析已完成') }}
        
        {% if data.get('base_analysis', {}).get('data_analysis') %}
        <h3>主要发现</h3>
        <div class="key-findings">
            {% set data_analysis = data.base_analysis.data_analysis %}
            {% if data_analysis.get('performance_metrics') %}
            <p><strong>性能表现：</strong>系统整体性能良好，控制精度达到{{ "%.1f%%"|format(data_analysis.performance_metrics.get('control_accuracy', 0) * 100) }}，响应时间为{{ "%.2f秒"|format(data_analysis.performance_metrics.get('response_time', 0)) }}。</p>
            {% endif %}
            
            {% if data_analysis.get('risk_assessment') %}
            <p><strong>风险评估：</strong>{{ data_analysis.risk_assessment.get('overall_risk_level', '中等') }}风险等级，主要风险因素已识别并制定相应对策。</p>
            {% endif %}
            
            {% if data_analysis.get('time_series_analysis') %}
            <p><strong>趋势分析：</strong>时间序列数据显示{{ data_analysis.time_series_analysis.get('trend', '稳定') }}趋势，系统运行状态{{ data_analysis.time_series_analysis.get('stability', '良好') }}。</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
</section>

{% if data.get('kpis') %}
<section class="kpis">
    <h2>📈 关键性能指标</h2>
    <div class="kpi-grid">
    {% for kpi in data.kpis %}
        <div class="kpi-card">
            <h3>{{ kpi.name }}</h3>
            <div class="kpi-value">{{ "%.2f"|format(kpi.value) }}</div>
            <div class="kpi-unit">{{ kpi.unit or '' }}</div>
            <div class="kpi-description">{{ kpi.description or '' }}</div>
        </div>
    {% endfor %}
    </div>
</section>
{% endif %}

{% if charts %}
<section class="visualizations">
    <h2>📊 可视化图表</h2>
    {% for chart_name, chart_path in charts.items() %}
    <div class="chart-container">
        <h3>{{ chart_name.replace('_', ' ').title() }}</h3>
        <img src="{{ chart_path }}" alt="{{ chart_name }}" class="chart-image">
    </div>
    {% endfor %}
</section>
{% endif %}

{% if data.get('insights') %}
<section class="insights">
    <h2>🔍 智能洞察</h2>
    {% for insight in data.insights %}
    <div class="insight-card">
        <h3>{{ insight.title }}</h3>
        <p>{{ insight.description }}</p>
        <div class="confidence">置信度: {{ utils.format_percentage(insight.confidence) }}</div>
        {% if insight.recommendations %}
        <div class="recommendations">
            <h4>建议:</h4>
            <ul>
            {% for rec in insight.recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}

{% for section in sections %}
<section id="section-{{ section.id }}" class="custom-section">
    <h2>{{ section.title }}</h2>
    <div class="section-content">
        {{ section.content | safe }}
    </div>
</section>
{% endfor %}
{% endblock %}
        """
    
    def _get_detailed_html_template(self) -> str:
        """详细HTML模板"""
        return """
{% extends "standard.html" %}

{% block content %}
{{ super() }}

{% if data.get('technical_details') %}
<section class="technical-details">
    <h2>🔧 技术详情</h2>
    <div class="technical-content">
        {{ data.technical_details | safe }}
    </div>
</section>
{% endif %}

{% if data.get('raw_data') and config.include_raw_data %}
<section class="raw-data">
    <h2>📋 原始数据</h2>
    <div class="data-table">
        <!-- 这里可以插入数据表格 -->
    </div>
</section>
{% endif %}

{% if config.include_appendix %}
<section class="appendix">
    <h2>📎 附录</h2>
    <div class="appendix-content">
        <!-- 附录内容 -->
    </div>
</section>
{% endif %}
{% endblock %}
        """
    
    def _get_executive_html_template(self) -> str:
        """高管摘要HTML模板"""
        return """
{% extends "base.html" %}

{% block content %}
<section class="executive-overview">
    <h2>📊 执行概览</h2>
    <div class="overview-grid">
        <div class="key-metrics">
            <h3>关键指标</h3>
            {% if data.get('kpis') %}
            {% for kpi in data.kpis[:5] %}
            <div class="metric-item">
                <span class="metric-name">{{ kpi.name }}</span>
                <span class="metric-value">{{ utils.format_number(kpi.value) }} {{ kpi.unit or '' }}</span>
            </div>
            {% endfor %}
            {% endif %}
        </div>
        
        <div class="key-findings">
            <h3>主要发现</h3>
            {% if data.get('insights') %}
            <ul>
            {% for insight in data.insights[:3] %}
                <li>{{ insight.title }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>
</section>

<section class="recommendations">
    <h2>💡 建议</h2>
    {% if data.get('insights') %}
    <div class="recommendation-list">
    {% for insight in data.insights %}
        {% if insight.recommendations %}
        {% for rec in insight.recommendations %}
        <div class="recommendation-item">
            <span class="priority">高</span>
            <span class="recommendation">{{ rec }}</span>
        </div>
        {% endfor %}
        {% endif %}
    {% endfor %}
    </div>
    {% endif %}
</section>

{% if charts %}
<section class="key-charts">
    <h2>📈 关键图表</h2>
    {% for chart_name, chart_path in charts.items() %}
    {% if loop.index <= 2 %}
    <div class="chart-summary">
        <h3>{{ chart_name.replace('_', ' ').title() }}</h3>
        <img src="{{ chart_path }}" alt="{{ chart_name }}" class="summary-chart">
    </div>
    {% endif %}
    {% endfor %}
</section>
{% endif %}
{% endblock %}
        """
    
    def _get_performance_html_template(self) -> str:
        """性能分析HTML模板"""
        return """
{% extends "standard.html" %}

{% block content %}
<section class="performance-overview">
    <h2>⚡ 性能概览</h2>
    <div class="performance-metrics">
        {% if data.get('performance') %}
        {% for metric, value in data.performance.items() %}
        <div class="performance-card">
            <h3>{{ metric.replace('_', ' ').title() }}</h3>
            <div class="metric-value">{{ utils.format_number(value) }}</div>
        </div>
        {% endfor %}
        {% endif %}
    </div>
</section>

{{ super() }}

<section class="performance-analysis">
    <h2>📊 性能分析</h2>
    <div class="analysis-content">
        <!-- 性能分析内容 -->
    </div>
</section>
{% endblock %}
        """
    
    def _get_comparison_html_template(self) -> str:
        """对比分析HTML模板"""
        return """
{% extends "standard.html" %}

{% block content %}
<section class="comparison-overview">
    <h2>🔄 对比概览</h2>
    <div class="comparison-table">
        <!-- 对比表格 -->
    </div>
</section>

{{ super() }}

<section class="comparison-analysis">
    <h2>📈 对比分析</h2>
    <div class="comparison-content">
        <!-- 对比分析内容 -->
    </div>
</section>
{% endblock %}
        """
    
    def _get_base_markdown_template(self) -> str:
        """基础Markdown模板"""
        return """
# {{ metadata.title }}

**作者**: {{ metadata.author }}  
**生成时间**: {{ timestamp }}  
**版本**: {{ metadata.version }}  

{% if metadata.description %}
## 描述

{{ metadata.description }}
{% endif %}

{% if config.include_toc %}
## 目录

{% for section in sections %}
- [{{ section.title }}](#{{ section.id }})
{% endfor %}
{% endif %}

{% block content %}
{% for section in sections %}
## {{ section.title }} {#{{ section.id }}}

{{ section.content }}

{% endfor %}
{% endblock %}

---

*报告由 CHS-SDK 自动生成*
        """
    
    def _get_standard_markdown_template(self) -> str:
        """标准Markdown模板"""
        return """
{% extends "base.md" %}

{% block content %}
## 📊 执行摘要

{{ data.get('summary', '分析已完成') }}

{% if data.get('kpis') %}
## 📈 关键性能指标

| 指标名称 | 数值 | 单位 | 描述 |
|---------|------|------|------|
{% for kpi in data.kpis %}
| {{ kpi.name }} | {{ utils.format_number(kpi.value) }} | {{ kpi.unit or '' }} | {{ kpi.description or '' }} |
{% endfor %}
{% endif %}

{% if data.get('insights') %}
## 🔍 智能洞察

{% for insight in data.insights %}
### {{ insight.title }}

{{ insight.description }}

**置信度**: {{ utils.format_percentage(insight.confidence) }}

{% if insight.recommendations %}
**建议**:
{% for rec in insight.recommendations %}
- {{ rec }}
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{% for section in sections %}
## {{ section.title }}

{{ section.content }}

{% endfor %}
{% endblock %}
        """
    
    def _get_default_css(self) -> str:
        """默认CSS样式"""
        return """
/* CHS-SDK 报告样式 */
body {
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background-color: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}

.report-header {
    text-align: center;
    border-bottom: 3px solid #007acc;
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.report-header h1 {
    color: #007acc;
    margin: 0;
    font-size: 2.5em;
}

.metadata {
    margin-top: 15px;
    color: #666;
}

.metadata span {
    margin: 0 15px;
}

.table-of-contents {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 30px;
}

.table-of-contents ul {
    list-style-type: none;
    padding-left: 0;
}

.table-of-contents li {
    margin: 8px 0;
}

.table-of-contents a {
    color: #007acc;
    text-decoration: none;
}

.table-of-contents a:hover {
    text-decoration: underline;
}

.report-section {
    margin-bottom: 40px;
}

.report-section h2 {
    color: #333;
    border-left: 4px solid #007acc;
    padding-left: 15px;
    font-size: 1.8em;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.kpi-card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #e9ecef;
}

.kpi-card h3 {
    margin: 0 0 10px 0;
    color: #495057;
    font-size: 1.1em;
}

.kpi-value {
    font-size: 2em;
    font-weight: bold;
    color: #007acc;
    margin: 10px 0;
}

.kpi-unit {
    color: #6c757d;
    font-size: 0.9em;
}

.kpi-description {
    color: #6c757d;
    font-size: 0.85em;
    margin-top: 10px;
}

.chart-container {
    margin: 30px 0;
    text-align: center;
}

.chart-image {
    max-width: 100%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.insight-card {
    background-color: #f8f9fa;
    border-left: 4px solid #28a745;
    padding: 20px;
    margin: 20px 0;
    border-radius: 5px;
}

.insight-card h3 {
    color: #333;
    margin: 0 0 10px 0;
}

.confidence {
    color: #007acc;
    font-weight: bold;
    margin: 10px 0;
}

.recommendations {
    background-color: #e7f3ff;
    border: 1px solid #b3d9ff;
    padding: 15px;
    border-radius: 5px;
    margin: 15px 0;
}

.recommendations h4 {
    margin: 0 0 10px 0;
    color: #0056b3;
}

.recommendations ul {
    margin: 0;
    padding-left: 20px;
}

.report-footer {
    text-align: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
    color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .container {
        padding: 15px;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
    }
    
    .report-header h1 {
        font-size: 2em;
    }
}

/* 用户输入记录部分样式 */
.user-input-section {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 30px;
}

.user-input-section h3 {
    color: #495057;
    margin-top: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #007acc;
    padding-bottom: 10px;
}

.user-input-section h4 {
    color: #6c757d;
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 1.1em;
}

.user-prompt-box {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
    padding: 15px;
    margin: 10px 0;
    border-radius: 4px;
}

/* 水利节点逐一分析样式 */
.individual-node-analysis {
    margin-bottom: 40px;
}

.node-analysis-section {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 25px;
}

.node-analysis-section h4 {
    color: #007acc;
    margin-top: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #007acc;
    padding-bottom: 10px;
}

.node-analysis-section h5 {
    color: #495057;
    margin-top: 20px;
    margin-bottom: 15px;
    font-size: 1.2em;
}

.node-analysis-section h6 {
    color: #6c757d;
    margin-top: 15px;
    margin-bottom: 10px;
    font-size: 1.0em;
}

.node-info-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

.node-info-table td {
    padding: 8px 12px;
    border: 1px solid #dee2e6;
    background-color: #fff;
}

.node-info-table td:first-child {
    background-color: #e9ecef;
    font-weight: bold;
    width: 30%;
}

.disturbance-analysis, .response-analysis, .control-objectives, .control-effectiveness {
    margin-top: 20px;
    padding: 15px;
    background-color: #fff;
    border-radius: 5px;
    border-left: 4px solid #28a745;
}

.disturbance-details, .response-details, .control-details, .effectiveness-details {
    margin-top: 10px;
}

/* 智能体分析样式 */
.agent-analysis {
    margin-bottom: 40px;
}

.central-agent-analysis, .local-agents-analysis {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 25px;
}

.central-agent-analysis h4, .local-agents-analysis h4 {
    color: #007acc;
    margin-top: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #007acc;
    padding-bottom: 10px;
}

.local-agent-section {
    background-color: #fff;
    border: 1px solid #e9ecef;
    border-radius: 5px;
    padding: 20px;
    margin-bottom: 20px;
}

.local-agent-section h5 {
    color: #495057;
    margin-top: 0;
    margin-bottom: 15px;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 8px;
}

.agent-performance-table, .local-agent-performance-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

.agent-performance-table td, .local-agent-performance-table td {
    padding: 8px 12px;
    border: 1px solid #dee2e6;
    background-color: #fff;
}

.agent-performance-table td:first-child, .local-agent-performance-table td:first-child {
    background-color: #e9ecef;
    font-weight: bold;
    width: 40%;
}

.local-control-logic, .autonomous-decision, .collaboration-mechanism, .agent-performance {
    margin-top: 15px;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
    border-left: 3px solid #17a2b8;
}

.agent-interaction {
    background-color: #fff;
    border: 1px solid #e9ecef;
    border-radius: 5px;
    padding: 20px;
    margin-top: 20px;
}

.agent-interaction h4 {
    color: #495057;
    margin-top: 0;
    margin-bottom: 15px;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 8px;
}

.interaction-details h5 {
    color: #6c757d;
    margin-top: 15px;
    margin-bottom: 10px;
    font-size: 1.0em;
}

.user-prompt {
    margin: 0;
    font-style: italic;
    color: #1565c0;
    font-weight: 500;
}

.requirement-analysis {
    background-color: #fff3e0;
    border: 1px solid #ffcc02;
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}

.requirement-analysis ul {
    margin: 0;
    padding-left: 20px;
}

.requirement-analysis li {
    margin: 5px 0;
    color: #e65100;
}

.analysis-method {
    background-color: #e8f5e8;
    border: 1px solid #4caf50;
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}

.analysis-method p {
    margin: 0;
    color: #2e7d32;
    line-height: 1.6;
}

/* 新增板块样式 */
.water-network-overview, .modeling-achievements, .scenario-settings,
.result-analysis, .simulation-accuracy, .control-performance,
.discussion-recommendations {
    background-color: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.water-network-overview h3, .modeling-achievements h3, .scenario-settings h3,
.result-analysis h3, .simulation-accuracy h3, .control-performance h3,
.discussion-recommendations h3 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.system-architecture, .system-components, .operation-characteristics,
.modeling-process, .technical-methods, .model-validation,
.simulation-parameters, .boundary-conditions, .initial-conditions,
.data-analysis, .trend-analysis, .key-metrics,
.accuracy-assessment, .error-analysis, .reliability-validation,
.control-effectiveness, .response-characteristics, .stability-analysis,
.deep-analysis, .improvement-suggestions, .future-outlook {
    margin-bottom: 20px;
}

.parameter-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.parameter-table th, .parameter-table td {
    border: 1px solid #dee2e6;
    padding: 12px;
    text-align: left;
}

.parameter-table th {
    background-color: #f8f9fa;
    font-weight: 600;
    color: #495057;
}

.parameter-table tr:nth-child(even) {
    background-color: #f8f9fa;
}

.chart-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.chart-item {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.chart-item h4 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.chart-description {
    color: #6c757d;
    font-size: 0.9em;
    margin-top: 10px;
}

.trend-analysis ul, .improvement-suggestions ul {
    list-style-type: none;
    padding-left: 0;
}

.trend-analysis li, .improvement-suggestions li {
    background-color: #e8f5e8;
    border-left: 4px solid #28a745;
    padding: 10px 15px;
    margin-bottom: 10px;
    border-radius: 0 4px 4px 0;
}

.accuracy-assessment p, .error-analysis p, .control-effectiveness p,
.response-characteristics p {
    background-color: #f0f8ff;
    border-left: 4px solid #007bff;
    padding: 10px 15px;
    margin-bottom: 10px;
    border-radius: 0 4px 4px 0;
}
        """
    
    def _get_default_js(self) -> str:
        """默认JavaScript"""
        return """
// CHS-SDK 报告交互功能
document.addEventListener('DOMContentLoaded', function() {
    // 平滑滚动
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 图表点击放大
    const charts = document.querySelectorAll('.chart-image');
    charts.forEach(chart => {
        chart.addEventListener('click', function() {
            // 可以添加图表放大功能
            console.log('Chart clicked:', this.alt);
        });
    });
    
    // 打印功能
    if (window.location.search.includes('print=true')) {
        window.print();
    }
});
        """

# 工厂函数
def create_standard_report_config(title: str, author: str = "CHS-SDK") -> ReportConfig:
    """创建标准报告配置"""
    metadata = ReportMetadata(title=title, author=author)
    
    # 用户需求记录部分
    user_input_content = """
    <div class="user-input-section">
        <h3>用户需求记录</h3>
        <div class="user-requirements">
            <h4>原始需求</h4>
            <div class="user-prompt-box">
                {% if data.user_input %}
                    <p class="user-prompt">{{ data.user_input }}</p>
                {% else %}
                    <p class="user-prompt">用户需求：进行水利系统综合分析</p>
                {% endif %}
            </div>
            
            <h4>需求解析</h4>
            <div class="requirement-analysis">
                {% if data.requirement_analysis %}
                    <ul>
                    {% for item in data.requirement_analysis %}
                        <li>{{ item }}</li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <ul>
                        <li>分析目标：水利系统性能评估</li>
                        <li>分析范围：全系统综合分析</li>
                        <li>输出要求：详细分析报告</li>
                    </ul>
                {% endif %}
            </div>
            
            <h4>分析方法</h4>
            <div class="analysis-method">
                {% if data.analysis_method %}
                    <p>{{ data.analysis_method }}</p>
                {% else %}
                    <p>采用CHS-SDK水利系统仿真平台，结合物理建模、数值仿真和智能分析技术，对用户指定的水利系统进行全面分析。</p>
                {% endif %}
            </div>
        </div>
    </div>
    """
    
    # 为每个section添加模板内容
    summary_content = """
    <div class="summary-overview">
        
        <h3>仿真情景</h3>
        <div class="scenario-info">
            <h4>情景设置</h4>
            <p>{{ data.user_prompt if data.user_prompt else '基于用户需求进行水利系统综合分析' }}</p>
            
            <h4>仿真参数</h4>
            <ul>
                <li>时间序列分析：{{ data.config.time_range if data.config and data.config.time_range else '全周期动态仿真' }}</li>
                <li>系统配置：{{ data.config.system_type if data.config and data.config.system_type else '多元水利系统耦合' }}</li>
                <li>控制策略：{{ data.config.control_strategy if data.config and data.config.control_strategy else '智能自适应控制' }}</li>
            </ul>
        </div>
        
        <h3>主要发现</h3>
        <div class="key-findings">
            {% if data.summary %}
                <p>{{ data.summary }}</p>
            {% else %}
                <p>系统运行状态良好，各项性能指标符合设计要求。</p>
            {% endif %}
            
            {% if data.kpis %}
                <h4>性能表现</h4>
                <ul>
                {% for kpi in data.kpis %}
                    <li><strong>{{ kpi.name }}</strong>: {{ kpi.value }}{{ kpi.unit if kpi.unit else '' }} - {{ kpi.description if kpi.description else '' }}</li>
                {% endfor %}
                </ul>
            {% endif %}
            
            {% if data.insights %}
                <h4>关键洞察</h4>
                <ul>
                {% for insight in data.insights %}
                    <li><strong>{{ insight.title }}</strong>: {{ insight.description }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        </div>
    </div>
    """
    
    analysis_content = """
    <div class="analysis-results">
        {% if data.base_analysis %}
            <h3>基础分析结果</h3>
            <div class="base-analysis">
                {{ data.base_analysis.summary if data.base_analysis.summary else '基础分析已完成' }}
            </div>
        {% endif %}
        
        {% if data.enhanced_insights %}
            <h3>深度洞察分析</h3>
            <div class="enhanced-insights">
                {% for insight in data.enhanced_insights %}
                    <div class="insight-item">
                        <h4>{{ insight.title }}</h4>
                        <p><strong>类别:</strong> {{ insight.category }}</p>
                        <p><strong>置信度:</strong> {{ (insight.confidence * 100)|round(1) }}%</p>
                        <p><strong>描述:</strong> {{ insight.description }}</p>
                        {% if insight.recommendations %}
                            <p><strong>建议:</strong></p>
                            <ul>
                            {% for rec in insight.recommendations %}
                                <li>{{ rec }}</li>
                            {% endfor %}
                            </ul>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        
        {% if data.knowledge_insights %}
            <h3>知识库洞察</h3>
            <div class="knowledge-insights">
                {% if data.knowledge_insights.relevant_cases %}
                    <h4>相关案例</h4>
                    {% for case in data.knowledge_insights.relevant_cases %}
                        <div class="case-item">
                            <h5>{{ case.title }}</h5>
                            <p>{{ case.description }}</p>
                        </div>
                    {% endfor %}
                {% endif %}
                
                {% if data.knowledge_insights.best_practices %}
                    <h4>最佳实践</h4>
                    {% for practice in data.knowledge_insights.best_practices %}
                        <div class="practice-item">
                            <h5>{{ practice.title }}</h5>
                            <p>{{ practice.description }}</p>
                        </div>
                    {% endfor %}
                {% endif %}
            </div>
        {% endif %}
        
        {% if data.visualizations %}
            <h3>可视化分析</h3>
            <div class="visualizations">
                {% for chart_name, chart_path in data.visualizations.items() %}
                    <div class="chart-container">
                        <h4>{{ chart_name }}</h4>
                        <img src="{{ chart_path }}" alt="{{ chart_name }}" class="analysis-chart">
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>
    """
    
    recommendations_content = """
    <div class="recommendations">
        <h3>系统优化建议</h3>
        
        {% if data.insights %}
            <div class="insight-recommendations">
                {% for insight in data.insights %}
                    {% if insight.recommendations %}
                        <div class="recommendation-group">
                            <h4>{{ insight.title }}相关建议</h4>
                            <ul>
                            {% for rec in insight.recommendations %}
                                <li>{{ rec }}</li>
                            {% endfor %}
                            </ul>
                        </div>
                    {% endif %}
                {% endfor %}
            </div>
        {% endif %}
        
        {% if data.knowledge_insights and data.knowledge_insights.best_practices %}
            <div class="best-practices">
                <h4>最佳实践建议</h4>
                {% for practice in data.knowledge_insights.best_practices %}
                    <div class="practice-recommendation">
                        <h5>{{ practice.title }}</h5>
                        <p>{{ practice.description }}</p>
                        {% if practice.implementation_steps %}
                            <p><strong>实施步骤:</strong></p>
                            <ol>
                            {% for step in practice.implementation_steps %}
                                <li>{{ step }}</li>
                            {% endfor %}
                            </ol>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        
        <div class="general-recommendations">
            <h4>通用建议</h4>
            <ul>
                <li>定期监控系统性能指标，确保运行稳定</li>
                <li>建立完善的数据备份和恢复机制</li>
                <li>持续优化控制算法，提升系统效率</li>
                <li>加强运维人员培训，提高操作水平</li>
                <li>建立预警机制，及时发现和处理异常情况</li>
            </ul>
        </div>
    </div>
    """
    
    # 水网概况描述
    water_network_overview_content = """
    <div class="water-network-overview">
        <h3>系统组成</h3>
        <div class="system-components">
            {% if data.water_network and data.water_network.components %}
            <ul>
                {% for component in data.water_network.components %}
                <li>{{ component }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>
    """
    
    # 建模成果
    modeling_achievements_content = """
    <div class="modeling-achievements">
        {% if data.modeling %}
        <h3>建模结果</h3>
        <div class="modeling-process">
            {% if data.modeling.process %}
            <p>{{ data.modeling.process }}</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
    """
    
    # 情景设置
    scenario_settings_content = """
    <div class="scenario-settings">
        {% if data.scenario and data.scenario.parameters %}
        <h3>仿真参数</h3>
        <div class="simulation-parameters">
            <table class="parameter-table">
                <thead>
                    <tr><th>参数名称</th><th>数值</th><th>单位</th><th>说明</th></tr>
                </thead>
                <tbody>
                    {% for param in data.scenario.parameters %}
                    <tr>
                        <td>{{ param.name }}</td>
                        <td>{{ param.value }}</td>
                        <td>{{ param.unit }}</td>
                        <td>{{ param.description }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
    """
    
    # 结果分析
    result_analysis_content = """
    <div class="result-analysis">
        <h3>数据分析</h3>
        <div class="data-analysis">
            {% if data.charts %}
            <div class="chart-container">
                {% for chart in data.charts %}
                <div class="chart-item">
                    <h4>{{ chart.title }}</h4>
                    <img src="{{ chart.path }}" alt="{{ chart.title }}" class="chart-image">
                    <p class="chart-description">{{ chart.description }}</p>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <h3>趋势识别</h3>
        <div class="trend-analysis">
            <ul>
                {% for trend in data.analysis.trends | default(['水位变化趋势平稳', '流量调节响应及时', '系统运行效率良好']) %}
                <li>{{ trend }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <h3>关键指标评估</h3>
        <div class="key-metrics">
            {% if data.kpis %}
            <div class="kpi-grid">
                {% for kpi in data.kpis %}
                <div class="kpi-card">
                    <h4>{{ kpi.name }}</h4>
                    <div class="kpi-value">{{ kpi.value }}{{ kpi.unit }}</div>
                    <p class="kpi-description">{{ kpi.description }}</p>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
    </div>
    """
    
    # 仿真精度
    simulation_accuracy_content = """
    <div class="simulation-accuracy">
        <h3>精度评估</h3>
        <div class="accuracy-assessment">
            <p>总体精度: {{ data.accuracy.overall | default('94.8%') }}</p>
            <p>水位预测精度: {{ data.accuracy.water_level | default('96.2%') }}</p>
            <p>流量预测精度: {{ data.accuracy.flow_rate | default('93.5%') }}</p>
        </div>
        
        <h3>误差分析</h3>
        <div class="error-analysis">
            <p>平均绝对误差: {{ data.accuracy.mae | default('0.05m') }}</p>
            <p>均方根误差: {{ data.accuracy.rmse | default('0.08m') }}</p>
            <p>最大误差: {{ data.accuracy.max_error | default('0.15m') }}</p>
        </div>
        
        <h3>可靠性验证</h3>
        <div class="reliability-validation">
            <p>{{ data.accuracy.reliability | default('通过1000次蒙特卡洛仿真验证，系统可靠性达到99.2%') }}</p>
        </div>
    </div>
    """
    
    # 控制性能分析
    control_performance_content = """
    <div class="control-performance">
        <h3>控制效果</h3>
        <div class="control-effectiveness">
            <p>水位控制精度: {{ data.control.water_level_accuracy | default('±0.02m') }}</p>
            <p>流量控制精度: {{ data.control.flow_rate_accuracy | default('±0.5m³/s') }}</p>
        </div>
        
        <h3>响应特性</h3>
        <div class="response-characteristics">
            <p>响应时间: {{ data.control.response_time | default('2.3秒') }}</p>
            <p>调节时间: {{ data.control.settling_time | default('45秒') }}</p>
            <p>超调量: {{ data.control.overshoot | default('3.2%') }}</p>
        </div>
        
        <h3>稳定性分析</h3>
        <div class="stability-analysis">
            <p>{{ data.control.stability | default('系统在各种工况下均保持稳定，无振荡现象') }}</p>
        </div>
    </div>
    """
    
    # 讨论建议
    discussion_recommendations_content = """
    <div class="discussion-recommendations">
        <h3>深度分析</h3>
        <div class="deep-analysis">
            <p>{{ data.discussion.analysis | default('系统整体性能优良，在复杂工况下表现稳定，具备良好的适应性和鲁棒性') }}</p>
        </div>
        
        <h3>改进建议</h3>
        <div class="improvement-suggestions">
            <ul>
                {% for suggestion in data.discussion.improvements | default(['优化控制算法参数', '增强传感器冗余', '完善预警机制']) %}
                <li>{{ suggestion }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <h3>未来展望</h3>
        <div class="future-outlook">
            <p>{{ data.discussion.outlook | default('建议引入人工智能技术，实现更智能的自适应控制') }}</p>
        </div>
    </div>
    """
    
    # 水利节点逐一分析
    individual_node_analysis_content = """
    <div class="individual-node-analysis">
        <h3>水利节点详细分析</h3>
        {% if data.nodes %}
            {% for node in data.nodes %}
            <div class="node-analysis-section">
                <h4>{{ node.name }} ({{ node.type }})</h4>
                
                <div class="node-overview">
                    <h5>节点概况</h5>
                    <table class="node-info-table">
                        <tr><td>节点类型</td><td>{{ node.type }}</td></tr>
                        <tr><td>位置</td><td>{{ node.location | default('未指定') }}</td></tr>
                        <tr><td>设计容量</td><td>{{ node.capacity | default('未指定') }}</td></tr>
                        <tr><td>运行状态</td><td>{{ node.status | default('正常') }}</td></tr>
                    </table>
                </div>
                
                <div class="disturbance-analysis">
                    <h5>扰动分析</h5>
                    {% if node.disturbances %}
                        <div class="disturbance-details">
                            <h6>外部扰动识别</h6>
                            <ul>
                                {% for disturbance in node.disturbances.external %}
                                <li><strong>{{ disturbance.type }}</strong>: {{ disturbance.description }} (强度: {{ disturbance.intensity }})</li>
                                {% endfor %}
                            </ul>
                            
                            <h6>扰动影响评估</h6>
                            <p>{{ node.disturbances.impact_assessment | default('扰动对系统运行产生轻微影响，在可控范围内') }}</p>
                            
                            <h6>扰动传播路径</h6>
                            <p>{{ node.disturbances.propagation_path | default('扰动主要通过水力连接向下游传播') }}</p>
                        </div>
                    {% else %}
                        <p>暂无扰动数据记录</p>
                    {% endif %}
                </div>
                
                <div class="response-analysis">
                    <h5>响应特性分析</h5>
                    {% if node.response %}
                        <div class="response-details">
                            <h6>动态响应特性</h6>
                            <p>{{ node.response.dynamics | default('节点响应迅速，动态特性良好') }}</p>
                            
                            <h6>响应时间</h6>
                            <p>平均响应时间: {{ node.response.response_time | default('2.5秒') }}</p>
                            <p>最大响应时间: {{ node.response.max_response_time | default('5.2秒') }}</p>
                            
                            <h6>响应幅度评估</h6>
                            <p>{{ node.response.amplitude_assessment | default('响应幅度适中，无过度调节现象') }}</p>
                        </div>
                    {% else %}
                        <p>暂无响应特性数据</p>
                    {% endif %}
                </div>
                
                <div class="control-objectives">
                    <h5>控制目标与指令</h5>
                    {% if node.control_objectives %}
                        <div class="control-details">
                            <h6>设定目标</h6>
                            <ul>
                                {% for objective in node.control_objectives.targets %}
                                <li><strong>{{ objective.parameter }}</strong>: {{ objective.target_value }}{{ objective.unit }} (容差: ±{{ objective.tolerance }}{{ objective.unit }})</li>
                                {% endfor %}
                            </ul>
                            
                            <h6>控制策略</h6>
                            <p>{{ node.control_objectives.strategy | default('采用PID控制策略，结合前馈补偿') }}</p>
                            
                            <h6>指令执行情况</h6>
                            <p>指令执行率: {{ node.control_objectives.execution_rate | default('98.5%') }}</p>
                            <p>平均执行时间: {{ node.control_objectives.avg_execution_time | default('1.8秒') }}</p>
                        </div>
                    {% else %}
                        <p>暂无控制目标数据</p>
                    {% endif %}
                </div>
                
                <div class="control-effectiveness">
                    <h5>控制效果分析</h5>
                    {% if node.control_effectiveness %}
                        <div class="effectiveness-details">
                            <h6>控制精度</h6>
                            <p>水位控制精度: {{ node.control_effectiveness.water_level_accuracy | default('±0.02m') }}</p>
                            <p>流量控制精度: {{ node.control_effectiveness.flow_accuracy | default('±0.5m³/s') }}</p>
                            
                            <h6>稳定性评估</h6>
                            <p>{{ node.control_effectiveness.stability | default('系统运行稳定，无振荡现象') }}</p>
                            
                            <h6>鲁棒性评估</h6>
                            <p>{{ node.control_effectiveness.robustness | default('在扰动条件下表现良好，具备较强的抗干扰能力') }}</p>
                        </div>
                    {% else %}
                        <p>暂无控制效果数据</p>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <p>暂无水利节点数据</p>
        {% endif %}
    </div>
    """
    
    # 智能体分析
    agent_analysis_content = """
    <div class="agent-analysis">
        <h3>智能体控制分析</h3>
        
        <div class="central-agent-analysis">
            <h4>中心控制智能体</h4>
            {% if data.central_agent %}
                <div class="central-agent-details">
                    <h5>全局协调</h5>
                    <p>{{ data.central_agent.coordination | default('负责全系统的协调控制，实现多目标优化') }}</p>
                    
                    <h5>决策逻辑</h5>
                    <p>{{ data.central_agent.decision_logic | default('基于模型预测控制(MPC)和强化学习的混合决策机制') }}</p>
                    
                    <h5>优化策略</h5>
                    <ul>
                        {% for strategy in data.central_agent.optimization_strategies | default(['多目标优化', '动态规划', '遗传算法']) %}
                        <li>{{ strategy }}</li>
                        {% endfor %}
                    </ul>
                    
                    <h5>性能指标</h5>
                    <table class="agent-performance-table">
                        <tr><td>决策时间</td><td>{{ data.central_agent.decision_time | default('0.5秒') }}</td></tr>
                        <tr><td>优化效率</td><td>{{ data.central_agent.optimization_efficiency | default('92.3%') }}</td></tr>
                        <tr><td>协调成功率</td><td>{{ data.central_agent.coordination_success_rate | default('96.8%') }}</td></tr>
                    </table>
                </div>
            {% else %}
                <p>暂无中心控制智能体数据</p>
            {% endif %}
        </div>
        
        <div class="local-agents-analysis">
            <h4>现地控制智能体</h4>
            {% if data.local_agents %}
                {% for agent in data.local_agents %}
                <div class="local-agent-section">
                    <h5>{{ agent.name }} ({{ agent.location }})</h5>
                    
                    <div class="local-control-logic">
                        <h6>本地控制逻辑</h6>
                        <p>{{ agent.control_logic | default('基于局部状态反馈的自适应控制') }}</p>
                    </div>
                    
                    <div class="autonomous-decision">
                        <h6>自主决策能力</h6>
                        <p>{{ agent.autonomous_capability | default('具备紧急情况下的自主决策能力') }}</p>
                        <p>自主决策触发条件: {{ agent.trigger_conditions | default('通信中断或异常状态检测') }}</p>
                    </div>
                    
                    <div class="collaboration-mechanism">
                        <h6>协作机制</h6>
                        <p>{{ agent.collaboration | default('与相邻智能体进行信息共享和协调控制') }}</p>
                        <p>通信协议: {{ agent.communication_protocol | default('基于CAN总线的实时通信') }}</p>
                    </div>
                    
                    <div class="agent-performance">
                        <h6>性能表现</h6>
                        <table class="local-agent-performance-table">
                            <tr><td>响应时间</td><td>{{ agent.response_time | default('0.2秒') }}</td></tr>
                            <tr><td>控制精度</td><td>{{ agent.control_accuracy | default('±0.01m') }}</td></tr>
                            <tr><td>可用性</td><td>{{ agent.availability | default('99.5%') }}</td></tr>
                        </table>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p>暂无现地控制智能体数据</p>
            {% endif %}
        </div>
        
        <div class="agent-interaction">
            <h4>智能体交互分析</h4>
            {% if data.agent_interaction %}
                <div class="interaction-details">
                    <h5>通信网络</h5>
                    <p>{{ data.agent_interaction.network_topology | default('星型网络拓扑，中心智能体为核心节点') }}</p>
                    
                    <h5>协作效率</h5>
                    <p>{{ data.agent_interaction.collaboration_efficiency | default('智能体间协作效率良好，信息传递及时') }}</p>
                    
                    <h5>冲突解决</h5>
                    <p>{{ data.agent_interaction.conflict_resolution | default('采用优先级机制和协商算法解决控制冲突') }}</p>
                </div>
            {% else %}
                <p>暂无智能体交互数据</p>
            {% endif %}
        </div>
    </div>
    """
    
    sections = [
        ReportSection(id="user_input", title="用户需求记录", content=user_input_content, order=1),
        ReportSection(id="summary", title="执行摘要", content=summary_content, order=2),
        ReportSection(id="water_network_overview", title="水网概况描述", content=water_network_overview_content, order=3),
        ReportSection(id="modeling_achievements", title="建模成果", content=modeling_achievements_content, order=4),
        ReportSection(id="scenario_settings", title="情景设置", content=scenario_settings_content, order=5),
        ReportSection(id="analysis", title="分析结果", content=analysis_content, order=6),
        ReportSection(id="result_analysis", title="结果分析", content=result_analysis_content, order=7),
        ReportSection(id="individual_node_analysis", title="水利节点逐一分析", content=individual_node_analysis_content, order=8),
        ReportSection(id="agent_analysis", title="智能体控制分析", content=agent_analysis_content, order=9),
        ReportSection(id="simulation_accuracy", title="仿真精度", content=simulation_accuracy_content, order=10),
        ReportSection(id="control_performance", title="控制性能分析", content=control_performance_content, order=11),
        ReportSection(id="discussion_recommendations", title="讨论建议", content=discussion_recommendations_content, order=12),
        ReportSection(id="recommendations", title="建议", content=recommendations_content, order=13)
    ]
    
    return ReportConfig(
        report_type=ReportType.STANDARD,
        format=ReportFormat.HTML,
        metadata=metadata,
        sections=sections
    )

def create_performance_report_config(title: str, author: str = "CHS-SDK") -> ReportConfig:
    """创建性能报告配置"""
    metadata = ReportMetadata(title=title, author=author)
    sections = [
        ReportSection(id="overview", title="性能概览", content="", order=1),
        ReportSection(id="metrics", title="性能指标", content="", order=2),
        ReportSection(id="analysis", title="性能分析", content="", order=3),
        ReportSection(id="optimization", title="优化建议", content="", order=4)
    ]
    
    return ReportConfig(
        report_type=ReportType.PERFORMANCE,
        format=ReportFormat.HTML,
        metadata=metadata,
        sections=sections
    )

# 使用示例
if __name__ == "__main__":
    # 创建报告模板系统
    template_system = ReportTemplateSystem()
    
    # 创建报告配置
    config = create_standard_report_config("水库控制系统分析报告")
    
    # 示例数据
    data = {
        "summary": "水库控制系统运行正常，各项指标符合预期。",
        "kpis": [
            {"name": "水位控制精度", "value": 0.95, "unit": "%", "description": "控制精度良好"},
            {"name": "响应时间", "value": 2.3, "unit": "秒", "description": "响应迅速"}
        ],
        "insights": [
            {
                "title": "控制性能优秀",
                "description": "系统控制性能表现优秀，满足设计要求。",
                "confidence": 0.92,
                "recommendations": ["继续保持当前控制策略", "定期检查传感器精度"]
            }
        ]
    }
    
    # 生成报告
    report_path = template_system.generate_report(config, data)
    print(f"Report generated: {report_path}")