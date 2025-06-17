import paho.mqtt.client as mqtt_client
import random
from src.data_processing.processor import getAoAmqtt
from src.visualization.plot_generator import *


processed_result = None 
    
class MQTTSubscriber:
    """
    MQTT Client Subscriber
    Args:
    config (dict): Configuration dictionary with keys:
        - broker: MQTT broker address
        - port: Broker port
        - username: Authentication username
        - password: Authentication password
        - topic: Subscription topic
    """
    def __init__(self, config):  
        self.config = config  # 初始化配置属性
        self.client = mqtt_client.Client(client_id = f'subscribe-{random.randint(0, 100)}')
        self.client.username_pw_set(config['username'], config['password'])
        self.client.connect(config['broker'], config['port'])
 
        print(f"✅ Connected to {self.config['broker']}:{self.config['port']}")

    def subscribe(self):
        self.client.subscribe(self.config['topic'])
        print(f"🔔 Subscribed to topic: {self.config['topic']}")
        self.client.on_message = self.on_message

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        # print(f"Received `{payload}` from `{msg.topic}` topic")
        """ 
        - 新增on_connect和on_disconnect回调函数
        - 在连接成功时重置_missing_count计数器
        - 在断开连接时增加计数器并输出日志
        - 设置keepalive参数为60秒,可根据需求调整
        """
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
            print(f"卡尔曼滤波后距离: {result['Kdistance']} 米")  
            print("------------------------------")
            
            # # 调用绘图函数
            # draw_aoa_plot(result, lines, fig, ax)
            # # 调用绘图函数时传入双视图参数
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
            # print("解析失败,无效的AOA数据")
            return
    def run(self):
        self.client.loop_forever()
def mqtt_run():
    subscriber = MQTTSubscriber()
    subscriber.subscribe()
    subscriber.run()

if __name__ == "__main__":
    mqtt_run()