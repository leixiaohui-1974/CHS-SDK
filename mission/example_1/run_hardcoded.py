#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1 - 硬编码入口
演示纯物理组件（渠道和闸门）动态行为

这个脚本直接在代码中定义参数，集成了通用调试工具。
"""

import math
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入核心组件
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.gate import Gate

# 导入通用调试工具
from core_lib.debug.log_manager import get_log_manager, setup_logging
from core_lib.debug.debug_collector import collect_debug_data
import time

def run_physical_model_example():
    """
    演示纯物理组件（渠道和闸门）的动态行为
    集成了完整的调试和监控功能
    """
    # 设置调试工具
    log_config = {
        'level': 'INFO',
        'handlers': {
            'console': {
                'type': 'console',
                'level': 'INFO'
            },
            'file': {
                'type': 'file',
                'level': 'INFO',
                'file': 'logs/mission_example_1_hardcoded.log'
            }
        }
    }
    setup_logging(log_config)
    logger = get_log_manager()
    
    logger.info("=== Mission Example 1 - 物理模型仿真开始 ===")
    logger.info("演示纯物理组件（渠道和闸门）的动态行为")
    
    # 开始计时
    start_time = time.time()
    
    # 1. 初始化物理组件
    logger.info("初始化物理组件...")
    
    # 渠道参数
    canal_params = {
        'bottom_width': 20.0,   # 渠底宽度 (m)
        'length': 1000.0,       # 渠道长度 (m)
        'slope': 0.001,         # 坡度
        'side_slope_z': 2.0,    # 边坡系数 (z:1)
        'manning_n': 0.025      # 曼宁糙率系数
    }
    
    # 初始状态
    initial_canal_state = {
        'volume': 50000,        # 初始蓄水量 (m^3)
        'water_level': 2.0,     # 初始水位 (m)
        'outflow': 0            # 初始出流量 (m^3/s)
    }
    
    upstream_canal = UnifiedCanal(
        model_type='integral',
        name="upstream_canal",
        initial_state=initial_canal_state,
        parameters=canal_params
    )
    
    # 闸门参数
    gate_params = {
        'discharge_coefficient': 0.8, # 流量系数
        'width': 10.0,                # 闸门宽度 (m)
        'max_opening': 3.0,           # 最大开度 (m)
        'max_rate_of_change': 0.1     # 开度最大变化速率 (m/s)
    }
    
    # 初始状态
    initial_gate_state = {
        'opening': 0.2, # 初始开度 (m)
        'outflow': 0
    }
    
    control_gate = Gate(
        name="control_gate",
        initial_state=initial_gate_state,
        parameters=gate_params
    )
    
    logger.info(f"渠道初始化完成: 长度={canal_params['length']}m, 宽度={canal_params['bottom_width']}m")
    logger.info(f"闸门初始化完成: 宽度={gate_params['width']}m, 初始开度={initial_gate_state['opening']}m")
    
    # 收集初始化数据
    collect_debug_data(
        data_type='component_initialization',
        name='initialization_params',
        value={
            'canal_params': canal_params,
            'gate_params': gate_params,
            'initial_canal_state': initial_canal_state,
            'initial_gate_state': initial_gate_state
        },
        source='mission_example_1_hardcoded'
    )
    
    # 2. 仿真循环设置
    dt = 10.0  # 时间步长 (s)
    duration = 1000  # 仿真总时长 (s)
    num_steps = int(duration / dt)
    inflow = 10.0  # 初始入流量 (m^3/s)
    
    # 存储历史数据用于验证
    history = []
    
    logger.info(f"仿真参数: 时长={duration}s, 步长={dt}s, 总步数={num_steps}")
    logger.info(f"初始入流: {inflow} m^3/s, 闸门开度固定为: {initial_gate_state['opening']} m")
    
    print(f"\n开始仿真... 时长: {duration}s, 步长: {dt}s")
    print(f"初始入流: {inflow} m^3/s, 闸门开度固定为: {initial_gate_state['opening']} m")
    
    # 3. 仿真主循环
    simulation_start = time.time()
    for i in range(num_steps):
        current_time = i * dt
        
        # 在仿真一半时，模拟阶跃式入流变化
        if current_time >= duration / 2:
            if inflow != 20.0:  # 只在第一次变化时记录
                logger.info(f"时间 {current_time}s: 入流从 {inflow} 变化为 20.0 m^3/s")
            inflow = 20.0
        
        # 获取渠道当前水位作为闸门的上游水头
        canal_state = upstream_canal.get_state()
        canal_water_level = canal_state['water_level']
        
        # 计算闸门出流量
        gate_action = {
            'upstream_head': canal_water_level,
            'downstream_head': 0,
            'control_signal': initial_gate_state['opening']
        }
        gate_state = control_gate.step(gate_action, dt)
        gate_outflow = gate_state['outflow']
        
        # 更新渠道蓄水量
        canal_volume = canal_state['volume']
        new_canal_volume = canal_volume + (inflow - gate_outflow) * dt
        new_canal_volume = max(0, new_canal_volume)
        
        # 根据蓄水量重新计算水位
        L = upstream_canal._params.get('length', 1000.0)
        b = upstream_canal._params.get('bottom_width', 10.0)
        z = upstream_canal._params.get('side_slope_z', 1.0)
        
        c_quad = -new_canal_volume / L if L > 0 else 0
        
        if z == 0:  # 矩形渠道
            new_water_level = new_canal_volume / (b * L) if (b * L) > 0 else 0
        else:  # 梯形渠道
            discriminant = b**2 - 4 * z * c_quad
            if discriminant >= 0:
                new_water_level = (-b + math.sqrt(discriminant)) / (2 * z)
            else:
                new_water_level = 0
        
        # 更新渠道状态
        new_canal_state = {
            'volume': new_canal_volume,
            'water_level': new_water_level,
            'outflow': gate_outflow
        }
        upstream_canal.set_state(new_canal_state)
        
        # 记录历史数据
        step_data = {
            'time': current_time,
            'inflow': inflow,
            'canal_water_level': new_water_level,
            'canal_volume': new_canal_volume,
            'gate_outflow': gate_outflow
        }
        history.append(step_data)
        
        # 收集调试数据（每5步收集一次）
        if i % 5 == 0:
            collect_debug_data(
                data_type='simulation_state',
                name=f'step_{i}',
                value=step_data,
                source='mission_example_1_hardcoded'
            )
        
        # 打印进度（每10步打印一次）
        if i % 10 == 0:
            output_msg = (f"Time: {current_time:5.1f}s | Inflow: {inflow:5.2f} | "
                        f"Canal Level: {new_water_level:5.3f}m | Gate Outflow: {gate_outflow:5.3f} m^3/s")
            print(output_msg)
            logger.debug(output_msg)
    
    print("\n仿真结束。")
    logger.info("仿真主循环完成")
    
    # 4. 验证结果
    logger.info("开始结果验证...")
    print("\n--- 结果验证 ---")
    
    level_before_change = history[int(num_steps / 2) - 1]['canal_water_level']
    level_after_change = history[-1]['canal_water_level']
    outflow_before_change = history[int(num_steps / 2) - 1]['gate_outflow']
    outflow_after_change = history[-1]['gate_outflow']
    
    validation_results = {
        'level_before_change': level_before_change,
        'level_after_change': level_after_change,
        'outflow_before_change': outflow_before_change,
        'outflow_after_change': outflow_after_change
    }
    
    print(f"入流变化前稳定水位: {level_before_change:.3f} m")
    print(f"入流变化前稳定出流: {outflow_before_change:.3f} m^3/s")
    print(f"入流变化后稳定水位: {level_after_change:.3f} m")
    print(f"入流变化后稳定出流: {outflow_after_change:.3f} m^3/s")
    
    logger.info(f"验证结果: {validation_results}")
    
    # 简单断言
    try:
        assert level_after_change > level_before_change, "入流增加后，水位应该上升"
        assert outflow_after_change > outflow_before_change, "入流增加后，出流应该增加"
        print("\n验证成功：水位和出流对入流变化做出了正确响应。")
        logger.info("验证成功：系统响应符合预期")
        
        # 收集验证结果
        collect_debug_data(
            data_type='validation_results',
            name='validation_success',
            value={
                'validation_passed': True,
                'results': validation_results
            },
            source='mission_example_1_hardcoded'
        )
        
    except AssertionError as e:
        error_msg = f"验证失败: {str(e)}"
        print(f"\n{error_msg}")
        logger.error(error_msg)
        
        # 收集验证失败数据
        collect_debug_data(
            data_type='validation_results',
            name='validation_failure',
            value={
                'validation_passed': False,
                'error': str(e),
                'results': validation_results
            },
            source='mission_example_1_hardcoded'
        )
        raise
    
    # 输出性能统计
    total_time = time.time() - start_time
    simulation_time = time.time() - simulation_start
    print("\n--- 性能统计 ---")
    print(f"总执行时间: {total_time:.3f}s")
    print(f"仿真循环时间: {simulation_time:.3f}s")
    print(f"平均每步时间: {simulation_time/num_steps:.6f}s")
    
    logger.info(f"性能统计 - 总时间: {total_time:.3f}s, 仿真时间: {simulation_time:.3f}s")
    logger.info("=== Mission Example 1 - 物理模型仿真完成 ===")

def main():
    """
    主入口函数
    """
    try:
        run_physical_model_example()
    except Exception as e:
        # 确保错误被记录
        logger = get_log_manager()
        logger.error(f"仿真执行失败: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()