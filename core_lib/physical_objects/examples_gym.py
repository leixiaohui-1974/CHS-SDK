"""
基于 Gymnasium 的物理对象使用示例

演示如何使用新的统一 Action 接口和 gymnasium 环境来控制各种物理对象。
"""

import numpy as np
from typing import Dict, Any
from core_lib.core.interfaces import State, Parameters

# 导入现有物理对象
from .valve import Valve
from .pump import Pump
from .reservoir import Reservoir
from .gate import Gate

# 导入新的 gymnasium 接口
from .base_gym import (
    ControlSignalAction, FlowControlAction, LevelControlAction, 
    StatusControlAction, MixedControlAction, ActionType
)
from .gym_adapter import (
    make_gym_compatible, create_typed_env, auto_create_env,
    detect_object_type
)


def example_valve_control():
    """示例：使用新接口控制阀门"""
    print("=== 阀门控制示例 ===")
    
    # 创建阀门实例
    valve_params = Parameters({
        'discharge_coefficient': 0.6,
        'diameter': 0.5,
        'max_opening': 1.0
    })
    valve_state = State({
        'opening': 0.5,
        'outflow': 0.0
    })
    
    valve = Valve("示例阀门", valve_state, valve_params)
    
    # 方式1：直接使用新的 Action 接口
    compatible_valve = make_gym_compatible(valve)
    
    # 使用不同类型的 Action
    actions = [
        ControlSignalAction(control_signal=0.8),  # 开度控制
        ControlSignalAction(control_signal=0.3),  # 减小开度
        ControlSignalAction(control_signal=1.0),  # 全开
    ]
    
    print("使用 ControlSignalAction 控制阀门:")
    for i, action in enumerate(actions):
        print(f"\n步骤 {i+1}: 设置开度为 {action.control_signal}")
        state = compatible_valve.step_with_action(action, 1.0)
        print(f"阀门状态: 开度={state['opening']:.2f}, 出流={state['outflow']:.2f}")
    
    # 方式2：使用 gymnasium 环境
    print("\n使用 Gymnasium 环境:")
    env = create_typed_env(valve, "valve")
    
    observation, info = env.reset()
    print(f"初始观测: {observation}")
    
    for step in range(3):
        action = env.action_space.sample()  # 随机动作
        observation, reward, terminated, truncated, info = env.step(action)
        print(f"步骤 {step+1}: 动作={action[0]:.2f}, 奖励={reward:.2f}")
        env.render()


def example_pump_control():
    """示例：使用新接口控制泵站"""
    print("\n=== 泵站控制示例 ===")
    
    # 创建泵站实例
    pump_params = Parameters({
        'max_flow': 50.0,
        'max_head': 30.0,
        'rated_power': 15.0,
        'max_efficiency': 0.85
    })
    pump_state = State({
        'status': 0,
        'outflow': 0.0,
        'power_draw': 0.0,
        'efficiency': 0.0
    })
    
    pump = Pump("示例泵站", pump_state, pump_params)
    compatible_pump = make_gym_compatible(pump)
    
    # 使用状态控制动作
    print("使用 StatusControlAction 控制泵站:")
    actions = [
        StatusControlAction(status=1),  # 开启
        MixedControlAction(status=1, upstream_level=20.0, downstream_level=10.0),  # 运行状态
        StatusControlAction(status=0),  # 关闭
    ]
    
    for i, action in enumerate(actions):
        print(f"\n步骤 {i+1}: {action}")
        state = compatible_pump.step_with_action(action, 1.0)
        print(f"泵站状态: 状态={state['status']}, 出流={state['outflow']:.2f}, "
              f"功率={state['power_draw']:.2f}, 效率={state['efficiency']:.2f}")
    
    # 使用 gymnasium 环境进行优化训练示例
    print("\nGymnasium 环境示例:")
    env = create_typed_env(pump, "pump")
    
    observation, info = env.reset()
    total_reward = 0
    
    for step in range(5):
        # 简单策略：基于当前状态决定动作
        if observation[0] < 0.5:  # 假设第一个观测值是状态
            action = 1  # 开启
        else:
            action = 0  # 关闭
            
        observation, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(f"步骤 {step+1}: 动作={action}, 奖励={reward:.2f}")
    
    print(f"总奖励: {total_reward:.2f}")


def example_reservoir_control():
    """示例：使用新接口控制水库"""
    print("\n=== 水库控制示例 ===")
    
    # 创建水库实例
    reservoir_params = Parameters({
        'surface_area': 1000000,  # 1 km²
        'max_volume': 50000000,   # 50 million m³
        'storage_curve': [
            [0, 0],
            [10, 10000000],
            [20, 35000000], 
            [30, 50000000]
        ]
    })
    reservoir_state = State({
        'water_level': 15.0,
        'volume': 20000000,
        'outflow': 0.0
    })
    
    reservoir = Reservoir("示例水库", reservoir_state, reservoir_params)
    compatible_reservoir = make_gym_compatible(reservoir)
    
    # 使用水位控制动作
    print("使用 LevelControlAction 和 FlowControlAction:")
    actions = [
        LevelControlAction(upstream_level=16.0, downstream_level=8.0),
        FlowControlAction(target_flow=25.0),
        MixedControlAction(upstream_level=14.0, target_flow=15.0),
    ]
    
    for i, action in enumerate(actions):
        print(f"\n步骤 {i+1}: {action}")
        state = compatible_reservoir.step_with_action(action, 3600)  # 1小时时间步
        print(f"水库状态: 水位={state['water_level']:.2f}m, "
              f"库容={state['volume']/1e6:.1f}M m³, 出流={state['outflow']:.2f}")


def example_mixed_control():
    """示例：混合控制多个物理对象"""
    print("\n=== 混合控制示例 ===")
    
    # 创建多个物理对象
    objects = []
    
    # 阀门
    valve = Valve("控制阀", State({'opening': 0.5, 'outflow': 0}),
                  Parameters({'discharge_coefficient': 0.6, 'diameter': 0.3}))
    
    # 泵站  
    pump = Pump("提升泵", State({'status': 0, 'outflow': 0}),
                Parameters({'max_flow': 30.0, 'max_head': 25.0}))
    
    objects = [valve, pump]
    
    # 为每个对象创建兼容包装器和环境
    compatible_objects = [make_gym_compatible(obj) for obj in objects]
    envs = [auto_create_env(obj) for obj in objects]
    
    print("检测到的对象类型:")
    for obj in objects:
        obj_type = detect_object_type(obj)
        print(f"- {obj.name}: {obj_type}")
    
    # 协调控制示例
    print("\n协调控制:")
    for step in range(3):
        print(f"\n=== 时间步 {step+1} ===")
        
        # 泵站控制：根据需求开关
        pump_action = StatusControlAction(status=1 if step % 2 == 0 else 0)
        pump_state = compatible_objects[1].step_with_action(pump_action, 1.0)
        print(f"泵站: {pump_action} -> 状态={pump_state['status']}, 出流={pump_state['outflow']:.2f}")
        
        # 阀门控制：根据泵站出流调节
        target_opening = 0.8 if pump_state['status'] > 0 else 0.3
        valve_action = ControlSignalAction(control_signal=target_opening)
        valve_state = compatible_objects[0].step_with_action(valve_action, 1.0)
        print(f"阀门: {valve_action} -> 开度={valve_state['opening']:.2f}, 出流={valve_state['outflow']:.2f}")


def example_backward_compatibility():
    """示例：向后兼容性测试"""
    print("\n=== 向后兼容性测试 ===")
    
    # 创建物理对象
    valve = Valve("兼容测试阀", State({'opening': 0.5}), Parameters({'diameter': 0.4}))
    compatible_valve = make_gym_compatible(valve)
    
    print("测试不同调用方式的兼容性:")
    
    # 方式1：原有字典接口
    old_action = {'control_signal': 0.7}
    state1 = compatible_valve.step(old_action, 1.0)
    print(f"原有接口: {old_action} -> 开度={state1['opening']:.2f}")
    
    # 方式2：新的 BaseAction 接口
    new_action = ControlSignalAction(control_signal=0.9)
    state2 = compatible_valve.step(new_action, 1.0)
    print(f"新接口: {new_action} -> 开度={state2['opening']:.2f}")
    
    # 方式3：直接数值 (自动转换为 ControlSignalAction)
    direct_action = 0.2
    state3 = compatible_valve.step(direct_action, 1.0)
    print(f"直接数值: {direct_action} -> 开度={state3['opening']:.2f}")
    
    print("✓ 所有接口都正常工作!")


def run_all_examples():
    """运行所有示例"""
    print("🚀 运行基于 Gymnasium 的物理对象控制示例\n")
    
    try:
        example_valve_control()
        example_pump_control() 
        example_reservoir_control()
        example_mixed_control()
        example_backward_compatibility()
        
        print("\n✅ 所有示例运行完成!")
        print("\n📋 新架构特点:")
        print("1. 统一的 Action 接口 - 所有物理对象使用相同的动作定义")
        print("2. 类型安全 - 动作验证确保参数正确性")
        print("3. Gymnasium 兼容 - 支持标准强化学习接口")
        print("4. 向后兼容 - 现有代码无需修改")
        print("5. 类型特化 - 为不同对象类型提供专门优化")
        
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
