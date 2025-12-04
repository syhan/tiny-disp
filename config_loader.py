#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Configuration Loader
配置文件加载器
"""

import configparser
import os
from typing import Dict, Any


class ConfigLoader:
    """Load and manage configuration from .tiny-disp.conf"""

    def __init__(self, config_file: str = ".tiny-disp.conf"):
        """
        Initialize configuration loader

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            print(f"⚠️  Config file not found: {self.config_file}")
            print("Using default configuration")

    def get_clock_config(self) -> Dict[str, Any]:
        """Get clock plugin configuration"""
        if 'clock' not in self.config:
            return {
                'cities': {
                    'Shanghai': 'Asia/Shanghai',
                    'Berlin': 'Europe/Berlin',
                    'Vancouver': 'America/Vancouver',
                    'Washington': 'America/New_York'
                }
            }

        cities_str = self.config.get('clock', 'cities', fallback='Shanghai:Asia/Shanghai')
        cities = {}
        for city_pair in cities_str.split(','):
            if ':' in city_pair:
                name, tz = city_pair.strip().split(':', 1)
                cities[name] = tz

        return {'cities': cities}

    def get_weather_config(self) -> Dict[str, Any]:
        """Get weather plugin configuration"""
        return {
            'location': self.config.get('weather', 'location', fallback='Shanghai'),
            'update_interval': self.config.getint('weather', 'update_interval', fallback=600)
        }

    def get_zfs_config(self) -> Dict[str, Any]:
        """Get ZFS plugin configuration"""
        return {
            'host': self.config.get('zfs', 'host', fallback='10.0.0.129'),
            'user': self.config.get('zfs', 'user', fallback='root'),
            'password': self.config.get('zfs', 'password', fallback=''),
            'port': self.config.getint('zfs', 'port', fallback=22),
            'pool_name': self.config.get('zfs', 'pool_name', fallback='tank'),
            'update_interval': self.config.getint('zfs', 'update_interval', fallback=15)
        }

    def get_zfs_pages_config(self) -> Dict[str, Any]:
        """Get ZFS pages plugin configuration"""
        # Start with base ZFS config
        config = self.get_zfs_config()

        # Add pages-specific settings
        if 'zfs_pages' in self.config:
            datasets_str = self.config.get('zfs_pages', 'datasets', fallback='archives,photos,music,videos')
            config['datasets'] = [ds.strip() for ds in datasets_str.split(',')]
            config['page_duration'] = self.config.getint('zfs_pages', 'page_duration', fallback=4)
            config['update_interval'] = self.config.getint('zfs_pages', 'update_interval', fallback=1)
        else:
            config['datasets'] = ['archives', 'photos', 'music', 'videos']
            config['page_duration'] = 4
            config['update_interval'] = 1

        return config

    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics plugin configuration"""
        return {
            'update_interval': self.config.getint('metrics', 'update_interval', fallback=10)
        }

    def get_metrics_rotated_config(self) -> Dict[str, Any]:
        """Get metrics rotated plugin configuration"""
        return {
            'update_interval': self.config.getint('metrics_rotated', 'update_interval', fallback=10)
        }


# Global config instance
_config_instance = None


def get_config() -> ConfigLoader:
    """
    Get global configuration instance

    Returns:
        ConfigLoader: Global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
