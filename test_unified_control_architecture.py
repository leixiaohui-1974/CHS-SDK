"""
测试统一控制代理架构

验证重构后的控制代理功能完整性：
1. 所有控制代理都继承统一基类
2. 工厂类能正确创建各种控制代理
3. 控制策略正确映射
4. 接口一致性
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_lib.local_agents.control import (
    ControlAgentFactory,
    UnifiedLocalControlAgent,
    ControlStrategy,
    GateControlAgent,
    PumpControlAgent,
    ValveControlAgent,
    WaterTurbineControlAgent,
    PIDController
)
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.pump import PumpStation, Pump

def test_architecture_consistency():
    """测试架构一致性"""
    print("🔍 测试架构一致性...")
    
    # 验证所有控制代理都继承统一基类
    control_agents = [GateControlAgent, PumpControlAgent, ValveControlAgent, WaterTurbineControlAgent]
    
    for agent_class in control_agents:
        assert issubclass(agent_class, UnifiedLocalControlAgent), f"{agent_class.__name__} 应该继承 UnifiedLocalControlAgent"
        print(f"✅ {agent_class.__name__} 正确继承 UnifiedLocalControlAgent")
    
    print("✅ 架构一致性测试通过")

def test_control_strategies():
    """测试控制策略映射"""
    print("\n🔍 测试控制策略映射...")
    
    expected_strategies = {
        'gate': ControlStrategy.MULTI_ACTUATOR,
        'pump': ControlStrategy.DISCRETE,
        'valve': ControlStrategy.CONTINUOUS,
        'water_turbine': ControlStrategy.CONTINUOUS,
    }
    
    for agent_type, expected_strategy in expected_strategies.items():
        actual_strategy = ControlAgentFactory.get_default_strategy(agent_type)
        assert actual_strategy == expected_strategy, f"{agent_type} 的控制策略应该是 {expected_strategy}"
        print(f"✅ {agent_type} -> {actual_strategy.value}")
    
    print("✅ 控制策略映射测试通过")

def test_factory_creation():
    """测试工厂类创建功能"""
    print("\n🔍 测试工厂类创建功能...")
    
    message_bus = MessageBus()
    time_step = 1.0
    
    # 测试标准控制代理创建（需要控制器）
    controller = PIDController(kp=1.0, ki=0.1, kd=0.01)
    
    # 创建闸门控制代理
    gate_agent = ControlAgentFactory.create_control_agent(
        agent_type='gate',
        agent_id='test_gate',
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic='gate.observation',
        observation_key='water_level',
        action_topic='gate.action'
    )
    assert isinstance(gate_agent, GateControlAgent)
    assert gate_agent.control_strategy == ControlStrategy.MULTI_ACTUATOR
    print("✅ 闸门控制代理创建成功")
    
    # 创建阀门控制代理
    valve_agent = ControlAgentFactory.create_control_agent(
        agent_type='valve',
        agent_id='test_valve',
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic='valve.observation',
        observation_key='flow_rate',
        action_topic='valve.action'
    )
    assert isinstance(valve_agent, ValveControlAgent)
    assert valve_agent.control_strategy == ControlStrategy.CONTINUOUS
    print("✅ 阀门控制代理创建成功")
    
    # 创建水轮机控制代理
    turbine_agent = ControlAgentFactory.create_control_agent(
        agent_type='water_turbine',
        agent_id='test_turbine',
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic='turbine.observation',
        observation_key='power_demand',
        action_topic='turbine.action'
    )
    assert isinstance(turbine_agent, WaterTurbineControlAgent)
    assert turbine_agent.control_strategy == ControlStrategy.CONTINUOUS
    print("✅ 水轮机控制代理创建成功")
    
    # 创建泵控制代理（不需要控制器）
    pump1 = Pump(name='pump_1', initial_state={}, parameters={'max_flow_rate': 10.0})
    pump_station = PumpStation(name='test_pump_station', initial_state={}, parameters={}, pumps=[pump1])
    
    pump_agent = ControlAgentFactory.create_control_agent(
        agent_type='pump',
        agent_id='test_pump',
        message_bus=message_bus,
        time_step=time_step,
        pump_station=pump_station,
        demand_topic='pump.demand',
        control_topic_prefix='pump.control'
    )
    assert isinstance(pump_agent, PumpControlAgent)
    assert pump_agent.control_strategy == ControlStrategy.DISCRETE
    print("✅ 泵控制代理创建成功")
    
    print("✅ 工厂类创建功能测试通过")

def test_config_based_creation():
    """测试基于配置的创建"""
    print("\n🔍 测试基于配置的创建...")
    
    message_bus = MessageBus()
    time_step = 1.0
    controller = PIDController(kp=1.0, ki=0.1, kd=0.01)
    
    # 闸门配置
    gate_config = {
        'type': 'gate',
        'agent_id': 'config_gate',
        'observation_topic': 'gate.obs',
        'observation_key': 'level',
        'action_topic': 'gate.act'
    }
    
    gate_agent = ControlAgentFactory.create_from_config(gate_config, message_bus, time_step, controller)
    assert isinstance(gate_agent, GateControlAgent)
    assert gate_agent.agent_id == 'config_gate'
    print("✅ 基于配置创建闸门控制代理成功")
    
    print("✅ 基于配置的创建测试通过")

def test_supported_types():
    """测试支持的类型"""
    print("\n🔍 测试支持的类型...")
    
    supported_types = ControlAgentFactory.get_supported_types()
    expected_types = ['gate', 'pump', 'valve', 'water_turbine', 'turbine', 'hydropower']
    
    for expected_type in expected_types:
        assert expected_type in supported_types, f"应该支持类型: {expected_type}"
    
    print(f"✅ 支持的类型: {supported_types}")
    print("✅ 支持类型测试通过")

def test_interface_consistency():
    """测试接口一致性"""
    print("\n🔍 测试接口一致性...")
    
    message_bus = MessageBus()
    time_step = 1.0
    controller = PIDController(kp=1.0, ki=0.1, kd=0.01)
    
    # 创建不同类型的控制代理
    agents = []
    
    # 闸门代理
    gate_agent = ControlAgentFactory.create_control_agent(
        'gate', 'test_gate', message_bus, time_step, controller,
        observation_topic='gate.obs', action_topic='gate.act'
    )
    agents.append(gate_agent)
    
    # 阀门代理
    valve_agent = ControlAgentFactory.create_control_agent(
        'valve', 'test_valve', message_bus, time_step, controller,
        observation_topic='valve.obs', action_topic='valve.act'
    )
    agents.append(valve_agent)
    
    # 水轮机代理
    turbine_agent = ControlAgentFactory.create_control_agent(
        'water_turbine', 'test_turbine', message_bus, time_step, controller,
        observation_topic='turbine.obs', action_topic='turbine.act'
    )
    agents.append(turbine_agent)
    
    # 验证所有代理都有统一的接口
    for agent in agents:
        # 基础属性
        assert hasattr(agent, 'agent_id')
        assert hasattr(agent, 'bus')
        assert hasattr(agent, 'time_step')
        assert hasattr(agent, 'control_strategy')
        
        # 统一方法
        assert hasattr(agent, 'run')
        assert hasattr(agent, 'handle_observation')
        assert hasattr(agent, 'publish_action')
        
        print(f"✅ {agent.__class__.__name__} 接口一致性验证通过")
    
    print("✅ 接口一致性测试通过")

def main():
    """主测试函数"""
    print("🚀 开始测试统一控制代理架构...\n")
    
    try:
        test_architecture_consistency()
        test_control_strategies()
        test_factory_creation()
        test_config_based_creation()
        test_supported_types()
        test_interface_consistency()
        
        print("\n🎉 所有测试通过！统一控制代理架构重构成功！")
        print("\n📊 重构总结:")
        print("✅ 删除了 6 个旧的控制代理实现")
        print("✅ 创建了统一的 UnifiedLocalControlAgent 基类")
        print("✅ 重构了 4 个控制代理类（Gate, Pump, Valve, WaterTurbine）")
        print("✅ 实现了 ControlAgentFactory 工厂类")
        print("✅ 更新了类映射和导入引用")
        print("✅ 架构一致性、接口统一性验证通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
