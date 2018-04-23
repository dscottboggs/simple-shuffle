#!/usr/bin/env python3
"""Begin the simple_shuffle and watch for commands on a port."""
from flask import Flask, request
from simple_shuffle.player import Player
from os.path import join as getpath
from os import environ
from json import dumps
# from multiprocessing import Pool
app = Flask(__name__)
# pool = Pool(1)
try:
    player = Player(
        environ['SIMPLE_SHUFFLE_FOLDER'],
        autoplay=True
    )
except KeyError:
    player = Player(
        getpath(environ['HOME'], 'Music'),
        autoplay=True
    )


@app.route("/isplaying")
def isplaying():
    """Get whether or not the player is paused with HTTP response codes.

    Returns 200/OK if the player is playing now, '204/No Content' if it's
    paused.
    """
    if not player.paused:
        return '', 204
    return '', 200


@app.route("/pause_unpause")
def pause_unpause():
    """Call Player.pause_unpause on the thread."""
    player.pause_unpause()
    return ''


@app.route("/quit")
@app.route("/stop")
@app.route("/stop_drop_and_roll")
def stop_drop_and_roll():
    """Stop playback and exit."""
    player.stop_drop_and_roll()
    exit(0)


@app.route("/skip")
def skip():
    """Call Player.skip on the thread."""
    player.skip()
    player.begin_playback()
    return ''


@app.route("/previous")
def previous():
    """Call Player.previous on the thread."""
    player.previous()
    player.begin_playback()
    return ''


@app.route("/volume_up")
def volume_up():
    """Call Player.volume_up on the thread."""
    player.volume_up()
    return ''


@app.route("/volume_down")
def volume_down():
    """Call Player.volume_down on the thread."""
    player.volume_down()
    return ''


@app.route("/current_position")
def get_pos():
    """Return the current time as milliseconds."""
    return str(player.current_position)


@app.route("/current_time")
def gettime():
    """Return the current time as M:SS format."""
    return player.current_time


@app.route("/song_info")
def song_info():
    return player.song_info


@app.route("/current_file")
def current_file():
    return player.current_file


@app.route("/displayed_text")
def displayed_text():
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


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=21212)
