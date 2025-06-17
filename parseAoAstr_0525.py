"""
解析来自AOA(Angle of Arrival)的字符串数据,并提取以下信息：
- macid: MAC地址
- customdata: 用户数据
- rssi: 信号强度
- snr: 信噪比
- azimuth: 方位角
- elevation: 倾角
"""
# from paho.mqtt import client as mqtt_client
import math
from unittest import result
import paho.mqtt.client as mqtt_client
import random
import matplotlib.pyplot as plt
# import numpy as np
import argparse
parser = argparse.ArgumentParser(description='AOA可视化控制')
parser.add_argument('--show-all', action='store_true', help='显示所有窗口（默认）')
parser.add_argument('--show-raw', action='store_true', help='仅显示原始坐标窗口')
parser.add_argument('--show-filter', action='store_true', help='仅显示滤波坐标窗口')
parser.add_argument('--show-distance', action='store_true', help='仅显示距离窗口')
args = parser.parse_args()

# MQTT代理的地址和端口
mqtt_topic = "topic/aoatest"
# mqtt_broker = "www.prosensing.top"
mqtt_broker = "mqtt.3kniu.cn"
mqtt_port = 11882
mqtt_username = "bleAoAecho"
mqtt_password = "Prosensing#2023"
client_id = f'subscribe-{random.randint(0, 100)}'

#极坐标系映射为笛卡尔坐标系
def coordinate_mapping(azimuth, elevation, height = 1.5, X=0, Y=0):
    """极坐标系映射为笛卡尔坐标系"""
    azimuth = 360 - azimuth
    elevation = 90 - elevation
    r = height * math.tan(math.radians(elevation))
    dx = r * math.cos(math.radians(azimuth))
    dy = r * math.sin(math.radians(azimuth))
    return X + dx, Y + dy
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
# 低通滤波函数
def low_pass_filter(x, y, alfa=0.2):
    """低通滤波计算"""
    global preX, preY
    if 'preX' not in globals():
        preX = x
    if 'preY' not in globals():
        preY = y
    
    FX = x * alfa + preX * (1 - alfa)
    FY = y * alfa + preY * (1 - alfa)
    
    preX, preY = FX, FY  # 更新历史值
    return FX, FY

# 计算当前坐标(x,y)与参考点(X,Y)的欧氏距离
def calculate_distance(x, y, X=0, Y=0):
    dx = abs(x - X)  
    dy = abs(y - Y)
    return round(math.sqrt(dx**2 + dy**2), 2)
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
    UNDERANGLE = 5      # 仰角补正阈值

    try:
        strstart = 16 # 数据起始位置
        payload = payload.strip() # 去除payload首尾空白字符
        payloadlen = len(payload) # 计算payload总长度
        
        # 验证 payload 长度
        if payloadlen != MAXPAYLOADLEN:
            raise ValueError("无效的 payload 长度")
            
        if not payload.startswith('AOA='):
            raise ValueError("无效的 AOA 前缀")

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
        if azimuth != 0:
            azimuth = 360 - azimuth  # 补正为顺时针角度
        
        # 仰角计算（转换为垂直参考）
        elevation = int(
            payload[strstart + customdatalen + 14:strstart + customdatalen + 16] +
            payload[strstart + customdatalen + 12:strstart + customdatalen + 14], 
            16
        ) * 0.5
        elevation = 90 - elevation   # 转换为垂直方向
        
        if azimuth != 0:
            x, y = coordinate_mapping(azimuth, elevation)
            FX, FY = low_pass_filter(x, y)
            distance = calculate_distance(x, y)
            KX, KY = kalman_filter((x, y), macid=macid, is_coordinate=True)
            Kdistance = kalman_filter(distance, macid=macid)
        else:
            # 当azimuth为0时设置默认值
            x, y = 0.0, 0.0
            FX, FY = 0.0, 0.0
            distance = 0.0
            KX, KY = 0.0, 0.0
            Kdistance = 0.0
            
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
            "distance": round(distance, 2),  # 确保始终包含distance字段
            "Kdistance": round(Kdistance, 2)
        }

    except Exception as e:
        print(f"解析错误: {str(e)}")
        return None
def connect_mqtt():
    # client = mqtt_client.Client (
    # callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    # client_id=client_id
    # )   
    client = mqtt_client.Client (client_id=client_id)  
    client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(mqtt_broker, mqtt_port)
    return client

# 初始化绘图窗口
# plt.ion()  # Enable interactive mode
# fig1, ax1 = plt.subplots()  # 原始数据窗口
# fig2, ax2 = plt.subplots()  # 滤波数据窗口
# fig3, ax3 = plt.subplots()  # 基站与tag距离窗口
# ax1.set_title("Raw Coordinates") 
# ax2.set_title("Filtered Coordinates")
# ax3.set_title("Distance Tracking")
# lines = {}
# lines2 = {}
# lines3 = {}  
# 修复窗口初始化逻辑
if args.show_raw or args.show_filter or args.show_distance:
    plt.close('all')
    fig1, ax1, fig2, ax2, fig3, ax3 = None, None, None, None, None, None  # 显式初始化所有变量
    if args.show_raw:
        fig1, ax1 = plt.subplots()
        ax1.set_title("Raw Coordinates")
    if args.show_filter:
        fig2, ax2 = plt.subplots()
        ax2.set_title("Filtered Coordinates")
    if args.show_distance:
        fig3, ax3 = plt.subplots()
        ax3.set_title("Distance Tracking")
else:
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()
    ax1.set_title("Raw Coordinates")
    ax2.set_title("Filtered Coordinates")
    ax3.set_title("Distance Tracking")
lines = {}
lines2 = {}
lines3 = {}  

# def draw_aoa_plot(result, lines, fig, ax):
    # """实时绘制AOA数据坐标图"""
    # mac = result['macid']
    
    # # 初始化设备轨迹线
    # if mac not in lines:
    #     lines[mac], = ax.plot([], [], 'o-', label=mac)
    #     ax.legend()

    # # 更新滤波后坐标数据
    # x_data = list(lines[mac].get_xdata()) + [result['FX']]
    # y_data = list(lines[mac].get_ydata()) + [result['FY']]
    # lines[mac].set_data(x_data, y_data)
    
    # # 动态调整坐标范围
    # ax.relim()
    # ax.autoscale_view()
    # fig.canvas.draw_idle()
    # fig.canvas.flush_events()
def draw_aoa_plot(result, lines, lines2, lines3, fig1, ax1, fig2, ax2, fig3, ax3):
    global data_counter  # 新增全局计数器
    if 'data_counter' not in globals():
        data_counter = 0
        
    mac = result['macid']
    data_counter += 1  # 每次调用递增计数器
    
    plt.ion()
    
    # 原始数据窗口处理
    if fig1 and ax1:
        if mac not in lines:
            lines[mac], = ax1.plot([], [], 'o-', label=f'{mac}')
            ax1.legend()
        x_data = list(lines[mac].get_xdata()) + [result['x']]
        y_data = list(lines[mac].get_ydata()) + [result['y']]
        lines[mac].set_data(x_data, y_data)
        ax1.relim()
        ax1.autoscale_view()
        fig1.canvas.draw_idle()
    
    # 滤波数据窗口处理
    if fig2 and ax2: 
        if mac not in lines2:
            lines2[mac], = ax2.plot([], [], 's--', label=f'{mac}')
            ax2.legend()
        fx_data = list(lines2[mac].get_xdata()) + [result['FX']]
        fy_data = list(lines2[mac].get_ydata()) + [result['FY']]
        lines2[mac].set_data(fx_data, fy_data)
        ax2.relim()
        ax2.autoscale_view()
        fig2.canvas.draw_idle()
    
    # 距离窗口处理
    if fig3 and ax3:
        # 初始化两个轨迹线（自动颜色分配）
        if mac not in lines3:
            # 根据MAC哈希值生成唯一颜色索引
            color_idx = hash(mac) % 10  # 使用matplotlib默认10色循环
            line_style = ['-', '--']  # 实线原始，虚线滤波
            
            lines3[mac] = (
                ax3.plot([], [], marker='^', linestyle=line_style[0], 
                        markersize=6, color=f'C{color_idx}', label=f'{mac} Raw')[0],
                ax3.plot([], [], marker='s', linestyle=line_style[1],
                        markersize=4, color=f'C{color_idx}', label=f'{mac} Filter')[0]
            )
            ax3.legend()
        
        # 更新数据时记录序号
        raw_line, filter_line = lines3[mac]
        raw_data = list(raw_line.get_ydata()) + [result['distance']]
        filter_data = list(filter_line.get_ydata()) + [result['Kdistance']]
        
        max_points = 50
        raw_data = raw_data[-max_points:]
        filter_data = filter_data[-max_points:]
        
        # 计算起始序号（修复序号计算逻辑）
        start_idx = max(0, data_counter - len(raw_data))
        end_idx = data_counter - 1
        x_labels = [f"{i}" for i in range(start_idx, end_idx + 1)]
        
        # 设置数据点序号标签
        raw_line.set_data(range(len(raw_data)), raw_data)
        filter_line.set_data(range(len(filter_data)), filter_data)
        
        # 配置X轴显示
        ax3.set_xticks(range(0, len(raw_data), 5))  # 每5个点显示一个标签
        ax3.set_xticklabels(x_labels[::5])  # 显示实际数据点序号
        ax3.set_xlabel(f"Data Points ({start_idx}-{end_idx})")  # 标题显示范围
        
        # 设置双轨迹数据
        max_points = 50  # X轴最大显示50个数据点
        raw_data = raw_data[-max_points:]  # 保留最后50个原始数据
        filter_data = filter_data[-max_points:]  # 保留最后50个滤波数据
        
        x_points = range(len(raw_data))  # X轴坐标基于数据长度
        raw_line.set_data(x_points, raw_data)
        filter_line.set_data(x_points, filter_data)
        
        # 固定X轴范围
        ax3.set_xlim(0, max_points-1)
        ax3.relim()
        ax3.autoscale_view(scaley=True)  # 仅自动缩放Y轴
        ax3.autoscale_view()
        fig3.canvas.draw_idle()
    
    # 强制刷新所有图形
    plt.pause(0.001)  # 添加短暂的暂停保证GUI刷新
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    result = getAoAmqtt(payload)
    
    if result:
        print("\n解析结果:")
        print(f"MAC地址: {result['macid']}")
        print(f"用户数据: {result['customdata']}")
        print(f"信号强度: {result['rssi']} dBm")
        print(f"信噪比: {result['snr']} dB")
        print(f"方位角: {result['azimuth']}°")
        print(f"倾角: {result['elevation']}°")
        print(f"x坐标: {result['x']}")
        print(f"y坐标: {result['y']}")
        print(f"低通滤波后x坐标: {result['FX']}")
        print(f"低通滤波后y坐标: {result['FY']}")
        print(f"距离基准点: {result['distance']} 米") 
        print(f"卡尔曼滤波后距离: {result['Kdistance']} 米")  # 修正键名从distance_kalman改为Kdistance
        print("------------------------------")
        # 调用绘图函数
        # draw_aoa_plot(result, lines, fig, ax)
        # 调用绘图函数时传入双视图参数
        # draw_aoa_plot(result, lines, lines2, fig1, ax1, fig2, ax2)  
        # draw_aoa_plot(result, lines, lines2, lines3, fig1, ax1, fig2, ax2, fig3, ax3)
                
        # 更新后的函数调用需要传递所有参数
        draw_aoa_plot(
            result, 
            lines,   # 原始坐标轨迹线
            lines2,  # 滤波坐标轨迹线 
            lines3,  # 新增距离轨迹线
            fig1, ax1,  # 原始窗口
            fig2, ax2,  # 滤波窗口
            fig3, ax3   # 距离窗口
        )
    else:
        print("解析失败,无效的AOA数据")
    # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    return msg.payload.decode()
def subscribe(client: mqtt_client.Client):
    client.subscribe(mqtt_topic)    
    client.on_message = on_message

def mqtt_run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == "__main__":
    # test_payload = "AOA=AF0A9F4D33541EFFC7007B4ECD60EB620511C50000C951C506609209B9005E250001007A00AA00"
    # result = getAoAmqtt(test_payload)    
    # if result:
    #     print("解析结果：")
    #     print(f"MAC地址: {result['macid']}")
    #     print(f"用户数据: {result['customdata']}")
    #     print(f"信号强度: {result['rssi']} dBm")
    #     print(f"信噪比: {result['snr']} dB")
    #     print(f"方位角: {result['azimuth']}°")
    #     print(f"倾角: {result['elevation']}°")
    # else:
    #     print("解析失败，请检查输入数据")

    mqtt_run()

