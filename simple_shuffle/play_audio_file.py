#!/usr/bin/env python3.6
"""Simple keyboard controlled ncurses audio player for shuffling."""
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from pygame import error as PyGameError
from os import access, walk, environ, unlink
from os import sep as root
from os.path import isdir, basename, exists
from os.path import join as getpath
from os import R_OK as FILE_IS_READABLE
from tinytag import TinyTag, TinyTagException
import curses
from binascii import hexlify
from strict_hint import strict
from typing import Dict, Callable
from textwrap import wrap
from datetime import datetime
from random import shuffle
from blist import blist
import click as cli
import socket
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


class PlayingFile:
    """Methods and data for the currently playing file"""
    def __init__(self, filepath):
        self.filepath = filepath
        self._tags = False

    @property
    def tags(self):
        """Return TinyTag or mutagen metatags for this file."""
        if not self._tags:
            try:
                self._tags = self.get_tiny_tags()
            except TinyTagException:
                self._tags = self.get_mutagen_tags()
                if not self._tags:
                    return get_filename(self.filepath)
        return self._tags

    @strict
    def get_tiny_tags(self):
        """Alias for TinyTag.get()"""
        return TinyTag.get(self.filepath)

    @strict
    def get_mutagen_tags(self) -> str:
        """Return appropriatly formatted metatags from the current file.

        TODO tags from mutagen as a fallback for when TinyTag fails.

        Example file:
            /home/scott/Music/DJ Shadow/(1998) Entroducing/07 - untitled.flac

        """
        return get_filename(self.current_file.filepath)

    @property
    def sample_rate(self):
        """Attempt to retrieve the sample rate.

        In the case that the attempt fails, raise ValueError.
        """
        try:
            return self.get_tiny_tags().samplerate
        except (TinyTagException, LookupError):
            raise ValueError(
                f"Unable to determine sample rate for {self.filepath}"
            )


class Player:
    """An object containing the actual player."""
    @strict
    def __init__(self, folder: str):
        """Initialize the player with a folder to shuffle."""
        self.shuffle_folder = folder
        self.shuffle = Shuffler(self.shuffle_folder)
        self.socket = Config.socket_file_location
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
    def socket(self) -> socket.socket:
        """A socket on which to listen to commands."""
        return self.sock

    @socket.setter
    @strict
    def socket(self, path: str):
        """Set up the command socket."""
        try:
            # the file can't exist already if we're going to bind to it.
            unlink(Config.socket_file_location)
        except OSError:
            if exists(Config.socket_file_location):
                raise
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(Config.socket_file_location)
        self.sock.listen(1)
        self.sock.setblocking(False)

    @property
    @strict
    def current_file(self) -> PlayingFile:
        try:
            if self._current_file.filepath == self.shuffle.current:
                return self._current_file
            self._current_file = PlayingFile(self.shuffle.current)
        except AttributeError:  # the first time there won't be a _current_file
            self._current_file = PlayingFile(self.shuffle.current)
        return self._current_file

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

    @property
    @strict
    def song_info(self) -> str:
        """Return appropriatly formatted metatags from the current file.

        Makes several attempts at picking fewer tags before finally displaying
        the filename as a fallback.
        """
        outtxt: str = ''
        if self.current_file.tags.title is None:
            get_filename(self.current_file.filepath)
        else:
            if self.current_file.tags.track is None\
                    or self.current_file.tags.album is None:
                try:
                    # Perhaps the tracknumber or album tags are missing, try
                    # displaying just the song title and the artist
                    outtxt = "%s by %s" % (
                        self.current_file.tags.artist,
                        self.current_file.tags.title
                    )
                    self.curses_logger("Song info: %s", outtxt)
                    return outtxt
                except (KeyError, ValueError):
                    try:
                        # perhaps there's still a title tag, try just that.
                        outtxt = self.current_file.tags.title
                        self.curses_logger("Song info: %s", outtxt)
                        return outtxt
                    except (KeyError, ValueError):
                        # Just return the filename...
                        get_filename(self.current_file.filepath)
            else:
                # the default output
                outtxt = "%s by %s, track %s from the album %s." % (
                    self.current_file.tags.title,
                    self.current_file.tags.artist,
                    get_track_number(self.current_file.tags),
                    self.current_file.tags.album
                )
                self.curses_logger("Song info: %s", outtxt)
                return outtxt

    @strict
    def begin_playback(self) -> None:
        """Play an audio file."""
        mixer.quit()
        try:
            mixer.init(self.current_file.sample_rate)
        except ValueError:
            log.info(
                "TinyTag couldn't parse the tags for %s"
                % self.current_file.filepath
            )
            self.skip()
            self.begin_playback()
        try:
            log.debug(
                f"Attempting to begin playback of {self.current_file.filepath}"
            )
            mixer.music.load(self.current_file.filepath)
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
        text.update({
            str(int(float(mixer.music.get_pos()/1000))) + " seconds": {
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
            try:
                data_from_socket, _ = self.socket.accept()
            except BlockingIOError:
                data_from_socket = None
            if data_from_socket:
                # parse data from socket
                ...
            else:
                button_press = curses.wrapper(
                    self.display, self.displayed_text, self.curses_logger
                )

            def skip_back():
                if mixer.music.get_pos() <= 5000:
                    self.previous()
                    self.begin_playback()
                else:
                    self.restart()
                    self.begin_playback()

            def skip():
                self.skip()
                self.begin_playback()

            def pause():
                log.debug(
                    "Pausing playback at %d",
                    mixer.music.get_pos() / 1000
                )
                mixer.music.pause()
                self.paused = True

            def unpause():
                log.debug("Resuming playback.")
                mixer.music.unpause()
                self.paused = False

            def stop_drop_and_roll():
                log.debug("Stopping and exiting")
                self.socket.close()
                mixer.music.stop()
                mixer.quit()
                exit(0)
            button_action = blist([None])
            button_action *= 2**16  # I just picked that number because it'll
            # probably be big enough. Could be 32 or 64 if need be.
            button_action[curses.KEY_DOWN] = lambda: mixer.music.set_volume(
                mixer.music.get_volume() - 0.05
            )
            button_action[curses.KEY_UP] = lambda: mixer.music.set_volume(
                mixer.music.get_volume() + 0.05
            )
            button_action[curses.KEY_LEFT] = skip_back
            button_action[curses.KEY_RIGHT] = skip
            button_action[char_to_int(' ')] = pause if self.paused else unpause
            button_action[char_to_int('s')] = stop_drop_and_roll
            button_action[char_to_int('q')] = stop_drop_and_roll
            try:
                button_action[button_press]()        # call the function at the
                #                     index of the number received from getch()
            except IndexError:
                log.debug("Unexpected keystroke %d received." % button_press)

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


def get_track_number(tags: TinyTag) -> str:
    """Get either the track number with or without the total."""
    return str(tags.track) if tags.track_total is None\
        else f"{tags.track} out of {tags.track_total}"


def get_filename(filepath: str) -> str:
    """Get the filename without its path or extension."""
    try:
        outtxt = basename(filepath).rsplit('.', maxsplit=1)[0]
        return outtxt
    except IndexError:
        # the filename has no extension to trim
        outtxt = basename(filepath)
        return outtxt


if __name__ == '__main__':
    main()
