# Tiny Display - Docker 部署指南

## 📦 Docker 镜像特性

### 镜像优化
- ✅ **多阶段构建** - 分离构建和运行环境
- ✅ **Alpine Linux** - 最小化基础镜像（~50MB）
- ✅ **虚拟环境** - 隔离Python依赖
- ✅ **非root用户** - 安全性增强
- ✅ **精简依赖** - 仅安装必要运行时依赖

### 预期镜像大小
- 基础镜像: ~50MB (python:3.11-alpine)
- Python依赖: ~20-30MB
- 应用代码: <1MB
- **总计: 约80-100MB**

## 🚀 快速开始

### 方式1: 使用 Docker Compose（推荐）

```bash
# 1. 准备配置文件
cp .tiny-disp.conf.sample .tiny-disp.conf
nano .tiny-disp.conf

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 方式2: 直接使用 Docker

```bash
# 1. 构建镜像
docker build -t tiny-disp:latest .

# 2. 运行容器
docker run -d \
  --name tiny-disp \
  --privileged \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  -v $(pwd)/.tiny-disp.conf:/app/.tiny-disp.conf:ro \
  -e TZ=Asia/Shanghai \
  tiny-disp:latest \
  python3 main.py --plugin "System Metrics"

# 3. 查看日志
docker logs -f tiny-disp

# 4. 停止容器
docker stop tiny-disp
docker rm tiny-disp
```

## 🔧 配置说明

### USB 设备映射

不同系统的设备路径不同：

```yaml
# Linux
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0
  - /dev/ttyACM0:/dev/ttyACM0

# macOS
devices:
  - /dev/cu.usbmodem01234567891:/dev/cu.usbmodem01234567891
```

### 查找USB设备

```bash
# Linux
ls /dev/tty*

# macOS
ls /dev/cu.*

# 或使用 dmesg 查看设备连接信息
dmesg | grep tty
```

### 环境变量

在 `docker-compose.yml` 中配置：

```yaml
environment:
  - PYTHONUNBUFFERED=1         # Python输出不缓冲
  - TZ=Asia/Shanghai           # 时区设置
  - PLUGIN_NAME=System Metrics # 指定运行的插件（名称）
  # 或使用插件索引
  # - PLUGIN_INDEX=2           # 指定运行的插件（索引）
  # 留空则进入交互模式
```

**插件选择方式：**

1. **使用插件名称** (推荐):
   ```yaml
   - PLUGIN_NAME=World Clock
   - PLUGIN_NAME=System Metrics
   - PLUGIN_NAME=ZFS Pool Monitor
   ```

2. **使用插件索引**:
   ```yaml
   - PLUGIN_INDEX=0  # World Clock
   - PLUGIN_INDEX=2  # System Metrics
   - PLUGIN_INDEX=4  # ZFS Pool Monitor
   ```

3. **交互模式** (留空或注释掉):
   ```yaml
   # - PLUGIN_NAME=
   # - PLUGIN_INDEX=
   ```

### 卷挂载

```yaml
volumes:
  # 配置文件（只读）
  - ./.tiny-disp.conf:/app/.tiny-disp.conf:ro

  # 日志目录（可选）
  - ./logs:/app/logs

  # 自定义插件（可选）
  - ./custom-plugins:/app/plugins
```

## 🎯 运行模式

### 1. 交互模式（开发/调试）

```bash
# 进入容器交互式运行
docker run -it --rm \
  --privileged \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  -v $(pwd)/.tiny-disp.conf:/app/.tiny-disp.conf:ro \
  tiny-disp:latest \
  python3 main.py
```

### 2. 指定插件模式（生产）

```bash
# 运行特定插件
docker run -d \
  --name tiny-disp \
  --privileged \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  -v $(pwd)/.tiny-disp.conf:/app/.tiny-disp.conf:ro \
  tiny-disp:latest \
  python3 main.py --plugin "World Clock"
```

### 3. 列出可用插件

```bash
docker run --rm \
  --privileged \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  tiny-disp:latest \
  python3 main.py --list
```

## 📊 管理命令

### 镜像管理

```bash
# 构建镜像
docker build -t tiny-disp:latest .

# 查看镜像大小
docker images tiny-disp

# 清理未使用的镜像
docker image prune

# 重新构建（无缓存）
docker build --no-cache -t tiny-disp:latest .
```

### 容器管理

```bash
# 启动容器
docker-compose up -d

# 停止容器
docker-compose down

# 重启容器
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器shell
docker-compose exec tiny-disp sh
```

### 调试命令

```bash
# 查看容器详细信息
docker inspect tiny-disp

# 查看容器资源使用
docker stats tiny-disp

# 查看容器进程
docker top tiny-disp

# 复制文件到容器
docker cp file.txt tiny-disp:/app/

# 复制文件从容器
docker cp tiny-disp:/app/file.txt .
```

## 🔍 故障排查

### 问题1: 找不到USB设备

```bash
# 1. 确认设备路径
ls /dev/tty*

# 2. 检查设备权限
ls -l /dev/ttyUSB0

# 3. 添加用户到dialout组（Linux）
sudo usermod -aG dialout $USER

# 4. 重新登录或重启
```

### 问题2: 权限拒绝

```bash
# 使用 --privileged 模式
docker run --privileged ...

# 或添加特定权限
docker run --cap-add=SYS_ADMIN ...
```

### 问题3: 配置文件未生效

```bash
# 1. 检查挂载路径
docker inspect tiny-disp | grep Mounts -A 10

# 2. 确认配置文件存在
ls -l .tiny-disp.conf

# 3. 重新挂载
docker-compose down
docker-compose up -d
```

### 问题4: 镜像太大

```bash
# 查看镜像层级
docker history tiny-disp:latest

# 清理构建缓存
docker builder prune

# 使用 dive 分析镜像
dive tiny-disp:latest
```

## 🎨 自定义配置

### 修改插件

**方式1: 使用环境变量** (推荐):

编辑 `docker-compose.yml`:

```yaml
environment:
  - PLUGIN_NAME=World Clock    # 修改为要运行的插件
  # 或使用索引
  # - PLUGIN_INDEX=0
```

**方式2: 使用配置文件**:

编辑 `.tiny-disp.conf`:

```ini
[general]
default_plugin = World Clock
```

然后重启容器：
```bash
docker-compose restart
```

**可用插件列表：**

| 索引 | 插件名称 | 说明 |
|------|---------|------|
| 0 | World Clock | 世界时钟 |
| 1 | Weather | 天气显示 |
| 2 | System Metrics | 系统指标 |
| 3 | System Metrics (Rotated) | 系统指标（旋转） |
| 4 | ZFS Pool Monitor | ZFS池监控 |
| 5 | ZFS Pool Monitor (Pages) | ZFS池监控（多页） |

**查看完整插件列表：**
```bash
docker-compose run --rm tiny-disp python3 main.py --list
```

### 修改时区

```yaml
environment:
  - TZ=America/New_York  # 美国东部
  - TZ=Europe/London     # 英国伦敦
  - TZ=Asia/Tokyo        # 日本东京
```

### 添加自定义插件

1. 创建插件文件夹
2. 挂载到容器

```yaml
volumes:
  - ./my-plugins:/app/plugins/custom
```

## 🚢 生产部署

### Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.yml tiny-disp

# 查看服务
docker service ls

# 删除服务
docker stack rm tiny-disp
```

### Kubernetes

创建 `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tiny-disp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tiny-disp
  template:
    metadata:
      labels:
        app: tiny-disp
    spec:
      containers:
      - name: tiny-disp
        image: tiny-disp:latest
        securityContext:
          privileged: true
        volumeMounts:
        - name: config
          mountPath: /app/.tiny-disp.conf
          subPath: .tiny-disp.conf
        - name: usb-device
          mountPath: /dev/ttyUSB0
      volumes:
      - name: config
        configMap:
          name: tiny-disp-config
      - name: usb-device
        hostPath:
          path: /dev/ttyUSB0
```

## 📈 性能优化

### 减小镜像大小

1. **多阶段构建** - 已实现
2. **Alpine基础镜像** - 已使用
3. **精简依赖** - 仅安装必要包
4. **清理缓存** - 删除apk缓存

### 优化启动时间

```dockerfile
# 预编译Python文件
RUN python -m compileall /app
```

### 资源限制

```yaml
services:
  tiny-disp:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

## ✅ 最佳实践

1. **使用配置文件** - 不要硬编码配置
2. **挂载配置** - 配置文件作为只读卷挂载
3. **日志管理** - 配置日志轮转
4. **健康检查** - 添加容器健康检查
5. **版本标签** - 使用明确的版本标签
6. **非root用户** - 已在Dockerfile中实现
7. **最小权限** - 仅授予必要的权限

## 📚 参考资源

- [Docker官方文档](https://docs.docker.com/)
- [Alpine Linux](https://alpinelinux.org/)
- [多阶段构建](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose](https://docs.docker.com/compose/)

---

更新日期：2024-12-04
