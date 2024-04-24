import atexit
import logging.config
import logging.handlers


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
            "filename": "log.log",
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
# zrobić normalnie i tyle