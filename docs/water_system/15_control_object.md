# 8. 控制 (Control) - 对象文档

## 概述

`Control` 对象是水系统自动控制模块的核心。它是连接数字世界与物理世界的桥梁，负责将上层应用（如优化调度 `Scheduling`）计算出的控制指令，准确无误地执行到物理世界的设备（PLC、RTU等）上。它不仅负责“下发”指令，还要负责监控指令的执行状态，并处理可能出现的执行偏差或失败。

## `Control` 对象

### 属性

`Control` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 控制服务的唯一标识符。
    *   **示例:** `"ctrl_service_main_pumps"`

*   **`name` (String):**
    *   **描述:** 控制服务的名称。
    *   **示例:** `"主泵群自动控制服务"`

*   **`target_devices` (Array<ControlDevice>):**
    *   **描述:** 定义了该控制服务能够直接通信和控制的物理设备或接口。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "device_id": "plc_pump_station_A",
            "protocol": "modbus_tcp",
            "address": "192.168.1.200:502",
            "mapping": {
              // 将系统中的逻辑设备映射到具体的物理设备地址
              "pump_A1_status": { "unit_id": 1, "register_type": "coil", "address": 0 },
              "pump_A1_feedback": { "unit_id": 1, "register_type": "discrete_input", "address": 0 },
              "pump_A2_status": { "unit_id": 1, "register_type": "coil", "address": 1 },
              "pump_A2_feedback": { "unit_id": 1, "register_type": "discrete_input", "address": 1 }
            }
          }
        ]
        ```

*   **`active_schedule` (ControlSchedule):**
    *   **描述:** 当前正在执行的控制调度计划。这个计划通常由 `Scheduling` 模块生成并加载进来。
    *   **只读:** 该属性由 `load_schedule` 方法更新。

*   **`execution_mode` (String):**
    *   **描述:** 控制服务的执行模式。
        *   `automatic`: 自动根据 `active_schedule` 在每个时间点下发控制指令。
        *   `manual`: 服务暂停自动执行，只接受 `manual_override` 指令。
        *   `advisory`: 服务只生成建议，不下发指令，需要人工确认。
    *   **默认值:** `manual`

*   **`control_loop_status` (Object):**
    *   **描述:** 一个只读对象，反映了当前控制回路的状态。
    *   **数据结构 (示例):**
        ```json
        {
          "last_command_time": "2023-09-01T16:00:01Z",
          "last_command": { "element_id": "pump_A1", "action": "start" },
          "last_command_status": "success", // success, failed, pending
          "next_command_time": "2023-09-01T17:00:00Z",
          "next_command": { "element_id": "pump_A2", "action": "stop" },
          "communication_status": {
            "plc_pump_station_A": "online" // online, offline
          }
        }
        ```

*   **`execution_log` (Array<LogEntry>):**
    *   **描述:** 详细记录了所有控制指令的下发、反馈和结果。这是进行审计和故障排查的重要依据。

### 设计理念

`Control` 对象的设计重点是“可靠性”和“安全性”。

1.  **抽象与解耦:** `Control` 对象为上层应用提供了一个统一的、抽象的控制接口（如 `start_pump('pump_A1')`），而将与具体硬件协议（如Modbus, OPC-UA）相关的复杂性封装在 `target_devices` 的定义中。这使得上层业务逻辑可以独立于底层的硬件实现，更换硬件设备时，只需修改配置，无需改动业务代码。

2.  **闭环控制思想:** `Control` 不仅仅是“发号施令”，它还包含了“确认反馈”的环节。在 `target_devices` 的 `mapping` 中，同时定义了控制点（`pump_A1_status`）和反馈点（`pump_A1_feedback`）。下发指令后，系统会检查反馈点的状态，以确认指令是否被成功执行，从而形成一个闭环。

3.  **模式管理:** `execution_mode` 的设计提供了必要的安全保障。在系统调试或紧急情况下，可以随时切换到 `manual` 或 `advisory` 模式，将控制权交还给操作员，防止错误的自动控制指令造成损失。

4.  **详细日志:** 任何对物理世界的控制操作都必须有据可查。`execution_log` 确保了所有操作的可追溯性。

`Control` 对象是整个智能决策系统“落地”的最后一公里，它的稳定性和可靠性直接关系到整个系统的成败和物理设施的安全。
