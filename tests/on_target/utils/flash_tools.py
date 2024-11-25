Flash Tool for Nordic Semiconductor Devices
    
    This module provides utilities for flashing and managing Nordic Semiconductor devices,
    particularly focusing on the Thingy:91 device family.

Copyright (c) 2024 Nordic Semiconductor
SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
"""

import subprocess
import os
import sys
from typing import Optional, Dict, List, Union
from pathlib import Path
import logging
from enum import Enum

from utils.logger import get_logger
from utils.thingy91x_dfu import detect_family_from_zip

# Constants
# DEFAULT_TIMEOUT = 30  # seconds
# NRFUTIL_CMD = "nrfutil"
# 
# class ResetKind(Enum):
#     """Enumeration of supported reset types."""
#     SYSTEM = "RESET_SYSTEM"
#     SOFT = "RESET_SOFT"
# 
# class FlashError(Exception):
#     """Custom exception for flash-related errors."""in    pass
# 
# class DeviceManager:
#     """Handles device management operations including reset and flashing."""flashing    
#     def __init__(self, logger: Optional[logging.Logger] = None):
#         """Initialize the DeviceManager.dfu_device        
#         Args:
#             logger: Optional logger instance. If None, a new logger will be created.
#         """
#         self.logger = logger or get_logger()
#         self.segger = os.getenv('SEGGER')
#         if not self.segger:
#             self.logger.warning("SEGGER environment variable not set")
# 
#     def reset_device(self, serial: str = None, reset_kind: str = "RESET_SYSTEM") -> bool:
#         """Reset a device using nrfutil.
#         
#         Args:
#             serial: Device serial number. Defaults to SEGGER env variable.
#             reset_kind: Type of reset to perform. Must be one of ResetKind values.
#             
#         Returns:
#             bool: True if reset was successful, False otherwise.
#             
#         Raises:
#             FlashError: If the reset operation fails.
#         """
#         serial = serial or self.segger
#         if not serial:
#             raise FlashError("No serial number provided and SEGGER env var not set")
#             
#         try:
#             reset_kind = ResetKind(reset_kind).value
#         except ValueError:
#             raise FlashError(f"Invalid reset kind: {reset_kind}")
#             
#         self.logger.info(f"Resetting device, segger: {serial}")
#         
#         try:
#             cmd = [
#                 NRFUTIL_CMD,
#                 "device",
#                 "reset",
#                 "--serial-number",
#                 serial,
#                 "--reset-kind",
#                 reset_kind
#             ]
#             
#             result = subprocess.run(
#                 cmd,
#                 capture_output=True,
#                 text=True,
#                 timeout=DEFAULT_TIMEOUT
#             )
#             
#             if result.returncode != 0:
#                 raise FlashError(f"Reset failed: {result.stderr}")
#                 
#             return True
#             
#         except subprocess.TimeoutExpired:
#             raise FlashError("Reset operation timed out")
#         except subprocess.SubprocessError as e:
#             raise FlashError(f"Reset operation failed: {str(e)}")
# 
#     def flash_device(self, hex_file: Union[str, Path], serial: str = None) -> bool:
#         """Flash a hex file to a device.
#         
#         Args:
#             hex_file: Path to the hex file to flash
#             serial: Device serial number. Defaults to SEGGER env var.
#             
#         Returns:
#             bool: True if flashing was successful
#             
#         Raises:
#             FlashError: If the flashing operation fails
#         """
#         serial = serial or self.segger
#         if not serial:
#             raise FlashError("No serial number provided and SEGGER env var not set")
#             
#         hex_path = Path(hex_file)
#         if not hex_path.exists():
#             raise FlashError(f"Hex file not found: {hex_file}")
#             
#         self.logger.info(f"Flashing device {serial} with {hex_file}")
#         
#         try:
#             # Detect family from hex file if possible
#             family = detect_family_from_zip(hex_file)
#             
#             cmd = [
#                 NRFUTIL_CMD,
#                 "device",
#                 "program",
#                 "--serial-number",
#                 serial,
#                 "--file",
#                 str(hex_path)
#             ]
#             
#             if family:
#                 cmd.extend(["--family", family])
#             
#             result = subprocess.run(
#                 cmd,
#                 capture_output=True,
#                 text=True,
#                 timeout=DEFAULT_TIMEOUT
#             )
#             
#             if result.returncode != 0:
#                 raise FlashError(f"Flashing failed: {result.stderr}")
#                 
#             return True
#             
#         except subprocess.TimeoutExpired:
#             raise FlashError("Flash operation timed out")
#         except subprocess.SubprocessError as e:
#             raise FlashError(f"Flash operation failed: {str(e)}")
# 
# def get_device_manager(logger: Optional[logging.Logger] = None) -> DeviceManager:
#     """Factory function to create a DeviceManager instance.
#     
#     Args:
#         logger: Optional logger instance
#         
#     Returns:
#         DeviceManager: Configured device manager instance
#     """
#     return DeviceManager(logger)
# 
# # For backwards compatibility
# def reset_device(serial: str = None, reset_kind: str = "RESET_SYSTEM") -> bool:
#     """Legacy function for resetting a device. Prefer using DeviceManager class."""
#     manager = get_device_manager()
#     return manager.reset_device(serial, reset_kind)##########################################################################################
# Copyright (c) 2024 Nordic Semiconductor
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
##########################################################################################

import subprocess
import os
import sys
import glob
sys.path.append(os.getcwd())
from utils.logger import get_logger
from utils.thingy91x_dfu import detect_family_from_zip

logger = get_logger()

SEGGER = os.getenv('SEGGER')

def reset_device(serial=SEGGER, reset_kind="RESET_SYSTEM"):
    logger.info(f"Resetting device, segger: {serial}")
    try:
        result = subprocess.run(
            ['nrfutil', 'device', 'reset', '--serial-number', serial, '--reset-kind', reset_kind],
            check=True,
            text=True,
            capture_output=True
        )
        logger.info("Command completed successfully.")
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.info("An error occurred while resetting the device.")
        logger.info("Error output:")
        logger.info(e.stderr)
        raise

def flash_device(hexfile, serial=SEGGER, extra_args=[]):
    # hexfile (str): Full path to file (hex or zip) to be programmed
    if not isinstance(hexfile, str):
        raise ValueError("hexfile cannot be None")
    logger.info(f"Flashing device, segger: {serial}, firmware: {hexfile}")
    try:
        result = subprocess.run(['nrfutil', 'device', 'program', *extra_args, '--firmware', hexfile, '--serial-number', serial], check=True, text=True, capture_output=True)
        logger.info("Command completed successfully.")
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.info("An error occurred while flashing the device.")
        logger.info("Error output:")
        logger.info(e.stderr)
        raise

    reset_device(serial)

def recover_device(serial=SEGGER, core="Application"):
    logger.info(f"Recovering device, segger: {serial}")
    try:
        result = subprocess.run(['nrfutil', 'device', 'recover', '--serial-number', serial, '--core', core], check=True, text=True, capture_output=True)
        logger.info("Command completed successfully.")
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.info("An error occurred while recovering the device.")
        logger.info("Error output:")
        logger.info(e.stderr)
        raise

def dfu_device(zipfile, serial=None, reset_only=False, check_53_version=False, bootloader_slot=1):
    chip, is_mcuboot = detect_family_from_zip(zipfile)
    if chip is None:
        logger.error("Could not determine chip family from image")
        raise ValueError("Invalid image file")
    command = [
        'python3',
        'utils/thingy91x_dfu.py',
        '--image', zipfile,
        '--chip', chip,
        '--bootloader-slot', str(bootloader_slot)
    ]

    if serial:
        command.append('--serial')
        command.append(serial)
    if reset_only:
        command.append('--reset-only')
    if check_53_version:
        command.append('--check-nrf53-version')

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        logger.info("Output from dfu script:")
        logger.info(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error("Error from dfu script:")
        logger.error(e.stderr)
        raise e

def setup_jlink(serial_number):
    """
    Flash Segger firmware to nRF53 on Thingy91x through external debugger.

    Args:
        serial_number (str): Serial number of the external debugger.

    Raises:
        subprocess.CalledProcessError: If the setup-jlink command fails.
    """
    logger.info("Flashing Segger firmware to nRF53 on Thingy91x through external debugger")

    setup_jlink_command = ['/opt/setup-jlink/setup-jlink.bash', serial_number]

    try:
        subprocess.run(
            setup_jlink_command,
            check=True,
            text=True,
            capture_output=True
        )
        logger.info("Segger firmware flashed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to flash Segger firmware.")
        logger.error(f"Command: {' '.join(setup_jlink_command)}")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Standard output:\n{e.stdout}")
        logger.error(f"Standard error:\n{e.stderr}")
        raise

def get_first_artifact_match(pattern):
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    else:
        return None
