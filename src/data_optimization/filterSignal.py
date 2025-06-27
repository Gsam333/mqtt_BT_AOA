# 输出干扰过滤模型
def filterSignal(elevation, rssi, snr, MinAngle=20, MinRSSI=-85, UnderElevation=5, MinSNR=3.0):
    """
    根据给定的参数过滤信号
    参数:
        elevation: 仰角
        rssi: 信号强度
        snr: 信噪比
        MinAngle: 最小角度阈值 (默认20)
        MinRSSI: 最小RSSI阈值 (默认-85)
        UnderElevation: 仰角下限阈值 (默认5)
        MinSNR: 最小SNR阈值 (默认3.0)
        
    返回:
        True: 数据应被丢弃
        False: 数据有效
    """
    if elevation > 90 - MinAngle:
        return True
    if rssi < MinRSSI:
        return True
    if elevation > UnderElevation and snr < MinSNR:
        return True
    return False


# def filterSignal(elevation,rssi,snr):
#     MinAngle = 20
#     MinRSSI = -85 
#     UnderElevation = 5   
#     MinSNR = 3.0   
    
#     if elevation > 90 - MinAngle:
#         return True
#     if rssi < MinRSSI:
#         return True
#     if (elevation > UnderElevation):
#         if snr < MinSNR:
#             return True
#         else:
#             if (elevation > UnderElevation):
#                 if snr < MinSNR:
#                     return True
#     return False