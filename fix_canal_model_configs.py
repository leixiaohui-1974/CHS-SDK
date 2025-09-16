#!/usr/bin/env python3
"""
修复 canal_model 文件夹中的配置文件
统一使用 start_time, end_time, time_step, real_time_factor
"""
import os
import yaml
import re
from pathlib import Path

def fix_config_file(file_path):
    """修复单个配置文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 在 simulation 部分，将 duration 改为 end_time
        def replace_duration_in_simulation(match):
            sim_content = match.group(1)
            # 在 simulation 部分替换 duration: 为 end_time:
            sim_content = re.sub(r'^(\s*)duration:\s*', r'\1end_time: ', sim_content, flags=re.MULTILINE)
            return f"simulation:{sim_content}"
        
        content = re.sub(r'simulation:(.*?)(?=\n\w+:|$)', replace_duration_in_simulation, content, flags=re.DOTALL)
        
        # 在 simulation 部分，将 dt: 改为 time_step:
        def replace_dt_in_simulation(match):
            sim_content = match.group(1)
            # 在 simulation 部分替换 dt: 为 time_step:
            sim_content = re.sub(r'^(\s*)dt:\s*', r'\1time_step: ', sim_content, flags=re.MULTILINE)
            return f"simulation:{sim_content}"
        
        content = re.sub(r'simulation:(.*?)(?=\n\w+:|$)', replace_dt_in_simulation, content, flags=re.DOTALL)
        
        # 在 agents 部分，将 dt: 改为 time_step:
        def replace_dt_in_agents(match):
            agent_content = match.group(1)
            # 在 agents 部分替换 dt: 为 time_step:
            agent_content = re.sub(r'^(\s*)dt:\s*', r'\1time_step: ', agent_content, flags=re.MULTILINE)
            return f"agents:{agent_content}"
        
        content = re.sub(r'agents:(.*?)(?=\n\w+:|$)', replace_dt_in_agents, content, flags=re.DOTALL)
        
        # 确保 simulation 部分包含所有必需的参数
        def ensure_simulation_params(match):
            sim_content = match.group(1)
            
            # 检查是否包含必需的参数
            required_params = {
                'start_time': '0.0',
                'end_time': '100.0', 
                'time_step': '1.0',
                'real_time_factor': '1.0'
            }
            
            # 添加缺失的参数
            for param, default_value in required_params.items():
                if param not in sim_content:
                    sim_content = f"{sim_content}\n  {param}: {default_value}"
            
            return f"simulation:{sim_content}"
        
        content = re.sub(r'simulation:(.*?)(?=\n\w+:|$)', ensure_simulation_params, content, flags=re.DOTALL)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Updated"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """主函数"""
    canal_model_path = Path("examples/canal_model")
    
    # 查找所有需要修改的文件
    files_to_fix = []
    
    # 主目录下的配置文件
    for pattern in ["*.yml", "*.yaml"]:
        files_to_fix.extend(canal_model_path.glob(pattern))
    
    # 子目录下的配置文件
    for subdir in canal_model_path.iterdir():
        if subdir.is_dir():
            for pattern in ["*.yml", "*.yaml"]:
                files_to_fix.extend(subdir.glob(pattern))
    
    print(f"🔍 找到 {len(files_to_fix)} 个配置文件需要检查")
    
    updated_count = 0
    error_count = 0
    
    for file_path in files_to_fix:
        print(f"\n📁 处理: {file_path}")
        success, message = fix_config_file(file_path)
        
        if success:
            print(f"✅ {message}")
            updated_count += 1
        else:
            print(f"⏭️  {message}")
            if "Error" in message:
                error_count += 1
    
    print(f"\n📊 处理结果:")
    print(f"  - 更新: {updated_count} 个文件")
    print(f"  - 错误: {error_count} 个文件")
    print(f"  - 总计: {len(files_to_fix)} 个文件")

if __name__ == "__main__":
    main()
