import pandas as pd

# --- Configuration ---
RESULTS_CSV_PATH = 'examples/watertank_refactored/02_parameter_identification/results.csv'
# This value is manually extracted from the simulation log for this specific run.
# A better implementation would be to have the agent log this to a topic.
FINAL_IDENTIFIED_COEFFICIENT = 0.3578
TRUE_COEFFICIENT = 0.8 # From components.yml for the 'real_valve'

# --- Load Data ---
try:
    df = pd.read_csv(RESULTS_CSV_PATH)
except FileNotFoundError as e:
    print(f"Error loading data: {e}")
    exit()

# --- KPI Calculations ---
# 1. Final error between real and twin water levels
final_level_error = abs(df['real_reservoir.water_level'].iloc[-1] - df['twin_reservoir.water_level'].iloc[-1])

# 2. Identification Error
identification_error = abs(FINAL_IDENTIFIED_COEFFICIENT - TRUE_COEFFICIENT) / TRUE_COEFFICIENT * 100

# --- Format Output ---
kpi_table = f"""
| 指标 (Indicator) | 值 (Value) |
| :--- | :--- |
| 最终辨识出的排放系数 (Final Identified Discharge Coeff.) | {FINAL_IDENTIFIED_COEFFICIENT:.4f} |
| 排放系数真值 (True Discharge Coeff.) | {TRUE_COEFFICIENT:.4f} |
| 辨识误差 (Identification Error) | {identification_error:.2f} % |
| 真实与孪生水位最终误差 (Final Water Level Error) | {final_level_error:.4f} m |
"""

print("KPIs for Scenario 02:\n")
print(kpi_table)
