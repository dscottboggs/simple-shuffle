#!/usr/bin/env python3
"""Begin the simple_shuffle and watch for commands on a port."""
from flask import Flask
from simple_shuffle.play_audio_file import Player
import click as cli
from os.path import join as getpath
from os import environ
from os import sep as root
from multiprocessing import Pool
app = Flask(__name__)
pool = Pool(1)
player = Player(
    getpath(root, 'home', environ['USER'], 'Music'),
    autoplay=True,
    curses_display=False
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
    pool.apply(player.pause_unpause)


@app.route("/skip")
def skip():
    """Call Player.skip on the thread."""
    pool.apply(player.skip)


@app.route("/previous")
def previous():
    """Call Player.previous on the thread."""
    pool.apply(player.previous)


@app.route("/volume_up")
def volume_up():
    """Call Player.volume_up on the thread."""
    pool.apply(player.volume_up)


@app.route("/volume_down")
def volume_down():
    """Call Player.volume_down on the thread."""
    pool.apply(player.volume_down)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="21212")
