import atexit
import traceback
import logging.config
import logging.handlers
import os
from tkinter import messagebox
from base_classes import MyErrorWindow

dir_log = f"{os.getcwd()}/log.log"

my_config_python_3_12= {
    "version": 1,
    "disable_existing_loggers": False,
    # "filters": {},
    "formatters": {
        "basic": {
            "format": "%s(levelname)s; %(module)s; %(lineno)d; %(asctime)s; %(message) *** ",
            "datefmt": "%Y-%m-%dT%H:%M:%Sz"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "basic",
            "filename": dir_log,
            "maxBytes": 10000000,
            "backupCount": 3
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
                "file"
            ],
            "respect_handler_level": True
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "queue_handler"
            ]
        }
    }
}

my_config_python_3_11 = {
    "version": 1,
    "disable_existing_loggers": False,
    # "filters": {},
    "formatters": {
        "basic": {
            "format": "%(levelname)s; %(module)s; %(lineno)d; %(asctime)s; %(message)s *** ",
            "datefmt": "%Y-%m-%dT%H:%M:%Sz"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "basic",
            "filename": dir_log,
            "maxBytes": 10000000,
            "backupCount": 3
        },
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "file"
            ]
        }
    }
}

my_logger = logging.getLogger("my_logger")
logging.config.dictConfig(my_config_python_3_11)
queue_handler = logging.getHandlerByName("queue_handler")  # add if my_config_python_3_12
# if queue_handler:
#     queue_handler.listener.start()
#     atexit.register(queue_handler.listener.stop())


def log_exception(func_or_class):
    def wrapper(*args, **kwargs):
        try:
            return func_or_class(*args, **kwargs)
        except Exception as e:
            my_logger.exception(e)
            MyErrorWindow(e)
    return wrapper


def log_exception_decorator(decorator):
    def decorate(cls):
        for attr in cls.__dict__:  # there's probably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


if __name__ == "__main__":
    pass
