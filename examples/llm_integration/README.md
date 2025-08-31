示例：集成大语言模型（LLM）的智能体
本示例旨在演示如何将在 core_lib.llm_integration_agents 中定义的、由大语言模型（LLM）驱动的新型智能体集成到仿真工作流中。

该示例不执行完整的水力学仿真，而是通过模拟和打印信息来清晰地展示每个LLM智能体如何在其指定的角色中工作。

包含文件
run_llm_demonstration.py: 主执行脚本。

演示流程
脚本 run_llm_demonstration.py 将按顺序执行以下步骤：

角色一：系统构建师 (LLMSystemBuilderAgent)

向LLMSystemBuilderAgent提供一句关于水网系统的自然语言描述。

智能体（模拟地）调用LLM，将描述转化为结构化的YAML配置文件字符串。

打印生成的 components, topology, 和 agents 配置。

角色二：情景设计师 (LLMScenarioDesignerAgent)

向LLMScenarioDesignerAgent提供一句关于复杂仿真情景的自然语言描述。

智能体（模拟地）调用LLM，将描述转化为 ScenarioAgent 可以使用的YAML事件脚本。

打印生成的场景配置。

角色三：智能调度指挥官 (LLMDispatchCommanderAgent)

初始化一个模拟的消息总线和一个LLMDispatchCommanderAgent。

模拟一个外部输入，向指挥官的命令主题发布一句高级别的自然语言调度指令。

LLMDispatchCommanderAgent 接收到指令，（模拟地）调用LLM进行意图理解，并向CentralDispatcherAgent的控制主题发布一个结构化的调度策略。

脚本将监听并打印出这个结构化的指令，展示从自然语言到机器指令的转换。

角色四：数据分析师与诊断专家 (LLMDataAnalystAgent)

创建一个模拟的CSV日志文件。

初始化一个LLMDataAnalystAgent。

向分析师智能体提供日志文件路径和一个自然语言的分析查询。

智能体读取数据，（模拟地）调用LLM进行分析，并返回一份自然语言的分析报告。

打印最终的分析报告。

如何运行
直接在代码库根目录运行此脚本：

python examples/llm_integration/run_llm_demonstration.py
