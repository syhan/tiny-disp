#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Tiny Display - Main Program
统一显示接口主程序 - 可插拔式显示系统
"""

import time
import sys
from typing import Optional

from lib.msc_display_lib import wait_for_msc_device, is_device_connected
from plugin_manager import PluginManager
from logger import get_logger

# Initialize logger
logger = get_logger()


def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("Tiny Display - Pluggable Display System")
    print("可插拔式显示系统")
    print("=" * 60)
    print()


def print_menu(manager: PluginManager):
    """Print plugin selection menu"""
    print("\n" + "=" * 60)
    print("Available Display Plugins:")
    print("=" * 60)

    plugins = manager.list_plugins()
    for plugin in plugins:
        print(f"• {plugin['name']}")
        print(f"  {plugin['description']}")
        print(f"  Update interval: {plugin['update_interval']}s")
        print()

    current = manager.get_current_plugin()
    if current:
        print(f"Current: {current.get_name()}")
    else:
        print("Current: None")
    print("=" * 60)


def run_plugin_loop(manager: PluginManager):
    """Run the main plugin update loop"""
    print("\n✓ Plugin started successfully")
    print("✓ Press Ctrl+C to switch plugins or exit\n")

    current_plugin = manager.get_current_plugin()
    if not current_plugin:
        print("⚠️  No plugin active")
        return

    update_interval = current_plugin.get_update_interval()
    keepalive_interval = 3  # Send keep-alive every 3 seconds

    try:
        while True:
            # Check device connection
            if not is_device_connected(manager.ser):
                print("\n⚠️  Device disconnected!")
                return

            # Update plugin
            try:
                if not manager.update_current_plugin():
                    print("⚠️  Plugin update failed, returning to menu...")
                    manager.cleanup()  # This will stop and clear current plugin
                    time.sleep(2)
                    break  # Return to plugin selection menu
            except Exception as e:
                print(f"⚠️  Plugin error: {e}")
                manager.cleanup()  # This will stop and clear current plugin
                time.sleep(2)
                break  # Return to plugin selection menu

            # Wait with periodic keep-alives
            elapsed = 0
            while elapsed < update_interval:
                if not is_device_connected(manager.ser):
                    print("\n⚠️  Device disconnected!")
                    return

                time.sleep(keepalive_interval)
                elapsed += keepalive_interval

    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
        raise


def select_plugin_interactive(manager: PluginManager) -> bool:
    """Interactive plugin selection with keep-alive support"""
    import threading
    from lib.msc_display_lib import send_keep_alive, wake_from_screensaver

    print_menu(manager)

    # Start keep-alive thread
    keep_alive_active = True

    def keep_alive_worker():
        """Background thread to send keep-alive"""
        last_keepalive = time.time()
        while keep_alive_active:
            if time.time() - last_keepalive > 3:
                try:
                    send_keep_alive(manager.ser)
                    last_keepalive = time.time()
                except:
                    pass
            time.sleep(0.5)

    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive_worker, daemon=True)
    keep_alive_thread.start()

    try:
        choice = input("\nEnter plugin name (or 'q' to quit): ").strip()
        keep_alive_active = False  # Stop keep-alive thread

        if choice.lower() == 'q':
            return False

        if not choice:
            print("⚠️  Please enter a plugin name")
            time.sleep(1)
            return True

        # Wake device before switching plugin
        wake_from_screensaver(manager.ser)

        # Try to switch to plugin by name
        if manager.switch_to_name(choice):
            return True
        else:
            print(f"⚠️  Plugin '{choice}' not found")
            print("   Please check the plugin name and try again")
            time.sleep(2)
            return True

    except KeyboardInterrupt:
        keep_alive_active = False
        print("\n")
        return False


def main():
    """Main application entry point"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Tiny Display - Pluggable Display System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode (default)
  python3 main.py
  python3 main.py --interactive

  # Run specific plugin by filename
  python3 main.py --plugin plugin_clock
  python3 main.py --plugin plugin_metrics
  python3 main.py --plugin plugin_sample

  # List available plugins
  python3 main.py --list
        '''
    )
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Interactive mode (select plugins from menu)')
    parser.add_argument('-p', '--plugin', type=str,
                       help='Plugin to run (by filename, e.g., plugin_clock)')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List available plugins and exit')

    args = parser.parse_args()

    print_banner()

    # Determine mode
    interactive_mode = args.interactive or (not args.plugin and not args.list)
    plugin_to_run = args.plugin

    try:
        while True:
            # Wait for device connection
            ser = wait_for_msc_device(retry_interval=5, silent=False)

            print("✓ Device connected\n")

            # Initialize plugin manager
            manager = PluginManager(ser)

            # Handle non-interactive mode with specific plugin (no need to discover all)
            if not interactive_mode and plugin_to_run and not args.list:
                print(f"🚀 Loading plugin: {plugin_to_run}")

                # Load only the requested plugin by filename
                plugin_class = manager.load_plugin_by_file(plugin_to_run)

                if not plugin_class:
                    print(f"⚠️  Plugin file '{plugin_to_run}' not found!")
                    print("\nPlugin filename examples:")
                    print("  plugin_clock")
                    print("  plugin_metrics")
                    print("  plugin_sample")
                    print("\nTo see all available plugins, run:")
                    print("  python3 main.py --list")
                    return

                # Start the plugin directly
                if not manager.switch_plugin(plugin_class):
                    print(f"⚠️  Failed to start plugin")
                    return

                # Run plugin continuously (non-interactive)
                try:
                    while True:
                        if not is_device_connected(ser):
                            print("\n⚠️  Device disconnected!")
                            break

                        run_plugin_loop(manager)
                except KeyboardInterrupt:
                    print("\n\n👋 Exiting...")
                finally:
                    manager.cleanup()
                    ser.close()
                return

            # Discover plugins for interactive mode or list mode
            print("🔍 Discovering plugins...")
            plugin_count = manager.discover_plugins()

            if plugin_count == 0:
                print("⚠️  No plugins found!")
                print("Please ensure plugin files are in the plugins directory.")
                time.sleep(5)
                continue

            print(f"✓ Found {plugin_count} plugin(s)\n")

            # Handle --list mode
            if args.list:
                print_menu(manager)
                return

            # Interactive mode
            try:
                while True:
                    # Check device connection
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        manager.cleanup()
                        break

                    # Select plugin if none active
                    if not manager.get_current_plugin():
                        if not select_plugin_interactive(manager):
                            # User wants to quit
                            raise KeyboardInterrupt

                    # Run plugin loop
                    if manager.get_current_plugin():
                        try:
                            run_plugin_loop(manager)
                        except KeyboardInterrupt:
                            # User interrupted, return to menu
                            print("\n🔄 Returning to menu...")
                            if manager.get_current_plugin():
                                manager.get_current_plugin().stop()
                            time.sleep(1)
                            continue

                    # Check connection again before continuing
                    if not is_device_connected(ser):
                        print("\n⚠️  Device disconnected!")
                        manager.cleanup()
                        break

            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                manager.cleanup()
                try:
                    ser.close()
                except:
                    pass
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        try:
            if 'manager' in locals():
                manager.cleanup()
            if 'ser' in locals():
                ser.close()
        except:
            pass
        print("✓ Cleanup complete")


if __name__ == "__main__":
    main()
