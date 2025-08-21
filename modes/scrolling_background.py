import asyncio

from lib.ili9341 import Display, color565

BACKGROUND_IMAGE = "scrollable-background"
BACKGROUND_SKY_COLOR = color565(70, 52, 94)

BIRD_IMAGE      = const("bird")
BIRD_WIDTH      = const(40)
BIRD_HEIGHT     = const(40)
BIRD_COUNT      = const(8)
BIRD_Y_OFFSET   = const(52)
BIRD_X_POSITION = const(141) # centre of screen with sprite taken into account

UPDATE_TIME = 0.05 # how long between each screen update (s)
SCROLL_INCREMENT = 1 # how much the screen is scrolled by (px)

SPRITE_UPDATE_TIME = 4

# left means how many pixels from the left, returns the rest from the right
def get_y_splits(bird_data:bytes, left:int) -> list[bytearray]:
    left_bird_slices = [bird_data[i:i + left * 2] for i in range(0, len(bird_data), BIRD_WIDTH * 2)]
    right_bird_slices = [bird_data[i + left * 2:i + BIRD_WIDTH * 2] for i in range(0, len(bird_data), BIRD_WIDTH * 2)]

    slices = [left_bird_slices, right_bird_slices]

    result = []

    for slice in slices:
        flattened = bytearray()
        for s in slice:
            flattened.extend(s)
        result.append(flattened)

    return result

async def run(display:Display):
    try:
        display.draw_image(f"images/{BACKGROUND_IMAGE}.raw")

        scroll_amount = display.width

        print('Loading bird image sprites')
        bird_sprites:list[bytes] = []
        for i in range(BIRD_COUNT):
            bird_sprites.append(display.load_sprite(f"images/{BIRD_IMAGE}-{i}.raw", BIRD_WIDTH, BIRD_HEIGHT))

        bird_index = 0
        timer = 0
        bird_y_modifier = 0

        while True:

            timer += 1
            if timer >= SPRITE_UPDATE_TIME:
                bird_index += 1
                bird_index %= BIRD_COUNT
                timer = 0

            # make bird sprite bob up and down
            if bird_index in [3, 4]:
                bird_y_modifier = -1
            elif bird_index in [0, 7]:
                bird_y_modifier = 1
            else:
                bird_y_modifier = 0

            scroll_amount -= SCROLL_INCREMENT
            if scroll_amount <= 0:
                scroll_amount = display.width + scroll_amount

            draw_x_position = (BIRD_X_POSITION + display.width - scroll_amount) % display.width
            if draw_x_position + BIRD_WIDTH >= display.width: # sprite is being drawn over the right edge, must split
                overshoot = draw_x_position + BIRD_WIDTH - display.width # how much draw over the right edge (px)
                left_bytes, right_bytes = get_y_splits(bird_sprites[bird_index], BIRD_WIDTH - overshoot)
                display.draw_sprite(left_bytes, draw_x_position, BIRD_Y_OFFSET + bird_y_modifier, BIRD_WIDTH - overshoot, BIRD_HEIGHT)
                display.draw_sprite(right_bytes, 0, BIRD_Y_OFFSET + bird_y_modifier, overshoot, BIRD_HEIGHT)
            else:
                display.draw_sprite(bird_sprites[bird_index], draw_x_position, BIRD_Y_OFFSET + bird_y_modifier, BIRD_WIDTH, BIRD_HEIGHT)

            display.scroll(scroll_amount)

            await asyncio.sleep(UPDATE_TIME)

    except asyncio.CancelledError:
        display.scroll(0)
        raise
