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
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.identification.identification_agent import ParameterIdentificationAgent
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

def main():
    """
    运行闸门辨识场景的主函数。
    """
    print("开始执行闸门流量系数辨识示例...")

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

    true_gate_conf = components_config['true_gate']
    true_gate = Gate(name='true_gate',
                     initial_state=true_gate_conf['initial_state'],
                     parameters=true_gate_conf['parameters'])

    twin_gate_conf = components_config['twin_gate']
    twin_gate = Gate(name='twin_gate',
                     initial_state=twin_gate_conf['initial_state'],
                     parameters=twin_gate_conf['parameters'])

    components = [upstream_reservoir, downstream_reservoir, true_gate, twin_gate]

    # 创建智能体
    agents = []
    all_models = {c.name: c for c in components}

    # 感知智能体
    up_obs_conf = agents_config['upstream_observer']['parameters']
    agents.append(DigitalTwinAgent('upstream_observer', all_models[up_obs_conf['target_model']], bus, up_obs_conf['publish_topic']))

    down_obs_conf = agents_config['downstream_observer']['parameters']
    agents.append(DigitalTwinAgent('downstream_observer', all_models[down_obs_conf['target_model']], bus, down_obs_conf['publish_topic']))

    gate_obs_conf = agents_config['gate_observer']['parameters']
    agents.append(DigitalTwinAgent('gate_observer', all_models[gate_obs_conf['target_model']], bus, gate_obs_conf['publish_topic']))

    # 辨识与更新智能体
    id_agent_conf = agents_config['identification_agent']['parameters'].copy()
    # Remove target_model from config since we pass it explicitly
    id_agent_conf.pop('target_model', None)
    agents.append(ParameterIdentificationAgent(
        agent_id='identification_agent',
        target_model=twin_gate,
        message_bus=bus,
        **id_agent_conf
    ))

    updater_conf = agents_config['model_updater']['parameters']
    agents.append(ModelUpdaterAgent('model_updater', bus, f"identified_parameters/{updater_conf['target_model_name']}", all_models))

    # --- 3. 存储初始参数用于最终对比 ---
    true_coeff = true_gate.get_parameters()['discharge_coefficient']
    initial_twin_coeff = twin_gate.get_parameters()['discharge_coefficient']

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

    # --- 5. 定义并添加一个自定义智能体来触发闸门开度变化事件 ---
    class GateControlEventAgent(Agent):
        def __init__(self, agent_id, gate_to_control):
            super().__init__(agent_id)
            self.gate = gate_to_control

        def run(self, current_time: float):
            if current_time == 500:
                print(f"  [{current_time}s] 事件: 设置闸门开度为 0.8")
                self.gate.target_opening = 0.8
            elif current_time == 10000:
                print(f"  [{current_time}s] 事件: 设置闸门开度为 0.3")
                self.gate.target_opening = 0.3

    event_agent = GateControlEventAgent('gate_event_controller', true_gate)
    harness.add_agent(event_agent)


    print("开始多智能体仿真...")
    harness.run_mas_simulation()
    print("仿真结束。")

    # --- 6. 获取最终参数并展示结果 ---
    final_twin_coeff = twin_gate.get_parameters()['discharge_coefficient']

    print("\n辨识过程完成，正在对比结果...")
    print("-" * 50)
    print("闸门流量系数 (C) 辨识结果")
    print("-" * 50)
    print(f"真实值:      {true_coeff:.4f}")
    print(f"初始猜测值:   {initial_twin_coeff:.4f}")
    print(f"最终辨识值:  {final_twin_coeff:.4f}")
    print("-" * 50)

if __name__ == "__main__":
    main()
