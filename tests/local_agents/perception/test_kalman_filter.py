#-*- coding: utf-8 -*-
"""
Unit tests for the Kalman Filter implementation.
"""
import numpy as np
import pytest

from swp.local_agents.perception.kalman_filter import KalmanFilter

def test_kalman_filter_constant_velocity():
    """
    Tests the KalmanFilter with a simple 1D constant velocity model.
    The filter should be able to track a moving object based on noisy position measurements.
    """
    # Time step
    dt = 1.0

    # Define the state-space model for a 1D constant velocity object
    # State x = [position, velocity]'
    # State transition matrix
    F = np.array([[1, dt],
                  [0, 1]])
    # No control input
    B = np.array([[0],
                  [0]])
    # Measurement matrix (we only measure position)
    H = np.array([[1, 0]])

    # Process noise covariance (some uncertainty in velocity)
    Q = np.array([[0.01, 0],
                  [0, 0.01]])
    # Measurement noise covariance (uncertainty of the sensor)
    R = np.array([[1.0]])

    # Initial state [position, velocity]
    x0 = np.array([[0],
                   [0]])
    # Initial estimate covariance
    P0 = np.eye(2) * 1.0

    # --- Create the Kalman Filter ---
    kf = KalmanFilter(F=F, B=B, H=H, Q=Q, R=R, x0=x0, P0=P0)

    # --- Generate synthetic data ---
    true_velocity = 0.5
    num_steps = 100
    true_states = []
    measurements = []

    # Generate true states and noisy measurements
    np.random.seed(42) # for reproducibility
    true_pos = 0
    for _ in range(num_steps):
        true_pos += true_velocity * dt
        true_states.append(true_pos)
        # Add noise to the measurement
        measurement = true_pos + np.random.randn() * np.sqrt(R[0,0])
        measurements.append(measurement)

    # --- Run the filter ---
    estimates = []
    for z in measurements:
        kf.predict()
        kf.update(np.array([[z]]))
        estimates.append(kf.x.copy())

    # --- Assertions ---
    # The final estimated position should be close to the true final position
    final_true_state = true_states[-1]
    final_estimate = estimates[-1][0, 0]

    # The final measurement will likely be far from the true state due to noise
    final_measurement = measurements[-1]

    # Key assertion: The filter's estimate should be better (closer) than the raw measurement
    assert abs(final_estimate - final_true_state) < abs(final_measurement - final_true_state)

    # The estimated velocity should be close to the true velocity
    final_estimated_velocity = estimates[-1][1, 0]
    assert abs(final_estimated_velocity - true_velocity) < 0.2

    print(f"\nTest Summary:")
    print(f"True final position: {final_true_state:.4f}")
    print(f"Final measurement:   {final_measurement:.4f} (Error: {abs(final_measurement - final_true_state):.4f})")
    print(f"Final estimate:      {final_estimate:.4f} (Error: {abs(final_estimate - final_true_state):.4f})")
    print(f"True velocity: {true_velocity:.4f}")
    print(f"Estimated velocity: {final_estimated_velocity:.4f}")

    assert abs(final_estimate - final_true_state) < 0.6 # Check if the final position error is reasonable
