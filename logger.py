#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Logger Module
日志模块 - 统一的日志管理
"""

import logging
import sys
from typing import Optional


class TinyDispLogger:
    """Tiny Display Logger with configurable log levels"""

    # Log level mapping
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, name: str = 'TinyDisp', level: str = 'INFO'):
        """
        Initialize logger

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.set_level(level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Formatter with colors for terminal
        formatter = ColoredFormatter(
            '%(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def set_level(self, level: str):
        """Set log level"""
        level_value = self.LEVELS.get(level.upper(), logging.INFO)
        self.logger.setLevel(level_value)

    def debug(self, msg: str):
        """Log debug message"""
        self.logger.debug(msg)

    def info(self, msg: str):
        """Log info message"""
        self.logger.info(msg)

    def warning(self, msg: str):
        """Log warning message"""
        self.logger.warning(msg)

    def error(self, msg: str):
        """Log error message"""
        self.logger.error(msg)

    def critical(self, msg: str):
        """Log critical message"""
        self.logger.critical(msg)


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    # Emoji prefixes
    EMOJI = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠️',
        'ERROR': '✗',
        'CRITICAL': '🚨'
    }

    def format(self, record):
        """Format log record with colors and emoji"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS['RESET'])
        emoji = self.EMOJI.get(levelname, '')
        reset = self.COLORS['RESET']

        # Format: emoji LEVEL - message
        record.levelname = f"{emoji} {levelname}"
        formatted = super().format(record)

        return f"{color}{formatted}{reset}"


# Global logger instance
_logger_instance: Optional[TinyDispLogger] = None


def get_logger(level: Optional[str] = None) -> TinyDispLogger:
    """
    Get global logger instance

    Args:
        level: Optional log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        TinyDispLogger: Global logger instance
    """
    global _logger_instance

    if _logger_instance is None:
        # Load log level from config if available
        if level is None:
            try:
                from config_loader import get_config
                config = get_config()
                if config.config.has_option('general', 'log_level'):
                    level = config.config.get('general', 'log_level')
                else:
                    level = 'INFO'
            except:
                level = 'INFO'

        _logger_instance = TinyDispLogger(level=level)
    elif level is not None:
        _logger_instance.set_level(level)

    return _logger_instance


# Convenience functions
def debug(msg: str):
    """Log debug message"""
    get_logger().debug(msg)


def info(msg: str):
    """Log info message"""
    get_logger().info(msg)


def warning(msg: str):
    """Log warning message"""
    get_logger().warning(msg)


def error(msg: str):
    """Log error message"""
    get_logger().error(msg)


def critical(msg: str):
    """Log critical message"""
    get_logger().critical(msg)
