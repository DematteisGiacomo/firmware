##########################################################################################
# Copyright (c) 2024 Nordic Semiconductor
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
##########################################################################################

import pytest
import time
import os
import json
import types
from tests.conftest import get_uarts
from ppk2_api.ppk2_api import PPK2_API
from utils.uart import Uart
from utils.flash_tools import flash_device, reset_device, recover_device
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger()

UART_TIMEOUT = 60 * 30
POWER_TIMEOUT = 60 * 5
MAX_CURRENT_PSM_UA = 10

SEGGER = os.getenv('SEGGER')
UART_ID = os.getenv('UART_ID', SEGGER)

def get_uarts():
    base_path = "/dev/serial/by-id"
    try:
        serial_paths = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
    except (FileNotFoundError, PermissionError) as e:
        logger.error(e)
        return False

    uarts = []

    for path in sorted(serial_paths):
        logger.warning(path)
        logger.warning(UART_ID)
        if UART_ID in path:
            uarts.append(path)
        else:
            continue
    return uarts

def save_badge_data(average):
    logger.info(f"Minimum average current measured: {average}uA")
    if average < 0:
        pytest.fail(f"current cant be negative, current average: {average}")
    if average <= 10:
        color = "green"
    elif average <= 50:
        color = "yellow"
    else:
        color = "red"

    badge_data = {
        "label": "psm_current uA",
        "message": f"{average}",
        "schemaVersion": 1,
        "color": f"{color}"
    }

    # Save the JSON data to a file
    with open('power_badge.json', 'w') as json_file:
        json.dump(badge_data, json_file)

    logger.info(f"Minimum average current saved to 'power_badge.json'")


@pytest.fixture(scope="module")
def ppk2():
    '''
    This fixture sets up ppk measurement tool.
    '''
    ppk2s_connected = PPK2_API.list_devices()
    ppk2s_connected.sort()
    if len(ppk2s_connected) == 2:
        ppk2_port = ppk2s_connected[0]
        print(f"Found PPK2 at {ppk2_port}")
    elif len(ppk2s_connected) == 0:
        pytest.fail("No ppk found")
    else:
        pytest.fail(f"Multiple PPks found")

    ppk2_test = PPK2_API(ppk2_port, timeout=1, write_timeout=1, exclusive=True)

    # get modifier might fail, retry 15 times
    for _ in range(15):
        try:
            ppk2_test.get_modifiers()
            break
        except Exception as e:
            logger.error(f"Failed to get modifiers: {e}")
            time.sleep(5)
    else:
        pytest.fail("Failed to get ppk modifiers after 10 attempts")


    ppk2_test.set_source_voltage(3300)

    ppk2_test.use_ampere_meter()  # set ampere meter mode

    ppk2_test.toggle_DUT_power("ON")  # enable DUT power


    time.sleep(10)

    for i in range(10):
        try:
            all_uarts = get_uarts()
            if not all_uarts:
                logger.error("No UARTs found")
            log_uart_string = all_uarts[0]
            break
        except Exception:
            ppk2_test.toggle_DUT_power("OFF")  # disable DUT power
            time.sleep(2)
            ppk2_test.toggle_DUT_power("ON")  # enable DUT power
            time.sleep(5)
            continue
    else:
        pytest.fail("NO uart after 10 attempts")

    uart = Uart(log_uart_string, timeout=UART_TIMEOUT)

    yield types.SimpleNamespace(ppk2_test=ppk2_test, uart=uart,)

    uart.stop()
    # recover_device()
    ppk2_test.stop_measuring()

# @pytest.mark.dut_ppk
def test_power(ppk2, hex_file):
    # flash_device(os.path.abspath(hex_file))
    reset_device()
    time.sleep(5)
    ppk2.uart.xfactoryreset()
    patterns_boot = [
            "Network connectivity established",
            "Connected to Cloud",
            "trigger: frequent_poll_entry: frequent_poll_entry",
            "trigger: trigger_work_fn: Sending data sample trigger",
            "environmental_module: sample: temp:",
            "transport: state_connected_ready_run: Payload",
            "Location search done"
    ]

    ppk2.ppk2_test.start_measuring()

    # Boot
    ppk2.uart.flush()
    reset_device()
    # ppk2.uart.wait_for_str(patterns_boot, timeout=120)

    # ppk2.uart.wait_for_str("Disabling UARTs", timeout=120)

    start = time.time()
    min_average = float('inf')
    average = None
    sampling_interval = 0.01
    averages = []
    average_of_averages = 0
    last_log_time = start
    while time.time() < start + POWER_TIMEOUT:
        try:
            read_data = ppk2.ppk2_test.get_data()
            if read_data != b'':
                samples, _ = ppk2.ppk2_test.get_samples(read_data)
                average = sum(samples)/len(samples)

                # Store the average for rolling calculation
                averages.append(average)
                # Keep only the averages from the last 3 seconds
                if len(averages) > int(3 / sampling_interval):
                    averages.pop(0)

                # Calculate the average of averages
                average_of_averages = sum(averages) / len(averages) if averages else 0

                # Log and store every 5 seconds
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    logger.info(f"Average current over last 3 secs: {average_of_averages} uA")
                    last_log_time = current_time

                if average_of_averages < min_average:
                    min_average = average_of_averages

        except Exception as e:
            logger.error(f"Catching exception: {e}")
            pytest.skip("Something went wrong, unable to perform power measurements")

        if average_of_averages < MAX_CURRENT_PSM_UA:
            # Log and store the last sample
            logger.info(f"Average current over last 3 secs: {average_of_averages} uA")
            logger.info("psm target reached for more than 3 secs")
            break
        time.sleep(sampling_interval)  # lower time between sampling -> less samples read in one sampling period
    else:
        save_badge_data(min_average)
        pytest.fail(f"PSM target not reached after {POWER_TIMEOUT} seconds, only reached {min_average} uA")
    save_badge_data(min_average)
