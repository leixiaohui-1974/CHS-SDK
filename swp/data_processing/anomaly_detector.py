#-*- coding: utf-8 -*-
"""
This module provides wrappers for anomaly detection algorithms.
"""
import pandas as pd
from sklearn.ensemble import IsolationForest

class IsolationForestAnomalyDetector:
    """
    A wrapper for the scikit-learn IsolationForest model to provide a consistent
    interface for anomaly detection within the SWP project.
    """

    def __init__(self, n_estimators=100, contamination='auto', random_state=42):
        """
        Initializes the anomaly detector.

        Args:
            n_estimators (int): The number of base estimators in the ensemble.
            contamination (float or 'auto'): The amount of contamination of the data set, i.e.,
                the proportion of outliers in the data set.
            random_state (int): Controls the pseudo-randomness of the selection of the feature
                and split values for each branching decision.
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1  # Use all available processors
        )

    def fit_predict(self, data: pd.DataFrame) -> pd.Series:
        """
        Fits the model to the data and predicts the labels (1 for inliers, -1 for outliers).

        Args:
            data (pd.DataFrame): The input data to fit the model to and predict.
                The data should be a DataFrame where each column is a feature.

        Returns:
            pd.Series: A series containing the predictions, where 1 indicates an inlier
                       and -1 indicates an outlier. The series index will match the input data.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if data.empty:
            return pd.Series(dtype=int)

        predictions = self.model.fit_predict(data)
        return pd.Series(predictions, index=data.index)
