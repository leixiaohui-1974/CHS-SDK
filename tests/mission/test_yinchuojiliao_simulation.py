# -*- coding: utf-8 -*-

"""
Test for the main Yin Chuo Ji Liao project simulation script.
"""

import os
from swp.mission.yinchuojiliao_main import run_simulation

def test_run_yinchuojiliao_simulation():
    """
    Tests that the main simulation script runs to completion without errors
    and produces the expected output file.
    """
    # Define the expected output filename
    output_filename = "yinchuojiliao_simulation_results.png"

    # Clean up any previous run's output file
    if os.path.exists(output_filename):
        os.remove(output_filename)

    # Run the full simulation
    try:
        run_simulation()
        simulation_success = True
    except Exception as e:
        simulation_success = False
        print(f"Simulation run failed with an exception: {e}")

    # Assert that the simulation ran without raising an exception
    assert simulation_success, "The simulation script raised an exception."

    # Assert that the output plot was created
    assert os.path.exists(output_filename), f"The output plot '{output_filename}' was not created."

    # Clean up the created file after the test
    if os.path.exists(output_filename):
        os.remove(output_filename)
