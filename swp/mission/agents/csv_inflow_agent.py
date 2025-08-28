# -*- coding: utf-8 -*-

"""
An agent to provide data-driven inflow from a CSV file.
"""
import pandas as pd
from swp.core.interfaces import Agent, Simulatable

class CsvInflowAgent(Agent):
    """
    An agent that reads time-series data from a CSV file and directly sets
    the inflow on a target simulation component.
    """

    def __init__(self,
                 agent_id: str,
                 target_component: Simulatable,
                 csv_filepath: str,
                 time_col: str,
                 data_col: str):
        """
        Initializes the CsvInflowAgent.

        Args:
            agent_id: The unique ID for this agent.
            target_component: The simulation object to set the inflow on.
            csv_filepath: The path to the CSV file.
            time_col: The name of the column containing time data.
            data_col: The name of the column containing inflow data.
        """
        super().__init__(agent_id)
        self.target_component = target_component

        try:
            self.data = pd.read_csv(csv_filepath, index_col=time_col)
            self.data_col = data_col
            print(f"CsvInflowAgent '{agent_id}' initialized, loaded {len(self.data)} records from {csv_filepath}.")
        except FileNotFoundError:
            print(f"Error: CsvInflowAgent could not find file at {csv_filepath}")
            self.data = None

    def run(self, current_time: float):
        """
        Called at each simulation step. Looks up the inflow for the current
        time and sets it on the target component.
        """
        if self.data is None:
            self.target_component.inflow = 0
            return

        # Find the closest timestamp in the data using nearest-neighbor lookup
        pos = self.data.index.get_indexer([current_time], method='nearest')
        inflow_value = self.data.iloc[pos][self.data_col].values[0]

        # Directly set the inflow on the physical component
        self.target_component.inflow = inflow_value
