# Tiny Display - 可插拔式显示系统

一个统一的、可插拔的MSC显示设备驱动系统，支持多种显示模式。

## 项目架构

### 核心组件

1. **display_interface.py** - 显示插件基类
   - `DisplayPlugin` - 所有显示插件必须继承的抽象基类
   - `DisplayConfig` - 显示配置类

2. **plugin_manager.py** - 插件管理器
   - 自动发现和加载插件
   - 插件切换和生命周期管理
   - 统一的插件接口

3. **msc_display_lib.py** - MSC设备底层库
   - 设备连接和通信
   - 基础绘图函数
   - 颜色和字体定义

4. **main.py** - 主程序
   - 设备连接管理
   - 交互式插件选择
   - 自动重连机制

### 显示插件

所有插件都实现了统一的 `DisplayPlugin` 接口:

- **plugin_clock.py** - 世界时钟显示 (4个城市)
- **plugin_weather.py** - 天气信息显示
- **plugin_metrics.py** - 系统指标监控 (CPU/内存/磁盘等)
- **plugin_metrics_rotated.py** - 旋转版系统指标
- **plugin_zfs.py** - ZFS存储池监控 (完整实现)
- **plugin_zfs_pages.py** - ZFS多页显示 (完整实现，支持触摸按钮)

## 使用方法

### 基本使用

```bash
# 运行主程序，交互式选择插件
python3 main.py

# 自动启动指定插件
python3 main.py "World Clock"
python3 main.py "Weather"
python3 main.py "System Metrics"
```

### 运行单个插件

原有的独立程序仍然可用:

```bash
python3 clock.py
python3 weather.py
python3 metrics.py
python3 zfs.py
```

## 插件开发指南

### 创建新插件

1. 创建新的插件文件 (例如 `plugin_myapp.py`)
2. 继承 `DisplayPlugin` 基类
3. 实现必需的方法

```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
My Custom Plugin
自定义插件
"""

import serial
from display_interface import DisplayPlugin
from msc_display_lib import MSCDisplay, Colors, clear_screen


class MyCustomPlugin(DisplayPlugin):
    """My Custom Display Plugin"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None

    def get_name(self) -> str:
        return "My Custom Display"

    def get_description(self) -> str:
        return "Description of what this plugin does"

    def get_update_interval(self) -> int:
        return 10  # Update every 10 seconds

    def initialize(self) -> bool:
        """Initialize the display"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            return True
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    def update(self) -> bool:
        """Update the display"""
        try:
            if self.first_draw:
                clear_screen(self.ser, Colors.BLACK)
                self.first_draw = False

            # Your display logic here

            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
```

### 插件生命周期

1. **initialize()** - 插件被激活时调用一次
2. **update()** - 根据 `get_update_interval()` 定期调用
3. **cleanup()** - 插件被停止或切换时调用

### 必需方法

- `get_name()` - 返回插件显示名称
- `get_description()` - 返回插件描述
- `get_update_interval()` - 返回更新间隔(秒)
- `initialize()` - 初始化插件
- `update()` - 更新显示内容
- `cleanup()` - 清理资源

## 特性

### ✅ 已实现

- 统一的插件接口
- 自动插件发现和加载
- 交互式插件选择
- 自动设备重连
- 命令行参数支持
- 保留原有独立程序

### 🚧 待实现

- 配置文件支持
- 插件热重载
- 多设备支持
- Web管理界面
- 插件依赖管理

## 依赖

```bash
pip install pyserial psutil pytz requests pillow
```

## 文件结构

```
tiny-disp/
├── display_interface.py      # 显示插件基类
├── plugin_manager.py          # 插件管理器
├── msc_display_lib.py        # MSC设备底层库
├── main.py                   # 主程序
├── plugin_clock.py           # 时钟插件
├── plugin_weather.py         # 天气插件
├── plugin_metrics.py         # 系统指标插件
├── plugin_metrics_rotated.py # 旋转版系统指标
├── plugin_zfs.py             # ZFS插件
├── plugin_zfs_pages.py       # ZFS多页插件
├── clock.py                  # 原时钟程序(保留)
├── weather.py                # 原天气程序(保留)
├── metrics.py                # 原指标程序(保留)
├── metrics_rotated.py        # 原旋转指标程序(保留)
├── zfs.py                    # 原ZFS程序(保留)
├── zfs_pages.py              # 原ZFS多页程序(保留)
├── MSU2_MINI_DemoV1.6_Output.py  # 原始演示程序(保留)
├── requirements.txt          # Python依赖
└── README.md                 # 本文件
```

## 设备规格

- 屏幕: 160x80 像素
- 接口: USB串口 (19200 波特率)
- 颜色: RGB565 格式

## 许可

本项目基于原有代码重构，保留所有原始版权信息。

## 更新日志

### v2.0.0 (2025-12-04)
- ✨ 全新的可插拔架构
- ✨ 统一的显示接口
- ✨ 插件管理系统
- ✨ 交互式插件选择
- ✨ 保留所有原有功能
