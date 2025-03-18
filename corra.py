import asyncio
import os
import threading

import light_control
import shell
import telegram_bot


def send_status(status, tg_session=False, color1=None, color2=None):
    match status:
        case "lamp_on":
            text = "[OK] Lamp ON! Let there be light!"
        case "lamp_off":
            text = "[OK] Lamp OFF. Back to the void..."
        case "un_command":
            text = "[???] Unknown command. Are you speaking robot? O_o"
        case "no_conn":
            text = "Huh? It seems we don't have internet, please check connection."
        case "no_found":
            text = "[ERR] Desk lamp not found... uh-oh (╯°□°）╯"
        case "no_color":
            text = f"[ERR] Invalid color: {color1}. My circuits are confused."
        case "color_set":
            text = f"[OK] Color set: {color1} ({color2}). Lookin' good!"
        case "no_tint":
            text = f"[ERR] Invalid tint: {color1}. My circuits are confused."
        case "color_changed":
            text = f"[OK] Now current color is: {color1} ({color2}). XOXO"
        case "un_status":
            text = "[ERR] I don't know if it's on or not."
        case "lamp_toggle":
            if light_control.is_led_on is True:
                text = "[OK] Lamp OFF. Back to the void..."
            else:
                text = "[OK] Lamp ON! Let there be light!"

    if tg_session is True:
        telegram_bot.send_tg_status(text)
        shell.statusbar(text)
    if tg_session is False:
        shell.statusbar(text)


async def main():
    print("\n" * 10)
    print(shell.center_text(shell.CORRA_HELLO))
    print("\n" * 10)

    while True:
        try:
            command = input(">> ").strip()
            if not command:
                continue
            match command:
                case cmd if cmd.startswith("dl"):
                    await light_control.control_desk_lamp(command[len("dl") :].strip())
                case "exit" | "quit":
                    telegram_bot.send_tg_status("[SYS] Shutting down...")
                    shell.statusbar("[SYS] Shutting down... Beep boop, bye.")
                    break
        except KeyboardInterrupt:
            telegram_bot.send_tg_status("[SYS] Shutting down...")
            shell.statusbar("[SYS] Shutting down... Beep boop, bye.")
            break


def start_telegram_bot():
    telegram_bot.start_bot()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()

    asyncio.run(main())
