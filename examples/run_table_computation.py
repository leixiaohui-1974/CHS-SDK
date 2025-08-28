import json
import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from itertools import combinations

# --- Constants ---
RHO = 1000  # Water density
G = 9.81    # Gravity

def get_turbine_efficiency(power_mw, head_m, params):
    p_opt, p_max, base_eff = params['p_opt'], params['p_max'], params['base_eff']
    if power_mw <= 0 or power_mw > p_max: return 0
    power_penalty = ((power_mw - p_opt) / p_opt)**2
    head_penalty = ((head_m - 12) / 12)**2
    return max(0, base_eff * (1 - power_penalty - head_penalty))

def power_to_flow(power_mw, head_m, efficiency):
    if efficiency <= 0: return float('inf')
    return (power_mw * 1e6) / (efficiency * RHO * G * head_m)

def objective_function(power_allocations, head_m, turbine_params):
    total_flow = sum(power_to_flow(p, head_m, get_turbine_efficiency(p, head_m, tp)) for p, tp in zip(power_allocations, turbine_params))
    return total_flow

def optimize_for_combination(target_power, head, num_active, turbine_indices, all_params):
    active_params = [all_params[i] for i in turbine_indices]
    constraints = ({'type': 'eq', 'fun': lambda p: np.sum(p) - target_power})
    bounds = [(p['p_min'], p['p_max']) for p in active_params]
    initial_guess = [target_power / num_active] * num_active
    result = minimize(objective_function, initial_guess, args=(head, active_params), method='SLSQP', bounds=bounds, constraints=constraints)
    if result.success:
        final_allocations = np.zeros(len(all_params))
        for i, idx in enumerate(turbine_indices):
            final_allocations[idx] = result.x[i]
        return result.fun, final_allocations
    return float('inf'), np.zeros(len(all_params))

def generate_turbine_table_from_config(config):
    print(f"--- Generating Turbine Economic Dispatch Table ---")
    turbine_params = config['turbine_params']
    grid = config['calculation_grid']
    head_range = np.arange(grid['head_m']['start'], grid['head_m']['stop'], grid['head_m']['step'])
    power_range = np.arange(grid['power_mw']['start'], grid['power_mw']['stop'], grid['power_mw']['step'])

    table_data = []
    for head in head_range:
        for p_total in power_range:
            best_flow, best_allocations = float('inf'), np.zeros(len(turbine_params))
            for num_on in range(1, len(turbine_params) + 1):
                for turbine_indices in combinations(range(len(turbine_params)), num_on):
                    max_power = sum(turbine_params[i]['p_max'] for i in turbine_indices)
                    min_power = sum(turbine_params[i]['p_min'] for i in turbine_indices)
                    if not (min_power <= p_total <= max_power): continue
                    flow, allocations = optimize_for_combination(p_total, head, num_on, turbine_indices, turbine_params)
                    if flow < best_flow: best_flow, best_allocations = flow, allocations
            if best_flow != float('inf'):
                efficiency = (p_total * 1e6) / (best_flow * RHO * G * head) if best_flow > 0 else 0
                row = {'target_power_mw': p_total, 'head_m': head, 'total_flow_m3s': best_flow, 'overall_efficiency': efficiency}
                for i in range(len(turbine_params)): row[f'turbine_{i+1}_power_mw'] = best_allocations[i]
                table_data.append(row)
    return pd.DataFrame(table_data)

def get_opening_for_flow(flow, head, params):
    if head <= 0 or flow <= 0: return 0.0
    denominator = params['discharge_coeff'] * params['width'] * np.sqrt(2 * G * head)
    if denominator < 1e-6: return float('inf')
    return min(flow / denominator, params['max_opening'])

def calculate_gate_openings(total_target_flow, head, params, rules):
    openings = np.zeros(params['num_gates'])
    flow_remaining = total_target_flow
    for indices in rules['sequence']:
        if flow_remaining <= 0: break
        required_opening = get_opening_for_flow(flow_remaining / len(indices), head, params)
        for idx in indices: openings[idx] = required_opening
        flow_from_group = (get_opening_for_flow(required_opening, head, params) * len(indices))
        flow_remaining -= get_flow_for_opening(required_opening, head, params) * len(indices)
        if required_opening < params['max_opening']: break
    return openings

def generate_gate_table_from_config(config):
    print(f"--- Generating Spillway Gate Flow Allocation Table ---")
    params = config['gate_params']
    rules = config['operational_rules']
    grid = config['calculation_grid']
    head_range = np.arange(grid['head_m']['start'], grid['head_m']['stop'], grid['head_m']['step'])
    flow_range = np.arange(grid['flow_m3s']['start'], grid['flow_m3s']['stop'], grid['flow_m3s']['step'])

    table_data = []
    for head in head_range:
        for target_flow in flow_range:
            if head <= 0: continue
            openings = calculate_gate_openings(target_flow, head, params, rules)
            row = {'target_flow_m3s': target_flow, 'head_m': head}
            for i in range(params['num_gates']): row[f'gate_{i+1}_opening_m'] = openings[i]
            table_data.append(row)
    return pd.DataFrame(table_data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>")
        sys.exit(1)

    config_file_path = sys.argv[1]
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Table Generation from Config: {os.path.basename(config_file_path)} ---")
    print(f"--- {config.get('description', '')} ---")

    comp_type = config.get("computation_type")

    if comp_type == "turbine_optimization":
        try:
            import scipy
        except ImportError:
            print("\nError: Turbine optimization requires the 'scipy' library.", file=sys.stderr)
            sys.exit(1)
        df = generate_turbine_table_from_config(config)
    elif comp_type == "gate_allocation":
        df = generate_gate_table_from_config(config)
    else:
        print(f"Error: Unknown computation_type '{comp_type}' in config.", file=sys.stderr)
        sys.exit(1)

    if df.empty:
        print("No valid operating points found. Table is empty.")
    else:
        output_path = config['output_settings']['csv_path']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nSuccessfully generated and saved table to: {output_path}")
        print("\nTable Preview:")
        print(df.head())
