import asyncio
from machine import Pin
from network import WLAN

from lib.ili9341 import Display

async def run(display:Display, wlan:WLAN):
    """Nothing ever happens"""

    backlight_pin:Pin = Pin(8, Pin.OUT)

    try:
        display.clear()
        display.sleep(True)
        backlight_pin.off()
        wlan.config(pm=WLAN.PM_POWERSAVE)

        while True:
            await asyncio.sleep(100_000)

    except asyncio.CancelledError:
        display.sleep(False)
        backlight_pin.on()
        wlan.config(pm=WLAN.PM_NONE)
        raise
