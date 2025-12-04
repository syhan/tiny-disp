#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Clock Display Plugin
世界时钟显示插件
"""

import time
from datetime import datetime
import pytz
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
from config_loader import get_config




class ClockPlugin(DisplayPlugin):
    """World Clock Display Plugin"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None
        self.last_minute = -1

        # Load configuration
        config = get_config().get_clock_config()
        self.cities = []
        for name, tz in config['cities'].items():
            short_name = name[:8].upper()  # Limit to 8 chars for display
            self.cities.append({
                'name': short_name,
                'timezone': tz,
                'short': name[:3].upper()  # First 3 chars for short display
            })

    def get_name(self) -> str:
        return "World Clock"

    def get_description(self) -> str:
        return "Display world clock for multiple cities (90° rotated)"

    def get_update_interval(self) -> int:
        return 4  # Update every 4 seconds to check minute changes

    def initialize(self) -> bool:
        """Initialize the clock display"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            self.last_minute = -1
            return True
        except Exception as e:
            logger.error(f"Clock plugin initialization Error: {e}")
            return False

    def update(self) -> bool:
        """Update the clock display"""
        try:
            now = datetime.now()
            current_minute = now.minute
            minute_changed = (current_minute != self.last_minute)

            if minute_changed:
                self.last_minute = current_minute

            if self.first_draw or minute_changed:
                self._display_world_clock(first_draw=self.first_draw, minute_changed=minute_changed)
                self.first_draw = False

                if minute_changed:
                    logger.info(f"\n🌍 World Time Update:")
                    for city in self.cities:
                        city_data = self._get_city_time(city['timezone'])
                        logger.info(f"   {city['name']:12} {city_data['time']}")
            else:
                send_keep_alive(self.ser)

            return True
        except Exception as e:
            logger.error(f"Clock update Error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        self.last_minute = -1

    def _get_city_time(self, timezone_str):
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
            logger.info(f"Error getting time for {timezone_str}: {e}")
            return {
                'time': "--:--",
                'date': "--/--",
                'hour': 0
            }

    def _get_time_color(self, hour):
        """Get color based on time of day"""
        if 6 <= hour < 12:
            return Colors.YELLOW  # Morning
        elif 12 <= hour < 18:
            return Colors.ORANGE  # Afternoon
        elif 18 <= hour < 22:
            return Colors.CYAN  # Evening
        else:
            return Colors.BLUE  # Night

    def _display_world_clock(self, first_draw=False, minute_changed=False):
        """Display world clock for multiple cities"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN

        if first_draw:
            clear_screen(self.ser, BLACK)

            # Draw title at top (rotated text)
            draw_text_bitmap(self.ser, 2, 2, "WORLD", BRIGHT_GREEN, scale=1, rotated=True)
            draw_text_bitmap(self.ser, 2, 42, "CLOCK", BRIGHT_GREEN, scale=1, rotated=True)

            # Layout: 4 cities in rows
            x_positions = [25, 60, 95, 130]

            # Draw static city names (only once)
            for i, city_info in enumerate(self.cities):
                x = x_positions[i]
                draw_text_bitmap(self.ser, x, 2, city_info['short'], DARK_GREEN, scale=1, rotated=True)

            # Draw separator lines between cities (only once)
            for i in range(1, 4):
                x = x_positions[i] - 5
                # Dashed line
                for y in range(5, 75, 6):
                    draw_rect(self.ser, x, y, 1, 3, DARK_GREEN)

        # Only update times when minute changes
        if minute_changed or first_draw:
            x_positions = [25, 60, 95, 130]

            for i, city_info in enumerate(self.cities):
                x = x_positions[i]

                # Get time for this city
                city_data = self._get_city_time(city_info['timezone'])
                time_color = self._get_time_color(city_data['hour'])

                # Only clear and redraw the TIME area (not city name or separators)
                draw_rect(self.ser, x, 28, 30, 50, BLACK)  # Clear only time area

                # Draw time
                draw_text_bitmap(self.ser, x, 28, city_data['time'], time_color, scale=1, rotated=True)

        # Only send keep-alive when no drawing happens
        if not minute_changed and not first_draw:
            send_keep_alive(self.ser)
