import asyncio
import re

from lib.ili9341 import Display, color565

# ==============================================================================

TXT_FILE = "tao_te_ching.txt"

# built-in font
CHARACTER_WIDTH = 8
CHARACTER_HEIGHT = 8

CHARACTER_DELAY = 0.1 # delay between each typed character (s)
SHORTER_DELAY   = 0.25 # commas, semicolons, colons (s)
LONGER_DELAY    = 0.5 # periods (s)

END_PAGE_DELAY  = 5 # delay before refreshing to next 'page' (s)
NEW_PAGE_DELAY  = 1 # delay after refreshing to next 'page' (s)
END_TEXT_DELAY  = 5 # delay after finishing printing text before restart (s)

X_OFFSET = 8
Y_OFFSET = 8
Y_DISTANCE = 12 # distance between each line

DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

MAX_LENGTH = (DISPLAY_WIDTH - X_OFFSET * 2) // CHARACTER_WIDTH # padding on either side (38)
MAX_LINES = (DISPLAY_HEIGHT - Y_OFFSET) // Y_DISTANCE # also padding at top and bottom (28)

RED     = color565(255, 0, 0)
WHITE   = color565(255, 255, 255)

# ==============================================================================

# highlight_regex = re.compile(r"\d+:\d+") # e.g. 7:12
highlight_regex = re.compile(r"Chapter \w+")

# ==============================================================================

async def next_page(display: Display, cursor: dict[str, int]):
    await asyncio.sleep(END_PAGE_DELAY)
    display.fill_hrect(X_OFFSET, Y_OFFSET, DISPLAY_WIDTH - 2 * X_OFFSET, DISPLAY_HEIGHT - 2 * Y_OFFSET, 0)
    cursor['x'] = 0
    cursor['y'] = 0
    await asyncio.sleep(NEW_PAGE_DELAY)
    # print("Text buffer -> {text_buffer}")

# breaks line into array of multiple lines that fit screen width
def break_line(text:str) -> list[str]:
    lines: list[str] = []
    words: list[str] = text.strip().split(' ')
    line: str = ''

    for word in words:
        if len(line) + len(word) >= MAX_LENGTH:
            lines.append(line)
            line = word
        else:
            if line != '':
                line += ' ' + word
            else:
                line = word

    if line != '':
        lines.append(line)

    return lines

async def run(display:Display):
    """Scrolling text"""
    try:
        while True:
            display.clear()
            cursor = {'x': 0, 'y': 0}

            with open(f"text/{TXT_FILE}") as txt_file:
                for passage in txt_file:

                    if passage.strip() == '':
                        continue

                    lines:list[str] = break_line(passage)
                    # print(str(lines) + '\n')

                    if cursor['y'] + len(lines) > MAX_LINES:
                        await next_page(display, cursor)

                    for line in lines:
                        for index, word in enumerate(line.split(' ')):

                            word_color = RED if re.match(highlight_regex, word) else WHITE

                            if index != 0:
                                word = ' ' + word

                            for char in word:
                                display.draw_text8x8(X_OFFSET + cursor['x'] * CHARACTER_WIDTH, Y_OFFSET + cursor['y'] * Y_DISTANCE, char, word_color)
                                cursor['x'] += 1

                                delay = CHARACTER_DELAY

                                if char == '.':
                                    delay = LONGER_DELAY
                                elif char in [',', ';', ':']:
                                    delay = SHORTER_DELAY

                                await asyncio.sleep(delay)

                        cursor['x'] = 0
                        cursor['y'] += 1

                    cursor['y'] += 1 # space between passages

            await asyncio.sleep(END_TEXT_DELAY)

    except asyncio.CancelledError:
        raise
