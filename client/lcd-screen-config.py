#!/usr/bin/env python3

import os
import requests
import json
import time

import pyudev
import serial

# ==============================================================================

RED = "\x1b[31m"  # red
GRE = "\x1b[32m"  # green
YEL = "\x1b[33m"  # yellow
BLU = "\x1b[34m"  # blue
MAG = "\x1b[35m"  # magenta
CYA = "\x1b[36m"  # cyan

BOL = "\x1b[1m"  # bold
RES = "\x1b[0m"  # reset
CLS = "\x1b[H\x1b[J"  # clear screen

CONFIG_DIRECTORY = f"{os.getenv('HOME')}/.config/lcd-box-config"
CONFIG_FILE = "config"
DEFAULT_TRANSFER = "USB"

BAUD_RATE = 115200
SERIAL_WAIT_TIME = 1  # how long to wait between connecting and sending data (s)

PICO_IP_ADDRESS = "http://10.42.0.167"
TIMEOUT_LEN = 5  # seconds

HEADING = r"""
██╗      ██████╗██████╗      ██████╗███████╗ ██████╗
██║     ██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔════╝
██║     ██║     ██║  ██║    ██║     █████╗  ██║  ███╗
██║     ██║     ██║  ██║    ██║     ██╔══╝  ██║   ██║
███████╗╚██████╗██████╔╝    ╚██████╗██║     ╚██████╔╝
╚══════╝ ╚═════╝╚═════╝      ╚═════╝╚═╝      ╚═════╝"""

# id, list name, list description
MODES = [
    ("dvd_bounce", "󰗮 Bounce", "A bouncing DVD logo. Will it hit the corner?"),
    ("currency_tracker", "󰁰 Currency Tracker", "Get the latest stock and commodities prices."),
    ("idle", "󰒲 Idle", "Uses minimum power."),
    ("jokes", "󰍬 Jokes", "Only the best jokes from jokeapi.dev"),
    ("scrolling_background", "󰜱 Scrolling Background", "A bird flying over mountains."),
    ("text_scroll", "󰦨 Scrolling Text", "May require squinting."),
    ("status", "󰖩 Status", "Shows current device status."),
    ("test", "󰣪 Test", "Testing 1, 2, 3..."),
    ("wallpaper_rotation", "󰋩 Wallpaper", "A nice image to look at."),
]

# ==============================================================================

# necessary because ttyACM(X) can refer to other devices
def get_tty_device_path() -> str:
    context = pyudev.Context()
    for i in range(10):
        tty_device_path = f"/dev/ttyACM{i}"
        if os.path.exists(tty_device_path):
            device = pyudev.Devices.from_device_file(context, tty_device_path)
            if device.get("ID_VENDOR") == "MicroPython":
                return f"/dev/ttyACM{i}"

    raise Exception("MicroPython tty device not found")

def get_transfer_preference() -> str:
    try:
        with open(f"{CONFIG_DIRECTORY}/{CONFIG_FILE}") as config_file:
            return json.load(config_file)["transfer_type"]
    except OSError:
        return "USB"


def save_transfer_preference(transfer_preference: str):
    try:
        if not os.path.exists(CONFIG_DIRECTORY):
            os.mkdir(CONFIG_DIRECTORY)
        with open(f"{CONFIG_DIRECTORY}/{CONFIG_FILE}", "w") as config_file:
            json.dump({"transfer_type": transfer_preference}, config_file)
    except OSError:
        print(f"\n{RED}Error:{RES} Could not write transfer preference to file")


def print_help():
    print("\nHELP:")
    print(f"{MAG}t{RES} -> Toggle transfer type (USB or WiFi)")
    print(f"{MAG}c{RES} -> Clear screen")
    print(f"{MAG}h{RES} -> Print this help")
    print(f"{MAG}q{RES} -> Quit")

def print_choices(transfer_preference: str):
    print(f"\nChoose a mode (via {BOL}{transfer_preference}{RES}):")

    max_length = max(len(mode[1]) for mode in MODES)

    for i, mode_data in enumerate(MODES):
        print(f"{MAG}{BOL}{i + 1}{RES} {BOL}{mode_data[1].ljust(max_length)}{RES} - {mode_data[2]}")
    print(f"\nEnter a number ({MAG}1{RES} - {MAG}{len(MODES)}{RES}) or letter ({MAG}t{RES}/{MAG}c{RES}/{MAG}h{RES}/{MAG}q{RES})")

def get_input() -> str:
    try:
        user_input: str = input()
    except EOFError:
        print(CLS, end="")
        quit()

    return user_input

def choose_mode(transfer_preference: str) -> int:
    while True:
        print_choices(transfer_preference)
        print(f"Input: ", end="")
        user_input: str = get_input()

        if user_input.isnumeric():
            user_selection: int = int(user_input)
            if 1 <= user_selection <= len(MODES):
                return user_selection - 1

        match(user_input):
            case "t":
                transfer_preference = "USB" if transfer_preference == "WiFi" else "WiFi"
                save_transfer_preference(transfer_preference)
            case "c":
                print(CLS, end="")
            case "q":
                print(CLS, end="")
                exit()
            case "h":
                print_help()
            case _:
                print("Invalid input")


def transfer_data_USB(mode: str, tty_device: str):
    try:
        pico = serial.Serial(tty_device, BAUD_RATE, timeout=1)
        time.sleep(SERIAL_WAIT_TIME)  # wait for connection to stabilize

        # newline is requred otherwise pico stalls
        pico.write(bytes(mode + "\n", "ascii"))

        pico.close()

    except Exception as exception:
        print(f"\n{RED}Error{RES}: USB communication failed -> {exception}")

def transfer_data_wifi(mode: str):
    try:
        req: requests.Response = requests.get(
            url=f"{PICO_IP_ADDRESS}/mode/{mode}",
            timeout=TIMEOUT_LEN,
        )
        print(req.json())

    except (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
    ):
        print(f"\n{RED}Error{RES}: Request timed out")

    except Exception as exception:
        print(f"\n{RED}Error{RES}: Request failed -> {exception}")

def main():
    tty_device: str = get_tty_device_path()

    print(f"{CYA}{HEADING}{RES}")

    while True:
        transfer_preference: str = get_transfer_preference()
        mode_index: int = choose_mode(transfer_preference)  # zero-indexed

        match transfer_preference:
            case "USB":
                transfer_data_USB(MODES[mode_index][0], tty_device)
            case "WiFi":
                transfer_data_wifi(MODES[mode_index][0])
            case _:
                print(f"\n{RED}Error{RES}: Transfer type '{transfer_preference}' is invalid.")


if __name__ == "__main__":
    main()
