#!/usr/bin/env python3
"""
适配器功能验证脚本

验证所有旧Agent类通过适配器能够正常工作
确保向后兼容性完整
"""
import sys
import time
import warnings
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core_lib.core.event_bus import get_global_event_bus
from core_lib.core.registry import register_all_agents

def test_data_source_adapters():
    """测试数据源适配器"""
    print("=== 测试数据源适配器 ===")
    
    try:
        # 测试 CsvReaderAgent 适配器
        from core_lib.core.new_agents.service_agents.data.unified_data_source import CsvReaderAgentAdapter
        
        # 创建临时CSV文件用于测试
        test_csv_path = Path(__file__).parent / "test_data.csv"
        test_csv_content = """time,value
0,1.0
1,2.0
2,3.0
3,4.0
4,5.0"""
        
        with open(test_csv_path, 'w') as f:
            f.write(test_csv_content)
        
        print("1. 测试 CsvReaderAgentAdapter...")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            csv_agent = CsvReaderAgentAdapter(
                csv_file_path=str(test_csv_path),
                time_column='time',
                data_column='value',
                agent_id='test_csv_reader'
            )
            
            # 验证废弃警告
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        # 设置事件总线
        event_bus = get_global_event_bus()
        csv_agent.set_event_bus(event_bus)
        
        # 测试基本功能
        assert csv_agent.configure({}) == True
        assert csv_agent.start() == True
        assert csv_agent.connect() == True
        
        # 读取数据
        data = csv_agent.read_data()
        assert len(data) == 5
        assert data[0]['value'] == 1.0
        
        csv_agent.stop()
        print("   ✓ CsvReaderAgentAdapter 功能正常")
        
        # 测试 CsvInflowAgent 适配器
        print("2. 测试 CsvInflowAgentAdapter...")
        from core_lib.core.new_agents.service_agents.data.unified_data_source import CsvInflowAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            inflow_agent = CsvInflowAgentAdapter(
                csv_file_path=str(test_csv_path),
                time_column='time',
                data_column='value',
                inflow_topic='test.inflow',
                target_component='test_component'
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        inflow_agent.set_event_bus(event_bus)
        assert inflow_agent.start() == True
        assert inflow_agent.connect() == True
        inflow_agent.stop()
        print("   ✓ CsvInflowAgentAdapter 功能正常")
        
        # 清理测试文件
        test_csv_path.unlink()
        
        print("✅ 数据源适配器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 数据源适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_control_adapters():
    """测试控制适配器"""
    print("=== 测试控制适配器 ===")
    
    try:
        event_bus = get_global_event_bus()
        
        # 测试 GateControlAgent 适配器
        print("1. 测试 GateControlAgentAdapter...")
        from core_lib.core.new_agents.local_agents.control.unified_local_control import GateControlAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            gate_agent = GateControlAgentAdapter(
                agent_id='test_gate',
                message_bus=event_bus,
                time_step=1.0,
                observation_topic='test.gate.observation',
                action_topic='test.gate.action',
                observation_key='water_level'
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        gate_agent.set_event_bus(event_bus)
        assert gate_agent.configure({}) == True
        assert gate_agent.start() == True
        
        # 测试设备状态
        state = gate_agent.get_device_state()
        assert state['device_type'] == 'gate'
        assert state['agent_id'] == 'test_gate'
        
        gate_agent.stop()
        print("   ✓ GateControlAgentAdapter 功能正常")
        
        # 测试 PumpControlAgent 适配器
        print("2. 测试 PumpControlAgentAdapter...")
        from core_lib.core.new_agents.local_agents.control.unified_local_control import PumpControlAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            pump_agent = PumpControlAgentAdapter(
                agent_id='test_pump'
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        pump_agent.set_event_bus(event_bus)
        assert pump_agent.start() == True
        
        state = pump_agent.get_device_state()
        assert state['device_type'] == 'pump'
        
        pump_agent.stop()
        print("   ✓ PumpControlAgentAdapter 功能正常")
        
        # 测试 ValveControlAgent 适配器
        print("3. 测试 ValveControlAgentAdapter...")
        from core_lib.core.new_agents.local_agents.control.unified_local_control import ValveControlAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            valve_agent = ValveControlAgentAdapter(
                agent_id='test_valve'
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        valve_agent.set_event_bus(event_bus)
        assert valve_agent.start() == True
        
        state = valve_agent.get_device_state()
        assert state['device_type'] == 'valve'
        
        valve_agent.stop()
        print("   ✓ ValveControlAgentAdapter 功能正常")
        
        print("✅ 控制适配器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 控制适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_disturbance_adapters():
    """测试扰动适配器"""
    print("=== 测试扰动适配器 ===")
    
    try:
        event_bus = get_global_event_bus()
        
        # 测试 RainfallAgent 适配器
        print("1. 测试 RainfallAgentAdapter...")
        from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import RainfallAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            rainfall_agent = RainfallAgentAdapter(
                agent_id='test_rainfall',
                base_intensity=0.0,
                peak_intensity=10.0,
                storm_duration=1800.0
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        rainfall_agent.set_event_bus(event_bus)
        assert rainfall_agent.start() == True
        
        # 测试扰动生成
        current_time = time.time()
        assert rainfall_agent.is_active(current_time) == True
        
        disturbance = rainfall_agent.generate_disturbance(current_time)
        assert 'value' in disturbance
        assert disturbance['disturbance_type'] == 'rainfall'
        
        rainfall_agent.stop()
        print("   ✓ RainfallAgentAdapter 功能正常")
        
        # 测试 WaterUseAgent 适配器
        print("2. 测试 WaterUseAgentAdapter...")
        from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import WaterUseAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            water_use_agent = WaterUseAgentAdapter(
                agent_id='test_water_use',
                base_demand=5.0,
                peak_factor=2.0
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        water_use_agent.set_event_bus(event_bus)
        assert water_use_agent.start() == True
        
        disturbance = water_use_agent.generate_disturbance(current_time)
        assert 'value' in disturbance
        assert disturbance['disturbance_type'] == 'water_use'
        
        water_use_agent.stop()
        print("   ✓ WaterUseAgentAdapter 功能正常")
        
        print("✅ 扰动适配器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 扰动适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_identification_adapters():
    """测试识别适配器"""
    print("=== 测试识别适配器 ===")
    
    try:
        event_bus = get_global_event_bus()
        
        # 测试 IdentificationAgent 适配器
        print("1. 测试 IdentificationAgentAdapter...")
        from core_lib.core.new_agents.service_agents.identification.unified_identification import IdentificationAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            id_agent = IdentificationAgentAdapter(
                agent_id='test_identification',
                target_parameters=['param1', 'param2'],
                identification_method='offline'
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        id_agent.set_event_bus(event_bus)
        assert id_agent.start() == True
        
        # 测试参数拟合
        test_data = [
            {'input_param1': 1.0, 'input_param2': 2.0, 'output': 3.0},
            {'input_param1': 2.0, 'input_param2': 3.0, 'output': 5.0}
        ]
        
        params = id_agent.fit_parameters(test_data)
        assert isinstance(params, dict)
        
        id_agent.stop()
        print("   ✓ IdentificationAgentAdapter 功能正常")
        
        # 测试 ModelUpdaterAgent 适配器
        print("2. 测试 ModelUpdaterAgentAdapter...")
        from core_lib.core.new_agents.service_agents.identification.unified_identification import ModelUpdaterAgentAdapter
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            updater_agent = ModelUpdaterAgentAdapter(
                agent_id='test_model_updater',
                target_parameters=['param1'],
                window_size=50
            )
            
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            print("   ✓ 废弃警告正常显示")
        
        updater_agent.set_event_bus(event_bus)
        assert updater_agent.start() == True
        
        # 测试在线更新
        new_data = {'param1': 1.5, 'timestamp': time.time()}
        params = updater_agent.update_online(new_data)
        assert isinstance(params, dict)
        
        updater_agent.stop()
        print("   ✓ ModelUpdaterAgentAdapter 功能正常")
        
        print("✅ 识别适配器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 识别适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_registry_integration():
    """测试注册中心集成"""
    print("=== 测试注册中心集成 ===")
    
    try:
        # 注册所有Agent
        register_all_agents()
        
        from core_lib.core.factories import get_global_agent_factory
        factory = get_global_agent_factory()
        
        supported_types = factory.get_supported_types()
        print(f"已注册的Agent类型数量: {len(supported_types)}")
        
        # 验证适配器类型已注册
        adapter_types = [
            'CsvReaderAgent', 'CsvInflowAgent',
            'GateControlAgent', 'PumpControlAgent', 'ValveControlAgent',
            'RainfallAgent', 'WaterUseAgent',
            'IdentificationAgentOld', 'ModelUpdaterAgent'
        ]
        
        for adapter_type in adapter_types:
            assert adapter_type in supported_types, f"适配器类型 {adapter_type} 未注册"
            print(f"   ✓ {adapter_type} 已注册")
        
        print("✅ 注册中心集成测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 注册中心集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有适配器测试"""
    print("适配器功能验证测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("数据源适配器", test_data_source_adapters()))
    test_results.append(("控制适配器", test_control_adapters()))
    test_results.append(("扰动适配器", test_disturbance_adapters()))
    test_results.append(("识别适配器", test_identification_adapters()))
    test_results.append(("注册中心集成", test_registry_integration()))
    
    # 汇总结果
    print("=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有适配器测试通过！可以安全使用适配器进行过渡。")
        return True
    else:
        print("⚠️  部分测试失败，需要修复后再进行迁移。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
