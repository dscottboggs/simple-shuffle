#!/usr/bin/env python3.6
"""Simple keyboard controlled ncurses audio player for shuffling."""
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from magic import detect_from_filename as get_filetype
from os import access
from os.path import isdir, basename
from os import R_OK as FILE_IS_READABLE
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import curses
from binascii import hexlify
from strict_hint import strict
from typing import Dict, Callable
from textwrap import wrap
from config import Config

log = Config.logger
mixer.init(frequency=44100)
valid_filetypes = (
    "audio/x-wav",
    "audio/x-flac",
    "audio/ogg"
)


class Player():
    """An object containing the actual player."""
    def __init__(self, folder: str):
        """Initialize the player with a folder to shuffle."""
        self.shuffle_folder = folder
        self.current_file = "/home/scott/Music/Audioslave - Shadow On The Sun.flac"
        self.begin_playback()
        self.show()

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
        """Return appropriatly formatted ID3 tags from the current file.

        Makes several attempts at picking fewer tags before finally displaying
        the filename as a fallback.
        """
        outtxt: str = ''
        try:
            tags = EasyID3(self.current_file)
        except ID3NoHeaderError:
            # This is raised if there is absolutely no ID3 information in
            # the file
            try:
                outtxt = basename(
                    self.current_file
                ).rsplit('.', maxsplit=1)[0]
                log.debug("Song info: %s", outtxt)
                return outtxt
            except IndexError:
                # the filename has no extension to trim
                outtxt = basename(self.current_file)
                log.debug("Song info: %s", outtxt)
                return outtxt
        try:
            # the default output
            outtxt = "%s by %s,\nTrack %d out of %d from their album, %s." % (
                tags['title'][0],
                tags['artist'][0],
                int(tags['tracknumber'][0].split('/', maxsplit=1)[0]),
                int(tags['tracknumber'][0].split('/', maxsplit=1)[1]),
                tags['album'][0]
            )
            log.debug("Song info: %s", outtxt)
            return outtxt
        except (KeyError, ValueError):
            try:
                # Perhaps the tracknumber or album tags are missing, try
                # displaying just the song title and the artist
                outtxt = "%s by %s" % (tags['title'][0], tags['artist'][0])
                log.debug("Song info: %s", outtxt)
                return outtxt
            except (KeyError, ValueError):
                try:
                    # perhaps there's still a title tag, try displaying that.
                    outtxt = tags['title'][0]
                    log.debug("Song info: %s", outtxt)
                    return outtxt
                except (KeyError, ValueError):
                    # Just return the filename...
                    try:
                        outtxt = basename(
                            self.current_file
                        ).rsplit('.', maxsplit=1)[1]
                        log.debug("Song info: %s", outtxt)
                        return outtxt
                    except IndexError:
                        # the filename has no extension to trim
                        outtxt = basename(self.current_file)
                        log.debug("Song info: %s", outtxt)
                        return outtxt

    @strict
    def begin_playback(self):
        """Play an audio file."""
        filetype = get_filetype(self.current_file).mime_type
        if filetype in valid_filetypes:
            log.debug("Beginning playback of %s", self.current_file)
            mixer.music.load(self.current_file)
            mixer.music.play()
            self.paused = False
        else:
            raise ValueError(
                "Filetype %s of audio file %s isn't playable." % (
                    filetype, self.current_file
                )
                + " This script can only handle wav, flac, and ogg filetypes, "
                + "due to the underlying library capabilities."
            )

    @strict
    def displayed_text(self, maxcolumns, maxlines) -> Dict[str, Dict[str, int]]:
        """Retrieve the text to display and where to display it."""
        text = {}
        song_txt_list = wrap(                   # wrap the text to be one-third
            self.song_info, int(maxcolumns/3)   # of the width of the window.
        )
        for lineno, line in zip(range(len(song_txt_list)), song_txt_list):
            text.update({       # self.show requires a function which returns
                lambda: line: {     # the text, so that it can get updates.
                    'x': int((maxcolumns - len(line)) / 2),
                    'y': int((maxlines-len(song_txt_list)) / 2 + lineno)
                }
            })
        # text.update({     # I'll come back to this
        #     lambda: float(mixer.music.get_pos()/100) + " seconds": {
        #         'x': maxcolumns/3,
        #         'y': maxlines - 1
        #     }
        # })
        text.update({
            lambda: "VOL: %f%%" % mixer.get_volume() * 100: {
                'x': int(maxcolumns - 12),
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
            button_press = curses.wrapper(self.display, self.displayed_text)
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
    def display(screen, text: Callable) -> int:
        """Display some text in ncurses.

        This is essentially a wrapper around stdscr.addstr and stdscr.getch.
        The text must be received in the following format:
            function which returns text to be displayed: {
                x: x coord
                y: y coord
            }
        """
        screen.clear()
        max_lines, max_cols = screen.getmaxyx()
        for txt, coords in text(max_cols, max_lines).items():
            screen.addstr(
                coords['y'],
                coords['x'],
                txt()
            )
        screen.refresh()
        return screen.getch()


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


Player("/home/scott/Music")
