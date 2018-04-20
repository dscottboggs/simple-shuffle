#!/usr/bin/env python3.6
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from magic import detect_from_filename as get_filetype
from time import sleep
from os import environ
from typing import List, Tuple
from mutagen.easyid3 import EasyID3
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
    screen.addstr(
        int(curses.LINES/2),
        int((curses.COLS-len(text))/2),
        text
    )
    screen.refresh()
    return to_char(screen.getch())


@strict
def display_info(filename: str):
    """Display info about the currently playing audio file."""
    try:
        if environ['BLOCK_INSTANCE'] == 'currently_playing':
            # just print the info.
            print(get_id3_tags(filename))
    except KeyError:
        # launched from term, use curses display
        while True:
            button_press = curses.wrapper(cursesdisplay, str(EasyID3(filename)))
            if button_press:
                print(button_press)
                break


play_audio_file("/home/scott/Music/Moon Hooch/14 Mega Tubes.ogg")
display_info("/home/scott/Music/Moon Hooch/14 Mega Tubes.mp3")
sleep(5)
mixer.music.stop()
