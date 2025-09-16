# 给 Jules 的任务提示：使用 Pydantic 和 FastAPI 重构水力模型配置与 API

致： Jules  
发件人： 项目负责人  
主题： 技术任务：使用 Pydantic 和 FastAPI 重构水力模型配置与 API

## 高级目标

为了提升我们 CHS-SDK 的健壮性、易用性和开发者体验，我们需要进行一次重要的技术升级。本次任务的核心是将我们当前基于 YAML 的配置体系与现代化的数据验证框架相结合，并将 Web 服务后端从 Flask 迁移至 FastAPI。

## 背景与动机

正如我们的核心设计哲学所强调的，系统采用"数据驱动+智能体编程"的范式。用户通过编写 YAML 配置文件来定义仿真场景。然而，目前这种方式缺少一套在代码执行前对配置进行静态检查的强大机制。当用户提供了错误的拓扑关系（例如，连接了一个不存在的组件）或数据类型不匹配时，错误往往在仿真运行到一半时才以比较晦涩的方式抛出。

通过引入 Pydantic 和 FastAPI，我们可以实现以下关键目标：

1. **强数据验证**：在任务开始前，对用户提供的所有配置数据进行严格的结构和类型验证。
2. **自文档化 API**：自动生成交互式的 Swagger UI 接口文档，极大方便前端或其他服务的对接。
3. **精准的错误提示**：利用框架能力，为不规范的输入数据提供清晰、具体的错误信息，提升用户体验。

## 具体行动项

请按以下步骤执行此项重构任务：

### 1. 为所有基础单元定义 Pydantic 模型

#### 1a. 水力学模型 (Hydraulic Models)

**任务**: 为 core_lib/physical_objects 和 core_lib/hydro_nodes 目录下的每一个核心物理组件（如 Reservoir, Gate, Pipe, UnifiedCanal 等）创建一个对应的 Pydantic BaseModel。

**要求**:
- 模型中的每个字段都必须有严格的类型注解（例如 name: str, length: float, levels: List[float]）。
- 利用 Pydantic 的 validator 功能，为复杂的约束条件添加验证逻辑。例如，在 Reservoir 模型中，验证 storage_curve 里的 levels 和 storage 两个列表长度必须相等。

#### 1b. 智能体模型 (Agent Models)

**任务**: 同样地，为 core_lib 中所有可配置的智能体类（如 ReservoirPerceptionAgent, GateControlAgent, CSVInflowAgent 等）创建对应的 Pydantic BaseModel。

**要求**:
- 这些模型主要用于验证 agents.yml 中每个智能体条目下的 params 字典。
- 每个参数都应有明确的类型注解（例如 agent_name: str, setpoint: float, pid_params: PIDParamsModel）。可以为像 PID 参数这样的复杂结构创建嵌套的 Pydantic 模型。

### 2. 为系统级配置文件创建顶层 Pydantic 模型

**任务**: 分别为 components.yml、topology.yml 和 agents.yml 的整体结构创建顶层的 Pydantic 模型。这些模型将聚合在步骤 1 中创建的基础单元模型。

**要求**:
- ComponentsModel: 其结构应能容纳按类型组织的物理组件列表，例如 reservoirs: List[ReservoirModel] = [], gates: List[GateModel] = []。
- TopologyModel: 需要添加一个自定义的根验证器 (root_validator)，用于检查 connections 中定义的 upstream 和 downstream 名称是否都真实存在于传入的 ComponentsModel 实例所包含的组件列表中。这是实现拓扑关系验证的关键。
- AgentsModel: 这应该是一个包含多种智能体模型的列表。最关键的是，需要定义一个能代表单个智能体配置的 AgentConfigModel，它包含 class: str 字段和 params: BaseModel 字段。然后，使用 Pydantic 的 Union 类型来指定 params 可以是步骤 1b 中定义的任何一种具体的智能体参数模型。这样，解析器就可以根据 class 的值来决定使用哪个 Pydantic 模型验证 params 的内容。

### 3. 将 Web 服务从 Flask 迁移到 FastAPI

**任务**: 替换 api/server.py 中现有的 Flask 应用实例，改为初始化一个 FastAPI 应用。

**目标**: 搭建起基础的 FastAPI 服务框架。

### 4. 创建带数据验证的 API 端点 (Endpoint)

**任务**: 设计并实现一个核心的 API 端点，例如 POST /run_simulation。这个端点将作为根目录下 run_scenario.py 脚本的 Web API 等价物。

**要求**:
- 此端点的请求体 (Request Body) 必须使用在第2步中创建的系统级 Pydantic 模型来定义，其数据结构应与 YAML 文件一一对应。
- FastAPI 将利用这些模型自动解析和验证传入的 JSON 数据。如果验证失败，它会自动返回一个包含详细错误信息的 422 Unprocessable Entity 响应。你无需手动编写验证和错误处理代码。
- 后端逻辑: 该端点的实现逻辑应当复用 run_scenario.py 所调用的核心仿真引擎。其主要职责是将经过 Pydantic 验证的数据模型传递给仿真引擎来执行，并将结果返回给客户端。

### 5. 验证自动生成的 API 文档

**任务**: 启动重构后的 FastAPI 服务。

**要求**: 访问 /docs 路径，确认 Swagger UI 是否已自动生成并且功能正常。访问 /redoc 确认 ReDoc 文档是否可用。确保 API 的模型、参数、类型和约束都已在文档中清晰展示。

## 预期成果

任务完成后，我们将拥有一个具备以下特性的、更加现代化和可靠的 Web 服务：

1. 一个能够接收结构化 JSON 数据（其结构与我们的 YAML 文件相对应）来运行仿真的 API。
2. 在仿真开始前就能捕获绝大多数配置错误的强大验证能力。
3. 一份无需手动维护、始终与代码同步的交互式 API 文档。

## 建议

建议从最核心的几个组件（如 Reservoir 和 Gate）和对应的智能体开始，先完成它们的 Pydantic 模型作为概念验证，然后再逐步推广到整个库。

祝顺利！
