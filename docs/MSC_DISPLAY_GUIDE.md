# MSC 显示设备开发指南

## 📖 概述

本文档详细介绍如何连接和控制 MSC (Mass Storage Class) 显示设备，以及如何通过位图方式在不同方向上正确显示文字和图形。

## 🔌 设备连接

### 1. 硬件连接

MSC显示设备通过USB连接到计算机：

```
Computer USB Port  <---USB Cable--->  MSC Display Device
     (Host)                              (Peripheral)
```

### 2. 设备识别

```python
import serial
import serial.tools.list_ports

def find_msc_device():
    """查找MSC显示设备"""
    # 扫描所有串口
    ports = serial.tools.list_ports.comports()

    for port in ports:
        # 检查设备描述
        if "MSC" in port.description or "USB Serial" in port.description:
            return port.device

    return None

# 使用示例
device_path = find_msc_device()
print(f"Found device: {device_path}")
# Linux: /dev/ttyUSB0
# macOS: /dev/cu.usbmodem01234567891
# Windows: COM3
```

### 3. 打开连接

```python
import serial

def connect_device(port, baudrate=115200):
    """连接到MSC设备"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        return ser
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

# 使用示例
ser = connect_device('/dev/ttyUSB0')
if ser:
    print("Connected successfully!")
```

## 📺 显示屏幕信息

### 屏幕规格

```
┌─────────────────────────────┐
│                             │  Standard Mode (横屏)
│                             │  Width:  160 pixels
│                             │  Height: 80 pixels
│                             │
└─────────────────────────────┘

┌──────────┐
│          │  Rotated Mode (竖屏 90°)
│          │  Width:  80 pixels  (原height)
│          │  Height: 160 pixels (原width)
│          │
│          │
│          │
│          │
└──────────┘
```

### 坐标系统

#### 标准模式 (0°)
```
(0,0)────────────────────(159,0)
  │                          │
  │                          │
  │        Screen            │
  │                          │
  │                          │
(0,79)───────────────────(159,79)
```

#### 旋转模式 (90°)
```
(0,0)──────(79,0)
  │            │
  │            │
  │   Screen   │
  │            │
  │            │
  │            │
  │            │
(0,159)────(79,159)
```

## 🎨 位图显示原理

### 1. 像素格式

MSC设备使用 **RGB565** 颜色格式：

```
16-bit color (RGB565):
┌─────────┬──────────┬─────────┐
│ 5 bits  │ 6 bits   │ 5 bits  │
│   RED   │  GREEN   │  BLUE   │
└─────────┴──────────┴─────────┘

常用颜色定义:
RED     = 0xF800  (11111 000000 00000)
GREEN   = 0x07E0  (00000 111111 00000)
BLUE    = 0x001F  (00000 000000 11111)
WHITE   = 0xFFFF  (11111 111111 11111)
BLACK   = 0x0000  (00000 000000 00000)
YELLOW  = 0xFFE0  (11111 111111 00000)
CYAN    = 0x07FF  (00000 111111 11111)
MAGENTA = 0xF81F  (11111 000000 11111)
```

### 2. 绘制区域设置

```python
def set_drawing_area(ser, x, y, width, height):
    """设置绘制区域"""
    # 命令格式: 0xA5, x_start, y_start, x_end, y_end
    x_end = x + width - 1
    y_end = y + height - 1

    cmd = bytes([
        0xA5,           # 命令头
        x >> 8, x & 0xFF,         # X起始 (高字节, 低字节)
        y >> 8, y & 0xFF,         # Y起始
        x_end >> 8, x_end & 0xFF, # X结束
        y_end >> 8, y_end & 0xFF  # Y结束
    ])

    ser.write(cmd)
```

### 3. 填充颜色

```python
def fill_area(ser, x, y, width, height, color):
    """填充矩形区域"""
    # 设置绘制区域
    set_drawing_area(ser, x, y, width, height)

    # 准备像素数据
    pixel_count = width * height
    color_high = (color >> 8) & 0xFF
    color_low = color & 0xFF

    # 发送像素数据
    data = bytes([color_high, color_low] * pixel_count)
    ser.write(data)

# 使用示例
fill_area(ser, 0, 0, 160, 80, 0xF800)  # 填充整个屏幕为红色
```

## 📝 文字显示

### 1. 字体位图

每个字符使用位图表示：

```
字符 'A' (8x16 像素)
Bitmap (每bit代表一个像素):

  01111000  (0x78)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  11111100  (0xFC)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  11001100  (0xCC)
  00000000  (0x00)
  00000000  (0x00)
  00000000  (0x00)
  00000000  (0x00)

1 = 前景色 (文字)
0 = 背景色 (透明或背景)
```

### 2. 标准方向显示文字

```python
def draw_char_normal(ser, x, y, char, fg_color, bg_color):
    """
    标准方向显示字符

    Args:
        x, y: 起始坐标
        char: 字符
        fg_color: 前景色 (RGB565)
        bg_color: 背景色 (RGB565)
    """
    # 获取字符位图 (假设8x16)
    bitmap = get_char_bitmap(char)  # 返回16个字节
    char_width = 8
    char_height = 16

    # 设置绘制区域
    set_drawing_area(ser, x, y, char_width, char_height)

    # 准备像素数据
    pixels = []
    for row in range(char_height):
        byte = bitmap[row]
        for col in range(char_width):
            # 检查该位是否为1
            if byte & (0x80 >> col):
                # 前景色
                pixels.append((fg_color >> 8) & 0xFF)
                pixels.append(fg_color & 0xFF)
            else:
                # 背景色
                pixels.append((bg_color >> 8) & 0xFF)
                pixels.append(bg_color & 0xFF)

    # 发送像素数据
    ser.write(bytes(pixels))

# 使用示例
draw_char_normal(ser, 10, 10, 'A', 0xFFFF, 0x0000)
```

**显示效果：**
```
屏幕 (标准方向):
┌─────────────────────┐
│                     │
│      A              │  字符正常显示
│                     │
└─────────────────────┘
```

### 3. 旋转90°显示文字

旋转显示需要变换坐标：

```python
def draw_char_rotated_90(ser, x, y, char, fg_color, bg_color):
    """
    旋转90度显示字符 (逆时针)

    坐标变换:
    原始 (col, row) → 旋转后 (x - row, y + col)
    """
    bitmap = get_char_bitmap(char)
    char_width = 8
    char_height = 16

    # 旋转后的尺寸对调
    rotated_width = char_height   # 16
    rotated_height = char_width    # 8

    # 为旋转后的字符准备像素阵列
    pixels = [[0] * rotated_width for _ in range(rotated_height)]

    # 读取原始位图并旋转
    for row in range(char_height):
        byte = bitmap[row]
        for col in range(char_width):
            if byte & (0x80 >> col):
                # 坐标变换: (col, row) -> (row, width-1-col)
                # 逆时针90度
                new_col = row
                new_row = char_width - 1 - col
                pixels[new_row][new_col] = fg_color
            else:
                new_col = row
                new_row = char_width - 1 - col
                pixels[new_row][new_col] = bg_color

    # 设置绘制区域
    set_drawing_area(ser, x, y, rotated_width, rotated_height)

    # 发送像素数据
    data = []
    for row in pixels:
        for color in row:
            data.append((color >> 8) & 0xFF)
            data.append(color & 0xFF)

    ser.write(bytes(data))

# 使用示例
draw_char_rotated_90(ser, 10, 10, 'A', 0xFFFF, 0x0000)
```

**显示效果：**
```
屏幕 (旋转模式):
┌──────┐
│      │
│  <   │  字符旋转90度
│  │   │  从右向左读
│  A   │
│      │
│      │
└──────┘
```

### 4. 旋转变换详解

```
原始字符 'A':          旋转90°后:

  ●●●●●○○○            ○○○○○○○○○○○○○○●●
  ●●○○●●○○            ○○○○○○○○○○○○●●○○
  ●●○○●●○○            ○○○○○○○○○○○○●●○○
  ●●○○●●○○            ○○○○○○○○○○○○●●○○
  ●●●●●●○○            ○○○○○○○○○○○○●●○○
  ●●○○●●○○     →      ○○○○○○○○○○○○●●○○
  ●●○○●●○○            ○○○○○○○○○○○○●●○○
  ●●○○●●○○            ●●●●●●●●●●●●●●●●
  ...                  (8行 × 16列)
  (16行 × 8列)

变换公式:
  新坐标 = (原y, 宽度-1-原x)

逆时针90°: (x,y) → (y, width-1-x)
顺时针90°: (x,y) → (height-1-y, x)
180°旋转:  (x,y) → (width-1-x, height-1-y)
```

## 🖼️ 完整示例

### 示例1: 显示横屏文本

```python
def display_text_landscape(ser, text, x, y):
    """横屏显示文本"""
    cursor_x = x
    for char in text:
        draw_char_normal(ser, cursor_x, y, char, 0xFFFF, 0x0000)
        cursor_x += 8  # 字符宽度

    return cursor_x

# 使用
display_text_landscape(ser, "HELLO", 10, 30)
```

**效果:**
```
┌─────────────────────────────┐
│                             │
│     HELLO                   │
│                             │
└─────────────────────────────┘
```

### 示例2: 显示竖屏文本

```python
def display_text_portrait(ser, text, x, y):
    """竖屏显示文本(旋转90度)"""
    cursor_y = y
    for char in text:
        draw_char_rotated_90(ser, x, cursor_y, char, 0xFFFF, 0x0000)
        cursor_y += 16  # 旋转后的字符高度

    return cursor_y

# 使用
display_text_portrait(ser, "HELLO", 30, 10)
```

**效果:**
```
┌──────────┐
│          │
│    H     │
│    E     │
│    L     │
│    L     │
│    O     │
│          │
│          │
└──────────┘
```

### 示例3: 多行文本

```python
def display_multiline_text(ser, lines, x, y, line_spacing=20):
    """显示多行文本"""
    current_y = y
    for line in lines:
        display_text_landscape(ser, line, x, current_y)
        current_y += line_spacing

# 使用
lines = [
    "Line 1",
    "Line 2",
    "Line 3"
]
display_multiline_text(ser, lines, 10, 10)
```

**效果:**
```
┌─────────────────────────────┐
│                             │
│     Line 1                  │
│     Line 2                  │
│     Line 3                  │
│                             │
└─────────────────────────────┘
```

## 🎯 实际应用示例

### 时钟显示（横屏）

```python
def display_clock_landscape(ser):
    """横屏时钟显示"""
    from datetime import datetime

    # 清屏
    fill_area(ser, 0, 0, 160, 80, 0x0000)

    # 获取时间
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    # 显示时间 (大字体, 居中)
    display_text_landscape(ser, time_str, 35, 25)

    # 显示日期 (小字体, 下方)
    display_text_landscape(ser, date_str, 25, 50)

# 效果:
# ┌─────────────────────────────┐
# │                             │
# │       14:35:20              │
# │      2024-12-04             │
# │                             │
# └─────────────────────────────┘
```

### 时钟显示（竖屏）

```python
def display_clock_portrait(ser):
    """竖屏时钟显示"""
    from datetime import datetime

    # 清屏
    fill_area(ser, 0, 0, 80, 160, 0x0000)

    # 获取时间
    now = datetime.now()
    time_str = now.strftime("%H:%M")

    # 显示时间 (旋转90度)
    display_text_portrait(ser, time_str, 30, 40)

# 效果:
# ┌──────────┐
# │          │
# │    1     │
# │    4     │
# │    :     │
# │    3     │
# │    5     │
# │          │
# └──────────┘
```

## 💡 最佳实践

### 1. 性能优化

```python
# ❌ 不好 - 每个像素单独发送
for y in range(height):
    for x in range(width):
        draw_pixel(ser, x, y, color)

# ✅ 好 - 批量发送整个区域
fill_area(ser, 0, 0, width, height, color)
```

### 2. 缓冲区使用

```python
def create_buffer(width, height, bg_color):
    """创建帧缓冲区"""
    return [[bg_color] * width for _ in range(height)]

def draw_to_buffer(buffer, x, y, color):
    """在缓冲区绘制"""
    buffer[y][x] = color

def flush_buffer(ser, buffer):
    """将缓冲区刷新到屏幕"""
    height = len(buffer)
    width = len(buffer[0])

    set_drawing_area(ser, 0, 0, width, height)

    data = []
    for row in buffer:
        for color in row:
            data.append((color >> 8) & 0xFF)
            data.append(color & 0xFF)

    ser.write(bytes(data))
```

### 3. 防闪烁

```python
def update_display(ser, new_content):
    """防闪烁更新"""
    # 1. 在缓冲区准备新内容
    buffer = create_buffer(160, 80, 0x0000)
    draw_content_to_buffer(buffer, new_content)

    # 2. 一次性刷新整个屏幕
    flush_buffer(ser, buffer)
```

### 4. 错误处理

```python
def safe_draw(ser, draw_function, *args, **kwargs):
    """安全绘制，带重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            draw_function(ser, *args, **kwargs)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Draw failed after {max_retries} attempts: {e}")
                return False
            time.sleep(0.1)
```

## 📊 调试技巧

### 1. 可视化位图

```python
def print_bitmap(bitmap):
    """打印位图用于调试"""
    for byte in bitmap:
        binary = format(byte, '08b')
        visual = binary.replace('1', '█').replace('0', '░')
        print(visual)

# 示例
bitmap = get_char_bitmap('A')
print_bitmap(bitmap)
# 输出:
# ░███████░
# ██░░░░██
# ██░░░░██
# ...
```

### 2. 颜色测试

```python
def test_colors(ser):
    """测试所有基本颜色"""
    colors = {
        'RED': 0xF800,
        'GREEN': 0x07E0,
        'BLUE': 0x001F,
        'WHITE': 0xFFFF,
        'YELLOW': 0xFFE0,
        'CYAN': 0x07FF,
        'MAGENTA': 0xF81F
    }

    y = 0
    for name, color in colors.items():
        fill_area(ser, 0, y, 160, 10, color)
        y += 10
```

### 3. 坐标系统验证

```python
def draw_coordinate_grid(ser):
    """绘制坐标网格"""
    # 绘制垂直线
    for x in range(0, 160, 20):
        draw_vertical_line(ser, x, 0, 80, 0x07E0)

    # 绘制水平线
    for y in range(0, 80, 20):
        draw_horizontal_line(ser, 0, y, 160, 0x07E0)

    # 标记原点
    fill_area(ser, 0, 0, 5, 5, 0xF800)
```

## 🔗 参考资源

### 字体资源
- [GNU Unifont](http://unifoundry.com/unifont/) - 免费位图字体
- [Terminus Font](http://terminus-font.sourceforge.net/) - 等宽字体
- [Pixelated Font Generator](https://www.pentacom.jp/pentacom/bitfontmaker2/) - 在线位图字体工具

### 工具推荐
- **Image2LCD** - 图片转位图数组
- **LCD Assistant** - 位图字体生成器
- **GIMP** - 图像处理和位图创建

### 相关协议
- USB CDC (Communications Device Class)
- RGB565 颜色格式规范

---

更新日期：2024-12-04
作者：Tiny Display Project
