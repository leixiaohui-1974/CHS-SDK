# 1. 仿真与物理对象

本篇文档详细介绍 `core_lib` 中物理世界仿真的核心概念和实现。

## 1. `PhysicalObjectInterface`：万物皆模型

在 `core_lib` 的设计中，所有代表物理世界实体的模型，无论是简单的管道(`Pipe`)，还是复杂的河道(`RiverChannel`)，都必须实现一个共同的接口：`PhysicalObjectInterface`。

这个接口定义在 `core_lib/core/interfaces.py` 中，其核心是 `step()` 方法。

```python
# core_lib/core/interfaces.py (示意)
class PhysicalObjectInterface:
    def step(self, action: Any, dt: float) -> State:
        """
        根据外部动作，将模型的状态向前推进一个时间步长(dt)。
        """
        raise NotImplementedError
```

这种设计的精妙之处在于，它允许仿真引擎以一种统一的方式与任何物理对象进行交互，而无需关心其内部模型的复杂程度。

## 2. 双模仿真引擎

`core_lib` 实际上提供了两种不同复杂度的仿真模式，以适应不同的应用场景。

### 模式一：基于智能体的离散事件仿真

在这种模式下，每一个物理对象（如一个`Pipe`实例）都被一个智能体（如`DigitalTwinAgent`）封装。仿真引擎 (`SimulationHarness`) 在每个时间步，依次调用每个智能体的`run()`方法，智能体再调用其内部物理对象的`step()`方法来更新状态。

*   **适用对象**: `pipe.py`, `pump.py`, `valve.py`, 以及简化的`river_channel.py`等。
*   **特点**:
    *   模型之间是**解耦**的，一个对象的状态更新不直接依赖于另一个对象在同一时间步的状态。
    *   计算速度快，适合大规模、网络结构简单的系统，或作为高层级控制逻辑的快速“沙盘”。
    *   物理精确性相对较低，例如，它无法精确模拟回水、潮汐等复杂的水力现象。

### 模式二：基于隐式求解器的耦合水动力仿真

为了进行高精度的水力计算，`core_lib` 提供了 `core_lib/core_engine/solver/network_solver.py`。这是一个基于有限差分法的复杂水动力求解器。

*   **适用对象**: `st_venant_reach.py` (使用圣维南方程组的河道模型), `hydro_nodes` (水力节点)等。
*   **特点**:
    *   模型之间是**紧耦合**的。求解器会将所有相关的河道和节点的方程联立起来，形成一个巨大的稀疏矩阵。
    *   在每个时间步，通过求解这个矩阵方程组，**同时得出**网络中所有点的水位(H)和流量(Q)。
    *   物理精确性高，能够准确模拟回水、潮汐、溃坝波等复杂的水力学现象。
    *   计算量大，对计算资源要求高。

## 3. 物理对象库

所有物理对象的具体实现都位于 `core_lib/physical_objects/` 目录中。开发者可以根据需求，选择合适的模型或自行开发新的模型（只需实现`PhysicalObjectInterface`接口即可）。

**核心对象分类**:
*   **承压流体**: `pipe.py`, `pump.py`, `valve.py`
*   **开放渠系**: `river_channel.py`, `canal.py`, `st_venant_reach.py`
*   **控制结构**: `gate.py`
*   **存储单元**: `reservoir.py`, `lake.py`
*   **水文单元**: `rainfall_runoff.py`
*   **能源单元**: `water_turbine.py`, `hydropower_station.py`

通过组合这些物理对象，可以灵活地构建出从单一水泵到整个流域的复杂水系统模型。
