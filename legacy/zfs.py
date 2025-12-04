#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device TrueNAS ZFS Pool Display
在MSC设备上显示TrueNAS的ZFS存储池信息
运行在Proxmox VE上，通过SSH连接TrueNAS
"""

import serial
import serial.tools.list_ports
import time
import subprocess
import re
from typing import Optional, Dict


# 5x7 bitmap font
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
}


# TrueNAS SSH Configuration
TRUENAS_CONFIG = {
    'host': '10.0.0.129',  # 修改为你的TrueNAS IP
    'user': 'syhan',            # TrueNAS SSH用户
    'password': '',  # TrueNAS SSH密码
    'port': 22,
    'pool_name': 'tank',   # 指定要监控的ZFS pool名称
}


def get_zfs_metrics(ssh_config: Dict) -> Dict:
    """Get ZFS pool metrics from TrueNAS via SSH"""
    try:
        # SSH command to get ZFS pool list (using sshpass for password auth)
        ssh_cmd = [
            'sshpass',
            '-p', ssh_config['password'],
            'ssh',
            '-p', str(ssh_config['port']),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=5',
            f"{ssh_config['user']}@{ssh_config['host']}",
            'zpool list -H -o name,size,alloc,free,cap,health,dedup'
        ]

        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print(f"SSH Error: {result.stderr}")
            return get_default_metrics()

        # Parse ZFS pool data
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[0]:
            return get_default_metrics()

        # Find specified pool by name
        target_pool = ssh_config.get('pool_name', 'tank')
        fields = None
        for line in lines:
            line_fields = line.split('\t')
            if line_fields and line_fields[0] == target_pool:
                fields = line_fields
                break

        # If specified pool not found, return error
        if not fields:
            print(f"Warning: Pool '{target_pool}' not found")
            return get_default_metrics()
        if len(fields) >= 7:
            name = fields[0]
            size = fields[1]  # e.g., "10T"
            alloc = fields[2]  # e.g., "2.5T"
            free = fields[3]   # e.g., "7.5T"
            cap = fields[4].replace('%', '')  # e.g., "25"
            health = fields[5]  # e.g., "ONLINE"
            dedup = fields[6]   # e.g., "1.00x"

            # Get scrub status
            scrub_cmd = [
                'sshpass',
                '-p', ssh_config['password'],
                'ssh',
                '-p', str(ssh_config['port']),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                f"{ssh_config['user']}@{ssh_config['host']}",
                f'zpool status {name} | grep "scan:"'
            ]
            scrub_result = subprocess.run(scrub_cmd, capture_output=True, text=True, timeout=10)
            scrub_status = "NONE"
            if "in progress" in scrub_result.stdout:
                scrub_status = "RUN"
            elif "completed" in scrub_result.stdout:
                scrub_status = "OK"

            return {
                'name': name[:8],  # Limit name length
                'size': size,
                'alloc': alloc,
                'free': free,
                'cap': int(cap) if cap.isdigit() else 0,
                'health': health[:6],  # ONLINE -> ONLINE, DEGRADED -> DEGRAD
                'dedup': dedup,
                'scrub': scrub_status,
                'online': True
            }

    except Exception as e:
        print(f"Error getting ZFS metrics: {e}")

    return get_default_metrics()


def get_default_metrics() -> Dict:
    """Return default metrics when unable to connect"""
    return {
        'name': 'N/A',
        'size': 'N/A',
        'alloc': 'N/A',
        'free': 'N/A',
        'cap': 0,
        'health': 'N/A',
        'dedup': 'N/A',
        'scrub': 'N/A',
        'online': False
    }


def find_msc_device() -> Optional[serial.Serial]:
    """Find and connect to MSC device"""
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


def draw_pixel(ser, x, y, color):
    """Draw a single pixel"""
    cmd = bytearray([2, 0, x // 256, x % 256, y // 256, y % 256])
    ser.write(cmd)
    cmd = bytearray([2, 1, 0, 1, 0, 1])
    ser.write(cmd)
    cmd = bytearray([2, 3, 11, color // 256, color % 256, 0])
    ser.write(cmd)
    time.sleep(0.001)
    ser.read(ser.in_waiting)


def draw_rect(ser, x, y, width, height, color):
    """Draw a filled rectangle"""
    cmd = bytearray([2, 0, x // 256, x % 256, y // 256, y % 256])
    ser.write(cmd)
    cmd = bytearray([2, 1, width // 256, width % 256, height // 256, height % 256])
    ser.write(cmd)
    cmd = bytearray([2, 3, 11, color // 256, color % 256, 0])
    ser.write(cmd)
    time.sleep(0.002)
    ser.read(ser.in_waiting)


def clear_screen(ser, color=0x0000):
    """Clear entire screen - landscape mode (160x80)"""
    draw_rect(ser, 0, 0, 160, 80, color)
    time.sleep(0.08)


def draw_char_bitmap(ser, x, y, char, color, scale=1):
    """Draw a character using 5x7 bitmap font"""
    if char.upper() not in FONT_5X7:
        return x + 6 * scale

    bitmap = FONT_5X7[char.upper()]

    for col in range(5):
        col_data = bitmap[col]
        for row in range(7):
            if col_data & (1 << row):
                if scale == 1:
                    draw_pixel(ser, x + col, y + row, color)
                else:
                    draw_rect(ser, x + col * scale, y + row * scale, scale, scale, color)

    return x + 6 * scale


def draw_text_bitmap(ser, x, y, text, color, scale=1):
    """Draw text string using bitmap font"""
    current_x = x
    for char in text:
        current_x = draw_char_bitmap(ser, current_x, y, char, color, scale)
    return current_x


def display_zfs_metrics(ser, metrics, frame, first_draw=False):
    """Display TrueNAS ZFS metrics - LANDSCAPE MODE"""

    # Matrix green color palette
    BLACK = 0x0000
    DARK_GREEN = 0x0200
    GREEN = 0x07E0
    BRIGHT_GREEN = 0x07E0
    RED = 0xF800  # For warnings
    YELLOW = 0xFFE0  # For degraded status

    # Reset LCD
    cmd = bytearray([2, 3, 10, 0, 0, 0])
    ser.write(cmd)
    time.sleep(0.02)
    ser.read(ser.in_waiting)

    # Only full redraw on first time
    if first_draw:
        clear_screen(ser, BLACK)

        # Draw static labels
        # Left column - Pool info
        draw_text_bitmap(ser, 2, 2, "POOL:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 14, "SIZE:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 26, "USED:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 38, "FREE:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 50, "CAP:", DARK_GREEN, scale=1)

        # Vertical separator
        for y in range(2, 78, 4):
            draw_rect(ser, 76, y, 1, 2, DARK_GREEN)

        # Right column - Status
        draw_text_bitmap(ser, 80, 2, "STAT:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 26, "DEDUP:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 38, "SCRUB:", DARK_GREEN, scale=1)

        # Bottom - Connection
        draw_text_bitmap(ser, 2, 64, "HOST:", DARK_GREEN, scale=1)

    # Send keep-alive
    cmd = bytearray([2, 3, 10, 0, 0, 0])
    ser.write(cmd)
    ser.read(ser.in_waiting)

    # Update dynamic content - Left column

    # Pool name
    draw_rect(ser, 38, 2, 36, 10, BLACK)
    name_color = GREEN if metrics['online'] else RED
    draw_text_bitmap(ser, 38, 2, metrics['name'], name_color, scale=1)

    # Total size
    draw_rect(ser, 38, 14, 36, 10, BLACK)
    draw_text_bitmap(ser, 38, 14, metrics['size'], GREEN, scale=1)

    # Used (allocated)
    draw_rect(ser, 38, 26, 36, 10, BLACK)
    draw_text_bitmap(ser, 38, 26, metrics['alloc'], BRIGHT_GREEN, scale=1)

    # Free space
    draw_rect(ser, 38, 38, 36, 10, BLACK)
    draw_text_bitmap(ser, 38, 38, metrics['free'], GREEN, scale=1)

    # Capacity percentage
    draw_rect(ser, 32, 50, 42, 10, BLACK)
    cap_color = RED if metrics['cap'] >= 90 else (YELLOW if metrics['cap'] >= 80 else GREEN)
    draw_text_bitmap(ser, 32, 50, f"{metrics['cap']}%", cap_color, scale=1)

    # Update Right column

    # Health status
    draw_rect(ser, 116, 2, 42, 10, BLACK)
    health_color = GREEN if metrics['health'] in ['ONLINE', 'N/A'] else (YELLOW if 'DEGRAD' in metrics['health'] else RED)
    draw_text_bitmap(ser, 116, 2, metrics['health'], health_color, scale=1)

    # Dedup ratio
    draw_rect(ser, 122, 26, 36, 10, BLACK)
    draw_text_bitmap(ser, 122, 26, metrics['dedup'], GREEN, scale=1)

    # Scrub status
    draw_rect(ser, 128, 38, 30, 10, BLACK)
    scrub_color = BRIGHT_GREEN if metrics['scrub'] == 'OK' else (YELLOW if metrics['scrub'] == 'RUN' else GREEN)
    draw_text_bitmap(ser, 128, 38, metrics['scrub'], scrub_color, scale=1)

    # Bottom - TrueNAS host
    draw_rect(ser, 38, 64, 120, 10, BLACK)
    host_display = TRUENAS_CONFIG['host']
    status_indicator = "ON" if metrics['online'] else "OFF"
    draw_text_bitmap(ser, 38, 64, f"{host_display} {status_indicator}", GREEN if metrics['online'] else RED, scale=1)

    # Final keep-alive
    cmd = bytearray([2, 3, 10, 0, 0, 0])
    ser.write(cmd)
    ser.read(ser.in_waiting)

    print(f"💾 [ZFS] Pool:{metrics['name']} Cap:{metrics['cap']}% Health:{metrics['health']} Free:{metrics['free']}")


def check_sshpass():
    """Check if sshpass is installed"""
    try:
        result = subprocess.run(['which', 'sshpass'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


def main():
    """Main application"""
    print("="*60)
    print("TrueNAS ZFS Pool Monitor")
    print("="*60)

    # Check if sshpass is installed
    if not check_sshpass():
        print("\n❌ ERROR: sshpass is not installed!")
        print("\nPlease install sshpass first:")
        print("  On Debian/Ubuntu/Proxmox VE:")
        print("    apt update && apt install sshpass -y")
        print("\n  On macOS:")
        print("    brew install sshpass")
        print("\n  On other systems:")
        print("    Use your package manager to install sshpass")
        return

    print("\n💚 Connecting to TrueNAS ZFS storage...")
    print(f"Host: {TRUENAS_CONFIG['host']}")
    print(f"User: {TRUENAS_CONFIG['user']}")
    print()

    # Test SSH connection first
    print("Testing SSH connection...")
    test_metrics = get_zfs_metrics(TRUENAS_CONFIG)
    if not test_metrics['online']:
        print("⚠️  WARNING: Cannot connect to TrueNAS!")
        print("Please check:")
        print(f"  1. TrueNAS host: {TRUENAS_CONFIG['host']}")
        print(f"  2. SSH username: {TRUENAS_CONFIG['user']}")
        print(f"  3. SSH password is correct")
        print("  4. sshpass is installed: apt install sshpass")
        print("\nContinuing with offline display...\n")
    else:
        print(f"✓ Connected to TrueNAS")
        print(f"✓ Found pool: {test_metrics['name']}")
        print()

    ser = find_msc_device()
    if not ser:
        print("✗ MSC Device not found!")
        return

    # Set LCD orientation to landscape
    cmd = bytearray([2, 3, 10, 0, 0, 0])
    ser.write(cmd)
    time.sleep(0.1)
    ser.read(ser.in_waiting)

    print("✓ MSC Device ready")
    print("✓ Screen: 160x80 pixels (landscape)")
    print("\nUpdating every 15 seconds (keep-alive every 3s). Press Ctrl+C to exit.\n")

    try:
        frame = 0
        first = True
        update_interval = 15  # Update ZFS metrics every 15 seconds
        keepalive_interval = 3  # Keep-alive every 3 seconds

        while True:
            # Get and display metrics
            metrics = get_zfs_metrics(TRUENAS_CONFIG)
            display_zfs_metrics(ser, metrics, frame, first_draw=first)
            first = False
            frame += 1

            # Wait with periodic keep-alives
            elapsed = 0
            while elapsed < update_interval:
                time.sleep(keepalive_interval)
                elapsed += keepalive_interval

                # Keep-alive command
                cmd = bytearray([2, 3, 10, 0, 0, 0])
                ser.write(cmd)
                ser.read(ser.in_waiting)

    except KeyboardInterrupt:
        print("\n\n💾 Exiting TrueNAS monitor...")

    finally:
        ser.close()
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
