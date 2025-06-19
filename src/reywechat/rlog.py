# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-19 11:33:45
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Log methods.
"""


from os.path import join as os_join
from reykit.rlog import RLog as RRLog

from .rreceive import RMessage
from .rsend import RSendParam
from .rwechat import RWeChat


__all__ = (
    'RLog',
)


class RLog(object):
    """
    Rey's `log` type.
    """


    def __init__(
        self,
        rwechat: RWeChat
    ) -> None:
        """
        Build `log` attributes.

        Parameters
        ----------
        rwechat : `RClient` instance.
        """

        # Set attribute.
        self.rwechat = rwechat

        # Logger.
        self.rrlog = RRLog('WeChat')
        self.rrlog_print = RRLog('WeChat.WeChatPrint')
        self.rrlog_file = RRLog('WeChat.WeChatFile')

        # Add handler.
        self._add_handler()


    def _add_handler(self) -> None:
        """
        Add log handler.
        """

        # Set parameter.
        format_ = (
            '%(format_time)s | '
            '%(format_levelname)s | '
            '%(format_message_)s'
        )

        # Add.

        ## Reset.
        self.rrlog_print.clear_handler()

        ## Add handler print.
        self.rrlog_print.add_print(format_=format_)

        ## Add handler file.
        file_path = os_join(self.rwechat.dir_log, 'WeChat')
        self.rrlog_file.add_file(
            file_path,
            time='m',
            format_=format_
        )


    @property
    def print_colour(self) -> bool:
        """
        Whether print colour.

        Returns
        -------
        Result.
        """

        # Get parameter.
        result = self.rrlog.print_colour

        return result


    @print_colour.setter
    def print_colour(self, value: bool) -> None:
        """
        Set whether print colour.

        Parameters
        ----------
        value : Set value.
        """

        # Set.
        self.rrlog.print_colour = value
        self.rrlog_print.print_colour = value
        self.rrlog_file.print_colour = value


    def log_receive(
        self,
        rmessage: RMessage
    ) -> None:
        """
        Log receive message.

        Parameters
        ----------
        rmessage : `RMessage` instance.
        """

        # Generate record.
        if rmessage.room is None:
            message_object = rmessage.user
        else:
            message_object = rmessage.room
        content_print = 'RECEIVE | %-20s' % message_object
        content_file = 'RECEIVE | %s' % rmessage.params
        if rmessage.exc_reports == []:
            level = self.rrlog.INFO
        else:
            level = self.rrlog.ERROR
            exc_report = '\n'.join(rmessage.exc_reports)
            content_print = '%s\n%s' % (content_print, exc_report)
            content_file = '%s\n%s' % (content_file, exc_report)

        ## Add color.
        if self.rrlog.print_colour:
            color_code = self.rrlog.get_level_color_ansi(level)
            content_print = f'{color_code}{content_print}\033[0m'

        # Log.
        self.rrlog_print.log(
            format_message_=content_print,
            level=level
        )
        self.rrlog_file.log(
            format_message_=content_file,
            level=level
        )


    def log_send(
        self,
        rsparam: RSendParam
    ) -> None:
        """
        Log send message.

        Parameters
        ----------
        rsparam : `RSendParams` instance.
        """

        # Generate record.
        content_print = 'SEND    | %-20s' % rsparam.receive_id
        content_file = 'SEND    | %s' % {
            'receive_id': rsparam.receive_id,
            **rsparam.params
        }
        if rsparam.exc_reports == []:
            level = self.rrlog.INFO
        else:
            level = self.rrlog.ERROR
            exc_report = '\n'.join(rsparam.exc_reports)
            content_print = '%s\n%s' % (content_print, exc_report)
            content_file = '%s\n%s' % (content_file, exc_report)

        ## Add color.
        if self.rrlog.print_colour:
            color_code = self.rrlog.get_level_color_ansi(level)
            content_print = f'{color_code}{content_print}\033[0m'

        # Log.
        self.rrlog_print.log(
            format_message_=content_print,
            level=level
        )
        self.rrlog_file.log(
            format_message_=content_file,
            level=level
        )
