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

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.fmt = fmt

    def format(self, record):
        color_code = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
        formatter = logging.Formatter(
            color_code + self.fmt + self.RESET_CODE, self.datefmt)
        return formatter.format(record)

class WekoLoggingST(WekoLoggingBase):

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The flask application.
        """
        if app:
            self.init_app(app)


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
            "[%(asctime)s][%(levelname)s][weko/%(module)s] - %(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]"
        )

        handler = logging.StreamHandler()
        # handler.
        # handler.set_name("weko-logging")
        # handler.setFormatter(formatter)

        # app.logger.info(len(app.logger.handlers))

        # if not any(h.get_name() == "weko-logging" for h in app.logger.handlers):
        #     # ハンドラーを追加
        #     app.logger.addHandler(handler)
        #     app.logger.info(app.config['WEKO_LOGGING_ST_MESSAGE_DICTIONARY']['0003'])

        for handler in app.logger.handlers:
            handler.setLevel(logging.INFO)
            handler.set_name("weko-logging")
            handler.setFormatter(formatter)
            app.logger.info(app.config['WEKO_LOGGING_ST_MESSAGE_DICTIONARY']['0004'])

        # app.logger.info(len(app.logger.handlers))
