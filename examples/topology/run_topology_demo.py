#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水利系统拓扑仿真演示脚本
基于CHS-SDK核心库的完整仿真案例

系统组成：
- 上游水库 -> 渠道1 -> 分水口1 -> 渠道2 -> 管道1 -> 闸门1 -> 渠道3 -> 下游水库
"""

import os
import sys
import yaml
import numpy as np
from pathlib import Path

# 添加核心库路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入核心库
from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def load_configuration():
    """加载配置文件"""
    print("=== 加载配置文件 ===")
    
    config_dir = Path(__file__).parent
    
    # 检查配置文件是否存在
    config_files = {
        'config': config_dir / 'config.yml',
        'components': config_dir / 'components.yml',
        'topology': config_dir / 'topology.yml',
        'agents': config_dir / 'agents.yml'
    }
    
    for name, file_path in config_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        print(f"✓ {name}: {file_path}")
    
    return str(config_dir)

def create_simulation_components(scenario_path):
    """创建仿真组件"""
    print("\n=== 创建仿真组件 ===")
    
    try:
        # 创建YAML仿真加载器
        loader = YamlSimulationLoader(scenario_path)
        print("✓ YAML仿真加载器创建完成")
        
        # 加载完整仿真
        harness = loader.load()
        print("✓ 仿真加载完成")
        
        # 获取组件信息
        components = getattr(loader, 'component_instances', {})
        message_bus = getattr(loader, 'message_bus', None)
        
        print(f"✓ 成功加载 {len(components)} 个组件:")
        for name, component in components.items():
            print(f"  - {name}: {component.__class__.__name__}")
        
        return harness, components, message_bus
        
    except Exception as e:
        print(f"✗ 创建仿真组件失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def run_simulation(harness):
    """运行仿真"""
    print("\n=== 开始仿真 ===")
    
    try:
        # 运行MAS仿真
        print("正在运行多智能体仿真...")
        harness.run_mas_simulation()
        
        print("✓ 仿真运行完成")
        
        # 获取仿真历史数据
        history = getattr(harness, 'history', [])
        print(f"✓ 仿真历史包含 {len(history)} 个时间步")
        
        return history
        
    except Exception as e:
        print(f"✗ 仿真运行失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def analyze_results(results):
    """分析和展示仿真结果"""
    print("\n=== 仿真结果分析 ===")
    
    if not results:
        print("⚠ 没有仿真结果可供分析")
        return
    
    print(f"仿真历史记录数量: {len(results)}")
    
    # 检查数据结构
    if results:
        sample_step = results[-1]
        print(f"最终数据结构类型: {type(sample_step)}")
        if isinstance(sample_step, dict):
            print(f"最终数据键: {list(sample_step.keys())}")
        
        # 分析最后的状态 - 使用正确的数据结构
        final_step = results[-1]
        current_time = final_step.get('time', 0)  # 使用'time'而不是'current_time'
        
        print(f"最终仿真时间: {current_time} 秒 ({current_time/3600:.2f} 小时)")
        
        # 查找组件数据 - 直接从步骤中获取
        component_count = 0
        key_components = ['Upstream_Reservoir', 'Channel_1', 'Gate_1', 'Channel_3', 'Downstream_Reservoir']
        
        print("\n关键组件最终状态:")
        for comp_name in key_components:
            if comp_name in final_step:
                component_count += 1
                state = final_step[comp_name]
                print(f"  {comp_name}:")
                
                # 显示水位信息
                if 'water_level' in state:
                    print(f"    水位: {state['water_level']:.3f} m")
                
                # 显示流量信息
                if 'outflow' in state:
                    print(f"    出流: {state['outflow']:.3f} m³/s")
                
                # 显示闸门开度
                if 'opening' in state:
                    print(f"    开度: {state['opening']:.3f}")
                
                # 显示库容
                if 'volume' in state:
                    print(f"    库容: {state['volume']:.1f} m³")
                
                # 显示入流
                if 'inflow' in state:
                    print(f"    入流: {state['inflow']:.3f} m³/s")
            else:
                print(f"  {comp_name}: 未找到数据")
        
        print(f"\n找到的组件数量: {component_count}")
        
        # 显示其他组件
        other_components = [key for key in final_step.keys() if key not in ['time'] and key not in key_components]
        if other_components:
            print(f"其他组件: {other_components}")

def save_results(results, output_dir=None):
    """保存仿真结果"""
    print("\n=== 保存仿真结果 ===")
    
    if output_dir is None:
        output_dir = Path(__file__).parent  # 直接保存到topology文件夹
    
    output_dir = Path(output_dir)
    
    try:
        # 保存为JSON格式
        import json
        output_file = output_dir / "topology_simulation_results.json"
        
        # 转换numpy数组为列表以便JSON序列化
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        converted_results = convert_numpy(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON结果已保存到: {output_file}")
        
        # 创建详细的Excel报告
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = output_dir / f"topology_simulation_detailed_results_{timestamp}.xlsx"
        create_detailed_excel_report(results, excel_file)
        print(f"✓ 详细Excel报告已保存到: {excel_file}")
        
        # 创建简单的CSV报告（保留兼容性）
        csv_file = output_dir / "key_metrics.csv"
        create_csv_report(results, csv_file)
        print(f"✓ 关键指标CSV已保存到: {csv_file}")
        
    except Exception as e:
        print(f"⚠ 保存结果时出错: {e}")
        import traceback
        traceback.print_exc()

def create_detailed_excel_report(results, excel_file):
    """创建Excel格式的详细仿真报告"""
    try:
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils.dataframe import dataframe_to_rows
    except ImportError:
        print("⚠ 需要安装pandas和openpyxl: pip install pandas openpyxl")
        return
    
    # 创建Excel工作簿
    wb = Workbook()
    wb.remove(wb.active)  # 删除默认工作表
    
    # 1. 总体数据工作表
    ws_overview = wb.create_sheet("总体数据")
    
    # 准备数据
    data_rows = []
    
    for step in results:
        current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
        states = step.get('component_states', {})
        
        # 初始化行数据
        row_data = {
            '时间(s)': current_time,
            '时间(h)': round(current_time / 3600, 3),
        }
        
        # 闸门数据
        if 'Gate_1' in step:
            gate_state = step['Gate_1']
            row_data.update({
                '闸门开度': gate_state.get('opening', 0),
                '闸门过流流量(m³/s)': gate_state.get('outflow', 0),
            })
        
        # 渠道数据 - 闸前和闸后水深（这里用水位代替）
        if 'Channel_1' in step:
            ch1_state = step['Channel_1']
            row_data.update({
                '闸前水位(m)': ch1_state.get('water_level', 0),
                '渠道1入流(m³/s)': ch1_state.get('inflow', 0),
                '渠道1出流(m³/s)': ch1_state.get('outflow', 0),
            })
        
        if 'Channel_3' in step:
            ch3_state = step['Channel_3']
            row_data.update({
                '闸后水位(m)': ch3_state.get('water_level', 0),
                '渠道3入流(m³/s)': ch3_state.get('inflow', 0),
                '渠道3出流(m³/s)': ch3_state.get('outflow', 0),
            })
        
        if 'Channel_2' in step:
            ch2_state = step['Channel_2']
            row_data.update({
                '渠道2入流(m³/s)': ch2_state.get('inflow', 0),
                '渠道2出流(m³/s)': ch2_state.get('outflow', 0),
                '渠道2水位(m)': ch2_state.get('water_level', 0),
            })
        
        # 倒虹吸数据
        if 'Pipe_1' in step:
            pipe_state = step['Pipe_1']
            row_data.update({
                '倒虹吸流量(m³/s)': pipe_state.get('outflow', 0),
                '倒虹吸水头损失(m)': pipe_state.get('head_loss', 0),
            })
            
            # 倒虹吸进口和出口水深（通过相邻渠道的水位来推算）
            if 'Channel_2' in step and 'Channel_3' in step:
                row_data.update({
                    '倒虹吸进口水深(m)': step['Channel_2'].get('water_level', 0),
                    '倒虹吸出口水深(m)': step['Channel_3'].get('water_level', 0),
                })
        
        # 水库数据
        if 'Upstream_Reservoir' in step:
            up_res_state = step['Upstream_Reservoir']
            row_data.update({
                '上游水库水位(m)': up_res_state.get('water_level', 0),
                '上游水库库容(m³)': up_res_state.get('volume', 0),
                '上游水库出流(m³/s)': up_res_state.get('outflow', 0),
            })
        
        if 'Downstream_Reservoir' in step:
            down_res_state = step['Downstream_Reservoir']
            row_data.update({
                '下游水库水位(m)': down_res_state.get('water_level', 0),
                '下游水库库容(m³)': down_res_state.get('volume', 0),
                '下游水库出流(m³/s)': down_res_state.get('outflow', 0),
            })
        
        # 分水口数据
        if 'Diversion_1' in step:
            div_state = step['Diversion_1']
            row_data.update({
                '分水口1出流(m³/s)': div_state.get('outflow', 0),
            })
        
        data_rows.append(row_data)
    
    # 转换为Pandas DataFrame
    df = pd.DataFrame(data_rows)
    
    # 写入数据到Excel
    for r in dataframe_to_rows(df, index=False, header=True):
        ws_overview.append(r)
    
    # 设置样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # 设置表头样式
    for cell in ws_overview[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # 调整列宽
    for column in ws_overview.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 20)
        ws_overview.column_dimensions[column_letter].width = adjusted_width
    
    # 2. 创建分类数据工作表
    
    # 闸门数据工作表
    ws_gate = wb.create_sheet("闸门数据")
    gate_data = []
    for step in results:
        current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
        states = step.get('component_states', {})
        if 'Gate_1' in states:
            gate_state = states['Gate_1']
            gate_data.append({
                '时间(s)': current_time,
                '时间(h)': round(current_time / 3600, 3),
                '闸门开度': gate_state.get('opening', 0),
                '闸门过流流量(m³/s)': gate_state.get('outflow', 0),
                '闸前水位(m)': states.get('Channel_1', {}).get('water_level', 0),
                '闸后水位(m)': states.get('Channel_3', {}).get('water_level', 0),
            })
    
    df_gate = pd.DataFrame(gate_data)
    for r in dataframe_to_rows(df_gate, index=False, header=True):
        ws_gate.append(r)
    
    # 设置闸门数据表头样式
    for cell in ws_gate[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # 渠道数据工作表
    ws_channel = wb.create_sheet("渠道数据")
    channel_data = []
    for step in results:
        current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
        states = step.get('component_states', {})
        
        row = {
            '时间(s)': current_time,
            '时间(h)': round(current_time / 3600, 3),
        }
        
        for ch_name, ch_label in [('Channel_1', '渠道1'), ('Channel_2', '渠道2'), ('Channel_3', '渠道3')]:
            if ch_name in states:
                ch_state = states[ch_name]
                row.update({
                    f'{ch_label}水位(m)': ch_state.get('water_level', 0),
                    f'{ch_label}入流(m³/s)': ch_state.get('inflow', 0),
                    f'{ch_label}出流(m³/s)': ch_state.get('outflow', 0),
                    f'{ch_label}库容(m³)': ch_state.get('volume', 0),
                })
        
        channel_data.append(row)
    
    df_channel = pd.DataFrame(channel_data)
    for r in dataframe_to_rows(df_channel, index=False, header=True):
        ws_channel.append(r)
    
    # 设置渠道数据表头样式
    for cell in ws_channel[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # 倒虹吸数据工作表
    ws_pipe = wb.create_sheet("倒虹吸数据")
    pipe_data = []
    for step in results:
        current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
        states = step.get('component_states', {})
        if 'Pipe_1' in states:
            pipe_state = states['Pipe_1']
            pipe_data.append({
                '时间(s)': current_time,
                '时间(h)': round(current_time / 3600, 3),
                '倒虹吸流量(m³/s)': pipe_state.get('outflow', 0),
                '倒虹吸水头损失(m)': pipe_state.get('head_loss', 0),
                '进口水深(m)': states.get('Channel_2', {}).get('water_level', 0),
                '出口水深(m)': states.get('Channel_3', {}).get('water_level', 0),
            })
    
    df_pipe = pd.DataFrame(pipe_data)
    for r in dataframe_to_rows(df_pipe, index=False, header=True):
        ws_pipe.append(r)
    
    # 设置倒虹吸数据表头样式
    for cell in ws_pipe[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # 水库数据工作表
    ws_reservoir = wb.create_sheet("水库数据")
    reservoir_data = []
    for step in results:
        current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
        states = step.get('component_states', {})
        
        row = {
            '时间(s)': current_time,
            '时间(h)': round(current_time / 3600, 3),
        }
        
        if 'Upstream_Reservoir' in states:
            up_state = states['Upstream_Reservoir']
            row.update({
                '上游水库水位(m)': up_state.get('water_level', 0),
                '上游水库库容(m³)': up_state.get('volume', 0),
                '上游水库出流(m³/s)': up_state.get('outflow', 0),
            })
        
        if 'Downstream_Reservoir' in states:
            down_state = states['Downstream_Reservoir']
            row.update({
                '下游水库水位(m)': down_state.get('water_level', 0),
                '下游水库库容(m³)': down_state.get('volume', 0),
                '下游水库出流(m³/s)': down_state.get('outflow', 0),
            })
        
        reservoir_data.append(row)
    
    df_reservoir = pd.DataFrame(reservoir_data)
    for r in dataframe_to_rows(df_reservoir, index=False, header=True):
        ws_reservoir.append(r)
    
    # 设置水库数据表头样式
    for cell in ws_reservoir[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # 调整所有工作表的列宽
    for ws in [ws_gate, ws_channel, ws_pipe, ws_reservoir]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # 保存Excel文件
    wb.save(excel_file)
    print(f"✓ Excel报告包含{len(wb.sheetnames)}个工作表: {", ".join(wb.sheetnames)}")

def create_csv_report(results, csv_file):
    """创建CSV格式的关键指标报告"""
    import csv
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 写入标题行
        headers = ['时间(s)', '上游水库水位(m)', '渠道1水位(m)', '闸门1开度', 
                  '渠道3水位(m)', '下游水库水位(m)', '闸门1流量(m³/s)']
        writer.writerow(headers)
        
        # 写入数据行
        for step in results:
            current_time = step.get('time', 0)  # 使用'time'而不是'current_time'
            
            row = [current_time]
            
            # 提取关键指标 - 直接从步骤中获取
            components = ['Upstream_Reservoir', 'Channel_1', 'Gate_1', 'Channel_3', 'Downstream_Reservoir']
            metrics = ['water_level', 'water_level', 'opening', 'water_level', 'water_level']
            
            for comp, metric in zip(components, metrics):
                if comp in step and metric in step[comp]:
                    row.append(step[comp][metric])
                else:
                    row.append('')
            
            # 添加闸门流量
            if 'Gate_1' in step and 'outflow' in step['Gate_1']:
                row.append(step['Gate_1']['outflow'])
            else:
                row.append('')
            
            writer.writerow(row)
    """创建CSV格式的关键指标报告"""
    import csv
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 写入标题行
        headers = ['时间(s)', '上游水库水位(m)', '渠道1水位(m)', '闸门1开度', 
                  '渠道3水位(m)', '下游水库水位(m)', '闸门1流量(m³/s)']
        writer.writerow(headers)
        
        # 写入数据行
        for step in results:
            current_time = step.get('time', 0)  # 修正：使用'time'而不是'current_time'
            states = step.get('component_states', {})
            
            row = [current_time]
            
            # 提取关键指标
            components = ['Upstream_Reservoir', 'Channel_1', 'Gate_1', 'Channel_3', 'Downstream_Reservoir']
            metrics = ['water_level', 'water_level', 'opening', 'water_level', 'water_level']
            
            for comp, metric in zip(components, metrics):
                if comp in states and metric in states[comp]:
                    row.append(states[comp][metric])
                else:
                    row.append('')
            
            # 添加闸门流量
            if 'Gate_1' in states and 'outflow' in states['Gate_1']:
                row.append(states['Gate_1']['outflow'])
            else:
                row.append('')
            
            writer.writerow(row)

def main():
    """主函数"""
    print("CHS-SDK 水利系统拓扑仿真演示")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        scenario_path = load_configuration()
        
        # 2. 创建仿真组件
        harness, components, message_bus = create_simulation_components(scenario_path)
        
        # 3. 运行仿真
        results = run_simulation(harness)
        
        # 4. 分析结果
        analyze_results(results)
        
        # 5. 保存结果
        save_results(results)
        
        print("\n" + "=" * 50)
        print("✓ 仿真演示完成！")
        
    except Exception as e:
        print(f"\n✗ 仿真演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)