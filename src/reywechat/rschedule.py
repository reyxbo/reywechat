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
from reykit.rschedule import RSchedule as RRSchedule
from reykit.rtype import RBase

from .rsend import SendType
from .rwechat import RWeChat


class RSchedule(RBase):
    """
    Rey's `schedule` type.
    """


    def __init__(
        self,
        rwechat: RWeChat
    ) -> None:
        """
        Build `schedule` instance attributes.

        Parameters
        ----------
        rwechat : `RClient` instance.
        """

        # Set attribute.
        self.rwechat = rwechat
        self.rrschedule = RRSchedule()

        # Start.
        self.rrschedule.start()


    def send(
        self,
        trigger: Literal['date', 'interval', 'cron'],
        trigger_kwargs: dict,
        send_type: SendType,
        receive_id: str,
        **params: Callable[[], Any] | Any
    ) -> None:
        """
        Schedule send message.

        Parameters
        ----------
        trigger : Trigger type.
        trigger_kwargs : Trigger keyword arguments.
        send_type : Send type.
            - `Literal[SendType.SEND_TEXT]`: Send text message, use `RClient.send_text`: method.
            - `Literal[SendType.SEND_TEXT_AT]`: Send text message with `@`, use `RClient.send_text_at`: method.
            - `Literal[SendType.SEND_FILE]`: Send file message, use `RClient.send_file`: method.
            - `Literal[SendType.SEND_IMAGE]`: Send image message, use `RClient.send_image`: method.
            - `Literal[SendType.SEND_EMOTION]`: Send emotion message, use `RClient.send_emotion`: method.
            - `Literal[SendType.SEND_PAT]`: Send pat message, use `RClient.send_pat`: method.
            - `Literal[SendType.SEND_PUBLIC]`: Send public account message, use `RClient.send_public`: method.
            - `Literal[SendType.SEND_FORWARD]`: Forward message, use `RClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        params : Send parameters.
            - `Callable`: Use execute return value.
            - `Any`: Use this value.
        """

        # Get parameter.
        kwargs = {
            'send_type': send_type,
            'receive_id': receive_id,
            **params
        }

        # Add.
        self.rrschedule.add_task(
            self.rwechat.rsend.send,
            trigger,
            kwargs=kwargs,
            **trigger_kwargs
        )


    def add(
        self,
        trigger: Literal['date', 'interval', 'cron'],
        task: Callable[[RSchedule], Any],
        **trigger_kwargs: Any
    ) -> None:
        """
        Add schedule send message task.

        Parameters
        ----------
        trigger : Trigger type.
        task : Function of task. The parameter is the `RSchedule` instance.
        trigger_kwargs : Trigger keyword arguments.
        """

        # Get parameter.
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
