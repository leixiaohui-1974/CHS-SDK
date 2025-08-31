import pandas as pd
import matplotlib.pyplot as plt
import imageio
import os

# --- Configuration ---
RESULTS_CSV_PATH = 'examples/watertank_refactored/02_parameter_identification/results.csv'
GIF_PATH = 'examples/watertank_refactored/02_parameter_identification/simulation_results.gif'
TEMP_FRAME_DIR = 'temp_frames_02'

# --- Load Data ---
try:
    df = pd.read_csv(RESULTS_CSV_PATH)
except FileNotFoundError as e:
    print(f"Error: {e}. Make sure the CSV file is in the correct directory.")
    exit()

# --- Prepare Environment ---
if not os.path.exists(TEMP_FRAME_DIR):
    os.makedirs(TEMP_FRAME_DIR)

# --- Generate Frames ---
frame_files = []
for i in range(1, len(df)): # Start from 1 to have a previous point for line plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f'Scenario 02: Parameter Identification (Time: {df["time"][i]:.1f}s)', fontsize=16)

    # 1. Water Levels
    ax1.plot(df['time'][:i+1], df['real_reservoir.water_level'][:i+1], label='Real Water Level', color='blue')
    ax1.plot(df['time'][:i+1], df['twin_reservoir.water_level'][:i+1], label='Twin Water Level', color='cyan', linestyle='--')
    ax1.set_ylabel('Water Level (m)')
    ax1.legend()
    ax1.grid(True)

    # 2. Valve Outflows
    ax2.plot(df['time'][:i+1], df['real_valve.outflow'][:i+1], label='Real Valve Outflow', color='red')
    ax2.plot(df['time'][:i+1], df['twin_valve.outflow'][:i+1], label='Twin Valve Outflow', color='magenta', linestyle='--')
    ax2.set_ylabel('Outflow (m³/s)')
    ax2.set_xlabel('Time (s)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save frame
    frame_file = os.path.join(TEMP_FRAME_DIR, f'frame_{i:04d}.png')
    plt.savefig(frame_file)
    plt.close()
    frame_files.append(frame_file)

# --- Create GIF ---
with imageio.get_writer(GIF_PATH, mode='I', duration=0.1) as writer:
    for frame_file in frame_files:
        image = imageio.imread(frame_file)
        writer.append_data(image)

# --- Cleanup ---
for frame_file in frame_files:
    os.remove(frame_file)
os.rmdir(TEMP_FRAME_DIR)

print(f"Successfully created GIF: {GIF_PATH}")
