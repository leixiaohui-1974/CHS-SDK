# -*- coding: utf-8 -*-

"""
Windows编码问题修复工具

此脚本提供了修复Windows系统上常见的GBK编码错误的解决方案
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

def setup_utf8_environment() -> Dict[str, str]:
    """
    设置UTF-8环境变量，防止Windows GBK编码错误
    
    Returns:
        包含UTF-8配置的环境变量字典
    """
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # 强制使用Unicode输出
    return env

def run_with_utf8_encoding(command: list, cwd: Optional[str] = None, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """
    使用UTF-8编码运行子进程，避免GBK编码错误
    
    Args:
        command: 要执行的命令列表
        cwd: 工作目录
        timeout: 超时时间（秒）
        
    Returns:
        子进程执行结果
    """
    env = setup_utf8_environment()
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            encoding='utf-8',
            errors='replace',  # 替换无法解码的字符，避免乱码
            env=env
        )
        return result
    except subprocess.TimeoutExpired as e:
        print(f"命令执行超时: {' '.join(command)}")
        raise
    except Exception as e:
        print(f"命令执行出错: {e}")
        raise

def fix_unicode_output(text: str) -> str:
    """
    清理文本中的特殊字符，避免显示乱码
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除空字符和其他控制字符
    cleaned = text.replace('\x00', '').replace('\r\n', '\n').strip()
    return cleaned

def run_python_script_safe(script_path: str, args: list = None, cwd: Optional[str] = None) -> bool:
    """
    安全运行Python脚本，自动处理编码问题
    
    Args:
        script_path: Python脚本路径
        args: 脚本参数列表
        cwd: 工作目录
        
    Returns:
        是否成功执行
    """
    command = [sys.executable, script_path]
    if args:
        command.extend(args)
    
    try:
        result = run_with_utf8_encoding(command, cwd=cwd, timeout=300)
        
        # 清理输出
        stdout = fix_unicode_output(result.stdout)
        stderr = fix_unicode_output(result.stderr)
        
        if result.returncode == 0:
            print("✅ 脚本执行成功")
            if stdout:
                print(f"输出:\n{stdout}")
            return True
        else:
            print(f"❌ 脚本执行失败 (返回码: {result.returncode})")
            if stderr:
                print(f"错误信息:\n{stderr}")
            if stdout:
                print(f"标准输出:\n{stdout}")
            return False
            
    except Exception as e:
        print(f"❌ 执行过程中发生异常: {e}")
        return False

def main():
    """
    演示如何使用编码修复工具
    """
    print("🔧 Windows编码问题修复工具")
    print("=" * 50)
    
    # 设置UTF-8环境
    env = setup_utf8_environment()
    print("✅ UTF-8环境变量已设置:")
    for key in ['PYTHONIOENCODING', 'PYTHONUTF8', 'PYTHONLEGACYWINDOWSSTDIO']:
        print(f"  {key}={env.get(key)}")
    
    print("\n💡 使用方法:")
    print("1. 在脚本开头添加: from encoding_fix import setup_utf8_environment")
    print("2. 在运行subprocess前设置: env = setup_utf8_environment()")
    print("3. 或者直接使用: run_python_script_safe('your_script.py')")

if __name__ == "__main__":
    main()