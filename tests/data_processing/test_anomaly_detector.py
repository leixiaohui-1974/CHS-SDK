#-*- coding: utf-8 -*-
"""
Unit tests for the Anomaly Detector module.
"""
import numpy as np
import pandas as pd
import pytest

from swp.data_processing.anomaly_detector import IsolationForestAnomalyDetector

def test_isolation_forest_anomaly_detector():
    """
    Tests the IsolationForestAnomalyDetector wrapper to ensure it correctly
    identifies outliers in a synthetic dataset.
    """
    # 1. Create a synthetic dataset with obvious outliers
    np.random.seed(42)
    # Inliers clustered around (0, 0)
    inliers = np.random.randn(100, 2)
    # Outliers placed far away
    outliers = np.array([
        [10, 10],
        [-8, 8],
        [12, -12]
    ])

    data = np.vstack([inliers, outliers])
    df = pd.DataFrame(data, columns=['feature1', 'feature2'])

    # Known outlier indices
    num_inliers = len(inliers)
    num_outliers = len(outliers)
    known_outlier_indices = list(range(num_inliers, num_inliers + num_outliers))

    # 2. Instantiate the detector
    # Set contamination to the known proportion of outliers
    contamination = num_outliers / len(df)
    detector = IsolationForestAnomalyDetector(contamination=contamination, random_state=42)

    # 3. Run the fit_predict method
    predictions = detector.fit_predict(df)

    # 4. Assert the results
    assert isinstance(predictions, pd.Series)
    assert len(predictions) == len(df)

    # Check that the known outliers are flagged as -1
    predicted_outlier_indices = predictions[predictions == -1].index.tolist()

    # The Isolation Forest is stochastic, so it might not be perfect,
    # but it should catch most of the obvious outliers.
    # We will assert that at least 2 out of 3 are detected.

    detected_known_outliers = set(predicted_outlier_indices).intersection(set(known_outlier_indices))

    print(f"\nKnown outliers at indices: {known_outlier_indices}")
    print(f"Predicted outliers at indices: {predicted_outlier_indices}")
    print(f"Detected known outliers: {list(detected_known_outliers)}")

    # Assert that most of our obvious outliers were detected
    assert len(detected_known_outliers) >= 2

    # Assert that not too many inliers were misclassified
    # The number of predicted outliers should be close to the contamination level
    assert abs(len(predicted_outlier_indices) - num_outliers) <= 2
