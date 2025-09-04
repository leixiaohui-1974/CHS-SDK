#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换精度增强模块

针对双向转换中发现的关键问题进行专项改进：
1. 增强拓扑结构识别和转换精度
2. 改进仿真参数映射和保真度
3. 优化组件参数转换准确性
4. 提升结构完整性保持能力

作者: CHS-SDK Team
创建时间: 2024
"""

import re
import time
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from advanced_precision_enhancement import AdvancedPrecisionEnhancementFramework, AdvancedEnhancementResult
from pathlib import Path


@dataclass
class EnhancementResult:
    """增强结果数据类"""
    enhanced_config: Dict[str, Any]
    improvement_score: float
    applied_enhancements: List[str]
    warnings: List[str]
    metrics: Dict[str, float]


class TopologyEnhancer:
    """拓扑结构增强器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 常见的连接模式
        self.connection_patterns = {
            'reservoir_to_gate': {'type': 'flow', 'direction': 'downstream'},
            'gate_to_channel': {'type': 'flow', 'direction': 'downstream'},
            'channel_to_reservoir': {'type': 'flow', 'direction': 'downstream'},
            'pump_to_pipe': {'type': 'flow', 'direction': 'upstream'},
            'sensor_to_component': {'type': 'monitoring', 'direction': 'bidirectional'}
        }
        
        # 组件类型映射
        self.component_types = {
            'reservoir': ['Reservoir', 'Lake', 'Pond'],
            'gate': ['Gate', 'Valve', 'Sluice'],
            'channel': ['Channel', 'Canal', 'RiverChannel', 'Pipe'],
            'pump': ['Pump', 'PumpStation'],
            'sensor': ['Sensor', 'Monitor'],
            'controller': ['Controller', 'PIDController', 'MPCController']
        }
    
    def enhance_topology(self, config: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """增强拓扑结构"""
        enhanced_config = config.copy()
        
        # 获取组件信息
        components = self._extract_components(enhanced_config)
        
        # 分析现有连接
        existing_connections = self._extract_connections(enhanced_config)
        
        # 推断缺失的连接
        inferred_connections = self._infer_missing_connections(components, existing_connections, description)
        
        # 验证和优化连接
        validated_connections = self._validate_connections(components, existing_connections + inferred_connections)
        
        # 更新配置
        enhanced_config['topology'] = validated_connections
        
        self.logger.info(f"拓扑增强完成: 原有{len(existing_connections)}个连接，新增{len(inferred_connections)}个连接")
        
        return enhanced_config
    
    def _extract_components(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取组件信息"""
        components = []
        
        # 处理不同的组件格式
        comp_data = config.get('components', {})
        if isinstance(comp_data, dict):
            if 'components' in comp_data:
                components = comp_data['components']
            else:
                components = list(comp_data.values())
        elif isinstance(comp_data, list):
            components = comp_data
        
        # 标准化组件信息
        standardized = []
        for comp in components:
            if isinstance(comp, dict):
                standardized.append({
                    'id': comp.get('id', comp.get('name', f'comp_{len(standardized)}')),
                    'type': comp.get('type', 'Unknown'),
                    'category': self._categorize_component(comp.get('type', '')),
                    'params': comp.get('params', {})
                })
        
        return standardized
    
    def _categorize_component(self, comp_type: str) -> str:
        """组件分类"""
        for category, types in self.component_types.items():
            if any(t.lower() in comp_type.lower() for t in types):
                return category
        return 'unknown'
    
    def _extract_connections(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取现有连接"""
        connections = []
        
        topology = config.get('topology', [])
        if isinstance(topology, dict):
            if 'connections' in topology:
                connections = topology['connections']
            else:
                connections = list(topology.values())
        elif isinstance(topology, list):
            connections = topology
        
        # 标准化连接格式
        standardized = []
        for conn in connections:
            if isinstance(conn, dict):
                standardized.append({
                    'from': conn.get('from', conn.get('source')),
                    'to': conn.get('to', conn.get('target')),
                    'type': conn.get('type', 'flow'),
                    'direction': conn.get('direction', 'downstream')
                })
        
        return standardized
    
    def _infer_missing_connections(self, components: List[Dict], existing_connections: List[Dict], description: str) -> List[Dict]:
        """推断缺失的连接"""
        inferred = []
        
        # 基于组件类型推断连接
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i != j:
                    connection = self._should_connect(comp1, comp2, existing_connections)
                    if connection:
                        inferred.append(connection)
        
        # 基于描述文本推断连接
        if description:
            text_connections = self._extract_connections_from_text(description, components)
            inferred.extend(text_connections)
        
        return inferred
    
    def _should_connect(self, comp1: Dict, comp2: Dict, existing: List[Dict]) -> Optional[Dict]:
        """判断两个组件是否应该连接"""
        # 检查是否已存在连接
        for conn in existing:
            if (conn['from'] == comp1['id'] and conn['to'] == comp2['id']) or \
               (conn['from'] == comp2['id'] and conn['to'] == comp1['id']):
                return None
        
        # 基于组件类型判断
        cat1, cat2 = comp1['category'], comp2['category']
        
        # 水库到闸门
        if cat1 == 'reservoir' and cat2 == 'gate':
            return {'from': comp1['id'], 'to': comp2['id'], 'type': 'flow', 'direction': 'downstream'}
        
        # 闸门到河道
        if cat1 == 'gate' and cat2 == 'channel':
            return {'from': comp1['id'], 'to': comp2['id'], 'type': 'flow', 'direction': 'downstream'}
        
        # 泵到管道
        if cat1 == 'pump' and cat2 == 'channel':
            return {'from': comp1['id'], 'to': comp2['id'], 'type': 'flow', 'direction': 'upstream'}
        
        return None
    
    def _extract_connections_from_text(self, description: str, components: List[Dict]) -> List[Dict]:
        """从文本描述中提取连接关系"""
        connections = []
        comp_ids = [comp['id'] for comp in components]
        
        # 连接关键词模式
        patterns = [
            r'(\w+)\s*(?:流入|连接到|通向)\s*(\w+)',
            r'(\w+)\s*(?:->|→)\s*(\w+)',
            r'从\s*(\w+)\s*到\s*(\w+)',
            r'(\w+)\s*和\s*(\w+)\s*连接'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                source, target = match
                if source in comp_ids and target in comp_ids:
                    connections.append({
                        'from': source,
                        'to': target,
                        'type': 'flow',
                        'direction': 'downstream'
                    })
        
        return connections
    
    def _validate_connections(self, components: List[Dict], connections: List[Dict]) -> List[Dict]:
        """验证和优化连接"""
        validated = []
        comp_ids = {comp['id'] for comp in components}
        
        for conn in connections:
            # 检查组件是否存在
            if conn['from'] in comp_ids and conn['to'] in comp_ids:
                # 避免重复连接
                if not any(v['from'] == conn['from'] and v['to'] == conn['to'] for v in validated):
                    validated.append(conn)
        
        return validated


class SimulationParameterEnhancer:
    """仿真参数增强器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 参数映射规则
        self.parameter_mappings = {
            'dt': ['time_step', 'timestep', 'step_size'],
            'duration': ['end_time', 'total_time', 'simulation_time'],
            'solver': ['method', 'algorithm', 'integration_method'],
            'tolerance': ['tol', 'precision', 'accuracy'],
            'max_iterations': ['max_iter', 'iterations', 'max_steps']
        }
        
        # 默认参数值
        self.default_values = {
            'dt': 60.0,  # 1分钟
            'duration': 3600.0,  # 1小时
            'solver': 'rk4',
            'tolerance': 1e-6,
            'max_iterations': 1000,
            'name': '水利系统仿真',
            'description': '自动生成的仿真配置'
        }
    
    def enhance_simulation_params(self, config: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """增强仿真参数"""
        enhanced_config = config.copy()
        
        # 获取或创建仿真配置
        sim_config = enhanced_config.get('simulation', {})
        
        # 标准化参数名称
        sim_config = self._standardize_parameter_names(sim_config)
        
        # 填充缺失参数
        sim_config = self._fill_missing_parameters(sim_config, description)
        
        # 验证参数合理性
        sim_config = self._validate_parameters(sim_config)
        
        # 优化参数值
        sim_config = self._optimize_parameters(sim_config, enhanced_config)
        
        enhanced_config['simulation'] = sim_config
        
        self.logger.info(f"仿真参数增强完成: {len(sim_config)}个参数")
        
        return enhanced_config
    
    def _standardize_parameter_names(self, sim_config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化参数名称"""
        standardized = {}
        
        for standard_name, aliases in self.parameter_mappings.items():
            # 查找标准名称或别名
            value = sim_config.get(standard_name)
            if value is None:
                for alias in aliases:
                    if alias in sim_config:
                        value = sim_config[alias]
                        break
            
            if value is not None:
                standardized[standard_name] = value
        
        # 保留其他参数
        for key, value in sim_config.items():
            if key not in standardized and key not in sum(self.parameter_mappings.values(), []):
                standardized[key] = value
        
        return standardized
    
    def _fill_missing_parameters(self, sim_config: Dict[str, Any], description: str) -> Dict[str, Any]:
        """填充缺失参数"""
        filled = sim_config.copy()
        
        # 从描述中提取参数
        if description:
            extracted = self._extract_params_from_description(description)
            for key, value in extracted.items():
                if key not in filled:
                    filled[key] = value
        
        # 使用默认值
        for key, default_value in self.default_values.items():
            if key not in filled:
                filled[key] = default_value
        
        return filled
    
    def _extract_params_from_description(self, description: str) -> Dict[str, Any]:
        """从描述中提取参数"""
        params = {}
        
        # 时间相关模式
        time_patterns = [
            (r'(\d+)\s*小时', lambda x: float(x) * 3600),
            (r'(\d+)\s*分钟', lambda x: float(x) * 60),
            (r'(\d+)\s*秒', lambda x: float(x)),
            (r'时间步长\s*(\d+(?:\.\d+)?)\s*秒', lambda x: float(x)),
            (r'步长\s*(\d+(?:\.\d+)?)\s*秒', lambda x: float(x))
        ]
        
        for pattern, converter in time_patterns:
            match = re.search(pattern, description)
            if match:
                if '小时' in pattern or '分钟' in pattern or '秒' in pattern and '步长' not in pattern:
                    params['duration'] = converter(match.group(1))
                elif '步长' in pattern:
                    params['dt'] = converter(match.group(1))
        
        # 求解器模式
        solver_patterns = [
            r'(?:使用|采用)\s*(rk4|euler|adams|bdf)\s*(?:求解器|方法)',
            r'求解器\s*[:：]\s*(\w+)'
        ]
        
        for pattern in solver_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                params['solver'] = match.group(1).lower()
                break
        
        return params
    
    def _validate_parameters(self, sim_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数合理性"""
        validated = sim_config.copy()
        
        # 验证时间步长
        if 'dt' in validated:
            dt = validated['dt']
            if isinstance(dt, (int, float)) and dt <= 0:
                validated['dt'] = self.default_values['dt']
                self.logger.warning(f"无效的时间步长 {dt}，使用默认值 {self.default_values['dt']}")
        
        # 验证仿真时长
        if 'duration' in validated:
            duration = validated['duration']
            if isinstance(duration, (int, float)) and duration <= 0:
                validated['duration'] = self.default_values['duration']
                self.logger.warning(f"无效的仿真时长 {duration}，使用默认值 {self.default_values['duration']}")
        
        # 验证时间步长与仿真时长的关系
        if 'dt' in validated and 'duration' in validated:
            dt, duration = validated['dt'], validated['duration']
            if isinstance(dt, (int, float)) and isinstance(duration, (int, float)):
                if dt > duration:
                    validated['dt'] = duration / 100  # 设置为仿真时长的1%
                    self.logger.warning(f"时间步长大于仿真时长，调整为 {validated['dt']}")
        
        return validated
    
    def _optimize_parameters(self, sim_config: Dict[str, Any], full_config: Dict[str, Any]) -> Dict[str, Any]:
        """优化参数值"""
        optimized = sim_config.copy()
        
        # 根据系统复杂度调整参数
        components = full_config.get('components', {})
        if isinstance(components, dict):
            comp_count = len(components.get('components', []))
        elif isinstance(components, list):
            comp_count = len(components)
        else:
            comp_count = 0
        
        # 复杂系统需要更小的时间步长
        if comp_count > 10 and 'dt' in optimized:
            current_dt = optimized['dt']
            if isinstance(current_dt, (int, float)) and current_dt > 30:
                optimized['dt'] = 30.0  # 最大30秒
                self.logger.info(f"复杂系统，调整时间步长为 {optimized['dt']} 秒")
        
        # 添加求解器配置
        if 'solver' in optimized and isinstance(optimized['solver'], str):
            solver_name = optimized['solver']
            optimized['solver'] = {
                'type': solver_name,
                'tolerance': optimized.get('tolerance', self.default_values['tolerance']),
                'max_iterations': optimized.get('max_iterations', self.default_values['max_iterations'])
            }
        
        return optimized


class ComponentParameterEnhancer:
    """组件参数增强器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 组件默认参数
        self.default_params = {
            'Reservoir': {
                'capacity': 1000000.0,  # 100万立方米
                'initial_volume': 500000.0,  # 50万立方米
                'surface_area': 100000.0,  # 10万平方米
                'max_outflow': 100.0  # 100立方米/秒
            },
            'Gate': {
                'max_flow_rate': 50.0,  # 50立方米/秒
                'opening': 0.5,  # 50%开度
                'width': 10.0,  # 10米宽
                'height': 5.0  # 5米高
            },
            'Channel': {
                'length': 1000.0,  # 1000米
                'width': 20.0,  # 20米宽
                'depth': 5.0,  # 5米深
                'roughness': 0.03  # 曼宁粗糙系数
            },
            'Pump': {
                'max_flow_rate': 30.0,  # 30立方米/秒
                'efficiency': 0.85,  # 85%效率
                'power': 100000.0  # 100kW
            }
        }
    
    def enhance_component_params(self, config: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """增强组件参数"""
        enhanced_config = config.copy()
        
        # 获取组件列表
        components = self._extract_components(enhanced_config)
        
        # 增强每个组件的参数
        enhanced_components = []
        for comp in components:
            enhanced_comp = self._enhance_single_component(comp, description)
            enhanced_components.append(enhanced_comp)
        
        # 更新配置
        self._update_components_in_config(enhanced_config, enhanced_components)
        
        self.logger.info(f"组件参数增强完成: {len(enhanced_components)}个组件")
        
        return enhanced_config
    
    def _extract_components(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取组件列表"""
        components = []
        
        comp_data = config.get('components', {})
        if isinstance(comp_data, dict):
            if 'components' in comp_data:
                components = comp_data['components']
            else:
                components = list(comp_data.values())
        elif isinstance(comp_data, list):
            components = comp_data
        
        return components
    
    def _enhance_single_component(self, component: Dict[str, Any], description: str) -> Dict[str, Any]:
        """增强单个组件参数"""
        enhanced = component.copy()
        comp_type = enhanced.get('type', '')
        comp_id = enhanced.get('id', '')
        
        # 获取现有参数
        params = enhanced.get('params', {})
        
        # 根据组件类型添加默认参数
        for base_type, defaults in self.default_params.items():
            if base_type.lower() in comp_type.lower():
                for param_name, default_value in defaults.items():
                    if param_name not in params:
                        params[param_name] = default_value
                break
        
        # 从描述中提取特定参数
        if description and comp_id:
            extracted_params = self._extract_component_params_from_description(description, comp_id, comp_type)
            params.update(extracted_params)
        
        # 验证参数合理性
        params = self._validate_component_params(params, comp_type)
        
        enhanced['params'] = params
        return enhanced
    
    def _extract_component_params_from_description(self, description: str, comp_id: str, comp_type: str) -> Dict[str, Any]:
        """从描述中提取组件参数"""
        params = {}
        
        # 构建搜索模式
        patterns = [
            rf'{comp_id}.*?容量\s*(\d+(?:\.\d+)?)\s*(?:万立方米|立方米)',
            rf'{comp_id}.*?流量\s*(\d+(?:\.\d+)?)\s*(?:立方米/秒|m³/s)',
            rf'{comp_id}.*?长度\s*(\d+(?:\.\d+)?)\s*(?:米|m)',
            rf'{comp_id}.*?宽度\s*(\d+(?:\.\d+)?)\s*(?:米|m)',
            rf'{comp_id}.*?深度\s*(\d+(?:\.\d+)?)\s*(?:米|m)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                value = float(match.group(1))
                if '容量' in pattern:
                    if '万立方米' in match.group(0):
                        value *= 10000
                    params['capacity'] = value
                elif '流量' in pattern:
                    params['max_flow_rate'] = value
                elif '长度' in pattern:
                    params['length'] = value
                elif '宽度' in pattern:
                    params['width'] = value
                elif '深度' in pattern:
                    params['depth'] = value
        
        return params
    
    def _validate_component_params(self, params: Dict[str, Any], comp_type: str) -> Dict[str, Any]:
        """验证组件参数合理性"""
        validated = params.copy()
        
        # 验证数值参数
        numeric_params = ['capacity', 'max_flow_rate', 'length', 'width', 'depth', 'efficiency']
        for param in numeric_params:
            if param in validated:
                value = validated[param]
                if isinstance(value, (int, float)) and value <= 0:
                    # 使用默认值
                    for base_type, defaults in self.default_params.items():
                        if base_type.lower() in comp_type.lower() and param in defaults:
                            validated[param] = defaults[param]
                            self.logger.warning(f"组件参数 {param} 值无效，使用默认值 {defaults[param]}")
                            break
        
        # 验证效率参数
        if 'efficiency' in validated:
            eff = validated['efficiency']
            if isinstance(eff, (int, float)):
                if eff > 1.0:
                    validated['efficiency'] = eff / 100  # 转换百分比
                elif eff <= 0 or eff > 1:
                    validated['efficiency'] = 0.85  # 默认85%
        
        return validated
    
    def _update_components_in_config(self, config: Dict[str, Any], enhanced_components: List[Dict[str, Any]]):
        """更新配置中的组件"""
        comp_data = config.get('components', {})
        
        if isinstance(comp_data, dict):
            if 'components' in comp_data:
                comp_data['components'] = enhanced_components
            else:
                # 重建字典结构
                new_comp_data = {}
                for comp in enhanced_components:
                    comp_id = comp.get('id', f'comp_{len(new_comp_data)}')
                    new_comp_data[comp_id] = comp
                config['components'] = new_comp_data
        elif isinstance(comp_data, list):
            config['components'] = enhanced_components
        else:
            config['components'] = {'components': enhanced_components}


class PrecisionEnhancementFramework:
    """精度增强框架"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.topology_enhancer = TopologyEnhancer()
        self.simulation_enhancer = SimulationParameterEnhancer()
        self.component_enhancer = ComponentParameterEnhancer()
        # 集成高级增强框架
        self.advanced_framework = AdvancedPrecisionEnhancementFramework()
    
    def enhance_conversion_precision(self, config: Dict[str, Any], description: str = "") -> EnhancementResult:
        """全面增强转换精度"""
        start_time = time.time()
        applied_enhancements = []
        warnings = []
        
        try:
            # 首先使用高级增强框架进行深度增强
            try:
                advanced_result = self.advanced_framework.enhance_conversion_precision(config, description)
                enhanced_config = advanced_result.enhanced_config
                applied_enhancements.extend(advanced_result.applied_enhancements)
                warnings.extend(advanced_result.warnings)
                
                # 记录高级增强的改进分数
                advanced_improvement = advanced_result.improvement_score
                self.logger.info(f"高级增强改进分数: {advanced_improvement:.3f}")
                
            except Exception as e:
                self.logger.warning(f"高级增强失败，回退到基础增强: {e}")
                warnings.append(f"高级增强失败: {e}")
                enhanced_config = config.copy()
                
                # 回退到原有的增强逻辑
                # 1. 增强拓扑结构
                enhanced_config = self.topology_enhancer.enhance_topology(enhanced_config, description)
                applied_enhancements.append("拓扑结构增强")
                
                # 2. 增强仿真参数
                enhanced_config = self.simulation_enhancer.enhance_simulation_params(enhanced_config, description)
                applied_enhancements.append("仿真参数增强")
                
                # 3. 增强组件参数
                enhanced_config = self.component_enhancer.enhance_component_params(enhanced_config, description)
                applied_enhancements.append("组件参数增强")
            
            # 4. 计算改进指标
            improvement_score = self._calculate_improvement_score(config, enhanced_config)
            
            # 5. 生成详细指标
            metrics = self._calculate_enhancement_metrics(config, enhanced_config)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"精度增强完成，耗时 {processing_time:.2f}秒，改进分数 {improvement_score:.3f}")
            
            return EnhancementResult(
                enhanced_config=enhanced_config,
                improvement_score=improvement_score,
                applied_enhancements=applied_enhancements,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            self.logger.error(f"精度增强失败: {e}")
            return EnhancementResult(
                enhanced_config=config,
                improvement_score=0.0,
                applied_enhancements=[],
                warnings=[f"增强失败: {str(e)}"],
                metrics={}
            )
    
    def _calculate_improvement_score(self, original: Dict[str, Any], enhanced: Dict[str, Any]) -> float:
        """计算改进分数"""
        score = 0.0
        
        # 拓扑改进
        orig_topology = len(original.get('topology', []))
        enh_topology = len(enhanced.get('topology', []))
        if enh_topology > orig_topology:
            score += 0.3 * (enh_topology - orig_topology) / max(orig_topology, 1)
        
        # 仿真参数改进
        orig_sim_params = len(original.get('simulation', {}))
        enh_sim_params = len(enhanced.get('simulation', {}))
        if enh_sim_params > orig_sim_params:
            score += 0.4 * (enh_sim_params - orig_sim_params) / max(orig_sim_params, 1)
        
        # 组件参数改进
        orig_comp_params = self._count_component_params(original)
        enh_comp_params = self._count_component_params(enhanced)
        if enh_comp_params > orig_comp_params:
            score += 0.3 * (enh_comp_params - orig_comp_params) / max(orig_comp_params, 1)
        
        return min(score, 1.0)  # 限制在0-1之间
    
    def _count_component_params(self, config: Dict[str, Any]) -> int:
        """统计组件参数数量"""
        count = 0
        components = config.get('components', {})
        
        if isinstance(components, dict):
            if 'components' in components:
                comp_list = components['components']
            else:
                comp_list = list(components.values())
        elif isinstance(components, list):
            comp_list = components
        else:
            comp_list = []
        
        for comp in comp_list:
            if isinstance(comp, dict):
                params = comp.get('params', {})
                if isinstance(params, dict):
                    count += len(params)
        
        return count
    
    def _calculate_enhancement_metrics(self, original: Dict[str, Any], enhanced: Dict[str, Any]) -> Dict[str, float]:
        """计算增强指标"""
        metrics = {}
        
        # 结构完整性改进
        orig_sections = set(original.keys())
        enh_sections = set(enhanced.keys())
        metrics['structural_improvement'] = len(enh_sections - orig_sections) / len(orig_sections) if orig_sections else 0
        
        # 参数丰富度改进
        orig_param_count = self._count_all_params(original)
        enh_param_count = self._count_all_params(enhanced)
        metrics['parameter_enrichment'] = (enh_param_count - orig_param_count) / max(orig_param_count, 1)
        
        # 连接完整性改进
        orig_conn_count = len(original.get('topology', []))
        enh_conn_count = len(enhanced.get('topology', []))
        metrics['connectivity_improvement'] = (enh_conn_count - orig_conn_count) / max(orig_conn_count, 1)
        
        return metrics
    
    def _count_all_params(self, config: Dict[str, Any]) -> int:
        """统计所有参数数量"""
        count = 0
        
        # 仿真参数
        sim_params = config.get('simulation', {})
        if isinstance(sim_params, dict):
            count += len(sim_params)
        
        # 组件参数
        count += self._count_component_params(config)
        
        return count


def main():
    """主函数 - 演示精度增强功能"""
    logging.basicConfig(level=logging.INFO)
    
    # 示例配置
    sample_config = {
        'simulation': {
            'duration': 3600
        },
        'components': {
            'components': [
                {'id': 'reservoir1', 'type': 'Reservoir', 'params': {}},
                {'id': 'gate1', 'type': 'Gate', 'params': {}}
            ]
        },
        'topology': []
    }
    
    sample_description = "水库reservoir1通过闸门gate1控制出流，仿真时长1小时，时间步长60秒"
    
    # 创建增强框架
    enhancer = PrecisionEnhancementFramework()
    
    # 执行增强
    result = enhancer.enhance_conversion_precision(sample_config, sample_description)
    
    print(f"增强结果:")
    print(f"改进分数: {result.improvement_score:.3f}")
    print(f"应用的增强: {', '.join(result.applied_enhancements)}")
    print(f"增强指标: {result.metrics}")
    print(f"增强后配置: {json.dumps(result.enhanced_config, indent=2, ensure_ascii=False)}")


if __name__ == '__main__':
    main()