# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Extensions for weko-logging."""

import logging


class WekoLoggingBase(object):
    """WEKO-Logging extension for console."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The flask application.
        """
        if app:
            WekoLoggingBase.init_app(self, app)

    def init_app(self, app):
        """Initialize app.

        :param app: The flask application.
        """
        WekoLoggingBase.install_handler(self, app)

    def install_handler(self, app):
        """Install handler.

        :param app: The flask application.
        """
        app.logger.setLevel(logging.INFO)
        logging.IMPORTANT = 25
        logging.addLevelName(logging.IMPORTANT, "IMPORTANT")
        setattr(app.logger, 'important', lambda msg, *args, **kwargs: app.logger._log(logging.IMPORTANT, msg, args, **kwargs))

        format = '[%(asctime)s,%(msecs)03d][%(levelname)s] weko - (id %(user_id)s, ip %(ip_address)s) - %(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]'
        datefmt = '%Y-%m-%d %H:%M:%S'

        formatter = logging.Formatter(fmt=format, datefmt=datefmt)
        if app.logger.handlers:
            for handler in app.logger.handlers:
                handler.setLevel(logging.INFO)
                handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)

        app.logger.addFilter(WekoLoggingFilter())

        app.logger.info('!!!!!!!!!!!!!!!!!!!!WEKO-Logging initialized!!!!!!!!!!!!!!!!!')
        app.logger.error(f'WEKO-Logging has {len(app.logger.handlers)} handlers.')
        app.logger.important(f'app.logger {type(app.logger)} handlers.')


    @staticmethod
    def capture_pywarnings(handler):
        """
        Log python system warnings.

        :param handler: Log handler object.
        """
        logger = logging.getLogger("py.warnings")
        # Check for previously installed handlers.
        for h in logger.handlers:
            if isinstance(h, handler.__class__):
                return
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)


class WekoLoggingFilter(logging.Filter):
    def filter(self, record):
        from flask_login import current_user
        from weko_accounts.utils import get_remote_addr

        try:
            record.user_id = current_user.id
        except AttributeError:
            record.user_id = None
        finally:
            record.ip_address = get_remote_addr()

        return True

