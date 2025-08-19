import pytest
import numpy as np
import pandas as pd

from swp.data_processing.cleaner import fill_missing_with_interpolation
from swp.data_processing.evaluator import calculate_rmse, calculate_nse, calculate_kge

# --- Tests for cleaner.py ---

def test_fill_missing_middle():
    data = [10, 20, np.nan, 40, 50]
    expected = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    pd.testing.assert_series_equal(fill_missing_with_interpolation(data), expected)

def test_fill_missing_start_and_end():
    data = [np.nan, 20, 30, 40, np.nan]
    # limit_direction='both' should fill both ends
    expected = pd.Series([20.0, 20.0, 30.0, 40.0, 40.0])
    pd.testing.assert_series_equal(fill_missing_with_interpolation(data), expected)

def test_fill_no_missing():
    data = [10, 20, 30]
    expected = pd.Series([10.0, 20.0, 30.0])
    pd.testing.assert_series_equal(fill_missing_with_interpolation(data), expected)


# --- Tests for evaluator.py ---

@pytest.fixture
def sample_data():
    """Provides sample data for evaluation tests."""
    sim = np.array([5, 5, 5, 5, 5])
    obs = np.array([4, 5, 6, 4, 6])
    return sim, obs

def test_calculate_rmse(sample_data):
    sim, obs = sample_data
    # (sim-obs)^2 = [1, 0, 1, 1, 1] -> mean is 4/5 = 0.8 -> sqrt(0.8) = 0.8944
    assert calculate_rmse(sim, obs) == pytest.approx(np.sqrt(0.8))

def test_calculate_nse_perfect_match():
    sim = [1, 2, 3]
    obs = [1, 2, 3]
    assert calculate_nse(sim, obs) == pytest.approx(1.0)

def test_calculate_nse_as_good_as_mean(sample_data):
    sim, obs = sample_data
    # obs_mean = 5.0. sim is always 5.0. So model is the mean. NSE should be 0.
    sim_as_mean = np.full_like(obs, np.mean(obs))
    assert calculate_nse(sim_as_mean, obs) == pytest.approx(0.0)

def test_calculate_nse_worse_than_mean():
    sim = [100, 200, 300]
    obs = [1, 2, 3]
    assert calculate_nse(sim, obs) < 0

def test_calculate_kge_perfect_match():
    sim = [1, 2, 3, 4, 5]
    obs = [1, 2, 3, 4, 5]
    # r=1, beta=1, gamma=1 -> KGE = 1 - sqrt(0+0+0) = 1
    assert calculate_kge(sim, obs) == pytest.approx(1.0)

def test_calculate_kge_known_values():
    sim = np.array([0.8, 1.8, 2.8, 3.8, 4.8]) # Slightly lower bias
    obs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    r = np.corrcoef(sim, obs)[0, 1] # Should be 1.0
    beta = np.mean(sim) / np.mean(obs) # 2.8 / 3.0 = 0.9333
    gamma = np.std(sim) / np.std(obs) # Should be 1.0

    expected_kge = 1 - np.sqrt((r-1)**2 + (beta-1)**2 + (gamma-1)**2)
    assert calculate_kge(sim, obs) == pytest.approx(expected_kge)
