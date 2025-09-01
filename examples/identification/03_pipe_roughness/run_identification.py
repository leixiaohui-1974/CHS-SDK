import sys
from pathlib import Path
import yaml
import numpy as np

# 将项目根目录添加到Python路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core.interfaces import Agent
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pipe import Pipe
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.identification.identification_agent import ParameterIdentificationAgent
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

def main():
    """
    运行管道糙率辨识场景的主函数。
    """
    print("开始执行管道糙率 (曼宁 n) 辨识示例...")

    scenario_path = Path(__file__).parent

    # --- 1. 从YAML文件加载配置 ---
    with open(scenario_path / 'config.yml', 'r') as f:
        config = yaml.safe_load(f)
    with open(scenario_path / 'components.yml', 'r') as f:
        components_config = yaml.safe_load(f)
    with open(scenario_path / 'agents.yml', 'r') as f:
        agents_config = yaml.safe_load(f)
    with open(scenario_path / 'topology.yml', 'r') as f:
        topology_config = yaml.safe_load(f)

    # --- 2. 手动实例化所有对象 ---
    bus = MessageBus()

    # 创建组件
    up_res_conf = components_config['upstream_reservoir']
    upstream_reservoir = Reservoir(name='upstream_reservoir',
                                   initial_state=up_res_conf['initial_state'],
                                   parameters=up_res_conf['parameters'])

    down_res_conf = components_config['downstream_reservoir']
    downstream_reservoir = Reservoir(name='downstream_reservoir',
                                     initial_state=down_res_conf['initial_state'],
                                     parameters=down_res_conf['parameters'])

    true_pipe_conf = components_config['true_pipe']
    true_pipe = Pipe(name='true_pipe',
                     initial_state=true_pipe_conf['initial_state'],
                     parameters=true_pipe_conf['parameters'])

    twin_pipe_conf = components_config['twin_pipe']
    twin_pipe = Pipe(name='twin_pipe',
                     initial_state=twin_pipe_conf['initial_state'],
                     parameters=twin_pipe_conf['parameters'])

    components = [upstream_reservoir, downstream_reservoir, true_pipe, twin_pipe]

    # 创建智能体
    agents = []
    all_models = {c.name: c for c in components}

    up_obs_conf = agents_config['upstream_observer']['parameters']
    agents.append(DigitalTwinAgent('upstream_observer', all_models[up_obs_conf['target_model']], bus, up_obs_conf['publish_topic']))

    down_obs_conf = agents_config['downstream_observer']['parameters']
    agents.append(DigitalTwinAgent('downstream_observer', all_models[down_obs_conf['target_model']], bus, down_obs_conf['publish_topic']))

    pipe_obs_conf = agents_config['pipe_observer']['parameters']
    agents.append(DigitalTwinAgent('pipe_observer', all_models[pipe_obs_conf['target_model']], bus, pipe_obs_conf['publish_topic']))

# 辨识与更新智能体
    id_agent_conf = agents_config['identification_agent']['parameters'].copy()
    # Remove target_model from config since we pass it explicitly
    id_agent_conf.pop('target_model', None)
    agents.append(ParameterIdentificationAgent(
        agent_id='identification_agent',
        target_model=twin_pipe,
        message_bus=bus,
        **id_agent_conf
    ))

    updater_conf = agents_config['model_updater']['parameters']
    agents.append(ModelUpdaterAgent('model_updater', bus, f"identified_parameters/{updater_conf['target_model_name']}", all_models))

    # --- 3. 存储初始参数用于最终对比 ---
    true_n = true_pipe.get_parameters()['manning_n']
    initial_twin_n = twin_pipe.get_parameters()['manning_n']

    # --- 4. 初始化并运行仿真平台 ---
    print("\n正在初始化仿真平台...")
    harness = SimulationHarness(config=config['simulation'])
    harness.message_bus = bus

    for comp in components:
        harness.add_component(comp.name, comp)
    for link in topology_config.get('links', []):
        harness.add_connection(link['upstream'], link['downstream'])
    for agent in agents:
        harness.add_agent(agent)

    harness.build()

    print("开始多智能体仿真...")
    harness.run_mas_simulation()
    print("仿真结束。")

    # --- 5. 获取最终参数并展示结果 ---
    final_twin_n = twin_pipe.get_parameters()['manning_n']

    print("\n辨识过程完成，正在对比结果...")
    print("-" * 50)
    print("管道糙率 (曼宁 n) 辨识结果")
    print("-" * 50)
    print(f"真实值:      {true_n:.6f}")
    print(f"初始猜测值:   {initial_twin_n:.6f}")
    print(f"最终辨识值:  {final_twin_n:.6f}")
    print("-" * 50)

if __name__ == "__main__":
    main()
