"""
This module contains functions for exporting simulation history data to various formats.
"""
import pandas as pd
import logging

def export_to_csv(history: list[dict], file_path: str):
    """
    Exports the simulation history to a CSV file.

    This function flattens the nested dictionary structure of the history
    and saves it in a standard tabular format.

    Args:
        history: The simulation history, a list of dictionaries.
        file_path: The path to save the output CSV file to.
    """
    if not history:
        logging.warning("History is empty, cannot export to CSV.")
        return

    # Flatten the data
    flattened_data = []
    for step in history:
        row = {}
        # The 'time' key is always at the top level
        row['time'] = step.get('time', 0)

        for key, value in step.items():
            if key == 'time':
                continue

            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    # Create a flattened column name like 'reservoir_1.water_level'
                    column_name = f"{key}.{sub_key}"
                    row[column_name] = sub_value
            else:
                # Handle top-level values if any (besides time)
                row[key] = value
        flattened_data.append(row)

    # Create a pandas DataFrame and save to CSV
    try:
        df = pd.DataFrame(flattened_data)

        # Reorder columns to have 'time' first, followed by sorted object/agent names
        cols = sorted([col for col in df.columns if col != 'time'])
        df = df[['time'] + cols]

        df.to_csv(file_path, index=False)
        logging.info(f"Successfully exported results to CSV: {file_path}")
    except Exception as e:
        logging.error(f"Failed to export to CSV: {e}")
