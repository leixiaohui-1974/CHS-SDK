import sys
from pathlib import Path
import yaml
import numpy as np

# 将项目根目录添加到Python路径，以允许从core_lib导入
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.data_access.csv_inflow_agent import CsvInflowAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.identification.identification_agent import ParameterIdentificationAgent
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

def print_curve_comparison(title, true_curve, initial_curve, final_curve):
    """用于打印库容曲线对比结果的辅助函数。"""
    print("-" * 65)
    print(title)
    print("-" * 65)
    print(f"{'库容 (m^3)':<15} | {'真实水位 (m)':<15} | {'初始水位 (m)':<18} | {'最终水位 (m)':<15}")
    print("-" * 65)
    for i in range(len(true_curve)):
        vol = true_curve[i][0]
        true_level = true_curve[i][1]
        initial_level = initial_curve[i][1]
        final_level = final_curve[i][1]
        print(f"{vol:<15.1e} | {true_level:<15.2f} | {initial_level:<18.2f} | {final_level:<15.2f}")
    print("-" * 65)

def plot_curves(true_curve, initial_curve, final_curve):
    """绘制库容曲线以进行可视化比较。"""
    try:
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    except ImportError:
        print("\n未找到Matplotlib，跳过绘图步骤。")
        return

    true_vols = true_curve[:, 0]
    true_levels = true_curve[:, 1]
    initial_levels = initial_curve[:, 1]
    final_levels = final_curve[:, 1]

    plt.figure(figsize=(12, 7))
    plt.plot(true_vols, true_levels, 'g-o', label='真实曲线', linewidth=3, markersize=8)
    plt.plot(true_vols, initial_levels, 'r--x', label='初始猜测曲线', markersize=8)
    plt.plot(true_vols, final_levels, 'b-^', label='辨识后曲线')

    plt.title('库容曲线辨识结果')
    plt.xlabel('库容 (m^3)')
    plt.ylabel('水位 (m)')
    plt.legend()
    plt.grid(True)

    output_path = "identification_results.png"
    plt.savefig(output_path)
    print(f"\n对比图已保存至 {output_path}")


def main():
    """
    运行水库辨识场景的主函数。
    """
    print("开始执行水库库容曲线辨识示例...")

    scenario_path = Path(__file__).parent

    # --- 1. 从YAML文件加载配置 ---
    with open(scenario_path / 'config.yml', 'r') as f:
        config = yaml.safe_load(f)
    with open(scenario_path / 'components.yml', 'r') as f:
        components_config = yaml.safe_load(f)
    with open(scenario_path / 'agents.yml', 'r') as f:
        agents_config = yaml.safe_load(f)

    # --- 2. 手动实例化所有对象 ---
    bus = MessageBus()

    # 创建组件
    true_res_conf = components_config['true_reservoir']
    true_reservoir = Reservoir(
        name='true_reservoir',
        initial_state=true_res_conf['initial_state'],
        parameters=true_res_conf['parameters'],
        message_bus=bus
    )

    twin_res_conf = components_config['twin_reservoir']
    twin_reservoir = Reservoir(
        name='twin_reservoir',
        initial_state=twin_res_conf['initial_state'],
        parameters=twin_res_conf['parameters'],
        message_bus=bus
    )

    components = [true_reservoir, twin_reservoir]

    # 创建智能体
    inflow_agent_conf = agents_config['inflow_agent']['parameters']
    inflow_agent = CsvInflowAgent(
        agent_id='inflow_agent',
        message_bus=bus,
        target_component=true_reservoir,
        inflow_topic=inflow_agent_conf['topic'],
        csv_file_path=str(scenario_path / inflow_agent_conf['filepath']),
        time_column=inflow_agent_conf['time_column'],
        data_column=inflow_agent_conf['data_column']
    )

    obs_agent_conf = agents_config['observation_agent']['parameters']
    observation_agent = DigitalTwinAgent(
        agent_id='observation_agent',
        message_bus=bus,
        simulated_object=true_reservoir,
        state_topic=obs_agent_conf['publish_topic']
    )

    twin_perc_agent_conf = agents_config['twin_perception_agent']['parameters']
    twin_perception_agent = DigitalTwinAgent(
        agent_id='twin_perception_agent',
        message_bus=bus,
        simulated_object=twin_reservoir,
        state_topic=twin_perc_agent_conf['publish_topic']
    )

    id_agent_conf = agents_config['identification_agent']['parameters'].copy()
    # Remove target_model from config since we pass it explicitly
    id_agent_conf.pop('target_model', None)
    identification_agent = ParameterIdentificationAgent(
        agent_id='identification_agent',
        target_model=twin_reservoir,
        message_bus=bus,
        **id_agent_conf
    )

    all_models_dict = {comp.name: comp for comp in components}
    model_updater = ModelUpdaterAgent(
        agent_id='model_updater',
        message_bus=bus,
        parameter_topic="identified_parameters/twin_reservoir",
        models=all_models_dict
    )

    agents = [inflow_agent, observation_agent, twin_perception_agent, identification_agent, model_updater]

    # --- 3. 存储初始参数用于最终对比 ---
    true_curve = np.array(true_reservoir.get_parameters()['storage_curve'])
    initial_twin_curve = np.array(twin_reservoir.get_parameters()['storage_curve'])

    # --- 4. 初始化并运行仿真平台 ---
    print("\n正在初始化仿真平台...")
    harness = SimulationHarness(config=config['simulation'])
    harness.message_bus = bus # 确保所有对象共享同一个消息总线

    # 向仿真平台添加组件和智能体
    for comp in components:
        harness.add_component(comp.name, comp)
    for agent in agents:
        harness.add_agent(agent)

    # 构建仿真平台（例如，进行拓扑排序）
    harness.build()

    print("开始多智能体仿真...")
    harness.run_mas_simulation()
    print("仿真结束。")

    # --- 5. 获取最终参数并展示结果 ---
    final_twin_curve = np.array(twin_reservoir.get_parameters()['storage_curve'])

    print("\n辨识过程完成，正在对比结果...")
    print_curve_comparison(
        "水库库容曲线辨识结果",
        true_curve,
        initial_twin_curve,
        final_twin_curve
    )

    # --- 6. 绘制结果图用于可视化检查 ---
    plot_curves(true_curve, initial_twin_curve, final_twin_curve)


if __name__ == "__main__":
    main()
