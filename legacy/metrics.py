#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device System Metrics Display - Matrix Style
黑客帝国风格的系统指标显示
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
    """Display system metrics with Matrix movie style - LANDSCAPE MODE"""

    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    LIME = Colors.LIME

    # Reset LCD
    send_keep_alive(ser)
    time.sleep(0.02)

    # Only full redraw on first time
    if first_draw:
        # Clear to black (pure black background, no rain)
        clear_screen(ser, BLACK)

        # Draw static labels (only once)
        # Left column - Primary metrics (label and value on same line)
        draw_text_bitmap(ser, 2, 2, "CPU:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 14, "MEM:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 26, "DSK:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 38, "LOAD:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 2, 50, "PROC:", DARK_GREEN, scale=1)

        # Vertical separator line (dashed) - moved right
        for y in range(2, 78, 4):
            draw_rect(ser, 76, y, 1, 2, DARK_GREEN)

        # Right column - Network & System (shifted right)
        draw_text_bitmap(ser, 80, 2, "IP:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 26, "UP:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 38, "TX:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 50, "RX:", DARK_GREEN, scale=1)

        # Bottom row - Additional metrics
        draw_text_bitmap(ser, 2, 64, "DATE:", DARK_GREEN, scale=1)
        draw_text_bitmap(ser, 80, 64, "FREE:", DARK_GREEN, scale=1)

    # Send keep-alive
    send_keep_alive(ser)

    # Update dynamic content - Left column (label:value on same line)
    # Clear only the VALUE area, not the label

    # CPU percentage
    draw_rect(ser, 32, 2, 34, 10, BLACK)
    draw_text_bitmap(ser, 32, 2, f"{metrics['cpu']:02d}%", BRIGHT_GREEN, scale=1)

    # Memory percentage
    draw_rect(ser, 32, 14, 34, 10, BLACK)
    draw_text_bitmap(ser, 32, 14, f"{metrics['mem']:02d}%", GREEN, scale=1)

    # Disk percentage
    draw_rect(ser, 32, 26, 34, 10, BLACK)
    draw_text_bitmap(ser, 32, 26, f"{metrics['disk']:02d}%", GREEN, scale=1)

    # Load average (LOAD: is at x=2, value starts after)
    draw_rect(ser, 38, 38, 28, 10, BLACK)
    draw_text_bitmap(ser, 38, 38, metrics['load'], GREEN, scale=1)

    # Process count (PROC: is at x=2, value starts after)
    draw_rect(ser, 38, 50, 28, 10, BLACK)
    draw_text_bitmap(ser, 38, 50, str(metrics['procs']), GREEN, scale=1)

    # Update Right column (shifted right)

    # IP address (only if changed)
    if first_draw or not hasattr(display_metrics_matrix_style, 'last_ip') or display_metrics_matrix_style.last_ip != metrics['ip']:
        draw_rect(ser, 80, 12, 78, 10, BLACK)
        draw_text_bitmap(ser, 80, 12, metrics['ip'], LIME, scale=1)
        display_metrics_matrix_style.last_ip = metrics['ip']

    # Uptime in hours
    draw_rect(ser, 98, 26, 60, 10, BLACK)
    uptime_str = f"{metrics['uptime']}H"
    draw_text_bitmap(ser, 98, 26, uptime_str, GREEN, scale=1)

    # Network TX (sent) - in MB
    tx_mb = metrics['net_sent'] // (1024 * 1024)
    draw_rect(ser, 98, 38, 60, 10, BLACK)
    draw_text_bitmap(ser, 98, 38, f"{tx_mb}M", GREEN, scale=1)

    # Network RX (received) - in MB
    rx_mb = metrics['net_recv'] // (1024 * 1024)
    draw_rect(ser, 98, 50, 60, 10, BLACK)
    draw_text_bitmap(ser, 98, 50, f"{rx_mb}M", GREEN, scale=1)

    # Bottom row - Additional metrics

    # Current Date (MM/DD format)
    draw_rect(ser, 38, 64, 32, 10, BLACK)
    draw_text_bitmap(ser, 38, 64, metrics['date'], GREEN, scale=1)

    # Memory Available (GB)
    draw_rect(ser, 110, 64, 48, 10, BLACK)
    draw_text_bitmap(ser, 110, 64, f"{metrics['mem_avail']}GB", GREEN, scale=1)

    # Final keep-alive
    send_keep_alive(ser)

    print(f"⚡ [MATRIX] CPU:{metrics['cpu']:02d}% MEM:{metrics['mem']:02d}% LOAD:{metrics['load']} PROC:{metrics['procs']} UP:{metrics['uptime']}H")


def main():
    """Main application"""
    print("="*60)
    print("MSC Metrics Display - MATRIX STYLE")
    print("="*60)
    print("\n🟢 Entering the Matrix...")
    print("Digital rain effect + System metrics")
    print("Green color theme inspired by The Matrix")
    print("🔄 Auto-reconnect mode enabled")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # Wait for device connection
            ser = wait_for_msc_device(retry_interval=5)

            # Set LCD orientation to default landscape
            display = MSCDisplay(ser)
            display.set_orientation(landscape=True)

            print("\n✓ Device ready")
            print("✓ Matrix mode activated (Landscape orientation)...")
            print("✓ Screen: 160x80 pixels (width x height)")
            print("\nUpdating every 10 seconds...\n")

            frame = 0
            first = True
            update_interval = 10  # Update metrics every 10 seconds
            keepalive_interval = 3  # Send keep-alive every 3 seconds

            try:
                while True:
                    # Check if device is still connected
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break  # Break inner loop to reconnect

                    # Update display
                    metrics = get_system_metrics()
                    display_metrics_matrix_style(ser, metrics, frame, first_draw=first)
                    first = False
                    frame += 1

                    # Wait with periodic keep-alives to prevent screensaver
                    elapsed = 0
                    while elapsed < update_interval:
                        if not is_device_connected(ser):
                            print("\n⚠️  Device disconnected!")
                            ser.close()
                            break

                        time.sleep(keepalive_interval)
                        elapsed += keepalive_interval

                        # Send keep-alive command to prevent screensaver
                        try:
                            send_keep_alive(ser)
                        except:
                            break

                    if not is_device_connected(ser):
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
