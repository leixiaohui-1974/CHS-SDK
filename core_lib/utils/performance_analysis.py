#!/usr/bin/env python3
"""
性能分析工具 (Performance Analysis)

提供标准化的性能指标计算和分析功能，简化示例代码中的性能评估部分。

主要功能：
- 控制性能指标计算
- 系统稳定性分析
- 统计分析
- 频域分析
- 性能报告生成
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import logging
from scipy import signal, stats
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class ControlMetrics:
    """
    控制性能指标数据类
    """
    rmse: float
    mae: float
    steady_state_error: float
    settling_time: float
    overshoot: float
    rise_time: float
    integral_absolute_error: float
    integral_squared_error: float
    control_effort: float
    stability_margin: float

@dataclass
class SystemMetrics:
    """
    系统性能指标数据类
    """
    efficiency: float
    throughput: float
    response_time: float
    reliability: float
    robustness: float
    energy_consumption: float

@dataclass
class StatisticalMetrics:
    """
    统计性能指标数据类
    """
    mean: float
    std: float
    variance: float
    min_value: float
    max_value: float
    median: float
    skewness: float
    kurtosis: float
    percentile_95: float
    percentile_5: float

class PerformanceAnalyzer:
    """
    性能分析器
    
    提供全面的性能分析功能。
    """
    
    def __init__(self, time_step: float = 1.0):
        """
        初始化性能分析器
        
        Args:
            dt: 采样时间间隔
        """
        self.time_step= dt
        self.results = {}
        
        logger.info(f"性能分析器初始化完成 (time_step={dt})")
    
    def calculate_control_metrics(self, 
                                setpoint: Union[float, np.ndarray],
                                actual: np.ndarray,
                                control_signal: Optional[np.ndarray] = None,
                                time: Optional[np.ndarray] = None) -> ControlMetrics:
        """
        计算控制性能指标
        
        Args:
            setpoint: 设定值
            actual: 实际值
            control_signal: 控制信号
            time: 时间数组
            
        Returns:
            ControlMetrics: 控制性能指标
        """
        if time is None:
            time = np.arange(len(actual)) * self.dt
        
        # 处理设定值
        if isinstance(setpoint, (int, float)):
            setpoint_array = np.full_like(actual, setpoint)
        else:
            setpoint_array = np.array(setpoint)
        
        # 计算误差
        error = setpoint_array - actual
        
        # 基本指标
        rmse = np.sqrt(np.mean(error**2))
        mae = np.mean(np.abs(error))
        
        # 稳态误差 (最后10%的数据)
        steady_start = int(0.9 * len(error))
        steady_state_error = np.mean(np.abs(error[steady_start:]))
        
        # 阶跃响应特性
        settling_time = self._calculate_settling_time(actual, setpoint_array, time)
        overshoot = self._calculate_overshoot(actual, setpoint_array)
        rise_time = self._calculate_rise_time(actual, setpoint_array, time)
        
        # 积分指标
        iae = np.trapz(np.abs(error), time)
        ise = np.trapz(error**2, time)
        
        # 控制努力
        if control_signal is not None:
            control_effort = np.trapz(np.abs(np.diff(control_signal)), time[1:])
        else:
            control_effort = 0.0
        
        # 稳定性裕度 (简化计算)
        stability_margin = self._calculate_stability_margin(actual, time)
        
        metrics = ControlMetrics(
            rmse=rmse,
            mae=mae,
            steady_state_error=steady_state_error,
            settling_time=settling_time,
            overshoot=overshoot,
            rise_time=rise_time,
            integral_absolute_error=iae,
            integral_squared_error=ise,
            control_effort=control_effort,
            stability_margin=stability_margin
        )
        
        logger.info(f"控制性能指标计算完成: RMSE={rmse:.4f}, 稳态误差={steady_state_error:.4f}")
        return metrics
    
    def calculate_system_metrics(self, 
                               input_data: Dict[str, np.ndarray],
                               output_data: Dict[str, np.ndarray],
                               energy_data: Optional[np.ndarray] = None) -> SystemMetrics:
        """
        计算系统性能指标
        
        Args:
            input_data: 输入数据字典
            output_data: 输出数据字典
            energy_data: 能耗数据
            
        Returns:
            SystemMetrics: 系统性能指标
        """
        # 效率计算
        if 'input_power' in input_data and 'output_power' in output_data:
            efficiency = np.mean(output_data['output_power']) / np.mean(input_data['input_power'])
        else:
            efficiency = 1.0
        
        # 吞吐量计算
        if 'flow_rate' in output_data:
            throughput = np.mean(output_data['flow_rate'])
        else:
            throughput = 0.0
        
        # 响应时间计算
        response_time = self._calculate_response_time(input_data, output_data)
        
        # 可靠性计算 (基于输出稳定性)
        reliability = self._calculate_reliability(output_data)
        
        # 鲁棒性计算 (基于输出变异性)
        robustness = self._calculate_robustness(output_data)
        
        # 能耗计算
        if energy_data is not None:
            energy_consumption = np.trapz(energy_data, dx=self.dt)
        else:
            energy_consumption = 0.0
        
        metrics = SystemMetrics(
            efficiency=efficiency,
            throughput=throughput,
            response_time=response_time,
            reliability=reliability,
            robustness=robustness,
            energy_consumption=energy_consumption
        )
        
        logger.info(f"系统性能指标计算完成: 效率={efficiency:.4f}, 吞吐量={throughput:.4f}")
        return metrics
    
    def calculate_statistical_metrics(self, data: np.ndarray) -> StatisticalMetrics:
        """
        计算统计性能指标
        
        Args:
            data: 数据数组
            
        Returns:
            StatisticalMetrics: 统计性能指标
        """
        metrics = StatisticalMetrics(
            mean=np.mean(data),
            std=np.std(data),
            variance=np.var(data),
            min_value=np.min(data),
            max_value=np.max(data),
            median=np.median(data),
            skewness=stats.skew(data),
            kurtosis=stats.kurtosis(data),
            percentile_95=np.percentile(data, 95),
            percentile_5=np.percentile(data, 5)
        )
        
        logger.info(f"统计指标计算完成: 均值={metrics.mean:.4f}, 标准差={metrics.std:.4f}")
        return metrics
    
    def analyze_frequency_response(self, 
                                 input_signal: np.ndarray,
                                 output_signal: np.ndarray,
                                 nperseg: Optional[int] = None) -> Dict[str, Any]:
        """
        频域分析
        
        Args:
            input_signal: 输入信号
            output_signal: 输出信号
            nperseg: 每段长度
            
        Returns:
            Dict[str, Any]: 频域分析结果
        """
        if nperseg is None:
            nperseg = min(256, len(input_signal) // 4)
        
        # 计算功率谱密度
        f_in, psd_in = signal.welch(input_signal, fs=1/self.dt, nperseg=nperseg)
        f_out, psd_out = signal.welch(output_signal, fs=1/self.dt, nperseg=nperseg)
        
        # 计算传递函数
        f_tf, tf = signal.csd(input_signal, output_signal, fs=1/self.dt, nperseg=nperseg)
        f_auto, auto = signal.csd(input_signal, input_signal, fs=1/self.dt, nperseg=nperseg)
        
        transfer_function = tf / auto
        
        # 计算相干性
        f_coh, coherence = signal.coherence(input_signal, output_signal, 
                                          fs=1/self.dt, nperseg=nperseg)
        
        # 带宽计算
        magnitude = np.abs(transfer_function)
        bandwidth = self._calculate_bandwidth(f_tf, magnitude)
        
        # 相位裕度和增益裕度
        phase_margin, gain_margin = self._calculate_margins(f_tf, transfer_function)
        
        results = {
            'frequencies': f_tf,
            'transfer_function': transfer_function,
            'magnitude': magnitude,
            'phase': np.angle(transfer_function),
            'coherence': coherence,
            'input_psd': psd_in,
            'output_psd': psd_out,
            'bandwidth': bandwidth,
            'phase_margin': phase_margin,
            'gain_margin': gain_margin
        }
        
        logger.info(f"频域分析完成: 带宽={bandwidth:.4f} Hz, 相位裕度={phase_margin:.2f}°")
        return results
    
    def detect_oscillations(self, data: np.ndarray, 
                          threshold: float = 0.1) -> Dict[str, Any]:
        """
        检测振荡
        
        Args:
            data: 数据数组
            threshold: 振荡检测阈值
            
        Returns:
            Dict[str, Any]: 振荡检测结果
        """
        # 去趋势
        detrended = signal.detrend(data)
        
        # 计算自相关
        autocorr = np.correlate(detrended, detrended, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        autocorr = autocorr / autocorr[0]  # 归一化
        
        # 寻找峰值
        peaks, properties = signal.find_peaks(autocorr[1:], height=threshold)
        
        # 计算振荡频率
        if len(peaks) > 0:
            # 主要振荡周期
            main_period = (peaks[0] + 1) * self.dt
            oscillation_freq = 1 / main_period
            
            # 振荡强度
            oscillation_strength = autocorr[peaks[0] + 1]
        else:
            main_period = 0
            oscillation_freq = 0
            oscillation_strength = 0
        
        # 计算振荡指数
        oscillation_index = np.std(detrended) / (np.mean(np.abs(data)) + 1e-10)
        
        results = {
            'has_oscillation': len(peaks) > 0 and oscillation_strength > threshold,
            'oscillation_frequency': oscillation_freq,
            'oscillation_period': main_period,
            'oscillation_strength': oscillation_strength,
            'oscillation_index': oscillation_index,
            'autocorrelation': autocorr,
            'peaks': peaks
        }
        
        logger.info(f"振荡检测完成: 频率={oscillation_freq:.4f} Hz, 强度={oscillation_strength:.4f}")
        return results
    
    def calculate_stability_metrics(self, data: np.ndarray) -> Dict[str, float]:
        """
        计算稳定性指标
        
        Args:
            data: 数据数组
            
        Returns:
            Dict[str, float]: 稳定性指标
        """
        # 趋势分析
        time_index = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_index, data)
        
        # 变异系数
        cv = np.std(data) / (np.abs(np.mean(data)) + 1e-10)
        
        # 稳定性指数 (基于滑动窗口方差)
        window_size = min(50, len(data) // 10)
        rolling_var = pd.Series(data).rolling(window=window_size).var().dropna()
        stability_index = 1 / (1 + np.mean(rolling_var))
        
        # 单调性检查
        diff = np.diff(data)
        monotonic_increasing = np.all(diff >= 0)
        monotonic_decreasing = np.all(diff <= 0)
        
        # 收敛性检查
        final_portion = data[-int(0.1 * len(data)):]
        convergence_error = np.std(final_portion)
        
        metrics = {
            'trend_slope': slope,
            'trend_r_squared': r_value**2,
            'coefficient_of_variation': cv,
            'stability_index': stability_index,
            'is_monotonic_increasing': monotonic_increasing,
            'is_monotonic_decreasing': monotonic_decreasing,
            'convergence_error': convergence_error,
            'is_converged': convergence_error < 0.01 * np.abs(np.mean(data))
        }
        
        logger.info(f"稳定性分析完成: 稳定性指数={stability_index:.4f}, 收敛误差={convergence_error:.4f}")
        return metrics
    
    def generate_performance_report(self, 
                                  control_metrics: Optional[ControlMetrics] = None,
                                  system_metrics: Optional[SystemMetrics] = None,
                                  statistical_metrics: Optional[StatisticalMetrics] = None,
                                  frequency_analysis: Optional[Dict[str, Any]] = None,
                                  stability_metrics: Optional[Dict[str, float]] = None,
                                  save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成性能报告
        
        Args:
            control_metrics: 控制性能指标
            system_metrics: 系统性能指标
            statistical_metrics: 统计性能指标
            frequency_analysis: 频域分析结果
            stability_metrics: 稳定性指标
            save_path: 保存路径
            
        Returns:
            Dict[str, Any]: 完整性能报告
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'sampling_time': self.dt
        }
        
        if control_metrics:
            report['control_performance'] = {
                'rmse': control_metrics.rmse,
                'mae': control_metrics.mae,
                'steady_state_error': control_metrics.steady_state_error,
                'settling_time': control_metrics.settling_time,
                'overshoot': control_metrics.overshoot,
                'rise_time': control_metrics.rise_time,
                'iae': control_metrics.integral_absolute_error,
                'ise': control_metrics.integral_squared_error,
                'control_effort': control_metrics.control_effort,
                'stability_margin': control_metrics.stability_margin
            }
        
        if system_metrics:
            report['system_performance'] = {
                'efficiency': system_metrics.efficiency,
                'throughput': system_metrics.throughput,
                'response_time': system_metrics.response_time,
                'reliability': system_metrics.reliability,
                'robustness': system_metrics.robustness,
                'energy_consumption': system_metrics.energy_consumption
            }
        
        if statistical_metrics:
            report['statistical_analysis'] = {
                'mean': statistical_metrics.mean,
                'std': statistical_metrics.std,
                'variance': statistical_metrics.variance,
                'min': statistical_metrics.min_value,
                'max': statistical_metrics.max_value,
                'median': statistical_metrics.median,
                'skewness': statistical_metrics.skewness,
                'kurtosis': statistical_metrics.kurtosis,
                'percentile_95': statistical_metrics.percentile_95,
                'percentile_5': statistical_metrics.percentile_5
            }
        
        if frequency_analysis:
            report['frequency_analysis'] = {
                'bandwidth': frequency_analysis['bandwidth'],
                'phase_margin': frequency_analysis['phase_margin'],
                'gain_margin': frequency_analysis['gain_margin']
            }
        
        if stability_metrics:
            report['stability_analysis'] = stability_metrics
        
        # 计算综合评分
        report['overall_score'] = self._calculate_overall_score(report)
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"性能报告已保存到: {save_path}")
        
        return report
    
    def _calculate_settling_time(self, actual: np.ndarray, 
                               setpoint: np.ndarray, 
                               time: np.ndarray,
                               tolerance: float = 0.02) -> float:
        """计算调节时间"""
        if isinstance(setpoint, (int, float)):
            final_value = setpoint
        else:
            final_value = setpoint[-1]
        
        error = np.abs(actual - final_value) / np.abs(final_value)
        
        # 从后往前找第一个超出容差的点
        for i in range(len(error) - 1, -1, -1):
            if error[i] > tolerance:
                return time[min(i + 1, len(time) - 1)]
        
        return time[0]
    
    def _calculate_overshoot(self, actual: np.ndarray, setpoint: np.ndarray) -> float:
        """计算超调量"""
        if isinstance(setpoint, (int, float)):
            final_value = setpoint
        else:
            final_value = setpoint[-1]
        
        max_value = np.max(actual)
        overshoot = (max_value - final_value) / np.abs(final_value) * 100
        
        return max(0, overshoot)
    
    def _calculate_rise_time(self, actual: np.ndarray, 
                           setpoint: np.ndarray, 
                           time: np.ndarray) -> float:
        """计算上升时间"""
        if isinstance(setpoint, (int, float)):
            final_value = setpoint
        else:
            final_value = setpoint[-1]
        
        initial_value = actual[0]
        
        # 10%到90%的时间
        value_10 = initial_value + 0.1 * (final_value - initial_value)
        value_90 = initial_value + 0.9 * (final_value - initial_value)
        
        t_10 = np.interp(value_10, actual, time)
        t_90 = np.interp(value_90, actual, time)
        
        return t_90 - t_10
    
    def _calculate_stability_margin(self, actual: np.ndarray, time: np.ndarray) -> float:
        """计算稳定性裕度"""
        # 简化计算：基于最后部分的变异性
        final_portion = actual[-int(0.2 * len(actual)):]
        stability_margin = 1 / (1 + np.std(final_portion))
        
        return stability_margin
    
    def _calculate_response_time(self, input_data: Dict[str, np.ndarray],
                               output_data: Dict[str, np.ndarray]) -> float:
        """计算响应时间"""
        # 简化计算：假设第一个输入和输出变量
        input_key = list(input_data.keys())[0]
        output_key = list(output_data.keys())[0]
        
        # 计算互相关
        correlation = np.correlate(output_data[output_key], input_data[input_key], mode='full')
        delay_samples = np.argmax(correlation) - len(input_data[input_key]) + 1
        
        return abs(delay_samples) * self.dt
    
    def _calculate_reliability(self, output_data: Dict[str, np.ndarray]) -> float:
        """计算可靠性"""
        # 基于输出稳定性
        reliabilities = []
        for data in output_data.values():
            cv = np.std(data) / (np.abs(np.mean(data)) + 1e-10)
            reliability = 1 / (1 + cv)
            reliabilities.append(reliability)
        
        return np.mean(reliabilities)
    
    def _calculate_robustness(self, output_data: Dict[str, np.ndarray]) -> float:
        """计算鲁棒性"""
        # 基于输出变异性的倒数
        robustness_values = []
        for data in output_data.values():
            normalized_std = np.std(data) / (np.max(data) - np.min(data) + 1e-10)
            robustness = 1 / (1 + normalized_std)
            robustness_values.append(robustness)
        
        return np.mean(robustness_values)
    
    def _calculate_bandwidth(self, frequencies: np.ndarray, magnitude: np.ndarray) -> float:
        """计算带宽"""
        # -3dB带宽
        max_mag = np.max(magnitude)
        cutoff_mag = max_mag / np.sqrt(2)
        
        # 找到截止频率
        cutoff_indices = np.where(magnitude >= cutoff_mag)[0]
        if len(cutoff_indices) > 0:
            return frequencies[cutoff_indices[-1]]
        else:
            return frequencies[-1]
    
    def _calculate_margins(self, frequencies: np.ndarray, 
                         transfer_function: np.ndarray) -> Tuple[float, float]:
        """计算相位裕度和增益裕度"""
        magnitude = np.abs(transfer_function)
        phase = np.angle(transfer_function, deg=True)
        
        # 增益裕度：相位为-180°时的增益
        phase_180_idx = np.argmin(np.abs(phase + 180))
        gain_margin = 1 / magnitude[phase_180_idx] if magnitude[phase_180_idx] > 0 else np.inf
        
        # 相位裕度：增益为1时的相位
        gain_1_idx = np.argmin(np.abs(magnitude - 1))
        phase_margin = 180 + phase[gain_1_idx]
        
        return phase_margin, 20 * np.log10(gain_margin)
    
    def _calculate_overall_score(self, report: Dict[str, Any]) -> float:
        """计算综合评分"""
        score = 0.0
        weight_sum = 0.0
        
        # 控制性能权重
        if 'control_performance' in report:
            control_score = 0.0
            control_score += max(0, 1 - report['control_performance']['rmse']) * 0.3
            control_score += max(0, 1 - report['control_performance']['steady_state_error']) * 0.3
            control_score += report['control_performance']['stability_margin'] * 0.4
            
            score += control_score * 0.4
            weight_sum += 0.4
        
        # 系统性能权重
        if 'system_performance' in report:
            system_score = 0.0
            system_score += report['system_performance']['efficiency'] * 0.4
            system_score += report['system_performance']['reliability'] * 0.3
            system_score += report['system_performance']['robustness'] * 0.3
            
            score += system_score * 0.3
            weight_sum += 0.3
        
        # 稳定性权重
        if 'stability_analysis' in report:
            stability_score = report['stability_analysis'].get('stability_index', 0.5)
            score += stability_score * 0.3
            weight_sum += 0.3
        
        return score / weight_sum if weight_sum > 0 else 0.0

def quick_analysis(data: np.ndarray, 
                  setpoint: Optional[Union[float, np.ndarray]] = None,
                  time_step: float = 1.0) -> Dict[str, Any]:
    """
    快速性能分析
    
    Args:
        data: 数据数组
        setpoint: 设定值
        dt: 采样时间
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    analyzer = PerformanceAnalyzer(dt)
    
    results = {}
    
    # 统计分析
    results['statistics'] = analyzer.calculate_statistical_metrics(data)
    
    # 稳定性分析
    results['stability'] = analyzer.calculate_stability_metrics(data)
    
    # 振荡检测
    results['oscillation'] = analyzer.detect_oscillations(data)
    
    # 控制分析（如果有设定值）
    if setpoint is not None:
        time = np.arange(len(data)) * dt
        results['control'] = analyzer.calculate_control_metrics(setpoint, data, time=time)
    
    return results

def compare_performance(data1: np.ndarray, data2: np.ndarray,
                       labels: List[str] = ['Method 1', 'Method 2'],
                       time_step: float = 1.0) -> Dict[str, Any]:
    """
    比较两种方法的性能
    
    Args:
        data1: 第一组数据
        data2: 第二组数据
        labels: 标签列表
        dt: 采样时间
        
    Returns:
        Dict[str, Any]: 比较结果
    """
    analyzer = PerformanceAnalyzer(dt)
    
    # 分别分析
    stats1 = analyzer.calculate_statistical_metrics(data1)
    stats2 = analyzer.calculate_statistical_metrics(data2)
    
    stability1 = analyzer.calculate_stability_metrics(data1)
    stability2 = analyzer.calculate_stability_metrics(data2)
    
    # 比较结果
    comparison = {
        'methods': labels,
        'statistics': {
            labels[0]: stats1,
            labels[1]: stats2
        },
        'stability': {
            labels[0]: stability1,
            labels[1]: stability2
        },
        'winner': {
            'lower_variance': labels[0] if stats1.variance < stats2.variance else labels[1],
            'higher_stability': labels[0] if stability1['stability_index'] > stability2['stability_index'] else labels[1],
            'better_convergence': labels[0] if stability1['convergence_error'] < stability2['convergence_error'] else labels[1]
        }
    }
    
    return comparison