# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-09 21:47:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Schedule methods.
"""


from __future__ import annotations
from typing import Any, Literal
from collections.abc import Callable
from reykit.rschedule import Schedule

from .rbase import BaseWeChat
from .rsend import WeChatSendTypeEnum
from .rwechat import WeChat


class WeChatSchedule(BaseWeChat):
    """
    WeChat schedule type.
    """

    TypeEnum = WeChatSendTypeEnum


    def __init__(
        self,
        wechat: WeChat
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChatClient` instance.
        """

        # Set attribute.
        self.wechat = wechat
        self.rrschedule = Schedule()

        # Start.
        self.rrschedule.start()


    def add_task(
        self,
        trigger: Literal['date', 'interval', 'cron'],
        task: Callable[[WeChatSchedule], Any],
        **trigger_kwargs: Any
    ) -> None:
        """
        Add schedule send message task.

        Parameters
        ----------
        trigger : Trigger type.
        task : Function of task. The parameter is the `WeChatSchedule` instance.
        trigger_kwargs : Trigger keyword arguments.
        """

        # Handle parameter.
        args = (self,)

        # Add.
        self.rrschedule.add_task(
            task,
            trigger,
            args,
            **trigger_kwargs
        )


    def pause(self) -> None:
        """
        Pause scheduler.
        """

        # Pause.
        self.rrschedule.pause()


    def resume(self) -> None:
        """
        Resume scheduler.
        """

        # Pause.
        self.rrschedule.resume
