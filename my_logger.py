import atexit
import logging.config
import logging.handlers
import os

dir_log = f"{os.getcwd()}/log.log"

my_config = {
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

my_logger = logging.getLogger("my_logger")
logging.config.dictConfig(my_config)
queue_handler = logging.getHandlerByName("queue_handler")
if queue_handler:
    queue_handler.listener.start()
    atexit.register(queue_handler.listener.stop())


def log_it(func):
    def wrapper(*args, **kwargs):
        try:
            f = func(*args, **kwargs)
            my_logger.info(f"{f.__name__}, {args}, {kwargs}, - OK")
        except Exception as e:
            my_logger.exception(f"{f.__name__}, {args}, {kwargs}, {e}")
        return f
    return wrapper


def log_it_methods_decorator(decorator):
    def decorate(cls):
        for attr in cls.__dict__: # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


if __name__ == "__main__":
    pass
