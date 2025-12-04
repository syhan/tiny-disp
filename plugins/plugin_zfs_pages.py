#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
ZFS Pool Display Plugin (Multi-page)
ZFS存储池显示插件（多页版本）
Page 1: Pool概览 + Events
Page 2: Datasets列表
Page 3: 磁盘状态
"""

import time
import subprocess
import serial
from typing import Dict, List

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


class ZFSPagesPlugin(DisplayPlugin):
    """ZFS Pool Display Plugin (Multi-page)"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None

        # Load configuration from config file
        self.ssh_config = {
            'host': config.get('zfs_pages', 'host', fallback=config.get('zfs', 'host', fallback='YOUR_TRUENAS_IP')),
            'user': config.get('zfs_pages', 'user', fallback=config.get('zfs', 'user', fallback='YOUR_USERNAME')),
            'password': config.get('zfs_pages', 'password', fallback=config.get('zfs', 'password', fallback='YOUR_PASSWORD')),
            'port': config.getint('zfs_pages', 'port', fallback=config.getint('zfs', 'port', fallback=22)),
            'pool_name': config.get('zfs_pages', 'pool_name', fallback=config.get('zfs', 'pool_name', fallback='tank')),
        }

        self.current_page = 0
        self.last_page_change = time.time()
        self.page_duration = config.getint('zfs_pages', 'page_duration', fallback=4)
        self.button_threshold = 0
        self.button_was_pressed = False

    def get_name(self) -> str:
        return "ZFS Pool Monitor (Pages)"

    def get_description(self) -> str:
        return "Display TrueNAS ZFS pool information (multi-page)"

    def get_update_interval(self) -> int:
        return 1  # Update every 1 second for button checks and page rotation

    def initialize(self) -> bool:
        """Initialize the ZFS Pages display"""
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

            # Calibrate button
            logger.info("Calibrating touch button...")
            adc_baseline = self._read_adc_channel(9)
            self.button_threshold = adc_baseline - 125
            logger.info(f" Button threshold: {self.button_threshold}")

            # Test SSH connection
            logger.info(f"Testing SSH connection to {self.ssh_config['host']}...")
            pool_info = self._get_pool_info()
            if pool_info['online']:
                logger.info(f" Connected to TrueNAS")
                logger.info(f" Found pool: {pool_info['name']}")
            else:
                logger.warning("  WARNING: Cannot connect to TrueNAS!")
                logger.info("Continuing with offline display...")

            logger.info(" Multi-page mode:")
            logger.info("  Page 1: Pool Overview + Events")
            logger.info("  Page 2: Datasets")
            logger.info("  Page 3: Disk Status")
            logger.info("👆 Touch button to switch pages manually")

            self.current_page = 0
            self.last_page_change = time.time()

            return True
        except Exception as e:
            logger.error(f"ZFS Pages plugin initialization Error: {e}")
            return False

    def update(self) -> bool:
        """Update the ZFS Pages display"""
        try:
            current_time = time.time()

            # Check for button press
            button_pressed = self._check_button_pressed()
            if button_pressed and not self.button_was_pressed:
                # Button just pressed - switch to next page
                self.current_page = (self.current_page + 1) % 3
                self.last_page_change = current_time
                self.first_draw = True
                logger.info("👆 Button pressed - switching page")
                self.button_was_pressed = True
            elif not button_pressed:
                self.button_was_pressed = False

            # Auto page rotation
            if current_time - self.last_page_change >= self.page_duration:
                self.current_page = (self.current_page + 1) % 3
                self.last_page_change = current_time
                self.first_draw = True

            # Display current page
            if self.first_draw:
                if self.current_page == 0:
                    pool_info = self._get_pool_info()
                    events = self._get_pool_events()
                    self._display_page1_pool(pool_info, events)
                    logger.info(f"📄 Page 1: {pool_info['name']} - {pool_info['cap']}% - {len(events)} events")
                elif self.current_page == 1:
                    datasets = self._get_datasets()
                    self._display_page2_datasets(datasets)
                    logger.info(f"📄 Page 2: {len(datasets)} datasets")
                else:
                    disks = self._get_disk_status()
                    self._display_page3_disks(disks)
                    logger.info(f"📄 Page 3: {len(disks)} disks")

                self.first_draw = False

            return True
        except Exception as e:
            logger.error(f"ZFS Pages update Error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        self.current_page = 0

    def _check_sshpass(self) -> bool:
        """Check if sshpass is installed"""
        try:
            result = subprocess.run(['which', 'sshpass'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def _run_ssh_command(self, command: str) -> str:
        """Execute SSH command and return output"""
        try:
            ssh_cmd = [
                'sshpass', '-p', self.ssh_config['password'],
                'ssh', '-p', str(self.ssh_config['port']),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                f"{self.ssh_config['user']}@{self.ssh_config['host']}",
                command
            ]
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"SSH command Error: {e}")
        return ""

    def _get_pool_info(self) -> Dict:
        """Get pool overview information"""
        pool_name = self.ssh_config.get('pool_name', 'tank')
        output = self._run_ssh_command('zpool list -H -o name,size,alloc,free,cap,health,dedup')

        for line in output.split('\n'):
            fields = line.split('\t')
            if fields and fields[0] == pool_name and len(fields) >= 7:
                return {
                    'name': fields[0][:8],
                    'size': fields[1],
                    'alloc': fields[2],
                    'free': fields[3],
                    'cap': int(fields[4].replace('%', '')) if fields[4].replace('%', '').isdigit() else 0,
                    'health': fields[5][:6],
                    'dedup': fields[6],
                    'online': True
                }
        return {'name': 'N/A', 'size': 'N/A', 'alloc': 'N/A', 'free': 'N/A',
                'cap': 0, 'health': 'N/A', 'dedup': 'N/A', 'online': False}

    def _get_datasets(self) -> List[Dict]:
        """Get specific datasets info"""
        pool_name = self.ssh_config.get('pool_name', 'tank')
        output = self._run_ssh_command(f'zfs list -H -r -o name,used,compressratio,compression {pool_name}')

        target_datasets = ['archives', 'photos', 'music', 'videos']
        datasets = []

        for line in output.split('\n'):
            if not line:
                continue
            fields = line.split('\t')
            if len(fields) >= 4:
                full_name = fields[0]
                short_name = full_name.replace(f"{pool_name}/", "")

                if short_name.lower() in target_datasets:
                    datasets.append({
                        'name': short_name[:10],
                        'used': fields[1],
                        'ratio': fields[2],
                        'compress': fields[3][:6]
                    })

        return datasets

    def _get_disk_status(self) -> List[Dict]:
        """Get disk status information"""
        pool_name = self.ssh_config.get('pool_name', 'tank')
        output = self._run_ssh_command(f'zpool status {pool_name}')

        disks = []
        in_config = False
        for line in output.split('\n'):
            line = line.strip()
            if 'NAME' in line and 'STATE' in line:
                in_config = True
                continue
            if in_config and line:
                parts = line.split()
                if len(parts) >= 2 and parts[0] not in [pool_name, 'mirror', 'raidz1', 'raidz2', 'raidz3']:
                    disk_name = parts[0][:8]
                    state = parts[1][:6]
                    disks.append({'name': disk_name, 'state': state})
            if line.startswith('errors:'):
                break
        return disks[:5]

    def _get_pool_events(self) -> List[str]:
        """Get recent pool events"""
        pool_name = self.ssh_config.get('pool_name', 'tank')
        status_output = self._run_ssh_command(f'zpool status {pool_name}')

        events = []

        if 'errors: No known data errors' in status_output:
            events.append("NO ERRORS")
        elif 'errors:' in status_output:
            for line in status_output.split('\n'):
                if 'errors:' in line.lower() and 'no known' not in line.lower():
                    events.append("ERR: " + line.strip()[:20])

        if 'state: ONLINE' in status_output:
            events.append("POOL ONLINE")
        elif 'state: DEGRADED' in status_output:
            events.append("WARN DEGRADED")
        elif 'state: FAULTED' in status_output:
            events.append("ERR FAULTED")

        for line in status_output.split('\n'):
            line = line.strip()
            if 'scan:' in line.lower():
                if 'scrub repaired' in line.lower():
                    events.append("SCRUB OK")
                elif 'scrub in progress' in line.lower():
                    events.append("SCRUB RUNNING")
                elif 'resilver' in line.lower():
                    events.append("RESILVER")
                elif 'none requested' in line.lower():
                    events.append("NO SCAN YET")

        if not events:
            events.append("HEALTHY")

        return events[:5]

    def _read_adc_channel(self, channel: int) -> int:
        """Read ADC channel value"""
        try:
            cmd = bytearray([8, channel, 0, 0, 0, 0])
            self.ser.write(cmd)
            time.sleep(0.01)
            recv = self.ser.read(self.ser.in_waiting)
            if recv and len(recv) >= 6:
                return recv[4] * 256 + recv[5]
        except:
            pass
        return 0

    def _check_button_pressed(self) -> bool:
        """Check if touch button is pressed"""
        adc_value = self._read_adc_channel(9)
        return adc_value < self.button_threshold if adc_value > 0 else False

    def _display_page1_pool(self, pool_info, events):
        """Page 1: Pool Overview with Events"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        YELLOW = Colors.YELLOW
        RED = Colors.RED

        send_keep_alive(self.ser)
        time.sleep(0.02)

        clear_screen(self.ser, BLACK)

        # Page indicator
        draw_text_bitmap(self.ser, 2, 2, ">POOL", BRIGHT_GREEN, 1)
        draw_text_bitmap(self.ser, 38, 2, "SETS", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 74, 2, "DISK", DARK_GREEN, 1)

        # Pool info
        draw_text_bitmap(self.ser, 2, 14, "CAP:", DARK_GREEN, 1)
        cap_color = RED if pool_info['cap'] >= 90 else (YELLOW if pool_info['cap'] >= 80 else GREEN)
        draw_text_bitmap(self.ser, 26, 14, f"{pool_info['cap']}%", cap_color, 1)

        draw_text_bitmap(self.ser, 2, 24, "USE:", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 26, 24, pool_info['alloc'][:6], BRIGHT_GREEN, 1)

        draw_text_bitmap(self.ser, 2, 34, "FRE:", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 26, 34, pool_info['free'][:6], GREEN, 1)

        # Events
        y = 14
        for event in events[:3]:
            if 'HEALTHY' in event or 'ONLINE' in event or 'OK' in event or 'NO ERROR' in event:
                color = BRIGHT_GREEN
            elif 'WARN' in event or 'DEGRAD' in event:
                color = YELLOW
            elif 'ERR' in event or 'FAULT' in event:
                color = RED
            else:
                color = GREEN

            draw_text_bitmap(self.ser, 70, y, event[:15], color, 1)
            y += 10

        send_keep_alive(self.ser)

    def _display_page2_datasets(self, datasets):
        """Page 2: Datasets"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        CYAN = Colors.CYAN

        send_keep_alive(self.ser)
        time.sleep(0.02)

        clear_screen(self.ser, BLACK)

        # Page indicator
        draw_text_bitmap(self.ser, 2, 2, "POOL", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 38, 2, ">SETS", BRIGHT_GREEN, 1)
        draw_text_bitmap(self.ser, 74, 2, "DISK", DARK_GREEN, 1)

        # Datasets
        y = 14
        for ds in datasets[:4]:
            draw_text_bitmap(self.ser, 2, y, ds['name'][:8], GREEN, 1)
            draw_text_bitmap(self.ser, 54, y, ds['used'][:6], BRIGHT_GREEN, 1)
            draw_text_bitmap(self.ser, 110, y, ds['ratio'][:6], CYAN, 1)
            y += 16

        send_keep_alive(self.ser)

    def _display_page3_disks(self, disks):
        """Page 3: Disk Status"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        YELLOW = Colors.YELLOW
        RED = Colors.RED

        send_keep_alive(self.ser)
        time.sleep(0.02)

        clear_screen(self.ser, BLACK)

        # Page indicator
        draw_text_bitmap(self.ser, 2, 2, "POOL", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 38, 2, "SETS", DARK_GREEN, 1)
        draw_text_bitmap(self.ser, 74, 2, ">DISK", BRIGHT_GREEN, 1)

        # Disks
        y = 14
        for disk in disks[:5]:
            draw_text_bitmap(self.ser, 2, y, disk['name'], GREEN, 1)
            state_color = BRIGHT_GREEN if disk['state'] == 'ONLINE' else (YELLOW if 'DEGRAD' in disk['state'] else RED)
            draw_text_bitmap(self.ser, 68, y, disk['state'], state_color, 1)
            y += 13
            if y > 72:
                break

        send_keep_alive(self.ser)
