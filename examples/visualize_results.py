import json
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def visualize(output_dir: str):
    """
    Generates plots from a standardized simulation output directory.
    """
    print(f"--- Generating visualizations for output in: {output_dir} ---")

    history_path = os.path.join(output_dir, 'history.csv')
    plot_config_path = os.path.join(output_dir, 'plots.json')

    if not os.path.exists(history_path):
        print(f"Error: `history.csv` not found in {output_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(plot_config_path):
        print(f"Error: `plots.json` not found in {output_dir}", file=sys.stderr)
        sys.exit(1)

    history_df = pd.read_csv(history_path)
    with open(plot_config_path, 'r') as f:
        plot_config = json.load(f)

    # --- Create Figure and Subplots ---
    num_subplots = len(plot_config.get('subplots', []))
    fig_config = plot_config.get('figure', {})
    fig, axes = plt.subplots(
        num_subplots, 1,
        figsize=fig_config.get('figsize', [12, 5 * num_subplots]),
        sharex=True
    )
    if num_subplots == 1: axes = [axes] # Ensure axes is always a list
    fig.suptitle(fig_config.get('title', 'Simulation Results'), fontsize=16)

    # --- Populate each subplot ---
    for i, subplot_config in enumerate(plot_config.get('subplots', [])):
        ax = axes[i]
        ax.set_title(subplot_config.get('title', ''))
        ax.set_ylabel(subplot_config.get('y_label', ''))
        if subplot_config.get('grid', False):
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Plot main series
        for series_config in subplot_config.get('series', []):
            ax.plot(
                history_df['time'],
                history_df[series_config['y_key']],
                label=series_config.get('label', series_config['y_key'])
            )

        # Add annotations (hlines, vlines, etc.)
        for anno_config in subplot_config.get('annotations', []):
            if anno_config['type'] == 'hline':
                ax.axhline(
                    y=anno_config['y'],
                    color=anno_config.get('color', 'r'),
                    linestyle=anno_config.get('linestyle', '--'),
                    label=anno_config.get('label', '')
                )

        if ax.get_legend_handles_labels()[1]: # Check if there are any labels
            ax.legend()

    # --- Final Touches ---
    # Set shared x-axis label on the last subplot
    axes[-1].set_xlabel(plot_config.get('subplots', [{}])[-1].get('x_label', 'Time (steps)'))

    # Format x-axis if time is in hours/days for better readability
    if history_df['time'].max() > 3600 * 2: # More than 2 hours
        axes[-1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/3600:.1f}h'))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the final plot
    plot_file = os.path.join(output_dir, fig_config.get('filename', 'results.png'))
    plt.savefig(plot_file)
    print(f"Plot saved to {plot_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_output_directory>", file=sys.stderr)
        sys.exit(1)
    visualize(sys.argv[1])
