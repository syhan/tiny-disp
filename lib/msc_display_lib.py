#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Display Library - Shared Module
提供MSC设备的通用显示功能
"""

import serial
import serial.tools.list_ports
import time
from typing import Optional

# 5x7 bitmap font - 共享字体定义
FONT_5X7 = {
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    'A': [0x7E, 0x09, 0x09, 0x09, 0x7E],
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    '%': [0x23, 0x13, 0x08, 0x64, 0x62],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
    '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
}


# Color constants (RGB565 format)
class Colors:
    """RGB565 color constants"""
    BLACK = 0x0000
    WHITE = 0xFFFF
    RED = 0xF800
    GREEN = 0x07E0
    BLUE = 0x001F
    YELLOW = 0xFFE0
    CYAN = 0x07FF
    MAGENTA = 0xF81F
    ORANGE = 0xFD20
    DARK_GREEN = 0x0200
    BRIGHT_GREEN = 0x07E0
    LIME = 0x07E0


def find_msc_device() -> Optional[serial.Serial]:
    """
    Find and connect to MSC device

    Returns:
        serial.Serial: Connected serial port or None if not found
    """
    port_list = list(serial.tools.list_ports.comports())

    for port_info in port_list:
        try:
            port_path = port_info.device
            ser = serial.Serial(port_path, 19200, timeout=2)
            time.sleep(0.25)

            recv = ser.read(ser.in_waiting)
            if recv:
                recv_str = recv.decode("gbk", errors="ignore")
                if "MSN" in recv_str:
                    ser.write(b'\x00MSNCN')
                    time.sleep(0.25)
                    confirm = ser.read(ser.in_waiting).decode("gbk", errors="ignore")
                    if "MSNCN" in confirm:
                        print(f"✓ Connected: {port_path}")
                        return ser
            ser.close()
        except:
            continue

    return None


def wait_for_msc_device(retry_interval: int = 5, silent: bool = False) -> serial.Serial:
    """
    Wait for MSC device to connect (blocking)

    Args:
        retry_interval: Seconds to wait between connection attempts
        silent: If True, don't print initial waiting message

    Returns:
        serial.Serial: Connected serial port
    """
    if not silent:
        print("⏳ Waiting for MSC device...")
    while True:
        ser = find_msc_device()
        if ser:
            return ser
        print(f"   Device not found, retrying in {retry_interval} seconds...")
        time.sleep(retry_interval)


def is_device_connected(ser) -> bool:
    """
    Check if device is still connected

    Args:
        ser: Serial connection to check

    Returns:
        bool: True if connected, False otherwise
    """
    try:
        # Try to send a keep-alive command
        send_keep_alive(ser)
        return True
    except:
        return False


def send_keep_alive(ser):
    """Send keep-alive command to prevent screensaver"""
    cmd = bytearray([2, 3, 10, 0, 0, 0])
    ser.write(cmd)
    time.sleep(0.001)
    ser.read(ser.in_waiting)


def wake_from_screensaver(ser):
    """Wake device from screensaver by sending multiple keep-alive commands"""
    for _ in range(3):
        cmd = bytearray([2, 3, 10, 0, 0, 0])
        ser.write(cmd)
        time.sleep(0.01)
        ser.read(ser.in_waiting)


def draw_pixel(ser, x, y, color):
    """
    Draw a single pixel

    Args:
        ser: Serial connection
        x: X coordinate
        y: Y coordinate
        color: RGB565 color value
    """
    cmd = bytearray([2, 0, x // 256, x % 256, y // 256, y % 256])
    ser.write(cmd)
    cmd = bytearray([2, 1, 0, 1, 0, 1])
    ser.write(cmd)
    cmd = bytearray([2, 3, 11, color // 256, color % 256, 0])
    ser.write(cmd)
    time.sleep(0.001)
    ser.read(ser.in_waiting)


def draw_rect(ser, x, y, width, height, color):
    """
    Draw a filled rectangle

    Args:
        ser: Serial connection
        x: X coordinate
        y: Y coordinate
        width: Rectangle width
        height: Rectangle height
        color: RGB565 color value
    """
    cmd = bytearray([2, 0, x // 256, x % 256, y // 256, y % 256])
    ser.write(cmd)
    cmd = bytearray([2, 1, width // 256, width % 256, height // 256, height % 256])
    ser.write(cmd)
    cmd = bytearray([2, 3, 11, color // 256, color % 256, 0])
    ser.write(cmd)
    time.sleep(0.002)
    ser.read(ser.in_waiting)


def clear_screen(ser, color=0x0000):
    """
    Clear entire screen

    Args:
        ser: Serial connection
        color: RGB565 color value (default: black)
    """
    draw_rect(ser, 0, 0, 160, 80, color)
    time.sleep(0.08)


def rotate_bitmap_90(bitmap):
    """
    Rotate a 5x7 bitmap 90 degrees clockwise to become 7x5

    Args:
        bitmap: List of 5 bytes representing 5x7 bitmap

    Returns:
        List of 7 bytes representing rotated 7x5 bitmap
    """
    rotated = []
    for row in range(7):
        new_byte = 0
        for col in range(5):
            if bitmap[col] & (1 << row):
                new_byte |= (1 << (4 - col))
        rotated.append(new_byte)
    return rotated


def draw_char_bitmap(ser, x, y, char, color, scale=1, rotated=False):
    """
    Draw a character using 5x7 bitmap font

    Args:
        ser: Serial connection
        x: X coordinate
        y: Y coordinate
        char: Character to draw
        color: RGB565 color value
        scale: Scale factor (default: 1)
        rotated: If True, rotate 90 degrees clockwise (default: False)

    Returns:
        Next x or y coordinate after character
    """
    if char.upper() not in FONT_5X7:
        if rotated:
            return y + 8 * scale
        else:
            return x + 6 * scale

    bitmap = FONT_5X7[char.upper()]

    if rotated:
        rotated_bitmap = rotate_bitmap_90(bitmap)
        for col in range(7):
            col_data = rotated_bitmap[col]
            for row in range(5):
                if col_data & (1 << row):
                    if scale == 1:
                        draw_pixel(ser, x + col, y + row, color)
                    else:
                        draw_rect(ser, x + col * scale, y + row * scale, scale, scale, color)
        return y + 8 * scale
    else:
        for col in range(5):
            col_data = bitmap[col]
            for row in range(7):
                if col_data & (1 << row):
                    if scale == 1:
                        draw_pixel(ser, x + col, y + row, color)
                    else:
                        draw_rect(ser, x + col * scale, y + row * scale, scale, scale, color)
        return x + 6 * scale


def draw_text_bitmap(ser, x, y, text, color, scale=1, rotated=False):
    """
    Draw text string using bitmap font

    Args:
        ser: Serial connection
        x: X coordinate
        y: Y coordinate
        text: Text string to draw
        color: RGB565 color value
        scale: Scale factor (default: 1)
        rotated: If True, rotate 90 degrees clockwise (default: False)

    Returns:
        Next x or y coordinate after text
    """
    if rotated:
        current_y = y
        for char in reversed(text):
            current_y = draw_char_bitmap(ser, x, current_y, char, color, scale, rotated=True)
        return current_y
    else:
        current_x = x
        for char in text:
            current_x = draw_char_bitmap(ser, current_x, y, char, color, scale, rotated=False)
        return current_x


class MSCDisplay:
    """High-level MSC display interface"""

    def __init__(self, ser):
        """
        Initialize MSC display

        Args:
            ser: Serial connection to MSC device
        """
        self.ser = ser
        self.reset_lcd()

    def reset_lcd(self):
        """Reset LCD to default state"""
        send_keep_alive(self.ser)
        time.sleep(0.02)

    def set_orientation(self, landscape=True):
        """
        Set screen orientation

        Args:
            landscape: True for landscape, False for portrait
        """
        cmd = bytearray([2, 3, 10, 0, 0, 0])
        self.ser.write(cmd)
        time.sleep(0.1)
        self.ser.read(self.ser.in_waiting)

    def clear(self, color=Colors.BLACK):
        """Clear screen with specified color"""
        clear_screen(self.ser, color)

    def draw_pixel(self, x, y, color):
        """Draw a pixel"""
        draw_pixel(self.ser, x, y, color)

    def draw_rect(self, x, y, width, height, color):
        """Draw a filled rectangle"""
        draw_rect(self.ser, x, y, width, height, color)

    def draw_text(self, x, y, text, color, scale=1, rotated=False):
        """Draw text"""
        return draw_text_bitmap(self.ser, x, y, text, color, scale, rotated)

    def draw_char(self, x, y, char, color, scale=1, rotated=False):
        """Draw a single character"""
        return draw_char_bitmap(self.ser, x, y, char, color, scale, rotated)

    def keep_alive(self):
        """Send keep-alive command"""
        send_keep_alive(self.ser)
