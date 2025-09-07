"""
性能分析器模块 - 统一管理各种性能分析功能

遵循单一职责原则，每个分析器只负责一种分析功能
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
import matplotlib.pyplot as plt

class PerformanceAnalyzer:
    """性能分析器基类 - 单一职责：分析性能数据"""
    
    def __init__(self):
        self.history = []
        
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, float]:
        """分析性能数据"""
        pass
        
    def record_data(self, timestamp: float, data: Dict[str, Any]):
        """记录数据"""
        self.history.append({'timestamp': timestamp, **data})

class ControlPerformanceAnalyzer(PerformanceAnalyzer):
    """控制性能分析器 - 单一职责：分析控制性能"""
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, float]:
        """分析控制性能"""
        if not self.history:
            return {}
            
        # 提取数据
        demands = [h['demand'] for h in self.history]
        flows = [h['total_flow'] for h in self.history]
        
        # 计算控制误差
        errors = [abs(flow - demand) for flow, demand in zip(flows, demands)]
        
        return {
            'mean_flow_error': np.mean(errors),
            'max_flow_error': np.max(errors),
            'flow_rmse': np.sqrt(np.mean([e**2 for e in errors])),
            'control_accuracy': 1.0 - (np.mean(errors) / np.mean(demands)) if np.mean(demands) > 0 else 0
        }

class EnergyPerformanceAnalyzer(PerformanceAnalyzer):
    """能耗性能分析器 - 单一职责：分析能耗性能"""
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, float]:
        """分析能耗性能"""
        if not self.history:
            return {}
            
        # 提取数据
        powers = [h['total_power'] for h in self.history]
        flows = [h['total_flow'] for h in self.history]
        efficiencies = [h['efficiency'] for h in self.history]
        
        return {
            'average_power': np.mean(powers),
            'total_energy': np.sum(powers) * (self.history[-1]['timestamp'] - self.history[0]['timestamp']),
            'average_efficiency': np.mean(efficiencies),
            'energy_per_unit_flow': np.mean(powers) / np.mean(flows) if np.mean(flows) > 0 else 0
        }

class UtilizationAnalyzer(PerformanceAnalyzer):
    """利用率分析器 - 单一职责：分析设备利用率"""
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, float]:
        """分析设备利用率"""
        if not self.history:
            return {}
            
        # 提取数据
        running_pumps = [h['running_pumps'] for h in self.history]
        total_pumps = data.get('total_pumps', 1)
        
        return {
            'pump_utilization': np.mean(running_pumps) / total_pumps,
            'max_utilization': np.max(running_pumps) / total_pumps,
            'utilization_variance': np.var(running_pumps) / total_pumps
        }

class ComprehensiveAnalyzer:
    """综合分析器 - 组合多个分析器"""
    
    def __init__(self):
        self.control_analyzer = ControlPerformanceAnalyzer()
        self.energy_analyzer = EnergyPerformanceAnalyzer()
        self.utilization_analyzer = UtilizationAnalyzer()
        
    def record_data(self, timestamp: float, data: Dict[str, Any]):
        """记录数据到所有分析器"""
        self.control_analyzer.record_data(timestamp, data)
        self.energy_analyzer.record_data(timestamp, data)
        self.utilization_analyzer.record_data(timestamp, data)
        
    def analyze_all(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """综合分析"""
        return {
            'control_performance': self.control_analyzer.analyze(system_info),
            'energy_performance': self.energy_analyzer.analyze(system_info),
            'utilization': self.utilization_analyzer.analyze(system_info)
        }
        
    def plot_results(self, save_path: str = "analysis_results.png"):
        """绘制分析结果"""
        if not self.control_analyzer.history:
            print("No data to plot")
            return
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 提取时间数据
        times = [h['timestamp'] for h in self.control_analyzer.history]
        
        # 1. 流量控制响应
        demands = [h['demand'] for h in self.control_analyzer.history]
        flows = [h['total_flow'] for h in self.control_analyzer.history]
        
        ax1.plot(times, demands, 'r--', linewidth=2, label='Demand')
        ax1.plot(times, flows, 'b-', linewidth=2, label='Actual Flow')
        ax1.set_title('Flow Control Response', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Flow Rate (m³/s)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 运行水泵数量
        running_pumps = [h['running_pumps'] for h in self.control_analyzer.history]
        ax2.plot(times, running_pumps, 'g-', linewidth=2, label='Running Pumps')
        ax2.set_title('Pump Operation Status', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Number of Running Pumps')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 功率消耗
        powers = [h['total_power'] for h in self.energy_analyzer.history]
        ax3.plot(times, powers, 'purple', linewidth=2, label='Total Power')
        ax3.set_title('Power Consumption', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Power (kW)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 效率特性
        efficiencies = [h['efficiency'] for h in self.energy_analyzer.history]
        ax4.plot(times, efficiencies, 'orange', linewidth=2, label='System Efficiency')
        ax4.set_title('System Efficiency Over Time', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Efficiency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Analysis results saved to {save_path}")
        plt.show()
