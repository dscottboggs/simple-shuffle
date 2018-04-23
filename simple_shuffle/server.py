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
player = Player(
    environ['SIMPLE_SHUFFLE_FOLDER']
    or getpath(environ['HOME'], 'Music'),
    autoplay=True
)


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
    return str(player.current_position)


@app.route("/song_info")
def song_info():
    return player.song_info


@app.route("/current_file")
def current_file():
    return player.current_file


@app.route("/displayed_text")
def displayed_text():
    return dumps(player.displayed_text(
        maxcolumns=request.args.get("x", 25),
        maxlines=request.args.get("y", 25)
    ))


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=21212)
