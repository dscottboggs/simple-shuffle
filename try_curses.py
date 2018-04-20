"""Trying out the curses module."""
from curses import wrapper
from binascii import unhexlify


def to_char(keycode: int) -> str:
    if keycode > 255 or keycode < 0:
        raise ValueError("Invalid Keycode!")
    return unhexlify(hex(keycode)[-2:]).decode()


def main(screen):
    screen.clear()
    screen.addstr("Hello, world, from curses!")
    screen.refresh()
    return screen.getch()


print(to_char(wrapper(main)))
