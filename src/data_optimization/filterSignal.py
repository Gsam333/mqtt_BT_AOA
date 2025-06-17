# 输出干扰过滤模型
def filterSignal(elevation,rssi,snr):
    MinAngle = 20
    # MinAngle = 299
    MinRSSI = -85 
    UnderElevation = 5   
    # UnderElevation = 60
    MinSNR = 3.0   
    
    if elevation > 90 - MinAngle:
        return True
    if rssi < MinRSSI:
        return True
    if (elevation > UnderElevation):
        if snr < MinSNR:
            return True
        else:
            if (elevation > UnderElevation):
                if snr < MinSNR:
                    return True
    return False