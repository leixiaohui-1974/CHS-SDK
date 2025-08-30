# 渠道模型 (Canal Model)

> [!NOTE]
> 从 v2.0 开始, 旧的 `Canal` 模型已被弃用。请使用 `UnifiedCanal` 模型并设置 `model_type='integral'`。

`UnifiedCanal` 模型可以用来代表一段渠道。当 `model_type` 设置为 `'integral'` 时，它使用简单的水量平衡方法来模拟水流。

## 状态变量

-   `water_level` (float): 渠道当前的水位 (m)。
-   `inflow` (float): 当前时间步的入流量 (m³/s)。
-   `outflow` (float): 当前时间步内计算出的渠道出流量 (m³/s)。

## 参数

当 `model_type='integral'` 时，主要参数为:
-   `surface_area` (float): 渠道的水面面积 (m²)。
-   `outlet_coefficient` (float): 出流系数，用于根据水位计算出流。

## 使用示例

```python
from core_lib.physical_objects.unified_canal import UnifiedCanal

# 使用统一渠道模型，并指定模型类型为'integral'
unified_canal = UnifiedCanal(
    name="my_unified_canal",
    initial_state={'water_level': 5.0, 'inflow': 50.0, 'outflow': 50.0},
    parameters={
        'model_type': 'integral',
        'surface_area': 10000,
        'outlet_coefficient': 5.0
    }
)
```
