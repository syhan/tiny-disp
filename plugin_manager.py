#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Plugin Manager - Manages display plugins
插件管理器 - 管理所有显示插件
"""

import importlib
import os
import sys
from typing import List, Optional, Type
import serial

from lib.display_interface import DisplayPlugin, DisplayConfig
from logger import get_logger

logger = get_logger()


class PluginManager:
    """Manages loading and switching between display plugins"""

    def __init__(self, ser: serial.Serial, plugin_dir: str = "plugins"):
        """
        Initialize plugin manager

        Args:
            ser: Serial connection to MSC device
            plugin_dir: Directory containing plugin modules
        """
        self.ser = ser
        self.plugin_dir = plugin_dir
        self.plugins: List[Type[DisplayPlugin]] = []
        self.current_plugin: Optional[DisplayPlugin] = None
        self.config = DisplayConfig()

    def discover_plugins(self) -> int:
        """
        Discover and load all available plugins from plugins directory

        Returns:
            int: Number of plugins loaded
        """
        self.plugins.clear()

        # Check if plugin directory exists
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory '{self.plugin_dir}' not found")
            return 0

        # Add plugin directory to path
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        # Automatically discover all plugin_*.py files
        plugin_files = []
        for filename in os.listdir(self.plugin_dir):
            if filename.startswith('plugin_') and filename.endswith('.py'):
                module_name = filename[:-3]  # Remove .py extension
                plugin_files.append(module_name)

        # Sort for consistent ordering
        plugin_files.sort()

        # Load each plugin module
        for module_name in plugin_files:
            try:
                # Try to import the module
                module = importlib.import_module(module_name)

                # Look for DisplayPlugin subclass
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, DisplayPlugin) and
                            attr is not DisplayPlugin):
                        self.plugins.append(attr)
                        logger.info(f"Loaded plugin: {module_name}")
                        break

            except ImportError as e:
                logger.warning(f"Failed to load {module_name}: {e}")
            except Exception as e:
                logger.warning(f"Error loading {module_name}: {e}")

        return len(self.plugins)

    def load_plugin_by_file(self, plugin_file: str) -> Optional[Type[DisplayPlugin]]:
        """
        Load a specific plugin by filename without discovering all plugins

        Args:
            plugin_file: Plugin filename (e.g., 'plugin_clock' or 'plugin_clock.py')

        Returns:
            Plugin class or None if not found
        """
        # Check if plugin directory exists
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory '{self.plugin_dir}' not found")
            return None

        # Add plugin directory to path
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        # Remove .py extension if provided
        if plugin_file.endswith('.py'):
            module_name = plugin_file[:-3]
        else:
            module_name = plugin_file

        # Ensure it starts with plugin_
        if not module_name.startswith('plugin_'):
            module_name = 'plugin_' + module_name

        # Check if the file exists
        plugin_path = os.path.join(self.plugin_dir, f"{module_name}.py")
        if not os.path.exists(plugin_path):
            logger.warning(f"Plugin file '{module_name}.py' not found")
            return None

        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Look for DisplayPlugin subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, DisplayPlugin) and
                        attr is not DisplayPlugin):
                    logger.info(f"Loaded plugin: {module_name}")
                    return attr

            logger.warning(f"No DisplayPlugin subclass found in {module_name}")
            return None

        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error loading {module_name}: {e}")
            return None

    def list_plugins(self) -> List[dict]:
        """
        Get list of available plugins

        Returns:
            List of plugin info dictionaries
        """
        plugin_list = []
        for i, plugin_class in enumerate(self.plugins):
            # Create temporary instance to get info
            temp_instance = plugin_class(self.ser)
            plugin_list.append({
                'index': i,
                'name': temp_instance.get_name(),
                'description': temp_instance.get_description(),
                'update_interval': temp_instance.get_update_interval()
            })
        return plugin_list

    def get_plugin_by_index(self, index: int) -> Optional[Type[DisplayPlugin]]:
        """
        Get plugin class by index

        Args:
            index: Plugin index

        Returns:
            Plugin class or None if index invalid
        """
        if 0 <= index < len(self.plugins):
            return self.plugins[index]
        return None

    def get_plugin_by_name(self, name: str) -> Optional[Type[DisplayPlugin]]:
        """
        Get plugin class by name

        Args:
            name: Plugin name

        Returns:
            Plugin class or None if not found
        """
        for plugin_class in self.plugins:
            temp_instance = plugin_class(self.ser)
            if temp_instance.get_name().lower() == name.lower():
                return plugin_class
        return None

    def switch_plugin(self, plugin_class: Type[DisplayPlugin]) -> bool:
        """
        Switch to a different plugin

        Args:
            plugin_class: Plugin class to switch to

        Returns:
            bool: True if switched successfully
        """
        # Stop current plugin
        if self.current_plugin:
            logger.info(f"Stopping: {self.current_plugin.get_name()}")
            self.current_plugin.stop()
            self.current_plugin = None

        # Start new plugin
        try:
            self.current_plugin = plugin_class(self.ser)
            if self.current_plugin.start():
                logger.info(f"Started: {self.current_plugin.get_name()}")
                return True
            else:
                logger.error(f"Failed to start: {self.current_plugin.get_name()}")
                self.current_plugin = None
                return False
        except Exception as e:
            logger.error(f"Error starting plugin: {e}")
            self.current_plugin = None
            return False

    def switch_to_index(self, index: int) -> bool:
        """
        Switch to plugin by index

        Args:
            index: Plugin index

        Returns:
            bool: True if switched successfully
        """
        plugin_class = self.get_plugin_by_index(index)
        if plugin_class:
            return self.switch_plugin(plugin_class)
        return False

    def switch_to_name(self, name: str) -> bool:
        """
        Switch to plugin by name

        Args:
            name: Plugin name

        Returns:
            bool: True if switched successfully
        """
        plugin_class = self.get_plugin_by_name(name)
        if plugin_class:
            return self.switch_plugin(plugin_class)
        return False

    def get_current_plugin(self) -> Optional[DisplayPlugin]:
        """
        Get current active plugin

        Returns:
            Current plugin instance or None
        """
        return self.current_plugin

    def update_current_plugin(self) -> bool:
        """
        Update the current plugin display

        Returns:
            bool: True if updated successfully
        """
        if self.current_plugin and self.current_plugin.is_running:
            try:
                # Wake device from screensaver before updating
                self.current_plugin.wake_device()
                return self.current_plugin.update()
            except Exception as e:
                logger.error(f"Error updating plugin: {e}")
                return False
        return False

    def cleanup(self):
        """Cleanup all resources"""
        if self.current_plugin:
            self.current_plugin.stop()
            self.current_plugin = None
