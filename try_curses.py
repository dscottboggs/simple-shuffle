"""Trying out the curses module."""
import curses
from binascii import unhexlify


outstr = "Hello, world, from curses!"


def to_char(keycode: int) -> str:
    if keycode > 255 or keycode < 0:
        raise ValueError("Invalid Keycode!")
    return unhexlify(hex(keycode)[-2:]).decode()


def main(screen):
    screen.clear()
    screen.addstr(
        int(curses.LINES/2),
        int((curses.COLS-len(outstr))/2),
        outstr
    )
    screen.refresh()
    return screen.getch()


print(to_char(curses.wrapper(main)))
