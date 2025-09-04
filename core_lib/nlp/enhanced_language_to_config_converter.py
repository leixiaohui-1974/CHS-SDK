#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版自然语言到配置文件转换器

融合LLM大模型的智能理解能力和规则系统的精确性，提供更高精度的转换结果。

主要特性：
1. LLM智能解析：利用大模型理解复杂的自然语言描述
2. 规则验证：使用现有规则系统验证和补充LLM输出
3. 混合策略：结合两种方法的优势，提升转换精度
4. 自动修正：当LLM输出不符合规则时自动修正
5. 渐进式改进：通过反馈机制持续优化转换质量

Author: CHS-SDK Team
Date: 2024
"""

import logging
import re
import yaml
from typing import Dict, List, Any, Union, Optional
from pathlib import Path
from dataclasses import dataclass

from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType
from core_lib.llm_services.llm_service import call_tongyi_qianwen_api
from core_lib.config.unified_config_manager import validate_yaml_content
from core_lib.nlp.language_to_config_converter import (
    LanguageToConfigConverter, ComponentInfo, AgentInfo, ConnectionInfo
)


@dataclass
class ConversionResult:
    """转换结果数据类"""
    config_data: Dict[str, Any]
    confidence_score: float
    llm_contribution: float
    rule_contribution: float
    validation_errors: List[str]
    improvements: List[str]
    source_method: str  # 'llm', 'rule', 'hybrid'


class EnhancedLanguageToConfigConverter:
    """增强版自然语言到配置文件转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = UnifiedConfigManager()
        self.rule_converter = LanguageToConfigConverter()
        
        # 转换策略配置
        self.use_llm_first = True  # 优先使用LLM
        self.enable_rule_validation = True  # 启用规则验证
        self.enable_hybrid_mode = True  # 启用混合模式
        self.confidence_threshold = 0.7  # 置信度阈值
        
    def get_llm_system_prompt(self) -> str:
        """获取LLM系统提示词"""
        return """
你是一位精通水利工程建模的顶级专家，专门使用 CHS-SDK。你的任务是将用户的自然语言描述转换成一个结构完整、语法正确的配置文件内容。

你必须严格遵循以下规则：
1. 你的输出**必须且只能**是YAML格式的文本，绝不能包含任何额外的解释或文字。
2. YAML的顶级键必须包含 `simulation`、`components` 和 `topology`。
3. 你必须理解并使用以下核心概念定义来创建组件：
   * **被控对象 (Controlled Objects)**: 水文状态需要被管理和控制的物理实体。包括: `Reservoir`, `Pipe`, `Canal`, `Channel`, `RiverChannel`, `Lake`, `Pond`。
   * **控制对象 (Controlling Objects)**: 能够改变被控对象状态的物理设施。包括: `Gate`, `Pump`, `Valve`, `PumpStation`, `ValveStation`, `ControlledSystem`。
   * **连接对象**: 连接不同组件的物理实体。包括: `Junction`, `Sensor`。
4. 在 `simulation` 中必须包含: `duration`(仿真时长,秒), `dt`(时间步长,秒), `name`(仿真名称), `solver`(求解器,默认rk4)。
5. 根据用户的描述，在 `components` 列表中创建相应的物理对象实例，并正确填写 `id`, `type`, 和 `params`。
6. 在 `topology` 列表中描述组件之间的连接关系，每个连接包含 `from`, `to`, `type`(默认flow)。
7. 如果描述中包含智能体信息，添加 `agents` 部分。
8. 确保所有组件ID在topology中被正确引用。
"""
    
    def convert_language_to_config(self, description: str, 
                                 config_type: ConfigType = ConfigType.UNIVERSAL_CONFIG,
                                 output_dir: Union[str, Path] = None,
                                 strategy: str = 'hybrid',
                                 enable_iterative_refinement: bool = True) -> ConversionResult:
        """将自然语言描述转换为配置文件
        
        Args:
            description: 自然语言描述
            config_type: 目标配置文件类型
            output_dir: 输出目录
            strategy: 转换策略 ('llm', 'rule', 'hybrid')
            enable_iterative_refinement: 是否启用迭代优化
            
        Returns:
            ConversionResult: 转换结果
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"开始转换，策略: {strategy}")
        
        try:
            if strategy == 'llm':
                result = self._convert_with_llm(description, config_type, output_dir)
            elif strategy == 'rule':
                result = self._convert_with_rules(description, config_type, output_dir)
            elif strategy == 'hybrid':
                result = self._convert_with_hybrid(description, config_type, output_dir)
            else:
                raise ValueError(f"不支持的转换策略: {strategy}")
            
            # 如果启用迭代优化且置信度较低，进行迭代优化
            if enable_iterative_refinement and result.confidence_score < 0.8 and result.config_data:
                self.logger.info(f"置信度较低 ({result.confidence_score:.2f})，启动迭代优化")
                optimized_config = self._iterative_refinement(result.config_data, description)
                
                # 重新计算置信度
                validation_issues = self._validate_config(optimized_config)
                if len(validation_issues) < len(self._validate_config(result.config_data)):
                    result.config_data = optimized_config
                    # 提升置信度
                    result.confidence_score = min(0.95, result.confidence_score + 0.2)
                    result.improvements.append("迭代优化提升了配置质量")
                    self.logger.info(f"迭代优化完成，新置信度: {result.confidence_score:.2f}")
            
            # 记录转换时间
            conversion_time = time.time() - start_time
            self.logger.info(f"转换完成，策略: {strategy}, 置信度: {result.confidence_score:.2f}, 耗时: {conversion_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"转换失败: {str(e)}")
            return ConversionResult(
                config_data={},
                confidence_score=0.0,
                llm_contribution=0.0,
                rule_contribution=0.0,
                validation_errors=[str(e)],
                improvements=[],
                source_method=strategy
            )
    
    def _convert_with_llm(self, description: str, config_type: ConfigType, 
                         output_dir: Union[str, Path] = None) -> ConversionResult:
        """使用LLM进行转换"""
        try:
            # 调用LLM生成配置
            system_prompt = self.get_llm_system_prompt()
            generated_yaml = call_tongyi_qianwen_api(description, system_prompt)
            
            # 验证生成的YAML
            validation_result = validate_yaml_content(generated_yaml)
            
            if validation_result['valid']:
                config_data = yaml.safe_load(generated_yaml)
                
                # 保存配置文件
                if output_dir:
                    self._save_config_files(config_data, config_type, output_dir)
                
                return ConversionResult(
                    config_data=config_data,
                    confidence_score=0.9,
                    llm_contribution=1.0,
                    rule_contribution=0.0,
                    validation_errors=[],
                    improvements=["LLM成功生成有效配置"],
                    source_method='llm'
                )
            else:
                # LLM生成失败，尝试修正
                self.logger.warning(f"LLM生成的配置验证失败: {validation_result['errors']}")
                
                # 尝试自我修正
                correction_prompt = f"""你上次生成的YAML配置未能通过验证，错误如下：
{validation_result['errors']}

请修正以上错误，并根据我的原始需求重新生成一个完整且正确的YAML配置：'{description}'"""
                
                corrected_yaml = call_tongyi_qianwen_api(correction_prompt, system_prompt)
                final_validation = validate_yaml_content(corrected_yaml)
                
                if final_validation['valid']:
                    config_data = yaml.safe_load(corrected_yaml)
                    
                    if output_dir:
                        self._save_config_files(config_data, config_type, output_dir)
                    
                    return ConversionResult(
                        config_data=config_data,
                        confidence_score=0.8,
                        llm_contribution=1.0,
                        rule_contribution=0.0,
                        validation_errors=validation_result['errors'],
                        improvements=["LLM自我修正后生成有效配置"],
                        source_method='llm'
                    )
                else:
                    # 修正也失败，返回错误结果
                    return ConversionResult(
                        config_data={},
                        confidence_score=0.0,
                        llm_contribution=1.0,
                        rule_contribution=0.0,
                        validation_errors=final_validation['errors'],
                        improvements=[],
                        source_method='llm'
                    )
                    
        except Exception as e:
            self.logger.error(f"LLM转换失败: {e}")
            return ConversionResult(
                config_data={},
                confidence_score=0.0,
                llm_contribution=1.0,
                rule_contribution=0.0,
                validation_errors=[str(e)],
                improvements=[],
                source_method='llm'
            )
    
    def _convert_with_rules(self, description: str, config_type: ConfigType,
                           output_dir: Union[str, Path] = None) -> ConversionResult:
        """使用规则系统进行转换"""
        try:
            # 使用现有的规则转换器
            config_data = self.rule_converter.convert_language_to_config(
                description, config_type, output_dir
            )
            
            # 计算置信度（基于提取到的组件数量等）
            components_count = len(config_data.get('components', {}).get('components', []))
            confidence_score = min(0.8, 0.3 + components_count * 0.1)
            
            return ConversionResult(
                config_data=config_data,
                confidence_score=confidence_score,
                llm_contribution=0.0,
                rule_contribution=1.0,
                validation_errors=[],
                improvements=["规则系统成功生成配置"],
                source_method='rule'
            )
            
        except Exception as e:
            self.logger.error(f"规则转换失败: {e}")
            return ConversionResult(
                config_data={},
                confidence_score=0.0,
                llm_contribution=0.0,
                rule_contribution=1.0,
                validation_errors=[str(e)],
                improvements=[],
                source_method='rule'
            )
    
    def _convert_with_hybrid(self, description: str, config_type: ConfigType,
                            output_dir: Union[str, Path] = None) -> ConversionResult:
        """使用混合策略进行转换"""
        # 首先尝试LLM转换
        llm_result = self._convert_with_llm(description, config_type)
        
        # 然后尝试规则转换
        rule_result = self._convert_with_rules(description, config_type)
        
        # 选择最佳结果或融合两个结果
        if llm_result.confidence_score >= self.confidence_threshold:
            # LLM结果足够好，使用LLM结果但用规则验证
            enhanced_result = self._enhance_with_rules(llm_result, rule_result, description)
            enhanced_result.source_method = 'hybrid'
            
            if output_dir:
                self._save_config_files(enhanced_result.config_data, config_type, output_dir)
            
            return enhanced_result
            
        elif rule_result.confidence_score > llm_result.confidence_score:
            # 规则结果更好，使用规则结果但用LLM增强
            enhanced_result = self._enhance_with_llm(rule_result, llm_result, description)
            enhanced_result.source_method = 'hybrid'
            
            if output_dir:
                self._save_config_files(enhanced_result.config_data, config_type, output_dir)
            
            return enhanced_result
            
        else:
            # 两个结果都不理想，尝试融合
            fused_result = self._fuse_results(llm_result, rule_result, description)
            fused_result.source_method = 'hybrid'
            
            if output_dir:
                self._save_config_files(fused_result.config_data, config_type, output_dir)
            
            return fused_result
    
    def _enhance_with_rules(self, llm_result: ConversionResult, 
                           rule_result: ConversionResult, 
                           description: str) -> ConversionResult:
        """用规则系统增强LLM结果"""
        enhanced_config = llm_result.config_data.copy()
        improvements = llm_result.improvements.copy()
        
        # 检查并补充缺失的仿真参数
        if 'simulation' not in enhanced_config:
            enhanced_config['simulation'] = {}
        
        sim_config = enhanced_config['simulation']
        rule_sim = rule_result.config_data.get('simulation', {})
        
        # 补充缺失的仿真参数
        if 'duration' not in sim_config and 'duration' in rule_sim:
            sim_config['duration'] = rule_sim['duration']
            improvements.append("规则系统补充了仿真时长")
        
        if 'dt' not in sim_config and 'time_step' not in sim_config:
            if 'dt' in rule_sim:
                sim_config['dt'] = rule_sim['dt']
                improvements.append("规则系统补充了时间步长")
            elif 'time_step' in rule_sim:
                sim_config['time_step'] = rule_sim['time_step']
                improvements.append("规则系统补充了时间步长")
        
        if 'solver' not in sim_config and 'solver' in rule_sim:
            sim_config['solver'] = rule_sim['solver']
            improvements.append("规则系统补充了求解器")
        
        # 验证组件类型映射
        if 'components' in enhanced_config:
            components = enhanced_config['components']
            if isinstance(components, dict) and 'components' in components:
                comp_list = components['components']
            elif isinstance(components, list):
                comp_list = components
            else:
                comp_list = []
            
            # 使用规则系统的类型映射验证组件类型
            for comp in comp_list:
                if 'type' in comp:
                    original_type = comp['type']
                    # 检查类型是否在规则系统的映射中
                    if original_type in self.rule_converter.component_type_reverse_map:
                        mapped_type = self.rule_converter.component_type_reverse_map[original_type]
                        if mapped_type != original_type:
                            comp['type'] = mapped_type
                            improvements.append(f"规则系统修正了组件类型: {original_type} -> {mapped_type}")
        
        return ConversionResult(
            config_data=enhanced_config,
            confidence_score=min(0.95, llm_result.confidence_score + 0.1),
            llm_contribution=0.8,
            rule_contribution=0.2,
            validation_errors=llm_result.validation_errors,
            improvements=improvements,
            source_method='hybrid'
        )
    
    def _iterative_refinement(self, initial_config: Dict[str, Any], description: str, max_iterations: int = 3) -> Dict[str, Any]:
        """迭代优化配置生成质量"""
        current_config = initial_config.copy()
        
        for iteration in range(max_iterations):
            self.logger.info(f"开始第 {iteration + 1} 轮迭代优化")
            
            # 验证当前结果
            validation_issues = self._validate_config(current_config)
            
            if not validation_issues:
                self.logger.info(f"第 {iteration + 1} 轮验证通过，无需进一步优化")
                break
            
            # 修正发现的问题
            current_config = self._fix_validation_issues(current_config, validation_issues, description)
            
            self.logger.info(f"第 {iteration + 1} 轮优化完成，修正了 {len(validation_issues)} 个问题")
        
        return current_config
    
    def _validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置文件的完整性和正确性"""
        issues = []
        
        # 检查必要的顶级字段
        required_fields = ['simulation', 'components']
        for field in required_fields:
            if field not in config or not config[field]:
                issues.append(f"缺少必要字段: {field}")
        
        # 检查仿真参数
        if 'simulation' in config and config['simulation']:
            sim = config['simulation']
            if 'duration' not in sim or (isinstance(sim['duration'], (int, float)) and sim['duration'] <= 0):
                issues.append("仿真时长无效或缺失")
            if 'dt' not in sim and 'time_step' not in sim:
                issues.append("时间步长缺失")
            elif 'dt' in sim and isinstance(sim['dt'], (int, float)) and sim['dt'] <= 0:
                issues.append("时间步长无效")
            elif 'time_step' in sim and isinstance(sim['time_step'], (int, float)) and sim['time_step'] <= 0:
                issues.append("时间步长无效")
        
        # 检查组件定义
        if 'components' in config and config['components']:
            components = config['components']
            if isinstance(components, dict) and 'components' in components:
                comp_list = components['components']
            elif isinstance(components, list):
                comp_list = components
            else:
                comp_list = []
            
            for comp in comp_list:
                if not isinstance(comp, dict):
                    continue
                if 'type' not in comp:
                    comp_id = comp.get('id', '未知组件')
                    issues.append(f"组件 {comp_id} 缺少类型定义")
                
                # 检查关键参数
                comp_type = comp.get('type', '')
                comp_id = comp.get('id', '未知组件')
                if 'Reservoir' in comp_type:
                    params = comp.get('params', {})
                    if 'capacity' not in params and 'volume' not in params:
                        issues.append(f"水库组件 {comp_id} 缺少库容参数")
                elif 'Gate' in comp_type:
                    params = comp.get('params', {})
                    if 'max_flow_rate' not in params and 'flow_capacity' not in params:
                        issues.append(f"闸门组件 {comp_id} 缺少最大流量参数")
        
        # 检查连接关系
        if 'topology' in config and config['topology']:
            components = config.get('components', {})
            if isinstance(components, dict) and 'components' in components:
                comp_list = components['components']
            elif isinstance(components, list):
                comp_list = components
            else:
                comp_list = []
            
            comp_ids = {comp.get('id', '') for comp in comp_list if isinstance(comp, dict)}
            
            topology = config['topology']
            if isinstance(topology, list):
                for conn in topology:
                    if isinstance(conn, dict):
                        source = conn.get('from')
                        target = conn.get('to')
                        if source and source not in comp_ids:
                            issues.append(f"连接中的源组件 {source} 不存在")
                        if target and target not in comp_ids:
                            issues.append(f"连接中的目标组件 {target} 不存在")
        
        return issues
    
    def _fix_validation_issues(self, config: Dict[str, Any], issues: List[str], description: str) -> Dict[str, Any]:
        """修正验证中发现的问题"""
        fixed_config = config.copy()
        
        for issue in issues:
            if "缺少必要字段: simulation" in issue:
                # 添加默认仿真参数
                fixed_config['simulation'] = {
                    'duration': 3600,  # 默认1小时
                    'dt': 60,   # 默认1分钟
                    'name': '水利系统仿真',
                    'solver': 'rk4'
                }
            
            elif "缺少必要字段: components" in issue:
                # 尝试从描述中重新提取组件
                try:
                    rule_result = self.rule_converter.convert_language_to_config(
                        description, ConfigType.UNIVERSAL_CONFIG
                    )
                    if 'components' in rule_result:
                        fixed_config['components'] = rule_result['components']
                except Exception as e:
                    self.logger.warning(f"无法从规则系统获取组件: {e}")
                    # 创建基本组件结构
                    fixed_config['components'] = {'components': []}
            
            elif "仿真时长无效或缺失" in issue:
                # 从描述中提取时长信息
                duration_match = re.search(r'(\d+)\s*(?:小时|h|hour)', description)
                if duration_match:
                    fixed_config['simulation']['duration'] = int(duration_match.group(1)) * 3600
                else:
                    fixed_config['simulation']['duration'] = 3600
            
            elif "时间步长" in issue:
                # 设置合理的时间步长
                duration = fixed_config.get('simulation', {}).get('duration', 3600)
                fixed_config['simulation']['dt'] = min(60, max(1, duration // 100))
            
            elif "缺少库容参数" in issue:
                # 为水库添加默认库容
                comp_id = self._extract_component_id_from_issue(issue)
                self._add_missing_param(fixed_config, comp_id, 'capacity', 1000000)
            
            elif "缺少最大流量参数" in issue:
                # 为闸门添加默认最大流量
                comp_id = self._extract_component_id_from_issue(issue)
                self._add_missing_param(fixed_config, comp_id, 'max_flow_rate', 100)
        
        return fixed_config
    
    def _extract_component_id_from_issue(self, issue: str) -> str:
        """从问题描述中提取组件ID"""
        # 尝试提取组件ID
        parts = issue.split()
        for i, part in enumerate(parts):
            if part in ['组件', 'component'] and i + 1 < len(parts):
                return parts[i + 1]
        return ""
    
    def _add_missing_param(self, config: Dict[str, Any], comp_id: str, param_name: str, default_value: Any):
        """为指定组件添加缺失的参数"""
        components = config.get('components', {})
        if isinstance(components, dict) and 'components' in components:
            comp_list = components['components']
        elif isinstance(components, list):
            comp_list = components
        else:
            return
        
        for comp in comp_list:
            if isinstance(comp, dict) and comp.get('id') == comp_id:
                if 'params' not in comp:
                    comp['params'] = {}
                comp['params'][param_name] = default_value
                break
    
    def _enhance_with_llm(self, rule_result: ConversionResult,
                         llm_result: ConversionResult,
                         description: str) -> ConversionResult:
        """用LLM增强规则结果"""
        enhanced_config = rule_result.config_data.copy()
        improvements = rule_result.improvements.copy()
        
        # 如果LLM生成了更好的描述性信息，使用LLM的
        if llm_result.config_data and 'simulation' in llm_result.config_data:
            llm_sim = llm_result.config_data['simulation']
            if 'simulation' not in enhanced_config:
                enhanced_config['simulation'] = {}
            
            sim_config = enhanced_config['simulation']
            
            # 使用LLM的描述性字段
            if 'name' in llm_sim and 'name' not in sim_config:
                sim_config['name'] = llm_sim['name']
                improvements.append("LLM补充了仿真名称")
            
            if 'description' in llm_sim and 'description' not in sim_config:
                sim_config['description'] = llm_sim['description']
                improvements.append("LLM补充了仿真描述")
        
        return ConversionResult(
            config_data=enhanced_config,
            confidence_score=min(0.9, rule_result.confidence_score + 0.15),
            llm_contribution=0.3,
            rule_contribution=0.7,
            validation_errors=rule_result.validation_errors,
            improvements=improvements,
            source_method='hybrid'
        )
    
    def _fuse_results(self, llm_result: ConversionResult,
                     rule_result: ConversionResult,
                     description: str) -> ConversionResult:
        """融合LLM和规则结果"""
        # 选择更好的基础结果
        if llm_result.confidence_score >= rule_result.confidence_score:
            base_config = llm_result.config_data.copy()
            base_improvements = llm_result.improvements.copy()
            base_errors = llm_result.validation_errors.copy()
            llm_contrib = 0.6
            rule_contrib = 0.4
        else:
            base_config = rule_result.config_data.copy()
            base_improvements = rule_result.improvements.copy()
            base_errors = rule_result.validation_errors.copy()
            llm_contrib = 0.4
            rule_contrib = 0.6
        
        # 尝试从另一个结果中补充信息
        other_config = rule_result.config_data if llm_contrib > rule_contrib else llm_result.config_data
        
        if other_config:
            # 补充缺失的顶级键
            for key in ['simulation', 'components', 'topology', 'agents']:
                if key not in base_config and key in other_config:
                    base_config[key] = other_config[key]
                    base_improvements.append(f"融合了{key}配置")
        
        avg_confidence = (llm_result.confidence_score + rule_result.confidence_score) / 2
        
        return ConversionResult(
            config_data=base_config,
            confidence_score=avg_confidence,
            llm_contribution=llm_contrib,
            rule_contribution=rule_contrib,
            validation_errors=base_errors,
            improvements=base_improvements,
            source_method='hybrid'
        )
    
    def _save_config_files(self, config_data: Dict[str, Any], 
                          config_type: ConfigType, 
                          output_dir: Union[str, Path]):
        """保存配置文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if config_type == ConfigType.UNIVERSAL_CONFIG:
            # 保存为universal_config.yml
            config_file = output_path / 'universal_config.yml'
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
        
        elif config_type == ConfigType.UNIFIED_SINGLE:
            # 保存为unified_config.yml
            config_file = output_path / 'unified_config.yml'
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)
        
        else:
            # 使用原有的保存逻辑
            self.rule_converter._save_config_files(config_data, config_type, output_dir)
    
    def evaluate_conversion_quality(self, original_description: str, 
                                  generated_config: Dict[str, Any]) -> Dict[str, float]:
        """评估转换质量"""
        quality_metrics = {
            'completeness': 0.0,  # 完整性
            'accuracy': 0.0,      # 准确性
            'consistency': 0.0,   # 一致性
            'overall': 0.0        # 总体质量
        }
        
        # 检查完整性
        required_keys = ['simulation', 'components', 'topology']
        present_keys = sum(1 for key in required_keys if key in generated_config)
        quality_metrics['completeness'] = present_keys / len(required_keys)
        
        # 检查准确性（基于组件数量和类型）
        components = generated_config.get('components', {})
        if isinstance(components, dict) and 'components' in components:
            comp_list = components['components']
        elif isinstance(components, list):
            comp_list = components
        else:
            comp_list = []
        
        # 简单的准确性评估：有组件就给分
        if comp_list:
            quality_metrics['accuracy'] = min(1.0, len(comp_list) * 0.2)
        
        # 检查一致性（topology中的组件是否在components中定义）
        topology = generated_config.get('topology', [])
        if comp_list and topology:
            comp_ids = {comp.get('id', '') for comp in comp_list}
            topology_refs = set()
            for conn in topology:
                if 'from' in conn:
                    topology_refs.add(conn['from'])
                if 'to' in conn:
                    topology_refs.add(conn['to'])
            
            if topology_refs:
                consistent_refs = len(topology_refs.intersection(comp_ids))
                quality_metrics['consistency'] = consistent_refs / len(topology_refs)
        
        # 计算总体质量
        quality_metrics['overall'] = (
            quality_metrics['completeness'] * 0.4 +
            quality_metrics['accuracy'] * 0.4 +
            quality_metrics['consistency'] * 0.2
        )
        
        return quality_metrics


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增强版自然语言到配置文件转换器')
    parser.add_argument('description', help='自然语言描述文件路径或直接描述文本')
    parser.add_argument('-t', '--type', choices=['traditional', 'unified', 'universal', 'hardcoded'],
                       default='universal', help='目标配置文件类型')
    parser.add_argument('-s', '--strategy', choices=['llm', 'rule', 'hybrid'],
                       default='hybrid', help='转换策略')
    parser.add_argument('-o', '--output', help='输出目录', default='enhanced_config')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 读取描述文本
        if Path(args.description).exists():
            with open(args.description, 'r', encoding='utf-8') as f:
                description = f.read()
        else:
            description = args.description
        
        # 确定配置类型
        config_type_map = {
            'traditional': ConfigType.TRADITIONAL_MULTI,
            'unified': ConfigType.UNIFIED_SINGLE,
            'universal': ConfigType.UNIVERSAL_CONFIG,
            'hardcoded': ConfigType.HARDCODED
        }
        config_type = config_type_map[args.type]
        
        # 创建增强转换器
        converter = EnhancedLanguageToConfigConverter()
        
        # 转换配置文件
        result = converter.convert_language_to_config(
            description, config_type, args.output, args.strategy, 
            enable_iterative_refinement=True
        )
        
        print(f"转换完成！")
        print(f"策略: {result.source_method}")
        print(f"置信度: {result.confidence_score:.2f}")
        print(f"LLM贡献: {result.llm_contribution:.2f}")
        print(f"规则贡献: {result.rule_contribution:.2f}")
        
        if result.improvements:
            print("\n改进:")
            for improvement in result.improvements:
                print(f"  - {improvement}")
        
        if result.validation_errors:
            print("\n验证错误:")
            for error in result.validation_errors:
                print(f"  - {error}")
        
        # 评估质量
        quality = converter.evaluate_conversion_quality(description, result.config_data)
        print(f"\n质量评估:")
        print(f"  完整性: {quality['completeness']:.2f}")
        print(f"  准确性: {quality['accuracy']:.2f}")
        print(f"  一致性: {quality['consistency']:.2f}")
        print(f"  总体质量: {quality['overall']:.2f}")
        
        print(f"\n配置文件已保存到: {args.output}")
        
    except Exception as e:
        print(f"转换失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()