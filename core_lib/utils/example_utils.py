#!/usr/bin/env python3
"""
示例工具库 (Example Utilities)

提供示例代码中常用的通用功能，减少重复代码，让示例更聚焦于业务逻辑。

主要功能：
- 配置文件加载
- 路径处理
- 项目根目录设置
- 通用的初始化函数
- 结果输出格式化
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExampleConfig:
    """示例配置管理类"""
    
    def __init__(self, example_path: Path):
        """
        初始化示例配置
        
        Args:
            example_path: 示例目录路径
        """
        self.example_path = Path(example_path)
        self.config = {}
        self.components_config = {}
        self.agents_config = {}
        self.topology_config = {}
        
    def load_all_configs(self) -> 'ExampleConfig':
        """加载所有配置文件"""
        self.load_config()
        self.load_components()
        self.load_agents()
        self.load_topology()
        return self
    
    def load_config(self) -> Dict[str, Any]:
        """加载主配置文件"""
        config_path = self.example_path / 'config.yml'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                logger.info(f"已加载配置文件: {config_path}")
        return self.config
    
    def load_components(self) -> Dict[str, Any]:
        """加载组件配置文件"""
        components_path = self.example_path / 'components.yml'
        if components_path.exists():
            with open(components_path, 'r', encoding='utf-8') as f:
                self.components_config = yaml.safe_load(f)
                logger.info(f"已加载组件配置: {components_path}")
        return self.components_config
    
    def load_agents(self) -> Dict[str, Any]:
        """加载智能体配置文件"""
        agents_path = self.example_path / 'agents.yml'
        if agents_path.exists():
            with open(agents_path, 'r', encoding='utf-8') as f:
                self.agents_config = yaml.safe_load(f)
                logger.info(f"已加载智能体配置: {agents_path}")
        return self.agents_config
    
    def load_topology(self) -> Dict[str, Any]:
        """加载拓扑配置文件"""
        topology_path = self.example_path / 'topology.yml'
        if topology_path.exists():
            with open(topology_path, 'r', encoding='utf-8') as f:
                self.topology_config = yaml.safe_load(f)
                logger.info(f"已加载拓扑配置: {topology_path}")
        return self.topology_config
    
    def get_simulation_params(self) -> Dict[str, Any]:
        """获取仿真参数"""
        return self.config.get('simulation', {})
    
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """获取指定组件的配置"""
        return self.components_config.get(component_name, {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """获取指定智能体的配置"""
        return self.agents_config.get(agent_name, {})

def setup_project_path(example_file: str) -> Path:
    """
    设置项目路径并添加到Python路径中
    
    Args:
        example_file: 示例文件的__file__变量
        
    Returns:
        Path: 项目根目录路径
    """
    # 计算项目根目录（假设示例在examples子目录下）
    example_path = Path(example_file).resolve()
    project_root = example_path.parents[3]  # 通常是 examples/category/example_name/script.py
    
    # 添加到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"已添加项目根目录到Python路径: {project_root}")
    
    return project_root

def get_example_directory(example_file: str) -> Path:
    """
    获取示例目录路径
    
    Args:
        example_file: 示例文件的__file__变量
        
    Returns:
        Path: 示例目录路径
    """
    return Path(example_file).resolve().parent

def load_example_configs(example_file: str) -> ExampleConfig:
    """
    一键加载示例的所有配置文件
    
    Args:
        example_file: 示例文件的__file__变量
        
    Returns:
        ExampleConfig: 配置对象
    """
    # 设置项目路径
    setup_project_path(example_file)
    
    # 获取示例目录
    example_dir = get_example_directory(example_file)
    
    # 加载配置
    config = ExampleConfig(example_dir)
    config.load_all_configs()
    
    return config

def print_section_header(title: str, width: int = 60, char: str = "=") -> None:
    """
    打印格式化的章节标题
    
    Args:
        title: 标题文本
        width: 总宽度
        char: 分隔符字符
    """
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")

def print_subsection_header(title: str, width: int = 50, char: str = "-") -> None:
    """
    打印格式化的子章节标题
    
    Args:
        title: 标题文本
        width: 总宽度
        char: 分隔符字符
    """
    print(f"\n{char * width}")
    print(f"{title}")
    print(f"{char * width}")

def print_key_value_table(data: Dict[str, Any], title: str = "参数表") -> None:
    """
    打印键值对表格
    
    Args:
        data: 要打印的数据字典
        title: 表格标题
    """
    print_subsection_header(title)
    
    if not data:
        print("无数据")
        return
    
    # 计算最大键长度
    max_key_len = max(len(str(k)) for k in data.keys())
    
    for key, value in data.items():
        print(f"{str(key):<{max_key_len}} : {value}")

def print_performance_summary(metrics: Dict[str, float], title: str = "性能摘要") -> None:
    """
    打印性能指标摘要
    
    Args:
        metrics: 性能指标字典
        title: 摘要标题
    """
    print_subsection_header(title)
    
    for metric_name, value in metrics.items():
        if isinstance(value, float):
            print(f"{metric_name}: {value:.4f}")
        else:
            print(f"{metric_name}: {value}")

def validate_control_performance(actual: float, target: float, tolerance: float, 
                               metric_name: str = "控制误差") -> bool:
    """
    验证控制性能
    
    Args:
        actual: 实际值
        target: 目标值
        tolerance: 容差
        metric_name: 指标名称
        
    Returns:
        bool: 是否通过验证
    """
    error = abs(actual - target)
    passed = error <= tolerance
    
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {metric_name} = {error:.4f} (容差: {tolerance:.4f})")
    
    return passed

def calculate_rmse(actual: List[float], target: float) -> float:
    """
    计算均方根误差
    
    Args:
        actual: 实际值列表
        target: 目标值
        
    Returns:
        float: RMSE值
    """
    import numpy as np
    errors = np.array(actual) - target
    return float(np.sqrt(np.mean(errors**2)))

def calculate_steady_state_error(values: List[float], target: float, 
                               last_n_points: int = 10) -> float:
    """
    计算稳态误差
    
    Args:
        values: 值列表
        target: 目标值
        last_n_points: 用于计算稳态的最后N个点
        
    Returns:
        float: 稳态误差
    """
    if len(values) < last_n_points:
        last_n_points = len(values)
    
    steady_state_value = sum(values[-last_n_points:]) / last_n_points
    return abs(steady_state_value - target)

def check_system_stability(values: List[float], last_n_points: int = 10, 
                         max_variation: float = 0.1) -> bool:
    """
    检查系统稳定性
    
    Args:
        values: 值列表
        last_n_points: 检查最后N个点
        max_variation: 最大允许变化
        
    Returns:
        bool: 系统是否稳定
    """
    if len(values) < last_n_points:
        return False
    
    recent_values = values[-last_n_points:]
    variation = max(recent_values) - min(recent_values)
    
    return variation <= max_variation

def save_results_to_csv(data: Dict[str, List[float]], filename: str, 
                       example_dir: Optional[Path] = None) -> Path:
    """
    保存结果到CSV文件
    
    Args:
        data: 数据字典，键为列名，值为数据列表
        filename: 文件名
        example_dir: 示例目录，如果为None则保存到当前目录
        
    Returns:
        Path: 保存的文件路径
    """
    import pandas as pd
    
    if example_dir is None:
        file_path = Path(filename)
    else:
        file_path = Path(example_dir) / filename
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    logger.info(f"结果已保存到: {file_path}")
    return file_path

class ExampleRunner:
    """
    示例运行器基类，提供通用的运行框架
    """
    
    def __init__(self, example_file: str, title: str = "仿真示例"):
        """
        初始化示例运行器
        
        Args:
            example_file: 示例文件的__file__变量
            title: 示例标题
        """
        self.title = title
        self.project_root = setup_project_path(example_file)
        self.example_dir = get_example_directory(example_file)
        self.config = ExampleConfig(self.example_dir)
        
    def load_configs(self) -> 'ExampleRunner':
        """加载配置文件"""
        self.config.load_all_configs()
        return self
    
    def print_header(self) -> None:
        """打印示例标题"""
        print_section_header(f"开始执行: {self.title}")
    
    def print_footer(self) -> None:
        """打印示例结束"""
        print_section_header(f"示例执行完成: {self.title}")
    
    def run(self) -> None:
        """运行示例（子类需要重写此方法）"""
        raise NotImplementedError("子类必须实现run方法")
    
    def execute(self) -> None:
        """执行示例的完整流程"""
        try:
            self.print_header()
            self.load_configs()
            self.run()
            self.print_footer()
        except Exception as e:
            logger.error(f"示例执行失败: {e}")
            raise