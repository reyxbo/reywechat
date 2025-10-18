# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : WeChat methods.
"""


from os import getcwd as os_getcwd
from reydb import Database
from reykit.rbase import block
from reyserver.rclient import ServerClient

from .rbase import WeChatBase


__all__ = (
    'WeChat',
)


class WeChat(WeChatBase):
    """
    WeChat type.

    Will start client API service with port `19088` and message callback service with port '19089'.

    Warnings, only applicable to WeChat clients with version `3.9.5.81`.

    Warnings, must close file automatic download.

    Warnings, the operating system version cannot be lower than `Windows 10 version 1709` or `Windows Server 2016 version 1709`.

    Warnings, need support “Microsoft Visual C++2015”.
    """


    def __init__(
        self,
        db: Database,
        sclient: ServerClient,
        max_receiver: int = 2,
        call_name: str | None = None,
        dir_log: str = 'log',
        dir_cache: str = 'cache'
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : Database. Note: must include database engine of `wechat` name.
        sclient : Server client.
        max_receiver : Maximum number of receivers.
        call_name : Trigger call name.
            - `None`: Use account nickname.
        dir_log : Log directory.
        dir_cache : Cache directory.
        """

        # Import.
        from .rcache import WeChatCache
        from .rclient import WeChatClient
        from .rdb import WeChatDatabase
        from .rlog import WeChatLog
        from .rreceive import WechatReceiver
        from .rsend import WeChatSendTypeEnum, WeChatSendStatusEnum, WeChatSender

        # Build.

        ## Instance.
        self.client = WeChatClient(self)
        self.cache = WeChatCache(self, dir_cache)
        self.error = WeChatLog(self, dir_log)
        self.receiver = WechatReceiver(self, max_receiver, call_name)
        self.trigger = self.receiver.trigger
        self.sender = WeChatSender(self)
        self.db = WeChatDatabase(self, db, sclient)

        ## Client.
        self.client_version = self.client.client_version
        self.client_version_int = self.client.client_version_int
        self.client_version_simulate = self.client.client_version_simulate
        self.client_version_simulate_int = self.client.client_version_simulate_int
        self.client_api_port = self.client.client_api_port
        self.message_callback_port = self.client.message_callback_port

        ## Receive.
        self.receive_add_handler = self.receiver.add_handler
        self.receive_start = self.receiver.start
        self.receive_stop = self.receiver.stop

        ## Trigger.
        self.trigger_add_rule = self.trigger.add_rule

        ## Send.
        self.SendTypeEnum = WeChatSendTypeEnum
        self.SendstatusEnum = WeChatSendStatusEnum
        self.send_add_handler = self.sender.add_handler
        self.send = self.sender.send
        self.send_start = self.sender.start
        self.send_stop = self.sender.stop
        self.wrap_try_send = self.sender.wrap_try_send

        ## Database.
        self.database_build = self.db.build_db


    def start(self) -> None:
        """
        Start all methods.
        """

        # Start.
        self.receive_start()
        self.send_start()


    def keep(self) -> None:
        """
        Blocking the main thread to keep running.
        """

        # Report.
        print('Keep runing.')

        # Blocking.
        block()


    @property
    def print_colour(self) -> bool:
        """
        Whether print colour.

        Returns
        -------
        Result.
        """

        # Parameter.
        result = self.error.rrlog.print_colour

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
        self.error.rrlog.print_colour = value
        self.error.rrlog_print.print_colour = value
        self.error.rrlog_file.print_colour = value
