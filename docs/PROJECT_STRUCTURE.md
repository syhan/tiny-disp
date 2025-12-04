# Tiny Display - 项目结构文档

## 📁 目录结构

```
tiny-disp/
├── main.py                    # 主程序入口
├── plugin_manager.py          # 插件管理器
├── config_loader.py          # 配置加载器
├── logger.py                 # 日志系统
├── .tiny-disp.conf           # 配置文件
├── requirements.txt          # Python依赖
├── README.md                 # 项目文档
├── .gitignore               # Git忽略文件
├── install-service.sh        # Systemd服务安装脚本
├── tiny-disp.service        # Systemd服务文件
│
├── lib/                      # 核心库目录
│   ├── __init__.py          # Python包标识
│   ├── msc_display_lib.py   # MSC显示硬件库
│   └── display_interface.py # 显示接口基类
│
├── plugins/                  # 插件目录
│   ├── __init__.py          # Python包标识
│   ├── plugin_clock.py      # 世界时钟插件
│   ├── plugin_weather.py    # 天气显示插件
│   ├── plugin_metrics.py    # 系统指标插件
│   ├── plugin_metrics_rotated.py  # 旋转系统指标插件
│   ├── plugin_zfs.py        # ZFS池监控插件
│   └── plugin_zfs_pages.py  # ZFS多页监控插件
│
├── docs/                     # 文档目录
│   ├── PROJECT_STRUCTURE.md # 项目结构文档（本文件）
│   ├── REFACTORING_SUMMARY.md # 重构总结
│   └── SYSTEMD_SERVICE.md   # Systemd服务文档
│
└── legacy/                   # 旧代码归档
    ├── clock.py             # 旧的时钟显示
    ├── weather.py           # 旧的天气显示
    ├── metrics.py           # 旧的系统指标
    ├── metrics_rotated.py   # 旧的旋转指标
    ├── zfs.py              # 旧的ZFS监控
    ├── zfs_pages.py        # 旧的ZFS多页
    └── MSU2_MINI_DemoV1.6_Output.py  # 原始演示代码
```

## 📦 模块说明

### 核心模块（根目录）

| 文件 | 说明 |
|------|------|
| `main.py` | 主程序入口，处理设备连接、插件选择和运行循环 |
| `plugin_manager.py` | 插件管理器，负责插件的发现、加载和切换 |
| `config_loader.py` | 配置文件加载器，读取 .tiny-disp.conf |
| `logger.py` | 统一日志系统，支持5个日志级别和彩色输出 |
| `.tiny-disp.conf` | 配置文件，包含所有插件的配置参数 |

### lib/ - 核心库

| 文件 | 说明 |
|------|------|
| `msc_display_lib.py` | MSC显示设备硬件库，提供设备通信功能 |
| `display_interface.py` | DisplayPlugin 抽象基类，定义插件接口规范 |

### plugins/ - 显示插件

| 文件 | 说明 |
|------|------|
| `plugin_clock.py` | 世界时钟，显示多个城市时间（90°旋转） |
| `plugin_weather.py` | 天气显示，获取并显示天气信息（90°旋转） |
| `plugin_metrics.py` | 系统指标，显示CPU、内存、磁盘等信息 |
| `plugin_metrics_rotated.py` | 旋转系统指标（90°旋转版本） |
| `plugin_zfs.py` | ZFS池监控，显示TrueNAS存储池状态 |
| `plugin_zfs_pages.py` | ZFS多页监控，分页显示详细ZFS信息 |

### docs/ - 文档

| 文件 | 说明 |
|------|------|
| `PROJECT_STRUCTURE.md` | 项目结构说明（本文件） |
| `REFACTORING_SUMMARY.md` | 重构总结文档 |
| `SYSTEMD_SERVICE.md` | Systemd服务安装和配置文档 |

### legacy/ - 旧代码归档

保留的原始显示模块文件，作为参考和历史记录。

## 🔧 模块依赖关系

```
main.py
  ├── lib.msc_display_lib (设备通信)
  ├── plugin_manager (插件管理)
  └── logger (日志记录)

plugin_manager.py
  ├── lib.display_interface (插件接口)
  └── importlib (动态加载插件)

plugins/plugin_*.py
  ├── lib.display_interface (继承DisplayPlugin)
  ├── lib.msc_display_lib (设备操作)
  └── config_loader (读取配置)

lib/display_interface.py
  └── lib.msc_display_lib (设备通信)
```

## 🎯 设计原则

### 1. 模块化设计
- 每个模块职责单一明确
- 低耦合高内聚
- 便于维护和扩展

### 2. 可插拔架构
- 插件独立于主程序
- 统一的接口规范
- 自动发现和加载

### 3. 配置驱动
- 集中式配置文件
- 每个插件独立配置段
- 便于定制和调整

### 4. 清晰的目录结构
- `lib/` - 核心库和接口
- `plugins/` - 所有插件
- `docs/` - 所有文档
- `legacy/` - 历史代码

## 🚀 添加新插件

1. 在 `plugins/` 目录创建新文件：
```python
# plugins/plugin_newdisplay.py
from lib.display_interface import DisplayPlugin
from lib.msc_display_lib import *

class NewDisplayPlugin(DisplayPlugin):
    def get_name(self) -> str:
        return "New Display"

    def get_description(self) -> str:
        return "Description of new display"

    def get_update_interval(self) -> int:
        return 5

    def initialize(self) -> bool:
        # 初始化代码
        return True

    def update(self) -> bool:
        # 更新显示代码
        return True

    def cleanup(self):
        # 清理代码
        pass
```

2. 更新 `plugin_manager.py` 的 `plugin_modules` 列表：
```python
plugin_modules = [
    'plugin_clock',
    'plugin_weather',
    # ... 其他插件 ...
    'plugin_newdisplay',  # 添加新插件
]
```

3. 如需配置，在 `.tiny-disp.conf` 添加配置段：
```ini
[newdisplay]
# 新插件的配置项
option1 = value1
option2 = value2
```

4. 重启程序，新插件自动出现在菜单中！

## 📝 代码规范

### 导入规范
```python
# 核心库导入
from lib.msc_display_lib import ...
from lib.display_interface import DisplayPlugin

# 配置和日志
from config_loader import ConfigLoader
from logger import get_logger
```

### 命名规范
- 插件文件：`plugin_<name>.py`
- 插件类：`<Name>Plugin`
- 配置段：`[<name>]`

## 🔍 导入路径说明

由于项目重构，所有导入路径已更新：

- **旧路径**：`from msc_display_lib import ...`
- **新路径**：`from lib.msc_display_lib import ...`

- **旧路径**：`from display_interface import ...`
- **新路径**：`from lib.display_interface import ...`

这样可以清晰地区分核心库（lib/）和业务代码（plugins/、根目录）。

## ✅ 优势

1. **清晰的结构** - 一目了然的目录组织
2. **易于维护** - 每个模块职责明确
3. **便于扩展** - 添加新插件非常简单
4. **专业规范** - 符合Python项目最佳实践
5. **代码复用** - 核心库可被多个插件使用

---

更新日期：2024-12-04
