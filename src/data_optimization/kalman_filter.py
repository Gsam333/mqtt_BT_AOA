# 卡尔曼滤波
class KalmanFilter:
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.prediction = None
        self.error_estimate = 1.0

    def update(self, measurement):
        if self.prediction is None:
            self.prediction = measurement
        else:
            self.error_estimate += self.process_noise

        kalman_gain = self.error_estimate / (self.error_estimate + self.measurement_noise)
        self.prediction += kalman_gain * (measurement - self.prediction)
        self.error_estimate *= (1 - kalman_gain)
        return self.prediction

kalman_states = {}

def kalman_filter(value, macid=None, is_coordinate=False, **kwargs):
    global kalman_states
    key_x = f"{macid}_coord_x"
    key_y = f"{macid}_coord_y"
    
    if is_coordinate:
        x, y = value
        # 初始化X/Y轴滤波器
        for key in [key_x, key_y]:
            if key not in kalman_states:
                kalman_states[key] = KalmanFilter(**kwargs)
        return (kalman_states[key_x].update(x), kalman_states[key_y].update(y))
    else:
        if macid not in kalman_states:
            kalman_states[macid] = KalmanFilter(**kwargs)
        return kalman_states[macid].update(value)