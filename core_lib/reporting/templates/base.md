
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
        