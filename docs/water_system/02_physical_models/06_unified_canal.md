# 物理模型: 统一渠池 (UnifiedCanal)

> [!WARNING]
> **模型已更新**: 从 v2.0 开始，旧的渠池模型 (`UnifiedCanal(model_type='integral')`, `StVenantReach`) 已被弃用，并统一由 `UnifiedCanal` 模型代替。请更新您的代码以使用新模型。

本篇文档介绍用于模拟明渠或渠池水力学行为的统一物理模型 `UnifiedCanal`。

*   **源代码**: `core_lib/physical_objects/unified_canal.py`

## 概述

`UnifiedCanal` 是一个灵活的、统一的渠池模型。它通过一个 `model_type` 参数，可以在多种不同复杂度的模型之间切换，以适应从精细化水力学仿真到高层次控制策略设计的不同需求。

这种设计大大提高了代码的可维护性和扩展性，允许用户在同一框架下轻松比较和切换不同的数学模型。

### `model_type` 选项

-   `'integral'`: 简单的积分（水库）模型。
-   `'integral_delay'`: 积分加时滞模型。
-   `'integral_delay_zero'`: 积分、时滞加零点模型。
-   `'linear_reservoir'`: 线性水库模型。
-   `'st_venant'`: 基于一维圣维南方程的完整水动力学模型。

---

## 1. 简化模型 (Lumped Models)

这些模型将一段渠池视为一个单一的蓄水池，适用于宏观模拟和控制系统设计。它们都通过 `step()` 方法进行仿真。

### 1.1 积分模型 (`model_type='integral'`)
*   **核心思想**: 渠池的水量变化等于净流入量。
*   **参数**: `surface_area`, `outlet_coefficient`

### 1.2 积分-时滞模型 (`model_type='integral_delay'`)
*   **核心思想**: 上游的流量变化需要经过一段时间的传播才能影响到下游。
*   **参数**: `gain`, `delay`

### 1.3 积分-时滞-零点模型 (`model_type='integral_delay_zero'`)
*   **核心思想**: 增加一个与入流变化率相关的项，可以更准确地模拟波的传播效应。
*   **参数**: `gain`, `delay`, `zero_time_constant`

### 1.4 线性水库模型 (`model_type='linear_reservoir'`)
*   **核心思想**: 渠段的蓄水量与出流量成线性关系 (`S = k * q_out`)。
*   **参数**: `storage_constant`, `level_storage_ratio`

---

## 2. 水动力学模型 (`model_type='st_venant'`)

这是 `UnifiedCanal` 中最复杂的模型，用于高精度的水力学仿真。

*   **核心思想**: 该模型将渠段离散为多个计算点，并基于**一维圣维南方程组**（包含连续性方程和动量方程）来描述每个点的水位 (H) 和流量 (Q) 的动态变化。
*   **适用场景**:
    -   需要精确模拟洪水波传播、回水效应、潮汐影响等复杂水力现象的场景。
    -   作为高精度数字孪生的核心物理引擎。
*   **工作机制**:
    -   与简化模型不同，`st_venant` 模型**不能**通过 `step()` 方法独立仿真。
    -   它必须与 `NetworkSolver` 一起使用。在每个时间步，它通过 `get_equations()` 方法提供描述其水力行为的线性化方程组。
    -   `NetworkSolver` 收集网络中所有元件（包括其他 `st_venant` 渠段和 `HydroNode` 水工建筑节点）的方程，构建一个大型稀疏矩阵，并统一求解。
    -   求解后，`NetworkSolver` 会调用 `update_state()` 方法，将计算出的状态增量（dH, dQ）返回给渠段，以更新其内部状态。
*   **参数**:
    -   `length` (float): 渠段长度 (m)。
    -   `num_points` (int): 离散化计算点的数量。
    -   `bottom_width` (float): 渠底宽度 (m)。
    -   `side_slope_z` (float): 边坡系数。
    -   `manning_n` (float): 曼宁糙率系数。
    -   `slope` (float): 渠底纵坡。
    -   `initial_H` (list/np.array): 每个计算点的初始水位数组。
    -   `initial_Q` (list/np.array): 每个计算点的初始流量数组。
