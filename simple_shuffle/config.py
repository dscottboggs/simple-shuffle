"""Configuration and logging for the project."""
from logging import getLogger, DEBUG
from logging.config import dictConfig
from os import sep as root
import os
import socket


def get_logging_config():
    """Check for a loggercfg.json file, or return a default config."""
    try:
        with open("loggercfg.json") as cfg:
            return cfg
    except FileNotFoundError:
        return {
            "version": 1,
            "formatters": {
                "brief": {
                    'format':
                        "%(levelname)s [%(asctime)s] %(filename)s@%(lineno)s:"
                        + " %(message)s"
                },
                "friendly": {
                    'format':
                        "In %(filename)s, at line %(lineno)s, a message was"
                        + " logged. Message follows:\n\t%(message)s\nThis"
                        + " message was logged by the function %(funcName)s,"
                        + " with\n%(levelname)s(%(levelno)s) severity,"
                        + " at %(asctime)s."
                }
            },
            "handlers": {
                "testhandler": {
                    "class": "logging.StreamHandler",
                    "formatter": "brief",
                    "level": DEBUG
                }
            },
            "root": {
                "handlers": ["testhandler"],
                "level": DEBUG
            }
        }

class Config:
    """Configuration and logging for the project."""
    dictConfig(get_logging_config())
    logger = getLogger()
    curses_logfile = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "curses_logfile.txt"
    )
    display_refresh_delay = 5
    sample_rate = 44100
    socket_file_location = os.path.join(root, "tmp", "simple_shuffle.sock")
