import asyncio
from random import randint

from lib.ili9341 import Display

IMAGES = ["mountain_air"]

async def run(display:Display):
    """Updates wallpaper with randomly chosen image"""
    try:

        display.draw_image(f"images/{IMAGES[0]}.raw")

        # current_image_index:int = -1
        #
        # while True:
        #     print("Wallpaper updated")
        #     new_index:int = current_image_index
        #     while new_index == current_image_index:
        #         new_index = randint(0, len(IMAGES) -1)
        #     current_image_index = new_index
        #     display.draw_image(f"images/{IMAGES[current_image_index]}.raw")
        #
        #     await asyncio.sleep(5)

    except asyncio.CancelledError:
        raise
