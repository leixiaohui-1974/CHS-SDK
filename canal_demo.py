#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
渠道案例演示脚本

基于run_scenario.py实现渠道控制系统的完整演示，包括：
- 渠道水流仿真
- PID控制器调节闸门开度
- 实时数据可视化
- 性能分析报告

使用方法：
python canal_demo.py [scenario_path] [--agents agents_file]
"""

import logging
import sys
import argparse
import time
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.io.yaml_writer import save_history_to_yaml

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class CanalDemo:
    """渠道案例演示类"""
    
    def __init__(self, scenario_path: str, agents_file: str = "agents.yml"):
        self.scenario_path = Path(scenario_path)
        self.agents_file = agents_file
        self.harness = None
        self.history = []
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def run_simulation(self):
        """运行渠道仿真"""
        self.logger.info(f"=== 渠道案例演示开始 ===")
        self.logger.info(f"场景路径: {self.scenario_path}")
        self.logger.info(f"智能体配置: {self.agents_file}")
        
        try:
            # 初始化仿真构建器
            loader = YamlSimulationLoader(
                scenario_path=str(self.scenario_path), 
                agents_file=self.agents_file
            )
            
            # 加载仿真系统
            self.logger.info("正在加载仿真系统...")
            self.harness = loader.load()
            
            # 运行仿真
            self.logger.info("开始运行渠道仿真...")
            start_time = time.time()
            self.harness.run_mas_simulation()
            end_time = time.time()
            
            # 获取仿真历史数据
            self.history = self.harness.history
            self.logger.info(f"仿真完成！运行时间: {end_time - start_time:.2f}秒")
            self.logger.info(f"生成了 {len(self.history)} 步历史数据")
            
            return True
            
        except Exception as e:
            self.logger.error(f"仿真运行失败: {e}")
            return False
    
    def create_visualization(self):
        """创建可视化图表"""
        if not self.history:
            self.logger.warning("没有历史数据，无法创建可视化")
            return
        
        self.logger.info("正在生成可视化图表...")
        
        # 提取时间序列数据
        time_data = [step['time'] for step in self.history]
        
        # 创建综合图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('渠道控制系统仿真结果', fontsize=16, fontweight='bold')
        
        # 1. 水位变化图
        ax1 = axes[0, 0]
        water_levels = self._extract_water_levels()
        for component, levels in water_levels.items():
            ax1.plot(time_data, levels, label=f'{component} 水位', linewidth=2)
        ax1.set_title('渠道水位变化')
        ax1.set_xlabel('时间 (秒)')
        ax1.set_ylabel('水位 (米)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 闸门开度图
        ax2 = axes[0, 1]
        gate_openings = self._extract_gate_openings()
        for gate, openings in gate_openings.items():
            ax2.plot(time_data, openings, label=f'{gate} 开度', linewidth=2)
        ax2.set_title('闸门开度变化')
        ax2.set_xlabel('时间 (秒)')
        ax2.set_ylabel('开度 (0-1)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 流量变化图
        ax3 = axes[1, 0]
        flow_rates = self._extract_flow_rates()
        for component, flows in flow_rates.items():
            ax3.plot(time_data, flows, label=f'{component} 流量', linewidth=2)
        ax3.set_title('流量变化')
        ax3.set_xlabel('时间 (秒)')
        ax3.set_ylabel('流量 (m³/s)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 控制性能图
        ax4 = axes[1, 1]
        control_errors = self._extract_control_errors()
        for component, errors in control_errors.items():
            ax4.plot(time_data, errors, label=f'{component} 控制误差', linewidth=2)
        ax4.set_title('控制误差')
        ax4.set_xlabel('时间 (秒)')
        ax4.set_ylabel('误差 (米)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_path = self.scenario_path / f"canal_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        self.logger.info(f"可视化图表已保存: {output_path}")
        
        # 显示图表
        plt.show()
        
        return output_path
    
    def _extract_water_levels(self):
        """提取水位数据"""
        water_levels = {}
        for step in self.history:
            for key, value in step.items():
                if 'level' in key.lower() and isinstance(value, (int, float)):
                    component = key.replace('_level', '').replace('_water_level', '')
                    if component not in water_levels:
                        water_levels[component] = []
                    water_levels[component].append(value)
        return water_levels
    
    def _extract_gate_openings(self):
        """提取闸门开度数据"""
        gate_openings = {}
        for step in self.history:
            for key, value in step.items():
                if 'opening' in key.lower() and isinstance(value, (int, float)):
                    gate = key.replace('_opening', '')
                    if gate not in gate_openings:
                        gate_openings[gate] = []
                    gate_openings[gate].append(value)
        return gate_openings
    
    def _extract_flow_rates(self):
        """提取流量数据"""
        flow_rates = {}
        for step in self.history:
            for key, value in step.items():
                if ('flow' in key.lower() or 'inflow' in key.lower() or 'outflow' in key.lower()) and isinstance(value, (int, float)):
                    component = key.replace('_flow', '').replace('_inflow', '').replace('_outflow', '')
                    if component not in flow_rates:
                        flow_rates[component] = []
                    flow_rates[component].append(value)
        return flow_rates
    
    def _extract_control_errors(self):
        """提取控制误差数据"""
        control_errors = {}
        for step in self.history:
            for key, value in step.items():
                if 'error' in key.lower() and isinstance(value, (int, float)):
                    component = key.replace('_error', '')
                    if component not in control_errors:
                        control_errors[component] = []
                    control_errors[component].append(value)
        return control_errors
    
    def generate_report(self):
        """生成分析报告"""
        if not self.history:
            self.logger.warning("没有历史数据，无法生成报告")
            return
        
        self.logger.info("正在生成分析报告...")
        
        # 计算性能指标
        water_levels = self._extract_water_levels()
        gate_openings = self._extract_gate_openings()
        flow_rates = self._extract_flow_rates()
        
        report = []
        report.append("# 渠道控制系统仿真分析报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"仿真时长: {len(self.history)} 步")
        report.append("")
        
        # 水位分析
        report.append("## 水位分析")
        for component, levels in water_levels.items():
            if levels:
                avg_level = np.mean(levels)
                max_level = np.max(levels)
                min_level = np.min(levels)
                std_level = np.std(levels)
                report.append(f"- **{component}**: 平均={avg_level:.2f}m, 最大={max_level:.2f}m, 最小={min_level:.2f}m, 标准差={std_level:.2f}m")
        report.append("")
        
        # 闸门开度分析
        report.append("## 闸门开度分析")
        for gate, openings in gate_openings.items():
            if openings:
                avg_opening = np.mean(openings)
                max_opening = np.max(openings)
                min_opening = np.min(openings)
                report.append(f"- **{gate}**: 平均开度={avg_opening:.3f}, 最大={max_opening:.3f}, 最小={min_opening:.3f}")
        report.append("")
        
        # 流量分析
        report.append("## 流量分析")
        for component, flows in flow_rates.items():
            if flows:
                avg_flow = np.mean(flows)
                max_flow = np.max(flows)
                min_flow = np.min(flows)
                report.append(f"- **{component}**: 平均流量={avg_flow:.2f}m³/s, 最大={max_flow:.2f}m³/s, 最小={min_flow:.2f}m³/s")
        report.append("")
        
        # 保存报告
        report_text = "\n".join(report)
        report_path = self.scenario_path / f"canal_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"分析报告已保存: {report_path}")
        print("\n" + "="*50)
        print("仿真分析报告")
        print("="*50)
        print(report_text)
        
        return report_path
    
    def save_results(self):
        """保存仿真结果"""
        if not self.history:
            self.logger.warning("没有历史数据，无法保存结果")
            return
        
        # 保存YAML格式的历史数据
        output_filename = f"canal_demo_output_{Path(self.agents_file).stem}.yml"
        output_path = self.scenario_path / output_filename
        save_history_to_yaml(self.history, str(output_path))
        self.logger.info(f"仿真结果已保存: {output_path}")
        
        return output_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="渠道案例演示脚本")
    parser.add_argument("scenario_path", type=str, help="仿真场景目录路径")
    parser.add_argument("--agents", type=str, default="agents.yml", help="智能体配置文件名称")
    parser.add_argument("--no-viz", action="store_true", help="不显示可视化图表")
    parser.add_argument("--no-report", action="store_true", help="不生成分析报告")
    
    args = parser.parse_args()
    
    # 检查场景路径
    scenario_path = Path(args.scenario_path)
    if not scenario_path.is_dir():
        print(f"错误: 场景路径不存在: {scenario_path}")
        sys.exit(1)
    
    # 创建演示实例
    demo = CanalDemo(str(scenario_path), args.agents)
    
    # 运行仿真
    if not demo.run_simulation():
        print("仿真运行失败，程序退出")
        sys.exit(1)
    
    # 创建可视化
    if not args.no_viz:
        demo.create_visualization()
    
    # 生成报告
    if not args.no_report:
        demo.generate_report()
    
    # 保存结果
    demo.save_results()
    
    print("\n渠道案例演示完成！")

if __name__ == "__main__":
    main()
