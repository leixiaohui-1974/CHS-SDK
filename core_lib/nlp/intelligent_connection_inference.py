#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能连接推理系统
基于水利工程原理自动推断隐含连接关系
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import networkx as nx

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    """连接类型"""
    FLOW = "flow"  # 流量连接
    CONTROL = "control"  # 控制连接
    SIGNAL = "signal"  # 信号连接
    DATA = "data"  # 数据连接
    POWER = "power"  # 电力连接
    STRUCTURAL = "structural"  # 结构连接

class FlowDirection(Enum):
    """流向"""
    UPSTREAM = "upstream"  # 上游
    DOWNSTREAM = "downstream"  # 下游
    BIDIRECTIONAL = "bidirectional"  # 双向

@dataclass
class ConnectionRule:
    """连接规则"""
    source_type: str
    target_type: str
    connection_type: ConnectionType
    flow_direction: FlowDirection
    probability: float
    conditions: List[str] = None  # 连接条件
    constraints: List[str] = None  # 约束条件

@dataclass
class InferredConnection:
    """推断的连接"""
    source_component: str
    target_component: str
    connection_type: ConnectionType
    flow_direction: FlowDirection
    confidence: float
    inference_method: str
    supporting_evidence: List[str]
    position_in_text: Optional[Tuple[int, int]] = None

@dataclass
class ComponentContext:
    """组件上下文"""
    component_name: str
    component_type: str
    position: Tuple[int, int]
    parameters: Dict[str, any] = None
    nearby_keywords: List[str] = None

class IntelligentConnectionInference:
    """智能连接推理系统"""
    
    def __init__(self):
        self.connection_rules = self._initialize_connection_rules()
        self.flow_patterns = self._initialize_flow_patterns()
        self.control_patterns = self._initialize_control_patterns()
        self.topology_rules = self._initialize_topology_rules()
        self.engineering_constraints = self._initialize_engineering_constraints()
        
    def _initialize_connection_rules(self) -> List[ConnectionRule]:
        """初始化连接规则"""
        rules = [
            # 水库连接规则
            ConnectionRule("Reservoir", "Gate", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.9,
                         conditions=["出水", "泄洪", "放水"], constraints=["水位控制"]),
            ConnectionRule("Gate", "Reservoir", ConnectionType.CONTROL, FlowDirection.UPSTREAM, 0.8,
                         conditions=["控制", "调节"], constraints=["水位监测"]),
            ConnectionRule("Reservoir", "Canal", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.85,
                         conditions=["灌溉", "供水", "输水"]),
            ConnectionRule("Reservoir", "Pipe", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.8,
                         conditions=["供水", "输水"]),
            ConnectionRule("Reservoir", "WaterTurbine", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.95,
                         conditions=["发电", "水力发电"]),
            
            # 泵站连接规则
            ConnectionRule("PumpStation", "Reservoir", ConnectionType.FLOW, FlowDirection.UPSTREAM, 0.9,
                         conditions=["抽水", "提升", "补水"]),
            ConnectionRule("PumpStation", "Pipe", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.85,
                         conditions=["供水", "输水", "加压"]),
            ConnectionRule("PumpStation", "Canal", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.8,
                         conditions=["灌溉", "排水"]),
            ConnectionRule("Pump", "PumpStation", ConnectionType.STRUCTURAL, FlowDirection.BIDIRECTIONAL, 0.95),
            
            # 闸门连接规则
            ConnectionRule("Gate", "Canal", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.9,
                         conditions=["泄流", "放水", "灌溉"]),
            ConnectionRule("Gate", "RiverChannel", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.85,
                         conditions=["泄洪", "排水"]),
            ConnectionRule("Gate", "Pipe", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.75,
                         conditions=["供水", "输水"]),
            
            # 阀门连接规则
            ConnectionRule("Valve", "Pipe", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.9,
                         conditions=["控制", "调节", "截止"]),
            ConnectionRule("Pipe", "Valve", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.9),
            ConnectionRule("ValveStation", "Pipe", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.85),
            ConnectionRule("Valve", "ValveStation", ConnectionType.STRUCTURAL, FlowDirection.BIDIRECTIONAL, 0.95),
            
            # 管道连接规则
            ConnectionRule("Pipe", "Junction", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.9),
            ConnectionRule("Junction", "Pipe", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.9),
            ConnectionRule("Pipe", "Canal", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.7,
                         conditions=["转换", "连接"]),
            
            # 渠道连接规则
            ConnectionRule("Canal", "Junction", ConnectionType.FLOW, FlowDirection.BIDIRECTIONAL, 0.85),
            ConnectionRule("Canal", "RiverChannel", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.8,
                         conditions=["汇入", "排入"]),
            ConnectionRule("RiverChannel", "Canal", ConnectionType.FLOW, FlowDirection.UPSTREAM, 0.75,
                         conditions=["引水", "取水"]),
            
            # 传感器连接规则
            ConnectionRule("Sensor", "Reservoir", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.9,
                         conditions=["监测", "测量"]),
            ConnectionRule("Sensor", "Gate", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.85),
            ConnectionRule("Sensor", "Pump", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.85),
            ConnectionRule("Sensor", "Valve", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.8),
            ConnectionRule("Sensor", "Canal", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.8),
            ConnectionRule("Sensor", "Pipe", ConnectionType.SIGNAL, FlowDirection.UPSTREAM, 0.75),
            
            # 水轮机和水电站连接规则
            ConnectionRule("WaterTurbine", "HydropowerStation", ConnectionType.STRUCTURAL, FlowDirection.BIDIRECTIONAL, 0.95),
            ConnectionRule("WaterTurbine", "RiverChannel", ConnectionType.FLOW, FlowDirection.DOWNSTREAM, 0.8,
                         conditions=["尾水", "排水"]),
            ConnectionRule("HydropowerStation", "Reservoir", ConnectionType.FLOW, FlowDirection.UPSTREAM, 0.9,
                         conditions=["取水", "引水"]),
        ]
        return rules
    
    def _initialize_flow_patterns(self) -> Dict[str, List[str]]:
        """初始化流向模式"""
        patterns = {
            "downstream_indicators": [
                "流向", "流入", "流出", "排入", "汇入", "注入", "输送到", "供给",
                "→", "-->", "=>", "流经", "通过", "经过", "到达", "进入"
            ],
            "upstream_indicators": [
                "来自", "源于", "取自", "引自", "抽取", "提取", "←", "<--", "<==",
                "回流", "返回", "逆流", "上游"
            ],
            "bidirectional_indicators": [
                "连接", "相连", "互通", "双向", "往返", "循环", "<->", "<==>",
                "交换", "互换", "对接"
            ],
            "control_indicators": [
                "控制", "调节", "管理", "操作", "驱动", "启动", "停止", "开启", "关闭",
                "监控", "指挥", "调度"
            ],
            "signal_indicators": [
                "监测", "检测", "测量", "感知", "采集", "传输", "发送", "接收",
                "反馈", "报告", "通信", "数据"
            ]
        }
        return patterns
    
    def _initialize_control_patterns(self) -> Dict[str, float]:
        """初始化控制模式"""
        patterns = {
            "PID控制": 0.9,
            "自动控制": 0.85,
            "手动控制": 0.7,
            "远程控制": 0.8,
            "联动控制": 0.85,
            "反馈控制": 0.8,
            "前馈控制": 0.75,
            "模糊控制": 0.7,
            "智能控制": 0.8
        }
        return patterns
    
    def _initialize_topology_rules(self) -> Dict[str, List[str]]:
        """初始化拓扑规则"""
        rules = {
            "series_components": [  # 串联组件
                "Reservoir->Gate->Canal",
                "Reservoir->WaterTurbine->RiverChannel",
                "PumpStation->Pipe->Valve",
                "Canal->Junction->Pipe",
                "Valve->Pipe->Junction"
            ],
            "parallel_components": [  # 并联组件
                "Gate|Gate->Canal",
                "Pump|Pump->Pipe",
                "Valve|Valve->Pipe"
            ],
            "feedback_loops": [  # 反馈回路
                "Reservoir->Gate->Canal->Sensor->Reservoir",
                "Pump->Pipe->Sensor->Pump",
                "Valve->Pipe->Sensor->Valve"
            ],
            "hierarchical_control": [  # 分层控制
                "HydropowerStation->WaterTurbine->Gate",
                "PumpStation->Pump->Valve",
                "ValveStation->Valve->Pipe"
            ]
        }
        return rules
    
    def _initialize_engineering_constraints(self) -> Dict[str, List[str]]:
        """初始化工程约束"""
        constraints = {
            "flow_constraints": [
                "水只能从高处流向低处（重力流）",
                "泵可以将水从低处提升到高处",
                "闸门控制水流的通断和流量",
                "阀门调节管道中的流量和压力",
                "管道承受一定的压力范围",
                "渠道适用于大流量低压力输水"
            ],
            "control_constraints": [
                "传感器只能监测不能控制",
                "执行器（闸门、阀门、泵）可以被控制",
                "控制信号从控制器发出到执行器",
                "反馈信号从传感器返回到控制器",
                "一个组件可以被多个控制器控制",
                "一个控制器可以控制多个组件"
            ],
            "structural_constraints": [
                "泵必须属于泵站",
                "水轮机必须属于水电站",
                "阀门可以独立存在或属于阀门站",
                "传感器可以安装在任何需要监测的位置",
                "管道连接各个组件",
                "渠道用于开放式输水"
            ]
        }
        return constraints
    
    def infer_connections(self, components: List[ComponentContext], 
                         text: str = "") -> List[InferredConnection]:
        """推断连接关系"""
        connections = []
        
        # 1. 基于规则的连接推断
        rule_based_connections = self._rule_based_inference(components)
        connections.extend(rule_based_connections)
        
        # 2. 基于文本的连接推断
        if text:
            text_based_connections = self._text_based_inference(components, text)
            connections.extend(text_based_connections)
        
        # 3. 基于拓扑的连接推断
        topology_connections = self._topology_based_inference(components, connections)
        connections.extend(topology_connections)
        
        # 4. 基于工程约束的连接验证和补充
        validated_connections = self._validate_and_supplement_connections(connections, components)
        
        # 5. 去重和排序
        final_connections = self._deduplicate_and_rank_connections(validated_connections)
        
        return final_connections
    
    def _rule_based_inference(self, components: List[ComponentContext]) -> List[InferredConnection]:
        """基于规则的连接推断"""
        connections = []
        
        # 为每对组件检查连接规则
        for i, source_comp in enumerate(components):
            for j, target_comp in enumerate(components):
                if i == j:  # 跳过自连接
                    continue
                
                # 查找适用的连接规则
                applicable_rules = self._find_applicable_rules(
                    source_comp.component_type, target_comp.component_type
                )
                
                for rule in applicable_rules:
                    # 检查连接条件
                    if self._check_connection_conditions(rule, source_comp, target_comp):
                        connection = InferredConnection(
                            source_component=source_comp.component_name,
                            target_component=target_comp.component_name,
                            connection_type=rule.connection_type,
                            flow_direction=rule.flow_direction,
                            confidence=rule.probability,
                            inference_method="rule_based",
                            supporting_evidence=[f"规则: {rule.source_type}->{rule.target_type}"]
                        )
                        connections.append(connection)
        
        return connections
    
    def _text_based_inference(self, components: List[ComponentContext], 
                            text: str) -> List[InferredConnection]:
        """基于文本的连接推断"""
        connections = []
        
        # 查找明确的连接表述
        explicit_connections = self._find_explicit_connections(components, text)
        connections.extend(explicit_connections)
        
        # 基于流向指示词推断连接
        flow_connections = self._infer_flow_connections(components, text)
        connections.extend(flow_connections)
        
        # 基于控制关系推断连接
        control_connections = self._infer_control_connections(components, text)
        connections.extend(control_connections)
        
        return connections
    
    def _find_explicit_connections(self, components: List[ComponentContext], 
                                 text: str) -> List[InferredConnection]:
        """查找明确的连接表述"""
        connections = []
        
        # 创建组件名称到组件的映射
        comp_map = {comp.component_name: comp for comp in components}
        
        # 连接模式
        connection_patterns = [
            r'([\u4e00-\u9fff\w]+)\s*(?:连接|连通|接入|流入|流向|输送到|供给)\s*([\u4e00-\u9fff\w]+)',
            r'([\u4e00-\u9fff\w]+)\s*(?:→|-->|=>)\s*([\u4e00-\u9fff\w]+)',
            r'从\s*([\u4e00-\u9fff\w]+)\s*(?:到|至|向)\s*([\u4e00-\u9fff\w]+)',
            r'([\u4e00-\u9fff\w]+)\s*(?:控制|调节|管理)\s*([\u4e00-\u9fff\w]+)',
            r'([\u4e00-\u9fff\w]+)\s*(?:监测|检测|测量)\s*([\u4e00-\u9fff\w]+)'
        ]
        
        for pattern in connection_patterns:
            for match in re.finditer(pattern, text):
                source_name = match.group(1)
                target_name = match.group(2)
                
                # 查找匹配的组件
                source_comp = self._find_component_by_name(source_name, components)
                target_comp = self._find_component_by_name(target_name, components)
                
                if source_comp and target_comp:
                    # 确定连接类型
                    connection_type = self._determine_connection_type_from_text(match.group(0))
                    flow_direction = self._determine_flow_direction_from_text(match.group(0))
                    
                    connection = InferredConnection(
                        source_component=source_comp.component_name,
                        target_component=target_comp.component_name,
                        connection_type=connection_type,
                        flow_direction=flow_direction,
                        confidence=0.9,
                        inference_method="explicit_text",
                        supporting_evidence=[match.group(0)],
                        position_in_text=match.span()
                    )
                    connections.append(connection)
        
        return connections
    
    def _infer_flow_connections(self, components: List[ComponentContext], 
                              text: str) -> List[InferredConnection]:
        """基于流向指示词推断连接"""
        connections = []
        
        # 分析文本中的流向描述
        flow_descriptions = self._extract_flow_descriptions(text)
        
        for description in flow_descriptions:
            # 在描述中查找组件
            mentioned_components = []
            for comp in components:
                if comp.component_name in description['text'] or \
                   any(keyword in description['text'] for keyword in comp.nearby_keywords or []):
                    mentioned_components.append(comp)
            
            # 基于流向指示词推断连接
            if len(mentioned_components) >= 2:
                flow_direction = description['direction']
                
                for i in range(len(mentioned_components) - 1):
                    source_comp = mentioned_components[i]
                    target_comp = mentioned_components[i + 1]
                    
                    # 根据流向调整源和目标
                    if flow_direction == FlowDirection.UPSTREAM:
                        source_comp, target_comp = target_comp, source_comp
                    
                    connection = InferredConnection(
                        source_component=source_comp.component_name,
                        target_component=target_comp.component_name,
                        connection_type=ConnectionType.FLOW,
                        flow_direction=flow_direction,
                        confidence=0.75,
                        inference_method="flow_inference",
                        supporting_evidence=[description['text']]
                    )
                    connections.append(connection)
        
        return connections
    
    def _infer_control_connections(self, components: List[ComponentContext], 
                                 text: str) -> List[InferredConnection]:
        """基于控制关系推断连接"""
        connections = []
        
        # 查找控制关系描述
        control_patterns = [
            r'([\u4e00-\u9fff\w]+)\s*(?:控制|调节|管理|操作)\s*([\u4e00-\u9fff\w]+)',
            r'([\u4e00-\u9fff\w]+)\s*(?:监测|检测|测量)\s*([\u4e00-\u9fff\w]+)\s*(?:的|状态|参数)',
            r'(?:通过|使用)\s*([\u4e00-\u9fff\w]+)\s*(?:控制|调节)\s*([\u4e00-\u9fff\w]+)'
        ]
        
        for pattern in control_patterns:
            for match in re.finditer(pattern, text):
                controller_name = match.group(1)
                controlled_name = match.group(2)
                
                controller_comp = self._find_component_by_name(controller_name, components)
                controlled_comp = self._find_component_by_name(controlled_name, components)
                
                if controller_comp and controlled_comp:
                    # 确定连接类型（控制或信号）
                    if "监测" in match.group(0) or "检测" in match.group(0) or "测量" in match.group(0):
                        connection_type = ConnectionType.SIGNAL
                        # 传感器到被监测对象的信号连接
                        source_comp = controlled_comp
                        target_comp = controller_comp
                    else:
                        connection_type = ConnectionType.CONTROL
                        # 控制器到被控对象的控制连接
                        source_comp = controller_comp
                        target_comp = controlled_comp
                    
                    connection = InferredConnection(
                        source_component=source_comp.component_name,
                        target_component=target_comp.component_name,
                        connection_type=connection_type,
                        flow_direction=FlowDirection.DOWNSTREAM,
                        confidence=0.8,
                        inference_method="control_inference",
                        supporting_evidence=[match.group(0)]
                    )
                    connections.append(connection)
        
        return connections
    
    def _topology_based_inference(self, components: List[ComponentContext], 
                                existing_connections: List[InferredConnection]) -> List[InferredConnection]:
        """基于拓扑的连接推断"""
        connections = []
        
        # 构建现有连接图
        graph = self._build_connection_graph(components, existing_connections)
        
        # 查找缺失的连接
        missing_connections = self._find_missing_connections(graph, components)
        connections.extend(missing_connections)
        
        # 推断串联连接
        series_connections = self._infer_series_connections(components, graph)
        connections.extend(series_connections)
        
        # 推断并联连接
        parallel_connections = self._infer_parallel_connections(components, graph)
        connections.extend(parallel_connections)
        
        return connections
    
    def _build_connection_graph(self, components: List[ComponentContext], 
                              connections: List[InferredConnection]) -> nx.DiGraph:
        """构建连接图"""
        graph = nx.DiGraph()
        
        # 添加节点
        for comp in components:
            graph.add_node(comp.component_name, 
                         component_type=comp.component_type,
                         position=comp.position)
        
        # 添加边
        for conn in connections:
            graph.add_edge(conn.source_component, conn.target_component,
                         connection_type=conn.connection_type,
                         flow_direction=conn.flow_direction,
                         confidence=conn.confidence)
        
        return graph
    
    def _find_missing_connections(self, graph: nx.DiGraph, 
                                components: List[ComponentContext]) -> List[InferredConnection]:
        """查找缺失的连接"""
        connections = []
        
        # 查找孤立节点
        isolated_nodes = list(nx.isolates(graph))
        
        for node in isolated_nodes:
            node_comp = next((comp for comp in components if comp.component_name == node), None)
            if not node_comp:
                continue
            
            # 为孤立节点寻找可能的连接
            potential_connections = self._find_potential_connections_for_isolated_node(
                node_comp, components, graph
            )
            connections.extend(potential_connections)
        
        # 查找弱连接的组件（只有很少连接的组件）
        for node in graph.nodes():
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            
            if in_degree + out_degree <= 1:  # 连接度很低
                node_comp = next((comp for comp in components if comp.component_name == node), None)
                if node_comp:
                    additional_connections = self._suggest_additional_connections(
                        node_comp, components, graph
                    )
                    connections.extend(additional_connections)
        
        return connections
    
    def _find_potential_connections_for_isolated_node(self, isolated_comp: ComponentContext,
                                                    all_components: List[ComponentContext],
                                                    graph: nx.DiGraph) -> List[InferredConnection]:
        """为孤立节点寻找潜在连接"""
        connections = []
        
        # 基于组件类型查找最可能的连接
        for rule in self.connection_rules:
            if rule.source_type == isolated_comp.component_type:
                # 查找目标类型的组件
                target_components = [comp for comp in all_components 
                                   if comp.component_type == rule.target_type and 
                                   comp.component_name != isolated_comp.component_name]
                
                for target_comp in target_components:
                    connection = InferredConnection(
                        source_component=isolated_comp.component_name,
                        target_component=target_comp.component_name,
                        connection_type=rule.connection_type,
                        flow_direction=rule.flow_direction,
                        confidence=rule.probability * 0.6,  # 降低置信度
                        inference_method="isolated_node_inference",
                        supporting_evidence=[f"孤立节点连接推断: {rule.source_type}->{rule.target_type}"]
                    )
                    connections.append(connection)
            
            elif rule.target_type == isolated_comp.component_type:
                # 查找源类型的组件
                source_components = [comp for comp in all_components 
                                   if comp.component_type == rule.source_type and 
                                   comp.component_name != isolated_comp.component_name]
                
                for source_comp in source_components:
                    connection = InferredConnection(
                        source_component=source_comp.component_name,
                        target_component=isolated_comp.component_name,
                        connection_type=rule.connection_type,
                        flow_direction=rule.flow_direction,
                        confidence=rule.probability * 0.6,
                        inference_method="isolated_node_inference",
                        supporting_evidence=[f"孤立节点连接推断: {rule.source_type}->{rule.target_type}"]
                    )
                    connections.append(connection)
        
        return connections
    
    def _suggest_additional_connections(self, comp: ComponentContext,
                                      all_components: List[ComponentContext],
                                      graph: nx.DiGraph) -> List[InferredConnection]:
        """为连接度低的组件建议额外连接"""
        connections = []
        
        # 基于工程常识添加连接
        if comp.component_type == "Sensor":
            # 传感器应该监测某些组件
            monitorable_types = ["Reservoir", "Gate", "Pump", "Valve", "Canal", "Pipe"]
            for target_comp in all_components:
                if target_comp.component_type in monitorable_types and \
                   not graph.has_edge(target_comp.component_name, comp.component_name):
                    
                    connection = InferredConnection(
                        source_component=target_comp.component_name,
                        target_component=comp.component_name,
                        connection_type=ConnectionType.SIGNAL,
                        flow_direction=FlowDirection.DOWNSTREAM,
                        confidence=0.5,
                        inference_method="additional_connection_suggestion",
                        supporting_evidence=["传感器通常监测其他组件"]
                    )
                    connections.append(connection)
        
        elif comp.component_type in ["Gate", "Valve"]:
            # 闸门和阀门通常控制流量
            if graph.in_degree(comp.component_name) == 0:  # 没有输入
                # 寻找可能的上游组件
                upstream_types = ["Reservoir", "Lake", "Pond", "Pump", "PumpStation"]
                for source_comp in all_components:
                    if source_comp.component_type in upstream_types:
                        connection = InferredConnection(
                            source_component=source_comp.component_name,
                            target_component=comp.component_name,
                            connection_type=ConnectionType.FLOW,
                            flow_direction=FlowDirection.DOWNSTREAM,
                            confidence=0.4,
                            inference_method="additional_connection_suggestion",
                            supporting_evidence=["闸门/阀门通常有上游水源"]
                        )
                        connections.append(connection)
        
        return connections
    
    def _infer_series_connections(self, components: List[ComponentContext], 
                                graph: nx.DiGraph) -> List[InferredConnection]:
        """推断串联连接"""
        connections = []
        
        # 查找串联模式
        for series_pattern in self.topology_rules["series_components"]:
            component_types = series_pattern.split("->")
            
            # 查找匹配的组件序列
            matching_sequences = self._find_matching_component_sequences(
                component_types, components
            )
            
            for sequence in matching_sequences:
                for i in range(len(sequence) - 1):
                    source_comp = sequence[i]
                    target_comp = sequence[i + 1]
                    
                    # 检查是否已存在连接
                    if not graph.has_edge(source_comp.component_name, target_comp.component_name):
                        connection = InferredConnection(
                            source_component=source_comp.component_name,
                            target_component=target_comp.component_name,
                            connection_type=ConnectionType.FLOW,
                            flow_direction=FlowDirection.DOWNSTREAM,
                            confidence=0.7,
                            inference_method="series_topology_inference",
                            supporting_evidence=[f"串联模式: {series_pattern}"]
                        )
                        connections.append(connection)
        
        return connections
    
    def _infer_parallel_connections(self, components: List[ComponentContext], 
                                  graph: nx.DiGraph) -> List[InferredConnection]:
        """推断并联连接"""
        connections = []
        
        # 查找相同类型的组件
        type_groups = defaultdict(list)
        for comp in components:
            type_groups[comp.component_type].append(comp)
        
        # 为相同类型的多个组件推断并联连接
        for comp_type, comp_list in type_groups.items():
            if len(comp_list) > 1 and comp_type in ["Pump", "Gate", "Valve"]:
                # 这些组件类型常常并联使用
                for i, comp1 in enumerate(comp_list):
                    for j, comp2 in enumerate(comp_list):
                        if i != j:
                            # 检查是否应该有并联连接
                            if self._should_have_parallel_connection(comp1, comp2, graph):
                                connection = InferredConnection(
                                    source_component=comp1.component_name,
                                    target_component=comp2.component_name,
                                    connection_type=ConnectionType.STRUCTURAL,
                                    flow_direction=FlowDirection.BIDIRECTIONAL,
                                    confidence=0.6,
                                    inference_method="parallel_topology_inference",
                                    supporting_evidence=[f"并联{comp_type}"]
                                )
                                connections.append(connection)
        
        return connections
    
    def _should_have_parallel_connection(self, comp1: ComponentContext, 
                                       comp2: ComponentContext, 
                                       graph: nx.DiGraph) -> bool:
        """判断两个组件是否应该有并联连接"""
        # 检查是否有共同的上游或下游组件
        comp1_predecessors = set(graph.predecessors(comp1.component_name))
        comp1_successors = set(graph.successors(comp1.component_name))
        comp2_predecessors = set(graph.predecessors(comp2.component_name))
        comp2_successors = set(graph.successors(comp2.component_name))
        
        # 如果有共同的上游和下游，可能是并联
        common_predecessors = comp1_predecessors & comp2_predecessors
        common_successors = comp1_successors & comp2_successors
        
        return len(common_predecessors) > 0 and len(common_successors) > 0
    
    def _validate_and_supplement_connections(self, connections: List[InferredConnection],
                                           components: List[ComponentContext]) -> List[InferredConnection]:
        """验证和补充连接"""
        validated_connections = []
        
        for connection in connections:
            # 验证连接的工程合理性
            if self._validate_engineering_feasibility(connection, components):
                validated_connections.append(connection)
            else:
                # 尝试修正连接
                corrected_connection = self._correct_connection(connection, components)
                if corrected_connection:
                    validated_connections.append(corrected_connection)
        
        # 补充必要的连接
        supplementary_connections = self._add_supplementary_connections(
            validated_connections, components
        )
        validated_connections.extend(supplementary_connections)
        
        return validated_connections
    
    def _validate_engineering_feasibility(self, connection: InferredConnection,
                                        components: List[ComponentContext]) -> bool:
        """验证工程可行性"""
        source_comp = next((comp for comp in components 
                          if comp.component_name == connection.source_component), None)
        target_comp = next((comp for comp in components 
                          if comp.component_name == connection.target_component), None)
        
        if not source_comp or not target_comp:
            return False
        
        # 检查连接类型的合理性
        if connection.connection_type == ConnectionType.FLOW:
            # 流量连接的约束检查
            if source_comp.component_type == "Sensor":
                return False  # 传感器不能作为流量源
            
            if target_comp.component_type == "Sensor":
                return False  # 传感器不能作为流量目标
        
        elif connection.connection_type == ConnectionType.SIGNAL:
            # 信号连接的约束检查
            if source_comp.component_type not in ["Sensor"] and \
               target_comp.component_type not in ["Sensor"]:
                return False  # 信号连接至少涉及一个传感器
        
        elif connection.connection_type == ConnectionType.CONTROL:
            # 控制连接的约束检查
            controllable_types = ["Gate", "Valve", "Pump", "PumpStation"]
            if target_comp.component_type not in controllable_types:
                return False  # 目标必须是可控制的组件
        
        return True
    
    def _correct_connection(self, connection: InferredConnection,
                          components: List[ComponentContext]) -> Optional[InferredConnection]:
        """修正连接"""
        # 尝试交换源和目标
        corrected_connection = InferredConnection(
            source_component=connection.target_component,
            target_component=connection.source_component,
            connection_type=connection.connection_type,
            flow_direction=FlowDirection.UPSTREAM if connection.flow_direction == FlowDirection.DOWNSTREAM 
                          else FlowDirection.DOWNSTREAM if connection.flow_direction == FlowDirection.UPSTREAM 
                          else connection.flow_direction,
            confidence=connection.confidence * 0.8,  # 降低置信度
            inference_method=f"{connection.inference_method}_corrected",
            supporting_evidence=connection.supporting_evidence + ["方向修正"]
        )
        
        if self._validate_engineering_feasibility(corrected_connection, components):
            return corrected_connection
        
        return None
    
    def _add_supplementary_connections(self, existing_connections: List[InferredConnection],
                                     components: List[ComponentContext]) -> List[InferredConnection]:
        """添加补充连接"""
        supplementary = []
        
        # 为每个传感器添加监测连接（如果缺失）
        sensors = [comp for comp in components if comp.component_type == "Sensor"]
        
        for sensor in sensors:
            # 检查传感器是否有监测目标
            has_monitoring_target = any(
                conn.source_component != sensor.component_name and 
                conn.target_component == sensor.component_name and 
                conn.connection_type == ConnectionType.SIGNAL
                for conn in existing_connections
            )
            
            if not has_monitoring_target:
                # 为传感器分配监测目标
                monitorable_components = [
                    comp for comp in components 
                    if comp.component_type in ["Reservoir", "Gate", "Pump", "Valve", "Canal", "Pipe"]
                ]
                
                if monitorable_components:
                    # 选择最近的组件作为监测目标
                    closest_comp = min(monitorable_components, 
                                     key=lambda c: abs(c.position[0] - sensor.position[0]))
                    
                    connection = InferredConnection(
                        source_component=closest_comp.component_name,
                        target_component=sensor.component_name,
                        connection_type=ConnectionType.SIGNAL,
                        flow_direction=FlowDirection.DOWNSTREAM,
                        confidence=0.6,
                        inference_method="supplementary_sensor_connection",
                        supporting_evidence=["传感器需要监测目标"]
                    )
                    supplementary.append(connection)
        
        return supplementary
    
    def _deduplicate_and_rank_connections(self, connections: List[InferredConnection]) -> List[InferredConnection]:
        """去重和排序连接"""
        # 去重
        unique_connections = {}
        
        for conn in connections:
            key = (conn.source_component, conn.target_component, conn.connection_type.value)
            
            if key not in unique_connections or \
               unique_connections[key].confidence < conn.confidence:
                unique_connections[key] = conn
        
        # 排序
        sorted_connections = sorted(unique_connections.values(), 
                                  key=lambda c: c.confidence, reverse=True)
        
        return sorted_connections
    
    # 辅助方法
    def _find_applicable_rules(self, source_type: str, target_type: str) -> List[ConnectionRule]:
        """查找适用的连接规则"""
        return [rule for rule in self.connection_rules 
                if rule.source_type == source_type and rule.target_type == target_type]
    
    def _check_connection_conditions(self, rule: ConnectionRule, 
                                   source_comp: ComponentContext, 
                                   target_comp: ComponentContext) -> bool:
        """检查连接条件"""
        if not rule.conditions:
            return True
        
        # 检查组件的上下文关键词
        source_keywords = source_comp.nearby_keywords or []
        target_keywords = target_comp.nearby_keywords or []
        all_keywords = source_keywords + target_keywords
        
        return any(condition in ' '.join(all_keywords) for condition in rule.conditions)
    
    def _find_component_by_name(self, name: str, components: List[ComponentContext]) -> Optional[ComponentContext]:
        """根据名称查找组件"""
        # 精确匹配
        for comp in components:
            if comp.component_name == name:
                return comp
        
        # 模糊匹配
        for comp in components:
            if name in comp.component_name or comp.component_name in name:
                return comp
        
        return None
    
    def _determine_connection_type_from_text(self, text: str) -> ConnectionType:
        """从文本确定连接类型"""
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in self.flow_patterns["control_indicators"]):
            return ConnectionType.CONTROL
        elif any(indicator in text_lower for indicator in self.flow_patterns["signal_indicators"]):
            return ConnectionType.SIGNAL
        else:
            return ConnectionType.FLOW
    
    def _determine_flow_direction_from_text(self, text: str) -> FlowDirection:
        """从文本确定流向"""
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in self.flow_patterns["upstream_indicators"]):
            return FlowDirection.UPSTREAM
        elif any(indicator in text_lower for indicator in self.flow_patterns["bidirectional_indicators"]):
            return FlowDirection.BIDIRECTIONAL
        else:
            return FlowDirection.DOWNSTREAM
    
    def _extract_flow_descriptions(self, text: str) -> List[Dict[str, any]]:
        """提取流向描述"""
        descriptions = []
        
        # 查找包含流向指示词的句子
        sentences = re.split(r'[。！？；]', text)
        
        for sentence in sentences:
            direction = None
            
            if any(indicator in sentence for indicator in self.flow_patterns["downstream_indicators"]):
                direction = FlowDirection.DOWNSTREAM
            elif any(indicator in sentence for indicator in self.flow_patterns["upstream_indicators"]):
                direction = FlowDirection.UPSTREAM
            elif any(indicator in sentence for indicator in self.flow_patterns["bidirectional_indicators"]):
                direction = FlowDirection.BIDIRECTIONAL
            
            if direction:
                descriptions.append({
                    'text': sentence.strip(),
                    'direction': direction
                })
        
        return descriptions
    
    def _find_matching_component_sequences(self, component_types: List[str], 
                                         components: List[ComponentContext]) -> List[List[ComponentContext]]:
        """查找匹配的组件序列"""
        sequences = []
        
        # 按类型分组组件
        type_groups = defaultdict(list)
        for comp in components:
            type_groups[comp.component_type].append(comp)
        
        # 递归查找序列
        def find_sequences(current_sequence, remaining_types):
            if not remaining_types:
                sequences.append(current_sequence[:])
                return
            
            next_type = remaining_types[0]
            if next_type in type_groups:
                for comp in type_groups[next_type]:
                    if comp not in current_sequence:
                        current_sequence.append(comp)
                        find_sequences(current_sequence, remaining_types[1:])
                        current_sequence.pop()
        
        find_sequences([], component_types)
        return sequences