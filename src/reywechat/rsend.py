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
from reykit.rre import sub
from reykit.rtime import sleep
from reykit.rwrap import wrap_thread, wrap_exc

from .rbase import BaseWeChat, WeChatTriggerContinueExit, WeChatTriggerBreakExit
from .rwechat import WeChat


__all__ = (
    'WeChatSendTypeEnum',
    'WeChatSendParameter',
    'WeChatSender'
)


class WeChatSendTypeEnum(BaseWeChat, IntEnum):
    """
    WeChat send type enumeration type.

    Attributes
    ----------
    TEXT : Send text message.
    TEXT_AT : Send text message with @.
    FILE : Send file message.
    IMAGE : Send image message.
    EMOTION : Send emotion message.
    PAT : Send pat message.
    PUBLIC : Send public account message.
    FORWARD : Forward message.
    """

    TEXT = 0
    TEXT_AT = 1
    FILE = 2
    IMAGE = 3
    EMOTION = 4
    PAT = 5
    PUBLIC = 6
    FORWARD = 7


class WeChatSendStatusEnum(BaseWeChat, IntEnum):
    """
    WeChat send status enumeration type.

    Attributes
    ----------
    INIT : After initialization, before inserting into database queue.
    WAIT : After get from database queue, before sending.
    SENT : After sending.
    """

    INIT = 0
    WAIT = 1
    SENT = 2


class WeChatSendParameter(BaseWeChat):
    """
    WeChat send parameters type.
    """

    TypeEnum = WeChatSendTypeEnum
    StatusEnum = WeChatSendStatusEnum


    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendTypeEnum.TEXT],
        receive_id: str,
        send_id: int | None = None,
        *,
        text: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendTypeEnum.TEXT_AT],
        receive_id: str,
        send_id: int | None = None,
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendTypeEnum.FILE, WeChatSendTypeEnum.IMAGE, WeChatSendTypeEnum.EMOTION],
        receive_id: str,
        send_id: int | None = None,
        *,
        file_path: str,
        file_name: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendTypeEnum.PAT],
        receive_id: str,
        send_id: int | None = None,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        sender: WeChatSender,
        send_type: Literal[WeChatSendTypeEnum.PUBLIC],
        receive_id: str,
        send_id: int | None = None,
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
        send_type: Literal[WeChatSendTypeEnum.FORWARD],
        receive_id: str,
        send_id: int | None = None,
        *,
        message_id: str
    ) -> None: ...

    def __init__(
        self,
        sender: WeChatSender,
        send_type: WeChatSendTypeEnum,
        receive_id: str,
        send_id: int | None = None,
        **params: Any
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        sender : `WeChatSender` instance.
        send_type : Send type.
            - `Literal[WeChatSendTypeEnum.TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendTypeEnum.TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendTypeEnum.FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendTypeEnum.IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendTypeEnum.EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendTypeEnum.PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendTypeEnum.PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendTypeEnum.FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        send_id : Send ID of database.
            - `None`: Not inserted into database.
        params : Send parameters.
        """

        # Set attribute.
        self.sender = sender
        self.send_type = send_type
        self.receive_id = receive_id
        self.send_id = send_id
        self.params = params
        self.exc_reports: list[str] = []
        self.status: WeChatSendStatusEnum


class WeChatSender(BaseWeChat):
    """
    WeChat sender type.

    Attribute
    ---------
    WeChatSendTypeEnum : Send type enumeration.
    """

    TypeEnum = WeChatSendTypeEnum


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

            send_param = self.queue.get()
            handle_handler_exception = lambda exc_report, *_: send_param.exc_reports.append(exc_report)

            ## Handler.
            for handler in self.handlers:
                handler = wrap_exc(handler, handler=handle_handler_exception)
                handler(send_param)

            ## Send.
            try:
                self.__send(send_param)

            ## Exception.
            except:

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                send_param.exc_reports.append(exc_report)

            send_param.status = send_param.StatusEnum.SENT

            ## Handler.
            for handler in self.handlers:
                handler = wrap_exc(handler, handler=handle_handler_exception)
                handler(send_param)

            ## Log.
            self.wechat.log.log_send(send_param)


    def __send(
        self,
        send_param: WeChatSendParameter
    ) -> None:
        """
        Send message.

        Parameters
        ----------
        send_param : `WeChatSendParameter` instance.
        """

        # Send.
        match send_param.send_type:

            ## Text.
            case WeChatSendTypeEnum.TEXT:
                self.wechat.client.send_text(
                    send_param.receive_id,
                    send_param.params['text']
                )

            ## Text with '@'.
            case WeChatSendTypeEnum.TEXT_AT:
                self.wechat.client.send_text_at(
                    send_param.receive_id,
                    send_param.params['user_id'],
                    send_param.params['text']
                )

            ## File.
            case WeChatSendTypeEnum.FILE:
                self.wechat.client.send_file(
                    send_param.receive_id,
                    send_param.params['file_path']
                )

            ## Image.
            case WeChatSendTypeEnum.IMAGE:
                self.wechat.client.send_image(
                    send_param.receive_id,
                    send_param.params['file_path']
                )

            ## Emotion.
            case WeChatSendTypeEnum.EMOTION:
                self.wechat.client.send_emotion(
                    send_param.receive_id,
                    send_param.params['file_path']
                )

            ## Pat.
            case WeChatSendTypeEnum.PAT:
                self.wechat.client.send_pat(
                    send_param.receive_id,
                    send_param.params['user_id']
                )

            ## Public account.
            case WeChatSendTypeEnum.PUBLIC:
                self.wechat.client.send_public(
                    send_param.receive_id,
                    send_param.params['page_url'],
                    send_param.params['title'],
                    send_param.params['text'],
                    send_param.params['image_url'],
                    send_param.params['public_name'],
                    send_param.params['public_id']
                )

            ## Forward.
            case WeChatSendTypeEnum.FORWARD:
                self.wechat.client.send_forward(
                    send_param.receive_id,
                    send_param.params['message_id']
                )

            ## Throw exception.
            case send_type:
                throw(ValueError, send_type)


    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.TEXT],
        receive_id: str,
        *,
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.TEXT_AT],
        receive_id: str,
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.FILE, WeChatSendTypeEnum.IMAGE, WeChatSendTypeEnum.EMOTION],
        receive_id: str,
        *,
        file_path: str,
        file_name: str | None = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.PAT],
        receive_id: str,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.PUBLIC],
        receive_id: str,
        *,
        page_url: str,
        title: str,
        text: str | None = None,
        image_url: str | None = None,
        public_name: str | None = None,
        public_id: str | None = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendTypeEnum.FORWARD],
        receive_id: str,
        *,
        message_id: str
    ) -> None: ...

    def send(
        self,
        send_type: WeChatSendTypeEnum,
        receive_id: str | None = None,
        **params: Any
    ) -> None:
        """
        Insert into `wechat.message_send` table of database, wait send.

        Parameters
        ----------
        send_type : Send type.
            - `Literal[WeChatSendTypeEnum.TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendTypeEnum.TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendTypeEnum.FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendTypeEnum.IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendTypeEnum.EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendTypeEnum.PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendTypeEnum.PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendTypeEnum.FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        params : Send parameters.
        """

        # Handle parameter.
        send_param = WeChatSendParameter(
            self,
            send_type,
            receive_id,
            **params
        )
        send_param.status = send_param.StatusEnum.INIT
        handle_handler_exception = lambda exc_report, *_: send_param.exc_reports.append(exc_report)

        # Handler.
        for handler in self.handlers:
            handler = wrap_exc(handler, handler=handle_handler_exception)
            handler(send_param)

        # Insert.
        self.wechat.database._insert_send(send_param)


    def add_handler(
        self,
        handler: Callable[[WeChatSendParameter], Any]
    ) -> None:
        """
        Add send handler function.
        Call at the after initialization, before inserting into database queue.
        Call at the after get from database queue, before sending.
        Call at the after sending.
        Can be use `WeChatSendParameter.status` judge status.

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

        # Handle parameter.
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
                            WeChatSendTypeEnum.TEXT,
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
