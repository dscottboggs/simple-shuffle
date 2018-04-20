"""Configuration and logging for the project."""
from logging import getLogger, DEBUG
from logging.config import dictConfig


def get_logging_config():
    """Check for a loggercfg.json file, or return a default config."""
    curses_logfile = "/home/scott/Documents/code/simple-shuffle/curses_logfile.txt"
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


class Config():
    """Configuration and logging for the project."""
    dictConfig(get_logging_config())
    logger = getLogger()
