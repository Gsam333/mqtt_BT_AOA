# MQTT BT AOA 项目

## 项目简介
MQTT BT AOA是一个基于MQTT的蓝牙AOA(Angle of Arrival)定位系统，用于实时跟踪和分析蓝牙设备的位置信息。该系统通过接收蓝牙AOA数据，应用多种滤波算法进行数据优化，最终实现高精度的室内定位功能。

## 技术架构

### 系统架构
该项目采用模块化设计，主要包含以下核心组件：

```
MQTT BT AOA
│
├── 数据采集层 - MQTT通信模块
│   └── 接收和处理蓝牙AOA原始数据
│
├── 数据处理层
│   ├── 数据预处理
│   └── 数据优化（多种滤波算法）
│
├── 数据存储层 - SQLite数据库
│   └── 存储原始和处理后的定位数据
│
└── 数据展示层 - 可视化模块
    └── 实时显示定位结果和轨迹
```

### 核心模块

#### 1. MQTT通信模块 (`src/mqtt/`)
- 负责与MQTT代理建立连接
- 订阅相关主题，接收蓝牙AOA数据
- 处理接收到的消息并转发给数据处理模块

#### 2. 数据处理模块 (`src/data_processing/`)
- 解析和预处理原始AOA数据
- 转换数据格式，为后续处理做准备

#### 3. 数据优化模块 (`src/data_optimization/`)
- 实现多种滤波算法：
  - 卡尔曼滤波器 (`kalman_filter.py`)
  - 低通滤波器 (`low_pass_filter.py`) 
  - AOA特定滤波器 (`aoa_filter.py`)
  - 信号滤波处理 (`filterSignal.py`)
- 坐标映射功能 (`coordinate_mapping.py`)
- 提高定位精度，减少噪声干扰

#### 4. 数据库模块 (`src/database/`)
- 基于SQLite的数据存储实现 (`sqlite_handler.py`)
- 存储原始数据和处理后的结果
- 支持历史数据查询和分析

#### 5. 可视化模块 (`src/visualization/`)
- 实时绘图生成器 (`plot_generator.py`)
- 支持多种显示模式：
  - 原始坐标显示
  - 滤波后坐标显示
  - 距离跟踪显示
- 提供直观的数据可视化界面

### 技术栈
- 编程语言：Python
- 通信协议：MQTT
- 数据库：SQLite
- 数据处理：NumPy, SciPy
- 可视化：Matplotlib
- 配置管理：YAML

## 安装与使用

### 依赖安装
```bash
pip install -r requirements.txt
```

### 配置
编辑`config.yaml`文件，设置MQTT代理地址、主题和其他参数。

### 运行
```bash
python main.py
```

## 许可证
[待添加]

## 贡献者
[待添加]