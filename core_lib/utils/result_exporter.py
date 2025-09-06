#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台结果导出工具
提供多种格式的仿真结果导出功能
"""

import json
import csv
import logging
import os
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from io import BytesIO, StringIO

import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import LineChart, BarChart, ScatterChart, Reference
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from sqlalchemy.orm import Session
from core_lib.database.database import get_db
from core_lib.database.models import SimulationResult, ExportRecord

# 配置日志
logger = logging.getLogger(__name__)

class ExportFormat(Enum):
    """导出格式枚举"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"
    XML = "xml"
    MATLAB = "matlab"
    PYTHON = "python"
    ZIP = "zip"

class ChartType(Enum):
    """图表类型枚举"""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"
    VIOLIN = "violin"

@dataclass
class ExportOptions:
    """导出选项配置"""
    format: ExportFormat
    include_metadata: bool = True
    include_parameters: bool = True
    include_charts: bool = False
    chart_types: List[ChartType] = None
    custom_template: Optional[str] = None
    compression: bool = False
    password_protection: bool = False
    password: Optional[str] = None
    file_name_template: str = "simulation_results_{timestamp}"
    date_format: str = "%Y%m%d_%H%M%S"

@dataclass
class ExportResult:
    """导出结果"""
    export_id: str
    file_path: str
    file_size: int
    format: ExportFormat
    created_at: datetime
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class ResultExporter:
    """
    仿真结果导出器
    
    提供多种格式的仿真结果导出功能：
    - JSON格式导出
    - CSV格式导出
    - Excel格式导出（包含图表）
    - PDF报告导出
    - HTML报告导出
    - XML格式导出
    - MATLAB格式导出
    - Python脚本导出
    - 批量压缩导出
    """
    
    def __init__(self, export_dir: str = "exports"):
        """
        初始化结果导出器
        
        Args:
            export_dir: 导出文件目录
        """
        self.export_dir = export_dir
        
        # 确保导出目录存在
        os.makedirs(export_dir, exist_ok=True)
        
        # 设置matplotlib样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        logger.info(f"结果导出器初始化完成，导出目录: {export_dir}")
    
    async def export_results(
        self,
        result_ids: List[str],
        options: ExportOptions,
        user_id: str = None
    ) -> ExportResult:
        """
        导出仿真结果
        
        Args:
            result_ids: 结果ID列表
            options: 导出选项
            user_id: 用户ID
        
        Returns:
            ExportResult: 导出结果
        """
        try:
            logger.info(f"开始导出仿真结果，格式: {options.format.value}，结果数量: {len(result_ids)}")
            
            # 加载仿真结果数据
            results_data = await self._load_results_data(result_ids)
            
            if not results_data:
                raise ValueError("没有找到有效的仿真结果数据")
            
            # 生成文件名
            timestamp = datetime.now().strftime(options.date_format)
            file_name = options.file_name_template.format(timestamp=timestamp)
            
            # 根据格式执行导出
            if options.format == ExportFormat.JSON:
                file_path = await self._export_json(results_data, file_name, options)
            elif options.format == ExportFormat.CSV:
                file_path = await self._export_csv(results_data, file_name, options)
            elif options.format == ExportFormat.EXCEL:
                file_path = await self._export_excel(results_data, file_name, options)
            elif options.format == ExportFormat.PDF:
                file_path = await self._export_pdf(results_data, file_name, options)
            elif options.format == ExportFormat.HTML:
                file_path = await self._export_html(results_data, file_name, options)
            elif options.format == ExportFormat.XML:
                file_path = await self._export_xml(results_data, file_name, options)
            elif options.format == ExportFormat.MATLAB:
                file_path = await self._export_matlab(results_data, file_name, options)
            elif options.format == ExportFormat.PYTHON:
                file_path = await self._export_python(results_data, file_name, options)
            elif options.format == ExportFormat.ZIP:
                file_path = await self._export_zip(results_data, file_name, options)
            else:
                raise ValueError(f"不支持的导出格式: {options.format.value}")
            
            # 应用压缩和密码保护
            if options.compression or options.password_protection:
                file_path = await self._apply_post_processing(file_path, options)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 创建导出结果
            export_result = ExportResult(
                export_id=f"export_{timestamp}_{hash(str(result_ids))}",
                file_path=file_path,
                file_size=file_size,
                format=options.format,
                created_at=datetime.now()
            )
            
            # 保存导出记录
            await self._save_export_record(export_result, result_ids, user_id)
            
            logger.info(f"仿真结果导出完成，文件: {file_path}，大小: {file_size} bytes")
            return export_result
            
        except Exception as e:
            logger.error(f"导出仿真结果失败: {str(e)}")
            raise
    
    async def _export_json(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出JSON格式
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.json")
        
        # 构建导出数据
        export_data = {
            "export_info": {
                "format": "json",
                "created_at": datetime.now().isoformat(),
                "total_results": len(results_data)
            },
            "results": []
        }
        
        for result in results_data:
            result_export = {
                "result_id": result["id"],
                "name": result.get("name", ""),
                "created_at": result.get("created_at", ""),
                "outputs": result.get("outputs", {})
            }
            
            if options.include_parameters:
                result_export["parameters"] = result.get("parameters", {})
            
            if options.include_metadata:
                result_export["metadata"] = result.get("metadata", {})
            
            export_data["results"].append(result_export)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return file_path
    
    async def _export_csv(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出CSV格式
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.csv")
        
        # 展平数据结构
        flattened_data = []
        
        for result in results_data:
            row = {
                "result_id": result["id"],
                "name": result.get("name", ""),
                "created_at": result.get("created_at", "")
            }
            
            # 添加输出数据
            outputs = result.get("outputs", {})
            for key, value in outputs.items():
                if isinstance(value, (int, float, str)):
                    row[f"output_{key}"] = value
                elif isinstance(value, list) and len(value) > 0:
                    if all(isinstance(x, (int, float)) for x in value):
                        row[f"output_{key}_mean"] = np.mean(value)
                        row[f"output_{key}_std"] = np.std(value)
                        row[f"output_{key}_min"] = np.min(value)
                        row[f"output_{key}_max"] = np.max(value)
            
            # 添加参数数据
            if options.include_parameters:
                parameters = result.get("parameters", {})
                for key, value in parameters.items():
                    if isinstance(value, (int, float, str)):
                        row[f"param_{key}"] = value
            
            # 添加元数据
            if options.include_metadata:
                metadata = result.get("metadata", {})
                for key, value in metadata.items():
                    if isinstance(value, (int, float, str)):
                        row[f"meta_{key}"] = value
            
            flattened_data.append(row)
        
        # 写入CSV文件
        if flattened_data:
            df = pd.DataFrame(flattened_data)
            df.to_csv(file_path, index=False, encoding='utf-8')
        
        return file_path
    
    async def _export_excel(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出Excel格式（包含图表）
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.xlsx")
        
        # 创建工作簿
        wb = Workbook()
        
        # 删除默认工作表
        wb.remove(wb.active)
        
        # 创建摘要工作表
        summary_ws = wb.create_sheet("Summary")
        self._create_summary_sheet(summary_ws, results_data)
        
        # 创建详细数据工作表
        data_ws = wb.create_sheet("Data")
        self._create_data_sheet(data_ws, results_data, options)
        
        # 创建参数工作表
        if options.include_parameters:
            params_ws = wb.create_sheet("Parameters")
            self._create_parameters_sheet(params_ws, results_data)
        
        # 创建图表工作表
        if options.include_charts and options.chart_types:
            charts_ws = wb.create_sheet("Charts")
            self._create_charts_sheet(charts_ws, results_data, options.chart_types)
        
        # 保存工作簿
        wb.save(file_path)
        
        return file_path
    
    async def _export_pdf(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出PDF报告
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.pdf")
        
        # 创建PDF文档
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # 居中
        )
        story.append(Paragraph("仿真结果报告", title_style))
        story.append(Spacer(1, 20))
        
        # 摘要信息
        summary_data = [
            ["项目", "值"],
            ["结果数量", str(len(results_data))],
            ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["导出格式", "PDF"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # 详细结果
        for i, result in enumerate(results_data):
            # 结果标题
            result_title = f"结果 {i+1}: {result.get('name', result['id'][:8])}"
            story.append(Paragraph(result_title, styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # 结果详情表格
            result_data = [
                ["属性", "值"]
            ]
            
            # 基本信息
            result_data.append(["结果ID", result["id"]])
            result_data.append(["创建时间", str(result.get("created_at", ""))])
            
            # 输出数据
            outputs = result.get("outputs", {})
            for key, value in outputs.items():
                if isinstance(value, (int, float)):
                    result_data.append([f"输出_{key}", f"{value:.4f}"])
                elif isinstance(value, str):
                    result_data.append([f"输出_{key}", value])
                elif isinstance(value, list) and len(value) > 0:
                    if all(isinstance(x, (int, float)) for x in value):
                        result_data.append([f"输出_{key}_均值", f"{np.mean(value):.4f}"])
            
            # 参数数据
            if options.include_parameters:
                parameters = result.get("parameters", {})
                for key, value in parameters.items():
                    if isinstance(value, (int, float, str)):
                        result_data.append([f"参数_{key}", str(value)])
            
            result_table = Table(result_data)
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(result_table)
            story.append(Spacer(1, 20))
        
        # 生成图表（如果需要）
        if options.include_charts and options.chart_types:
            story.append(Paragraph("图表分析", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # 生成图表并添加到PDF
            chart_paths = await self._generate_charts(results_data, options.chart_types)
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    img = Image(chart_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 10))
        
        # 构建PDF
        doc.build(story)
        
        return file_path
    
    async def _export_html(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出HTML报告
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.html")
        
        # HTML模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>仿真结果报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        .summary {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .result-card {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            margin-bottom: 20px;
            padding: 20px;
            background-color: #ffffff;
        }
        .result-title {
            color: #2980b9;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>仿真结果报告</h1>
        
        <div class="summary">
            <h2>摘要信息</h2>
            <p><strong>结果数量:</strong> {{ results_count }}</p>
            <p><strong>生成时间:</strong> {{ generated_at }}</p>
            <p><strong>导出格式:</strong> HTML</p>
        </div>
        
        <h2>详细结果</h2>
        {% for result in results %}
        <div class="result-card">
            <div class="result-title">结果 {{ loop.index }}: {{ result.name or result.id[:8] }}</div>
            
            <table>
                <tr><th>属性</th><th>值</th></tr>
                <tr><td>结果ID</td><td>{{ result.id }}</td></tr>
                <tr><td>创建时间</td><td>{{ result.created_at }}</td></tr>
                
                {% for key, value in result.outputs.items() %}
                <tr><td>输出_{{ key }}</td><td>{{ value }}</td></tr>
                {% endfor %}
                
                {% if include_parameters %}
                {% for key, value in result.parameters.items() %}
                <tr><td>参数_{{ key }}</td><td>{{ value }}</td></tr>
                {% endfor %}
                {% endif %}
            </table>
        </div>
        {% endfor %}
        
        <div class="footer">
            <p>由CHS仿真平台生成 - {{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 渲染模板
        template = Template(html_template)
        html_content = template.render(
            results=results_data,
            results_count=len(results_data),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            include_parameters=options.include_parameters
        )
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    async def _export_xml(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出XML格式
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.xml")
        
        # 构建XML内容
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<simulation_results>')
        xml_content.append(f'  <export_info>')
        xml_content.append(f'    <format>xml</format>')
        xml_content.append(f'    <created_at>{datetime.now().isoformat()}</created_at>')
        xml_content.append(f'    <total_results>{len(results_data)}</total_results>')
        xml_content.append(f'  </export_info>')
        xml_content.append('  <results>')
        
        for result in results_data:
            xml_content.append(f'    <result id="{result["id"]}">')
            xml_content.append(f'      <name>{result.get("name", "")}</name>')
            xml_content.append(f'      <created_at>{result.get("created_at", "")}</created_at>')
            
            # 输出数据
            xml_content.append('      <outputs>')
            outputs = result.get("outputs", {})
            for key, value in outputs.items():
                if isinstance(value, (int, float, str)):
                    xml_content.append(f'        <{key}>{value}</{key}>')
                elif isinstance(value, list):
                    xml_content.append(f'        <{key}>')
                    for item in value:
                        xml_content.append(f'          <item>{item}</item>')
                    xml_content.append(f'        </{key}>')
            xml_content.append('      </outputs>')
            
            # 参数数据
            if options.include_parameters:
                xml_content.append('      <parameters>')
                parameters = result.get("parameters", {})
                for key, value in parameters.items():
                    xml_content.append(f'        <{key}>{value}</{key}>')
                xml_content.append('      </parameters>')
            
            # 元数据
            if options.include_metadata:
                xml_content.append('      <metadata>')
                metadata = result.get("metadata", {})
                for key, value in metadata.items():
                    xml_content.append(f'        <{key}>{value}</{key}>')
                xml_content.append('      </metadata>')
            
            xml_content.append('    </result>')
        
        xml_content.append('  </results>')
        xml_content.append('</simulation_results>')
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_content))
        
        return file_path
    
    async def _export_matlab(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出MATLAB格式
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.m")
        
        # 构建MATLAB脚本
        matlab_content = []
        matlab_content.append(f"% 仿真结果数据 - 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        matlab_content.append("% CHS仿真平台导出")
        matlab_content.append("")
        matlab_content.append("clear all; clc;")
        matlab_content.append("")
        matlab_content.append("% 结果数据结构")
        matlab_content.append(f"results = struct();")
        matlab_content.append(f"results.export_info.total_results = {len(results_data)};")
        matlab_content.append(f"results.export_info.created_at = '{datetime.now().isoformat()}';")
        matlab_content.append("")
        
        # 导出每个结果
        for i, result in enumerate(results_data):
            idx = i + 1  # MATLAB索引从1开始
            matlab_content.append(f"% 结果 {idx}")
            matlab_content.append(f"results.data({idx}).id = '{result['id']}';")
            matlab_content.append(f"results.data({idx}).name = '{result.get('name', '')}';")
            matlab_content.append(f"results.data({idx}).created_at = '{result.get('created_at', '')}';")
            
            # 输出数据
            outputs = result.get("outputs", {})
            for key, value in outputs.items():
                if isinstance(value, (int, float)):
                    matlab_content.append(f"results.data({idx}).outputs.{key} = {value};")
                elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                    value_str = '[' + ', '.join(map(str, value)) + ']'
                    matlab_content.append(f"results.data({idx}).outputs.{key} = {value_str};")
                elif isinstance(value, str):
                    matlab_content.append(f"results.data({idx}).outputs.{key} = '{value}';")
            
            # 参数数据
            if options.include_parameters:
                parameters = result.get("parameters", {})
                for key, value in parameters.items():
                    if isinstance(value, (int, float)):
                        matlab_content.append(f"results.data({idx}).parameters.{key} = {value};")
                    elif isinstance(value, str):
                        matlab_content.append(f"results.data({idx}).parameters.{key} = '{value}';")
            
            matlab_content.append("")
        
        # 添加一些有用的MATLAB函数
        matlab_content.append("% 辅助函数")
        matlab_content.append("function plot_results(results)")
        matlab_content.append("    % 绘制结果图表")
        matlab_content.append("    figure;")
        matlab_content.append("    % 在这里添加绘图代码")
        matlab_content.append("    title('仿真结果');")
        matlab_content.append("    xlabel('X轴');")
        matlab_content.append("    ylabel('Y轴');")
        matlab_content.append("    grid on;")
        matlab_content.append("end")
        matlab_content.append("")
        matlab_content.append("% 使用示例:")
        matlab_content.append("% plot_results(results);")
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(matlab_content))
        
        return file_path
    
    async def _export_python(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出Python脚本
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.export_dir, f"{file_name}.py")
        
        # 构建Python脚本
        python_content = []
        python_content.append("#!/usr/bin/env python3")
        python_content.append("# -*- coding: utf-8 -*-")
        python_content.append(f"\"\"\"")
        python_content.append(f"仿真结果数据 - 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        python_content.append(f"CHS仿真平台导出")
        python_content.append(f"\"\"\"")
        python_content.append("")
        python_content.append("import json")
        python_content.append("import pandas as pd")
        python_content.append("import matplotlib.pyplot as plt")
        python_content.append("import numpy as np")
        python_content.append("from datetime import datetime")
        python_content.append("")
        python_content.append("# 结果数据")
        python_content.append(f"RESULTS_DATA = {json.dumps(results_data, indent=4, default=str)}")
        python_content.append("")
        python_content.append("def load_results():")
        python_content.append("    \"\"\"加载仿真结果数据\"\"\"")
        python_content.append("    return RESULTS_DATA")
        python_content.append("")
        python_content.append("def get_result_by_id(result_id):")
        python_content.append("    \"\"\"根据ID获取结果\"\"\"")
        python_content.append("    for result in RESULTS_DATA:")
        python_content.append("        if result['id'] == result_id:")
        python_content.append("            return result")
        python_content.append("    return None")
        python_content.append("")
        python_content.append("def to_dataframe():")
        python_content.append("    \"\"\"转换为pandas DataFrame\"\"\"")
        python_content.append("    # 展平数据结构")
        python_content.append("    flattened_data = []")
        python_content.append("    for result in RESULTS_DATA:")
        python_content.append("        row = {")
        python_content.append("            'result_id': result['id'],")
        python_content.append("            'name': result.get('name', ''),")
        python_content.append("            'created_at': result.get('created_at', '')")
        python_content.append("        }")
        python_content.append("        ")
        python_content.append("        # 添加输出数据")
        python_content.append("        outputs = result.get('outputs', {})")
        python_content.append("        for key, value in outputs.items():")
        python_content.append("            if isinstance(value, (int, float, str)):")
        python_content.append("                row[f'output_{key}'] = value")
        python_content.append("            elif isinstance(value, list) and len(value) > 0:")
        python_content.append("                if all(isinstance(x, (int, float)) for x in value):")
        python_content.append("                    row[f'output_{key}_mean'] = np.mean(value)")
        python_content.append("                    row[f'output_{key}_std'] = np.std(value)")
        python_content.append("        ")
        python_content.append("        flattened_data.append(row)")
        python_content.append("    ")
        python_content.append("    return pd.DataFrame(flattened_data)")
        python_content.append("")
        python_content.append("def plot_results():")
        python_content.append("    \"\"\"绘制结果图表\"\"\"")
        python_content.append("    df = to_dataframe()")
        python_content.append("    ")
        python_content.append("    # 获取数值列")
        python_content.append("    numeric_columns = df.select_dtypes(include=[np.number]).columns")
        python_content.append("    ")
        python_content.append("    if len(numeric_columns) > 0:")
        python_content.append("        plt.figure(figsize=(12, 8))")
        python_content.append("        ")
        python_content.append("        for i, col in enumerate(numeric_columns[:4]):  # 最多显示4个图")
        python_content.append("            plt.subplot(2, 2, i+1)")
        python_content.append("            plt.plot(df[col])")
        python_content.append("            plt.title(col)")
        python_content.append("            plt.grid(True)")
        python_content.append("        ")
        python_content.append("        plt.tight_layout()")
        python_content.append("        plt.show()")
        python_content.append("    else:")
        python_content.append("        print('没有找到数值数据用于绘图')")
        python_content.append("")
        python_content.append("def export_to_csv(filename='exported_results.csv'):")
        python_content.append("    \"\"\"导出到CSV文件\"\"\"")
        python_content.append("    df = to_dataframe()")
        python_content.append("    df.to_csv(filename, index=False)")
        python_content.append("    print(f'结果已导出到 {filename}')")
        python_content.append("")
        python_content.append("if __name__ == '__main__':")
        python_content.append("    # 使用示例")
        python_content.append("    print(f'加载了 {len(RESULTS_DATA)} 个仿真结果')")
        python_content.append("    ")
        python_content.append("    # 转换为DataFrame")
        python_content.append("    df = to_dataframe()")
        python_content.append("    print('\\nDataFrame信息:')")
        python_content.append("    print(df.info())")
        python_content.append("    ")
        python_content.append("    # 显示前几行")
        python_content.append("    print('\\n前5行数据:')")
        python_content.append("    print(df.head())")
        python_content.append("    ")
        python_content.append("    # 绘制图表")
        python_content.append("    # plot_results()")
        python_content.append("    ")
        python_content.append("    # 导出CSV")
        python_content.append("    # export_to_csv()")
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(python_content))
        
        return file_path
    
    async def _export_zip(
        self,
        results_data: List[Dict[str, Any]],
        file_name: str,
        options: ExportOptions
    ) -> str:
        """
        导出ZIP压缩包（包含多种格式）
        
        Args:
            results_data: 结果数据
            file_name: 文件名
            options: 导出选项
        
        Returns:
            str: 文件路径
        """
        zip_path = os.path.join(self.export_dir, f"{file_name}.zip")
        
        # 创建临时目录
        temp_dir = os.path.join(self.export_dir, f"temp_{file_name}")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 生成多种格式的文件
            formats_to_export = [
                ExportFormat.JSON,
                ExportFormat.CSV,
                ExportFormat.EXCEL,
                ExportFormat.HTML
            ]
            
            exported_files = []
            
            for fmt in formats_to_export:
                temp_options = ExportOptions(
                    format=fmt,
                    include_metadata=options.include_metadata,
                    include_parameters=options.include_parameters,
                    include_charts=options.include_charts,
                    chart_types=options.chart_types
                )
                
                if fmt == ExportFormat.JSON:
                    file_path = await self._export_json(results_data, file_name, temp_options)
                elif fmt == ExportFormat.CSV:
                    file_path = await self._export_csv(results_data, file_name, temp_options)
                elif fmt == ExportFormat.EXCEL:
                    file_path = await self._export_excel(results_data, file_name, temp_options)
                elif fmt == ExportFormat.HTML:
                    file_path = await self._export_html(results_data, file_name, temp_options)
                
                # 移动文件到临时目录
                temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
                os.rename(file_path, temp_file_path)
                exported_files.append(temp_file_path)
            
            # 生成图表文件
            if options.include_charts and options.chart_types:
                chart_paths = await self._generate_charts(results_data, options.chart_types)
                for chart_path in chart_paths:
                    if os.path.exists(chart_path):
                        temp_chart_path = os.path.join(temp_dir, os.path.basename(chart_path))
                        os.rename(chart_path, temp_chart_path)
                        exported_files.append(temp_chart_path)
            
            # 创建ZIP文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in exported_files:
                    zipf.write(file_path, os.path.basename(file_path))
                
                # 添加README文件
                readme_content = f"""
仿真结果导出包
================

导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
结果数量: {len(results_data)}

包含文件:
{chr(10).join([f'- {os.path.basename(f)}' for f in exported_files])}

说明:
- JSON格式: 原始数据，适合程序处理
- CSV格式: 表格数据，适合Excel打开
- Excel格式: 包含图表的完整报告
- HTML格式: 网页报告，适合浏览器查看

由CHS仿真平台生成
                """
                
                zipf.writestr("README.txt", readme_content)
            
            return zip_path
            
        finally:
            # 清理临时文件
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    # 辅助方法实现...
    async def _load_results_data(self, result_ids: List[str]) -> List[Dict[str, Any]]:
        """加载仿真结果数据"""
        try:
            db = next(get_db())
            results_data = []
            
            for result_id in result_ids:
                result_record = db.query(SimulationResult).filter(
                    SimulationResult.id == result_id
                ).first()
                
                if result_record:
                    result_json = json.loads(result_record.result_data) if result_record.result_data else {}
                    
                    result_data = {
                        "id": result_id,
                        "name": result_json.get("name", ""),
                        "created_at": result_record.created_at,
                        "outputs": result_json.get("outputs", {}),
                        "parameters": result_json.get("parameters", {}),
                        "metadata": result_json.get("metadata", {})
                    }
                    
                    results_data.append(result_data)
            
            db.close()
            return results_data
            
        except Exception as e:
            logger.error(f"加载仿真结果数据失败: {str(e)}")
            raise
    
    def _create_summary_sheet(self, ws, results_data):
        """创建Excel摘要工作表"""
        # 标题
        ws['A1'] = '仿真结果摘要'
        ws['A1'].font = Font(size=16, bold=True)
        
        # 基本信息
        ws['A3'] = '结果数量:'
        ws['B3'] = len(results_data)
        ws['A4'] = '生成时间:'
        ws['B4'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 设置列宽
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 20
    
    def _create_data_sheet(self, ws, results_data, options):
        """创建Excel数据工作表"""
        # 表头
        headers = ['结果ID', '名称', '创建时间']
        
        # 添加输出列
        if results_data:
            sample_outputs = results_data[0].get('outputs', {})
            for key in sample_outputs.keys():
                headers.append(f'输出_{key}')
        
        # 添加参数列
        if options.include_parameters and results_data:
            sample_params = results_data[0].get('parameters', {})
            for key in sample_params.keys():
                headers.append(f'参数_{key}')
        
        # 写入表头
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
        
        # 写入数据
        for row, result in enumerate(results_data, 2):
            ws.cell(row=row, column=1, value=result['id'])
            ws.cell(row=row, column=2, value=result.get('name', ''))
            ws.cell(row=row, column=3, value=str(result.get('created_at', '')))
            
            col = 4
            # 输出数据
            outputs = result.get('outputs', {})
            for key in (results_data[0].get('outputs', {}).keys() if results_data else []):
                value = outputs.get(key, '')
                if isinstance(value, list):
                    value = str(value)
                ws.cell(row=row, column=col, value=value)
                col += 1
            
            # 参数数据
            if options.include_parameters:
                parameters = result.get('parameters', {})
                for key in (results_data[0].get('parameters', {}).keys() if results_data else []):
                    value = parameters.get(key, '')
                    ws.cell(row=row, column=col, value=value)
                    col += 1
    
    def _create_parameters_sheet(self, ws, results_data):
        """创建Excel参数工作表"""
        # 实现参数工作表创建逻辑
        pass
    
    def _create_charts_sheet(self, ws, results_data, chart_types):
        """创建Excel图表工作表"""
        # 实现图表工作表创建逻辑
        pass
    
    async def _generate_charts(self, results_data, chart_types):
        """生成图表文件"""
        chart_paths = []
        
        for chart_type in chart_types:
            try:
                chart_path = os.path.join(self.export_dir, f"chart_{chart_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
                plt.figure(figsize=(10, 6))
                
                if chart_type == ChartType.LINE:
                    # 生成线图
                    for i, result in enumerate(results_data[:5]):  # 最多显示5个结果
                        outputs = result.get('outputs', {})
                        for key, value in outputs.items():
                            if isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                                plt.plot(value, label=f"{result.get('name', f'Result {i+1}')} - {key}")
                                break
                    plt.title('结果趋势图')
                    plt.xlabel('时间点')
                    plt.ylabel('值')
                    plt.legend()
                    plt.grid(True)
                
                elif chart_type == ChartType.BAR:
                    # 生成柱状图
                    names = [result.get('name', f'Result {i+1}') for i, result in enumerate(results_data)]
                    values = []
                    
                    # 获取第一个数值输出
                    for result in results_data:
                        outputs = result.get('outputs', {})
                        for key, value in outputs.items():
                            if isinstance(value, (int, float)):
                                values.append(value)
                                break
                            elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                                values.append(np.mean(value))
                                break
                        else:
                            values.append(0)
                    
                    plt.bar(names, values)
                    plt.title('结果对比图')
                    plt.xlabel('结果')
                    plt.ylabel('值')
                    plt.xticks(rotation=45)
                
                plt.tight_layout()
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                chart_paths.append(chart_path)
                
            except Exception as e:
                logger.warning(f"生成图表失败 {chart_type.value}: {str(e)}")
        
        return chart_paths
    
    async def _apply_post_processing(self, file_path, options):
        """应用后处理（压缩、加密等）"""
        # 实现压缩和密码保护逻辑
        return file_path
    
    async def _save_export_record(self, export_result, result_ids, user_id):
        """保存导出记录"""
        try:
            db = next(get_db())
            
            export_record = ExportRecord(
                id=export_result.export_id,
                user_id=user_id,
                result_ids=json.dumps(result_ids),
                format=export_result.format.value,
                file_path=export_result.file_path,
                file_size=export_result.file_size,
                created_at=export_result.created_at
            )
            
            db.add(export_record)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"保存导出记录失败: {str(e)}")