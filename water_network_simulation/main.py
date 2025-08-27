import time
import os

def run_simulation():
    """
    主仿真函数
    """
    # Create __init__.py files to make directories importable as packages
    # This is a good practice for structuring Python projects.
    dirs_to_init = ['agents', 'communication', 'models']
    for d in dirs_to_init:
        os.makedirs(d, exist_ok=True)
        init_path = os.path.join(d, '__init__.py')
        if not os.path.exists(init_path):
            open(init_path, 'w').close()

    from communication.pubsub_broker import PubSubBroker
    from agents.ontology_simulation_agent import OntologySimulationAgent
    from agents.channel_perception_agent import ChannelPerceptionAgent
    from agents.gate_station_agents import GateStationPerceptionAgent, GateStationControlAgent
    from agents.central_dispatch_agent import CentralDispatchAgent

    print("===============================================")
    print("=== Water Network 'Unmanned' System Simulation ===")
    print("===============================================\n")

    # 1. 初始化通信代理
    broker = PubSubBroker()

    # 2. 初始化所有智能体
    # 本体仿真智能体 (物理世界)
    initial_state = {'upstream_level': 5.0, 'downstream_level': 4.5, 'inflow': 10}
    sim_agent = OntologySimulationAgent("simulator_01", broker, initial_state)

    # 渠道感知智能体 (下游渠道的数字孪生)
    channel_agent = ChannelPerceptionAgent("channel_perception_01", broker, "downstream_channel")

    # 闸站感知与控制智能体
    gate_perception_agent = GateStationPerceptionAgent("gate_perception_01", broker, "gate_1")
    pid_params = {'Kp': 0.5, 'Ki': 0.1, 'Kd': 0.05}
    gate_control_agent = GateStationControlAgent("gate_control_01", broker, "gate_1", pid_params)

    # 中心调度智能体 (宏观大脑)
    central_agent = CentralDispatchAgent("central_dispatch_01", broker)

    agents = [sim_agent, channel_agent, gate_perception_agent, gate_control_agent, central_agent]

    # 3. 运行仿真循环
    simulation_steps = 200
    print(f"\n--- Starting simulation for {simulation_steps} steps ---\n")
    time.sleep(2)

    for i in range(simulation_steps):
        print(f"\n========================= TIME STEP {i} =========================")

        # 按照逻辑顺序执行每个智能体的单步操作
        # 1. 仿真器根据上一轮的指令更新物理世界
        sim_agent.run_step(i)
        time.sleep(0.1) # 等待消息传播

        # 2. 感知智能体获取新数据并进行分析
        channel_agent.run_step(i)
        gate_perception_agent.run_step(i)
        time.sleep(0.1)

        # 3. 中心调度智能体根据感知信息进行宏观决策
        central_agent.run_step(i)
        time.sleep(0.1)

        # 4. 现地控制智能体根据上级指令和本地状态生成具体控制指令
        gate_control_agent.run_step(i)

        time.sleep(0.2) # 减慢循环速度，便于观察

    print("\n===============================================")
    print("=== Simulation Finished ===")
    print("===============================================\n")


if __name__ == "__main__":
    # Change CWD to the script's directory to ensure relative imports work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != script_dir:
        os.chdir(script_dir)
    run_simulation()
