#!/usr/bin/env python3.6
"""Simple keyboard controlled ncurses audio player for shuffling."""
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from magic import detect_from_filename as get_filetype
from os import environ, access
from os.path import isdir, basename
from os import X_OK as FILE_IS_EXECUTABLE
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import curses
from binascii import hexlify
from strict_hint import strict

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
        try:
            tags = EasyID3(self.current_file)
        except ID3NoHeaderError:
            # This is raised if there is absolutely no ID3 information in
            # the file
            return self.current_file.split('/')[-1:]
        try:
            # the default output
            return "%s by %s,\nTrack %d out of %d from their album, %s." % (
                tags['title'][0],
                tags['artist'][0],
                int(tags['tracknumber'][0].split('/', maxsplit=1)[0]),
                int(tags['tracknumber'][0].split('/', maxsplit=1)[1]),
                tags['album'][0]
            )
        except (KeyError, ValueError):
            try:
                # Perhaps the tracknumber or album tags are missing, try
                # displaying just the song title and the artist
                return "%s by %s" % (tags['title'][0], tags['artist'][0])
            except (KeyError, ValueError):
                try:
                    # perhaps there's still a title tag, try displaying that.
                    return tags['title'][0]
                except (KeyError, ValueError):
                    # Just return the filename...
                    try:
                        return basename(
                            self.current_file
                        ).rsplit('.', maxsplit=1)[1]
                    except IndexError:
                        # the filename has no extension to trim
                        return basename(self.current_file)

    @strict
    def begin_playback(self):
        """Play an audio file."""
        filetype = get_filetype(self.current_file).mime_type
        if filetype in valid_filetypes:
            mixer.music.load(self.current_file)
            mixer.music.play()
        else:
            raise ValueError(
                "Filetype %s of audio file %s isn't playable." % (
                    filetype, self.current_file
                )
                + " This script can only handle wav, flac, and ogg filetypes, "
                + "due to the underlying library capabilities."
            )

    def show(self):
        """Loop curses display and keycode watching.

        When a keypress is returned from display(), it will be checked to see
        if it's one of the ones we're watching for, then the display will
        be refreshed again, unless the stop button is pressed, then exit.
        """
        while True:
            button_press = curses.wrapper(self.display, self.song_info)
            # Wraps the "display" function call in a curses window.
            if button_press == char_to_int(' '):
                if mixer.music.get_busy():
                    mixer.music.pause()
                else:
                    mixer.music.unpause()
            if button_press == char_to_int('s')\
                    or button_press == char_to_int('q'):
                mixer.music.stop()
                exit(0)

    @staticmethod
    @strict
    def display(screen, text: str) -> str:
        """Display some text centered in the screen."""
        screen.clear()
        for lineno, line in zip(
                    range(len(text.split('\n'))),
                    text.split('\n')
                ):
            screen.addstr(
                int((curses.LINES - len(text.split('\n'))) / 2) + lineno,
                int((curses.COLS-len(line))/2),
                line
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
