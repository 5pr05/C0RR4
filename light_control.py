import logging
import os

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

import config
import corra
import internet_control

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("meross_iot").setLevel(logging.CRITICAL)
logging.getLogger("meross_iot").disabled = True

EMAIL = os.environ.get("MEROSS_EMAIL") or config.MERROSEMAIL
PASSWORD = os.environ.get("MEROSS_PASSWORD") or config.MERROSPASSWORD

is_led_on = None
led_current_color = "#000000"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def add_colors(color1: str, color2: str) -> str:
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    new_rgb = tuple(min(c1 + c2, 255) for c1, c2 in zip(rgb1, rgb2))
    return rgb_to_hex(new_rgb)


def subtract_colors(color1: str, color2: str) -> str:
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    new_rgb = tuple(max(c1 - c2, 0) for c1, c2 in zip(rgb1, rgb2))
    return rgb_to_hex(new_rgb)


async def control_desk_lamp(command):
    global is_led_on, led_current_color
    if internet_control.internet is None:
        internet_control.is_connected(internet_control.REMOTE_SERVER)
    if not internet_control.internet:
        corra.send_status("no_conn")
        return

    http_api_client = await MerossHttpClient.async_from_user_password(
        api_base_url="https://iotx-eu.meross.com",
        email=EMAIL,
        password=PASSWORD,
    )
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()
    await manager.async_device_discovery()
    lamps = manager.find_devices(device_type="msl120d")
    if not lamps:
        corra.send_status("no_found")
        await http_api_client.async_logout()
        manager.close()
        return

    lamp = lamps[0]
    await lamp.async_update()

    try:
        match command:
            case cmd if cmd.startswith("-color="):
                color_hex = cmd.split("=")[1]
                if len(color_hex) == 6:
                    color_hex = f"#{color_hex}"
                    rgb = hex_to_rgb(color_hex)
                    await lamp.async_set_light_color(rgb=rgb)
                    await lamp.async_update()
                    if lamp.light_color == rgb:
                        led_current_color = color_hex
                        corra.send_status("color_set", color_hex, rgb)
                else:
                    corra.send_status("no_color")
            case cmd if cmd.startswith("-more="):
                tint = cmd.split("=")[1]
                if len(tint) == 6:
                    tint = f"#{tint}"
                    new_color = add_colors(led_current_color, tint)
                    new_rgb = hex_to_rgb(new_color)
                    await lamp.async_set_light_color(rgb=new_rgb)
                    await lamp.async_update()
                    if lamp.light_color == new_rgb:
                        led_current_color = new_color
                        corra.send_status("color_set", new_color, new_rgb)
                else:
                    corra.send_status("no_tint", tint)
            case cmd if cmd.startswith("-less="):
                tint = cmd.split("=")[1]
                if len(tint) == 6:
                    tint = f"#{tint}"
                    new_color = subtract_colors(led_current_color, tint)
                    new_rgb = hex_to_rgb(new_color)
                    await lamp.async_set_light_color(rgb=new_rgb)
                    await lamp.async_update()
                    if lamp.light_color == new_rgb:
                        led_current_color = new_color
                        corra.send_status("color_changed", new_color, new_rgb)
                else:
                    corra.send_status("no_tint", tint)
            case "-on":
                await lamp.async_turn_on()
                await lamp.async_update()
                if lamp.is_on:
                    is_led_on = True
                    corra.send_status("lamp_on")
            case "-off":
                await lamp.async_turn_off()
                await lamp.async_update()
                if not lamp.is_on:
                    is_led_on = False
                    corra.send_status("lamp_off")
            case "-toggle":
                if is_led_on is True:
                    await lamp.async_turn_off()
                    is_led_on = False
                    corra.send_status("lamp_off")
                else:
                    await lamp.async_turn_on()
                    is_led_on = True
                    corra.send_status("lamp_on")
            case _:
                corra.send_status("un_command")
    finally:
        await http_api_client.async_logout()
        manager.close()
