import numpy as np
from collections import deque

class AOAFilter:
    """
    蓝牙AOA数据异常值过滤器
    实现基于滑动窗口和Z-Score的异常值检测
    """
    def __init__(self, window_size=10, z_threshold=3):
        """
        初始化过滤器
        :param window_size: 滑动窗口大小
        :param z_threshold: Z-Score阈值
        """
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.angle_history = deque(maxlen=window_size)
        
    def filter_aoa(self, angle):
        """
        过滤AOA角度异常值
        :param angle: 输入角度值(度)
        :return: 过滤后的角度值或None(如果被判定为异常值)
        """
        if len(self.angle_history) >= self.window_size // 2:
            # 计算Z-Score
            angles = np.array(self.angle_history)
            mean = np.mean(angles)
            std = np.std(angles)
            z_score = abs((angle - mean) / std) if std != 0 else 0
            
            if z_score > self.z_threshold:
                return None  # 异常值
                
        self.angle_history.append(angle)
        return angle


def filter_aoa_data(angles, window_size=5, z_threshold=2.5):
    """
    批量过滤AOA数据
    :param angles: 角度值列表
    :param window_size: 滑动窗口大小
    :param z_threshold: Z-Score阈值
    :return: 过滤后的角度列表
    """
    aoa_filter = AOAFilter(window_size, z_threshold)
    filtered = []
    
    for angle in angles:
        result = aoa_filter.filter_aoa(angle)
        if result is not None:
            filtered.append(result)
            
    return filtered