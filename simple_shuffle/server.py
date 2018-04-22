from flask import Flask
from play_audio_file import Player
from click import click as cli
from os.path import join as getpath
from os import environ
from os import sep as root
app = Flask(__name__)


@cli.command("shuffle-server")
@cli.argument("shuffle_folder", required=False)
def main(*args, **kwargs):
    """The simple_shuffle script shuffles a folder of flac and ogg files.

    It does a true shuffle of all of the songs in the folder, without repeats,
    unless you've got duplicates. Specify the folder to be shuffled on the
    command line just after the name. By default it shuffles /home/$USER/Music.
    """
    if kwargs['shuffle_folder'] is None:
        Player(getpath(root, 'home', environ['USER'], 'Music'))
    else:
        Player(kwargs['shuffle_folder'])


player = Player()


@app.route("/pause")
def fname(arg):
    pass
