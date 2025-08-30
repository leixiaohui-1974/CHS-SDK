# 物理模型: 圣维南方程河道 (StVenantReach)

*   **源代码**: `core_lib/physical_objects/st_venant_reach.py`
*   **接口**: (特殊) 不直接实现`PhysicalObjectInterface`的`step`，而是为`NetworkSolver`提供方程。

## 1. 概述

`StVenantReach` 是 `core_lib` 中用于**高精度水动力仿真**的核心物理模型。它专门用于模拟开放式渠道（河流、大型运河）中的**非恒定流 (Unsteady Flow)**。

与简化的 `RiverChannel` 模型不同，`StVenantReach` 能够精确地模拟复杂的水力现象，如洪水波的传播、回水效应、潮汐影响等。

## 2. 数学模型：一维圣维南方程组

该模型基于完整的一维**圣维南方程组 (Saint-Venant Equations)**，这是描述开放渠道非恒定流的偏微分方程组：
1.  **连续性方程 (Continuity Equation)**: 描述了质量守恒。
    `∂Q/∂x + ∂A/∂t = 0`
2.  **动量方程 (Momentum Equation)**: 描述了动量守恒，考虑了重力、压力、惯性和摩擦力的影响。
    `∂Q/∂t + ∂(vQ)/∂x + gA(∂h/∂x - S_0 + S_f) = 0`

其中:
*   `Q`: 流量
*   `A`: 过水断面面积
*   `h`: 水深
*   `x`: 沿河道距离
*   `t`: 时间
*   `S_0`: 河床坡度
*   `S_f`: 摩擦坡度 (通常用曼宁公式计算)

## 3. 实现方法：Preissmann隐式差分格式

直接求解圣维南方程组没有解析解，必须使用数值方法。`core_lib` 采用了在计算水力学领域非常成熟和稳定的**普雷斯曼四点隐式差分格式 (Preissmann 4-point implicit scheme)**。

其核心思想是：
1.  **离散化**: 将一段河道在空间上离散为 `n` 个计算点，在时间上按 `dt` 离散。
2.  **线性化**: 将非线性的偏微分方程在每个计算点和每个时间步上进行线性化，得到一组关于水位增量(`dH`)和流量增量(`dQ`)的线性代数方程。
3.  **提供方程**: `StVenantReach` 对象的核心职责**不是自己求解这些方程**。相反，它的 `get_equations()` 方法负责为自己所代表的河段，生成这些线性化的方程系数矩阵 (`A_i`, `B_i`) 和右侧项向量 (`C_i`)。

## 4. 在系统中的角色

`StVenantReach` 对象是 `NetworkSolver` 的一个关键“客户”。

1.  在 `NetworkSolver` 的 `build_system()` 阶段，求解器会调用其管辖的所有 `StVenantReach` 实例的 `get_equations()` 方法。
2.  求解器收集所有这些方程系数，并将它们组装成一个代表整个河网系统的、巨大的稀疏线性方程组。
3.  求解器通过 `spsolve` 一次性求解这个巨大的方程组，得到整个河网在当前时间步所有计算点上的水位和流量增量 (`dH`, `dQ`)。
4.  最后，求解器调用每个 `StVenantReach` 实例的 `update_state(dH, dQ)` 方法，将只属于该河段的解分配回去，以更新其内部状态。

通过这种方式，系统实现了对复杂河网系统的**全隐式、紧耦合**求解，保证了计算结果的物理真实性和数值稳定性。
