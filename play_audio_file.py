#!/usr/bin/env python3.6
# SimpleAudio and PyAudio only accept .wav files, use PyGame
from pygame import mixer
from magic import detect_from_filename as get_filetype

mixer.init(frequency=44100)
valid_filetypes = (
    "audio/x-wav",
    "audio/x-flac",
    "audio/ogg"
)

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

play_audio_file("Music/Moon Hooch/14 Mega Tubes.ogg")
