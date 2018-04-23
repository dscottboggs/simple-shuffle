#!/usr/bin/env python3.6
"""A curses interface to the Flask server API."""
import curses
from binascii import hexlify
from strict_hint import strict
from typing import Callable, Dict, Union
from requests import get, Response
from requests.exceptions import ConnectionError
from datetime import datetime
from blist import blist
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


class FrozenDetector:
    """Detect that playback has stalled."""
    def __init__(self):
        self.same_counter: int = 0
        self.time_value: int = 0

    @strict
    def check(self, time: Union[int, str, float]) -> bool:
        """Get whether or not the time has been the same for too long.

        "Too long" is defined in config.py as Config.frozen_threshold.
        returns a boolean based on whether or not it's "frozen".
        """
        if self.time_value == int(time):
            self.same_counter += 1
        self.time_value = int(time)
        if self.same_counter >= Config.frozen_threshold:
            return True
        return False

    def reset(self):
        self.same_counter = 0
        self.time_value = 0


class CursesInterface():
    """A curses interface to the Flask server API."""
    def __init__(self):
        self.freezedetect = FrozenDetector()
        self.show()

    @property
    @strict
    def paused(self):
        return self.query("isplaying").status_code == 200

    @staticmethod
    @strict
    def query(server_method: str) -> Response:
        """Query the server for a specified method."""
        if server_method == "disconnect":
            exit(0)
        try:
            return get("%s/%s" % (Config.server_url, server_method))
        except ConnectionError:
            if server_method in ("stop", "quit", "stop_drop_and_roll"):
                exit(0)
            raise

    @staticmethod
    @strict
    def displayed_text(columns: int, lines: int) -> Dict[str, Dict[str, str]]:
        """Query the server for the value from Player.displayed_text."""
        return get(
            f"{Config.server_url}/displayed_text?x={columns}&y={lines}"
        ).json()

    def show(self):
        """Loop curses display and keycode watching.

        When a keypress is returned from display(), it will be checked to see
        if it's one of the ones we're watching for, then the display will
        be refreshed again, unless the stop button is pressed, then exit.
        """
        while True:
            current_position = int(
                self.query("current_position").content.decode()
            )
            if current_position == -1:
                self.query("skip")
            if not self.paused:
                if self.freezedetect.check(
                            current_position
                        ):
                    Config.logger.warn(
                        "Player frozen at %s on %s!" % (
                            current_position,
                            self.query("current_file").content.decode()
                        )
                    )
                    self.freezedetect.reset()
                    self.query("skip")
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
            button_action[char_to_int('q')] = "disconnect"
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
