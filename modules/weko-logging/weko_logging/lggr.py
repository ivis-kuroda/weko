from flask import current_app

import logging

class CustomLogFilter(logging.Filter):
    def filter(self, record):
        try:
            from flask_login import current_user
            from weko_accounts.utils import get_remote_addr
        except ImportError:
            record.user_id = None
            record.ip_address = None
        else:
            record.user_id = current_user.id
            record.ip_address = get_remote_addr()
        return True


def weko_logger(msg):
    format = '[%(asctime)s,%(msecs)03d][%(levelname)s] weko - (id %(user_id)s, ip %(ip_address)s) - %(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]'
    # format = '[%(asctime)s,%(msecs)03d][%(levelname)s] weko - %(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]'
    datefmt = '%Y-%m-%d %H:%M:%S'

    formatter = logging.Formatter(fmt=format, datefmt=datefmt)
    for handler in current_app.logger.handlers:
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
    # current_app.logger.addFilter(CustomLogFilter())

    current_app.logger.error(msg)
