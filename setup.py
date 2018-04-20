from setuptools import setup
from git.repo.base import Repo
from os.path import dirname, realpath

vcs = Repo(dirname(realpath(__file__)))

help(vcs)
exit()

setup(
    name="Simple Shuffle",
    version="0.0.1",
    author="D. Scott Boggs",
    author_email="scott@tams.tech",
    description="Shuffles a folder of music. That is all.",
    license="GPLv3",
    keywords="music player shuffle curses ncurses minimal simple"
)
