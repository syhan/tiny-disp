#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
System Metrics Display Plugin
系统指标显示插件
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


class MetricsPlugin(DisplayPlugin):
    """System Metrics Display Plugin (Landscape)"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None
        self.frame = 0
        self.last_ip = None

    def get_name(self) -> str:
        return "System Metrics"

    def get_description(self) -> str:
        return "Display system metrics (CPU, Memory, Disk, etc.)"

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
            logger.error(f"Metrics plugin initialization Error: {e}")
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
            logger.error(f"Metrics update Error: {e}")
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
        """Display system metrics - LANDSCAPE MODE"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        LIME = Colors.LIME

        send_keep_alive(self.ser)
        time.sleep(0.02)

        if first_draw:
            clear_screen(self.ser, BLACK)

            # Draw static labels
            draw_text_bitmap(self.ser, 2, 2, "CPU:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 14, "MEM:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 26, "DSK:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 38, "LOAD:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 50, "PROC:", DARK_GREEN, scale=1)

            # Vertical separator line
            for y in range(2, 78, 4):
                draw_rect(self.ser, 76, y, 1, 2, DARK_GREEN)

            # Right column
            draw_text_bitmap(self.ser, 80, 2, "IP:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 26, "UP:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 38, "TX:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 50, "RX:", DARK_GREEN, scale=1)

            # Bottom row
            draw_text_bitmap(self.ser, 2, 64, "DATE:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 64, "FREE:", DARK_GREEN, scale=1)

        send_keep_alive(self.ser)

        # Update dynamic content
        draw_rect(self.ser, 32, 2, 34, 10, BLACK)
        draw_text_bitmap(self.ser, 32, 2, f"{metrics['cpu']:02d}%", BRIGHT_GREEN, scale=1)

        draw_rect(self.ser, 32, 14, 34, 10, BLACK)
        draw_text_bitmap(self.ser, 32, 14, f"{metrics['mem']:02d}%", GREEN, scale=1)

        draw_rect(self.ser, 32, 26, 34, 10, BLACK)
        draw_text_bitmap(self.ser, 32, 26, f"{metrics['disk']:02d}%", GREEN, scale=1)

        draw_rect(self.ser, 38, 38, 28, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 38, metrics['load'], GREEN, scale=1)

        draw_rect(self.ser, 38, 50, 28, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 50, str(metrics['procs']), GREEN, scale=1)

        # IP address (only if changed)
        if first_draw or self.last_ip != metrics['ip']:
            draw_rect(self.ser, 80, 12, 78, 10, BLACK)
            draw_text_bitmap(self.ser, 80, 12, metrics['ip'], LIME, scale=1)
            self.last_ip = metrics['ip']

        draw_rect(self.ser, 98, 26, 60, 10, BLACK)
        uptime_str = f"{metrics['uptime']}H"
        draw_text_bitmap(self.ser, 98, 26, uptime_str, GREEN, scale=1)

        tx_mb = metrics['net_sent'] // (1024 * 1024)
        draw_rect(self.ser, 98, 38, 60, 10, BLACK)
        draw_text_bitmap(self.ser, 98, 38, f"{tx_mb}M", GREEN, scale=1)

        rx_mb = metrics['net_recv'] // (1024 * 1024)
        draw_rect(self.ser, 98, 50, 60, 10, BLACK)
        draw_text_bitmap(self.ser, 98, 50, f"{rx_mb}M", GREEN, scale=1)

        draw_rect(self.ser, 38, 64, 32, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 64, metrics['date'], GREEN, scale=1)

        draw_rect(self.ser, 110, 64, 48, 10, BLACK)
        draw_text_bitmap(self.ser, 110, 64, f"{metrics['mem_avail']}GB", GREEN, scale=1)

        send_keep_alive(self.ser)

        logger.info(f"⚡ [MATRIX] CPU:{metrics['cpu']:02d}% MEM:{metrics['mem']:02d}% LOAD:{metrics['load']} PROC:{metrics['procs']} UP:{metrics['uptime']}H")
