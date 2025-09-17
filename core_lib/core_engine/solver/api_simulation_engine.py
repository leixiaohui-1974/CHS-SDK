#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台API仿真引擎
提供面向API的仿真执行功能，将API请求转换为内部仿真执行
"""

import logging
from typing import Any, Dict
from core_lib.models.api_models import SimulationRequest, SimulationResult
from core_lib.core_engine.lifecycle.basic_simulation_engine import BasicSimulationEngine

# 配置日志
logger = logging.getLogger(__name__)

class ApiSimulationEngine:
    """API仿真引擎 - 将API请求转换为内部仿真执行"""
    
    def __init__(self):
        """初始化API仿真引擎"""
        logger.info("API仿真引擎初始化完成")
    
    def solve(self, simulation_request: SimulationRequest) -> SimulationResult:
        """
        执行仿真求解
        
        Args:
            simulation_request: 仿真请求
            
        Returns:
            SimulationResult: 仿真结果
        """
        try:
            logger.info(f"开始执行仿真: {simulation_request}")

            # 从请求中提取时间参数，提供合理默认值
            req_dict: Dict[str, Any] = simulation_request.dict() if hasattr(simulation_request, 'dict') else {}
            sim_cfg: Dict[str, Any] = req_dict.get('simulation', req_dict)
            start_time = float(sim_cfg.get('start_time', 0.0))
            end_time = float(sim_cfg.get('end_time', start_time + 10.0))
            time_step = float(sim_cfg.get('time_step', sim_cfg.get('dt', 1.0)))

            # 通过基础仿真引擎执行
            engine = BasicSimulationEngine()
            engine.configure({
                'start_time': start_time,
                'end_time': end_time,
                'time_step': time_step,
            })
            engine.initialize()
            sim_result = engine.run()
            engine.finalize()

            # 将结果转换为 API 层的 SimulationResult
            outputs: Dict[str, Any] = {
                'history': sim_result.history,
                'start_time': sim_result.start_time,
                'end_time': sim_result.end_time,
                'time_step': sim_result.time_step,
            }

            result = SimulationResult(
                simulation_id="sim_" + str(hash(str(req_dict))),
                user_id=req_dict.get('user_id'),
                outputs=outputs,
                parameters=req_dict,
                metadata={
                    'engine_version': 'basic-1.0',
                },
                execution_time=None,
                created_at=None,
            )

            logger.info("仿真执行完成")
            return result

        except Exception as e:
            logger.error(f"仿真执行失败: {str(e)}")
            raise

class SimulationSolver(ApiSimulationEngine):
    """仿真求解器（别名）"""
    pass

# 向后兼容性别名
SimulationEngine = ApiSimulationEngine
