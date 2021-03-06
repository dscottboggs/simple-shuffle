from setuptools import setup
from git.repo.base import Repo
from os.path import dirname, realpath, exists
import os

vcs = Repo(dirname(realpath(__file__)))
urls = [u for u in vcs.remote().urls]
if len(urls) < 1:
    raise NotImplementedError()
versionnum = (len([c for c in vcs.iter_commits()])
    - 116   # version 0.0.* had 115 revisions
    - 57    # version 0.1.* had 56 revisions
    - 71    # version 0.2.* had 70 revisions
)
versionstr = "0.3.%d" % versionnum
print("Current version %s" % versionstr)

logfile = os.path.join(
    os.sep,
    "var",
    "log",
    "simple_shuffle.log"
)

# HACK: This requires that the permissions be changed manually, needs to be
# fixed. How to determine the user executing a command as sudo?
if not exists(logfile):
    open(logfile, 'w').close()

setup(
    name="Simple Shuffle",
    version=versionstr,
    author="D. Scott Boggs",
    author_email="scott@tams.tech",
    description="Shuffles a folder of music. That is all.",
    license="GPLv3",
    keywords="music player shuffle curses ncurses minimal simple",
    url=urls[0],
    packages=["simple_shuffle"],
    install_requires=["pygame", "mutagen", "file-magic", "click", "blist"],
    setup_requires=["gitpython"]
)
