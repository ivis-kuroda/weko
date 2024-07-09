import logging

from . import config
from .ext import WekoLoggingBase


class LevelBasedFormatter(logging.Formatter):
    COLOR_CODES = {
        logging.DEBUG: "\033[37m",    # 白
        logging.INFO: "\033[36m",     # シアン
        logging.WARNING: "\033[33m",  # 黄色
        logging.ERROR: "\033[31m",    # 赤
        logging.CRITICAL: "\033[41m",  # 背景赤
    }
    RESET_CODE = "\033[0m"

    def __init__(self, fmt=None, datefmt=None, level_formats=None):
        super().__init__(fmt, datefmt)
        self.level_formats = level_formats if level_formats else {}

    def format(self, record):
        log_fmt = self.level_formats.get(record.levelno, self._fmt)
        color_code = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
        formatter = logging.Formatter(
            color_code + log_fmt + self.RESET_CODE, self.datefmt)
        return formatter.format(record)


class WekoLoggingST(WekoLoggingBase):
    def init_app(self, app):
        """
            Flask application initialization.

            :param app: The flask application.
            """
        self.init_config(app)
        app.logger.info(
            app.config['WEKO_LOGGING_ST_MESSAGE_DICTIONARY']['0002'])

        self.install_handler(app)
        app.extensions["weko-logging-st"] = self

    def init_config(self, app):
        for k in dir(config):
            if k.startswith("WEKO_LOGGING_ST"):
                app.config.setdefault(k, getattr(config, k))

    def install_handler(self, app):
        app.logger.setLevel(logging.INFO)

        formatter = LevelBasedFormatter(
            level_formats={
                logging.DEBUG: "[%(asctime)s][%(levelname)s/weko]  - %(message)s [in %(filename)s]",
                logging.INFO: "[%(asctime)s][%(levelname)s/weko] - %(message)s [in %(filename)s]",
                logging.WARN: "[%(asctime)s][%(levelname)s/weko]  - %(message)s [in %(pathname)s:%(lineno)d]",
                logging.ERROR: "[%(asctime)s][%(levelname)s/weko] - %(message)s [in %(pathname)s:%(lineno)d]"
            }
        )

        # handler= logging.StreamHandler()
        # handler.setFormatter(formatter)
        # app.logger.addHandler(handler)

        for handler in app.logger.handlers:
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)

        app.logger.info(
            app.config['WEKO_LOGGING_ST_MESSAGE_DICTIONARY']['0003'])
