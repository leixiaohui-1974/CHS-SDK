import unittest
import sys
import numpy as np
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.physical_objects.reservoir import Reservoir

class TestReservoir(unittest.TestCase):
    """
    Unit tests for the Reservoir physical component.
    """

    def setUp(self):
        """Set up a new reservoir for each test."""
        self.initial_volume = 1e6
        self.initial_level = 105.0

        # Define a simple, linear storage curve for testing
        # Format: [volume_m3, level_m]
        self.storage_curve = [
            [0, 100.0],
            [2e6, 110.0]  # A 10m change in level for 2e6 m^3 volume -> Area = 2e5 m^2
        ]

        self.initial_state = {'volume': self.initial_volume}
        self.parameters = {'storage_curve': self.storage_curve}

        self.reservoir = Reservoir(
            name="test_reservoir",
            initial_state=self.initial_state,
            parameters=self.parameters
        )
        # Manually set initial level based on the curve for consistent testing
        self.reservoir._state['water_level'] = self.reservoir._get_level_from_volume(self.initial_volume)
        self.initial_level = self.reservoir.get_state()['water_level']


    def test_initialization(self):
        """Test that the reservoir is initialized correctly."""
        state = self.reservoir.get_state()
        self.assertEqual(self.reservoir.name, "test_reservoir")
        self.assertAlmostEqual(state['volume'], self.initial_volume)
        self.assertAlmostEqual(state['water_level'], self.initial_level)

    def test_water_balance_positive_net_inflow(self):
        """Test the water balance equation with a net inflow."""
        dt = 60.0
        self.reservoir.set_inflow(2000.0)
        action = {'outflow': 500.0}

        delta_volume = (2000.0 - 500.0) * dt
        expected_new_volume = self.initial_volume + delta_volume
        expected_new_water_level = np.interp(expected_new_volume,
                                             np.array(self.storage_curve)[:, 0],
                                             np.array(self.storage_curve)[:, 1])

        new_state = self.reservoir.step(action, dt)

        self.assertAlmostEqual(new_state['volume'], expected_new_volume)
        self.assertAlmostEqual(new_state['water_level'], expected_new_water_level)

    def test_water_balance_negative_net_inflow(self):
        """Test the water balance equation with a net outflow."""
        dt = 100.0
        self.reservoir.set_inflow(200.0)
        action = {'outflow': 800.0}

        delta_volume = (200.0 - 800.0) * dt
        expected_new_volume = self.initial_volume + delta_volume
        expected_new_water_level = np.interp(expected_new_volume,
                                             np.array(self.storage_curve)[:, 0],
                                             np.array(self.storage_curve)[:, 1])

        new_state = self.reservoir.step(action, dt)

        self.assertAlmostEqual(new_state['volume'], expected_new_volume)
        self.assertAlmostEqual(new_state['water_level'], expected_new_water_level)

    def test_data_inflow_message(self):
        """Test that the reservoir correctly handles data-driven inflow via messages."""
        from core_lib.central_coordination.collaboration.message_bus import MessageBus
        bus = MessageBus()

        reservoir_with_bus = Reservoir(
            name="test_reservoir_with_bus",
            initial_state=self.initial_state,
            parameters=self.parameters,
            message_bus=bus,
            inflow_topic="inflow/test"
        )
        # Manually set initial level
        reservoir_with_bus._state['water_level'] = reservoir_with_bus._get_level_from_volume(self.initial_volume)

        bus.publish("inflow/test", {'inflow_rate': 300.0})

        dt = 10.0
        reservoir_with_bus.set_inflow(500.0)
        action = {'outflow': 400.0}

        delta_volume = (500.0 + 300.0 - 400.0) * dt
        expected_new_volume = self.initial_volume + delta_volume

        new_state = reservoir_with_bus.step(action, dt)
        self.assertAlmostEqual(new_state['volume'], expected_new_volume)

    def test_identify_parameters(self):
        """Test the parameter identification for the storage curve."""
        # 1. Define a "true" storage curve
        true_storage_curve = [
            [0, 100.0],
            [1e6, 105.0],
            [2e6, 110.0],
            [4e6, 120.0]
        ]
        true_reservoir = Reservoir("true_res", {'volume': 1e6}, {'storage_curve': true_storage_curve})
        true_reservoir._state['water_level'] = true_reservoir._get_level_from_volume(true_reservoir.get_state()['volume'])

        # 2. Generate synthetic data using the true model
        num_points = 100
        dt = 3600
        np.random.seed(0)
        # Make outflow higher than average inflow to drain the reservoir and test the lower part of the curve
        inflows = 150 + 100 * np.sin(np.linspace(0, 4 * np.pi, num_points)) # More dynamic inflow
        outflows = np.full_like(inflows, 200) # Constant high outflow

        observed_levels = np.zeros(num_points)
        current_volume = true_reservoir.get_state()['volume']

        for i in range(num_points):
            # Set the volume and re-calculate the level for a consistent state
            true_reservoir._state['volume'] = current_volume
            true_reservoir._state['water_level'] = true_reservoir._get_level_from_volume(current_volume)

            # Record the observed level
            observed_levels[i] = true_reservoir.get_state()['water_level']

            # Calculate volume for the *next* step
            delta_v = (inflows[i] - outflows[i]) * dt
            current_volume += delta_v

        # 3. Create a test reservoir with an incorrect initial curve
        initial_guess_curve = [
            [0, 98.0],    # Incorrect levels
            [1e6, 106.0],
            [2e6, 109.0],
            [4e6, 122.0]
        ]
        test_reservoir = Reservoir("test_res", {'volume': 1e6}, {'storage_curve': initial_guess_curve})

        # 4. Run parameter identification
        identification_data = {
            'inflows': inflows,
            'outflows': outflows,
            'levels': observed_levels
        }
        identified_params = test_reservoir.identify_parameters(identification_data)
        new_curve = np.array(identified_params['storage_curve'])
        true_curve = np.array(true_storage_curve)

        # 5. Check if the identified curve is closer to the true curve
        initial_error = np.sum((np.array(initial_guess_curve)[:, 1] - true_curve[:, 1])**2)
        final_error = np.sum((new_curve[:, 1] - true_curve[:, 1])**2)

        self.assertIsNotNone(new_curve)
        self.assertEqual(new_curve.shape, true_curve.shape)
        # The optimizer should significantly reduce the error
        self.assertLess(final_error, initial_error / 2)
        # Check that the identified levels are very close to the true levels
        np.testing.assert_allclose(new_curve[:, 1], true_curve[:, 1], rtol=1e-2) # 1% tolerance


if __name__ == '__main__':
    unittest.main()
