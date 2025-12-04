#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
System Metrics Display Plugin (Rotated)
系统指标显示插件（90度旋转版本）
"""

import time
import psutil
import socket
import serial

from lib.display_interface import DisplayPlugin
from logger import get_logger

logger = get_logger()
from lib.msc_display_lib import (
    MSCDisplay,
    Colors,
    draw_text_bitmap,
    draw_rect,
    clear_screen,
    send_keep_alive
)


class MetricsRotatedPlugin(DisplayPlugin):
    """System Metrics Display Plugin (90° Rotated - Portrait Mode)"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None
        self.frame = 0
        self.last_ip = None

    def get_name(self) -> str:
        return "System Metrics (Rotated)"

    def get_description(self) -> str:
        return "Display system metrics (90° rotated version)"

    def get_update_interval(self) -> int:
        return 10  # Update every 10 seconds

    def initialize(self) -> bool:
        """Initialize the metrics display"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            self.frame = 0
            self.last_ip = None
            return True
        except Exception as e:
            logger.error(f"Metrics (Rotated) plugin initialization Error: {e}")
            return False

    def update(self) -> bool:
        """Update the metrics display"""
        try:
            metrics = self._get_system_metrics()
            self._display_metrics(metrics, first_draw=self.first_draw)
            self.first_draw = False
            self.frame += 1
            return True
        except Exception as e:
            logger.error(f"Metrics (Rotated) update Error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        self.frame = 0
        self.last_ip = None

    def _get_system_metrics(self):
        """Get current system metrics"""
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()

        try:
            load = psutil.getloadavg()[0]
        except:
            load = 0.0

        proc_count = len(psutil.pids())

        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = int(uptime_seconds / 3600)
        except:
            uptime_hours = 0

        from datetime import datetime
        current_date = datetime.now().strftime("%m/%d")

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

    def _display_metrics(self, metrics, first_draw=False):
        """Display system metrics - 90° ROTATED LAYOUT"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        LIME = Colors.LIME

        if first_draw:
            clear_screen(self.ser, BLACK)

            # Labels on left (high y), values on right (low y)
            # When rotated 90° clockwise: labels on left, values on right

            # Row 1: CPU
            draw_text_bitmap(self.ser, 2, 48, "CPU:", DARK_GREEN, scale=1, rotated=True)

            # Row 2: Memory
            draw_text_bitmap(self.ser, 16, 48, "MEM:", DARK_GREEN, scale=1, rotated=True)

            # Row 3: Disk
            draw_text_bitmap(self.ser, 30, 48, "DSK:", DARK_GREEN, scale=1, rotated=True)

            # Row 4: Load
            draw_text_bitmap(self.ser, 44, 42, "LOAD:", DARK_GREEN, scale=1, rotated=True)

            # Row 5: Process
            draw_text_bitmap(self.ser, 58, 42, "PROC:", DARK_GREEN, scale=1, rotated=True)

            # Row 6: TX
            draw_text_bitmap(self.ser, 72, 48, "TX:", DARK_GREEN, scale=1, rotated=True)

            # Row 7: RX
            draw_text_bitmap(self.ser, 86, 48, "RX:", DARK_GREEN, scale=1, rotated=True)

            # Row 8: Uptime
            draw_text_bitmap(self.ser, 100, 48, "UP:", DARK_GREEN, scale=1, rotated=True)

            # Row 9: Date
            draw_text_bitmap(self.ser, 114, 42, "DATE:", DARK_GREEN, scale=1, rotated=True)

            # Row 10: Free Memory
            draw_text_bitmap(self.ser, 128, 42, "FREE:", DARK_GREEN, scale=1, rotated=True)

            # Row 11: IP
            draw_text_bitmap(self.ser, 142, 48, "IP:", DARK_GREEN, scale=1, rotated=True)

        # Update dynamic content (values on right side - low y values)

        # CPU value
        draw_rect(self.ser, 2, 2, 12, 42, BLACK)
        cpu_str = f"{metrics['cpu']:02d}%"
        draw_text_bitmap(self.ser, 2, 2, cpu_str, BRIGHT_GREEN, scale=1, rotated=True)

        # Memory value
        draw_rect(self.ser, 16, 2, 12, 42, BLACK)
        mem_str = f"{metrics['mem']:02d}%"
        draw_text_bitmap(self.ser, 16, 2, mem_str, GREEN, scale=1, rotated=True)

        # Disk value
        draw_rect(self.ser, 30, 2, 12, 42, BLACK)
        dsk_str = f"{metrics['disk']:02d}%"
        draw_text_bitmap(self.ser, 30, 2, dsk_str, GREEN, scale=1, rotated=True)

        # Load value
        draw_rect(self.ser, 44, 2, 12, 36, BLACK)
        load_str = metrics['load']
        draw_text_bitmap(self.ser, 44, 2, load_str, GREEN, scale=1, rotated=True)

        # Process count
        draw_rect(self.ser, 58, 2, 12, 36, BLACK)
        proc_str = str(metrics['procs'])
        draw_text_bitmap(self.ser, 58, 2, proc_str, GREEN, scale=1, rotated=True)

        # TX value
        tx_mb = metrics['net_sent'] // (1024 * 1024)
        draw_rect(self.ser, 72, 2, 12, 42, BLACK)
        tx_str = f"{tx_mb}M"
        draw_text_bitmap(self.ser, 72, 2, tx_str, GREEN, scale=1, rotated=True)

        # RX value
        rx_mb = metrics['net_recv'] // (1024 * 1024)
        draw_rect(self.ser, 86, 2, 12, 42, BLACK)
        rx_str = f"{rx_mb}M"
        draw_text_bitmap(self.ser, 86, 2, rx_str, GREEN, scale=1, rotated=True)

        # Uptime value
        draw_rect(self.ser, 100, 2, 12, 42, BLACK)
        uptime_str = f"{metrics['uptime']}H"
        draw_text_bitmap(self.ser, 100, 2, uptime_str, GREEN, scale=1, rotated=True)

        # Date value
        draw_rect(self.ser, 114, 2, 12, 36, BLACK)
        draw_text_bitmap(self.ser, 114, 2, metrics['date'], GREEN, scale=1, rotated=True)

        # Free memory value
        draw_rect(self.ser, 128, 2, 12, 36, BLACK)
        free_str = f"{metrics['mem_avail']}GB"
        draw_text_bitmap(self.ser, 128, 2, free_str, GREEN, scale=1, rotated=True)

        # IP address (only update if changed)
        if first_draw or self.last_ip != metrics['ip']:
            draw_rect(self.ser, 142, 0, 18, 58, BLACK)

            ip_parts = metrics['ip'].split('.')
            if len(ip_parts) == 4:
                line1 = f"{ip_parts[0]}.{ip_parts[1]}"
                line2 = f"{ip_parts[2]}.{ip_parts[3]}"
                draw_text_bitmap(self.ser, 142, 2, line1, LIME, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 151, 2, line2, LIME, scale=1, rotated=True)
            else:
                draw_text_bitmap(self.ser, 142, 2, metrics['ip'], LIME, scale=1, rotated=True)

            self.last_ip = metrics['ip']

        send_keep_alive(self.ser)

        logger.debug(f"⚡ [MATRIX ROTATED] CPU:{metrics['cpu']:02d}% MEM:{metrics['mem']:02d}% LOAD:{metrics['load']} PROC:{metrics['procs']} UP:{metrics['uptime']}H")
