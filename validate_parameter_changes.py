#!/usr/bin/env python3
"""
验证参数优化后的代码正确性
"""
import sys
from pathlib import Path

def check_parameter_consistency():
    """检查参数使用的一致性"""
    core_lib_path = Path("core_lib")
    
    issues = []
    
    print("=== 检查 dt 参数替换情况 ===")
    
    # 检查是否还有未替换的 dt 参数
    for py_file in core_lib_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines, 1):
                # 检查函数定义中的 dt: float
                if 'def ' in line and 'dt:' in line and 'time_step:' not in line:
                    issues.append(f"{py_file}:{i} - 未替换的dt参数: {line.strip()}")
                
                # 检查函数调用中的 dt=
                if 'dt=' in line and 'time_step=' not in line:
                    # 排除注释行
                    if not line.strip().startswith('#'):
                        issues.append(f"{py_file}:{i} - 未替换的dt调用: {line.strip()}")
                        
        except Exception as e:
            print(f"检查文件 {py_file} 时出错: {e}")
    
    print("=== 检查 duration 概念冲突 ===")
    
    # 检查是否还有与仿真时间相关的 duration 参数
    simulation_duration_patterns = [
        'simulation_duration',
        'total_duration', 
        'run_duration'
    ]
    
    for py_file in core_lib_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines, 1):
                for pattern in simulation_duration_patterns:
                    if pattern in line and 'end_time' not in line:
                        # 排除注释行
                        if not line.strip().startswith('#'):
                            issues.append(f"{py_file}:{i} - 可能的仿真时长概念冲突: {line.strip()}")
                        
        except Exception as e:
            print(f"检查文件 {py_file} 时出错: {e}")
    
    return issues

def check_interface_consistency():
    """检查接口一致性"""
    print("=== 检查接口一致性 ===")
    
    interfaces_file = Path("core_lib/core/interfaces.py")
    issues = []
    
    if interfaces_file.exists():
        try:
            with open(interfaces_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查 Simulatable 接口
            if 'def step(self, action: Any, time_step: float)' not in content:
                issues.append("Simulatable接口的step方法参数未正确更新")
            
            # 检查 Controller 接口
            if 'def compute_control_action(self, observation: State, time_step: float)' not in content:
                issues.append("Controller接口的compute_control_action方法参数未正确更新")
                
        except Exception as e:
            issues.append(f"检查接口文件时出错: {e}")
    else:
        issues.append("核心接口文件不存在")
    
    return issues

def main():
    """主函数"""
    print("开始验证参数优化结果...")
    
    # 检查参数一致性
    param_issues = check_parameter_consistency()
    
    # 检查接口一致性
    interface_issues = check_interface_consistency()
    
    all_issues = param_issues + interface_issues
    
    if all_issues:
        print(f"\n发现 {len(all_issues)} 个问题:")
        for issue in all_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 所有检查通过，参数优化成功！")
    
    # 统计信息
    core_lib_path = Path("core_lib")
    total_files = len(list(core_lib_path.rglob("*.py")))
    print(f"\n统计信息:")
    print(f"  - 检查了 {total_files} 个Python文件")
    print(f"  - 发现 {len(all_issues)} 个问题")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
