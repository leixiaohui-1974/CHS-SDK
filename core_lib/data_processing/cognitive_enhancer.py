#-*- coding: utf-8 -*-
"""
一个可重用的模块，为感知智能体提供认知能力。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

from core_lib.data_processing.anomaly_detector import IsolationForestAnomalyDetector
from core_lib.data_processing.cleaner import fill_missing_with_interpolation

class CognitiveEnhancer:
    """
    一个可重用的模块，为感知智能体提供认知能力。

    该类管理观测历史，并用它来执行：
    1. 数据清洗（对缺失值进行插值）
    2. 异常诊断（使用孤立森林）
    3. 预测性预警（基于简单的趋势分析）
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 CognitiveEnhancer。

        Args:
            config: 配置字典。预期键：
                - 'history_size': (int) 要保留的最大时间步数。
                - 'target_variables': (List[str]) 要监控的状态变量。
                - 'anomaly_detection': (Optional[Dict]) 异常检测的配置。
                    - 'contamination': (float) 预期的异常比例。
                - 'predictive_warning': (Optional[Dict]) 预警的配置。
                    - 'trend_window': (int) 用于趋势分析的回溯步数。
                    - 'thresholds': (Dict[str, float]) 各变量触发预警的阈值。
        """
        self.config = config
        self.history_size = config.get('history_size', 50)
        self.target_variables = config.get('target_variables', [])

        # 使用DataFrame存储历史记录，以时间为索引
        self.history = pd.DataFrame(columns=['time'] + self.target_variables).set_index('time')

        # 如果配置了异常检测器，则初始化
        self.anomaly_detector = None
        if 'anomaly_detection' in self.config and self.config['anomaly_detection']:
            self.anomaly_detector = IsolationForestAnomalyDetector(
                contamination=self.config['anomaly_detection'].get('contamination', 'auto')
            )
            print("CognitiveEnhancer: 已启用异常检测。")

        print(f"CognitiveEnhancer 已为变量初始化: {self.target_variables}")

    def enhance(self, state: Dict[str, Any], time: float) -> Dict[str, Any]:
        """
        处理当前状态以生成认知增强功能。

        Args:
            state: 来自仿真模型的当前原始状态。
            time: 当前仿真时间。

        Returns:
            一个包含增强结果（如'is_anomaly'和'warning_message'）的字典。
        """
        # 1. 用新状态更新历史记录
        current_data = {var: state.get(var) for var in self.target_variables}
        new_row = pd.DataFrame(current_data, index=[time])

        self.history = pd.concat([self.history, new_row])

        # 2. 数据清洗
        # 注意：此处清洗的是整个历史记录，以处理传入的NaN
        self._clean_history()

        # 裁剪历史记录以保持大小
        if len(self.history) > self.history_size:
            self.history = self.history.iloc[-self.history_size:]

        # 准备结果
        enhancements = {
            'is_anomaly': False,
            'warning_message': None
        }

        # 3. 异常诊断
        if self.anomaly_detector:
            enhancements['is_anomaly'] = self._detect_anomaly()

        # 4. 预测性预警
        if 'predictive_warning' in self.config and self.config['predictive_warning']:
            enhancements['warning_message'] = self._check_for_warnings()

        return enhancements

    def _clean_history(self):
        """
        检查并填充历史记录中的缺失值。
        """
        for var in self.target_variables:
            # fill_missing_with_interpolation 预期接收一个Series
            series_with_missing_values = self.history[var]
            cleaned_series = fill_missing_with_interpolation(series_with_missing_values)
            self.history[var] = cleaned_series

    def _detect_anomaly(self) -> bool:
        """
        对历史数据运行异常检测。
        如果*当前*点是异常，则返回True。
        """
        if len(self.history) < 2: # 数据不足以检测异常
            return False

        # 异常检测器预期接收一个特征的DataFrame
        features = self.history[self.target_variables].dropna()
        if len(features) < 2:
            return False

        predictions = self.anomaly_detector.fit_predict(features)

        # 返回最后一个点的预测结果（-1表示异常）
        return predictions.iloc[-1] == -1

    def _check_for_warnings(self) -> Optional[str]:
        """
        执行简单的趋势分析以生成预警。
        """
        warning_config = self.config.get('predictive_warning', {})
        window = warning_config.get('trend_window', 3)

        if len(self.history) < window:
            return None

        # 检查每个目标变量的预警
        for var in self.target_variables:
            threshold = warning_config.get('thresholds', {}).get(var)
            if threshold is None:
                continue

            recent_data = self.history[var].iloc[-window:]
            # Ensure we have enough non-null points to calculate a trend
            if recent_data.isnull().any():
                continue

            change = recent_data.iloc[-1] - recent_data.iloc[0]

            # 检查负阈值（下降）
            if threshold < 0 and change < threshold:
                return f"预测性预警: {var} 在过去 {window} 个步骤中下降了 {change:.2f}，超过了阈值 {threshold}。"
            # 也可以在这里添加对正阈值（飙升）的检查

        return None
