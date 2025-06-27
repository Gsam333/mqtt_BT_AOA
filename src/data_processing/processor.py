from src.data_optimization.coordinate_mapping import coordinate_mapping, calculate_distance
from src.data_optimization.low_pass_filter import low_pass_filter
from src.data_optimization.kalman_filter import kalman_filter
from src.data_optimization.aoa_filter import AOAFilter
from src.data_optimization.filterSignal import filterSignal
import time

# 新增全局计数器
_missing_count = 0
_MAX_MISSING = 10

def get_heartbeat_status(payload):
    global _missing_count
    
    if payload and payload.startswith('AoA_usps hb='):
        _missing_count = 0  # 收到心跳包重置计数器
        print(f"❤️ 心跳包已接收 | 内容: {payload[:20]}")
        return True
    elif not payload: # 收到空payload,无法触发on_message回调函数
        _missing_count += 1
        print("⚠️ 收到空payload,心跳包丢失计数增加")
        return False

def getAoAmqtt(payload):
    """
    解析 AOA 数据并返回位置信息。

    参数:
    payload (str): 包含 AOA 数据的字符串。

    返回:
    dict: 包含以下键值对的字典：
        - macid: MAC地址
        - customdata: 用户数据
        - rssi: 信号强度 (dBm)
        - snr: 信噪比 (dB)
        - azimuth: 方位角 (°)
        - elevation: 倾角 (°)

    如果解析失败，则返回 None。
    """
    MAXPAYLOADLEN = 82  # 定义payload最大长度
    MINSNR = 3.0        # 信噪比阈值
    MINRSSI = -85       # 信号强度阈值
    MINANGLE = 20       # 仰角过滤阈值
    
    # if check_heartbeat(payload):
    #     global _last_hb_time
    #     _last_hb_time = time.time()
    #     print(f"❤️ 心跳包已接收 | 内容: {payload[:20]}")
    #     return None
    if get_heartbeat_status(payload):
        # print('missing_count', _missing_count)
        return None
    
    if not payload.startswith('AOA='):
        return None

    try:
        strstart = 16 # 数据起始位置
        payload = payload.strip() # 去除payload首尾空白字符
        payloadlen = len(payload) # 计算payload总长度
        
        # 验证 payload 长度
        if payloadlen != MAXPAYLOADLEN:
            raise ValueError("无效的 payload 长度")
            
        # if not payload.startswith('AOA='):
        #     raise ValueError("无效的 AOA 前缀")

        customdatalen = 36 + 14  
        
        # MAC地址提取（逆序拼接）
        macid = (
            payload[strstart - 2:strstart] +       # 第14-16字符
            payload[strstart - 4:strstart - 2] +   # 第12-14字符
            payload[strstart - 6:strstart - 4] +   # 第10-12字符
            payload[strstart - 8:strstart - 6] +    # 第8-10字符
            payload[strstart - 10:strstart - 8] +   # 第6-8字符
            payload[strstart - 12:strstart - 10]   # 第4-6字符
        )
        customdata = payload[strstart:strstart+customdatalen]  
        
        # RSSI计算（补码转换）
        rssi = (int(
            payload[strstart + customdatalen + 2:strstart + customdatalen + 4] +
            payload[strstart + customdatalen:strstart + customdatalen + 2], 
            16
        ) - 256) * 0.5
        
        # SNR计算（信噪比）
        snr = int(
            payload[strstart + customdatalen + 6:strstart + customdatalen + 8] +
            payload[strstart + customdatalen + 4:strstart + customdatalen + 6], 
            16
        ) / 10
        
        # 方位角计算（补正方向）
        azimuth = int(
            payload[strstart + customdatalen + 10:strstart + customdatalen + 12] +
            payload[strstart + customdatalen + 8:strstart + customdatalen + 10], 
            16
        ) * 0.5
        # 仰角计算（转换为垂直参考）
        elevation = int(
            payload[strstart + customdatalen + 14:strstart + customdatalen + 16] +
            payload[strstart + customdatalen + 12:strstart + customdatalen + 14], 
            16
        ) * 0.5
        
        if azimuth != 0:
            azimuth = 360 - azimuth  # 补正为顺时针角度
        elevation = 90 - elevation   # 转换为垂直方向
        # 过滤干扰数据,MinSNR: 最小SNR阈值 (默认3.0)
        if filterSignal(elevation, rssi, snr, MinSNR = 2.0):
            print(f"警告：数据被过滤 - elevation:{elevation} rssi:{rssi} snr:{snr}")
            return None
    
        x, y = coordinate_mapping(azimuth, elevation)                     # 极坐标系映射为笛卡尔坐标系
        FX, FY = low_pass_filter(x, y)                                    # 低通滤波       
        distance = calculate_distance(FX, FY)                               # 计算距离，输入参数为低通滤波运算后坐标
        # distance = calculate_distance(x, y)                               # 计算距离，输入参数为原始坐标
        # if azimuth != 0:
        KX, KY = kalman_filter((x, y), macid=macid, is_coordinate=True)   # 卡尔曼滤波
        Kdistance = kalman_filter(distance, macid=macid)                  # 卡尔曼滤波
        # else:
        #     # 当azimuth为0时设置默认值
        #     x, y = 0.0, 0.0
        #     FX, FY = 0.0, 0.0
        #     distance = 0.0
        #     KX, KY = 0.0, 0.0
        #     Kdistance = 0.0
            
        return {
            "macid": macid.upper(),
            "customdata": customdata,
            "rssi": round(rssi, 1),
            "snr": round(snr, 1),
            "azimuth": round(azimuth, 1),
            "elevation": round(elevation, 1),
            "x": round(x, 2),
            "y": round(y, 2),
            "FX": round(FX, 2),
            "FY": round(FY, 2),
            "KX": round(KX, 2),
            "KY": round(KY, 2),
            "distance": round(distance, 2),  
            "Kdistance": round(Kdistance, 2)
        }

    except Exception as e:
        print(f"解析错误: {str(e)}")
        return None

if __name__ == "__main__":
    pass