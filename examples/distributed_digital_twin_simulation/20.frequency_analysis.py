#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频率分析脚本
分析水位波动和用水需求的频率特性差异
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from pathlib import Path
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

class FrequencyAnalyzer:
    """频率分析器"""
    
    def __init__(self, results_dir="experiment_results"):
        self.results_dir = Path(results_dir)
        
    def load_data(self, mode, scenario):
        """加载数据"""
        file_path = self.results_dir / f"{mode}_{scenario}_data.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            print(f"警告: 文件 {file_path} 不存在")
            return None
    
    def compute_fft(self, signal_data, sampling_rate):
        """计算FFT频谱"""
        # 去除直流分量
        signal_data = signal_data - np.mean(signal_data)
        
        # 计算FFT
        fft_result = np.fft.fft(signal_data)
        freqs = np.fft.fftfreq(len(signal_data), 1/sampling_rate)
        
        # 只取正频率部分
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        
        return positive_freqs, magnitude
    
    def analyze_frequency_characteristics(self):
        """分析频率特性"""
        scenarios = ["normal_operation", "rainfall_disturbance", "extreme_disturbance"]
        modes = ["rule", "mpc"]
        
        for scenario in scenarios:
            print(f"\n分析场景: {scenario}")
            
            fig, axes = plt.subplots(3, 2, figsize=(16, 12))
            fig.suptitle(f'频率特性分析 - {scenario.replace("_", " ").title()}', 
                        fontsize=16, fontweight='bold')
            
            for mode_idx, mode in enumerate(modes):
                data = self.load_data(mode, scenario)
                if data is None:
                    continue
                
                # 采样率 (每10秒一个数据点)
                dt = 10  # 秒
                sampling_rate = 1.0 / dt  # Hz
                
                # 时间轴（分钟）
                time_minutes = data['time'] / 60
                
                # 分析用水需求频率特性
                water_demand = data['water_demand_1'].values
                freqs_demand, magnitude_demand = self.compute_fft(water_demand, sampling_rate)
                
                # 分析水位波动频率特性
                water_level = data['Gate_1_upstream_level'].values
                freqs_level, magnitude_level = self.compute_fft(water_level, sampling_rate)
                
                # 分析控制指令频率特性
                control_command = data['control_command_1'].values
                freqs_control, magnitude_control = self.compute_fft(control_command, sampling_rate)
                
                # 绘制时域信号
                ax_time = axes[0, mode_idx]
                ax_time.plot(time_minutes, water_demand, 'b-', label='用水需求', linewidth=1.5)
                ax_time.plot(time_minutes, water_level, 'r-', label='水位', linewidth=1.5)
                ax_time.plot(time_minutes, control_command, 'g-', label='控制指令', linewidth=1.5)
                ax_time.set_xlabel('时间 (分钟)')
                ax_time.set_ylabel('幅值')
                ax_time.set_title(f'{mode.upper()}模式 - 时域信号')
                ax_time.legend()
                ax_time.grid(True, alpha=0.3)
                
                # 绘制频谱
                ax_freq = axes[1, mode_idx]
                # 转换频率到周期（分钟）
                periods_demand = 1.0 / (freqs_demand[1:] * 60)  # 跳过直流分量
                periods_level = 1.0 / (freqs_level[1:] * 60)
                periods_control = 1.0 / (freqs_control[1:] * 60)
                
                ax_freq.loglog(periods_demand, magnitude_demand[1:], 'b-', label='用水需求', linewidth=2)
                ax_freq.loglog(periods_level, magnitude_level[1:], 'r-', label='水位', linewidth=2)
                ax_freq.loglog(periods_control, magnitude_control[1:], 'g-', label='控制指令', linewidth=2)
                ax_freq.set_xlabel('周期 (分钟)')
                ax_freq.set_ylabel('幅值')
                ax_freq.set_title(f'{mode.upper()}模式 - 频谱分析')
                ax_freq.legend()
                ax_freq.grid(True, alpha=0.3)
                
                # 计算主要频率成分
                self._analyze_dominant_frequencies(freqs_demand, magnitude_demand, 
                                                 freqs_level, magnitude_level,
                                                 freqs_control, magnitude_control,
                                                 mode, scenario)
                
                # 绘制功率谱密度对比
                ax_psd = axes[2, mode_idx]
                # 计算功率谱密度
                f_demand, psd_demand = signal.welch(water_demand, fs=sampling_rate, nperseg=min(256, len(water_demand)//4))
                f_level, psd_level = signal.welch(water_level, fs=sampling_rate, nperseg=min(256, len(water_level)//4))
                f_control, psd_control = signal.welch(control_command, fs=sampling_rate, nperseg=min(256, len(control_command)//4))
                
                # 转换到周期（分钟）
                periods_psd_demand = 1.0 / (f_demand[1:] * 60)
                periods_psd_level = 1.0 / (f_level[1:] * 60)
                periods_psd_control = 1.0 / (f_control[1:] * 60)
                
                ax_psd.loglog(periods_psd_demand, psd_demand[1:], 'b-', label='用水需求', linewidth=2)
                ax_psd.loglog(periods_psd_level, psd_level[1:], 'r-', label='水位', linewidth=2)
                ax_psd.loglog(periods_psd_control, psd_control[1:], 'g-', label='控制指令', linewidth=2)
                ax_psd.set_xlabel('周期 (分钟)')
                ax_psd.set_ylabel('功率谱密度')
                ax_psd.set_title(f'{mode.upper()}模式 - 功率谱密度')
                ax_psd.legend()
                ax_psd.grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_file = self.results_dir / f"frequency_analysis_{scenario}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"已生成频率分析图: {output_file}")
    
    def _analyze_dominant_frequencies(self, freqs_demand, magnitude_demand, 
                                    freqs_level, magnitude_level,
                                    freqs_control, magnitude_control,
                                    mode, scenario):
        """分析主要频率成分"""
        # 找到主要频率成分（排除直流分量）
        demand_peaks = signal.find_peaks(magnitude_demand[1:], height=np.max(magnitude_demand[1:])*0.1)[0] + 1
        level_peaks = signal.find_peaks(magnitude_level[1:], height=np.max(magnitude_level[1:])*0.1)[0] + 1
        control_peaks = signal.find_peaks(magnitude_control[1:], height=np.max(magnitude_control[1:])*0.1)[0] + 1
        
        print(f"\n{mode.upper()}模式 - {scenario}:")
        
        if len(demand_peaks) > 0:
            dominant_freq_demand = freqs_demand[demand_peaks[0]]
            period_demand = 1.0 / dominant_freq_demand / 60  # 转换为分钟
            print(f"  用水需求主要周期: {period_demand:.1f} 分钟")
        
        if len(level_peaks) > 0:
            dominant_freq_level = freqs_level[level_peaks[0]]
            period_level = 1.0 / dominant_freq_level / 60
            print(f"  水位波动主要周期: {period_level:.1f} 分钟")
        
        if len(control_peaks) > 0:
            dominant_freq_control = freqs_control[control_peaks[0]]
            period_control = 1.0 / dominant_freq_control / 60
            print(f"  控制指令主要周期: {period_control:.1f} 分钟")
    
    def generate_frequency_report(self):
        """生成频率分析报告"""
        report_content = """
# 频率特性分析报告

## 分析目的
分析水位波动频率比用水波动频率高的原因

## 理论分析

### 1. 控制系统动态特性
- **用水需求**: 外部扰动输入，变化相对缓慢，主要受用户行为模式影响
- **水位响应**: 系统输出，受多种因素影响，包括扰动、控制作用和系统动态
- **控制指令**: 控制器输出，响应频率取决于控制算法和系统需求

### 2. 频率差异的原因

#### 2.1 控制系统的放大效应
- 控制系统为了快速响应扰动，会产生比扰动频率更高的控制动作
- PID控制器的微分项会放大高频成分
- MPC预测控制会产生预测性的高频调节

#### 2.2 系统动态响应
- 水位作为被控变量，需要快速跟踪设定值
- 系统的自然频率和阻尼特性影响响应频率
- 多个扰动源的叠加效应

#### 2.3 噪声和不确定性
- 测量噪声引入高频成分
- 模型不确定性导致控制器产生高频修正
- 随机扰动的影响

### 3. 模拟数据中的体现

#### 3.1 用水需求特性
- 基于小时周期的正弦变化 (周期 = 60分钟)
- 变化相对平缓，符合实际用水模式
- 频率成分主要集中在低频段

#### 3.2 水位波动特性
- 包含多个频率成分的叠加
- 控制响应产生的高频成分
- 随机噪声引入的宽频谱特性

#### 3.3 控制指令特性
- Rule模式: 本地PID控制，响应频率较高
- MPC模式: 预测控制，包含预测性高频调节

## 实际工程意义

### 1. 控制系统设计
- 需要考虑控制带宽和稳定性的平衡
- 滤波器设计以抑制高频噪声
- 控制参数调优以减少不必要的高频动作

### 2. 系统性能评估
- 频率域分析有助于理解控制性能
- 识别系统的主要频率特性
- 优化控制策略以改善频率响应

### 3. 实际应用建议
- 在实际系统中应监控频率特性
- 避免过度控制导致的高频振荡
- 合理设置控制器参数以平衡响应速度和稳定性
"""
        
        report_file = self.results_dir / "frequency_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n已生成频率分析报告: {report_file}")

def main():
    """主函数"""
    print("开始频率特性分析...")
    
    analyzer = FrequencyAnalyzer()
    
    # 执行频率分析
    analyzer.analyze_frequency_characteristics()
    
    # 生成分析报告
    analyzer.generate_frequency_report()
    
    print("\n频率分析完成！")
    print("结果保存在: experiment_results")

if __name__ == "__main__":
    main()