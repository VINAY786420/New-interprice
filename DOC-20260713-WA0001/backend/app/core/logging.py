import logging
import sys

class SimpleLogger:
    def __init__(self, name: str = "sdv"):
        self._logger = logging.getLogger(name)

    def info(self, msg: str, **kwargs):
        if kwargs:
            self._logger.info(f"{msg} | " + " ".join(f"{k}={v}" for k, v in kwargs.items()))
        else:
            self._logger.info(msg)

    def error(self, msg: str, **kwargs):
        if kwargs:
            self._logger.error(f"{msg} | " + " ".join(f"{k}={v}" for k, v in kwargs.items()))
        else:
            self._logger.error(msg)

logger = SimpleLogger()


def configure_logging(level: str = "INFO"):
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
