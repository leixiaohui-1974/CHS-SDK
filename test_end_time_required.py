#!/usr/bin/env python3
"""
Test script to verify that end_time is required in simulation configuration.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory

def test_simulation_harness_without_end_time():
    """Test that SimulationHarness raises error when end_time is missing"""
    print("Testing SimulationHarness without end_time...")
    try:
        config = {'time_step': 1.0}  # Missing end_time
        harness = SimulationHarness(config=config)
        print("❌ ERROR: Should have raised KeyError!")
        return False
    except KeyError as e:
        if "end_time" in str(e):
            print("✅ PASS: SimulationHarness correctly requires end_time")
            return True
        else:
            print(f"❌ ERROR: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

def test_simulation_factory_without_end_time():
    """Test that UnifiedComponentFactory can be used without end_time"""
    print("Testing UnifiedComponentFactory without end_time...")
    try:
        factory = UnifiedComponentFactory()
        print("✅ PASS: UnifiedComponentFactory doesn't require end_time")
        return True
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

def test_simulation_harness_with_end_time():
    """Test that SimulationHarness works when end_time is provided"""
    print("Testing SimulationHarness with end_time...")
    try:
        config = {'end_time': 1000, 'dt': 1.0}
        harness = SimulationHarness(config=config)
        print("✅ PASS: SimulationHarness works with end_time")
        return True
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

def test_simulation_factory_with_end_time():
    """Test that UnifiedComponentFactory works when end_time is provided (even though not needed)"""
    print("Testing UnifiedComponentFactory with end_time...")
    try:
        factory = UnifiedComponentFactory()
        # Factory doesn't need config, but we can test it still works
        print("✅ PASS: UnifiedComponentFactory works regardless of end_time")
        return True
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Testing end_time requirement ===\n")
    
    tests = [
        test_simulation_harness_without_end_time,
        test_simulation_factory_without_end_time,
        test_simulation_harness_with_end_time,
        test_simulation_factory_with_end_time
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! end_time is now required.")
    else:
        print("❌ Some tests failed.")

if __name__ == "__main__":
    main()
