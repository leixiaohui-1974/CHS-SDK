
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
        