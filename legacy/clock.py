#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device World Clock Display (90° Rotated - Portrait Mode)
世界时钟显示 - 同时显示多个时区 (90度旋转 - 竖屏模式)
"""

import time
from datetime import datetime
import pytz

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


# World clock configuration
WORLD_CITIES = [
    {'name': 'SHANGHAI', 'timezone': 'Asia/Shanghai', 'short': 'SHA'},
    {'name': 'BERLIN', 'timezone': 'Europe/Berlin', 'short': 'BER'},
    {'name': 'VANCOUVR', 'timezone': 'America/Vancouver', 'short': 'VAN'},
    {'name': 'WASHINGTN', 'timezone': 'America/New_York', 'short': 'DC'},
]


def get_city_time(timezone_str):
    """Get current time for a specific timezone"""
    try:
        tz = pytz.timezone(timezone_str)
        city_time = datetime.now(tz)
        return {
            'time': city_time.strftime("%H:%M"),
            'date': city_time.strftime("%m/%d"),
            'hour': city_time.hour
        }
    except Exception as e:
        print(f"Error getting time for {timezone_str}: {e}")
        return {
            'time': "--:--",
            'date': "--/--",
            'hour': 0
        }


def get_time_color(hour):
    """Get color based on time of day"""
    if 6 <= hour < 12:
        return Colors.YELLOW  # Morning
    elif 12 <= hour < 18:
        return Colors.ORANGE  # Afternoon
    elif 18 <= hour < 22:
        return Colors.CYAN  # Evening
    else:
        return Colors.BLUE  # Night


def display_world_clock(ser, first_draw=False, minute_changed=False):
    """Display world clock for multiple cities"""

    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN

    if first_draw:
        clear_screen(ser, BLACK)

        # Draw title at top (rotated text)
        draw_text_bitmap(ser, 2, 2, "WORLD", BRIGHT_GREEN, scale=1, rotated=True)
        draw_text_bitmap(ser, 2, 42, "CLOCK", BRIGHT_GREEN, scale=1, rotated=True)

        # Layout: 4 cities in rows
        x_positions = [25, 60, 95, 130]

        # Draw static city names (only once)
        for i, city_info in enumerate(WORLD_CITIES):
            x = x_positions[i]
            draw_text_bitmap(ser, x, 2, city_info['short'], DARK_GREEN, scale=1, rotated=True)

        # Draw separator lines between cities (only once)
        for i in range(1, 4):
            x = x_positions[i] - 5
            # Dashed line
            for y in range(5, 75, 6):
                draw_rect(ser, x, y, 1, 3, DARK_GREEN)

    # Only update times when minute changes
    if minute_changed or first_draw:
        x_positions = [25, 60, 95, 130]

        for i, city_info in enumerate(WORLD_CITIES):
            x = x_positions[i]

            # Get time for this city
            city_data = get_city_time(city_info['timezone'])
            time_color = get_time_color(city_data['hour'])

            # Only clear and redraw the TIME area (not city name or separators)
            draw_rect(ser, x, 28, 30, 50, BLACK)  # Clear only time area

            # Draw time
            draw_text_bitmap(ser, x, 28, city_data['time'], time_color, scale=1, rotated=True)

    # Only send keep-alive when no drawing happens
    if not minute_changed and not first_draw:
        send_keep_alive(ser)


def main():
    """Main application"""
    print("="*60)
    print("MSC World Clock Display (90° ROTATED)")
    print("="*60)
    print("\n🌍 World Clock - 4 Cities")
    print("  Shanghai (Asia/Shanghai)")
    print("  Berlin (Europe/Berlin)")
    print("  Vancouver (America/Vancouver)")
    print("  Washington DC (America/New_York)")
    print("\n🔄 Auto-reconnect mode enabled")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # Wait for device connection
            ser = wait_for_msc_device(retry_interval=5)

            # Keep LCD in landscape mode, but arrange content for 90° physical rotation
            display = MSCDisplay(ser)
            display.set_orientation(landscape=True)

            print("\n✓ Device ready")
            print("✓ World clock activated (Landscape mode with rotated layout)...")
            print("✓ Screen: 160x80 pixels (arrange for 90° physical rotation)")
            print("\nUpdating every minute...\n")

            first = True
            last_minute = -1

            try:
                while True:
                    # Check if device is still connected
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break  # Break inner loop to reconnect

                    # Get current time
                    now = datetime.now()
                    current_minute = now.minute

                    # Check if minute changed
                    minute_changed = (current_minute != last_minute)

                    if minute_changed:
                        last_minute = current_minute

                    # Only update display when minute changes
                    if first or minute_changed:
                        display_world_clock(ser, first_draw=first, minute_changed=minute_changed)
                        first = False

                        # Print all city times
                        if minute_changed:
                            print(f"\n🌍 World Time Update:")
                            for city in WORLD_CITIES:
                                city_data = get_city_time(city['timezone'])
                                print(f"   {city['name']:12} {city_data['time']}")

                    # Wait 4 second before next check
                    time.sleep(4)

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
