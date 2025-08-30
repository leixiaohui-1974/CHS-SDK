# 大模型驱动的CHS-SDK仿真建模指南 (LLM Modeling Guide)
版本: 1.0

致大型语言模型（LLM）开发者：

本文档是您在使用 CHS-SDK 代码库构建水系统仿真与控制工程案例时必须遵守的核心操作规程。请严格遵循本文档中定义的原则和步骤。

1. 核心编程范式与最高指令
CHS-SDK 的核心设计哲学是数据驱动+智能体编程 (Data-Driven + Agent-Based)。这意味着，所有仿真场景的构建工作都应通过编写和组织配置文件来完成，而不是通过编写新的 Python 逻辑代码。

最高指令 (Prime Directive):

禁止硬编码，禁止自定义脚本。 您唯一的任务是根据用户需求，生成一个包含完整配置文件的场景文件夹 (Scenario Folder)。所有仿真都必须且只能通过根目录的 run_scenario.py 脚本来启动。严禁为每个案例创建新的、独立的 Python 执行脚本（如 run_my_simulation.py）。

2. 标准执行入口：run_scenario.py
本代码库唯一的、标准的仿真执行入口是位于根目录的 run_scenario.py 脚本。

标准用法:
该脚本通过命令行参数接收一个指向场景文件夹的路径。

python run_scenario.py --scenario_path <path_to_your_scenario_folder>

例如，如果您的场景文件夹名为 mission/scenarios/yinchuojiliao，则执行命令为：

python run_scenario.py --scenario_path mission/scenarios/yinchuojiliao

您的核心任务就是创建这样一个 <path_to_your_scenario_folder> 文件夹及其内部的所有必需文件。

3. 场景文件夹 (Scenario Folder) 的标准结构
一个标准的、可执行的场景文件夹必须包含以下配置文件：

components.yml: 必需。定义系统中所有物理实体及其静态参数。

topology.yml: 必需。定义物理实体之间的水流拓扑连接关系。

agents.yml: 必需。定义所有智能体，包括它们的类型、参数以及它们之间的通信方式（消息订阅/发布）。

config.yml: 必需。定义全局仿真设置，如仿真时长、时间步长，并指定前三个配置文件的路径。

event_scenario.yml: 可选。定义一系列按时间顺序触发的预定事件，用于模拟复杂工况。

data/ (文件夹): 可选。存放所有外部数据文件，如 inflow.csv, rainfall.csv 等。

4. LLM 建模工作流 (Step-by-Step Workflow)
请严格按照以下步骤，将用户的自然语言需求转化为一个完整的仿真场景文件夹。

第1步：解析需求 & 创建场景目录
解析: 从用户需求中识别出：

物理组件: 水库、闸门、水泵、管道、河道等。

物理参数: 水库库容曲线、管道长度、闸门宽度等。

连接关系: 哪个组件在哪个组件的上游或下游。

控制目标: "保持A水库水位在100米"、"控制B闸门流量为50m³/s"。

外部输入: 历史入流数据、降雨过程数据等。

创建目录: 在 examples/ 或 mission/scenarios/ 目录下创建一个新的、具有描述性名称的文件夹，用于存放该场景的所有文件。

第2步：生成 components.yml (物理世界)
映射组件: 将用户描述的物理组件映射到 core_lib.physical_objects 或 core_lib.hydro_nodes 中的基础类。

"水库" -> Reservoir

"闸门" -> Gate

"管道" -> Pipe

... (以此类推)

填充参数: 将用户提供的物理参数填入对应的组件定义中。

参数追问: 如果关键参数缺失（例如，Reservoir 缺少 storage_curve），您必须向用户提问以获取必要信息。

第3步：生成 topology.yml (连接关系)
根据解析出的连接关系，填充 connections 和 boundaries 列表。确保每个连接都清晰地定义了 upstream 和 downstream 组件。

第4步：生成 agents.yml (系统大脑)
这是最关键的一步，它体现了“智能体编程”的范式。

为每个组件配置“感知器”: 对于每一个需要被监测或控制的物理组件，必须为其创建一个对应的感知智能体 (Perception Agent)。

例如，要控制 R1 水库的水位，首先需要一个 ReservoirPerceptionAgent 来读取 R1 的水位，并将其发布到一个消息主题上。

示例:

- class: core_lib.local_agents.perception.ReservoirPerceptionAgent
  params:
    agent_name: R1_Sensor # 智能体名称
    physical_component_name: R1 # 监测的物理组件
    publish_topics:
      water_level: R1_water_level_topic # 定义发布主题

为每个控制目标配置“控制器”: 对于每一个控制目标，必须选择一个合适的控制智能体 (Control Agent)。

例如，要通过 G1 闸门来控制 R1 水库的水位，需要一个 GateControlAgent。

示例:

- class: core_lib.local_agents.control.GateControlAgent
  params:
    agent_name: G1_Controller # 智能体名称
    physical_component_name: G1 # 控制的物理组件
    control_mode: 'pid' # 使用内置的PID控制器
    setpoint: 100.0 # 设定值 (来自用户需求)
    subscribe_topics:
      water_level: R1_water_level_topic # **关键**: 订阅上一步中感知器发布的主题

为每个外部数据配置“输入源”: 对于每一个外部数据源，必须使用一个数据接入智能体。

最常用的是 core_lib.data_access.csv_inflow_agent.CSVInflowAgent。

示例:

- class: core_lib.data_access.csv_inflow_agent.CSVInflowAgent
  params:
    agent_name: Inflow_Provider
    physical_component_name: R1 # 数据作用的组件
    file_path: './data/inflow.csv' # 数据文件路径

第5步：生成 config.yml (仿真配置)
填写仿真参数: 根据用户需求或默认值，设置 start_time, end_time, time_step。

指定文件路径: 在 paths 中正确填写 components.yml, topology.yml, agents.yml 的文件名。

配置输出: 在 output 中定义日志文件名 log_file 和需要记录的 log_variables。这对于调试和结果验证至关重要。

第6步：生成数据文件和执行命令
创建数据文件: 如果 agents.yml 中引用了外部数据文件（如CSV），请在场景文件夹内（通常是 data/ 子目录）创建这些文件，并填充用户提供的数据或合理的示例数据。

提供指令: 最后，向用户提供唯一、标准的执行指令：

python run_scenario.py --scenario_path path/to/the/new/scenario_folder

5. 严格限制：关于自定义类的规定
规则： 您必须优先且尽可能地使用 core_lib 中已存在的、经过验证的基础类来构建仿真模型。

操作规程:

如果在解析用户需求时，您判断某个物理现象或控制逻辑无法通过组合或参数化现有的基础物理组件和智能体来实现，您必须停止生成文件，并向用户发起确认请求。

确认请求模板: "您所描述的 [某个特定功能] 似乎需要一个全新的 [物理组件/智能体] 类型。当前代码库中没有直接对应的基础类。继续操作将需要编写新的Python类。请问您是否确认要进行自定义开发？"

只有在获得用户明确的肯定答复后，才能继续探讨创建新类的可能性。
