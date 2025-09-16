# -*- coding: utf-8 -*-
"""
本模块提供了用于在线参数辨识的递归最小二乘（RLS）估计算法的实现。
使用数值稳定的Joseph形式更新以避免协方差矩阵的数值问题。
"""
import numpy as np
from typing import Union, Tuple
import logging

logger = logging.getLogger(__name__)


class RLSEstimator:
    """
    一个用于在线辨识线性模型 y = phi' * theta 的递归最小二乘（RLS）估计算法。
    
    使用Joseph形式的协方差更新以确保数值稳定性。
    """

    def __init__(self, num_params: int, lambda_: float = 0.99, P0: float = 1000.0):
        """
        初始化RLS估计算法。

        参数:
            num_params: 要估计的参数数量（theta的维度）。
            lambda_: 遗忘因子 (0 < lambda <= 1)。默认为0.99。
            P0: 逆相关矩阵P对角线元素的初始值。
                一个较大的值表示对初始参数估计的置信度较低。默认为1000.0。
        """
        if not isinstance(num_params, int) or num_params <= 0:
            raise ValueError("参数数量num_params必须是正整数。")
        
        if not (0 < lambda_ <= 1):
            raise ValueError("遗忘因子lambda必须在0和1之间。")
        
        if P0 <= 0:
            raise ValueError("初始协方差P0必须为正数。")

        self.num_params = num_params
        self.lambda_ = lambda_
        
        # 初始化参数估计向量theta为零
        self.theta = np.zeros((num_params, 1))
        
        # 初始化逆相关矩阵P
        self.P = np.eye(num_params) * P0
        
        # 统计信息
        self.update_count = 0
        self.last_error = 0.0
        
        logger.info(f"RLS估计器初始化完成: num_params={num_params}, lambda={lambda_}, P0={P0}")

    def update(self, phi: Union[np.ndarray, list], y: float) -> Tuple[float, float]:
        """
        使用一个新的数据点更新参数估计。

        参数:
            phi: 输入向量（回归量向量），形状为 (num_params,) 或 (num_params, 1)。
            y: 测量的输出标量。
            
        返回:
            Tuple[float, float]: (预测误差, 增益范数)
        """
        # 输入验证
        phi = np.asarray(phi, dtype=float)
        if phi.size != self.num_params:
            raise ValueError(f"输入向量phi的维度({phi.size})与参数数量({self.num_params})不匹配。")
        
        phi = phi.reshape(self.num_params, 1)  # 确保phi是列向量
        y = float(y)
        
        try:
            # 1. 计算预测值和误差
            y_hat = np.dot(phi.T, self.theta)[0, 0]
            alpha = y - y_hat
            self.last_error = alpha
            
            # 2. 计算中间变量
            P_phi = np.dot(self.P, phi)
            phi_T_P_phi = np.dot(phi.T, P_phi)[0, 0]
            
            # 3. 计算卡尔曼增益向量k（数值稳定版本）
            denominator = self.lambda_ + phi_T_P_phi
            if abs(denominator) < 1e-12:
                logger.warning("RLS更新中分母接近零，跳过此次更新")
                return alpha, 0.0
            
            k = P_phi / denominator
            gain_norm = np.linalg.norm(k)
            
            # 4. 更新参数估计向量theta
            self.theta = self.theta + k * alpha
            
            # 5. 使用Joseph形式更新协方差矩阵P（数值稳定）
            # P = (I - k*phi^T) * P * (I - k*phi^T)^T / lambda + k*k^T*R/lambda
            # 简化版本（假设测量噪声方差R=1）：
            I_k_phi = np.eye(self.num_params) - np.dot(k, phi.T)
            self.P = (np.dot(I_k_phi, np.dot(self.P, I_k_phi.T)) + 
                     np.dot(k, k.T)) / self.lambda_
            
            # 确保P矩阵的对称性和正定性
            self.P = (self.P + self.P.T) / 2
            
            # 检查协方差矩阵的条件数
            cond_number = np.linalg.cond(self.P)
            if cond_number > 1e12:
                logger.warning(f"协方差矩阵条件数过大: {cond_number:.2e}")
            
            self.update_count += 1
            
            if self.update_count % 100 == 0:
                logger.debug(f"RLS更新 #{self.update_count}: 误差={alpha:.6f}, 增益范数={gain_norm:.6f}")
            
            return alpha, gain_norm
            
        except np.linalg.LinAlgError as e:
            logger.error(f"RLS更新中的线性代数错误: {e}")
            return alpha, 0.0
        except Exception as e:
            logger.error(f"RLS更新中的未知错误: {e}")
            return 0.0, 0.0

    def get_params(self) -> np.ndarray:
        """
        返回当前的参数估计。

        返回:
            np.ndarray: 当前的参数估计向量theta（一维数组）。
        """
        return self.theta.flatten()
    
    def get_covariance(self) -> np.ndarray:
        """
        返回当前的参数协方差矩阵。

        返回:
            np.ndarray: 参数协方差矩阵P。
        """
        return self.P.copy()
    
    def get_parameter_std(self) -> np.ndarray:
        """
        返回参数估计的标准差。

        返回:
            np.ndarray: 参数标准差向量。
        """
        return np.sqrt(np.diag(self.P))
    
    def reset(self, P0: float = None):
        """
        重置估计器状态。

        参数:
            P0: 新的初始协方差值，如果为None则使用原值。
        """
        if P0 is not None:
            if P0 <= 0:
                raise ValueError("初始协方差P0必须为正数。")
            self.P = np.eye(self.num_params) * P0
        else:
            self.P = np.eye(self.num_params) * 1000.0
            
        self.theta = np.zeros((self.num_params, 1))
        self.update_count = 0
        self.last_error = 0.0
        
        logger.info("RLS估计器已重置")
    
    def get_stats(self) -> dict:
        """
        获取估计器统计信息。

        返回:
            dict: 包含统计信息的字典。
        """
        return {
            'update_count': self.update_count,
            'last_error': self.last_error,
            'parameter_count': self.num_params,
            'forgetting_factor': self.lambda_,
            'covariance_condition_number': np.linalg.cond(self.P),
            'parameter_std': self.get_parameter_std().tolist()
        }
