#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Display Interface - Base class for all display plugins
统一的显示接口基类 - 所有显示插件的基础
"""

from abc import ABC, abstractmethod
from typing import Optional
import serial


class DisplayPlugin(ABC):
    """
    Abstract base class for all display plugins
    所有显示插件的抽象基类
    """

    def __init__(self, ser: serial.Serial):
        """
        Initialize display plugin

        Args:
            ser: Serial connection to MSC device
        """
        self.ser = ser
        self.is_running = False
        self.first_draw = True

    @abstractmethod
    def get_name(self) -> str:
        """
        Get plugin name

        Returns:
            str: Plugin display name
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get plugin description

        Returns:
            str: Brief description of what this plugin displays
        """
        pass

    @abstractmethod
    def get_update_interval(self) -> int:
        """
        Get update interval in seconds

        Returns:
            int: Seconds between updates
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the display plugin
        Called once when plugin is activated

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def update(self) -> bool:
        """
        Update the display
        Called periodically based on update_interval

        Returns:
            bool: True if update successful, False if error occurred
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Cleanup resources when plugin is deactivated
        Called when switching to another plugin or exiting
        """
        pass

    def start(self) -> bool:
        """
        Start the plugin

        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            return True

        if self.initialize():
            self.is_running = True
            self.first_draw = True
            return True
        return False

    def stop(self):
        """Stop the plugin"""
        if self.is_running:
            self.cleanup()
            self.is_running = False
            self.first_draw = True

    def is_device_connected(self) -> bool:
        """
        Check if device is still connected

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            from lib.msc_display_lib import send_keep_alive
            send_keep_alive(self.ser)
            return True
        except:
            return False

    def wake_device(self):
        """
        Wake device from screensaver if needed
        Should be called before any drawing operations
        """
        try:
            from lib.msc_display_lib import wake_from_screensaver
            wake_from_screensaver(self.ser)
        except:
            pass


class DisplayConfig:
    """Configuration for display plugins"""

    def __init__(self):
        """Initialize with default configuration"""
        self.rotation = 0  # 0, 90, 180, 270 degrees
        self.brightness = 100  # 0-100%
        self.auto_rotate = False
        self.screensaver_timeout = 0  # 0 = disabled, >0 = seconds

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'rotation': self.rotation,
            'brightness': self.brightness,
            'auto_rotate': self.auto_rotate,
            'screensaver_timeout': self.screensaver_timeout
        }

    def from_dict(self, data: dict):
        """Load config from dictionary"""
        self.rotation = data.get('rotation', 0)
        self.brightness = data.get('brightness', 100)
        self.auto_rotate = data.get('auto_rotate', False)
        self.screensaver_timeout = data.get('screensaver_timeout', 0)
