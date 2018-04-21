from setuptools import setup
from git.repo.base import Repo
from os.path import dirname, realpath

vcs = Repo(dirname(realpath(__file__)))
urls = [u for u in vcs.remote().urls]
if len(urls) < 1:
    raise NotImplementedError()
versionnum = len([c for c in vcs.iter_commits()])
print("Current version 0.0.%d" % versionnum)

setup(
    name="Simple Shuffle",
    version="0.0.%d" % versionnum,
    author="D. Scott Boggs",
    author_email="scott@tams.tech",
    description="Shuffles a folder of music. That is all.",
    license="GPLv3",
    keywords="music player shuffle curses ncurses minimal simple",
    url=urls[0],
    packages=["simple_shuffle"],
    install_requires=["pygame", "mutagen", "file-magic"],
    setup_requires=["gitpython"]
)
