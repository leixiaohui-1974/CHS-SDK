import pandas as pd

# Load the simulation results
try:
    df = pd.read_csv('examples/watertank_refactored/01_simple_simulation/results.csv')
except FileNotFoundError as e:
    print(f"Error loading data: {e}")
    exit()

# --- KPI Calculations ---
dt = df['time'].diff().mean()

# 1. Total Inflow Volume
# The 'simple_tank.inflow' column represents the flow rate (m³/s)
# To get volume, we multiply by the time step dt and sum it up.
total_inflow = (df['simple_tank.inflow'] * dt).sum()

# 2. Final Water Level
final_water_level = df['simple_tank.water_level'].iloc[-1]

# --- Format Output ---
kpi_table = f"""
| 指标 (Indicator) | 值 (Value) |
| :--- | :--- |
| 总入流量 (Total Inflow) | {total_inflow:.2f} m³ |
| 最终水位 (Final Water Level) | {final_water_level:.2f} m |
"""

print("KPIs for Scenario 01:\n")
print(kpi_table)
