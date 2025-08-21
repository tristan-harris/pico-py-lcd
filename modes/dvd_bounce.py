from utime import sleep_us, ticks_us, ticks_diff
import asyncio
import random

from lib.ili9341 import Display

# adapted from https://github.com/rdagger/micropython-ili9341/blob/master/demo_sprite.py

SPRITE_PATH = "images/DVD_logo.raw"
SPRITE_WIDTH = 86
SPRITE_HEIGHT = 38
SPRITE_SPEED = 1 # how fast the sprite bounces around

class BouncingSprite(object):
    """Bouncing Sprite."""

    def __init__(self, path:str, image_w:int, image_h:int, speed:int, display:Display):
        """Initialize sprite.

        Args:
            path (string): Path of sprite image.
            image_w (int): Width of image.
            image_h (int): Height of image.
            size (int): Square side length.
            speed(int): Initial XY-Speed of sprite.
            display (SSD1351): OLED display object.
        """
        self.buf = display.load_sprite(path, image_w, image_h)
        self.image_w = image_w
        self.image_h = image_h
        self.display = display
        self.x_speed = random.choice([-speed, speed])
        self.y_speed = random.choice([-speed, speed])
        self.x = self.display.width // 2 - self.image_w // 2
        self.y = self.display.height // 2 - self.image_h // 2
        self.prev_x = self.x
        self.prev_y = self.y

    def update_pos(self):
        """Update sprite speed and position."""
        x = self.x
        y = self.y
        w = self.image_w
        h = self.image_h
        x_speed = abs(self.x_speed)
        y_speed = abs(self.y_speed)

        if x + w + x_speed >= self.display.width:
            self.x_speed = -x_speed
        elif x - x_speed < 0:
            self.x_speed = x_speed

        if y + h + y_speed >= self.display.height:
            self.y_speed = -y_speed
        elif y - y_speed <= 0:
            self.y_speed = y_speed

        self.prev_x = x
        self.prev_y = y

        self.x = x + self.x_speed
        self.y = y + self.y_speed

    def draw(self):
        """Draw sprite."""
        x = self.x
        y = self.y
        prev_x = self.prev_x
        prev_y = self.prev_y
        w = self.image_w
        h = self.image_h
        x_speed = abs(self.x_speed)
        y_speed = abs(self.y_speed)

        # determine direction and remove previous portion of sprite
        if prev_x > x:
            # left
            self.display.fill_vrect(x + w, prev_y, x_speed, h, 0)
        elif prev_x < x:
            # right
            self.display.fill_vrect(x - x_speed, prev_y, x_speed, h, 0)
        if prev_y > y:
            # upward
            self.display.fill_vrect(prev_x, y + h, w, y_speed, 0)
        elif prev_y < y:
            # downward
            self.display.fill_vrect(prev_x, y - y_speed, w, y_speed, 0)

        self.display.draw_sprite(self.buf, x, y, w, h)

async def run(display:Display):
    try:
        display.clear()
        logo = BouncingSprite(SPRITE_PATH, SPRITE_WIDTH, SPRITE_HEIGHT, SPRITE_SPEED, display)
        while True:
            timer = ticks_us()
            logo.update_pos()
            logo.draw()
            # attempt to set framerate to 30 FPS
            timer_dif = 33333 - ticks_diff(ticks_us(), timer)
            if timer_dif > 0:
                # sleep_us(timer_dif)
                await asyncio.sleep(timer_dif / 1000_000)
    except asyncio.CancelledError:
        raise
