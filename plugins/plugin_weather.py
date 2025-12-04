#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Weather Display Plugin
天气显示插件
"""

import time
import requests
import serial

from lib.display_interface import DisplayPlugin
from lib.msc_display_lib import (
    MSCDisplay,
    Colors,
    draw_text_bitmap,
    draw_rect,
    clear_screen,
    send_keep_alive
)


class WeatherPlugin(DisplayPlugin):
    """Weather Display Plugin"""

    def __init__(self, ser: serial.Serial):
        super().__init__(ser)
        self.display = None
        self.weather_data = None

    def get_name(self) -> str:
        return "Weather"

    def get_description(self) -> str:
        return "Display weather information (90° rotated)"

    def get_update_interval(self) -> int:
        return 600  # Update every 10 minutes

    def initialize(self) -> bool:
        """Initialize the weather display"""
        try:
            self.display = MSCDisplay(self.ser)
            self.display.set_orientation(landscape=True)
            return True
        except Exception as e:
            print(f"Weather plugin initialization error: {e}")
            return False

    def update(self) -> bool:
        """Update the weather display"""
        try:
            # Get weather data
            self.weather_data = self._get_weather_data()
            self._display_weather_info(first_draw=self.first_draw)
            self.first_draw = False
            return True
        except Exception as e:
            print(f"Weather update error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.display = None
        self.weather_data = None

    def _get_weather_data(self):
        """Get weather data using wttr.in service"""
        try:
            response = requests.get('https://wttr.in/?format=j1', timeout=10)

            if response.status_code == 200:
                data = response.json()

                current = data['current_condition'][0]
                today = data['weather'][0]
                astronomy = today['astronomy'][0]

                temp_c = int(current['temp_C'])
                humidity = int(current['humidity'])
                weather_desc = current['weatherDesc'][0]['value'][:15]

                try:
                    aqi = int(current.get('air_quality', {}).get('pm2_5', 0))
                    if aqi == 0:
                        aqi = int(current.get('uvIndex', 0))
                        aqi_label = f"UV{aqi}"
                    else:
                        aqi_label = f"PM{aqi}"
                except:
                    aqi = 0
                    aqi_label = "N/A"

                sunrise = astronomy['sunrise']
                sunset = astronomy['sunset']

                try:
                    location = data['nearest_area'][0]['areaName'][0]['value'][:15]
                except:
                    location = "Unknown"

                feels_like = int(current['FeelsLikeC'])
                wind_speed = int(current['windspeedKmph'])

                return {
                    'temp': temp_c,
                    'humidity': humidity,
                    'weather': weather_desc,
                    'aqi': aqi_label,
                    'sunrise': sunrise,
                    'sunset': sunset,
                    'location': location,
                    'feels_like': feels_like,
                    'wind': wind_speed,
                }
            else:
                print(f"Weather API error: {response.status_code}")
                return None

        except requests.Timeout:
            print("Weather API timeout")
            return None
        except Exception as e:
            print(f"Error getting weather: {e}")
            return None

    def _display_weather_info(self, first_draw=False):
        """Display weather information in Matrix style"""
        BLACK = Colors.BLACK
        DARK_GREEN = Colors.DARK_GREEN
        GREEN = Colors.GREEN
        BRIGHT_GREEN = Colors.BRIGHT_GREEN
        CYAN = Colors.CYAN
        YELLOW = Colors.YELLOW
        ORANGE = Colors.ORANGE
        RED = Colors.RED

        send_keep_alive(self.ser)
        time.sleep(0.02)

        if first_draw:
            clear_screen(self.ser, BLACK)

            if self.weather_data:
                # Labels on left side
                draw_text_bitmap(self.ser, 2, 48, "TEMP:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 20, 48, "FEEL:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 38, 48, "HUM:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 56, 48, "AQI:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 74, 48, "WIND:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 92, 48, "RISE:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 110, 48, "SET:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 128, 48, "COND:", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 146, 48, "LOC:", DARK_GREEN, scale=1, rotated=True)
            else:
                draw_text_bitmap(self.ser, 40, 20, "WEATHER", DARK_GREEN, scale=1, rotated=True)
                draw_text_bitmap(self.ser, 55, 20, "ERROR", RED, scale=1, rotated=True)

        send_keep_alive(self.ser)

        if self.weather_data:
            # Temperature with color coding
            draw_rect(self.ser, 2, 2, 16, 42, BLACK)
            temp = self.weather_data['temp']
            if temp >= 35:
                temp_color = RED
            elif temp >= 30:
                temp_color = ORANGE
            elif temp >= 25:
                temp_color = YELLOW
            elif temp >= 15:
                temp_color = GREEN
            else:
                temp_color = CYAN
            temp_str = f"{temp}C"
            draw_text_bitmap(self.ser, 2, 2, temp_str, temp_color, scale=1, rotated=True)

            # Feels like
            draw_rect(self.ser, 20, 2, 16, 42, BLACK)
            feel_str = f"{self.weather_data['feels_like']}C"
            draw_text_bitmap(self.ser, 20, 2, feel_str, GREEN, scale=1, rotated=True)

            # Humidity
            draw_rect(self.ser, 38, 2, 16, 42, BLACK)
            hum_str = f"{self.weather_data['humidity']}%"
            draw_text_bitmap(self.ser, 38, 2, hum_str, CYAN, scale=1, rotated=True)

            # Air Quality
            draw_rect(self.ser, 56, 2, 16, 42, BLACK)
            aqi_str = self.weather_data['aqi']
            draw_text_bitmap(self.ser, 56, 2, aqi_str[:6], GREEN, scale=1, rotated=True)

            # Wind speed
            draw_rect(self.ser, 74, 2, 16, 42, BLACK)
            wind_str = f"{self.weather_data['wind']}K"
            draw_text_bitmap(self.ser, 74, 2, wind_str[:5], GREEN, scale=1, rotated=True)

            # Sunrise
            draw_rect(self.ser, 92, 2, 16, 42, BLACK)
            draw_text_bitmap(self.ser, 92, 2, self.weather_data['sunrise'][:5], YELLOW, scale=1, rotated=True)

            # Sunset
            draw_rect(self.ser, 110, 2, 16, 42, BLACK)
            draw_text_bitmap(self.ser, 110, 2, self.weather_data['sunset'][:5], ORANGE, scale=1, rotated=True)

            # Weather condition
            draw_rect(self.ser, 128, 2, 16, 42, BLACK)
            condition = self.weather_data['weather']
            if len(condition) > 5:
                line1 = condition[:5]
                draw_text_bitmap(self.ser, 128, 2, line1, BRIGHT_GREEN, scale=1, rotated=True)
            else:
                draw_text_bitmap(self.ser, 128, 2, condition, BRIGHT_GREEN, scale=1, rotated=True)

            # Location
            draw_rect(self.ser, 146, 2, 14, 76, BLACK)
            location = self.weather_data['location']
            draw_text_bitmap(self.ser, 146, 2, location[:9], CYAN, scale=1, rotated=True)

        send_keep_alive(self.ser)

        if self.weather_data:
            print(f"🌤️  Weather: {self.weather_data['temp']}°C, {self.weather_data['humidity']}%, {self.weather_data['weather']}, AQI: {self.weather_data['aqi']}")
        else:
            print("🌤️  Weather data unavailable")
