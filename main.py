import asyncio
import select
import sys
import json

from machine import Pin, SPI
import network

from lib.ili9341 import Display

from modes import currency_tracker, dvd_bounce, idle, jokes, news_ticker, scrolling_background, status, test, text_scroll, wallpaper_rotation

# ==============================================================================

WIFI_SSID = 'Swift-Hotspot'
WIFI_PASSWORD = '8sAr4LhnNi!3i@b02tT#&rdL#MayXq2R'

MODES = {
    "currency_tracker": currency_tracker,
    "dvd_bounce": dvd_bounce,
    "idle": idle,
    "jokes": jokes,
    "news_ticker": news_ticker,
    "scrolling_background": scrolling_background,
    "status": status,
    "test": test,
    "text_scroll": text_scroll,
    "wallpaper_rotation": wallpaper_rotation
}

# ==============================================================================

poller:select.poll = select.poll()
poller.register(sys.stdin, select.POLLIN) # use sys.stdin for USB serial input

wlan:network.WLAN   = network.WLAN(network.STA_IF)

reset_pin:Pin       = Pin(9, Pin.OUT, value=1)
spi:SPI             = SPI(0, baudrate=40_000_000, sck=Pin(18), mosi=Pin(19))
display:Display     = Display(spi, dc=Pin(6), cs=Pin(5), rst=Pin(7), width=320, height=240, rotation=90)

tasks = dict()

wlan.config(pm=network.WLAN.PM_NONE)

# ==============================================================================

async def switch_mode(mode:str) -> bool:
    if mode in MODES:
        # end task for current mode
        for task_name, task in tasks.items():
            if not task_name in ["connect_wifi", "usb_input", "http_input"]:
                if not task.done():
                    tasks[task_name].cancel()
                    try:
                        await tasks[task_name]
                    except asyncio.CancelledError:
                        pass
                del tasks[task_name]
                print(f"Ended task {task_name}")

        # start task for new mode
        if mode in ["dvd_bounce", "scrolling_background", "test", "text_scroll", "wallpaper_rotation"]:
            tasks[mode] = asyncio.create_task(MODES[mode].run(display))
            print(f"Created task {mode}")
            return True
        elif mode in ["currency_tracker", "idle", "jokes", "news_ticker", "status"]:
            tasks[mode] = asyncio.create_task(MODES[mode].run(display, wlan))
            print(f"Created task {mode}")
            return True

    return False

async def connect_to_wifi():
    """Periodically check WiFi connection and attempt to connect"""
    wlan.active(True)

    connected = False

    while True:
        if wlan.status() != network.STAT_GOT_IP:
            connected = False
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        else:
            if not connected:
                print(f"Connected, address is {wlan.ifconfig()[0]}")
                connected = True

        await asyncio.sleep(5)

async def read_usb_serial():
    """Asynchronously read from USB serial (sys.stdin) and echo back received data"""
    print("Starting USB serial listener...")
    while True:
        # check if there's data available to read
        if poller.poll(0):  # non-blocking check
            data = sys.stdin.readline().strip()  # read a line from USB serial
            if data:
                print(f"Received: {data}")
                # sys.stdout.write(f"Echo: {data}\n")  # echo back over USB
                await switch_mode(data)

        await asyncio.sleep(0.1)  # small delay to yield control

# this implementation is basic in that it accepts input via the route requested in an HTTP GET request
# a better implementation would parse the StreamReader lines and accept JSON in a POST request
# this however still works
async def read_http_input(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    # print("Client connected")

    request_line = await reader.readline()

    # skip http headers
    while await reader.readline() != b'\r\n': # b'\r\n' is the last line
        pass

    result = 'failure'

    request = request_line.decode()
    route = request.split(' ')[1]
    path = route.split('/')
    if len(path) == 3: # if something like /mode/status
        if path[1] == 'mode':
            mode_result = await switch_mode(path[2])
            if mode_result:
                result = 'success'

    writer.write(b'HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
    writer.write(json.dumps({'result': result}).encode())

    await writer.drain()
    await writer.wait_closed()
    # print("Client disconnected")

async def main():
    """Main coroutine to run all tasks"""
    tasks["connect_wifi"]   = asyncio.create_task(connect_to_wifi())
    tasks["usb_input"]      = asyncio.create_task(read_usb_serial())
    tasks["http_input"]     = asyncio.create_task(asyncio.start_server(read_http_input, '0.0.0.0', 80))
    tasks["idle"]           = asyncio.create_task(idle.run(display, wlan)) # start in idle mode

    await asyncio.gather(tasks["connect_wifi"], tasks["usb_input"], tasks["http_input"]) # wait for all task to complete (which never will in this case)

# run the asyncio event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    for task_name, task in tasks.items(): # clean up all tasks
        if not task.done():
            task.cancel()
    poller.unregister(sys.stdin)  # clean up poller
    print("Program terminated")
