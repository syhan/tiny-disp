# Systemd Service Setup

将 Tiny Display 设置为 Linux 系统服务，实现开机自启动和后台运行。

## 快速安装

### 自动安装（推荐）

使用提供的安装脚本：

```bash
# 给脚本添加执行权限
chmod +x install-service.sh

# 运行安装脚本
sudo ./install-service.sh
```

脚本会：
1. 提示选择要运行的插件
2. 自动配置服务文件
3. 安装并启用服务
4. 可选择立即启动服务

### 手动安装

如果需要手动配置：

1. **编辑服务文件**

编辑 `tiny-disp.service`，修改以下内容：

```ini
[Service]
User=你的用户名
WorkingDirectory=/path/to/tiny-disp
ExecStart=/usr/bin/python3 /path/to/tiny-disp/main.py --plugin "插件名称"
```

2. **安装服务**

```bash
# 复制服务文件到 systemd 目录
sudo cp tiny-disp.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启动）
sudo systemctl enable tiny-disp.service

# 启动服务
sudo systemctl start tiny-disp.service
```

## 服务管理命令

### 基本命令

```bash
# 启动服务
sudo systemctl start tiny-disp

# 停止服务
sudo systemctl stop tiny-disp

# 重启服务
sudo systemctl restart tiny-disp

# 查看服务状态
sudo systemctl status tiny-disp

# 启用开机自启动
sudo systemctl enable tiny-disp

# 禁用开机自启动
sudo systemctl disable tiny-disp
```

### 查看日志

```bash
# 实时查看日志
sudo journalctl -u tiny-disp -f

# 查看最近100行日志
sudo journalctl -u tiny-disp -n 100

# 查看今天的日志
sudo journalctl -u tiny-disp --since today

# 查看特定时间的日志
sudo journalctl -u tiny-disp --since "2025-01-01 00:00:00"
```

## 插件选择

服务可以运行任何可用的插件：

```ini
# World Clock
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "World Clock"

# Weather
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "Weather"

# System Metrics
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "System Metrics"

# System Metrics (Rotated)
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "System Metrics (Rotated)"

# ZFS Pool Monitor
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "ZFS Pool Monitor"

# ZFS Pool Monitor (Pages)
ExecStart=/usr/bin/python3 /path/to/main.py --plugin "ZFS Pool Monitor (Pages)"

# 或使用索引号
ExecStart=/usr/bin/python3 /path/to/main.py --plugin 2
```

## 故障排查

### 服务无法启动

1. **检查服务状态**
```bash
sudo systemctl status tiny-disp
```

2. **查看详细日志**
```bash
sudo journalctl -u tiny-disp -n 50
```

3. **检查Python路径**
```bash
which python3
# 确保服务文件中的路径正确
```

4. **检查工作目录**
```bash
# 确保WorkingDirectory路径正确
ls -la /path/to/tiny-disp
```

### 设备连接问题

如果服务启动但设备未连接：

1. **检查设备权限**
```bash
# 将用户添加到dialout组（USB设备访问）
sudo usermod -aG dialout $USER

# 需要注销重新登录才能生效
```

2. **检查USB设备**
```bash
# 查看连接的USB设备
lsusb

# 查看串口设备
ls -la /dev/tty*
```

### 修改运行的插件

如果需要更改服务运行的插件：

```bash
# 1. 编辑服务文件
sudo nano /etc/systemd/system/tiny-disp.service

# 2. 修改 ExecStart 行中的 --plugin 参数

# 3. 重新加载配置
sudo systemctl daemon-reload

# 4. 重启服务
sudo systemctl restart tiny-disp
```

## 多实例运行

如果需要同时运行多个插件（使用多个设备）：

1. **创建新的服务文件**
```bash
sudo cp /etc/systemd/system/tiny-disp.service /etc/systemd/system/tiny-disp@2.service
```

2. **编辑新服务文件**
修改插件名称和其他配置

3. **启动多个服务**
```bash
sudo systemctl start tiny-disp
sudo systemctl start tiny-disp@2
```

## 卸载服务

```bash
# 停止服务
sudo systemctl stop tiny-disp

# 禁用服务
sudo systemctl disable tiny-disp

# 删除服务文件
sudo rm /etc/systemd/system/tiny-disp.service

# 重新加载 systemd
sudo systemctl daemon-reload
```

## 开机启动顺序

服务配置为在 `network.target` 之后启动，确保网络服务（如天气、ZFS等插件）可用。

如需修改启动顺序，编辑服务文件中的 `After=` 行：

```ini
[Unit]
After=network.target   # 在网络服务之后
After=multi-user.target  # 在多用户环境之后
```

## 性能优化

### 降低CPU使用

如果服务占用CPU过高：

1. 增加更新间隔（编辑 `.tiny-disp.conf`）
2. 选择更轻量的插件
3. 检查是否有错误导致频繁重试

### 减少日志输出

编辑服务文件，限制日志级别：

```ini
[Service]
StandardOutput=null
StandardError=journal
```

## 安全建议

1. **不要以root用户运行**
   - 服务应该以普通用户权限运行
   - 在服务文件中指定 `User=` 为非root用户

2. **保护配置文件**
```bash
# 配置文件可能包含敏感信息（如密码）
chmod 600 .tiny-disp.conf
```

3. **限制服务权限**
   - 仅授予必要的设备访问权限
   - 使用最小权限原则

## 示例配置

### 示例1: 系统监控服务
```ini
[Unit]
Description=System Metrics Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tiny-disp
ExecStart=/usr/bin/python3 /home/pi/tiny-disp/main.py --plugin "System Metrics"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 示例2: ZFS监控服务（需要sshpass）
```ini
[Unit]
Description=ZFS Pool Monitoring Display
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/opt/tiny-disp
ExecStart=/usr/bin/python3 /opt/tiny-disp/main.py --plugin "ZFS Pool Monitor"
Restart=always
RestartSec=15
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

## 更多帮助

- 查看主README: `README.md`
- 配置文件说明: `.tiny-disp.conf`
- 问题反馈: GitHub Issues
