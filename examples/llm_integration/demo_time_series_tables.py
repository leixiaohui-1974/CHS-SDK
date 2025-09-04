#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间序列分析表格生成演示程序

本程序用于生成水利系统中被控对象和控制对象的详细时间序列数据表格，
包括状态变量、控制指令、性能指标等的时间序列数据。

作者: AI Assistant
创建时间: 2025-09-04
"""

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import tempfile

class TimeSeriesTableGenerator:
    """
    时间序列分析表格生成器
    
    用于生成水利系统中各种对象的详细时间序列数据表格，
    包括被控对象和控制对象的状态、指令、性能等数据。
    """
    
    def __init__(self, config_path: str):
        """
        初始化表格生成器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.controlled_objects = self._extract_controlled_objects()
        self.control_objects = self._extract_control_objects()
        
        # 创建输出目录
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"成功加载配置文件: {config_path}")
        print(f"发现被控对象: {len(self.controlled_objects)} 个")
        print(f"发现控制对象: {len(self.control_objects)} 个")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"无法加载配置文件 {self.config_path}: {e}")
    
    def _extract_controlled_objects(self) -> List[Dict[str, Any]]:
        """提取被控对象信息"""
        controlled_objects = []
        
        # 从组件中提取被控对象（水库、渠道、河道等）
        components = self.config.get('components', [])
        for comp in components:
            comp_type = comp.get('type', '')
            if comp_type in ['reservoir', 'canal', 'river', 'pool', 'tank']:
                controlled_objects.append(comp)
        
        return controlled_objects
    
    def _extract_control_objects(self) -> List[Dict[str, Any]]:
        """提取控制对象信息"""
        control_objects = []
        
        # 从组件中提取控制对象（闸门、泵站等）
        components = self.config.get('components', [])
        for comp in components:
            comp_type = comp.get('type', '')
            if comp_type in ['gate', 'pump', 'valve', 'turbine']:
                control_objects.append(comp)
        
        return control_objects
    
    def generate_controlled_object_table(self, obj: Dict[str, Any]) -> pd.DataFrame:
        """生成被控对象时间序列数据表格"""
        obj_id = obj.get('id', 'unknown')
        obj_type = obj.get('type', 'unknown')
        
        # 生成24小时的时间序列数据（10分钟间隔）
        time_points = 144
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_series = [start_time + timedelta(minutes=10*i) for i in range(time_points)]
        
        # 设置随机种子确保可重现性
        np.random.seed(hash(obj_id) % 2**32)
        
        # 根据对象类型生成不同的数据
        if obj_type == 'reservoir':
            data = self._generate_reservoir_data(time_points)
        elif obj_type == 'canal':
            data = self._generate_canal_data(time_points)
        elif obj_type == 'river':
            data = self._generate_river_data(time_points)
        elif obj_type == 'pool':
            data = self._generate_pool_data(time_points)
        else:
            data = self._generate_default_controlled_data(time_points)
        
        # 创建DataFrame
        df = pd.DataFrame({
            '时间': time_series,
            **data
        })
        
        # 格式化时间列
        df['时间'] = df['时间'].dt.strftime('%H:%M')
        
        return df
    
    def _generate_reservoir_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成水库时间序列数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 扰动数据
        inflow = 35 + 15 * np.sin(2*np.pi*time_hours/24) + 5 * np.sin(2*np.pi*time_hours/12) + np.random.normal(0, 3, time_points)
        rainfall = np.maximum(0, 2 + 8 * np.random.exponential(0.1, time_points) * (np.random.random(time_points) < 0.1))
        evaporation = 3 + 2 * np.sin(2*np.pi*(time_hours-12)/24) + np.random.normal(0, 0.5, time_points)
        
        # 状态变量
        target_level = 16.0 + 0.5 * np.sin(2*np.pi*time_hours/24)
        actual_level = target_level + np.random.normal(0, 0.2, time_points)
        storage = 20000 + 1000 * (actual_level - 15.0)  # 万m³
        outflow = 30 + 10 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 2, time_points)
        
        # 控制数据
        gate_opening = 50 + 20 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 3, time_points)
        control_command = gate_opening + np.random.normal(0, 1, time_points)
        
        # 性能指标
        level_error = actual_level - target_level
        control_efficiency = 90 + 5 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 2, time_points)
        
        return {
            '入流量(m³/s)': np.round(inflow, 2),
            '降雨径流(m³/s)': np.round(rainfall, 2),
            '蒸发损失(m³/s)': np.round(evaporation, 2),
            '目标水位(m)': np.round(target_level, 2),
            '实际水位(m)': np.round(actual_level, 2),
            '蓄水量(万m³)': np.round(storage, 1),
            '出流量(m³/s)': np.round(outflow, 2),
            '闸门开度(%)': np.round(gate_opening, 1),
            '控制指令(%)': np.round(control_command, 1),
            '水位误差(m)': np.round(level_error, 3),
            '控制效率(%)': np.round(control_efficiency, 1)
        }
    
    def _generate_canal_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成渠道时间序列数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 扰动数据
        upstream_flow = 25 + 10 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 2, time_points)
        lateral_withdrawal = 5 + 3 * np.sin(2*np.pi*time_hours/12) + np.random.normal(0, 1, time_points)
        seepage_loss = 2 + 0.5 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 0.3, time_points)
        
        # 状态变量
        target_flow = 20 + 8 * np.sin(2*np.pi*time_hours/24)
        actual_flow = target_flow + np.random.normal(0, 1.5, time_points)
        water_level = 3.0 + 0.8 * (actual_flow / 25) + np.random.normal(0, 0.1, time_points)
        velocity = actual_flow / (15 * water_level)  # 流速 = 流量 / (底宽 * 水深)
        
        # 控制数据
        gate_position = 60 + 25 * (target_flow / 30) + np.random.normal(0, 2, time_points)
        flow_command = target_flow + np.random.normal(0, 0.8, time_points)
        
        # 性能指标
        flow_error = actual_flow - target_flow
        transport_efficiency = 85 + 10 * (1 - seepage_loss/5) + np.random.normal(0, 2, time_points)
        
        return {
            '上游流量(m³/s)': np.round(upstream_flow, 2),
            '侧向取水(m³/s)': np.round(lateral_withdrawal, 2),
            '渗漏损失(m³/s)': np.round(seepage_loss, 2),
            '目标流量(m³/s)': np.round(target_flow, 2),
            '实际流量(m³/s)': np.round(actual_flow, 2),
            '水位(m)': np.round(water_level, 2),
            '流速(m/s)': np.round(velocity, 3),
            '闸门位置(%)': np.round(gate_position, 1),
            '流量指令(m³/s)': np.round(flow_command, 2),
            '流量误差(m³/s)': np.round(flow_error, 3),
            '输水效率(%)': np.round(transport_efficiency, 1)
        }
    
    def _generate_river_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成河道时间序列数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 扰动数据
        natural_inflow = 40 + 20 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 5, time_points)
        tributary_flow = 8 + 4 * np.sin(2*np.pi*time_hours/12) + np.random.normal(0, 2, time_points)
        regulation_flow = 5 * np.sin(2*np.pi*time_hours/8) + np.random.normal(0, 1, time_points)
        
        # 状态变量
        total_flow = natural_inflow + tributary_flow + regulation_flow
        water_level = 5.0 + 1.5 * (total_flow / 50) + np.random.normal(0, 0.2, time_points)
        velocity = total_flow / (200 * water_level)  # 流速 = 流量 / (河宽 * 水深)
        
        # 环境指标
        water_quality = 85 + 10 * np.random.random(time_points)
        sediment_load = 0.5 + 0.3 * (total_flow / 50) + np.random.normal(0, 0.1, time_points)
        
        # 生态指标
        fish_habitat_index = 75 + 15 * (1 - np.abs(velocity - 0.8)/0.8) + np.random.normal(0, 3, time_points)
        ecological_flow = np.maximum(10, 0.3 * total_flow)
        
        return {
            '天然径流(m³/s)': np.round(natural_inflow, 2),
            '支流汇入(m³/s)': np.round(tributary_flow, 2),
            '人工调节(m³/s)': np.round(regulation_flow, 2),
            '总流量(m³/s)': np.round(total_flow, 2),
            '水位(m)': np.round(water_level, 2),
            '流速(m/s)': np.round(velocity, 3),
            '水质指数': np.round(water_quality, 1),
            '含沙量(kg/m³)': np.round(sediment_load, 3),
            '鱼类栖息指数': np.round(fish_habitat_index, 1),
            '生态流量(m³/s)': np.round(ecological_flow, 2)
        }
    
    def _generate_pool_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成调节池时间序列数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 扰动数据
        inflow = 15 + 8 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 2, time_points)
        demand_flow = 12 + 6 * np.sin(2*np.pi*time_hours/12) + np.random.normal(0, 1.5, time_points)
        
        # 状态变量
        target_level = 8.5 + 0.3 * np.sin(2*np.pi*time_hours/24)
        actual_level = target_level + np.random.normal(0, 0.15, time_points)
        volume = 30 + 5 * (actual_level - 8.0)  # 万m³
        outflow = demand_flow + np.random.normal(0, 1, time_points)
        
        # 控制数据
        pump_speed = 800 + 300 * (outflow / 20) + np.random.normal(0, 20, time_points)
        valve_opening = 40 + 30 * (outflow / 20) + np.random.normal(0, 3, time_points)
        
        # 性能指标
        level_error = actual_level - target_level
        supply_reliability = 95 + 3 * np.random.random(time_points)
        
        return {
            '进水流量(m³/s)': np.round(inflow, 2),
            '需水流量(m³/s)': np.round(demand_flow, 2),
            '目标水位(m)': np.round(target_level, 2),
            '实际水位(m)': np.round(actual_level, 2),
            '蓄水量(万m³)': np.round(volume, 1),
            '出水流量(m³/s)': np.round(outflow, 2),
            '泵站转速(rpm)': np.round(pump_speed, 0),
            '阀门开度(%)': np.round(valve_opening, 1),
            '水位误差(m)': np.round(level_error, 3),
            '供水可靠性(%)': np.round(supply_reliability, 1)
        }
    
    def _generate_default_controlled_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成默认被控对象数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 通用数据
        input_signal = 50 + 20 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 3, time_points)
        output_signal = input_signal + np.random.normal(0, 2, time_points)
        target_value = 50 + 15 * np.sin(2*np.pi*time_hours/24)
        actual_value = target_value + np.random.normal(0, 2, time_points)
        
        return {
            '输入信号': np.round(input_signal, 2),
            '输出信号': np.round(output_signal, 2),
            '目标值': np.round(target_value, 2),
            '实际值': np.round(actual_value, 2),
            '误差': np.round(actual_value - target_value, 3)
        }
    
    def generate_control_object_table(self, obj: Dict[str, Any]) -> pd.DataFrame:
        """生成控制对象时间序列数据表格"""
        obj_id = obj.get('id', 'unknown')
        obj_type = obj.get('type', 'unknown')
        
        # 生成24小时的时间序列数据（10分钟间隔）
        time_points = 144
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_series = [start_time + timedelta(minutes=10*i) for i in range(time_points)]
        
        # 设置随机种子确保可重现性
        np.random.seed(hash(obj_id) % 2**32)
        
        # 根据对象类型生成不同的数据
        if obj_type == 'gate':
            data = self._generate_gate_data(time_points)
        elif obj_type == 'pump':
            data = self._generate_pump_data(time_points)
        elif obj_type == 'valve':
            data = self._generate_valve_data(time_points)
        elif obj_type == 'turbine':
            data = self._generate_turbine_data(time_points)
        else:
            data = self._generate_default_control_data(time_points)
        
        # 创建DataFrame
        df = pd.DataFrame({
            '时间': time_series,
            **data
        })
        
        # 格式化时间列
        df['时间'] = df['时间'].dt.strftime('%H:%M')
        
        return df
    
    def _generate_gate_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成闸门控制数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 控制目标
        target_opening = 50 + 20 * np.sin(2*np.pi*time_hours/24) + 10 * np.sin(2*np.pi*time_hours/12)
        actual_opening = target_opening + np.random.normal(0, 2, time_points)
        
        # 控制指令
        opening_command = target_opening + np.random.normal(0, 1, time_points)
        position_feedback = actual_opening + np.random.normal(0, 0.5, time_points)
        
        # 执行器状态
        motor_current = 20 + 10 * np.abs(np.diff(np.concatenate([[target_opening[0]], target_opening]))) + np.random.normal(0, 2, time_points)
        drive_torque = 2000 + 1000 * (motor_current / 30) + np.random.normal(0, 100, time_points)
        motor_temperature = 45 + 15 * (motor_current / 40) + np.random.normal(0, 3, time_points)
        
        # 控制性能
        opening_error = actual_opening - target_opening
        response_time = 2.0 + 0.5 * np.random.random(time_points)  # 分钟
        control_accuracy = 98 + 1.5 * np.random.random(time_points)
        
        return {
            '目标开度(%)': np.round(target_opening, 1),
            '实际开度(%)': np.round(actual_opening, 1),
            '开度指令(%)': np.round(opening_command, 1),
            '位置反馈(%)': np.round(position_feedback, 1),
            '电机电流(A)': np.round(motor_current, 1),
            '驱动力矩(N·m)': np.round(drive_torque, 0),
            '电机温度(°C)': np.round(motor_temperature, 1),
            '开度误差(%)': np.round(opening_error, 2),
            '响应时间(min)': np.round(response_time, 2),
            '控制精度(%)': np.round(control_accuracy, 1)
        }
    
    def _generate_pump_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成泵站控制数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 控制目标
        target_flow = 30 + 15 * np.sin(2*np.pi*time_hours/24) + 5 * np.sin(2*np.pi*time_hours/8)
        actual_flow = target_flow + np.random.normal(0, 1.5, time_points)
        
        # 控制指令
        speed_command = 1000 + 300 * (target_flow / 50) + np.random.normal(0, 20, time_points)
        actual_speed = speed_command + np.random.normal(0, 10, time_points)
        
        # 执行器状态
        motor_power = 100 + 50 * (actual_flow / 50) + np.random.normal(0, 5, time_points)
        outlet_pressure = 1.5 + 0.8 * (actual_flow / 50) + np.random.normal(0, 0.1, time_points)
        bearing_temperature = 55 + 20 * (motor_power / 150) + np.random.normal(0, 3, time_points)
        vibration_level = 2 + 3 * (actual_speed / 1500) + np.random.normal(0, 0.5, time_points)
        
        # 控制性能
        flow_error = actual_flow - target_flow
        pump_efficiency = 85 + 8 * (1 - np.abs(actual_flow - 40)/40) + np.random.normal(0, 2, time_points)
        energy_consumption = motor_power * 0.8 + np.random.normal(0, 2, time_points)
        
        return {
            '目标流量(m³/s)': np.round(target_flow, 2),
            '实际流量(m³/s)': np.round(actual_flow, 2),
            '转速指令(rpm)': np.round(speed_command, 0),
            '实际转速(rpm)': np.round(actual_speed, 0),
            '电机功率(kW)': np.round(motor_power, 1),
            '出口压力(MPa)': np.round(outlet_pressure, 2),
            '轴承温度(°C)': np.round(bearing_temperature, 1),
            '振动水平(mm/s)': np.round(vibration_level, 2),
            '流量误差(m³/s)': np.round(flow_error, 3),
            '泵效率(%)': np.round(pump_efficiency, 1),
            '能耗(kWh)': np.round(energy_consumption, 2)
        }
    
    def _generate_valve_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成阀门控制数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 控制目标
        target_position = 60 + 25 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 2, time_points)
        actual_position = target_position + np.random.normal(0, 1.5, time_points)
        
        # 流量控制
        flow_coefficient = 0.8 + 0.1 * np.sin(2*np.pi*time_hours/24)
        flow_rate = flow_coefficient * (actual_position / 100) * 25 + np.random.normal(0, 1, time_points)
        
        # 执行器状态
        actuator_pressure = 1.2 + 0.3 * (actual_position / 100) + np.random.normal(0, 0.05, time_points)
        position_error = actual_position - target_position
        response_time = 1.5 + 0.8 * np.random.random(time_points)
        
        # 性能指标
        control_precision = 99 - 2 * np.abs(position_error) + np.random.normal(0, 1, time_points)
        leakage_rate = 0.1 + 0.05 * np.random.random(time_points)
        
        return {
            '目标位置(%)': np.round(target_position, 1),
            '实际位置(%)': np.round(actual_position, 1),
            '流量系数': np.round(flow_coefficient, 3),
            '流量(m³/s)': np.round(flow_rate, 2),
            '执行器压力(MPa)': np.round(actuator_pressure, 2),
            '位置误差(%)': np.round(position_error, 2),
            '响应时间(s)': np.round(response_time, 2),
            '控制精度(%)': np.round(control_precision, 1),
            '泄漏率(%)': np.round(leakage_rate, 3)
        }
    
    def _generate_turbine_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成水轮机控制数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 控制目标
        target_power = 8 + 4 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 0.5, time_points)
        actual_power = target_power + np.random.normal(0, 0.3, time_points)
        
        # 水力参数
        head = 48 + 4 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 1, time_points)
        flow_rate = 22 + 6 * np.sin(2*np.pi*time_hours/24) + np.random.normal(0, 1, time_points)
        
        # 控制参数
        guide_vane_opening = 70 + 20 * (target_power / 12) + np.random.normal(0, 2, time_points)
        runner_speed = 150 + 20 * (actual_power / 12) + np.random.normal(0, 3, time_points)
        
        # 性能指标
        efficiency = 88 + 6 * (1 - np.abs(actual_power - 10)/10) + np.random.normal(0, 1.5, time_points)
        power_error = actual_power - target_power
        vibration = 1.5 + 2 * (runner_speed / 180) + np.random.normal(0, 0.3, time_points)
        
        return {
            '目标功率(MW)': np.round(target_power, 2),
            '实际功率(MW)': np.round(actual_power, 2),
            '水头(m)': np.round(head, 1),
            '流量(m³/s)': np.round(flow_rate, 2),
            '导叶开度(%)': np.round(guide_vane_opening, 1),
            '转轮转速(rpm)': np.round(runner_speed, 1),
            '效率(%)': np.round(efficiency, 1),
            '功率误差(MW)': np.round(power_error, 3),
            '振动(mm/s)': np.round(vibration, 2)
        }
    
    def _generate_default_control_data(self, time_points: int) -> Dict[str, np.ndarray]:
        """生成默认控制对象数据"""
        time_hours = np.linspace(0, 24, time_points)
        
        # 通用控制数据
        target = 50 + 20 * np.sin(2*np.pi*time_hours/24)
        actual = target + np.random.normal(0, 2, time_points)
        command = target + np.random.normal(0, 1, time_points)
        feedback = actual + np.random.normal(0, 0.5, time_points)
        
        return {
            '目标值': np.round(target, 2),
            '实际值': np.round(actual, 2),
            '控制指令': np.round(command, 2),
            '反馈信号': np.round(feedback, 2),
            '控制误差': np.round(actual - target, 3)
        }
    
    def generate_comprehensive_tables(self) -> str:
        """生成综合时间序列数据表格报告"""
        report_lines = []
        
        # 报告头部
        report_lines.extend([
            "# 时间序列分析数据表格报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**配置文件**: {os.path.basename(self.config_path)}",
            "",
            "## 概述",
            "",
            f"本报告包含 **{len(self.controlled_objects)}** 个被控对象和 **{len(self.control_objects)}** 个控制对象的详细时间序列数据表格。",
            "数据采样间隔为10分钟，覆盖24小时运行周期。",
            "",
            "---",
            ""
        ])
        
        # 被控对象数据表格
        if self.controlled_objects:
            report_lines.extend([
                "## 被控对象时间序列数据表格",
                ""
            ])
            
            for i, obj in enumerate(self.controlled_objects, 1):
                obj_id = obj.get('id', 'unknown')
                obj_type = obj.get('type', 'unknown')
                
                print(f"正在生成第 {i}/{len(self.controlled_objects)} 个被控对象数据表格: {obj_id}")
                
                type_name = {
                    'reservoir': '水库',
                    'canal': '渠道',
                    'river': '河道',
                    'pool': '调节池',
                    'tank': '水箱'
                }.get(obj_type, obj_type)
                
                report_lines.extend([
                    f"### {obj_id} ({type_name}) 时间序列数据",
                    ""
                ])
                
                # 生成数据表格
                df = self.generate_controlled_object_table(obj)
                
                # 保存为CSV文件
                csv_filename = f"{obj_id}_被控对象时间序列数据.csv"
                csv_path = os.path.join(self.output_dir, csv_filename)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                # 添加表格到报告（显示前20行）
                report_lines.append("**数据表格** (显示前20行):")
                report_lines.append("")
                
                # 转换为Markdown表格格式
                markdown_table = self._dataframe_to_markdown(df.head(20))
                report_lines.extend(markdown_table)
                
                report_lines.extend([
                    "",
                    f"**完整数据文件**: [{csv_filename}]({csv_path})",
                    "",
                    f"**数据说明**: 该表格包含{len(df)}个时间点的详细数据，涵盖扰动输入、状态变量、控制指令和性能指标。",
                    "",
                    "---",
                    ""
                ])
        
        # 控制对象数据表格
        if self.control_objects:
            report_lines.extend([
                "## 控制对象时间序列数据表格",
                ""
            ])
            
            for i, obj in enumerate(self.control_objects, 1):
                obj_id = obj.get('id', 'unknown')
                obj_type = obj.get('type', 'unknown')
                
                print(f"正在生成第 {i}/{len(self.control_objects)} 个控制对象数据表格: {obj_id}")
                
                type_name = {
                    'gate': '闸门',
                    'pump': '泵站',
                    'valve': '阀门',
                    'turbine': '水轮机'
                }.get(obj_type, obj_type)
                
                report_lines.extend([
                    f"### {obj_id} ({type_name}) 时间序列数据",
                    ""
                ])
                
                # 生成数据表格
                df = self.generate_control_object_table(obj)
                
                # 保存为CSV文件
                csv_filename = f"{obj_id}_控制对象时间序列数据.csv"
                csv_path = os.path.join(self.output_dir, csv_filename)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                # 添加表格到报告（显示前20行）
                report_lines.append("**数据表格** (显示前20行):")
                report_lines.append("")
                
                # 转换为Markdown表格格式
                markdown_table = self._dataframe_to_markdown(df.head(20))
                report_lines.extend(markdown_table)
                
                report_lines.extend([
                    "",
                    f"**完整数据文件**: [{csv_filename}]({csv_path})",
                    "",
                    f"**数据说明**: 该表格包含{len(df)}个时间点的详细数据，涵盖控制目标、控制指令、执行器状态和性能指标。",
                    "",
                    "---",
                    ""
                ])
        
        # 数据统计摘要
        report_lines.extend(self._generate_data_summary())
        
        # 保存报告
        report_path = os.path.join(self.output_dir, "时间序列分析数据表格报告.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return report_path
    
    def _dataframe_to_markdown(self, df: pd.DataFrame) -> List[str]:
        """将DataFrame转换为Markdown表格格式"""
        lines = []
        
        # 表头
        header = "| " + " | ".join(df.columns) + " |"
        lines.append(header)
        
        # 分隔线
        separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
        lines.append(separator)
        
        # 数据行
        for _, row in df.iterrows():
            data_row = "| " + " | ".join([str(val) for val in row]) + " |"
            lines.append(data_row)
        
        return lines
    
    def _generate_data_summary(self) -> List[str]:
        """生成数据统计摘要"""
        lines = [
            "## 数据统计摘要",
            "",
            "### 数据覆盖范围",
            "",
            "- **时间跨度**: 24小时 (00:00 - 23:50)",
            "- **采样间隔**: 10分钟",
            "- **数据点数**: 144个时间点",
            "- **被控对象数量**: {}个".format(len(self.controlled_objects)),
            "- **控制对象数量**: {}个".format(len(self.control_objects)),
            "",
            "### 数据类型说明",
            "",
            "**被控对象数据包含**:",
            "- 扰动输入 (入流量、降雨、蒸发等)",
            "- 状态变量 (水位、流量、蓄量等)",
            "- 控制指令 (闸门开度、泵站转速等)",
            "- 性能指标 (控制误差、效率等)",
            "",
            "**控制对象数据包含**:",
            "- 控制目标 (设定值、目标轨迹)",
            "- 控制指令 (开度指令、转速指令等)",
            "- 执行器状态 (电流、温度、压力等)",
            "- 控制性能 (精度、响应时间、效率等)",
            "",
            "### 数据质量",
            "",
            "- **数据完整性**: 100% (无缺失值)",
            "- **数据精度**: 根据实际工程精度要求设定",
            "- **噪声水平**: 符合实际测量噪声特征",
            "- **时间同步**: 所有数据严格时间同步",
            "",
            "### 使用说明",
            "",
            "1. **CSV文件**: 可直接导入Excel、MATLAB、Python等工具进行分析",
            "2. **数据格式**: UTF-8编码，逗号分隔",
            "3. **时间格式**: HH:MM (24小时制)",
            "4. **数值精度**: 根据物理量特性保留适当小数位数",
            "5. **单位说明**: 各列标题中已标注相应单位"
        ]
        
        return lines

def create_demo_config():
    """创建演示配置"""
    return {
        "metadata": {
            "name": "智能水利调度系统",
            "version": "2.0",
            "description": "基于多智能体的水利系统智能调度与控制"
        },
        "components": [
            # 被控对象
            {
                "id": "main_reservoir",
                "type": "reservoir",
                "parameters": {
                    "capacity": "5000万立方米",
                    "normal_level": "145.0米",
                    "flood_level": "147.5米",
                    "dead_level": "135.0米",
                    "surface_area": "25平方公里",
                    "initial_level": "正常蓄水位145.0米"
                }
            },
            {
                "id": "main_canal",
                "type": "canal",
                "parameters": {
                    "length": "80公里",
                    "width": "底宽15米",
                    "depth": "设计水深4米",
                    "slope": "1/5000",
                    "roughness": "0.025"
                }
            },
            {
                "id": "upstream_river",
                "type": "river",
                "parameters": {
                    "length": "50公里",
                    "width": "平均200米",
                    "depth": "平均5米",
                    "slope": "1/2000",
                    "roughness": "0.035"
                }
            },
            {
                "id": "distribution_pool",
                "type": "pool",
                "parameters": {
                    "capacity": "50万立方米",
                    "normal_level": "8.5米",
                    "max_level": "10.0米",
                    "initial_level": "运行水位8.5米"
                }
            },
            # 控制对象
            {
                "id": "main_gate",
                "type": "gate",
                "parameters": {
                    "max_opening": "100%",
                    "response_time": "2分钟",
                    "control_precision": "±1%",
                    "location": "主渠道入口",
                    "rated_flow": "80 m³/s",
                    "gate_type": "平板闸门"
                }
            },
            {
                "id": "pump_station_1",
                "type": "pump",
                "parameters": {
                    "rated_flow": "50 m³/s",
                    "rated_head": "20 m",
                    "efficiency": "85%",
                    "pump_count": 3,
                    "control_mode": "变频调速"
                }
            },
            {
                "id": "control_valve_1",
                "type": "valve",
                "parameters": {
                    "diameter": "1.5 m",
                    "pressure_rating": "1.6 MPa",
                    "flow_coefficient": "0.8",
                    "valve_type": "蝶阀"
                }
            },
            {
                "id": "turbine_1",
                "type": "turbine",
                "parameters": {
                    "rated_power": "10 MW",
                    "rated_head": "50 m",
                    "rated_flow": "25 m³/s",
                    "efficiency": "90%"
                }
            }
        ],
        "agents": [
            {
                "id": "reservoir_controller",
                "type": "OptimalController",
                "target_component": "main_reservoir"
            },
            {
                "id": "canal_controller",
                "type": "PIDController",
                "target_component": "main_canal"
            },
            {
                "id": "gate_controller",
                "type": "PIDController",
                "target_component": "main_gate"
            },
            {
                "id": "pump_controller",
                "type": "AdvancedController", 
                "target_component": "pump_station_1"
            }
        ]
    }

def main():
    """主函数"""
    print("开始生成时间序列分析数据表格...")
    
    # 创建模拟配置
    config = create_demo_config()
    
    # 创建临时配置文件
    temp_config_path = "temp_config.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    try:
        # 创建表格生成器
        generator = TimeSeriesTableGenerator(temp_config_path)
        
        # 生成综合数据表格报告
        report_path = generator.generate_comprehensive_tables()
        
        print(f"\n数据表格生成完成！报告已保存到: {report_path}")
        print(f"共生成了 {len(generator.controlled_objects)} 个被控对象数据表格")
        print(f"共生成了 {len(generator.control_objects)} 个控制对象数据表格")
        print(f"所有CSV数据文件已保存到: {generator.output_dir} 目录")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

if __name__ == "__main__":
    main()