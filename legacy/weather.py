#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
MSC Device Weather Display - Matrix Style (90° Rotated - Portrait Mode)
显示当前位置天气预报 (90度旋转 - 竖屏模式)
"""

import time
from datetime import datetime
import requests

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


def get_weather_data():
    """Get weather data using wttr.in service (no API key needed)"""
    try:
        # Use wttr.in for weather data - automatic location detection
        # Format: JSON output
        response = requests.get('https://wttr.in/?format=j1', timeout=10)

        if response.status_code == 200:
            data = response.json()

            current = data['current_condition'][0]
            today = data['weather'][0]
            astronomy = today['astronomy'][0]

            # Extract weather info
            temp_c = int(current['temp_C'])
            humidity = int(current['humidity'])
            weather_desc = current['weatherDesc'][0]['value'][:15]

            # Air quality - use PM2.5 if available, otherwise UV index as proxy
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

            # Sunrise and sunset
            sunrise = astronomy['sunrise']
            sunset = astronomy['sunset']

            # Location
            try:
                location = data['nearest_area'][0]['areaName'][0]['value'][:15]
            except:
                location = "Unknown"

            # Feels like temperature
            feels_like = int(current['FeelsLikeC'])

            # Wind speed
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




def display_weather_info(ser, weather, first_draw=False):
    """Display weather information in Matrix style"""

    # Use color constants from shared library
    BLACK = Colors.BLACK
    DARK_GREEN = Colors.DARK_GREEN
    GREEN = Colors.GREEN
    BRIGHT_GREEN = Colors.BRIGHT_GREEN
    CYAN = Colors.CYAN
    YELLOW = Colors.YELLOW
    ORANGE = Colors.ORANGE
    RED = Colors.RED
    BLUE = Colors.BLUE

    # Reset LCD
    send_keep_alive(ser)
    time.sleep(0.02)

    if first_draw:
        clear_screen(ser, BLACK)

        if weather:
            # Labels on left side
            draw_text_bitmap(ser, 2, 48, "TEMP:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 20, 48, "FEEL:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 38, 48, "HUM:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 56, 48, "AQI:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 74, 48, "WIND:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 92, 48, "RISE:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 110, 48, "SET:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 128, 48, "COND:", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 146, 48, "LOC:", DARK_GREEN, scale=1, rotated=True)
        else:
            # Error message
            draw_text_bitmap(ser, 40, 20, "WEATHER", DARK_GREEN, scale=1, rotated=True)
            draw_text_bitmap(ser, 55, 20, "ERROR", RED, scale=1, rotated=True)

    # Send keep-alive
    send_keep_alive(ser)

    if weather:
        # Temperature with color coding
        draw_rect(ser, 2, 2, 16, 42, BLACK)
        temp = weather['temp']
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
        draw_text_bitmap(ser, 2, 2, temp_str, temp_color, scale=1, rotated=True)

        # Feels like
        draw_rect(ser, 20, 2, 16, 42, BLACK)
        feel_str = f"{weather['feels_like']}C"
        draw_text_bitmap(ser, 20, 2, feel_str, GREEN, scale=1, rotated=True)

        # Humidity
        draw_rect(ser, 38, 2, 16, 42, BLACK)
        hum_str = f"{weather['humidity']}%"
        draw_text_bitmap(ser, 38, 2, hum_str, CYAN, scale=1, rotated=True)

        # Air Quality
        draw_rect(ser, 56, 2, 16, 42, BLACK)
        aqi_str = weather['aqi']
        draw_text_bitmap(ser, 56, 2, aqi_str[:6], GREEN, scale=1, rotated=True)

        # Wind speed
        draw_rect(ser, 74, 2, 16, 42, BLACK)
        wind_str = f"{weather['wind']}K"
        draw_text_bitmap(ser, 74, 2, wind_str[:5], GREEN, scale=1, rotated=True)

        # Sunrise
        draw_rect(ser, 92, 2, 16, 42, BLACK)
        draw_text_bitmap(ser, 92, 2, weather['sunrise'][:5], YELLOW, scale=1, rotated=True)

        # Sunset
        draw_rect(ser, 110, 2, 16, 42, BLACK)
        draw_text_bitmap(ser, 110, 2, weather['sunset'][:5], ORANGE, scale=1, rotated=True)

        # Weather condition (multiple lines)
        draw_rect(ser, 128, 2, 16, 42, BLACK)
        condition = weather['weather']
        if len(condition) > 5:
            line1 = condition[:5]
            draw_text_bitmap(ser, 128, 2, line1, BRIGHT_GREEN, scale=1, rotated=True)
        else:
            draw_text_bitmap(ser, 128, 2, condition, BRIGHT_GREEN, scale=1, rotated=True)

        # Location (at bottom)
        draw_rect(ser, 146, 2, 14, 76, BLACK)
        location = weather['location']
        draw_text_bitmap(ser, 146, 2, location[:9], CYAN, scale=1, rotated=True)

    # Final keep-alive
    send_keep_alive(ser)

    if weather:
        print(f"🌤️  Weather: {weather['temp']}°C, {weather['humidity']}%, {weather['weather']}, AQI: {weather['aqi']}")
    else:
        print("🌤️  Weather data unavailable")


def main():
    """Main application"""
    print("="*60)
    print("MSC Weather Display - MATRIX STYLE (90° ROTATED)")
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

            print("\n✓ Device ready")
            print("✓ Matrix mode activated...")
            print("✓ Screen: 160x80 pixels (arranged for 90° rotation)")
            print("✓ Using wttr.in for weather data (auto location)")
            print("\nUpdating every 10 minutes...\n")

            first = True
            update_interval = 600  # Update every 10 minutes
            keepalive_interval = 3

            try:
                while True:
                    # Check if device is still connected
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        ser.close()
                        break  # Break inner loop to reconnect

                    # Get weather data
                    weather = get_weather_data()
                    display_weather_info(ser, weather, first_draw=first)
                    first = False

                    # Wait with periodic keep-alives
                    elapsed = 0
                    while elapsed < update_interval:
                        if not is_device_connected(ser):
                            print("\n⚠️  Device disconnected!")
                            ser.close()
                            break

                        time.sleep(keepalive_interval)
                        elapsed += keepalive_interval

                        # Send keep-alive
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
        print("\n\n👁️ Exiting...")
        try:
            ser.close()
        except:
            pass
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
