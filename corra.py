import asyncio
import logging
import os
import shutil
import sys
import time

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

import config

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("meross_iot").setLevel(logging.CRITICAL)
logging.getLogger("meross_iot").disabled = True

# Константы
EMAIL = os.environ.get("MEROSS_EMAIL") or config.MERROSEMAIL
PASSWORD = os.environ.get("MEROSS_PASSWORD") or config.MERROSPASSWORD

LINE_CLEAR = "\x1b[2K"
CURSOR_UP = "\x1b[1A"

led_status = 2


CORRA_HELLO = r"""
 ░▒▓██████▓▒░░▒▓████████▓▒░▒▓███████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓██████▓▒░░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
Ready to roll ^_^
"""


def center_text(text):
    terminal_width = shutil.get_terminal_size().columns
    centered_lines = []
    for line in text.strip().split("\n"):
        padding = (terminal_width - len(line)) // 2
        centered_lines.append(" " * padding + line)
    return "\n".join(centered_lines)


def clear_last_line():
    sys.stdout.write("\r" + LINE_CLEAR)
    sys.stdout.flush()


def statusbar(status):
    print(status)
    time.sleep(3)
    sys.stdout.write(CURSOR_UP + LINE_CLEAR)
    sys.stdout.flush()
    time.sleep(0.3)
    sys.stdout.write(CURSOR_UP + LINE_CLEAR)


async def control_desk_lamp(command):
    global led_status
    http_api_client = await MerossHttpClient.async_from_user_password(
        api_base_url="https://iotx-eu.meross.com", email=EMAIL, password=PASSWORD
    )
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()
    await manager.async_device_discovery()
    lamps = manager.find_devices(device_type="msl120d")

    if not lamps:
        statusbar("[ERR] Desk lamp not found... uh-oh (╯°□°）╯")
        return

    lamp = lamps[0]
    await lamp.async_update()

    if "-color=" in command:
        color_hex = command.split("=")[1]
        if len(color_hex) == 6:
            rgb = tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))
            statusbar(f"[OK] Color set: {color_hex} ({rgb}). Lookin' good!")
            await lamp.async_set_light_color(rgb=rgb)
        else:
            statusbar(f"[ERR] Invalid color: {color_hex}. My circuits are confused.")

    elif "-on" in command:
        statusbar("[OK] Lamp ON! Let there be light!")
        await lamp.async_turn_on()
        led_status = 1

    elif "-off" in command:
        statusbar("[OK] Lamp OFF. Back to the void...")
        await lamp.async_turn_off()
        led_status = 0

    elif "-toggle" in command:
        if led_status == 0:
            statusbar("[OK] Lamp ON! Let there be light!")
            await lamp.async_turn_on()
            led_status = 1
        elif led_status == 1:
            statusbar("[OK] Lamp OFF. Back to the void...")
            await lamp.async_turn_off()
            led_status = 0
        else:
            statusbar("[ERR] I dunno if it's on or wha ?_?")

    await http_api_client.async_logout()
    manager.close()


async def main():
    print("\n" * 10)
    print(center_text(CORRA_HELLO))
    print("\n" * 10)
    while True:
        try:
            command = input(">>> ").strip()
            if not command:
                continue

            if command.startswith("dl"):
                await control_desk_lamp(command)
            elif command in ["exit", "quit"]:
                statusbar("[SYS] Shutting down... Beep boop, bye.")
                break
            else:
                statusbar("[???] Unknown command. Are you speaking robot? O_o")
        except KeyboardInterrupt:
            statusbar("[SYS] Shutting down... Beep boop, bye.")
            break


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
