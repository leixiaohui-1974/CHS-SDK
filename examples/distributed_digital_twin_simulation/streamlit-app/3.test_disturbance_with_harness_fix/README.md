# 扰动功能修复演示（Streamlit）

该应用为 `3.test_disturbance_with_harness_fix.py` 提供可视化界面：
- 运行原脚本 `main()` 并捕获日志/控制台输出
- 自定义参数运行仿真（基于脚本 `load_simulation_harness` 与 `patch_harness_for_disturbance`）
- 查看结果曲线/指标与下载 JSON
- 文档页签展示模块与函数 docstring

## 快速开始
```bash
pip install -r input/1.test_actuator_failure_disturbance.py/requirements.txt
pip install -r 3.test_disturbance_with_harness_fix_app/requirements.txt
streamlit run 3.test_disturbance_with_harness_fix_app/app.py
```

## 常见问题
- 如果流程图不显示，请安装 `graphviz`（同时可能需要系统级 Graphviz）。
- 若组件 ID 不正确，应用会提示可用组件列表。


