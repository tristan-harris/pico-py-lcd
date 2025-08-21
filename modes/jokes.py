import asyncio
import network
import requests

from lib.ili9341 import Display, color565
from lib.xglcd_font import XglcdFont

FONT_WIDTH = 13
FONT_HEIGHT = 18

X_OFFSET = 5
Y_OFFSET = 5
Y_DISTANCE = 22 # distance between each row

CHARACTER_COLUMNS = (320 - X_OFFSET * 2) // FONT_WIDTH
LINE_ROWS = (240 - Y_OFFSET * 2) // Y_DISTANCE

RED     = color565(255, 0, 0)
WHITE   = color565(255, 255, 255)

# UPDATE_TIME = 10 * 60 # how long to wait between api calls (s)
UPDATE_TIME = 15 # how long to wait between api calls (s)
NOT_CON_TIME = 1 * 60 # how long to wait before making another api call (if not connected)

# https://sv443.net/jokeapi/v2/
JOKE_API_URL = "https://v2.jokeapi.dev/joke/Any"

def write_text(row:int, text:str, font:XglcdFont, display:Display) -> int: # returns rows used

    text = text.replace('\n', ' ') # strip newline characters
    words = text.split(' ')

    current_row = row
    line = '' # current line

    for word in words:
        if len(line) + len(word) + 1 >= CHARACTER_COLUMNS: # idk why the +1 is needed but it is
            display.draw_text(X_OFFSET, Y_OFFSET + current_row * Y_DISTANCE, line, font, WHITE)
            current_row += 1
            line = word
        else:
            if line != '':
                line += ' ' + word
            else:
                line = word

        if current_row >= LINE_ROWS:
            return current_row - row

    if line != '':
        display.draw_text(X_OFFSET, Y_OFFSET + current_row * Y_DISTANCE, line, font, WHITE)
        current_row += 1

    return current_row - row

async def run(display:Display, wlan:network.WLAN):
    try:
        display.clear()
        print("Loading 'monogram' font")
        monogram:XglcdFont = XglcdFont('fonts/Monogram13x18.c', 13, 18)

        connected = True

        while True:
            if wlan.status() != network.STAT_GOT_IP:
                if connected:
                    display.clear()
                    display.draw_text(X_OFFSET, Y_OFFSET, "WiFi not connected", monogram, RED)
                    connected = False
                await asyncio.sleep(NOT_CON_TIME)

            else:
                req = requests.get(JOKE_API_URL)
                if req.status_code == 200:
                    display.clear()
                    req_data = req.json()
                    if req_data["type"] == "single":
                        write_text(0, req_data["joke"], monogram, display)
                    else:
                        rows = write_text(0, req_data["setup"], monogram, display)
                        write_text(rows + 2, req_data["delivery"], monogram, display)
                else:
                    print(f"ERROR (HTTP Status code -> {req.status_code})")

                req.close() # required for micropython implementation of 'requests'

                connected = True
                await asyncio.sleep(UPDATE_TIME)

    except asyncio.CancelledError:
        raise
