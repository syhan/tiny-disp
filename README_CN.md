# Tiny Display - 可插拔式显示系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个统一的、可插拔的MSC显示设备驱动系统，支持多种显示模式。采用模块化设计，易于扩展和维护。

> 🌍 **English Documentation**: [README.md](README.md)

## ✨ 特性

- 🔌 **可插拔架构** - 基于插件的模块化设计
- 🎯 **统一接口** - 所有插件遵循统一的DisplayPlugin接口
- 🔄 **自动重连** - 设备断开后自动等待重连
- 📝 **配置管理** - 支持配置文件和环境变量
- 🐳 **Docker支持** - 提供完整的容器化部署方案
- 📊 **日志系统** - 统一的彩色日志输出
- 🎨 **多种显示** - 时钟、天气、系统监控、ZFS存储等

## 📁 项目结构

```
tiny-disp/
├── main.py                   # 主程序入口
├── plugin_manager.py         # 插件管理器
├── config_loader.py          # 配置加载器
├── logger.py                 # 日志模块
├── .tiny-disp.conf          # 配置文件
├── .tiny-disp.conf.sample   # 配置文件示例
├── requirements.txt          # Python依赖
│
├── lib/                      # 核心库
│   ├── display_interface.py  # 显示插件基类
│   └── msc_display_lib.py    # MSC设备底层库
│
├── plugins/                  # 插件目录
│   ├── plugin_sample.py      # 示例插件
│   ├── plugin_clock.py       # 世界时钟
│   ├── plugin_weather.py     # 天气显示
│   ├── plugin_metrics.py     # 系统指标
│   ├── plugin_metrics_rotated.py  # 旋转版指标
│   ├── plugin_zfs.py         # ZFS存储监控
│   └── plugin_zfs_pages.py   # ZFS多页显示
│
├── legacy/                   # 旧版独立程序
│   ├── clock.py
│   ├── weather.py
│   ├── metrics.py
│   └── ...
│
├── docs/                     # 文档
│   ├── PROJECT_STRUCTURE.md  # 项目结构说明
│   ├── DOCKER.md             # Docker使用指南
│   ├── MSC_DISPLAY_GUIDE.md  # MSC显示设备指南
│   └── REMOVE_SENSITIVE_DATA.md  # 敏感数据清理
│
├── Dockerfile                # Docker镜像
├── docker-compose.yml        # Docker Compose配置
└── .dockerignore            # Docker忽略文件
```

## 🚀 快速开始

### 安装依赖

```bash
# 安装Python依赖
pip3 install -r requirements.txt

# macOS需要额外安装
brew install sshpass  # 用于ZFS插件SSH连接
```

### 基本使用

```bash
# 1. 交互模式 - 从菜单选择插件
python3 main.py

# 2. 列出所有可用插件
python3 main.py --list

# 3. 直接运行指定插件
python3 main.py --plugin plugin_clock
python3 main.py --plugin plugin_metrics
python3 main.py --plugin plugin_zfs
```

### 配置文件

```bash
# 复制配置文件模板
cp .tiny-disp.conf.sample .tiny-disp.conf

# 编辑配置
nano .tiny-disp.conf
```

配置文件示例：
```ini
[general]
log_level = INFO

[clock]
cities = Shanghai:Asia/Shanghai,Berlin:Europe/Berlin,Vancouver:America/Vancouver,Washington:America/New_York
update_interval = 4

[zfs]
host = 192.168.1.100
user = admin
password = your_password
port = 22
pool_name = tank
update_interval = 15

[zfs_pages]
datasets = archives,photos,music,videos
page_duration = 4
update_interval = 1
```

## 📖 使用示例

### 交互模式

```bash
$ python3 main.py

============================================================
Tiny Display - Pluggable Display System
可插拔式显示系统
============================================================

✓ INFO - Waiting for MSC device...
✓ INFO - Connected: /dev/cu.usbmodem01234567891
✓ INFO - Device connected

✓ INFO - Discovering plugins...
✓ INFO - Loaded plugin: plugin_clock
✓ INFO - Loaded plugin: plugin_metrics
✓ INFO - Loaded plugin: plugin_zfs
✓ INFO - Found 6 plugin(s)

============================================================
Available Display Plugins:
============================================================
• World Clock
  Display world clock for multiple cities (90° rotated)
  Update interval: 4s

• System Metrics
  Display system metrics (CPU, Memory, Disk, etc.)
  Update interval: 10s

• ZFS Pool Monitor
  Display TrueNAS ZFS pool information
  Update interval: 15s
...

Enter plugin name (or 'q' to quit): World Clock
```

### 非交互模式

```bash
# 运行时钟插件
$ python3 main.py --plugin plugin_clock

✓ INFO - Loading plugin: plugin_clock
✓ INFO - Plugin: World Clock
✓ INFO - Description: Display world clock for multiple cities (90° rotated)
✓ INFO - Update interval: 4s
✓ INFO - Plugin started successfully

🌍 World Time Update:
   SHANGHAI     15:30
   BERLIN       08:30
   VANCOUVR     23:30
   WASHINGTN    02:30
```

### Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

详细的Docker使用说明请参考 [docs/DOCKER.md](docs/DOCKER.md)

## 🔌 可用插件

| 插件名称 | 文件名 | 功能描述 | 更新间隔 |
|---------|--------|---------|---------|
| **World Clock** | plugin_clock.py | 显示4个城市的时间 | 4秒 |
| **Weather** | plugin_weather.py | 显示天气信息 | 600秒 |
| **System Metrics** | plugin_metrics.py | CPU/内存/磁盘监控 | 10秒 |
| **System Metrics (Rotated)** | plugin_metrics_rotated.py | 旋转版系统监控 | 10秒 |
| **ZFS Pool Monitor** | plugin_zfs.py | ZFS存储池监控 | 15秒 |
| **ZFS Pool Monitor (Pages)** | plugin_zfs_pages.py | ZFS多页显示（支持触摸按钮） | 1秒 |
| **Hello World Advanced** | plugin_sample.py | 彩虹色循环动画示例 | 2秒 |

## 🛠️ 插件开发

### 创建新插件

1. 在 `plugins/` 目录创建 `plugin_myapp.py`
2. 继承 `DisplayPlugin` 基类
3. 实现必需方法

```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
My Custom Plugin
自定义插件
"""

import serial
from lib.display_interface import DisplayPlugin
from lib.msc_display_lib import MSCDisplay, Colors, draw_text_bitmap, clear_screen
from logger import get_logger

logger = get_logger()


class MyCustomPlugin(DisplayPlugin):
    """自定义显示插件"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None

    def get_name(self) -> str:
        """插件名称"""
        return "My Custom Display"

    def get_description(self) -> str:
        """插件描述"""
        return "插件功能描述"

    def get_update_interval(self) -> int:
        """更新间隔（秒）"""
        return 10

    def initialize(self) -> bool:
        """初始化插件"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            logger.info("插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化错误: {e}")
            return False

    def update(self) -> bool:
        """更新显示内容"""
        try:
            if self.first_draw:
                clear_screen(self.ser, Colors.BLACK)
                self.first_draw = False

            # 你的显示逻辑
            draw_text_bitmap(self.ser, 10, 10, "HELLO", Colors.GREEN, scale=2)

            logger.info("显示已更新")
            return True
        except Exception as e:
            logger.error(f"更新错误: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        self.display = None
        logger.info("清理完成")
```

### 插件生命周期

```
initialize() → update() → update() → ... → cleanup()
     ↓           ↑                              ↓
     ↓           └─── (每隔 update_interval) ────┘
     ↓
 设备初始化     定期更新显示           插件停止时清理
```

### 必需实现的方法

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_name()` | str | 插件显示名称 |
| `get_description()` | str | 插件功能描述 |
| `get_update_interval()` | int | 更新间隔（秒） |
| `initialize()` | bool | 初始化，返回True表示成功 |
| `update()` | bool | 更新显示，返回True表示成功 |
| `cleanup()` | None | 清理资源 |

### 插件最佳实践

1. **使用logger而非print**
   ```python
   from logger import get_logger
   logger = get_logger()

   logger.info("正常信息")
   logger.warning("警告信息")
   logger.error("错误信息")
   ```

2. **使用配置文件**
   ```python
   from config_loader import config

   value = config.get('my_plugin', 'setting', fallback='default')
   ```

3. **异常处理**
   ```python
   def update(self) -> bool:
       try:
           # 更新逻辑
           return True
       except Exception as e:
           logger.error(f"更新失败: {e}")
           return False
   ```

4. **资源清理**
   ```python
   def cleanup(self):
       if self.resource:
           self.resource.close()
       self.display = None
   ```

## 📝 日志系统

系统使用统一的彩色日志输出：

```python
from logger import get_logger
logger = get_logger()

logger.debug("调试信息")    # 🔍 DEBUG - 青色
logger.info("正常信息")     # ✓ INFO - 绿色
logger.warning("警告信息")  # ⚠️ WARNING - 黄色
logger.error("错误信息")    # ✗ ERROR - 红色
logger.critical("严重错误")  # 🚨 CRITICAL - 紫色
```

配置日志级别：
```ini
# .tiny-disp.conf
[general]
log_level = INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🐳 Docker部署

### 构建和运行

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

### 环境变量

```yaml
# docker-compose.yml
environment:
  - PLUGIN_NAME=plugin_clock
  - LOG_LEVEL=INFO
  - ZFS_HOST=192.168.1.100
  - ZFS_USER=admin
  - ZFS_PASSWORD=secret
```

详细信息请参考 [docs/DOCKER.md](docs/DOCKER.md)

## 📋 命令行参数

```bash
python3 main.py [选项]

选项:
  -i, --interactive     交互模式（从菜单选择插件）
  -p, --plugin PLUGIN   直接运行指定插件（按文件名）
  -l, --list           列出所有可用插件并退出

示例:
  python3 main.py                          # 交互模式
  python3 main.py --interactive            # 交互模式
  python3 main.py --plugin plugin_clock    # 运行时钟插件
  python3 main.py --list                   # 列出所有插件
```

## 🔧 设备规格

- **屏幕尺寸**: 160×80 像素
- **接口**: USB串口
- **波特率**: 19200
- **颜色格式**: RGB565
- **方向**: 支持横屏/竖屏
- **字体**: 内置5×7点阵字体

## 🆘 故障排除

### 设备未找到

```bash
# macOS
ls /dev/cu.usbmodem*

# Linux
ls /dev/ttyACM*

# 权限问题 (Linux)
sudo usermod -a -G dialout $USER
# 需要重新登录
```

### Docker设备访问

```bash
# 查找设备
ls -l /dev/cu.* /dev/ttyACM*

# 更新docker-compose.yml中的设备路径
devices:
  - "/dev/cu.usbmodem01234567891:/dev/ttyUSB0"
```

### ZFS插件连接失败

```bash
# 确保sshpass已安装
brew install sshpass  # macOS
apt install sshpass   # Debian/Ubuntu

# 测试SSH连接
ssh user@192.168.1.100

# 检查配置文件
cat .tiny-disp.conf
```

## 📚 文档

- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [Docker部署指南](docs/DOCKER.md)
- [MSC显示设备指南](docs/MSC_DISPLAY_GUIDE.md)
- [敏感数据清理](docs/REMOVE_SENSITIVE_DATA.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目基于原有代码重构，保留所有原始版权信息。

## 🎉 更新日志

### v2.0.0 (2024-12-04)

- ✨ 全新的可插拔架构
- ✨ 统一的DisplayPlugin接口
- ✨ 插件自动发现和加载
- ✨ 配置文件支持
- ✨ 统一的日志系统
- ✨ Docker容器化支持
- ✨ 自动设备重连
- ✨ 命令行参数支持
- ✨ 完整的文档系统
- 🔧 保留所有原有功能
- 🐛 修复设备断开重复警告

## 🔗 相关链接

- [项目仓库](https://github.com/syhan/tiny-disp)
- [问题跟踪](https://github.com/syhan/tiny-disp/issues)
- [更新日志](CHANGELOG.md)

## 💡 致谢

感谢所有贡献者和用户的支持！

---

**Made with ❤️ by the Tiny Display Team**
