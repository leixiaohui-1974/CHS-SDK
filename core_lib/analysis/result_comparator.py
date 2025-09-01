#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台结果对比分析工具
提供仿真结果的对比、分析和可视化功能
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from sqlalchemy.orm import Session
from api.database.database import get_db
from api.database import models

# 配置日志
logger = logging.getLogger(__name__)

class ComparisonType(Enum):
    """对比类型枚举"""
    STATISTICAL = "statistical"  # 统计对比
    TREND = "trend"  # 趋势对比
    DISTRIBUTION = "distribution"  # 分布对比
    CORRELATION = "correlation"  # 相关性对比
    PERFORMANCE = "performance"  # 性能对比
    SENSITIVITY = "sensitivity"  # 敏感性对比

class MetricType(Enum):
    """指标类型枚举"""
    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    MIN = "min"
    MAX = "max"
    PERCENTILE_25 = "p25"
    PERCENTILE_75 = "p75"
    RANGE = "range"
    VARIANCE = "variance"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"

@dataclass
class ComparisonResult:
    """对比结果数据类"""
    comparison_id: str
    comparison_type: ComparisonType
    result_ids: List[str]
    metrics: Dict[str, Any]
    statistical_tests: Dict[str, Any]
    visualizations: Dict[str, Any]
    summary: str
    created_at: datetime
    confidence_level: float = 0.95

@dataclass
class SimulationResultData:
    """仿真结果数据类"""
    result_id: str
    name: str
    parameters: Dict[str, Any]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any]
    execution_time: float
    created_at: datetime

class ResultComparator:
    """
    仿真结果对比分析器
    
    提供多种仿真结果对比分析功能：
    - 统计对比分析
    - 趋势对比分析
    - 分布对比分析
    - 相关性分析
    - 性能对比分析
    - 敏感性分析
    - 可视化生成
    """
    
    def __init__(self):
        """
        初始化结果对比分析器
        """
        self.scaler = StandardScaler()
        self.pca = PCA()
        self.kmeans = KMeans()
        
        logger.info("仿真结果对比分析器初始化完成")
    
    async def compare_results(
        self,
        result_ids: List[str],
        comparison_type: ComparisonType,
        target_variables: List[str] = None,
        confidence_level: float = 0.95,
        user_id: str = None
    ) -> ComparisonResult:
        """
        对比仿真结果
        
        Args:
            result_ids: 结果ID列表
            comparison_type: 对比类型
            target_variables: 目标变量列表
            confidence_level: 置信水平
            user_id: 用户ID
        
        Returns:
            ComparisonResult: 对比结果
        """
        try:
            logger.info(f"开始对比仿真结果，类型: {comparison_type.value}，结果数量: {len(result_ids)}")
            
            # 加载仿真结果数据
            result_data = await self._load_simulation_results(result_ids)
            
            if len(result_data) < 2:
                raise ValueError("至少需要2个仿真结果进行对比")
            
            # 数据预处理
            processed_data = await self._preprocess_data(result_data, target_variables)
            
            # 执行对比分析
            comparison_result = await self._perform_comparison(
                processed_data,
                comparison_type,
                confidence_level
            )
            
            # 保存对比结果
            await self._save_comparison_result(comparison_result, user_id)
            
            logger.info(f"仿真结果对比完成，对比ID: {comparison_result.comparison_id}")
            return comparison_result
            
        except Exception as e:
            logger.error(f"仿真结果对比失败: {str(e)}")
            raise
    
    async def statistical_comparison(
        self,
        result_data: List[SimulationResultData],
        target_variables: List[str],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        统计对比分析
        
        Args:
            result_data: 仿真结果数据列表
            target_variables: 目标变量列表
            confidence_level: 置信水平
        
        Returns:
            Dict[str, Any]: 统计对比结果
        """
        try:
            statistical_results = {}
            
            for variable in target_variables:
                # 提取变量数据
                variable_data = []
                for result in result_data:
                    if variable in result.outputs:
                        value = result.outputs[variable]
                        if isinstance(value, (int, float)):
                            variable_data.append(value)
                        elif isinstance(value, list):
                            variable_data.extend(value)
                
                if len(variable_data) < 2:
                    continue
                
                # 基本统计量
                basic_stats = {
                    "count": len(variable_data),
                    "mean": np.mean(variable_data),
                    "median": np.median(variable_data),
                    "std": np.std(variable_data),
                    "min": np.min(variable_data),
                    "max": np.max(variable_data),
                    "range": np.max(variable_data) - np.min(variable_data),
                    "variance": np.var(variable_data),
                    "skewness": stats.skew(variable_data),
                    "kurtosis": stats.kurtosis(variable_data),
                    "percentile_25": np.percentile(variable_data, 25),
                    "percentile_75": np.percentile(variable_data, 75)
                }
                
                # 置信区间
                confidence_interval = stats.t.interval(
                    confidence_level,
                    len(variable_data) - 1,
                    loc=np.mean(variable_data),
                    scale=stats.sem(variable_data)
                )
                
                # 正态性检验
                normality_test = stats.shapiro(variable_data)
                
                # 异常值检测
                q1 = np.percentile(variable_data, 25)
                q3 = np.percentile(variable_data, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = [x for x in variable_data if x < lower_bound or x > upper_bound]
                
                statistical_results[variable] = {
                    "basic_statistics": basic_stats,
                    "confidence_interval": {
                        "lower": confidence_interval[0],
                        "upper": confidence_interval[1],
                        "level": confidence_level
                    },
                    "normality_test": {
                        "statistic": normality_test.statistic,
                        "p_value": normality_test.pvalue,
                        "is_normal": normality_test.pvalue > 0.05
                    },
                    "outliers": {
                        "count": len(outliers),
                        "values": outliers,
                        "percentage": len(outliers) / len(variable_data) * 100
                    }
                }
            
            return statistical_results
            
        except Exception as e:
            logger.error(f"统计对比分析失败: {str(e)}")
            raise
    
    async def trend_comparison(
        self,
        result_data: List[SimulationResultData],
        target_variables: List[str],
        time_variable: str = "time"
    ) -> Dict[str, Any]:
        """
        趋势对比分析
        
        Args:
            result_data: 仿真结果数据列表
            target_variables: 目标变量列表
            time_variable: 时间变量名
        
        Returns:
            Dict[str, Any]: 趋势对比结果
        """
        try:
            trend_results = {}
            
            for variable in target_variables:
                # 提取时间序列数据
                time_series_data = []
                
                for result in result_data:
                    if variable in result.outputs and time_variable in result.outputs:
                        time_values = result.outputs[time_variable]
                        variable_values = result.outputs[variable]
                        
                        if len(time_values) == len(variable_values):
                            time_series_data.append({
                                "result_id": result.result_id,
                                "name": result.name,
                                "time": time_values,
                                "values": variable_values
                            })
                
                if len(time_series_data) < 2:
                    continue
                
                # 趋势分析
                trend_analysis = []
                
                for ts_data in time_series_data:
                    time_vals = np.array(ts_data["time"])
                    variable_vals = np.array(ts_data["values"])
                    
                    # 线性趋势
                    slope, intercept, r_value, p_value, std_err = stats.linregress(time_vals, variable_vals)
                    
                    # 趋势强度
                    trend_strength = abs(r_value)
                    trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                    
                    # 变化率
                    change_rate = (variable_vals[-1] - variable_vals[0]) / variable_vals[0] * 100 if variable_vals[0] != 0 else 0
                    
                    trend_analysis.append({
                        "result_id": ts_data["result_id"],
                        "name": ts_data["name"],
                        "slope": slope,
                        "intercept": intercept,
                        "r_squared": r_value ** 2,
                        "p_value": p_value,
                        "trend_strength": trend_strength,
                        "trend_direction": trend_direction,
                        "change_rate_percent": change_rate,
                        "start_value": variable_vals[0],
                        "end_value": variable_vals[-1]
                    })
                
                # 趋势对比
                slopes = [analysis["slope"] for analysis in trend_analysis]
                r_squared_values = [analysis["r_squared"] for analysis in trend_analysis]
                
                trend_comparison_stats = {
                    "slope_statistics": {
                        "mean": np.mean(slopes),
                        "std": np.std(slopes),
                        "min": np.min(slopes),
                        "max": np.max(slopes)
                    },
                    "r_squared_statistics": {
                        "mean": np.mean(r_squared_values),
                        "std": np.std(r_squared_values),
                        "min": np.min(r_squared_values),
                        "max": np.max(r_squared_values)
                    },
                    "trend_consistency": np.std(slopes) / np.mean(np.abs(slopes)) if np.mean(np.abs(slopes)) > 0 else 0
                }
                
                trend_results[variable] = {
                    "individual_trends": trend_analysis,
                    "comparison_statistics": trend_comparison_stats
                }
            
            return trend_results
            
        except Exception as e:
            logger.error(f"趋势对比分析失败: {str(e)}")
            raise
    
    async def distribution_comparison(
        self,
        result_data: List[SimulationResultData],
        target_variables: List[str]
    ) -> Dict[str, Any]:
        """
        分布对比分析
        
        Args:
            result_data: 仿真结果数据列表
            target_variables: 目标变量列表
        
        Returns:
            Dict[str, Any]: 分布对比结果
        """
        try:
            distribution_results = {}
            
            for variable in target_variables:
                # 提取变量数据
                datasets = []
                
                for result in result_data:
                    if variable in result.outputs:
                        value = result.outputs[variable]
                        if isinstance(value, (int, float)):
                            datasets.append([value])
                        elif isinstance(value, list):
                            datasets.append(value)
                
                if len(datasets) < 2:
                    continue
                
                # 分布比较测试
                distribution_tests = {}
                
                # Kolmogorov-Smirnov测试（两样本）
                if len(datasets) == 2:
                    ks_statistic, ks_p_value = stats.ks_2samp(datasets[0], datasets[1])
                    distribution_tests["kolmogorov_smirnov"] = {
                        "statistic": ks_statistic,
                        "p_value": ks_p_value,
                        "significant_difference": ks_p_value < 0.05
                    }
                    
                    # Mann-Whitney U测试
                    mw_statistic, mw_p_value = stats.mannwhitneyu(datasets[0], datasets[1])
                    distribution_tests["mann_whitney_u"] = {
                        "statistic": mw_statistic,
                        "p_value": mw_p_value,
                        "significant_difference": mw_p_value < 0.05
                    }
                
                # Kruskal-Wallis测试（多样本）
                if len(datasets) > 2:
                    kw_statistic, kw_p_value = stats.kruskal(*datasets)
                    distribution_tests["kruskal_wallis"] = {
                        "statistic": kw_statistic,
                        "p_value": kw_p_value,
                        "significant_difference": kw_p_value < 0.05
                    }
                
                # 分布特征比较
                distribution_features = []
                
                for i, dataset in enumerate(datasets):
                    features = {
                        "result_index": i,
                        "result_id": result_data[i].result_id,
                        "name": result_data[i].name,
                        "mean": np.mean(dataset),
                        "median": np.median(dataset),
                        "std": np.std(dataset),
                        "skewness": stats.skew(dataset),
                        "kurtosis": stats.kurtosis(dataset),
                        "min": np.min(dataset),
                        "max": np.max(dataset)
                    }
                    distribution_features.append(features)
                
                # 分布相似性度量
                similarity_matrix = np.zeros((len(datasets), len(datasets)))
                
                for i in range(len(datasets)):
                    for j in range(len(datasets)):
                        if i != j:
                            # 使用Wasserstein距离度量分布相似性
                            similarity_matrix[i][j] = stats.wasserstein_distance(datasets[i], datasets[j])
                
                distribution_results[variable] = {
                    "distribution_tests": distribution_tests,
                    "distribution_features": distribution_features,
                    "similarity_matrix": similarity_matrix.tolist(),
                    "average_similarity": np.mean(similarity_matrix[similarity_matrix > 0])
                }
            
            return distribution_results
            
        except Exception as e:
            logger.error(f"分布对比分析失败: {str(e)}")
            raise
    
    async def correlation_analysis(
        self,
        result_data: List[SimulationResultData],
        target_variables: List[str]
    ) -> Dict[str, Any]:
        """
        相关性分析
        
        Args:
            result_data: 仿真结果数据列表
            target_variables: 目标变量列表
        
        Returns:
            Dict[str, Any]: 相关性分析结果
        """
        try:
            # 构建数据矩阵
            data_matrix = []
            variable_names = []
            
            for result in result_data:
                row = []
                for variable in target_variables:
                    if variable in result.outputs:
                        value = result.outputs[variable]
                        if isinstance(value, (int, float)):
                            row.append(value)
                        elif isinstance(value, list) and len(value) > 0:
                            row.append(np.mean(value))  # 使用均值代表列表值
                        else:
                            row.append(np.nan)
                    else:
                        row.append(np.nan)
                
                if not all(np.isnan(x) for x in row):
                    data_matrix.append(row)
                    variable_names.append(result.name)
            
            if len(data_matrix) < 2:
                return {"error": "数据不足，无法进行相关性分析"}
            
            # 转换为DataFrame
            df = pd.DataFrame(data_matrix, columns=target_variables, index=variable_names)
            
            # 删除全为NaN的列
            df = df.dropna(axis=1, how='all')
            
            if df.empty:
                return {"error": "没有有效数据进行相关性分析"}
            
            # Pearson相关系数
            pearson_corr = df.corr(method='pearson')
            
            # Spearman相关系数
            spearman_corr = df.corr(method='spearman')
            
            # 相关性显著性检验
            correlation_tests = {}
            variables = df.columns.tolist()
            
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    var1, var2 = variables[i], variables[j]
                    
                    # 去除NaN值
                    data1 = df[var1].dropna()
                    data2 = df[var2].dropna()
                    
                    if len(data1) > 2 and len(data2) > 2:
                        # Pearson相关性检验
                        pearson_r, pearson_p = stats.pearsonr(data1, data2)
                        
                        # Spearman相关性检验
                        spearman_r, spearman_p = stats.spearmanr(data1, data2)
                        
                        correlation_tests[f"{var1}_vs_{var2}"] = {
                            "pearson": {
                                "correlation": pearson_r,
                                "p_value": pearson_p,
                                "significant": pearson_p < 0.05
                            },
                            "spearman": {
                                "correlation": spearman_r,
                                "p_value": spearman_p,
                                "significant": spearman_p < 0.05
                            }
                        }
            
            # 主成分分析
            pca_results = None
            if df.shape[1] > 2:  # 至少需要3个变量
                # 标准化数据
                scaled_data = self.scaler.fit_transform(df.fillna(df.mean()))
                
                # PCA分析
                pca_transformed = self.pca.fit_transform(scaled_data)
                
                pca_results = {
                    "explained_variance_ratio": self.pca.explained_variance_ratio_.tolist(),
                    "cumulative_variance_ratio": np.cumsum(self.pca.explained_variance_ratio_).tolist(),
                    "components": self.pca.components_.tolist(),
                    "n_components": self.pca.n_components_
                }
            
            return {
                "pearson_correlation_matrix": pearson_corr.to_dict(),
                "spearman_correlation_matrix": spearman_corr.to_dict(),
                "correlation_tests": correlation_tests,
                "pca_analysis": pca_results,
                "data_summary": {
                    "n_samples": len(df),
                    "n_variables": len(df.columns),
                    "missing_data_percentage": (df.isnull().sum() / len(df) * 100).to_dict()
                }
            }
            
        except Exception as e:
            logger.error(f"相关性分析失败: {str(e)}")
            raise
    
    async def performance_comparison(
        self,
        result_data: List[SimulationResultData],
        performance_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """
        性能对比分析
        
        Args:
            result_data: 仿真结果数据列表
            performance_metrics: 性能指标列表
        
        Returns:
            Dict[str, Any]: 性能对比结果
        """
        try:
            if performance_metrics is None:
                performance_metrics = ["execution_time", "memory_usage", "cpu_usage"]
            
            performance_results = {}
            
            # 执行时间对比
            execution_times = [result.execution_time for result in result_data if result.execution_time is not None]
            
            if execution_times:
                performance_results["execution_time"] = {
                    "values": execution_times,
                    "mean": np.mean(execution_times),
                    "std": np.std(execution_times),
                    "min": np.min(execution_times),
                    "max": np.max(execution_times),
                    "fastest_result": result_data[np.argmin(execution_times)].result_id,
                    "slowest_result": result_data[np.argmax(execution_times)].result_id,
                    "speedup_ratio": np.max(execution_times) / np.min(execution_times) if np.min(execution_times) > 0 else 0
                }
            
            # 其他性能指标对比
            for metric in performance_metrics:
                if metric == "execution_time":
                    continue  # 已经处理过
                
                metric_values = []
                for result in result_data:
                    if metric in result.metadata:
                        value = result.metadata[metric]
                        if isinstance(value, (int, float)):
                            metric_values.append(value)
                
                if metric_values:
                    performance_results[metric] = {
                        "values": metric_values,
                        "mean": np.mean(metric_values),
                        "std": np.std(metric_values),
                        "min": np.min(metric_values),
                        "max": np.max(metric_values),
                        "best_result": result_data[np.argmin(metric_values)].result_id,
                        "worst_result": result_data[np.argmax(metric_values)].result_id
                    }
            
            # 综合性能评分
            if len(performance_results) > 1:
                # 标准化各项指标并计算综合得分
                scores = []
                for result in result_data:
                    score = 0
                    count = 0
                    
                    for metric, metric_data in performance_results.items():
                        if metric in ["execution_time", "memory_usage", "cpu_usage"]:  # 越小越好的指标
                            normalized_score = 1 - (result.execution_time - metric_data["min"]) / (metric_data["max"] - metric_data["min"]) if metric_data["max"] != metric_data["min"] else 1
                        else:  # 越大越好的指标
                            normalized_score = (result.execution_time - metric_data["min"]) / (metric_data["max"] - metric_data["min"]) if metric_data["max"] != metric_data["min"] else 1
                        
                        score += normalized_score
                        count += 1
                    
                    scores.append(score / count if count > 0 else 0)
                
                performance_results["overall_performance"] = {
                    "scores": scores,
                    "best_result": result_data[np.argmax(scores)].result_id,
                    "worst_result": result_data[np.argmin(scores)].result_id,
                    "performance_ranking": sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
                }
            
            return performance_results
            
        except Exception as e:
            logger.error(f"性能对比分析失败: {str(e)}")
            raise
    
    async def sensitivity_analysis(
        self,
        result_data: List[SimulationResultData],
        input_parameters: List[str],
        output_variables: List[str]
    ) -> Dict[str, Any]:
        """
        敏感性分析
        
        Args:
            result_data: 仿真结果数据列表
            input_parameters: 输入参数列表
            output_variables: 输出变量列表
        
        Returns:
            Dict[str, Any]: 敏感性分析结果
        """
        try:
            sensitivity_results = {}
            
            # 构建输入输出数据矩阵
            input_matrix = []
            output_matrix = []
            
            for result in result_data:
                input_row = []
                output_row = []
                
                # 提取输入参数
                for param in input_parameters:
                    if param in result.parameters:
                        value = result.parameters[param]
                        if isinstance(value, (int, float)):
                            input_row.append(value)
                        else:
                            input_row.append(np.nan)
                    else:
                        input_row.append(np.nan)
                
                # 提取输出变量
                for var in output_variables:
                    if var in result.outputs:
                        value = result.outputs[var]
                        if isinstance(value, (int, float)):
                            output_row.append(value)
                        elif isinstance(value, list) and len(value) > 0:
                            output_row.append(np.mean(value))
                        else:
                            output_row.append(np.nan)
                    else:
                        output_row.append(np.nan)
                
                if not all(np.isnan(x) for x in input_row + output_row):
                    input_matrix.append(input_row)
                    output_matrix.append(output_row)
            
            if len(input_matrix) < 3:
                return {"error": "数据不足，无法进行敏感性分析"}
            
            # 转换为DataFrame
            input_df = pd.DataFrame(input_matrix, columns=input_parameters)
            output_df = pd.DataFrame(output_matrix, columns=output_variables)
            
            # 删除全为NaN的列
            input_df = input_df.dropna(axis=1, how='all')
            output_df = output_df.dropna(axis=1, how='all')
            
            # 计算敏感性指标
            for output_var in output_df.columns:
                output_values = output_df[output_var].dropna()
                
                if len(output_values) < 3:
                    continue
                
                var_sensitivity = {}
                
                for input_param in input_df.columns:
                    input_values = input_df[input_param].dropna()
                    
                    if len(input_values) < 3:
                        continue
                    
                    # 确保输入输出数据对应
                    common_indices = input_df[input_param].dropna().index.intersection(
                        output_df[output_var].dropna().index
                    )
                    
                    if len(common_indices) < 3:
                        continue
                    
                    x = input_df.loc[common_indices, input_param].values
                    y = output_df.loc[common_indices, output_var].values
                    
                    # 线性敏感性（斜率）
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    # 标准化敏感性
                    if np.std(x) > 0 and np.std(y) > 0:
                        normalized_sensitivity = slope * (np.std(x) / np.std(y))
                    else:
                        normalized_sensitivity = 0
                    
                    # 相关性敏感性
                    correlation, corr_p_value = stats.pearsonr(x, y)
                    
                    var_sensitivity[input_param] = {
                        "linear_sensitivity": slope,
                        "normalized_sensitivity": normalized_sensitivity,
                        "correlation": correlation,
                        "r_squared": r_value ** 2,
                        "p_value": p_value,
                        "significant": p_value < 0.05,
                        "sensitivity_rank": abs(normalized_sensitivity)
                    }
                
                # 排序敏感性
                sorted_sensitivity = sorted(
                    var_sensitivity.items(),
                    key=lambda x: x[1]["sensitivity_rank"],
                    reverse=True
                )
                
                sensitivity_results[output_var] = {
                    "parameter_sensitivity": var_sensitivity,
                    "sensitivity_ranking": [(param, data["sensitivity_rank"]) for param, data in sorted_sensitivity],
                    "most_sensitive_parameter": sorted_sensitivity[0][0] if sorted_sensitivity else None,
                    "least_sensitive_parameter": sorted_sensitivity[-1][0] if sorted_sensitivity else None
                }
            
            return sensitivity_results
            
        except Exception as e:
            logger.error(f"敏感性分析失败: {str(e)}")
            raise
    
    async def generate_comparison_report(
        self,
        comparison_result: ComparisonResult,
        include_visualizations: bool = True
    ) -> Dict[str, Any]:
        """
        生成对比分析报告
        
        Args:
            comparison_result: 对比结果
            include_visualizations: 是否包含可视化
        
        Returns:
            Dict[str, Any]: 对比报告
        """
        try:
            report = {
                "comparison_id": comparison_result.comparison_id,
                "comparison_type": comparison_result.comparison_type.value,
                "result_count": len(comparison_result.result_ids),
                "confidence_level": comparison_result.confidence_level,
                "created_at": comparison_result.created_at.isoformat(),
                "summary": comparison_result.summary,
                "metrics": comparison_result.metrics,
                "statistical_tests": comparison_result.statistical_tests
            }
            
            if include_visualizations:
                report["visualizations"] = comparison_result.visualizations
            
            # 生成结论和建议
            conclusions = await self._generate_conclusions(comparison_result)
            report["conclusions"] = conclusions
            
            return report
            
        except Exception as e:
            logger.error(f"生成对比报告失败: {str(e)}")
            raise
    
    # 辅助方法
    async def _load_simulation_results(self, result_ids: List[str]) -> List[SimulationResultData]:
        """
        加载仿真结果数据
        
        Args:
            result_ids: 结果ID列表
        
        Returns:
            List[SimulationResultData]: 仿真结果数据列表
        """
        try:
            db = next(get_db())
            result_data = []
            
            for result_id in result_ids:
                result_record = db.query(models.SimulationResult).filter(
                    models.SimulationResult.id == result_id
                ).first()
                
                if result_record:
                    # 解析结果数据
                    result_json = json.loads(result_record.result_data) if result_record.result_data else {}
                    
                    simulation_data = SimulationResultData(
                        result_id=result_id,
                        name=result_json.get("name", f"Result_{result_id[:8]}"),
                        parameters=result_json.get("parameters", {}),
                        outputs=result_json.get("outputs", {}),
                        metadata=result_json.get("metadata", {}),
                        execution_time=result_json.get("execution_time", 0.0),
                        created_at=result_record.created_at
                    )
                    
                    result_data.append(simulation_data)
            
            db.close()
            return result_data
            
        except Exception as e:
            logger.error(f"加载仿真结果数据失败: {str(e)}")
            raise
    
    async def _preprocess_data(
        self,
        result_data: List[SimulationResultData],
        target_variables: List[str] = None
    ) -> List[SimulationResultData]:
        """
        数据预处理
        
        Args:
            result_data: 原始结果数据
            target_variables: 目标变量列表
        
        Returns:
            List[SimulationResultData]: 预处理后的数据
        """
        # 这里可以添加数据清洗、标准化等预处理步骤
        return result_data
    
    async def _perform_comparison(
        self,
        result_data: List[SimulationResultData],
        comparison_type: ComparisonType,
        confidence_level: float
    ) -> ComparisonResult:
        """
        执行对比分析
        
        Args:
            result_data: 结果数据
            comparison_type: 对比类型
            confidence_level: 置信水平
        
        Returns:
            ComparisonResult: 对比结果
        """
        comparison_id = str(uuid.uuid4())
        result_ids = [data.result_id for data in result_data]
        
        # 根据对比类型执行相应分析
        if comparison_type == ComparisonType.STATISTICAL:
            metrics = await self.statistical_comparison(result_data, list(result_data[0].outputs.keys()), confidence_level)
        elif comparison_type == ComparisonType.TREND:
            metrics = await self.trend_comparison(result_data, list(result_data[0].outputs.keys()))
        elif comparison_type == ComparisonType.DISTRIBUTION:
            metrics = await self.distribution_comparison(result_data, list(result_data[0].outputs.keys()))
        elif comparison_type == ComparisonType.CORRELATION:
            metrics = await self.correlation_analysis(result_data, list(result_data[0].outputs.keys()))
        elif comparison_type == ComparisonType.PERFORMANCE:
            metrics = await self.performance_comparison(result_data)
        elif comparison_type == ComparisonType.SENSITIVITY:
            metrics = await self.sensitivity_analysis(
                result_data,
                list(result_data[0].parameters.keys()),
                list(result_data[0].outputs.keys())
            )
        else:
            metrics = {}
        
        return ComparisonResult(
            comparison_id=comparison_id,
            comparison_type=comparison_type,
            result_ids=result_ids,
            metrics=metrics,
            statistical_tests={},
            visualizations={},
            summary=f"{comparison_type.value}对比分析完成",
            created_at=datetime.utcnow(),
            confidence_level=confidence_level
        )
    
    async def _save_comparison_result(self, comparison_result: ComparisonResult, user_id: str = None):
        """
        保存对比结果
        
        Args:
            comparison_result: 对比结果
            user_id: 用户ID
        """
        try:
            db = next(get_db())
            
            comparison_record = models.ResultComparison(
                id=comparison_result.comparison_id,
                user_id=user_id,
                comparison_type=comparison_result.comparison_type.value,
                result_ids=json.dumps(comparison_result.result_ids),
                metrics=json.dumps(comparison_result.metrics),
                summary=comparison_result.summary,
                confidence_level=comparison_result.confidence_level,
                created_at=comparison_result.created_at
            )
            
            db.add(comparison_record)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"保存对比结果失败: {str(e)}")
    
    async def _generate_conclusions(self, comparison_result: ComparisonResult) -> List[str]:
        """
        生成结论和建议
        
        Args:
            comparison_result: 对比结果
        
        Returns:
            List[str]: 结论列表
        """
        conclusions = []
        
        # 根据对比类型生成相应结论
        if comparison_result.comparison_type == ComparisonType.STATISTICAL:
            conclusions.append("基于统计分析的结论...")
        elif comparison_result.comparison_type == ComparisonType.PERFORMANCE:
            conclusions.append("基于性能对比的结论...")
        # 添加更多结论生成逻辑
        
        return conclusions