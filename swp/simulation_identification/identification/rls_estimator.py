#-*- coding: utf-8 -*-
"""
This module provides an implementation of the Recursive Least Squares (RLS) estimator
for online parameter identification.
"""
import numpy as np

class RLSEstimator:
    """
    A Recursive Least Squares (RLS) estimator for online parameter identification
    of a linear model y = phi' * theta.
    """

    def __init__(self, num_params, lambda_=0.99, P0=1000):
        """
        Initializes the RLS estimator.

        Args:
            num_params (int): The number of parameters to estimate (dimension of theta).
            lambda_ (float, optional): The forgetting factor (0 < lambda <= 1).
                Defaults to 0.99.
            P0 (float, optional): The initial value for the diagonal elements of the
                inverse correlation matrix P. A large value expresses low confidence
                in the initial parameter estimates. Defaults to 1000.
        """
        if not (0 < lambda_ <= 1):
            raise ValueError("Forgetting factor lambda must be between 0 and 1.")

        self.num_params = num_params
        self.lambda_ = lambda_

        # Initialize the parameter estimate vector theta to zeros
        self.theta = np.zeros((num_params, 1))

        # Initialize the inverse correlation matrix P
        self.P = np.eye(num_params) * P0

    def update(self, phi, y):
        """
        Updates the parameter estimates with a new data point.

        Args:
            phi (np.ndarray): The input vector (regressor vector) of shape (num_params, 1).
            y (float): The measured output scalar.
        """
        phi = phi.reshape(self.num_params, 1) # Ensure phi is a column vector

        # 1. Calculate the Kalman gain vector k
        k_numerator = np.dot(self.P, phi)
        k_denominator = self.lambda_ + np.dot(phi.T, k_numerator)
        k = k_numerator / k_denominator

        # 2. Calculate the a priori estimation error
        y_hat = np.dot(phi.T, self.theta)
        alpha = y - y_hat

        # 3. Update the parameter estimate vector theta
        self.theta = self.theta + k * alpha

        # 4. Update the inverse correlation matrix P
        P_numerator = np.dot(np.eye(self.num_params) - np.dot(k, phi.T), self.P)
        self.P = P_numerator / self.lambda_

    def get_params(self):
        """
        Returns the current parameter estimates.

        Returns:
            np.ndarray: The current parameter estimate vector theta.
        """
        return self.theta.flatten()
