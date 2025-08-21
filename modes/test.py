import asyncio

from lib.ili9341 import Display, color565
from lib.xglcd_font import XglcdFont

WHITE = color565(255, 255, 255)
TEXT = "Once more, forever."

async def run(display:Display):
    """Testing"""
    try:
        display.clear()

        print('Loading monogram (smaller)')
        monogram_small = XglcdFont('fonts/Monogram7x9.c', 7, 9)
        print('Loading monogram (bigger)')
        monogram_big = XglcdFont('fonts/Monogram13x18.c', 13, 18)

        display.draw_letter(10, 10, "B", monogram_big, WHITE)
        display.draw_letter(30, 30, "B", monogram_big, WHITE)
        display.draw_letter_manual(50, 50, "B", monogram_big, WHITE)

    except asyncio.CancelledError:
        raise
