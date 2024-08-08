import logging
from . import config
from .ext import WekoLoggingBase

class WekoLoggingSt(WekoLoggingBase):
    """WEKO-Logging extension. Logging Stream handler."""

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.install_handler(app)
        app.extensions["weko-logging-st"] = self

    def install_handler(self, app):
        app.logger.setLevel(logging.INFO)

        format = '[%(asctime)s,%(msecs)03d][%(levelname)s] weko - (id %(user_id)s, ip %(ip_address)s) - %(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]'
        datefmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(fmt=format, datefmt=datefmt)

        for handler in app.logger.handlers:
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)

        app.logger.addFilter(CustomLogFilter())

class CustomLogFilter(logging.Filter):
    def filter(self, record):
        try:
            from flask_login import current_user
            from weko_accounts.utils import get_remote_addr
            record.user_id = current_user.id
        except AttributeError:
            record.user_id = None
        finally:
            record.ip_address = get_remote_addr()

        return True
