#!/usr/bin/env python3.6
"""A client for simple_shuffle to be used with i3blocks status bar."""
import os
from requests import get, Response
from requests.exceptions import ConnectionError
from strict_hint import strict
base_url = "http://localhost:5000"
color = "#FFFFFF"


@strict
def query(endpoint: str) -> Response:
    """Attempt to get the specified API endpoint, or show no server message."""
    try:
        return get("%s/%s" % (base_url, endpoint))
    except ConnectionError:
        print("shuffle server not running")
        print("")
        exit(0)


try:
    instance = os.environ["BLOCK_INSTANCE"]
except (KeyError):
    instance = None
try:
    click = int(os.environ["BLOCK_BUTTON"])
except (KeyError, ValueError):
    click = None


def play_click_handler(paused: bool):
    """Play or pause and display the play/pause button."""
    if paused:
        if click == 1:
            # Button clicked and state is paued
            query("pause_unpause")
            print("|>")
            print("|>")
            print(color)
            exit(0)
        print("||")
        print("||")
        print(color)
        exit(0)
    if click == 1:
        query("pause_unpause")
        print("||")
        print("||")
        print(color)
        exit(0)
    print("|>")
    print("|>")
    print(color)
    exit(0)


if instance == "playpause":
    # The play-pause button.
    response = query("isplaying")
    if response.status_code not in (200, 204):
        response.raise_for_status()
        raise ValueError("Expected 200 or 204, got %d" % response.status_code)
    play_click_handler(response.status_code == 200)


if instance == "songinfo":
    # Show text from the song_info method
    info = query("song_info").content.decode()
    print(info)
    if ", track" in info:
        print(info.split(", track")[0])
    else:
        print(info)
    print(color)
    exit(0)

if instance == "songinfo.short":
    # Show text from the song_info method
    info = query("song_info").content.decode()
    if ", track" in info:
        print(info.split(", track")[0])
        print(info.split(", track")[0])
    else:
        print(info)
        print(info)
    print(color)
    exit(0)

if instance == "skip.forward":
    if click == 1:
        query("skip")
    print("»", "»", color, sep='\n')

if instance == "skip.backward":
    if click == 1:
        query("previous")
    print("«", "«", color, sep='\n')
