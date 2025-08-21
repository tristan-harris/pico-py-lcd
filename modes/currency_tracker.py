import asyncio
import network
import requests

from lib.ili9341 import Display, color565
from lib.xglcd_font import XglcdFont

FONT_WIDTH = 13
FONT_HEIGHT = 18

X_OFFSET = 13
Y_OFFSET = 18
Y_DISTANCE = 40 # distance between each row

BLACK   = color565(0, 0, 0)
RED     = color565(255, 0, 0)
WHITE   = color565(255, 255, 255)

UPDATE_TIME = 5 * 60 # how long to wait between screen updates (s)

COINCAP_API_URL = "https://api.coincap.io/v2/rates"

INFO_TEXT = "Prices listed in USD"
OFFLINE_TEXT = "(Offline)"

# by coincap ids
# needed because order varies with dictionary
ASSET_KEYS = ["australian-dollar", "bitcoin", "litecoin", "gold-ounce", "monero"]

ASSETS = {
    ASSET_KEYS[0]: ("AUD", color565(0, 106, 49)),
    ASSET_KEYS[1]: ("BTC", color565(247, 147, 26)),
    ASSET_KEYS[2]: ("LTC", color565(248, 252, 254)),
    ASSET_KEYS[3]: ("XAU", color565(255, 255, 0)),
    ASSET_KEYS[4]: ("XMR", color565(242, 104, 34))
}

async def run(display:Display, wlan:network.WLAN):
    try:
        print("Loading larger 'monogram' font")
        monogram:XglcdFont = XglcdFont('fonts/Monogram13x18.c', 13, 18)
        print("Loading smaller 'monogram' font")
        monogram_small:XglcdFont = XglcdFont('fonts/Monogram7x9.c', 7, 9)

        display.clear()

        connected = True

        for row, asset in enumerate(ASSET_KEYS):
            display.draw_text(X_OFFSET, Y_OFFSET + row * Y_DISTANCE, ASSETS[asset][0], monogram, ASSETS[asset][1])
        display.draw_text(X_OFFSET, Y_OFFSET + len(ASSETS) * Y_DISTANCE, INFO_TEXT, monogram_small, WHITE)

        while True:

            if wlan.status() != network.STAT_GOT_IP:
                if connected:
                    connected = False
                    display.draw_text(X_OFFSET + (len(INFO_TEXT) + 4) * 7, Y_OFFSET + len(ASSETS) * Y_DISTANCE, OFFLINE_TEXT, monogram_small, RED)
            else:
                if not connected:
                    connected = True
                    display.fill_hrect(X_OFFSET + (len(INFO_TEXT) + 4) * 7, Y_OFFSET + len(ASSETS) * Y_DISTANCE, 7 * len(OFFLINE_TEXT), 9, BLACK) # clear offline status text

                display.fill_hrect(X_OFFSET + 4 * FONT_WIDTH, Y_OFFSET, 12 * FONT_WIDTH, Y_OFFSET + (len(ASSETS) - 1) * Y_DISTANCE, BLACK) # clear prices

                for row, asset in enumerate(ASSET_KEYS):
                    print(f"Requesting {COINCAP_API_URL}/{asset}")
                    req = requests.get(f"{COINCAP_API_URL}/{asset}")
                    if req.status_code == 200:
                        req_data = req.json()
                        display.draw_text(X_OFFSET + 4 * FONT_WIDTH, Y_OFFSET + row * Y_DISTANCE, f"${round(float(req_data["data"]["rateUsd"]), 2)}", monogram, WHITE)
                    else:
                        print(f"ERROR (HTTP Status code -> {req.status_code})")

                    req.close()


            await asyncio.sleep(UPDATE_TIME)

    except asyncio.CancelledError:
        raise
