"""A curses interface to the Flask server API."""
import curses
from binascii import hexlify
from strict_hint import strict
from typing import Callable, Dict
from requests import get
from datetime import datetime
import blist
from simple_shuffle.server import app
from simple_shuffle.config import Config


@strict
def char_to_int(char: str) -> int:
    """Get the ascii value for a single character."""
    if len(char) != 1:
        raise ValueError(
            "The input string can only be one character long! Received %s"
            % char
        )
    return int(                 # the decimal equivalent
        hexlify(                # of the hex value of
            bytes(              # the string converted to a bytes-sequence
                char, 'ascii'   # encoded as ASCII
            )
        ), 16
    )


class CursesInterface():
    """A curses interface to the Flask server API."""
    def __init__(self, arg):
        self.show()

    @staticmethod
    def query(server_method: str):
        """Query the server for a specified method."""
        get("%s/%s" % (Config.server_url, server_method))

    @staticmethod
    def displayed_text() -> Dict[str, Dict[str, str]]:
        """Query the server for the value from Player.displayed_text."""
        get(f"{Config.server_url}/displayed_text").json()

    def show(self):
        """Loop curses display and keycode watching.

        When a keypress is returned from display(), it will be checked to see
        if it's one of the ones we're watching for, then the display will
        be refreshed again, unless the stop button is pressed, then exit.
        """
        while True:
            if self.query("current_position") == -1:
                self.skip()
                self.begin_playback()
            button_press = curses.wrapper(
                self.display, self.displayed_text, self.curses_logger
            )
            button_action = blist([None])
            button_action *= 2**16  # I just picked that number because it'll
            # probably be big enough. Could be 32 or 64 if need be.
            button_action[curses.KEY_DOWN] = "volume_down"
            button_action[curses.KEY_UP] = "volume_up"
            button_action[curses.KEY_LEFT] = "previous"
            button_action[curses.KEY_RIGHT] = "skip"
            button_action[char_to_int(' ')] = "pause_unpause"
            button_action[char_to_int('s')] = "stop_drop_and_roll"
            button_action[char_to_int('q')] = "stop_drop_and_roll"
            if button_action[button_press] is not None:
                self.query(button_action[button_press])     # call the function
                #              at the index of the number received from getch()

    @staticmethod
    def display(screen, text: Callable, logger) -> int:
        """Display some text in ncurses.

        This is essentially a wrapper around stdscr.addstr and stdscr.getch.
        The text must be received in the following format:
            text to be displayed: {
                x: x coord
                y: y coord
            }
        """
        curses.halfdelay(Config.display_refresh_delay)
        screen.clear()
        logger(
            " ------- Entering curses mode @ %s -------- ",
            datetime.now().isoformat()
        )
        max_lines, max_cols = screen.getmaxyx()
        logger("Max width: %d\nMax height:%d", max_cols, max_lines)
        for txt, coords in text(max_cols, max_lines).items():
            logger(
                "Adding string %s\nAt %d columns by %d lines",
                txt,
                coords['x'],
                coords['y']
            )
            screen.addstr(
                coords['y'],
                coords['x'],
                txt
            )
        screen.refresh()
        return screen.getch()

    @staticmethod
    @strict
    def curses_logger(text: str, *fstrings):
        """Function compatible with logger.funcs to write to a file.

        You can't display shit when curses is active.
        """
        if fstrings:
            with open(Config.curses_logfile, 'a') as logfile:
                logfile.write(text % fstrings + '\n')
        else:
            with open(Config.curses_logfile, 'a') as logfile:
                logfile.write(text + '\n')


CursesInterface()
