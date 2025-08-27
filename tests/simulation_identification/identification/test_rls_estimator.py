#-*- coding: utf-8 -*-
"""
Unit tests for the RLS Estimator module.
"""
import numpy as np
import pytest

from swp.simulation_identification.identification.rls_estimator import RLSEstimator

def test_rls_estimator_convergence():
    """
    Tests that the RLSEstimator correctly identifies the parameters of a
    simple linear system.
    """
    # 1. Define a known linear system: y = theta_true' * phi
    theta_true = np.array([2.5, -1.5, 0.5])
    num_params = len(theta_true)

    # 2. Instantiate the RLS estimator
    # Use a high forgetting factor for a stable system
    estimator = RLSEstimator(num_params=num_params, lambda_=0.98)

    # 3. Generate synthetic data and update the estimator
    num_samples = 500
    np.random.seed(42)

    for _ in range(num_samples):
        # Generate a random input vector phi
        phi = np.random.rand(num_params)

        # Calculate the true output and add some noise
        noise = np.random.randn() * 0.05 # small measurement noise
        y_true = np.dot(phi.T, theta_true)
        y_measured = y_true + noise

        # Update the estimator with the new data point
        estimator.update(phi, y_measured)

    # 4. Get the final estimated parameters
    theta_estimated = estimator.get_params()

    print(f"\nTrue parameters:      {theta_true}")
    print(f"Estimated parameters: {theta_estimated}")

    # 5. Assert that the estimated parameters are close to the true parameters
    # A tolerance (atol) of 0.1 should be sufficient given the noise and number of samples.
    assert np.allclose(theta_estimated, theta_true, atol=0.1)

def test_rls_estimator_value_error():
    """
    Tests that the RLSEstimator raises a ValueError for an invalid forgetting factor.
    """
    with pytest.raises(ValueError):
        RLSEstimator(num_params=2, lambda_=0.0) # lambda must be > 0

    with pytest.raises(ValueError):
        RLSEstimator(num_params=2, lambda_=1.1) # lambda must be <= 1
