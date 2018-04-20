#!/usr/bin/env python3.6
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from magic import detect_from_filename as get_filetype
from time import sleep
from os import environ
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import curses
from binascii import unhexlify
from strict_hint import strict

mixer.init(frequency=44100)
valid_filetypes = (
    "audio/x-wav",
    "audio/x-flac",
    "audio/ogg"
)


@strict
def get_song_info(filename: str) -> str:
    try:
        tags = EasyID3(filename)
    except ID3NoHeaderError:
        return filename.split('/')[-1:]
    try:
        return "%s by %s,\nTrack %d out of %d from their album, %s." % (
            tags['title'][0],
            tags['artist'][0],
            int(tags['tracknumber'][0].split('/', maxsplit=1)[0]),
            int(tags['tracknumber'][0].split('/', maxsplit=1)[1]),
            tags['album'][0]
        )
    except (KeyError, ValueError):
        try:
            return "%s by %s" % (tags['title'][0], tags['artist'][0])
        except (KeyError, ValueError):
            try:
                return "%s" % tags['title'][0]
            except (KeyError, ValueError):
                return filename.split("/")[-1:]


@strict
def to_char(keycode: int) -> str:
    if keycode > 255 or keycode < 0:
        raise ValueError("Invalid Keycode!")
    return unhexlify(hex(keycode)[-2:]).decode()


@strict
def play_audio_file(filename: str):
    """Plays an audio file."""
    filetype = get_filetype(filename).mime_type
    if filetype in valid_filetypes:
        mixer.music.load(filename)
        mixer.music.play()
    else:
        raise ValueError(
            f"Filetype {filetype} of audio file {filename} isn't playable."
            + " This script can only handle wav, flac, and ogg filetypes, "
            + "due to the underlying library capabilities."
        )


@strict
def cursesdisplay(screen, text: str) -> str:
    """Display some text centered in the screen."""
    screen.clear()
    for lineno, line in zip(range(len(text.split('\n'))), text.split('\n')):
        screen.addstr(
            int((curses.LINES - len(text.split('\n'))) / 2) + lineno,
            int((curses.COLS-len(line))/2),
            line
        )
    screen.refresh()
    return to_char(screen.getch())


@strict
def controls_wrapper(text_for_display: str) -> None:
    while True:
        button_press = curses.wrapper(cursesdisplay, text_for_display)
        if button_press == ' ':
            if mixer.music.get_busy():
                mixer.music.pause()
            else:
                mixer.music.unpause()
        if button_press == 's':
            mixer.music.stop()
            break


@strict
def display_info(filename: str):
    """Display info about the currently playing audio file."""
    try:
        if environ['BLOCK_INSTANCE'] == 'currently_playing':
            # just print the info.
            print(get_song_info(filename))
    except KeyError:
        # launched from term, use curses display
        controls_wrapper(filename)


play_audio_file("/home/scott/Music/Moon Hooch/14 Mega Tubes.ogg")
display_info("/home/scott/Music/Moon Hooch/14 Mega Tubes.mp3")
sleep(5)
mixer.music.stop()
