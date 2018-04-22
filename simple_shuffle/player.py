#!/usr/bin/env python3.6
"""Simple audio player for shuffling."""
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from pygame import error as PyGameError
from os import access, walk, environ
from os import sep as root
from os.path import isdir, basename
from os.path import join as getpath
from os import R_OK as FILE_IS_READABLE
from tinytag import TinyTag, TinyTagException
from strict_hint import strict
from typing import Dict, Union
from textwrap import wrap
from random import shuffle
import click as cli
from simple_shuffle.config import Config


log = Config.logger


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
    def __init__(self,
                 folder: str,
                 autoplay: bool=True
            ):
        """Initialize the player with a folder to shuffle."""
        self.shuffle_folder = folder
        self.shuffle = Shuffler(self.shuffle_folder)
        if autoplay:
            self.begin_playback()

    @staticmethod
    def volume_up():
        mixer.music.set_volume(
            mixer.music.get_volume() + 0.05
        )

    @staticmethod
    def volume_down():
        mixer.music.set_volume(
            mixer.music.get_volume() - 0.05
        )

    def pause_unpause(self):
        """Pause playing playback, or unpause if paused."""
        if self.paused:
            log.debug("Resuming playback.")
            mixer.music.unpause()
            self.paused = False
        else:
            log.debug(
                "Pausing playback at %d",
                self.current_position / 1000
            )
            mixer.music.pause()
            self.paused = True

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
        if self.current_position < 5000:
            return self.restart()
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
                    log.debug("Song info: %s", outtxt)
                    return outtxt
                except (KeyError, ValueError):
                    try:
                        # perhaps there's still a title tag, try just that.
                        outtxt = self.current_file.tags.title
                        log.debug("Song info: %s", outtxt)
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
                log.debug("Song info: %s", outtxt)
                return outtxt

    @property
    @strict
    def current_position(self):
        """Get the current position."""
        return mixer.music.get_pos()

    @strict
    def begin_playback(self) -> None:
        """Play an audio file."""
        mixer.quit()
        try:
            mixer.init(self.current_file.sample_rate)
        except (ValueError, TypeError):
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
                self, maxcolumns: Union[str, int], maxlines: Union[str, int]
            ) -> Dict[str, Dict[str, int]]:
        """Retrieve the text to display and where to display it."""
        text = {}
        song_txt_list = wrap(                   # wrap the text to be one-third
            self.song_info, int(int(maxcolumns)/3)   # of the width of the window.
        )
        for lineno in range(len(song_txt_list)):
            text.update({
                song_txt_list[lineno]: {
                    'x': int(
                        (int(maxcolumns) - len(song_txt_list[lineno])) / 2
                    ),
                    'y': int((int(maxlines)-len(song_txt_list)) / 2 + lineno)
                }
            })
        text.update({
            str(int(float(self.current_position/1000))) + " seconds": {
                'x': 2,
                'y': int(int(maxlines)) - 1
            }
        })
        text.update({
            "VOL: %f%%" % (float(mixer.music.get_volume()) * 100): {
                'x': int(int(maxcolumns) - 17),
                'y': int(int(maxlines) - 1)
            }
        })
        return text

    def stop_drop_and_roll(self):
        log.debug("Stopping and exiting")
        mixer.music.stop()
        mixer.quit()
        exit(0)


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
