#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Sample Display Plugin - Hello World
示例显示插件 - 显示 Hello World
"""

from lib.display_interface import DisplayPlugin
from lib.msc_display_lib import *
from config_loader import ConfigLoader
from logger import get_logger

# Initialize logger
logger = get_logger()


class HelloWorldPlugin(DisplayPlugin):
    """
    Hello World Sample Plugin
    在横屏模式下显示 "HELLO WORLD" 文本
    """

    def __init__(self, ser):
        """Initialize plugin"""
        super().__init__(ser)
        self.config = ConfigLoader()

        # 配置参数
        self.text = "HELLO WORLD"
        self.text_color = 0xFFFF  # 白色
        self.bg_color = 0x0000     # 黑色
        self.update_count = 0

    def get_name(self) -> str:
        """Get plugin name"""
        return "Hello World Sample"

    def get_description(self) -> str:
        """Get plugin description"""
        return "Display 'HELLO WORLD' in landscape mode (sample plugin)"

    def get_update_interval(self) -> int:
        """Get update interval in seconds"""
        return 5  # 每5秒更新一次

    def initialize(self) -> bool:
        """
        Initialize the display plugin
        设置横屏模式并清屏
        """
        try:
            logger.info("Initializing Hello World plugin...")

            # 清屏 (黑色背景)
            clear_screen(self.ser, self.bg_color)

            logger.info("✓ Hello World plugin initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Hello World plugin: {e}")
            return False

    def update(self) -> bool:
        """
        Update the display
        显示 "HELLO WORLD" 文本
        """
        try:
            if self.first_draw:
                logger.info("Drawing Hello World for the first time...")
                self.first_draw = False

            # 唤醒屏幕
            self.wake_device()

            # 清除屏幕
            clear_screen(self.ser, self.bg_color)

            # 计算文本位置 (居中显示)
            # 屏幕尺寸: 160x80
            # 每个字符: 8x16像素
            # "HELLO WORLD" = 11个字符
            text_width = len(self.text) * 8
            text_height = 16

            # 居中坐标
            x = (160 - text_width) // 2  # 横向居中
            y = (80 - text_height) // 2   # 纵向居中

            # 绘制文本 (使用实际可用的函数)
            draw_text_bitmap(
                self.ser,
                x, y,
                self.text,
                self.text_color,
                scale=2,  # 使用2倍大小
                rotated=False  # 横屏模式
            )

            # 在底部显示更新计数
            self.update_count += 1
            counter_text = f"Updates: {self.update_count}"
            draw_text_bitmap(
                self.ser,
                10, 65,  # 底部位置
                counter_text,
                0x07E0,  # 绿色
                scale=1,  # 正常大小
                rotated=False
            )

            logger.debug(f"Hello World updated (count: {self.update_count})")
            return True

        except Exception as e:
            logger.error(f"Failed to update Hello World display: {e}")
            return False

    def cleanup(self):
        """
        Cleanup resources
        清理资源并清屏
        """
        try:
            logger.info("Cleaning up Hello World plugin...")

            # 清屏
            clear_screen(self.ser, 0x0000)

            # 显示退出消息
            draw_text_bitmap(
                self.ser,
                50, 32,
                "Goodbye!",
                0xF800,  # 红色
                scale=2,  # 2倍大小
                rotated=False
            )

            # 等待一下让用户看到消息
            import time
            time.sleep(1)

            # 最后清屏
            clear_screen(self.ser, 0x0000)

            logger.info("✓ Hello World plugin cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# ============================================================
# 以下是高级示例，展示彩虹颜色循环
# ============================================================

class HelloWorldAdvancedPlugin(DisplayPlugin):
    """
    Advanced Hello World Plugin
    高级示例 - 彩虹颜色循环动画
    """

    def __init__(self, ser):
        """Initialize plugin"""
        super().__init__(ser)
        self.config = ConfigLoader()

        # 彩虹颜色列表
        self.colors = [
            0xF800,  # 红色
            0xFD20,  # 橙色
            0xFFE0,  # 黄色
            0x07E0,  # 绿色
            0x001F,  # 蓝色
            0x781F,  # 靛色
            0xF81F,  # 紫色
        ]
        self.color_index = 0

    def get_name(self) -> str:
        return "Hello World Advanced"

    def get_description(self) -> str:
        return "Rainbow color cycling animation"

    def get_update_interval(self) -> int:
        return 2  # 每2秒更新（更快的动画）

    def initialize(self) -> bool:
        """Initialize display"""
        try:
            clear_screen(self.ser, 0x0000)
            return True
        except Exception as e:
            logger.error(f"Initialize error: {e}")
            return False

    def update(self) -> bool:
        """Update with color animation"""
        try:
            self.wake_device()

            # 清屏
            clear_screen(self.ser, 0x0000)

            # 获取当前颜色
            current_color = self.colors[self.color_index]

            # 绘制主文本 (彩色循环)
            draw_text_bitmap(
                self.ser,
                35, 25,
                "HELLO",
                current_color,
                scale=2,
                rotated=False
            )

            draw_text_bitmap(
                self.ser,
                35, 45,
                "WORLD",
                current_color,
                scale=2,
                rotated=False
            )

            # 底部说明
            draw_text_bitmap(
                self.ser,
                20, 68,
                "Rainbow mode",
                0xFFFF,
                scale=1,
                rotated=False
            )

            # 切换到下一个颜色
            self.color_index = (self.color_index + 1) % len(self.colors)

            return True

        except Exception as e:
            logger.error(f"Update error: {e}")
            return False

    def cleanup(self):
        """Cleanup"""
        try:
            clear_screen(self.ser, 0x0000)

            # 彩虹色再见消息
            colors_for_goodbye = [0xF800, 0xFD20, 0xFFE0, 0x07E0, 0x001F, 0x781F, 0xF81F, 0xFFFF]
            chars = "Goodbye!"
            x_start = 40

            for i, char in enumerate(chars):
                color = colors_for_goodbye[i % len(colors_for_goodbye)]
                draw_char_bitmap(self.ser, x_start + i * 12, 32, char, color, scale=2)

            import time
            time.sleep(2)
            clear_screen(self.ser, 0x0000)

        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# 导出插件类
# Plugin Manager 会自动识别 DisplayPlugin 的第一个子类
# 这里会加载 HelloWorldPlugin（基础版本）
__all__ = ['HelloWorldPlugin']

# 注意：由于 Python 的类定义顺序，Plugin Manager 会找到文件中
# 第一个 DisplayPlugin 的子类。如果你想使用高级版本，
# 可以交换两个类的定义顺序，或者在 __all__ 中指定
