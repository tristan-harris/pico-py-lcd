import network
import asyncio

from lib.ili9341 import Display, color565
from lib.xglcd_font import XglcdFont

WHITE = color565(255, 255, 255)

ITERATION_TIME = 0.05 # time between each scroll increment (s)

async def run(display:Display, wlan:network.WLAN):
    try:
        print("Loading 'monogram' font")
        monogram:XglcdFont = XglcdFont('fonts/Monogram13x18.c', 13, 18)

        scroll_amount = display.width

        display.clear()
        display.draw_text(10, 10, "FLORIDA MAN", monogram, WHITE)

        while True:
            scroll_amount -= 1
            if scroll_amount == 0:
                scroll_amount = display.width

            display.scroll(scroll_amount)
            await asyncio.sleep(ITERATION_TIME)

    except asyncio.CancelledError:
        display.scroll(0)
        raise
