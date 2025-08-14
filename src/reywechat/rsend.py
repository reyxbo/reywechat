# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-03 22:53:18
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Send methods.
"""


from __future__ import annotations
from typing import Any, Literal, overload
from collections.abc import Callable
from enum import IntEnum
from functools import wraps as functools_wraps
from queue import Queue
from re import escape as re_escape
from reykit.rbase import throw, catch_exc
from reykit.ros import File
from reykit.rre import sub
from reykit.rtime import sleep
from reykit.rwrap import wrap_thread, wrap_exc

from .rbase import BaseWeChat, WeChatTriggerContinueExit, WeChatTriggerBreakExit
from .rwechat import WeChat


__all__ = (
    'WeChatSendEnum',
    'WeChatSendParameter',
    'WeChatSender'
)


class WeChatSendEnum(BaseWeChat, IntEnum):
    """
    WeChat send enumeration type.

    Attributes
    ----------
    SEND_TEXT : Send text message.
    SEND_TEXT_AT : Send text message with @.
    SEND_FILE : Send file message.
    SEND_IMAGE : Send image message.
    SEND_EMOTION : Send emotion message.
    SEND_PAT : Send pat message.
    SEND_PUBLIC : Send public account message.
    SEND_FORWARD : Forward message.
    """

    SEND_TEXT = 0
    SEND_TEXT_AT = 1
    SEND_FILE = 2
    SEND_IMAGE = 3
    SEND_EMOTION = 4
    SEND_PAT = 5
    SEND_PUBLIC = 6
    SEND_FORWARD = 7


class WeChatSendParameter(BaseWeChat):
    """
    WeChat send parameters type.
    """

    SendEnum = WeChatSendEnum


    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_TEXT],
        receive_id: str,
        send_id: int,
        *,
        text: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_TEXT_AT],
        receive_id: str,
        send_id: int,
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_FILE, WeChatSendEnum.SEND_IMAGE, WeChatSendEnum.SEND_EMOTION],
        receive_id: str,
        send_id: int,
        *,
        file_path: str,
        file_name: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_PAT],
        receive_id: str,
        send_id: int,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_PUBLIC],
        receive_id: str,
        send_id: int,
        *,
        page_url: str,
        title: str,
        text: str | None = None,
        image_url: str | None = None,
        public_name: str | None = None,
        public_id: str | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendEnum.SEND_FORWARD],
        receive_id: str,
        send_id: int,
        *,
        message_id: str
    ) -> None: ...

    def __init__(
        self,
        sender: WeChatSender,
        send_type: WeChatSendEnum,
        receive_id: str,
        send_id: int,
        **params: Any
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        sender : `WeChatSender` instance.
        send_type : Send type.
            - `Literal[WeChatSendEnum.SEND_TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendEnum.SEND_TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendEnum.SEND_FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendEnum.SEND_IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendEnum.SEND_EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendEnum.SEND_PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendEnum.SEND_PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendEnum.SEND_FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        send_id : Send ID of database.
        params : Send parameters.
        """

        # Set attribute.
        self.sender = sender
        self.send_type = send_type
        self.receive_id = receive_id
        self.send_id = send_id
        self.params = params
        self.exc_reports: list[str] = []
        self.sent: bool = False


class WeChatSender(BaseWeChat):
    """
    WeChat sender type.

    Attribute
    ---------
    WeChatSendEnum : Send type enumeration.
    """

    SendEnum = WeChatSendEnum


    def __init__(self, wechat: WeChat) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChatClient` instance.
        """

        # Set attribute.
        self.wechat = wechat
        self.queue: Queue[WeChatSendParameter] = Queue()
        self.handlers: list[Callable[[WeChatSendParameter], Any]] = []
        self.started: bool | None = False

        # Start.
        self.__start_sender()


    @wrap_thread
    def __start_sender(self) -> None:
        """
        Start sender, that will sequentially send message in the send queue.
        """


        # Define.
        def handle_handler_exception(exc_report, *_) -> None:
            """
            Handle Handler exception.

            Parameters
            ----------
            exc_report : Exception report text.
            """

            # Save.
            sendparam.exc_reports.append(exc_report)


        # Loop.
        while True:
            match self.started:

                ## Stop.
                case False:
                    sleep(0.1)
                    continue

                ## End.
                case None:
                    break

            sendparam = self.queue.get()

            ## Handler.
            for handler in self.handlers:
                handler = wrap_exc(handler, handler=handle_handler_exception)
                handler(sendparam)

            ## Send.
            try:
                self.__send(sendparam)

            ## Exception.
            except:

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                sendparam.exc_reports.append(exc_report)

            sendparam.sent = True

            ## Handler.
            for handler in self.handlers:
                handler = wrap_exc(handler, handler=handle_handler_exception)
                handler(sendparam)

            ## Log.
            self.wechat.log.log_send(sendparam)


    def __send(
        self,
        sendparam: WeChatSendParameter
    ) -> None:
        """
        Send message.

        Parameters
        ----------
        sendparam : `WeChatSendParameter` instance.
        """

        # Send.
        match sendparam.send_type:

            ## Text.
            case WeChatSendEnum.SEND_TEXT:
                self.wechat.client.send_text(
                    sendparam.receive_id,
                    sendparam.params['text']
                )

            ## Text with '@'.
            case WeChatSendEnum.SEND_TEXT_AT:
                self.wechat.client.send_text_at(
                    sendparam.receive_id,
                    sendparam.params['user_id'],
                    sendparam.params['text']
                )

            ## File.
            case WeChatSendEnum.SEND_FILE:
                self.wechat.client.send_file(
                    sendparam.receive_id,
                    sendparam.params['file_path']
                )

            ## Image.
            case WeChatSendEnum.SEND_IMAGE:
                self.wechat.client.send_image(
                    sendparam.receive_id,
                    sendparam.params['file_path']
                )

            ## Emotion.
            case WeChatSendEnum.SEND_EMOTION:
                self.wechat.client.send_emotion(
                    sendparam.receive_id,
                    sendparam.params['file_path']
                )

            ## Pat.
            case WeChatSendEnum.SEND_PAT:
                self.wechat.client.send_pat(
                    sendparam.receive_id,
                    sendparam.params['user_id']
                )

            ## Public account.
            case WeChatSendEnum.SEND_PUBLIC:
                self.wechat.client.send_public(
                    sendparam.receive_id,
                    sendparam.params['page_url'],
                    sendparam.params['title'],
                    sendparam.params['text'],
                    sendparam.params['image_url'],
                    sendparam.params['public_name'],
                    sendparam.params['public_id']
                )

            ## Forward.
            case WeChatSendEnum.SEND_FORWARD:
                self.wechat.client.send_forward(
                    sendparam.receive_id,
                    sendparam.params['message_id']
                )

            ## Throw exception.
            case send_type:
                throw(ValueError, send_type)


    def add_handler(
        self,
        handler: Callable[[WeChatSendParameter], Any]
    ) -> None:
        """
        Add send handler function.

        Parameters
        ----------
        handler : Handler method, input parameter is `WeChatSendParameter` instance.
        """

        # Add.
        self.handlers.append(handler)


    def add_at(
        self,
        text: str,
        room_id: str
    ) -> str:
        """
        Based on the user name in the text, automatic add `@` format.

        Parameters
        ----------
        text : Text.
        room_id : Chat room ID.

        Returns
        -------
        Added text.
        """

        # Get parameter.
        member_dict = self.wechat.client.get_room_member_dict(room_id)
        login_id = self.wechat.client.login_info['id']
        if login_id in member_dict:
            del member_dict[login_id]

        # Add.
        names = [
            re_escape(name)
            for name in member_dict.values()
            if len(name) != 1
        ]
        pattern = '(?<!@)(%s) *' % '|'.join(names)
        replace = lambda match: '@%s ' % match[1]
        text_at = sub(pattern, text, replace)

        return text_at


    def wrap_try_send(
        self,
        receive_id: str | list[str],
        func: Callable
    ) -> Callable:
        """
        Decorator, send exception information.

        Parameters
        ----------
        receive_id : Receive user ID or chat room ID.
            - `str`: An ID.
            - `list[str]`: Multiple ID.
        func : Function.

        Returns
        -------
        Decorated function.
        """

        # Handle parameter.
        if type(receive_id) == str:
            receive_ids = [receive_id]
        else:
            receive_ids = receive_id

        # Define.
        @functools_wraps(func)
        def wrap(
            *arg: Any,
            **kwargs: Any
        ) -> Any:
            """
            Decorate.

            Parameters
            ----------
            args : Position arguments of decorated function.
            kwargs : Keyword arguments of decorated function.

            Returns
            -------
            Function execution result.
            """

            # Execute.
            try:
                result = func(
                    *arg,
                    **kwargs
                )
            except:
                *_, exc_instance, _ = catch_exc()

                # Report.
                if not isinstance(
                    exc_instance,
                    (WeChatTriggerContinueExit, WeChatTriggerBreakExit)
                ):
                    text = '\n'.join(
                        [
                            str(arg)
                            for arg in exc_instance.args
                        ]
                    )
                    for receive_id in receive_ids:
                        self.send(
                            WeChatSendEnum.SEND_TEXT,
                            receive_id,
                            text=text
                        )

                # Throw exception.
                raise

            return result


        return wrap


    def start(self) -> None:
        """
        Start sender.
        """

        # Start.
        self.started = True

        # Report.
        print('Start sender.')


    def stop(self) -> None:
        """
        Stop sender.
        """

        # Stop.
        self.started = False

        # Report.
        print('Stop sender.')


    def end(self) -> None:
        """
        End sender.
        """

        # End.
        self.started = None

        # Report.
        print('End sender.')


    __del__ = end
