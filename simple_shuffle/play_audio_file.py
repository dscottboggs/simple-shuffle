#!/usr/bin/env python3.6
"""Simple keyboard controlled ncurses audio player for shuffling."""
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from pygame import error as PyGameError
from os import access, walk, environ
from os import sep as root
from os.path import isdir, basename
from os.path import join as getpath
from os import R_OK as FILE_IS_READABLE
from tinytag import TinyTag
import curses
from binascii import hexlify
from strict_hint import strict
from typing import Dict, Callable
from textwrap import wrap
from datetime import datetime
from random import shuffle
import click as cli
from config import Config

log = Config.logger
mixer.init(frequency=Config.sample_rate)


@strict
def char_to_int(char: str) -> int:
    """Get the ascii value for a single character."""
    if len(char) != 1:
        raise ValueError(
            "The input stwing can onwwy be one chawacter long! Received %s"
            % char
        )
    return int(                 # the decimal equivalent
        hexlify(                # of the hex value of
            bytes(              # the string converted to a bytes-sequence
                char, 'ascii'   # encoded as ASCII
            )
        ), 16
    )


@cli.command("shuffle")
@cli.argument("shuffle_folder", required=False)
def main(*args, **kwargs):
    """The simple_shuffle script shuffles a folder of flac and ogg files.

    It does a true shuffle of all of the songs in the folder, without repeats,
    unless you've got duplicates. Specify the folder to be shuffled on the
    command line just after the name. By default it shuffles /home/$USER/Music.
    """
    if kwargs['shuffle_folder'] is None:
        Player(getpath(root, 'home', environ['USER'], 'Music'))
    else:
        Player(kwargs['shuffle_folder'])


@strict
def list_recursively(f: str, *filepath) -> list:
    """Get a list of all files in a folder and its subfolders.

    :return: list: Absolute paths of all files in the folder.
    """
    if not isdir(getpath(f, *filepath)):
        # If the specified file isn't a directory, just return that one file.
        return [getpath(f, *filepath)]
    return [
        getpath(dp, f) for dp, dn, fn in walk(
            getpath(f, *filepath)
        ) for f in fn
    ]


class Shuffler:
    """Get all of the files in the folder, in a shuffled order."""
    def __init__(self, folder):
        self.files = list_recursively(folder)
        shuffle(self.files)
        self.index = 0

    def __iter__(self):
        return self

    @property
    def future(self):
        try:
            return self.files[self.index]
        except IndexError:
            return None

    @property
    def past(self):
        try:
            return self.files[self.index - 2]
        except IndexError:
            return None

    def previous(self):
        if self.index > 0:
            self.index -= 1
            return self.future
        else:
            raise StopIteration

    def next(self):
        """Get the current iteration point, and increment the index."""
        if self.index < len(self.files):
            self.index += 1
            return self.current
        else:
            raise StopIteration

    @property
    def current(self):
        """Get the current iteration point without updating the index."""
        return self.files[self.index - 1]


class Player():
    """An object containing the actual player."""
    @strict
    def __init__(self, folder: str):
        """Initialize the player with a folder to shuffle."""
        self.shuffle_folder = folder
        self.shuffle = Shuffler(self.shuffle_folder)
        self.begin_playback()
        self.show()

    @strict
    def restart(self) -> str:
        """Restart the currently playing song."""
        mixer.music.set_pos(0)
        return self.shuffle.current

    @strict
    def previous(self) -> str:
        """Go back to the previous song or restart the current one.

        Calls self.restart() if StopIteration is raised.
        """
        log.debug(
            "Skip-backwards button pressed.\nCurrent file: %s"
            + "\tCurrent Index:%d"
        )
        try:
            return self.shuffle.previous()
        except StopIteration:
            return self.restart()

    @strict
    def skip(self) -> str:
        """Skip to the next file in the shuffler."""
        log.debug(
            "Skip button pressed.\nCurrent file: %s\nNext file:%s",
            self.shuffle.current,
            self.shuffle.future
        )
        try:
            return self.shuffle.next()
        except StopIteration:
            log.fatal("List of tracks has been exhausted.")
            exit(0)

    @property
    @strict
    def current_file(self) -> str:
        return self.shuffle.current

    @property
    @strict
    def shuffle_folder(self) -> str:
        """Getter for the shuffle_folder attr."""
        return self._shuffle_folder

    @shuffle_folder.setter
    @strict
    def shuffle_folder(self, folder: str):
        """Verify and set the folder that we'll be shuffling over."""
        if access(folder, FILE_IS_READABLE) and isdir(folder):
            # Make sure that the folder is a valid folder and is readable.
            self._shuffle_folder = folder
        else:
            raise ValueError("%s is not accessible!" % folder)

    def get_tags(self, filename):
        """Get the tags from an arbitrary file.

        Alias for TinyTag.get.
        """
        return TinyTag.get(filename)

    @property
    @strict
    def song_info(self) -> str:
        """Return appropriatly formatted ID3 tags from the current file.

        Makes several attempts at picking fewer tags before finally displaying
        the filename as a fallback.
        """
        tags = self.get_tags(
            self.current_file
        )
        outtxt: str = ''
        if tags.title is None:
            get_filename(self.current_file)
        else:
            if tags.track is None or tracks.album is None:
                try:
                    # Perhaps the tracknumber or album tags are missing, try
                    # displaying just the song title and the artist
                    outtxt = f"{tags.title} by {tags.artist}"
                    self.curses_logger("Song info: %s", outtxt)
                    return outtxt
                except (KeyError, ValueError):
                    try:
                        # perhaps there's still a title tag, try just that.
                        outtxt = tags.title
                        self.curses_logger("Song info: %s", outtxt)
                        return outtxt
                    except (KeyError, ValueError):
                        # Just return the filename...
                        get_filename(self.current_file)
            else:
                # the default output
                outtxt = "%s by %s, track %s from the album %s." % (
                    tags.title,
                    tags.artist,
                    get_track_number(tags),
                    tags.album
                )
                self.curses_logger("Song info: %s", outtxt)
                return outtxt

    @strict
    def begin_playback(self) -> None:
        """Play an audio file."""
        try:
            log.debug("Attempting to begin playback of {self.current_file}")
            mixer.music.load(audio_file)
            mixer.music.play()
            self.paused = False
        except PyGameError:
            self.skip()
            self.begin_playback()

    @strict
    def displayed_text(
                self, maxcolumns, maxlines
            ) -> Dict[str, Dict[str, int]]:
        """Retrieve the text to display and where to display it."""
        text = {}
        song_txt_list = wrap(                   # wrap the text to be one-third
            self.song_info, int(maxcolumns/3)   # of the width of the window.
        )
        for lineno in range(len(song_txt_list)):
            text.update({
                song_txt_list[lineno]: {
                    'x': int((maxcolumns - len(song_txt_list[lineno])) / 2),
                    'y': int((maxlines-len(song_txt_list)) / 2 + lineno)
                }
            })
        text.update({     # I'll come back to this
            str(float(mixer.music.get_pos()/1000)) + " seconds": {
                'x': 2,
                'y': int(maxlines) - 1
            }
        })
        text.update({
            "VOL: %f%%" % (float(mixer.music.get_volume()) * 100): {
                'x': int(maxcolumns - 17),
                'y': int(maxlines - 1)
            }
        })
        return text

    def show(self):
        """Loop curses display and keycode watching.

        When a keypress is returned from display(), it will be checked to see
        if it's one of the ones we're watching for, then the display will
        be refreshed again, unless the stop button is pressed, then exit.
        """
        while True:
            if mixer.music.get_pos() == -1:
                self.skip()
                self.begin_playback()
            button_press = curses.wrapper(
                self.display, self.displayed_text, self.curses_logger
            )
            # Wraps the "display" function call in a curses window.
            if button_press == curses.KEY_DOWN:
                log.debug(
                    "Volume down button pressed. Current volume: %f.",
                    mixer.music.get_volume()
                )
                mixer.music.set_volume(mixer.music.get_volume() - 0.05)
            if button_press == curses.KEY_UP:
                log.debug(
                    "Volume up button pressed. Current volume: %f.",
                    mixer.music.get_volume()
                )
                mixer.music.set_volume(mixer.music.get_volume() + 0.05)
            if button_press == curses.KEY_RIGHT:
                self.skip()
                self.begin_playback()
            if button_press == curses.KEY_LEFT \
                    and mixer.music.get_pos() <= 5000:
                self.previous()
                self.begin_playback()
            if button_press == curses.KEY_LEFT \
                    and mixer.music.get_pos() > 5000:
                self.restart()
                self.begin_playback()
            if button_press == char_to_int(' '):
                if mixer.music.get_busy() and not self.paused:
                    log.debug(
                        "Pausing playback at %d",
                        mixer.music.get_pos() / 100
                    )
                    mixer.music.pause()
                    self.paused = True
                elif self.paused:
                    log.debug("Resuming playback.")
                    mixer.music.unpause()
                    self.paused = False
            if button_press == char_to_int('s')\
                    or button_press == char_to_int('q'):
                log.debug("Stopping and exiting")
                mixer.music.stop()
                exit(0)

    @staticmethod
    def display(screen, text: Callable, logger) -> int:
        """Display some text in ncurses.

        This is essentially a wrapper around stdscr.addstr and stdscr.getch.
        The text must be received in the following format:
            function which returns text to be displayed: {
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


def get_track_number(tags: TinyTag) -> str:
    """Get either the track number with or without the total."""
    return str(tags.track) if tags.track_total is None\
        else f"{tags.track} out of {tags.track_total}"


def get_filename(filepath: str) -> str:
    """Get the filename without its path or extension."""
    try:
        outtxt = basename(
            self.current_file
        ).rsplit('.', maxsplit=1)[0]
        self.curses_logger("Song info: %s", outtxt)
        return outtxt
    except IndexError:
        # the filename has no extension to trim
        outtxt = basename(self.current_file)
        self.curses_logger("Song info: %s", outtxt)
        return outtxt


if __name__ == '__main__':
    main()
