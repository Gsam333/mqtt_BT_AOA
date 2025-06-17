"""
解析来自AOA(Angle of Arrival)的字符串数据,并提取以下信息：
- macid: MAC地址
- customdata: 用户数据
- rssi: 信号强度
- snr: 信噪比
- azimuth: 方位角
- elevation: 倾角
"""
import math

def coordinate_mapping(azimuth, elevation, height = 1.5, X=0, Y=0):
    """极坐标系映射为笛卡尔坐标系"""
    azimuth = 360 - azimuth
    elevation = 90 - elevation
    r = height * math.tan(math.radians(elevation))
    dx = r * math.cos(math.radians(azimuth))
    dy = r * math.sin(math.radians(azimuth))
    return X + dx, Y + dy

# 计算当前坐标(x,y)与参考点(X,Y)的欧氏距离
def calculate_distance(x, y, X=0, Y=0):
    dx = abs(x - X)  
    dy = abs(y - Y)
    return round(math.sqrt(dx**2 + dy**2), 2)

if __name__ == "__main__":
    pass