# Tiny Display - Pluggable Display System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A unified, pluggable MSC display device driver system supporting multiple display modes. Built with modular design for easy extension and maintenance.

> 🌏 **中文文档**: [README_CN.md](README_CN.md)

## ✨ Features

- 🔌 **Pluggable Architecture** - Modular plugin-based design
- 🎯 **Unified Interface** - All plugins follow the DisplayPlugin interface
- 🔄 **Auto-Reconnect** - Automatically reconnects when device is disconnected
- 📝 **Configuration Management** - Support for config files and environment variables
- 🐳 **Docker Support** - Complete containerization solution
- 📊 **Logging System** - Unified colored log output
- 🎨 **Multiple Displays** - Clock, weather, system metrics, ZFS storage, etc.

## 📁 Project Structure

```
tiny-disp/
├── main.py                   # Main program entry
├── plugin_manager.py         # Plugin manager
├── config_loader.py          # Configuration loader
├── logger.py                 # Logging module
├── .tiny-disp.conf          # Configuration file
├── .tiny-disp.conf.sample   # Configuration template
├── requirements.txt          # Python dependencies
│
├── lib/                      # Core libraries
│   ├── display_interface.py  # Display plugin base class
│   └── msc_display_lib.py    # MSC device low-level library
│
├── plugins/                  # Plugin directory
│   ├── plugin_sample.py      # Sample plugin
│   ├── plugin_clock.py       # World clock
│   ├── plugin_weather.py     # Weather display
│   ├── plugin_metrics.py     # System metrics
│   ├── plugin_metrics_rotated.py  # Rotated metrics
│   ├── plugin_zfs.py         # ZFS storage monitor
│   └── plugin_zfs_pages.py   # ZFS multi-page display
│
├── legacy/                   # Legacy standalone programs
│   ├── clock.py
│   ├── weather.py
│   ├── metrics.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── PROJECT_STRUCTURE.md  # Project structure guide
│   ├── DOCKER.md             # Docker deployment guide
│   ├── MSC_DISPLAY_GUIDE.md  # MSC display device guide
│   └── REMOVE_SENSITIVE_DATA.md  # Sensitive data removal
│
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker Compose config
└── .dockerignore            # Docker ignore file
```

## 🚀 Quick Start

### Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# macOS additional requirement
brew install sshpass  # Required for ZFS plugin SSH connection
```

### Basic Usage

```bash
# 1. Interactive mode - select plugin from menu
python3 main.py

# 2. List all available plugins
python3 main.py --list

# 3. Run specific plugin directly
python3 main.py --plugin plugin_clock
python3 main.py --plugin plugin_metrics
python3 main.py --plugin plugin_zfs
```

### Configuration File

```bash
# Copy configuration template
cp .tiny-disp.conf.sample .tiny-disp.conf

# Edit configuration
nano .tiny-disp.conf
```

Configuration example:
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

## 📖 Usage Examples

### Interactive Mode

```bash
$ python3 main.py

============================================================
Tiny Display - Pluggable Display System
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

### Non-Interactive Mode

```bash
# Run clock plugin
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

### Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down
```

For detailed Docker usage, see [docs/DOCKER.md](docs/DOCKER.md)

## 🔌 Available Plugins

| Plugin Name | Filename | Description | Update Interval |
|------------|----------|-------------|----------------|
| **World Clock** | plugin_clock.py | Display time for 4 cities | 4s |
| **Weather** | plugin_weather.py | Display weather information | 600s |
| **System Metrics** | plugin_metrics.py | CPU/Memory/Disk monitoring | 10s |
| **System Metrics (Rotated)** | plugin_metrics_rotated.py | Rotated system metrics | 10s |
| **ZFS Pool Monitor** | plugin_zfs.py | ZFS storage pool monitoring | 15s |
| **ZFS Pool Monitor (Pages)** | plugin_zfs_pages.py | ZFS multi-page display (touch button support) | 1s |
| **Hello World Advanced** | plugin_sample.py | Rainbow color cycling animation | 2s |

## 🛠️ Plugin Development

### Create a New Plugin

1. Create `plugin_myapp.py` in the `plugins/` directory
2. Inherit from `DisplayPlugin` base class
3. Implement required methods

```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
My Custom Plugin
"""

import serial
from lib.display_interface import DisplayPlugin
from lib.msc_display_lib import MSCDisplay, Colors, draw_text_bitmap, clear_screen
from logger import get_logger

logger = get_logger()


class MyCustomPlugin(DisplayPlugin):
    """My Custom Display Plugin"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None

    def get_name(self) -> str:
        """Plugin name"""
        return "My Custom Display"

    def get_description(self) -> str:
        """Plugin description"""
        return "Description of what this plugin does"

    def get_update_interval(self) -> int:
        """Update interval in seconds"""
        return 10

    def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            logger.info("My plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    def update(self) -> bool:
        """Update display content"""
        try:
            if self.first_draw:
                clear_screen(self.ser, Colors.BLACK)
                self.first_draw = False

            # Your display logic here
            draw_text_bitmap(self.ser, 10, 10, "HELLO", Colors.GREEN, scale=2)

            logger.info("Display updated")
            return True
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        logger.info("Cleanup complete")
```

### Plugin Lifecycle

```
initialize() → update() → update() → ... → cleanup()
     ↓           ↑                              ↓
     ↓           └─── (every update_interval) ──┘
     ↓
Device Init      Periodic Update        Cleanup on Stop
```

### Required Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `get_name()` | str | Plugin display name |
| `get_description()` | str | Plugin functionality description |
| `get_update_interval()` | int | Update interval in seconds |
| `initialize()` | bool | Initialize, return True on success |
| `update()` | bool | Update display, return True on success |
| `cleanup()` | None | Cleanup resources |

### Best Practices

1. **Use Logger Instead of Print**
   ```python
   from logger import get_logger
   logger = get_logger()

   logger.info("Normal information")
   logger.warning("Warning message")
   logger.error("Error message")
   ```

2. **Use Configuration Files**
   ```python
   from config_loader import config

   value = config.get('my_plugin', 'setting', fallback='default')
   ```

3. **Exception Handling**
   ```python
   def update(self) -> bool:
       try:
           # Update logic
           return True
       except Exception as e:
           logger.error(f"Update failed: {e}")
           return False
   ```

4. **Resource Cleanup**
   ```python
   def cleanup(self):
       if self.resource:
           self.resource.close()
       self.display = None
   ```

## 📝 Logging System

The system uses unified colored log output:

```python
from logger import get_logger
logger = get_logger()

logger.debug("Debug info")      # 🔍 DEBUG - Cyan
logger.info("Normal info")      # ✓ INFO - Green
logger.warning("Warning")       # ⚠️ WARNING - Yellow
logger.error("Error")           # ✗ ERROR - Red
logger.critical("Critical")     # 🚨 CRITICAL - Magenta
```

Configure log level:
```ini
# .tiny-disp.conf
[general]
log_level = INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down
```

### Environment Variables

```yaml
# docker-compose.yml
environment:
  - PLUGIN_NAME=plugin_clock
  - LOG_LEVEL=INFO
  - ZFS_HOST=192.168.1.100
  - ZFS_USER=admin
  - ZFS_PASSWORD=secret
```

For detailed information, see [docs/DOCKER.md](docs/DOCKER.md)

## 📋 Command Line Arguments

```bash
python3 main.py [options]

Options:
  -i, --interactive     Interactive mode (select plugin from menu)
  -p, --plugin PLUGIN   Run specific plugin (by filename)
  -l, --list           List all available plugins and exit

Examples:
  python3 main.py                          # Interactive mode
  python3 main.py --interactive            # Interactive mode
  python3 main.py --plugin plugin_clock    # Run clock plugin
  python3 main.py --list                   # List all plugins
```

## 🔧 Device Specifications

- **Screen Size**: 160×80 pixels
- **Interface**: USB Serial
- **Baud Rate**: 19200
- **Color Format**: RGB565
- **Orientation**: Landscape/Portrait support
- **Font**: Built-in 5×7 bitmap font

## 🆘 Troubleshooting

### Device Not Found

```bash
# macOS
ls /dev/cu.usbmodem*

# Linux
ls /dev/ttyACM*

# Permission issue (Linux)
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### Docker Device Access

```bash
# Find device
ls -l /dev/cu.* /dev/ttyACM*

# Update device path in docker-compose.yml
devices:
  - "/dev/cu.usbmodem01234567891:/dev/ttyUSB0"
```

### ZFS Plugin Connection Failed

```bash
# Ensure sshpass is installed
brew install sshpass  # macOS
apt install sshpass   # Debian/Ubuntu

# Test SSH connection
ssh user@192.168.1.100

# Check configuration file
cat .tiny-disp.conf
```

## 📚 Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Docker Deployment Guide](docs/DOCKER.md)
- [MSC Display Device Guide](docs/MSC_DISPLAY_GUIDE.md)
- [Sensitive Data Removal](docs/REMOVE_SENSITIVE_DATA.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is refactored from original code, all original copyrights are preserved.

## 🎉 Changelog

### v2.0.0 (2024-12-04)

- ✨ New pluggable architecture
- ✨ Unified DisplayPlugin interface
- ✨ Automatic plugin discovery and loading
- ✨ Configuration file support
- ✨ Unified logging system
- ✨ Docker containerization support
- ✨ Automatic device reconnection
- ✨ Command-line argument support
- ✨ Complete documentation system
- 🔧 All original features preserved
- 🐛 Fixed duplicate device disconnect warnings

## 🔗 Links

- [Project Repository](https://github.com/syhan/tiny-disp)
- [Issue Tracker](https://github.com/syhan/tiny-disp/issues)
- [Changelog](CHANGELOG.md)

## 💡 Acknowledgments

Thanks to all contributors and users for their support!

---

**Made with ❤️ by the Tiny Display Team**
