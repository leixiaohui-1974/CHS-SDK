# 这个文件保留为向后兼容，请使用新的结构化智能体
from core_lib.central_agents.control.mpc_agent import MPCAgent as CentralMPCAgent

import warnings
warnings.warn(
    "core_lib.central_agents.central_mpc_agent.CentralMPCAgent is deprecated. "
    "Please use core_lib.central_agents.control.mpc_agent.MPCAgent instead.",
    DeprecationWarning,
    stacklevel=2
)

# 保持向后兼容
__all__ = ['CentralMPCAgent']