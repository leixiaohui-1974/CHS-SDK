"""
Junction component - migrated from hydro_nodes
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any, List, Tuple
import numpy as np

class Junction(PhysicalObjectInterface):
    """
    代表多个水道汇聚或分流的交汇点
    
    该节点强制执行两个物理定律：
    1. 连续性：进入交汇点的所有流量之和等于离开的流量之和
    2. 共同水头：交汇点所有连接点的水位（水头）相同
    
    既支持仿真模式也支持数值求解器模式
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        
        # 仿真模式状态
        self._state.setdefault('total_inflow', 0.0)
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('water_level', initial_state.get('water_level', 0.0))
        
        # 数值求解器模式属性
        self.in_connections: List[Tuple[object, int]] = []
        self.out_connections: List[Tuple[object, int]] = []
        
        print(f"Junction '{self.name}' 已创建")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        仿真模式：时间步进
        
        在仿真模式下，交汇点主要作为流量汇聚和分配的节点
        """
        # 处理来自上游的入流
        total_inflow = 0.0
        for component_name, inflow in action.get('inflows', {}).items():
            if isinstance(inflow, (int, float)):
                total_inflow += inflow
        
        self._state['total_inflow'] = total_inflow
        
        # 根据分配规则计算出流
        distribution_ratios = self._params.get('distribution_ratios', [1.0])
        total_outflow = 0.0
        
        for i, ratio in enumerate(distribution_ratios):
            outflow = total_inflow * ratio
            self._state[f'outflow_{i}'] = outflow
            total_outflow += outflow
        
        self._state['total_outflow'] = total_outflow
        
        # 更新水位（简化模型）
        net_flow = total_inflow - total_outflow
        area = self._params.get('junction_area', 1.0)
        water_level_change = net_flow * time_step / area
        self._state['water_level'] += water_level_change
        
        return self._state

    @property
    def is_stateful(self) -> bool:
        return True  # 交汇点具有水位状态

    # 数值求解器支持 - 从JunctionNode整合
    def add_in_connection(self, obj, idx: int = -1):
        """添加流入交汇点的连接"""
        self.in_connections.append((obj, idx))

    def add_out_connection(self, obj, idx: int = 0):
        """添加流出交汇点的连接"""
        self.out_connections.append((obj, idx))

    def get_equations(self, time_step: float, theta: float) -> list:
        """
        返回交汇点的线性化方程（数值求解器使用）
        
        整合自JunctionNode的实现，支持NetworkSolver
        """
        all_connections = self.in_connections + self.out_connections
        if len(all_connections) < 2:
            # 交汇点需要至少两个连接才有意义
            return []

        equations = []

        # 方程1: 连续性方程
        # 入流之和 - 出流之和 = 0
        eq_continuity = {}
        rhs_continuity = 0.0

        for obj, idx in self.in_connections:
            eq_continuity[(obj, 'Q', idx)] = 1.0
            rhs_continuity -= obj.Q[idx]

        for obj, idx in self.out_connections:
            eq_continuity[(obj, 'Q', idx)] = -1.0
            rhs_continuity += obj.Q[idx]

        eq_continuity['RHS'] = rhs_continuity
        equations.append(eq_continuity)

        # 水头方程 (N-1个方程)
        # H_1 = H_2, H_2 = H_3, ...
        # 创建N-1个方程确保所有水头相等
        first_conn_obj, first_conn_idx = all_connections[0]

        for i in range(1, len(all_connections)):
            next_conn_obj, next_conn_idx = all_connections[i]

            h_first = first_conn_obj.H[first_conn_idx]
            h_next = next_conn_obj.H[next_conn_idx]

            eq_head = {
                (first_conn_obj, 'H', first_conn_idx): 1.0,
                (next_conn_obj, 'H', next_conn_idx): -1.0,
                'RHS': -(h_first - h_next)
            }
            equations.append(eq_head)

        return equations
