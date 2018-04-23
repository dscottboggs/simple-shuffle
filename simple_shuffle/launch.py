"""CLI and launcher for simple_shuffle."""
import click as cli
import os
from simple_shuffle.curses_client import CursesInterface


@cli.command("shuffle")
@cli.option("server_only")
@cli.argument("shuffle_folder", required=False)
def main(*args, **kwargs):
    """Simply shuffle your library. That's all.

    You can enable just the server backend wit the server_only option, and
    specify the folder to be shuffled. An ncurses display is enabled by
    default.
    """
    os.environ["SIMPLE_SHUFFLE_FOLDER"] = kwargs['shuffle_folder']\
        or os.path.join(
            os.environ['HOME'], "Music"
        )
    server_filename = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "server.py"
    )
    exe = "flask"
    os.spawnlpe(os.P_NOWAIT, exe, exe, "run", {
        "FLASK_APP":    server_filename,
        "LANG":         os.environ['LANG'],
        "LC_ALL":       os.environ["LC_ALL"],
        "USER":         os.environ["USER"]
    })
    if not kwargs['server_only']:
        CursesInterface()
