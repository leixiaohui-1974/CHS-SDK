import json
import os
import sys
import numpy as np
import pandas as pd
from itertools import combinations

# --- Add project root to Python path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Constants ---
RHO = 1000  # Water density
G = 9.81    # Gravity

# --- Turbine Optimization Logic ---
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
    return sum(power_to_flow(p, head_m, get_turbine_efficiency(p, head_m, tp)) for p, tp in zip(power_allocations, turbine_params))

def optimize_for_combination(target_power, head, num_active, turbine_indices, all_params, minimize_func):
    active_params = [all_params[i] for i in turbine_indices]
    constraints = ({'type': 'eq', 'fun': lambda p: np.sum(p) - target_power})
    bounds = [(p['p_min'], p['p_max']) for p in active_params]
    initial_guess = [target_power / num_active] * num_active
    result = minimize_func(objective_function, initial_guess, args=(head, active_params), method='SLSQP', bounds=bounds, constraints=constraints)
    if result.success:
        final_allocations = np.zeros(len(all_params))
        for i, idx in enumerate(turbine_indices): final_allocations[idx] = result.x[i]
        return result.fun, final_allocations
    return float('inf'), np.zeros(len(all_params))

def generate_turbine_table(config, minimize_func):
    turbine_params = config['turbine_params']
    grid = config['calculation_grid']
    head_range = np.arange(grid['head_m']['start'], grid['head_m']['stop'], grid['head_m']['step'])
    power_range = np.arange(grid['power_mw']['start'], grid['power_mw']['stop'], grid['power_mw']['step'])
    table_data = []
    for head in head_range:
        for p_total in power_range:
            best_flow, best_allocations = float('inf'), np.zeros(len(turbine_params))
            for num_on in range(1, len(turbine_params) + 1):
                for inds in combinations(range(len(turbine_params)), num_on):
                    if not (sum(turbine_params[i]['p_min'] for i in inds) <= p_total <= sum(turbine_params[i]['p_max'] for i in inds)): continue
                    flow, allocs = optimize_for_combination(p_total, head, num_on, inds, turbine_params, minimize_func)
                    if flow < best_flow: best_flow, best_allocations = flow, allocs
            if best_flow != float('inf'):
                eff = (p_total * 1e6) / (best_flow * RHO * G * head) if best_flow > 0 else 0
                row = {'target_power_mw': p_total, 'head_m': head, 'total_flow_m3s': best_flow, 'overall_efficiency': eff}
                for i in range(len(turbine_params)): row[f'turbine_{i+1}_power_mw'] = best_allocations[i]
                table_data.append(row)
    return pd.DataFrame(table_data)

# --- Gate Allocation Logic ---
def get_opening_for_flow(flow, head, params):
    if head <= 0 or flow <= 0: return 0.0
    denom = params['discharge_coeff'] * params['width'] * np.sqrt(2 * G * head)
    return min(flow / denom, params['max_opening']) if denom > 1e-6 else float('inf')

def get_flow_for_opening(opening, head, params):
    if head <= 0 or opening <= 0: return 0.0
    return params['discharge_coeff'] * (params['width'] * opening) * np.sqrt(2 * G * head)

def calculate_gate_openings(total_flow, head, params, rules):
    openings, flow_rem = np.zeros(params['num_gates']), total_flow
    for inds in rules['sequence']:
        if flow_rem <= 0: break
        req_opening = get_opening_for_flow(flow_rem / len(inds), head, params)
        for idx in inds: openings[idx] = req_opening
        flow_rem -= get_flow_for_opening(req_opening, head, params) * len(inds)
        if req_opening < params['max_opening']: break
    return openings

def generate_gate_table(config):
    params, rules, grid = config['gate_params'], config['operational_rules'], config['calculation_grid']
    head_range = np.arange(grid['head_m']['start'], grid['head_m']['stop'], grid['head_m']['step'])
    flow_range = np.arange(grid['flow_m3s']['start'], grid['flow_m3s']['stop'], grid['flow_m3s']['step'])
    table_data = []
    for head in head_range:
        for flow in flow_range:
            if head <= 0: continue
            openings = calculate_gate_openings(flow, head, params, rules)
            row = {'target_flow_m3s': flow, 'head_m': head}
            for i in range(params['num_gates']): row[f'gate_{i+1}_opening_m'] = openings[i]
            table_data.append(row)
    return pd.DataFrame(table_data)

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>", file=sys.stderr)
        sys.exit(1)

    config_file_path = sys.argv[1]
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Table Generation from Config: {os.path.basename(config_file_path)} ---")

    comp_type = config.get("computation_type")
    df = None

    if comp_type == "turbine_optimization":
        try:
            from scipy.optimize import minimize
            df = generate_turbine_table(config, minimize)
        except ImportError:
            print("\nError: Turbine optimization requires the 'scipy' library.", file=sys.stderr)
            sys.exit(1)
    elif comp_type == "gate_allocation":
        df = generate_gate_table(config)
    else:
        print(f"Error: Unknown computation_type '{comp_type}' in config.", file=sys.stderr)
        sys.exit(1)

    if df is not None and not df.empty:
        output_path = config['output_settings']['csv_path']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nSuccessfully generated and saved table to: {output_path}")
        print("\nTable Preview:")
        print(df.head())
    else:
        print("No data generated for the table.")
