#!/usr/bin/env python3.6
"""A client for simple_shuffle to be used with i3blocks status bar."""
import os
from requests import get, Response
from requests.exceptions import ConnectionError
from strict_hint import strict
base_url = "http://localhost:5000"
color = "#FFFFFF"


@strict
def tryget(endpoint: str) -> Response:
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
            tryget("%s/pause_unpause" % base_url)
            print("▶")
            print("▶")
            print(color)
            exit(0)
    if click == 1:
        tryget("%s/pause_unpause" % base_url)
        print("▮▮")
        print("▮▮")
        print(color)
        exit(0)


if instance == "playpause":
    # The play-pause button.
    response = tryget("%s/isplaying" % base_url)
    if response.status_code not in (200, 204):
        response.raise_for_status()
        raise ValueError("Expected 200 or 204, got %d" % response.status_code)
    play_click_handler(response.status_code == 204)

print(
    "Block %s, %s" % (
        instance,
        "Button %s clicked" % click if click else "Not clicked."
    )
)
