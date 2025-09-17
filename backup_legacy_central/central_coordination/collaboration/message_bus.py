# 这个文件保留为向后兼容，请使用 core_lib.central_coordination.communication.message_bus
from core_lib.central_coordination.communication.message_bus import *

import warnings
warnings.warn(
    "core_lib.central_coordination.collaboration.message_bus is deprecated. "
    "Please use core_lib.central_coordination.communication.message_bus instead.",
    DeprecationWarning,
    stacklevel=2
)