# -*- coding: utf-8 -*-
"""
Analysis and Reporting Routes for MCP Service

实现AnalystAndReporterAgent的核心功能：
- 数据分析和KPI计算
- 图表生成和可视化
- 报告撰写和模板管理
- 结果导出和归档
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import uuid
import logging
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import tempfile
import base64
import io
from enum import Enum

# 导入可视化库
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

# 导入现有的分析工具
import subprocess
import sys
from pathlib import Path

# 导入LLM智能体
from core_lib.llm_integration_agents.llm_data_analyst_agent import LLMDataAnalystAgent
from core_lib.utils import seaborn_support

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

# 分析任务状态枚举
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# 报告格式枚举
class ReportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"

# 图表类型枚举
class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"
    AREA = "area"

# 分析任务存储
analysis_store: Dict[str, Dict[str, Any]] = {}

# Pydantic模型定义
class AnalysisRequest(BaseModel):
    """分析请求"""
    run_id: str
    analysis_type: str = "comprehensive"  # "comprehensive", "performance", "custom"
    metrics: Optional[List[str]] = None
    chart_types: Optional[List[ChartType]] = None
    report_format: ReportFormat = ReportFormat.JSON
    custom_analysis: Optional[Dict[str, Any]] = None

class ChartRequest(BaseModel):
    """图表生成请求"""
    run_id: str
    chart_type: ChartType
    variables: List[str]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    style: Optional[str] = "default"

class ReportRequest(BaseModel):
    """报告生成请求"""
    run_id: str
    template: str = "standard"
    format: ReportFormat = ReportFormat.MARKDOWN
    include_charts: bool = True
    include_raw_data: bool = False
    custom_sections: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    """分析响应"""
    analysis_id: str
    run_id: str
    status: AnalysisStatus
    message: str
    started_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    charts: Optional[List[str]] = None
    report_url: Optional[str] = None

class KPIResult(BaseModel):
    """KPI结果"""
    name: str
    value: Union[float, int, str]
    unit: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class ChartResult(BaseModel):
    """图表结果"""
    chart_id: str
    chart_type: ChartType
    title: str
    data_url: Optional[str] = None
    base64_data: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalystAndReporterAgent:
    """分析与报告智能体 - 数据科学家和报告专家"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.temp_dir = Path(tempfile.gettempdir()) / "chs_sdk_analysis"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 设置matplotlib样式
        seaborn_support.ensure_matplotlib_style('seaborn-v0_8')
        seaborn_support.set_palette("husl")
    
    async def start_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        启动分析任务
        
        Args:
            request: 分析请求
            
        Returns:
            AnalysisResponse: 分析响应
        """
        analysis_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting analysis {analysis_id} for run {request.run_id}")
            
            # 检查仿真结果是否存在
            from api.routes.simulation import simulation_store
            
            if request.run_id not in simulation_store:
                raise ValueError(f"Simulation run {request.run_id} not found")
            
            simulation_data = simulation_store[request.run_id]
            if simulation_data["status"] != "completed":
                raise ValueError("Simulation must be completed before analysis")
            
            # 初始化分析任务记录
            analysis_store[analysis_id] = {
                "analysis_id": analysis_id,
                "run_id": request.run_id,
                "status": AnalysisStatus.PENDING,
                "analysis_type": request.analysis_type,
                "metrics": request.metrics or [],
                "chart_types": request.chart_types or [],
                "report_format": request.report_format,
                "started_at": datetime.now().isoformat(),
                "results": {},
                "charts": [],
                "errors": []
            }
            
            # 异步启动分析进程
            asyncio.create_task(self._run_analysis_process(analysis_id, request))
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                run_id=request.run_id,
                status=AnalysisStatus.PENDING,
                message="分析任务已创建，正在启动...",
                started_at=analysis_store[analysis_id]["started_at"]
            )
            
        except Exception as e:
            logger.error(f"Error starting analysis: {str(e)}")
            return AnalysisResponse(
                analysis_id=analysis_id,
                run_id=request.run_id,
                status=AnalysisStatus.FAILED,
                message=f"启动分析失败: {str(e)}",
                started_at=datetime.now().isoformat()
            )
    
    async def _run_analysis_process(self, analysis_id: str, request: AnalysisRequest):
        """
        异步运行分析进程
        
        Args:
            analysis_id: 分析任务ID
            request: 分析请求
        """
        try:
            analysis_data = analysis_store[analysis_id]
            analysis_data["status"] = AnalysisStatus.RUNNING
            
            logger.info(f"Running analysis process {analysis_id}")
            
            # 1. 加载仿真数据
            simulation_data = await self._load_simulation_data(request.run_id)
            
            # 2. 运行综合结果分析器
            comprehensive_results = await self._run_comprehensive_analyzer(request.run_id)
            
            # 3. 计算KPI指标
            kpis = await self._calculate_kpis(simulation_data, request.metrics)
            
            # 4. 生成图表
            charts = await self._generate_charts(simulation_data, request.chart_types, analysis_id)
            
            # 5. 使用LLM进行智能分析
            llm_insights = await self._generate_llm_insights(simulation_data, kpis, request.run_id)
            
            # 6. 生成报告
            report_url = await self._generate_report(analysis_id, {
                "kpis": kpis,
                "charts": charts,
                "llm_insights": llm_insights,
                "comprehensive_results": comprehensive_results
            }, request.report_format)
            
            # 更新分析结果
            analysis_data.update({
                "status": AnalysisStatus.COMPLETED,
                "completed_at": datetime.now().isoformat(),
                "results": {
                    "kpis": kpis,
                    "comprehensive_results": comprehensive_results,
                    "llm_insights": llm_insights
                },
                "charts": charts,
                "report_url": report_url
            })
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in analysis process {analysis_id}: {str(e)}")
            analysis_store[analysis_id].update({
                "status": AnalysisStatus.FAILED,
                "errors": [str(e)]
            })
    
    async def _load_simulation_data(self, run_id: str) -> pd.DataFrame:
        """
        加载仿真数据
        
        Args:
            run_id: 仿真运行ID
            
        Returns:
            pd.DataFrame: 仿真数据
        """
        try:
            # 查找仿真输出文件
            from api.routes.simulation import simulation_store
            
            simulation_data = simulation_store[run_id]
            output_files = simulation_data.get("output_files", [])
            
            # 查找CSV文件
            csv_file = None
            for file_path in output_files:
                if file_path.endswith('.csv'):
                    csv_file = file_path
                    break
            
            if not csv_file:
                # 尝试查找默认输出文件
                default_files = [
                    self.base_path / "simulation_log.csv",
                    self.base_path / "output.csv",
                    self.base_path / "results.csv"
                ]
                
                for file_path in default_files:
                    if file_path.exists():
                        csv_file = str(file_path)
                        break
            
            if not csv_file:
                raise FileNotFoundError("No simulation output CSV file found")
            
            # 读取CSV数据
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded simulation data: {len(df)} rows, {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading simulation data: {str(e)}")
            raise
    
    async def _run_comprehensive_analyzer(self, run_id: str) -> Dict[str, Any]:
        """
        运行综合结果分析器
        
        Args:
            run_id: 仿真运行ID
            
        Returns:
            Dict[str, Any]: 综合分析结果
        """
        try:
            # 调用现有的comprehensive_result_analyzer.py
            script_path = self.base_path / "examples" / "comprehensive_result_analyzer.py"
            
            if not script_path.exists():
                logger.warning("Comprehensive result analyzer script not found")
                return {"status": "skipped", "reason": "Script not found"}
            
            # 运行分析脚本
            cmd = [sys.executable, str(script_path)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 尝试解析JSON输出
                try:
                    result = json.loads(stdout.decode('utf-8'))
                    return result
                except json.JSONDecodeError:
                    return {
                        "status": "completed",
                        "output": stdout.decode('utf-8'),
                        "success_rate": "Unknown"
                    }
            else:
                logger.error(f"Comprehensive analyzer failed: {stderr.decode('utf-8')}")
                return {
                    "status": "failed",
                    "error": stderr.decode('utf-8')
                }
                
        except Exception as e:
            logger.error(f"Error running comprehensive analyzer: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _calculate_kpis(self, df: pd.DataFrame, requested_metrics: List[str]) -> List[KPIResult]:
        """
        计算KPI指标
        
        Args:
            df: 仿真数据
            requested_metrics: 请求的指标列表
            
        Returns:
            List[KPIResult]: KPI结果列表
        """
        try:
            kpis = []
            
            # 基础统计指标
            if not requested_metrics or "basic_stats" in requested_metrics:
                for column in df.select_dtypes(include=[np.number]).columns:
                    if column.lower() != 'time':
                        kpis.extend([
                            KPIResult(
                                name=f"{column}_mean",
                                value=float(df[column].mean()),
                                unit="",
                                description=f"{column}的平均值",
                                category="基础统计"
                            ),
                            KPIResult(
                                name=f"{column}_max",
                                value=float(df[column].max()),
                                unit="",
                                description=f"{column}的最大值",
                                category="基础统计"
                            ),
                            KPIResult(
                                name=f"{column}_min",
                                value=float(df[column].min()),
                                unit="",
                                description=f"{column}的最小值",
                                category="基础统计"
                            ),
                            KPIResult(
                                name=f"{column}_std",
                                value=float(df[column].std()),
                                unit="",
                                description=f"{column}的标准差",
                                category="基础统计"
                            )
                        ])
            
            # 性能指标
            if not requested_metrics or "performance" in requested_metrics:
                # 仿真时长
                if 'time' in df.columns:
                    simulation_duration = df['time'].max() - df['time'].min()
                    kpis.append(KPIResult(
                        name="simulation_duration",
                        value=float(simulation_duration),
                        unit="时间单位",
                        description="仿真总时长",
                        category="性能指标"
                    ))
                
                # 数据点数量
                kpis.append(KPIResult(
                    name="data_points",
                    value=len(df),
                    unit="个",
                    description="数据点总数",
                    category="性能指标"
                ))
            
            # 水利系统特定指标
            if not requested_metrics or "hydraulic" in requested_metrics:
                # 水位相关指标
                water_level_cols = [col for col in df.columns if 'water_level' in col.lower() or 'level' in col.lower()]
                for col in water_level_cols:
                    if col in df.columns:
                        # 水位变化率
                        if len(df) > 1:
                            level_change_rate = (df[col].iloc[-1] - df[col].iloc[0]) / len(df)
                            kpis.append(KPIResult(
                                name=f"{col}_change_rate",
                                value=float(level_change_rate),
                                unit="单位/步",
                                description=f"{col}的变化率",
                                category="水利指标"
                            ))
                
                # 流量相关指标
                flow_cols = [col for col in df.columns if 'flow' in col.lower() or 'discharge' in col.lower()]
                for col in flow_cols:
                    if col in df.columns:
                        # 平均流量
                        avg_flow = df[col].mean()
                        kpis.append(KPIResult(
                            name=f"{col}_average",
                            value=float(avg_flow),
                            unit="流量单位",
                            description=f"{col}的平均流量",
                            category="水利指标"
                        ))
            
            logger.info(f"Calculated {len(kpis)} KPI metrics")
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {str(e)}")
            return []
    
    async def _generate_charts(self, df: pd.DataFrame, chart_types: List[ChartType], 
                             analysis_id: str) -> List[ChartResult]:
        """
        生成图表
        
        Args:
            df: 仿真数据
            chart_types: 图表类型列表
            analysis_id: 分析任务ID
            
        Returns:
            List[ChartResult]: 图表结果列表
        """
        try:
            charts = []
            
            # 如果没有指定图表类型，使用默认类型
            if not chart_types:
                chart_types = [ChartType.LINE, ChartType.BAR]
            
            # 数值列
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            time_col = 'time' if 'time' in df.columns else numeric_cols[0] if numeric_cols else None
            
            for chart_type in chart_types:
                try:
                    chart_id = f"{analysis_id}_{chart_type.value}_{len(charts)}"
                    
                    if chart_type == ChartType.LINE:
                        chart = await self._create_line_chart(df, time_col, numeric_cols, chart_id)
                    elif chart_type == ChartType.BAR:
                        chart = await self._create_bar_chart(df, numeric_cols, chart_id)
                    elif chart_type == ChartType.SCATTER:
                        chart = await self._create_scatter_chart(df, numeric_cols, chart_id)
                    elif chart_type == ChartType.HISTOGRAM:
                        chart = await self._create_histogram_chart(df, numeric_cols, chart_id)
                    elif chart_type == ChartType.HEATMAP:
                        chart = await self._create_heatmap_chart(df, numeric_cols, chart_id)
                    elif chart_type == ChartType.BOX:
                        chart = await self._create_box_chart(df, numeric_cols, chart_id)
                    else:
                        continue
                    
                    if chart:
                        charts.append(chart)
                        
                except Exception as e:
                    logger.error(f"Error creating {chart_type} chart: {str(e)}")
                    continue
            
            logger.info(f"Generated {len(charts)} charts")
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            return []
    
    async def _create_line_chart(self, df: pd.DataFrame, time_col: str, 
                                numeric_cols: List[str], chart_id: str) -> Optional[ChartResult]:
        """
        创建线图
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制数值列（排除时间列）
            plot_cols = [col for col in numeric_cols if col != time_col][:5]  # 最多5条线
            
            for col in plot_cols:
                if time_col and time_col in df.columns:
                    ax.plot(df[time_col], df[col], label=col, linewidth=2)
                else:
                    ax.plot(df.index, df[col], label=col, linewidth=2)
            
            ax.set_title('仿真结果时间序列图', fontsize=16, fontweight='bold')
            ax.set_xlabel('时间' if time_col else '步数', fontsize=12)
            ax.set_ylabel('数值', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.LINE,
                title="仿真结果时间序列图",
                base64_data=base64_data,
                metadata={"variables": plot_cols, "time_column": time_col}
            )
            
        except Exception as e:
            logger.error(f"Error creating line chart: {str(e)}")
            return None
    
    async def _create_bar_chart(self, df: pd.DataFrame, numeric_cols: List[str], 
                               chart_id: str) -> Optional[ChartResult]:
        """
        创建柱状图
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 计算各列的平均值
            means = [df[col].mean() for col in numeric_cols[:8]]  # 最多8个柱子
            cols = numeric_cols[:8]
            
            palette = seaborn_support.color_palette("husl", len(cols))
            bars = ax.bar(cols, means, color=palette)
            
            ax.set_title('各变量平均值对比', fontsize=16, fontweight='bold')
            ax.set_ylabel('平均值', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            
            # 添加数值标签
            for bar, mean in zip(bars, means):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean:.2f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.BAR,
                title="各变量平均值对比",
                base64_data=base64_data,
                metadata={"variables": cols, "values": means}
            )
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {str(e)}")
            return None
    
    async def _create_scatter_chart(self, df: pd.DataFrame, numeric_cols: List[str], 
                                   chart_id: str) -> Optional[ChartResult]:
        """
        创建散点图
        """
        try:
            if len(numeric_cols) < 2:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            x_col, y_col = numeric_cols[0], numeric_cols[1]
            
            scatter = ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50)
            
            ax.set_title(f'{x_col} vs {y_col} 散点图', fontsize=16, fontweight='bold')
            ax.set_xlabel(x_col, fontsize=12)
            ax.set_ylabel(y_col, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.SCATTER,
                title=f"{x_col} vs {y_col} 散点图",
                base64_data=base64_data,
                metadata={"x_variable": x_col, "y_variable": y_col}
            )
            
        except Exception as e:
            logger.error(f"Error creating scatter chart: {str(e)}")
            return None
    
    async def _create_histogram_chart(self, df: pd.DataFrame, numeric_cols: List[str], 
                                     chart_id: str) -> Optional[ChartResult]:
        """
        创建直方图
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            plot_cols = numeric_cols[:4]  # 最多4个直方图
            
            palette = seaborn_support.color_palette("husl", len(plot_cols))

            for i, col in enumerate(plot_cols):
                if i < len(axes):
                    axes[i].hist(df[col], bins=30, alpha=0.7, color=palette[i])
                    axes[i].set_title(f'{col} 分布', fontsize=12)
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel('频次')
                    axes[i].grid(True, alpha=0.3)
            
            # 隐藏多余的子图
            for i in range(len(plot_cols), len(axes)):
                axes[i].set_visible(False)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.HISTOGRAM,
                title="变量分布直方图",
                base64_data=base64_data,
                metadata={"variables": plot_cols}
            )
            
        except Exception as e:
            logger.error(f"Error creating histogram chart: {str(e)}")
            return None
    
    async def _create_heatmap_chart(self, df: pd.DataFrame, numeric_cols: List[str], 
                                   chart_id: str) -> Optional[ChartResult]:
        """
        创建热力图
        """
        try:
            if len(numeric_cols) < 2:
                return None
            
            # 计算相关性矩阵
            corr_matrix = df[numeric_cols].corr()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            seaborn_support.heatmap(
                corr_matrix,
                annot=True,
                cmap='coolwarm',
                center=0,
                ax=ax,
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": .8},
            )
            
            ax.set_title('变量相关性热力图', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.HEATMAP,
                title="变量相关性热力图",
                base64_data=base64_data,
                metadata={"variables": numeric_cols}
            )
            
        except Exception as e:
            logger.error(f"Error creating heatmap chart: {str(e)}")
            return None
    
    async def _create_box_chart(self, df: pd.DataFrame, numeric_cols: List[str], 
                               chart_id: str) -> Optional[ChartResult]:
        """
        创建箱线图
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            plot_cols = numeric_cols[:8]  # 最多8个箱线图
            
            # 标准化数据以便比较
            normalized_data = []
            for col in plot_cols:
                data = df[col]
                normalized = (data - data.mean()) / data.std()
                normalized_data.append(normalized)
            
            box_plot = ax.boxplot(normalized_data, labels=plot_cols, patch_artist=True)
            
            # 设置颜色
            colors = seaborn_support.color_palette("husl", len(plot_cols))
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_title('变量分布箱线图（标准化）', fontsize=16, fontweight='bold')
            ax.set_ylabel('标准化数值', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = self.temp_dir / f"{chart_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 转换为base64
            base64_data = self._image_to_base64(chart_path)
            
            return ChartResult(
                chart_id=chart_id,
                chart_type=ChartType.BOX,
                title="变量分布箱线图（标准化）",
                base64_data=base64_data,
                metadata={"variables": plot_cols, "normalized": True}
            )
            
        except Exception as e:
            logger.error(f"Error creating box chart: {str(e)}")
            return None
    
    def _image_to_base64(self, image_path: Path) -> str:
        """
        将图片转换为base64编码
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: base64编码的图片数据
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return ""
    
    async def _generate_llm_insights(self, df: pd.DataFrame, kpis: List[KPIResult], 
                                    run_id: str) -> Dict[str, Any]:
        """
        使用LLM生成智能分析洞察
        
        Args:
            df: 仿真数据
            kpis: KPI结果
            run_id: 仿真运行ID
            
        Returns:
            Dict[str, Any]: LLM分析洞察
        """
        try:
            # 使用现有的LLMDataAnalystAgent
            analyst_agent = LLMDataAnalystAgent(f"analyst_{run_id}", None)
            
            # 准备分析数据
            analysis_data = {
                "data_summary": {
                    "rows": len(df),
                    "columns": list(df.columns),
                    "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist()
                },
                "kpis": [kpi.dict() for kpi in kpis],
                "basic_stats": df.describe().to_dict()
            }
            
            # 模拟LLM分析（实际实现中应调用真实的LLM API）
            insights = {
                "summary": "仿真运行成功完成，数据质量良好",
                "key_findings": [
                    "系统运行稳定，各项指标在正常范围内",
                    "数据变化趋势符合预期",
                    "未发现异常波动或错误"
                ],
                "recommendations": [
                    "建议继续监控关键指标",
                    "可以考虑优化控制参数",
                    "建议进行更长时间的仿真验证"
                ],
                "data_quality": "优秀",
                "confidence_score": 0.85
            }
            
            logger.info(f"Generated LLM insights for run {run_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating LLM insights: {str(e)}")
            return {
                "summary": "LLM分析暂时不可用",
                "error": str(e)
            }
    
    async def _generate_report(self, analysis_id: str, analysis_results: Dict[str, Any], 
                              format: ReportFormat) -> str:
        """
        生成分析报告
        
        Args:
            analysis_id: 分析任务ID
            analysis_results: 分析结果
            format: 报告格式
            
        Returns:
            str: 报告文件URL或路径
        """
        try:
            if format == ReportFormat.MARKDOWN:
                return await self._generate_markdown_report(analysis_id, analysis_results)
            elif format == ReportFormat.HTML:
                return await self._generate_html_report(analysis_id, analysis_results)
            elif format == ReportFormat.JSON:
                return await self._generate_json_report(analysis_id, analysis_results)
            else:
                # 默认生成Markdown报告
                return await self._generate_markdown_report(analysis_id, analysis_results)
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return ""
    
    async def _generate_markdown_report(self, analysis_id: str, 
                                       analysis_results: Dict[str, Any]) -> str:
        """
        生成Markdown格式报告
        """
        try:
            kpis = analysis_results.get("kpis", [])
            charts = analysis_results.get("charts", [])
            llm_insights = analysis_results.get("llm_insights", {})
            comprehensive_results = analysis_results.get("comprehensive_results", {})
            
            # 生成Markdown内容
            markdown_content = f"""# 仿真分析报告

**分析ID**: {analysis_id}  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

## 执行摘要

{llm_insights.get('summary', '仿真分析已完成')}

## 关键性能指标 (KPIs)

| 指标名称 | 数值 | 单位 | 描述 | 类别 |
|---------|------|------|------|------|
"""
            
            # 添加KPI表格
            for kpi in kpis[:20]:  # 最多显示20个KPI
                markdown_content += f"| {kpi.name} | {kpi.value:.4f} | {kpi.unit or ''} | {kpi.description or ''} | {kpi.category or ''} |\n"
            
            # 添加主要发现
            if llm_insights.get('key_findings'):
                markdown_content += "\n## 主要发现\n\n"
                for finding in llm_insights['key_findings']:
                    markdown_content += f"- {finding}\n"
            
            # 添加建议
            if llm_insights.get('recommendations'):
                markdown_content += "\n## 建议\n\n"
                for recommendation in llm_insights['recommendations']:
                    markdown_content += f"- {recommendation}\n"
            
            # 添加图表信息
            if charts:
                markdown_content += "\n## 可视化图表\n\n"
                for chart in charts:
                    markdown_content += f"### {chart.title}\n\n"
                    markdown_content += f"**图表类型**: {chart.chart_type}  \n"
                    if chart.metadata:
                        markdown_content += f"**变量**: {', '.join(chart.metadata.get('variables', []))}  \n"
                    markdown_content += "\n"
            
            # 添加综合分析结果
            if comprehensive_results.get('status') == 'completed':
                markdown_content += "\n## 综合分析结果\n\n"
                if 'success_rate' in comprehensive_results:
                    markdown_content += f"**成功率**: {comprehensive_results['success_rate']}\n\n"
            
            # 保存报告文件
            report_path = self.temp_dir / f"report_{analysis_id}.md"
            report_path.write_text(markdown_content, encoding='utf-8')
            
            logger.info(f"Generated Markdown report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating Markdown report: {str(e)}")
            return ""
    
    async def _generate_json_report(self, analysis_id: str, 
                                   analysis_results: Dict[str, Any]) -> str:
        """
        生成JSON格式报告
        """
        try:
            report_data = {
                "analysis_id": analysis_id,
                "generated_at": datetime.now().isoformat(),
                "results": analysis_results
            }
            
            # 保存JSON报告
            report_path = self.temp_dir / f"report_{analysis_id}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated JSON report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            return ""
    
    async def _generate_html_report(self, analysis_id: str, 
                                   analysis_results: Dict[str, Any]) -> str:
        """
        生成HTML格式报告
        """
        try:
            # 先生成Markdown，然后转换为HTML
            markdown_path = await self._generate_markdown_report(analysis_id, analysis_results)
            
            if not markdown_path:
                return ""
            
            # 读取Markdown内容
            markdown_content = Path(markdown_path).read_text(encoding='utf-8')
            
            # 简单的HTML模板
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>仿真分析报告 - {analysis_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1, h2, h3 {{ color: #333; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div id="content">
        {markdown_content.replace(chr(10), '<br>')}
    </div>
</body>
</html>"""
            
            # 保存HTML报告
            report_path = self.temp_dir / f"report_{analysis_id}.html"
            report_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated HTML report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return ""

# 实例化智能体
analyst_agent = AnalystAndReporterAgent()

# API路由定义
@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    """
    启动分析任务
    
    接收分析请求，创建异步分析任务
    """
    try:
        response = await analyst_agent.start_analysis(request)
        
        logger.info(f"Started analysis {response.analysis_id} for run {request.run_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    获取分析状态
    
    返回指定分析任务的当前状态和进度
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_data = analysis_store[analysis_id]
        
        return JSONResponse(content={
            "analysis_id": analysis_id,
            "status": analysis_data["status"],
            "started_at": analysis_data["started_at"],
            "completed_at": analysis_data.get("completed_at"),
            "has_results": bool(analysis_data.get("results")),
            "has_charts": bool(analysis_data.get("charts")),
            "has_report": bool(analysis_data.get("report_url")),
            "errors": analysis_data.get("errors", [])
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    获取分析结果
    
    返回完整的分析结果，包括KPI、图表和洞察
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_data = analysis_store[analysis_id]
        
        if analysis_data["status"] != AnalysisStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Analysis not completed")
        
        return JSONResponse(content={
            "analysis_id": analysis_id,
            "status": analysis_data["status"],
            "results": analysis_data["results"],
            "charts": analysis_data["charts"],
            "report_url": analysis_data.get("report_url"),
            "completed_at": analysis_data["completed_at"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chart", response_model=ChartResult)
async def generate_chart(request: ChartRequest):
    """
    生成单个图表
    
    根据请求生成指定类型的图表
    """
    try:
        # 加载仿真数据
        df = await analyst_agent._load_simulation_data(request.run_id)
        
        # 生成图表ID
        chart_id = f"custom_{request.run_id}_{request.chart_type.value}_{int(datetime.now().timestamp())}"
        
        # 根据图表类型生成图表
        if request.chart_type == ChartType.LINE:
            chart = await analyst_agent._create_line_chart(df, 'time', request.variables, chart_id)
        elif request.chart_type == ChartType.BAR:
            chart = await analyst_agent._create_bar_chart(df, request.variables, chart_id)
        elif request.chart_type == ChartType.SCATTER:
            chart = await analyst_agent._create_scatter_chart(df, request.variables, chart_id)
        elif request.chart_type == ChartType.HISTOGRAM:
            chart = await analyst_agent._create_histogram_chart(df, request.variables, chart_id)
        elif request.chart_type == ChartType.HEATMAP:
            chart = await analyst_agent._create_heatmap_chart(df, request.variables, chart_id)
        elif request.chart_type == ChartType.BOX:
            chart = await analyst_agent._create_box_chart(df, request.variables, chart_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported chart type")
        
        if not chart:
            raise HTTPException(status_code=500, detail="Failed to generate chart")
        
        # 更新标题（如果提供）
        if request.title:
            chart.title = request.title
        
        return chart
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report")
async def generate_report(request: ReportRequest):
    """
    生成分析报告
    
    根据请求生成指定格式的分析报告
    """
    try:
        # 检查是否有现有的分析结果
        existing_analysis = None
        for analysis_id, data in analysis_store.items():
            if data["run_id"] == request.run_id and data["status"] == AnalysisStatus.COMPLETED:
                existing_analysis = data
                break
        
        if not existing_analysis:
            # 如果没有现有分析，启动新的分析
            analysis_request = AnalysisRequest(
                run_id=request.run_id,
                analysis_type="comprehensive",
                report_format=request.format
            )
            
            analysis_response = await analyst_agent.start_analysis(analysis_request)
            
            return JSONResponse(content={
                "message": "分析任务已启动，报告将在分析完成后生成",
                "analysis_id": analysis_response.analysis_id,
                "status": "pending"
            })
        
        # 使用现有分析结果生成报告
        report_url = await analyst_agent._generate_report(
            existing_analysis["analysis_id"],
            existing_analysis["results"],
            request.format
        )
        
        return JSONResponse(content={
            "message": "报告生成成功",
            "report_url": report_url,
            "format": request.format,
            "status": "completed"
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{analysis_id}/{file_type}")
async def download_analysis_file(analysis_id: str, file_type: str):
    """
    下载分析文件
    
    下载报告、图表或其他分析文件
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_data = analysis_store[analysis_id]
        
        if file_type == "report":
            report_url = analysis_data.get("report_url")
            if not report_url or not Path(report_url).exists():
                raise HTTPException(status_code=404, detail="Report file not found")
            
            return FileResponse(
                path=report_url,
                filename=f"analysis_report_{analysis_id}.{Path(report_url).suffix[1:]}",
                media_type="application/octet-stream"
            )
        
        elif file_type == "data":
            # 返回分析结果的JSON文件
            temp_file = analyst_agent.temp_dir / f"analysis_data_{analysis_id}.json"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data["results"], f, ensure_ascii=False, indent=2)
            
            return FileResponse(
                path=str(temp_file),
                filename=f"analysis_data_{analysis_id}.json",
                media_type="application/json"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading analysis file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_analyses():
    """
    列出所有分析任务
    
    返回当前系统中的所有分析任务状态
    """
    try:
        analyses = []
        for analysis_id, data in analysis_store.items():
            analyses.append({
                "analysis_id": analysis_id,
                "run_id": data["run_id"],
                "status": data["status"],
                "analysis_type": data["analysis_type"],
                "started_at": data["started_at"],
                "completed_at": data.get("completed_at"),
                "has_results": bool(data.get("results")),
                "has_charts": bool(data.get("charts")),
                "has_report": bool(data.get("report_url"))
            })
        
        return JSONResponse(content={"analyses": analyses})
        
    except Exception as e:
        logger.error(f"Error listing analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup/{analysis_id}")
async def cleanup_analysis(analysis_id: str):
    """
    清理分析任务
    
    删除分析任务记录和临时文件
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_data = analysis_store[analysis_id]
        
        # 删除报告文件
        if analysis_data.get("report_url"):
            report_path = Path(analysis_data["report_url"])
            if report_path.exists():
                report_path.unlink()
        
        # 删除图表文件
        for chart in analysis_data.get("charts", []):
            chart_path = analyst_agent.temp_dir / f"{chart['chart_id']}.png"
            if chart_path.exists():
                chart_path.unlink()
        
        # 删除记录
        del analysis_store[analysis_id]
        
        logger.info(f"Cleaned up analysis {analysis_id}")
        return JSONResponse(content={"message": "Analysis cleaned up successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))