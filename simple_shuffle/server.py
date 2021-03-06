#!/usr/bin/env python3
"""Begin the simple_shuffle and watch for commands on a port."""
from flask import Flask, request, Response
from simple_shuffle.player import Player
from os.path import join as getpath
from os import environ
from json import dumps
from strict_hint import strict
from typing import Tuple, Union
from simple_shuffle.config import Config


class FrozenDetector:
    """Detect that playback has stalled."""
    def __init__(self):
        Config.logger.debug("Initializing the FrozenDetector")
        self.same_counter: int = 0
        self.time_value: int = 0

    @strict
    def check(self, time: Union[int, str, float]) -> bool:
        """Get whether or not the time has been the same for too long.

        "Too long" is defined in config.py as Config.frozen_threshold. The
        method returns a boolean based on whether or not it's "frozen".

        time is converted internally to an int, so using a value like "Seven"
        will throw a ValueError and a value like 1.04309 will cause
        unpredicatble results.
        """
        Config.logger.debug(
            "Checking if frozen. Time: %d; Stored time: %d; Counter %d",
            int(time),
            self.time_value,
            self.same_counter
        )
        if self.time_value == int(time):
            self.same_counter += 1
        self.time_value = int(time)
        if self.same_counter >= Config.frozen_threshold:
            Config.logger.warn(
                "Frozen! Time: %d; Stored time: %d; Counter %d",
                int(time),
                self.time_value,
                self.same_counter
            )
            return True
        return False

    def reset(self):
        self.same_counter = 0
        self.time_value = 0

# class PlayerServer(Flask):
#     """The Flask server object to pair with the player."""
#     def __init__(self, import_name, player, *args, **kwargs):
#         self.frozen = FrozenDetector()
#         self.player = player
#         super().__init__(import_name, *args, **kwargs)


try:
    player = Player(environ['simple_shuffle_folder'])
except KeyError:
    try:
        player = Player(getpath(environ['HOME'], "Music"))
    except KeyError:
        player = Player(getpath('/', 'home', environ['USER'], "Music"))

app = Flask(__name__)
frozen = FrozenDetector()


@app.before_request
def check_frozen():
    """Check to see if the player is frozen."""
    if player.paused:
        if frozen.check(player.current_position):
            player.skip()
            player.begin_playback()
            frozen.reset()


def isplaying() -> Tuple[str, int]:
    """Get whether or not the player is paused with HTTP response codes.

    Returns 200/OK if the player is playing now, '204/No Content' if it's
    paused.
    """
    if not player.paused:
        return '', 204
    return '', 200
app.add_url_rule("/isplaying", "isplaying", isplaying)


def pause_unpause() -> str:
    """Call Player.pause_unpause on the thread."""
    player.pause_unpause()
    return ''
app.add_url_rule("/pause_unpause", "pause_unpause", pause_unpause)


def stop_drop_and_roll():
    """Stop playback and exit."""
    player.stop_drop_and_roll()
    exit(0)
app.add_url_rule(
    "/stop_drop_and_roll", "stop_drop_and_roll", stop_drop_and_roll
)
app.add_url_rule("/quit", "stop_drop_and_roll", stop_drop_and_roll)
app.add_url_rule("/stop", "stop_drop_and_roll", stop_drop_and_roll)


@strict
def skip() -> str:
    """Call Player.skip on the thread."""
    player.skip()
    player.begin_playback()
    return ''
app.add_url_rule("/skip", "skip", skip)


@strict
def previous() -> str:
    """Call Player.previous on the thread."""
    player.previous()
    player.begin_playback()
    return ''
app.add_url_rule("/previous", "previous", previous)


@strict
def current_volume() -> str:
    """Retrieve the current volume as a str of a float between 0 and 1."""
    return str(player.current_volume)
app.add_url_rule("/current_volume", "current_volume", current_volume)


@strict
def volume_up() -> str:
    """Call Player.volume_up on the thread."""
    player.volume_up()
    return ''
app.add_url_rule("/volume_up", "volume_up", volume_up)


@strict
def volume_down() -> str:
    """Call Player.volume_down on the thread."""
    player.volume_down()
    return ''
app.add_url_rule("/volume_down", "volume_down", volume_down)


@strict
def current_position() -> str:
    """Return the current time as milliseconds."""
    return str(player.current_position)
app.add_url_rule("/current_position", "current_position", current_position)


@strict
def current_time() -> str:
    """Return the current time as M:SS format."""
    return player.current_time
app.add_url_rule("/current_time", "current_time", current_time)


@strict
def song_info() -> str:
    """Get just the song-info text generated from the tags or filename."""
    return player.song_info
app.add_url_rule("/song_info", "song_info", song_info)


@strict
def current_file() -> str:
    """Retrieve the current filename."""
    return player.current_file.filepath
app.add_url_rule("/current_file", "current_file", current_file)


@strict
def displayed_text() -> str:
    """Retrieve the current text to display, given lines and columns.

    This is for the curses client, other clients should implement different
    methods for getting this data, that doesn't depend on lines and columns,
    unless lines and columns are convenient, but I really can't see another
    use for that outside of curses.
    """
    return dumps(player.displayed_text(
        maxcolumns=request.args.get("x", 25),
        maxlines=request.args.get("y", 25)
    ))
app.add_url_rule("/displayed_text", "displayed_text", displayed_text)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=21212)
