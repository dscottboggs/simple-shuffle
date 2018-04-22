#!/usr/bin/env python3
"""Begin the simple_shuffle and watch for commands on a port."""
from flask import Flask, request
from simple_shuffle.player import Player
import click as cli
from os.path import join as getpath
from os import environ
from os import sep as root
from json import dumps
# from multiprocessing import Pool
app = Flask(__name__)
# pool = Pool(1)
player = Player(
    getpath(root, 'home', environ['USER'], 'Music'),
    autoplay=True
)


@cli.command("shuffle-server")
@cli.argument("shuffle_folder", required=False)
def main(*args, **kwargs):
    """The shuffle-server script shuffles a folder of flac and ogg files.

    It does a true shuffle of all of the songs in the folder, without repeats,
    unless you've got duplicates. Specify the folder to be shuffled on the
    command line just after the name. By default it shuffles /home/$USER/Music.

    The server version sets up a Flask server to respond to actions on a port
    through standard HTTP requests.
    """
    if kwargs['shuffle_folder'] is None:
        return Player(getpath(root, 'home', environ['USER'], 'Music'))
    else:
        return Player(kwargs['shuffle_folder'])


# player = main()


@app.route("/pause_unpause")
def pause_unpause():
    """Call Player.pause_unpause on the thread."""
    player.pause_unpause()
    return ''


@app.route("/quit")
@app.route("/stop")
def stop_drop_and_roll():
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
