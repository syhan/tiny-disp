#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
ZFS Pool Display Plugin
ZFS存储池显示插件
"""

import time
import subprocess
import serial
from typing import Dict

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
from config_loader import config


class ZFSPlugin(DisplayPlugin):
    """ZFS Pool Display Plugin"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None
        self.frame = 0

        # Load configuration from config file
        self.ssh_config = {
            'host': config.get('zfs', 'host', fallback='YOUR_TRUENAS_IP'),
            'user': config.get('zfs', 'user', fallback='YOUR_USERNAME'),
            'password': config.get('zfs', 'password', fallback='YOUR_PASSWORD'),
            'port': config.getint('zfs', 'port', fallback=22),
            'pool_name': config.get('zfs', 'pool_name', fallback='tank'),
        }

    def get_name(self) -> str:
        return "ZFS Pool Monitor"

    def get_description(self) -> str:
        return "Display TrueNAS ZFS pool information"

    def get_update_interval(self) -> int:
        return 15  # Update every 15 seconds

    def initialize(self) -> bool:
        """Initialize the ZFS display"""
        try:
            # Check if sshpass is installed
            if not self._check_sshpass():
                logger.error(" ERROR: sshpass is not installed!")
                logger.info("\nPlease install sshpass first:")
                logger.info("  On Debian/Ubuntu/Proxmox VE:")
                logger.info("    apt update && apt install sshpass -y")
                logger.info("  On macOS:")
                logger.info("    brew install sshpass")
                return False

            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            self.frame = 0

            # Test SSH connection
            logger.info(f"Testing SSH connection to {self.ssh_config['host']}...")
            test_metrics = self._get_zfs_metrics()
            if test_metrics['online']:
                logger.info(f" Connected to TrueNAS")
                logger.info(f" Found pool: {test_metrics['name']}")
            else:
                logger.warning("  WARNING: Cannot connect to TrueNAS!")
                logger.info("Continuing with offline display...")

            return True
        except Exception as e:
            logger.error(f"ZFS plugin initialization Error: {e}")
            return False

    def update(self) -> bool:
        """Update the ZFS display"""
        try:
            metrics = self._get_zfs_metrics()
            self._display_zfs_metrics(metrics, first_draw=self.first_draw)
            self.first_draw = False
            self.frame += 1
            return True
        except Exception as e:
            logger.error(f"ZFS update Error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        self.frame = 0

    def _check_sshpass(self) -> bool:
        """Check if sshpass is installed"""
        try:
            result = subprocess.run(['which', 'sshpass'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def _get_zfs_metrics(self) -> Dict:
        """Get ZFS pool metrics from TrueNAS via SSH"""
        try:
            # SSH command to get ZFS pool list
            ssh_cmd = [
                'sshpass',
                '-p', self.ssh_config['password'],
                'ssh',
                '-p', str(self.ssh_config['port']),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                f"{self.ssh_config['user']}@{self.ssh_config['host']}",
                'zpool list -H -o name,size,alloc,free,cap,health,dedup'
            ]

            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return self._get_default_metrics()

            # Parse ZFS pool data
            lines = result.stdout.strip().split('\n')
            if not lines or not lines[0]:
                return self._get_default_metrics()

            # Find specified pool by name
            target_pool = self.ssh_config.get('pool_name', 'tank')
            fields = None
            for line in lines:
                line_fields = line.split('\t')
                if line_fields and line_fields[0] == target_pool:
                    fields = line_fields
                    break

            if not fields or len(fields) < 7:
                return self._get_default_metrics()

            name = fields[0]
            size = fields[1]
            alloc = fields[2]
            free = fields[3]
            cap = fields[4].replace('%', '')
            health = fields[5]
            dedup = fields[6]

            # Get scrub status
            scrub_cmd = [
                'sshpass',
                '-p', self.ssh_config['password'],
                'ssh',
                '-p', str(self.ssh_config['port']),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                f"{self.ssh_config['user']}@{self.ssh_config['host']}",
                f'zpool status {name} | grep "scan:"'
            ]
            scrub_result = subprocess.run(scrub_cmd, capture_output=True, text=True, timeout=10)
            scrub_status = "NONE"
            if "in progress" in scrub_result.stdout:
                scrub_status = "RUN"
            elif "completed" in scrub_result.stdout:
                scrub_status = "OK"

            return {
                'name': name[:8],
                'size': size,
                'alloc': alloc,
                'free': free,
                'cap': int(cap) if cap.isdigit() else 0,
                'health': health[:6],
                'dedup': dedup,
                'scrub': scrub_status,
                'online': True
            }

        except Exception as e:
            logger.info(f"Error getting ZFS metrics: {e}")
            return self._get_default_metrics()

    def _get_default_metrics(self) -> Dict:
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

    def _display_zfs_metrics(self, metrics, first_draw=False):
        """Display TrueNAS ZFS metrics - LANDSCAPE MODE"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        RED = Colors.RED
        YELLOW = Colors.YELLOW

        send_keep_alive(self.ser)
        time.sleep(0.02)

        if first_draw:
            clear_screen(self.ser, BLACK)

            # Draw static labels - Left column
            draw_text_bitmap(self.ser, 2, 2, "POOL:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 14, "SIZE:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 26, "USED:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 38, "FREE:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 2, 50, "CAP:", DARK_GREEN, scale=1)

            # Vertical separator
            for y in range(2, 78, 4):
                draw_rect(self.ser, 76, y, 1, 2, DARK_GREEN)

            # Right column
            draw_text_bitmap(self.ser, 80, 2, "STAT:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 26, "DEDUP:", DARK_GREEN, scale=1)
            draw_text_bitmap(self.ser, 80, 38, "SCRUB:", DARK_GREEN, scale=1)

            # Bottom
            draw_text_bitmap(self.ser, 2, 64, "HOST:", DARK_GREEN, scale=1)

        send_keep_alive(self.ser)

        # Update dynamic content

        # Pool name
        draw_rect(self.ser, 38, 2, 36, 10, BLACK)
        name_color = GREEN if metrics['online'] else RED
        draw_text_bitmap(self.ser, 38, 2, metrics['name'], name_color, scale=1)

        # Total size
        draw_rect(self.ser, 38, 14, 36, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 14, metrics['size'], GREEN, scale=1)

        # Used (allocated)
        draw_rect(self.ser, 38, 26, 36, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 26, metrics['alloc'], BRIGHT_GREEN, scale=1)

        # Free space
        draw_rect(self.ser, 38, 38, 36, 10, BLACK)
        draw_text_bitmap(self.ser, 38, 38, metrics['free'], GREEN, scale=1)

        # Capacity percentage
        draw_rect(self.ser, 32, 50, 42, 10, BLACK)
        cap_color = RED if metrics['cap'] >= 90 else (YELLOW if metrics['cap'] >= 80 else GREEN)
        draw_text_bitmap(self.ser, 32, 50, f"{metrics['cap']}%", cap_color, scale=1)

        # Health status
        draw_rect(self.ser, 116, 2, 42, 10, BLACK)
        health_color = GREEN if metrics['health'] in ['ONLINE', 'N/A'] else (YELLOW if 'DEGRAD' in metrics['health'] else RED)
        draw_text_bitmap(self.ser, 116, 2, metrics['health'], health_color, scale=1)

        # Dedup ratio
        draw_rect(self.ser, 122, 26, 36, 10, BLACK)
        draw_text_bitmap(self.ser, 122, 26, metrics['dedup'], GREEN, scale=1)

        # Scrub status
        draw_rect(self.ser, 128, 38, 30, 10, BLACK)
        scrub_color = BRIGHT_GREEN if metrics['scrub'] == 'OK' else (YELLOW if metrics['scrub'] == 'RUN' else GREEN)
        draw_text_bitmap(self.ser, 128, 38, metrics['scrub'], scrub_color, scale=1)

        # TrueNAS host
        draw_rect(self.ser, 38, 64, 120, 10, BLACK)
        host_display = self.ssh_config['host']
        status_indicator = "ON" if metrics['online'] else "OFF"
        draw_text_bitmap(self.ser, 38, 64, f"{host_display} {status_indicator}", GREEN if metrics['online'] else RED, scale=1)

        send_keep_alive(self.ser)

        logger.info(f"💾 [ZFS] Pool:{metrics['name']} Cap:{metrics['cap']}% Health:{metrics['health']} Free:{metrics['free']}")
