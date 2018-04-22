from flask import Flask
from play_audio_file import Player
from click import click as cli
from os.path import join as getpath
from os import environ
from os import sep as root
from multiprocessing import Pool
app = Flask(__name__)


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
        Player(getpath(root, 'home', environ['USER'], 'Music'))
    else:
        Player(kwargs['shuffle_folder'])


player = Player()
pool = Pool(1)


@app.route("/pause_unpause")
def pause_unpause():
    pool.apply(player.pause_unpause)


@app.route("/skip")
def skip():
    pool.apply(player.skip)


@app.route("/previous")
def previous():
    pool.apply(player.previous)


@app.route("/volume_up")
def volume_up():
    pool.apply(player.volume_up)


@app.route("/volume_down")
def volume_down():
    pool.apply(player.volume_down)
