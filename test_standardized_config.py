#!/usr/bin/env python3
"""
测试标准化后的配置文件
"""
import yaml
import os
from pathlib import Path

def test_config_file(file_path):
    """测试单个配置文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'simulation' not in config:
            return False, "Missing simulation section"
        
        sim_config = config['simulation']
        required_keys = ['start_time', 'end_time', 'time_step', 'real_time_factor']
        
        missing_keys = []
        for key in required_keys:
            if key not in sim_config:
                missing_keys.append(key)
        
        if missing_keys:
            return False, f"Missing keys: {missing_keys}"
        
        # 检查是否还有旧的参数名
        old_keys = ['dt', 'duration']
        found_old_keys = [key for key in old_keys if key in sim_config]
        if found_old_keys:
            return False, f"Found old parameter names: {found_old_keys}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """主测试函数"""
    # 测试几个关键的配置文件
    test_files = [
        "examples/distributed_digital_twin_simulation/config.yml",
        "examples/watertank/01_simulation/config.yml",
        "examples/mission_example_1/config.yml",
        "examples/canal_model/canal_pid_control/config.yml"
    ]
    
    print("🧪 测试标准化后的配置文件...")
    
    all_passed = True
    for file_path in test_files:
        if os.path.exists(file_path):
            success, message = test_config_file(file_path)
            status = "✅" if success else "❌"
            print(f"{status} {file_path}: {message}")
            if not success:
                all_passed = False
        else:
            print(f"⚠️  {file_path}: File not found")
    
    if all_passed:
        print("\n🎉 所有测试通过！配置文件标准化成功！")
    else:
        print("\n⚠️  部分测试失败，需要检查")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
