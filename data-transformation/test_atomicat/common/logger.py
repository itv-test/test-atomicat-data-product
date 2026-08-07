from logging import config as logging_config


config_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(filename)s] [%(levelname)s]: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"level": "NOTSET", "handlers": ["console"]},
}


def configure_logger():
    logging_config.dictConfig(config_dict)
