#-*- coding: utf-8 -*-
"""
This module provides a standard implementation of a Kalman Filter.
"""
import numpy as np

class KalmanFilter:
    """
    A simple, linear Kalman Filter implementation.

    Assumes a linear state-space model:
    x_k = F * x_{k-1} + B * u_k + w_k  (State equation)
    z_k = H * x_k + v_k                (Measurement equation)

    where:
    w_k ~ N(0, Q) (process noise)
    v_k ~ N(0, R) (measurement noise)
    """

    def __init__(self, F, B, H, Q, R, x0, P0):
        """
        Initializes the Kalman Filter.

        Args:
            F (np.ndarray): State transition matrix.
            B (np.ndarray): Control input matrix.
            H (np.ndarray): Measurement matrix.
            Q (np.ndarray): Process noise covariance matrix.
            R (np.ndarray): Measurement noise covariance matrix.
            x0 (np.ndarray): Initial state estimate.
            P0 (np.ndarray): Initial estimate covariance matrix.
        """
        self.F = F  # State transition matrix
        self.B = B  # Control input matrix
        self.H = H  # Measurement matrix
        self.Q = Q  # Process noise covariance
        self.R = R  # Measurement noise covariance

        self.x = x0  # Initial state estimate
        self.P = P0  # Initial estimate covariance

        self.n = F.shape[1]  # Number of state variables
        self.I = np.eye(self.n) # Identity matrix

    def predict(self, u=0):
        """
        Performs the prediction step.

        Args:
            u (np.ndarray, optional): Control vector. Defaults to 0.
        """
        # Project the state ahead
        self.x = np.dot(self.F, self.x) + np.dot(self.B, u)
        # Project the error covariance ahead
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        return self.x

    def update(self, z):
        """
        Performs the update step (correction).

        Args:
            z (np.ndarray): The measurement vector.
        """
        # Compute the Kalman Gain
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # Update estimate with measurement z
        y = z - np.dot(self.H, self.x)  # Measurement residual
        self.x = self.x + np.dot(K, y)

        # Update the error covariance
        self.P = np.dot(self.I - np.dot(K, self.H), self.P)

        return self.x
