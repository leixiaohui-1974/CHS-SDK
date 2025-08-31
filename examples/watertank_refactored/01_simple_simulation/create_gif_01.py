import pandas as pd
import matplotlib.pyplot as plt
import imageio
import os

# --- Configuration ---
RESULTS_CSV_PATH = 'examples/watertank_refactored/01_simple_simulation/results.csv'
GIF_PATH = 'examples/watertank_refactored/01_simple_simulation/simulation_results.gif'
TEMP_FRAME_DIR = 'temp_frames_01'

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
for i in range(len(df)):
    plt.figure(figsize=(10, 6))
    plt.plot(df['time'][:i+1], df['simple_tank.water_level'][:i+1], label='Water Level', color='blue')
    plt.title(f'Scenario 01: Simple Simulation (Time: {df["time"][i]:.1f}s)')
    plt.xlabel('Time (s)')
    plt.ylabel('Water Level (m)')
    plt.ylim(0, df['simple_tank.water_level'].max() * 1.2)
    plt.legend()
    plt.grid(True)

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
