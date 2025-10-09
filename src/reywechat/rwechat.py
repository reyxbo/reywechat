# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : WeChat methods.
"""


from typing import Literal
from os import getcwd as os_getcwd
from reydb import DatabaseEngine
from reykit.rbase import block

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
        db_engine: DatabaseEngine | dict[Literal['wechat', 'file'], DatabaseEngine] | None,
        max_receiver: int = 2,
        call_name: str | None = None,
        project_dir: str | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db_engine : Database engine.
            - `Database`, Set all `Database`: instances.
            - `dict`, Set each `Database`: instance, all item is required.
                `Key 'wechat'`: `Database` instance used in WeChat methods.
                `Key 'file'`: `Database` instance used in file methods.
        max_receiver : Maximum number of receivers.
        call_name : Trigger call name.
            - `None`: Use account nickname.
        project_dir: Project directory, will create sub folders.
            - `None`: Use working directory.
            - `str`: Use this directory.
        """

        # Import.
        from .rcache import WeChatCache
        from .rclient import WeChatClient
        from .rdb import WeChatDatabase
        from .rlog import WeChatLog
        from .rreceive import WechatReceiver
        from .rsend import WeChatSendTypeEnum, WeChatSendStatusEnum, WeChatSender

        # Set attribute.
        self.project_dir = project_dir or os_getcwd()

        ## Instance.
        self.client = WeChatClient(self)
        self.cache = WeChatCache(self)
        self.error = WeChatLog(self)
        self.receiver = WechatReceiver(self, max_receiver, call_name)
        self.trigger = self.receiver.trigger
        self.sender = WeChatSender(self)
        self.db = WeChatDatabase(self, db_engine)

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
