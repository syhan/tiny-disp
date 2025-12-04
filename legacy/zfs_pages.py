#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device TrueNAS ZFS Multi-Page Display
多页显示TrueNAS ZFS存储池、数据集和磁盘信息
Page 1: Pool概览
Page 2: Datasets列表
Page 3: 磁盘状态
"""

import time
import subprocess
from typing import Optional, Dict, List

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


# TrueNAS SSH Configuration
TRUENAS_CONFIG = {
    'host': '10.0.0.129',
    'user': 'syhan',
    'password': '',
    'port': 22,
    'pool_name': 'tank',
}


def run_ssh_command(ssh_config: Dict, command: str) -> str:
    """Execute SSH command and return output"""
    try:
        ssh_cmd = [
            'sshpass', '-p', ssh_config['password'],
            'ssh', '-p', str(ssh_config['port']),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=5',
            f"{ssh_config['user']}@{ssh_config['host']}",
            command
        ]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"SSH command error: {e}")
    return ""


def get_pool_info(ssh_config: Dict) -> Dict:
    """Get pool overview information"""
    pool_name = ssh_config.get('pool_name', 'tank')
    output = run_ssh_command(ssh_config, 'zpool list -H -o name,size,alloc,free,cap,health,dedup')

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


def get_datasets(ssh_config: Dict) -> List[Dict]:
    """Get detailed info for specific datasets: archives, photos, music, videos"""
    pool_name = ssh_config.get('pool_name', 'tank')
    # Get used, compression ratio, and compression algorithm
    output = run_ssh_command(ssh_config, f'zfs list -H -r -o name,used,compressratio,compression {pool_name}')

    # Filter for specific datasets only
    target_datasets = ['archives', 'photos', 'music', 'videos']
    datasets = []

    for line in output.split('\n'):
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) >= 4:
            # Extract just the dataset name (remove pool prefix)
            full_name = fields[0]
            short_name = full_name.replace(f"{pool_name}/", "")

            # Only include target datasets
            if short_name.lower() in target_datasets:
                datasets.append({
                    'name': short_name[:10],  # Limit length for display
                    'used': fields[1],
                    'ratio': fields[2],  # Compression ratio (e.g., "1.50x")
                    'compress': fields[3][:6]  # Compression algorithm (e.g., "lz4", "zstd")
                })

    return datasets


def get_disk_status(ssh_config: Dict) -> List[Dict]:
    """Get disk status information"""
    pool_name = ssh_config.get('pool_name', 'tank')
    output = run_ssh_command(ssh_config, f'zpool status {pool_name}')

    disks = []
    in_config = False
    for line in output.split('\n'):
        line = line.strip()
        if 'NAME' in line and 'STATE' in line:
            in_config = True
            continue
        if in_config and line:
            # Parse disk lines (e.g., "  da0  ONLINE  0  0  0")
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in [pool_name, 'mirror', 'raidz1', 'raidz2', 'raidz3']:
                disk_name = parts[0][:8]
                state = parts[1][:6]
                disks.append({'name': disk_name, 'state': state})
        if line.startswith('errors:'):
            break
    return disks[:5]  # Return first 5 disks


def get_pool_events(ssh_config: Dict) -> List[str]:
    """Get recent pool events and errors"""
    pool_name = ssh_config.get('pool_name', 'tank')

    # Get pool status for errors
    status_output = run_ssh_command(ssh_config, f'zpool status {pool_name}')

    events = []

    # Check for errors in status
    if 'errors: No known data errors' in status_output:
        events.append("NO ERRORS")
    elif 'errors:' in status_output:
        for line in status_output.split('\n'):
            if 'errors:' in line.lower() and 'no known' not in line.lower():
                events.append("ERR: " + line.strip()[:20])

    # Check pool health
    if 'state: ONLINE' in status_output:
        events.append("POOL ONLINE")
    elif 'state: DEGRADED' in status_output:
        events.append("WARN DEGRADED")
    elif 'state: FAULTED' in status_output:
        events.append("ERR FAULTED")

    # Get scan status (scrub/resilver)
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

    # If no events, add a default message
    if not events:
        events.append("HEALTHY")

    return events[:5]  # Return max 5 events


def read_adc_channel(ser, channel: int) -> int:
    """Read ADC channel value"""
    try:
        cmd = bytearray([8, channel, 0, 0, 0, 0])
        ser.write(cmd)
        time.sleep(0.01)
        recv = ser.read(ser.in_waiting)
        if recv and len(recv) >= 6:
            return recv[4] * 256 + recv[5]
    except:
        pass
    return 0


def check_button_pressed(ser, threshold: int) -> bool:
    """Check if touch button is pressed (ADC channel 9)"""
    adc_value = read_adc_channel(ser, 9)
    return adc_value < threshold if adc_value > 0 else False


def display_page1_pool(ser, pool_info, events, first_draw=False):
    """Page 1: Pool Overview with Events"""
    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    YELLOW = Colors.YELLOW
    RED = Colors.RED

    # Reset LCD
    send_keep_alive(ser)
    time.sleep(0.02)

    if first_draw:
        clear_screen(ser, BLACK)

        # Page indicator
        draw_text_bitmap(ser, 2, 2, ">POOL", BRIGHT_GREEN, 1)
        draw_text_bitmap(ser, 38, 2, "SETS", DARK_GREEN, 1)
        draw_text_bitmap(ser, 74, 2, "DISK", DARK_GREEN, 1)

        # Left column - Pool info
        draw_text_bitmap(ser, 2, 14, "CAP:", DARK_GREEN, 1)
        cap_color = RED if pool_info['cap'] >= 90 else (YELLOW if pool_info['cap'] >= 80 else GREEN)
        draw_text_bitmap(ser, 26, 14, f"{pool_info['cap']}%", cap_color, 1)

        draw_text_bitmap(ser, 2, 24, "USE:", DARK_GREEN, 1)
        draw_text_bitmap(ser, 26, 24, pool_info['alloc'][:6], BRIGHT_GREEN, 1)

        draw_text_bitmap(ser, 2, 34, "FRE:", DARK_GREEN, 1)
        draw_text_bitmap(ser, 26, 34, pool_info['free'][:6], GREEN, 1)

        # Right column - Events (top 3)
        y = 14
        for i, event in enumerate(events[:3]):
            # Color code based on event content
            if 'HEALTHY' in event or 'ONLINE' in event or 'OK' in event or 'NO ERROR' in event:
                color = BRIGHT_GREEN
            elif 'WARN' in event or 'DEGRAD' in event:
                color = YELLOW
            elif 'ERR' in event or 'FAULT' in event:
                color = RED
            else:
                color = GREEN

            draw_text_bitmap(ser, 70, y, event[:15], color, 1)
            y += 10


def display_page2_datasets(ser, datasets, first_draw=False):
    """Page 2: Datasets with compression details"""
    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    CYAN = Colors.CYAN

    # Reset LCD
    send_keep_alive(ser)
    time.sleep(0.02)

    if first_draw:
        clear_screen(ser, BLACK)

        # Page indicator
        draw_text_bitmap(ser, 2, 2, "POOL", DARK_GREEN, 1)
        draw_text_bitmap(ser, 38, 2, ">SETS", BRIGHT_GREEN, 1)
        draw_text_bitmap(ser, 74, 2, "DISK", DARK_GREEN, 1)

        # Draw datasets with compression info
        # Format: NAME  USED  RATIO
        y = 14
        for i, ds in enumerate(datasets[:4]):  # Max 4 specific datasets
            # Dataset name
            draw_text_bitmap(ser, 2, y, ds['name'][:8], GREEN, 1)
            # Used space
            draw_text_bitmap(ser, 54, y, ds['used'][:6], BRIGHT_GREEN, 1)
            # Compression ratio
            draw_text_bitmap(ser, 110, y, ds['ratio'][:6], CYAN, 1)
            y += 16


def display_page3_disks(ser, disks, first_draw=False):
    """Page 3: Disk Status"""
    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    YELLOW = Colors.YELLOW
    RED = Colors.RED

    # Reset LCD
    send_keep_alive(ser)
    time.sleep(0.02)

    if first_draw:
        clear_screen(ser, BLACK)

        # Page indicator
        draw_text_bitmap(ser, 2, 2, "POOL", DARK_GREEN, 1)
        draw_text_bitmap(ser, 38, 2, "SETS", DARK_GREEN, 1)
        draw_text_bitmap(ser, 74, 2, ">DISK", BRIGHT_GREEN, 1)

        # Draw disks
        y = 14
        for disk in disks[:5]:
            draw_text_bitmap(ser, 2, y, disk['name'], GREEN, 1)
            state_color = BRIGHT_GREEN if disk['state'] == 'ONLINE' else (YELLOW if 'DEGRAD' in disk['state'] else RED)
            draw_text_bitmap(ser, 68, y, disk['state'], state_color, 1)
            y += 13
            if y > 72:
                break


def main():
    print("="*60)
    print("TrueNAS ZFS Multi-Page Display")
    print("="*60)
    print("\n🔄 Auto-reconnect mode enabled")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # Wait for device connection
            ser = wait_for_msc_device(retry_interval=5)

            # Initialize display
            display = MSCDisplay(ser)
            display.set_orientation(landscape=True)

            # Get baseline ADC value for button detection
            print("Calibrating touch button...")
            adc_baseline = read_adc_channel(ser, 9)
            button_threshold = adc_baseline - 125  # Threshold for button press
            print(f"✓ Button threshold: {button_threshold}")

            print("✓ Device ready - Auto-rotating pages")
            print("  Page 1: Pool Overview + Events")
            print("  Page 2: Datasets (archives, photos, music, video)")
            print("  Page 3: Disk Status (up to 5)")
            print("\n👆 Touch button to switch pages manually")
            print("🔄 Auto-switch every 4 seconds\n")

            page = 0
            last_page = -1
            last_update = time.time()
            button_was_pressed = False
            page_duration = 4  # Auto-switch every 4 seconds

            try:
                while True:
                    current_time = time.time()

                    # Check if device is still connected
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break  # Break inner loop to reconnect

                    # Check for button press
                    try:
                        button_pressed = check_button_pressed(ser, button_threshold)
                    except:
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break

                    if button_pressed and not button_was_pressed:
                        # Button just pressed - switch to next page immediately
                        page = (page + 1) % 3
                        last_update = current_time
                        print("👆 Button pressed - switching page")
                        button_was_pressed = True
                    elif not button_pressed:
                        button_was_pressed = False

                    # Auto page rotation
                    if current_time - last_update >= page_duration:
                        page = (page + 1) % 3
                        last_update = current_time

                    # Display current page only when page changes
                    first_draw = (page != last_page)
                    if first_draw:
                        try:
                            if page == 0:
                                pool_info = get_pool_info(TRUENAS_CONFIG)
                                events = get_pool_events(TRUENAS_CONFIG)
                                display_page1_pool(ser, pool_info, events, first_draw)
                                print(f"📄 Page 1: {pool_info['name']} - {pool_info['cap']}% - {len(events)} events")
                            elif page == 1:
                                datasets = get_datasets(TRUENAS_CONFIG)
                                display_page2_datasets(ser, datasets, first_draw)
                                print(f"📄 Page 2: {len(datasets)} datasets")
                            else:
                                disks = get_disk_status(TRUENAS_CONFIG)
                                display_page3_disks(ser, disks, first_draw)
                                print(f"📄 Page 3: {len(disks)} disks")
                            last_page = page
                        except:
                            print("\n⚠️  Display error!")
                            ser.close()
                            break

                    time.sleep(0.2)  # Check button every 0.2s

            except Exception as e:
                print(f"\n⚠️  Connection error: {e}")
                try:
                    ser.close()
                except:
                    pass

    except KeyboardInterrupt:
        print("\n\n👁️ Exiting...")
        try:
            ser.close()
        except:
            pass
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
