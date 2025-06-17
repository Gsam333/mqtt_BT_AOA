import matplotlib.pyplot as plt
# import numpy as np

import argparse
parser = argparse.ArgumentParser(description='AOA可视化控制')
parser.add_argument('--show-all', action='store_true', help='显示所有窗口（默认）')
parser.add_argument('--show-raw', action='store_true', help='仅显示原始坐标窗口')
parser.add_argument('--show-filter', action='store_true', help='仅显示滤波坐标窗口')
parser.add_argument('--show-distance', action='store_true', help='仅显示距离窗口')
args = parser.parse_args()

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
    