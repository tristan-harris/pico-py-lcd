import asyncio
import time
import os

from machine import ADC
import network

from lib.ili9341 import Display, color565
from lib.xglcd_font import XglcdFont

FONT_WIDTH = 13
FONT_HEIGHT = 18

X_OFFSET = 15
Y_OFFSET = 15
Y_DISTANCE = 40 # distance between each row

TIME_TEXT_POS = (X_OFFSET + FONT_WIDTH * 6, Y_OFFSET + Y_DISTANCE * 0)
TEMP_TEXT_POS = (X_OFFSET + FONT_WIDTH * 14, Y_OFFSET + Y_DISTANCE * 1)
CONN_TEXT_POS = (X_OFFSET + FONT_WIDTH * 6, Y_OFFSET + Y_DISTANCE * 4)

BLACK   = color565(0, 0, 0)
GREEN   = color565(0, 255, 0)
RED     = color565(255, 0, 0)
WHITE   = color565(255, 255, 255)
YELLOW  = color565(255, 255, 0)

UPDATE_TIME = 5 # how long to wait between screen updates (s)

sensor_temp = ADC(4)
conversion_factor = 3.3 / (65535)

def get_time() -> str:
    # (year, month, mday, hour, minute, second, weekday, yearday)
    local_time = time.localtime(time.time())

    hour = local_time[3]

    meridiem = "am"
    if hour >= 12:
        meridiem = "pm"
    if hour >= 13:
        hour -= 12
    elif hour == 0: # hour after midnight
        hour += 12

    minute = str(local_time[4])
    if len(minute) == 1:
        minute = f"0{minute}" # zero-pad minute

    return str(hour) + ":" + minute + meridiem

def get_temperature() -> int:
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721 # celcius
    return round(temperature) # apparently the built-in sensor isn't that accurate anyway

def get_system_details() -> str:
    details = os.uname()
    return details[0] + ', ' + details[2]

def get_storage_status() -> float:
    stats = os.statvfs('/')
    return ((stats[2] - stats[3]) / stats[2]) * 100

def get_conn_status_text(status:int) -> tuple[str, int]:
    if status in [network.STAT_IDLE, network.STAT_WRONG_PASSWORD, network.STAT_NO_AP_FOUND, network.STAT_CONNECT_FAIL]:
        return ('No', RED)
    elif status == network.STAT_CONNECTING:
        return ('Connecting...', YELLOW)
    else:
        return ('Yes', GREEN)

async def run(display:Display, wlan:network.WLAN):
    """Status display"""
    try:
        display.clear()
        print("Loading 'monogram' font")
        monogram:XglcdFont = XglcdFont('fonts/Monogram13x18.c', 13, 18)

        display.draw_text(X_OFFSET, Y_OFFSET + Y_DISTANCE * 0, f"Time: ", monogram, WHITE)
        display.draw_text(X_OFFSET, Y_OFFSET + Y_DISTANCE * 1, f"Temperature: ", monogram, WHITE)
        display.draw_text(X_OFFSET, Y_OFFSET + Y_DISTANCE * 2, f"System: {get_system_details()}", monogram, WHITE)
        display.draw_text(X_OFFSET, Y_OFFSET + Y_DISTANCE * 3, f"Storage Used: {round(get_storage_status())}%", monogram, WHITE)
        display.draw_text(X_OFFSET, Y_OFFSET + Y_DISTANCE * 4, f"WiFi: ", monogram, WHITE)

        previous_time = ""
        previous_temperature = 0
        previous_connection_status = -1

        while True:

            current_time = get_time()
            current_temperature = get_temperature()
            current_connection_status = wlan.status()

            if previous_time != current_time:
                previous_time = current_time
                display.fill_hrect(TIME_TEXT_POS[0], TIME_TEXT_POS[1], FONT_WIDTH * 8, FONT_HEIGHT, BLACK)
                display.draw_text(TIME_TEXT_POS[0], TIME_TEXT_POS[1], get_time(), monogram, WHITE)

            if previous_temperature != current_temperature:
                previous_temperature = current_temperature
                display.fill_hrect(TEMP_TEXT_POS[0], TEMP_TEXT_POS[1], FONT_WIDTH * 8, FONT_HEIGHT, BLACK)
                display.draw_text(TEMP_TEXT_POS[0], TEMP_TEXT_POS[1], f"{get_temperature()}C", monogram, WHITE)

            if previous_connection_status != current_connection_status:
                previous_connection_status = current_connection_status
                status_text = get_conn_status_text(current_connection_status)
                display.fill_hrect(CONN_TEXT_POS[0], CONN_TEXT_POS[1], FONT_WIDTH * 15, FONT_HEIGHT, BLACK)
                display.draw_text(CONN_TEXT_POS[0], CONN_TEXT_POS[1], status_text[0], monogram, status_text[1])

            await asyncio.sleep(UPDATE_TIME)

    except asyncio.CancelledError:
        raise
