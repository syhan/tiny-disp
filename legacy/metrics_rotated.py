#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device System Metrics Display - Matrix Style (90° Rotated - Portrait Mode)
黑客帝国风格的系统指标显示 (90度旋转 - 竖屏模式)
"""

import time
import psutil
import socket

# Import shared MSC display library
from msc_display_lib import (
    wait_for_msc_device,
    is_device_connected,
    MSCDisplay,
    Colors,
    draw_text_bitmap,
    draw_rect,
    clear_screen,
    send_keep_alive
)


def get_system_metrics():
    """Get current system metrics"""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Get network stats
    net = psutil.net_io_counters()

    # Get system load (1 min average)
    try:
        load = psutil.getloadavg()[0]  # 1-minute load average
    except:
        load = 0.0

    # Get process count
    proc_count = len(psutil.pids())

    # Get uptime in hours
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = int(uptime_seconds / 3600)
    except:
        uptime_hours = 0

    # Get current date
    from datetime import datetime
    current_date = datetime.now().strftime("%m/%d")

    # Get memory available in GB
    mem_avail_gb = mem.available // (1024**3)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "0.0.0.0"

    return {
        'cpu': int(cpu),
        'mem': int(mem.percent),
        'disk': int(disk.percent),
        'ip': ip,
        'load': f"{load:.1f}",
        'procs': proc_count,
        'uptime': uptime_hours,
        'net_sent': net.bytes_sent,
        'net_recv': net.bytes_recv,
        'date': current_date,
        'mem_avail': mem_avail_gb
    }


def display_metrics_matrix_style(ser, metrics, frame, first_draw=False):
    """Display system metrics with Matrix movie style - ROTATED 90° LAYOUT (160x80 landscape)"""

    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    LIME = Colors.LIME

    # Only full redraw on first time
    if first_draw:
        # Clear to black (pure black background)
        clear_screen(ser, BLACK)

        # One info per row layout - labels on left (high y), values on right (low y)
        # When physically rotated 90° clockwise, labels appear on left, values on right

        # Row 1 (x=2): CPU
        draw_text_bitmap(ser, 2, 48, "CPU:", DARK_GREEN, scale=1, rotated=True)

        # Row 2 (x=16): Memory
        draw_text_bitmap(ser, 16, 48, "MEM:", DARK_GREEN, scale=1, rotated=True)

        # Row 3 (x=30): Disk
        draw_text_bitmap(ser, 30, 48, "DSK:", DARK_GREEN, scale=1, rotated=True)

        # Row 4 (x=44): Load
        draw_text_bitmap(ser, 44, 42, "LOAD:", DARK_GREEN, scale=1, rotated=True)

        # Row 5 (x=58): Process
        draw_text_bitmap(ser, 58, 42, "PROC:", DARK_GREEN, scale=1, rotated=True)

        # Row 6 (x=72): TX
        draw_text_bitmap(ser, 72, 48, "TX:", DARK_GREEN, scale=1, rotated=True)

        # Row 7 (x=86): RX
        draw_text_bitmap(ser, 86, 48, "RX:", DARK_GREEN, scale=1, rotated=True)

        # Row 8 (x=100): Uptime
        draw_text_bitmap(ser, 100, 48, "UP:", DARK_GREEN, scale=1, rotated=True)

        # Row 9 (x=114): Date
        draw_text_bitmap(ser, 114, 42, "DATE:", DARK_GREEN, scale=1, rotated=True)

        # Row 10 (x=128): Free Memory
        draw_text_bitmap(ser, 128, 42, "FREE:", DARK_GREEN, scale=1, rotated=True)

        # Row 11 (x=142): IP with label
        draw_text_bitmap(ser, 142, 48, "IP:", DARK_GREEN, scale=1, rotated=True)

    # Update dynamic content - values on right side (low y values)
    # Note: No keep-alive here to avoid flickering during drawing

    # Row 1: CPU value (right side)
    draw_rect(ser, 2, 2, 12, 42, BLACK)
    cpu_str = f"{metrics['cpu']:02d}%"
    draw_text_bitmap(ser, 2, 2, cpu_str, BRIGHT_GREEN, scale=1, rotated=True)

    # Row 2: Memory value (right side)
    draw_rect(ser, 16, 2, 12, 42, BLACK)
    mem_str = f"{metrics['mem']:02d}%"
    draw_text_bitmap(ser, 16, 2, mem_str, GREEN, scale=1, rotated=True)

    # Row 3: Disk value (right side)
    draw_rect(ser, 30, 2, 12, 42, BLACK)
    dsk_str = f"{metrics['disk']:02d}%"
    draw_text_bitmap(ser, 30, 2, dsk_str, GREEN, scale=1, rotated=True)

    # Row 4: Load value (right side)
    draw_rect(ser, 44, 2, 12, 36, BLACK)
    load_str = metrics['load']
    draw_text_bitmap(ser, 44, 2, load_str, GREEN, scale=1, rotated=True)

    # Row 5: Process count (right side)
    draw_rect(ser, 58, 2, 12, 36, BLACK)
    proc_str = str(metrics['procs'])
    draw_text_bitmap(ser, 58, 2, proc_str, GREEN, scale=1, rotated=True)

    # Row 6: TX value (right side)
    tx_mb = metrics['net_sent'] // (1024 * 1024)
    draw_rect(ser, 72, 2, 12, 42, BLACK)
    tx_str = f"{tx_mb}M"
    draw_text_bitmap(ser, 72, 2, tx_str, GREEN, scale=1, rotated=True)

    # Row 7: RX value (right side)
    rx_mb = metrics['net_recv'] // (1024 * 1024)
    draw_rect(ser, 86, 2, 12, 42, BLACK)
    rx_str = f"{rx_mb}M"
    draw_text_bitmap(ser, 86, 2, rx_str, GREEN, scale=1, rotated=True)

    # Row 8: Uptime value (right side)
    draw_rect(ser, 100, 2, 12, 42, BLACK)
    uptime_str = f"{metrics['uptime']}H"
    draw_text_bitmap(ser, 100, 2, uptime_str, GREEN, scale=1, rotated=True)

    # Row 9: Date value (right side)
    draw_rect(ser, 114, 2, 12, 36, BLACK)
    draw_text_bitmap(ser, 114, 2, metrics['date'], GREEN, scale=1, rotated=True)

    # Row 10: Free memory value (right side)
    draw_rect(ser, 128, 2, 12, 36, BLACK)
    free_str = f"{metrics['mem_avail']}GB"
    draw_text_bitmap(ser, 128, 2, free_str, GREEN, scale=1, rotated=True)

    # Row 11: IP address at bottom (split into multiple lines for better display)
    if first_draw or not hasattr(display_metrics_matrix_style, 'last_ip') or display_metrics_matrix_style.last_ip != metrics['ip']:
        # Clear IP value area (leave label area)
        draw_rect(ser, 142, 0, 18, 58, BLACK)

        # Split IP address into parts (e.g., "192.168.1.100" -> ["192.168", "1.100"])
        ip_parts = metrics['ip'].split('.')
        if len(ip_parts) == 4:
            # Display as two lines: "XXX.XXX" and "XXX.XXX"
            line1 = f"{ip_parts[0]}.{ip_parts[1]}"
            line2 = f"{ip_parts[2]}.{ip_parts[3]}"

            # First line
            draw_text_bitmap(ser, 142, 2, line1, LIME, scale=1, rotated=True)
            # Second line
            draw_text_bitmap(ser, 151, 2, line2, LIME, scale=1, rotated=True)
        else:
            # Fallback: display full IP on one line
            draw_text_bitmap(ser, 142, 2, metrics['ip'], LIME, scale=1, rotated=True)

        display_metrics_matrix_style.last_ip = metrics['ip']

    print(f"⚡ [MATRIX ROTATED] CPU:{metrics['cpu']:02d}% MEM:{metrics['mem']:02d}% LOAD:{metrics['load']} PROC:{metrics['procs']} UP:{metrics['uptime']}H")


def main():
    """Main application"""
    print("="*60)
    print("MSC Metrics Display - MATRIX STYLE (90° ROTATED)")
    print("="*60)
    print("\n🟢 Entering the Matrix (Portrait Mode)...")
    print("Digital rain effect + System metrics")
    print("Green color theme inspired by The Matrix")
    print("🔄 Auto-reconnect mode enabled")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # Wait for device connection
            ser = wait_for_msc_device(retry_interval=5)

            # Keep LCD in landscape mode, but arrange content for 90° physical rotation
            display = MSCDisplay(ser)
            display.set_orientation(landscape=True)

            print("\n✓ Device ready")
            print("✓ Matrix mode activated (Landscape mode with rotated layout)...")
            print("✓ Screen: 160x80 pixels (arrange for 90° physical rotation)")
            print("\nUpdating every 10 seconds...\n")

            frame = 0
            first = True
            update_interval = 10  # Update metrics every 10 seconds
            keepalive_interval = 3  # Send keep-alive every 3 seconds during idle to prevent screensaver

            try:
                while True:
                    # Check if device is still connected
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break  # Break inner loop to reconnect

                    # Update display (no keep-alive during drawing to avoid flicker)
                    metrics = get_system_metrics()
                    display_metrics_matrix_style(ser, metrics, frame, first_draw=first)
                    first = False
                    frame += 1

                    # Wait with keep-alives during idle time to prevent screensaver
                    elapsed = 0
                    while elapsed < update_interval:
                        time.sleep(min(keepalive_interval, update_interval - elapsed))
                        elapsed += keepalive_interval

                        # Only send keep-alive if still waiting and device connected
                        if elapsed < update_interval:
                            try:
                                send_keep_alive(ser)
                            except:
                                break

            except Exception as e:
                print(f"\n⚠️  Connection error: {e}")
                try:
                    ser.close()
                except:
                    pass

    except KeyboardInterrupt:
        print("\n\n👁️ Exiting the Matrix...")
        try:
            ser.close()
        except:
            pass
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
