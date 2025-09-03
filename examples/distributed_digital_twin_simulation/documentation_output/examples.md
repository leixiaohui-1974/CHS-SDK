# 示例代码

## 基础仿真示例

```python
from enhanced_simulation_harness import EnhancedSimulationHarness

# 创建仿真实例
config = {
    "simulation": {
        "start_time": 0,
        "end_time": 100,
        "dt": 1
    }
}

harness = EnhancedSimulationHarness(config)
results = harness.run_simulation()
print(f"仿真完成，结果: {results}")
```

## 扰动测试示例

```python
from run_disturbance_simulation import DisturbanceSimulationRunner

# 运行扰动仿真
runner = DisturbanceSimulationRunner()
results = runner.run_all_scenarios()
print(f"扰动测试完成: {results}")
```
