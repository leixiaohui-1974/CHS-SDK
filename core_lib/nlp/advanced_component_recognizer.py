#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级组件识别系统
实现同义词映射、上下文推理、模糊匹配和自动纠错
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import defaultdict
import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)

@dataclass
class ComponentMatch:
    """组件匹配结果"""
    component_type: str
    component_name: str
    confidence: float
    match_method: str  # 匹配方法：exact, synonym, fuzzy, context
    original_text: str
    position: Tuple[int, int]  # 在文本中的位置

@dataclass
class ContextClue:
    """上下文线索"""
    keyword: str
    component_types: List[str]
    weight: float
    context_window: int = 10  # 上下文窗口大小

class AdvancedComponentRecognizer:
    """高级组件识别器"""
    
    def __init__(self):
        self.component_synonyms = self._initialize_component_synonyms()
        self.context_clues = self._initialize_context_clues()
        self.component_patterns = self._initialize_component_patterns()
        self.correction_rules = self._initialize_correction_rules()
        self.component_relationships = self._initialize_component_relationships()
        
        # 初始化jieba分词
        self._setup_jieba()
    
    def _setup_jieba(self):
        """设置jieba分词器"""
        # 添加水利工程专业词汇
        water_engineering_terms = [
            "水库", "闸门", "泵站", "渠道", "管道", "阀门", "传感器",
            "水轮机", "发电站", "调节池", "沉淀池", "过滤器", "控制器",
            "流量计", "水位计", "压力计", "温度计", "湿度计", "风速计",
            "蓄水池", "配水池", "清水池", "污水池", "处理池", "曝气池"
        ]
        
        for term in water_engineering_terms:
            jieba.add_word(term, freq=1000, tag='water_eng')
    
    def _initialize_component_synonyms(self) -> Dict[str, List[str]]:
        """初始化组件同义词映射"""
        synonyms = {
            "Reservoir": [
                "水库", "蓄水库", "水库系统", "储水库", "调节水库", "防洪水库",
                "reservoir", "water_reservoir", "storage_reservoir", "dam_reservoir",
                "蓄水池", "储水池", "水池", "调蓄池", "调节池", "滞洪池"
            ],
            "Lake": [
                "湖泊", "湖", "天然湖", "人工湖", "调节湖", "蓄水湖",
                "lake", "artificial_lake", "natural_lake", "regulation_lake"
            ],
            "Pond": [
                "池塘", "水塘", "鱼塘", "养殖塘", "蓄水塘", "调节塘",
                "pond", "fish_pond", "storage_pond", "regulation_pond"
            ],
            "Gate": [
                "闸门", "水闸", "闸", "调节闸", "控制闸", "泄洪闸", "进水闸", "出水闸",
                "gate", "water_gate", "control_gate", "flood_gate", "sluice_gate",
                "闸阀", "水闸阀", "调节阀门", "控制阀"
            ],
            "Pump": [
                "泵", "水泵", "抽水泵", "离心泵", "潜水泵", "增压泵", "循环泵",
                "pump", "water_pump", "centrifugal_pump", "submersible_pump",
                "抽水机", "水泵机组", "泵机"
            ],
            "PumpStation": [
                "泵站", "抽水站", "提升泵站", "排水泵站", "供水泵站", "加压泵站",
                "pump_station", "pumping_station", "water_pumping_station",
                "泵房", "水泵站", "抽水泵站"
            ],
            "Valve": [
                "阀门", "阀", "调节阀", "控制阀", "截止阀", "球阀", "蝶阀", "闸阀",
                "valve", "control_valve", "regulation_valve", "ball_valve",
                "水阀", "流量阀", "压力阀", "安全阀"
            ],
            "ValveStation": [
                "阀门站", "阀站", "调节阀站", "控制阀站", "分水阀站",
                "valve_station", "control_valve_station", "regulation_station"
            ],
            "Pipe": [
                "管道", "管", "水管", "输水管", "供水管", "排水管", "压力管",
                "pipe", "water_pipe", "supply_pipe", "drainage_pipe",
                "管线", "输水管线", "管路", "水管路"
            ],
            "Canal": [
                "渠道", "水渠", "灌溉渠", "排水渠", "输水渠", "明渠", "暗渠",
                "canal", "water_canal", "irrigation_canal", "drainage_canal",
                "沟渠", "水沟", "排水沟", "灌溉沟"
            ],
            "UnifiedCanal": [
                "统一渠道", "综合渠道", "多功能渠道", "联合渠道",
                "unified_canal", "integrated_canal", "multi_purpose_canal"
            ],
            "RiverChannel": [
                "河道", "河流", "河", "天然河道", "人工河道", "河床", "河槽",
                "river", "river_channel", "natural_river", "artificial_river",
                "水道", "河流水道", "航道"
            ],
            "Junction": [
                "汇合点", "交汇点", "分流点", "节点", "连接点", "分水口", "汇水口",
                "junction", "confluence", "bifurcation", "node", "connection_point",
                "分叉口", "三通", "四通", "管道接头"
            ],
            "Sensor": [
                "传感器", "探测器", "检测器", "监测器", "测量器", "感应器",
                "sensor", "detector", "monitor", "measuring_device",
                "水位计", "流量计", "压力计", "温度计", "湿度计"
            ],
            "WaterTurbine": [
                "水轮机", "水力发电机", "水力机组", "发电水轮机", "涡轮机",
                "water_turbine", "hydro_turbine", "hydraulic_turbine",
                "水轮发电机", "水力涡轮机"
            ],
            "HydropowerStation": [
                "水电站", "水力发电站", "水电厂", "水力发电厂", "小水电站",
                "hydropower_station", "hydro_power_plant", "water_power_station",
                "发电站", "水力电站", "水电工程"
            ]
        }
        return synonyms
    
    def _initialize_context_clues(self) -> List[ContextClue]:
        """初始化上下文线索"""
        clues = [
            # 水库相关上下文
            ContextClue("蓄水", ["Reservoir", "Lake", "Pond"], 0.8),
            ContextClue("库容", ["Reservoir"], 0.9),
            ContextClue("防洪", ["Reservoir", "Gate"], 0.7),
            ContextClue("调节", ["Reservoir", "Gate", "Valve"], 0.6),
            
            # 泵站相关上下文
            ContextClue("抽水", ["Pump", "PumpStation"], 0.9),
            ContextClue("提升", ["Pump", "PumpStation"], 0.8),
            ContextClue("加压", ["Pump", "PumpStation"], 0.8),
            ContextClue("排水", ["Pump", "PumpStation", "Canal"], 0.7),
            
            # 闸门相关上下文
            ContextClue("控制", ["Gate", "Valve", "ValveStation"], 0.7),
            ContextClue("调节", ["Gate", "Valve"], 0.7),
            ContextClue("泄洪", ["Gate"], 0.9),
            ContextClue("开启", ["Gate", "Valve"], 0.8),
            ContextClue("关闭", ["Gate", "Valve"], 0.8),
            
            # 管道相关上下文
            ContextClue("输水", ["Pipe", "Canal"], 0.8),
            ContextClue("供水", ["Pipe", "PumpStation"], 0.8),
            ContextClue("管径", ["Pipe"], 0.9),
            ContextClue("管长", ["Pipe"], 0.9),
            
            # 渠道相关上下文
            ContextClue("灌溉", ["Canal"], 0.9),
            ContextClue("明渠", ["Canal"], 0.9),
            ContextClue("渠宽", ["Canal"], 0.9),
            ContextClue("渠深", ["Canal"], 0.9),
            
            # 传感器相关上下文
            ContextClue("监测", ["Sensor"], 0.8),
            ContextClue("测量", ["Sensor"], 0.8),
            ContextClue("检测", ["Sensor"], 0.8),
            ContextClue("数据采集", ["Sensor"], 0.9),
            
            # 发电相关上下文
            ContextClue("发电", ["WaterTurbine", "HydropowerStation"], 0.9),
            ContextClue("水力发电", ["WaterTurbine", "HydropowerStation"], 0.95),
            ContextClue("装机容量", ["WaterTurbine", "HydropowerStation"], 0.9),
            ContextClue("电力", ["WaterTurbine", "HydropowerStation"], 0.7)
        ]
        return clues
    
    def _initialize_component_patterns(self) -> Dict[str, List[str]]:
        """初始化组件识别模式"""
        patterns = {
            "Reservoir": [
                r'([\u4e00-\u9fff\w]+)[水库库]',
                r'([\u4e00-\u9fff\w]+)[蓄储调节]水[库池]',
                r'([\u4e00-\u9fff\w]+)水库系统',
                r'水库([\u4e00-\u9fff\w]+)',
                r'reservoir[_\s]*([\w]+)',
                r'([\w]+)[_\s]*reservoir'
            ],
            "Gate": [
                r'([\u4e00-\u9fff\w]+)[闸门]',
                r'([\u4e00-\u9fff\w]+)[水闸]',
                r'([\u4e00-\u9fff\w]+)[控制调节泄洪进出]水?闸',
                r'闸门([\u4e00-\u9fff\w]+)',
                r'gate[_\s]*([\w]+)',
                r'([\w]+)[_\s]*gate'
            ],
            "Pump": [
                r'([\u4e00-\u9fff\w]+)[泵]',
                r'([\u4e00-\u9fff\w]+)[水抽离心潜增循环]泵',
                r'泵([\u4e00-\u9fff\w]+)',
                r'pump[_\s]*([\w]+)',
                r'([\w]+)[_\s]*pump'
            ],
            "PumpStation": [
                r'([\u4e00-\u9fff\w]+)[泵站]',
                r'([\u4e00-\u9fff\w]+)[抽水提升排水供水加压]泵?站',
                r'泵站([\u4e00-\u9fff\w]+)',
                r'pump[_\s]*station[_\s]*([\w]+)',
                r'([\w]+)[_\s]*pump[_\s]*station'
            ],
            "Valve": [
                r'([\u4e00-\u9fff\w]+)[阀门阀]',
                r'([\u4e00-\u9fff\w]+)[调节控制截止球蝶闸流量压力安全]阀',
                r'阀门?([\u4e00-\u9fff\w]+)',
                r'valve[_\s]*([\w]+)',
                r'([\w]+)[_\s]*valve'
            ],
            "Pipe": [
                r'([\u4e00-\u9fff\w]+)[管道管]',
                r'([\u4e00-\u9fff\w]+)[水输供排压力]管',
                r'管道?([\u4e00-\u9fff\w]+)',
                r'pipe[_\s]*([\w]+)',
                r'([\w]+)[_\s]*pipe'
            ],
            "Canal": [
                r'([\u4e00-\u9fff\w]+)[渠道渠]',
                r'([\u4e00-\u9fff\w]+)[水灌溉排水输明暗]渠',
                r'渠道?([\u4e00-\u9fff\w]+)',
                r'canal[_\s]*([\w]+)',
                r'([\w]+)[_\s]*canal'
            ],
            "Sensor": [
                r'([\u4e00-\u9fff\w]+)[传感器探测器检测器监测器]',
                r'([\u4e00-\u9fff\w]+)[水位流量压力温度湿度]计',
                r'传感器([\u4e00-\u9fff\w]+)',
                r'sensor[_\s]*([\w]+)',
                r'([\w]+)[_\s]*sensor'
            ]
        }
        return patterns
    
    def _initialize_correction_rules(self) -> Dict[str, str]:
        """初始化纠错规则"""
        rules = {
            # 常见拼写错误
            "水库库": "水库",
            "闸门门": "闸门",
            "泵站站": "泵站",
            "管道道": "管道",
            "渠道道": "渠道",
            "阀门门": "阀门",
            
            # 英文拼写错误
            "resevoir": "reservoir",
            "resevior": "reservoir",
            "pumping_staion": "pumping_station",
            "wate_pump": "water_pump",
            "contol_valve": "control_valve",
            
            # 中英文混合错误
            "水库reservoir": "水库",
            "pump泵": "泵",
            "gate闸门": "闸门",
            "valve阀门": "阀门"
        }
        return rules
    
    def _initialize_component_relationships(self) -> Dict[str, List[str]]:
        """初始化组件关系"""
        relationships = {
            "Reservoir": ["Gate", "Sensor", "Pump", "Canal", "Pipe"],
            "Lake": ["Sensor", "Pump", "Canal", "Pipe"],
            "Pond": ["Sensor", "Pump", "Valve"],
            "Gate": ["Reservoir", "Canal", "RiverChannel", "Sensor"],
            "Pump": ["Reservoir", "Lake", "Pond", "Pipe", "Sensor"],
            "PumpStation": ["Pump", "Pipe", "Canal", "Sensor", "Valve"],
            "Valve": ["Pipe", "Canal", "Sensor"],
            "ValveStation": ["Valve", "Pipe", "Sensor"],
            "Pipe": ["Pump", "Valve", "Junction", "Sensor"],
            "Canal": ["Gate", "Pump", "Junction", "Sensor"],
            "Junction": ["Pipe", "Canal", "RiverChannel"],
            "Sensor": ["Reservoir", "Gate", "Pump", "Valve", "Pipe", "Canal"],
            "WaterTurbine": ["Reservoir", "Gate", "Sensor", "HydropowerStation"],
            "HydropowerStation": ["WaterTurbine", "Reservoir", "Gate", "Sensor"]
        }
        return relationships
    
    def recognize_components(self, text: str, enable_fuzzy: bool = True, 
                           enable_context: bool = True) -> List[ComponentMatch]:
        """识别组件"""
        matches = []
        
        # 1. 精确匹配和同义词匹配
        exact_matches = self._exact_and_synonym_matching(text)
        matches.extend(exact_matches)
        
        # 2. 模式匹配
        pattern_matches = self._pattern_matching(text)
        matches.extend(pattern_matches)
        
        # 3. 模糊匹配
        if enable_fuzzy:
            fuzzy_matches = self._fuzzy_matching(text, existing_matches=matches)
            matches.extend(fuzzy_matches)
        
        # 4. 上下文推理
        if enable_context:
            context_matches = self._context_inference(text, existing_matches=matches)
            matches.extend(context_matches)
        
        # 5. 去重和排序
        matches = self._deduplicate_and_rank(matches)
        
        # 6. 自动纠错
        matches = self._auto_correction(matches, text)
        
        return matches
    
    def _exact_and_synonym_matching(self, text: str) -> List[ComponentMatch]:
        """精确匹配和同义词匹配"""
        matches = []
        
        for component_type, synonyms in self.component_synonyms.items():
            for synonym in synonyms:
                # 查找所有匹配位置
                pattern = re.escape(synonym)
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start, end = match.span()
                    
                    # 检查是否为完整词汇（避免部分匹配）
                    if self._is_complete_word(text, start, end):
                        confidence = 0.95 if synonym == component_type.lower() else 0.85
                        
                        component_match = ComponentMatch(
                            component_type=component_type,
                            component_name=self._generate_component_name(component_type, synonym),
                            confidence=confidence,
                            match_method="exact" if synonym == component_type.lower() else "synonym",
                            original_text=synonym,
                            position=(start, end)
                        )
                        matches.append(component_match)
        
        return matches
    
    def _pattern_matching(self, text: str) -> List[ComponentMatch]:
        """模式匹配"""
        matches = []
        
        for component_type, patterns in self.component_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start, end = match.span()
                    matched_text = match.group(0)
                    
                    # 提取组件名称
                    if match.groups():
                        component_name = match.group(1)
                    else:
                        component_name = self._extract_name_from_match(matched_text, component_type)
                    
                    component_match = ComponentMatch(
                        component_type=component_type,
                        component_name=component_name,
                        confidence=0.8,
                        match_method="pattern",
                        original_text=matched_text,
                        position=(start, end)
                    )
                    matches.append(component_match)
        
        return matches
    
    def _fuzzy_matching(self, text: str, existing_matches: List[ComponentMatch], 
                       threshold: float = 0.7) -> List[ComponentMatch]:
        """模糊匹配"""
        matches = []
        
        # 分词
        words = list(jieba.cut(text))
        
        # 获取已匹配的位置，避免重复匹配
        matched_positions = set()
        for match in existing_matches:
            for i in range(match.position[0], match.position[1]):
                matched_positions.add(i)
        
        for word in words:
            if len(word) < 2:  # 跳过太短的词
                continue
            
            # 检查是否已被匹配
            word_start = text.find(word)
            if word_start != -1 and any(pos in matched_positions for pos in range(word_start, word_start + len(word))):
                continue
            
            best_match = None
            best_similarity = 0
            
            # 与所有同义词进行模糊匹配
            for component_type, synonyms in self.component_synonyms.items():
                for synonym in synonyms:
                    similarity = SequenceMatcher(None, word.lower(), synonym.lower()).ratio()
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = (component_type, synonym)
            
            if best_match:
                component_type, matched_synonym = best_match
                word_start = text.find(word)
                word_end = word_start + len(word)
                
                component_match = ComponentMatch(
                    component_type=component_type,
                    component_name=self._generate_component_name(component_type, word),
                    confidence=best_similarity * 0.7,  # 模糊匹配置信度较低
                    match_method="fuzzy",
                    original_text=word,
                    position=(word_start, word_end)
                )
                matches.append(component_match)
        
        return matches
    
    def _context_inference(self, text: str, existing_matches: List[ComponentMatch]) -> List[ComponentMatch]:
        """上下文推理"""
        matches = []
        
        # 分析上下文线索
        context_scores = defaultdict(float)
        
        for clue in self.context_clues:
            clue_positions = []
            for match in re.finditer(re.escape(clue.keyword), text, re.IGNORECASE):
                clue_positions.append(match.start())
            
            if clue_positions:
                for component_type in clue.component_types:
                    context_scores[component_type] += clue.weight * len(clue_positions)
        
        # 查找可能的组件提及
        words = list(jieba.cut(text))
        
        for word in words:
            if len(word) < 2:
                continue
            
            # 检查是否已被识别
            if any(word in match.original_text for match in existing_matches):
                continue
            
            # 基于上下文评分推断组件类型
            word_position = text.find(word)
            if word_position == -1:
                continue
            
            best_component_type = None
            best_score = 0
            
            for component_type, score in context_scores.items():
                # 检查上下文窗口内是否有相关线索
                window_score = self._calculate_context_window_score(
                    text, word_position, component_type
                )
                total_score = score * window_score
                
                if total_score > best_score and total_score > 0.3:
                    best_score = total_score
                    best_component_type = component_type
            
            if best_component_type:
                component_match = ComponentMatch(
                    component_type=best_component_type,
                    component_name=self._generate_component_name(best_component_type, word),
                    confidence=min(best_score, 0.8),
                    match_method="context",
                    original_text=word,
                    position=(word_position, word_position + len(word))
                )
                matches.append(component_match)
        
        return matches
    
    def _calculate_context_window_score(self, text: str, word_position: int, 
                                      component_type: str, window_size: int = 50) -> float:
        """计算上下文窗口评分"""
        start = max(0, word_position - window_size)
        end = min(len(text), word_position + window_size)
        context_window = text[start:end]
        
        score = 0
        for clue in self.context_clues:
            if component_type in clue.component_types:
                if clue.keyword in context_window:
                    # 计算距离权重
                    clue_pos = context_window.find(clue.keyword)
                    distance = abs(clue_pos - (word_position - start))
                    distance_weight = max(0, 1 - distance / window_size)
                    score += clue.weight * distance_weight
        
        return min(score, 1.0)
    
    def _deduplicate_and_rank(self, matches: List[ComponentMatch]) -> List[ComponentMatch]:
        """去重和排序"""
        # 按位置分组，处理重叠匹配
        position_groups = defaultdict(list)
        for match in matches:
            # 使用位置范围作为键
            key = (match.position[0] // 10, match.position[1] // 10)  # 粗粒度分组
            position_groups[key].append(match)
        
        deduplicated_matches = []
        
        for group in position_groups.values():
            if len(group) == 1:
                deduplicated_matches.extend(group)
            else:
                # 选择置信度最高的匹配
                best_match = max(group, key=lambda m: m.confidence)
                deduplicated_matches.append(best_match)
        
        # 按置信度排序
        deduplicated_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return deduplicated_matches
    
    def _auto_correction(self, matches: List[ComponentMatch], text: str) -> List[ComponentMatch]:
        """自动纠错"""
        corrected_matches = []
        
        for match in matches:
            original_text = match.original_text
            
            # 应用纠错规则
            corrected_text = original_text
            for error, correction in self.correction_rules.items():
                if error in original_text:
                    corrected_text = original_text.replace(error, correction)
                    break
            
            # 如果有纠错，更新匹配结果
            if corrected_text != original_text:
                corrected_match = ComponentMatch(
                    component_type=match.component_type,
                    component_name=self._generate_component_name(match.component_type, corrected_text),
                    confidence=match.confidence * 0.9,  # 纠错后置信度略降
                    match_method=f"{match.match_method}_corrected",
                    original_text=corrected_text,
                    position=match.position
                )
                corrected_matches.append(corrected_match)
            else:
                corrected_matches.append(match)
        
        return corrected_matches
    
    def _is_complete_word(self, text: str, start: int, end: int) -> bool:
        """检查是否为完整词汇"""
        # 检查前后字符是否为词边界
        before_char = text[start-1] if start > 0 else ' '
        after_char = text[end] if end < len(text) else ' '
        
        # 中文字符或标点符号视为词边界
        word_boundary_chars = ' \t\n\r，。；：！？、（）【】《》