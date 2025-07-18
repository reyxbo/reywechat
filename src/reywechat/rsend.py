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
from enum import Enum
from functools import wraps as functools_wraps
from os.path import join as os_join
from queue import Queue
from re import escape as re_escape
from reykit.rbase import throw, catch_exc
from reykit.rnet import compute_stream_time
from reykit.ros import File
from reykit.rrand import randn
from reykit.rre import sub
from reykit.rtime import sleep
from reykit.rwrap import wrap_thread, wrap_exc

from .rbase import BaseWeChat, WeChatTriggerContinueExit, WeChatTriggerBreakExit
from .rwechat import WeChat


__all__ = (
    'WeChatSendType',
    'WeChatSendParameter',
    'WeChatSend'
)


class WeChatSendType(BaseWeChat, Enum):
    """
    WeChat send type enumeration.

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


    def __init__(
        self,
        rsend: WeChatSend,
        send_type: WeChatSendType,
        receive_id: str,
        params: dict,
        send_id: int | None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rsend : `WeChatSend` instance.
        send_type : Send type.
            - `Literal[WeChatSendType.SEND_TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendType.SEND_TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendType.SEND_FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendType.SEND_IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendType.SEND_EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendType.SEND_PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendType.SEND_PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendType.SEND_FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        params : Send parameters.
        send_id : Send ID of database.
        """

        # Set attribute.
        self.rsend = rsend
        self.send_type = send_type
        self.receive_id = receive_id
        self.params = params
        self.send_id = send_id
        self.cache_path: str | None = None
        self.exc_reports: list[str] = []


class WeChatSend(BaseWeChat):
    """
    WeChat send type.

    Attribute
    ---------
    WeChatSendType : Send type enumeration.
    """

    WeChatSendType = WeChatSendType


    def __init__(
        self,
        rwechat: WeChat,
        bandwidth_upstream: float
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rwechat : `WeChatClient` instance.
        bandwidth_upstream : Upload bandwidth, impact send interval, unit Mpbs.
        """

        # Set attribute.
        self.rwechat = rwechat
        self.bandwidth_upstream = bandwidth_upstream
        self.queue: Queue[WeChatSendParameter] = Queue()
        self.handlers: list[Callable[[WeChatSendParameter], Any]] = []
        self.started: bool | None = False

        # Start.
        self._delete_cache_file()
        self._start_sender()


    @wrap_thread
    def _start_sender(self) -> None:
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

            ## Send.
            rsparam = self.queue.get()
            try:
                self._send(rsparam)

            ## Exception.
            except:

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                rsparam.exc_reports.append(exc_report)


            ## Handle.

            ### Define.
            def handle_handler_exception() -> None:
                """
                Handle Handler exception.
                """

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                rsparam.exc_reports.append(exc_report)


            ### Loop.
            for handler in self.handlers:
                wrap_exc(
                    handler,
                    rsparam,
                    _handler=handle_handler_exception
                )

            ## Log.
            self.rwechat.rlog.log_send(rsparam)


    def _delete_cache_file(self) -> None:
        """
        Add handler, Delete cache file.
        """


        # Define.
        def handler_delete_cache_file(rsparam: WeChatSendParameter) -> None:
            """
            Delete cache file.

            Parameters
            ----------
            rsparam : `RSendParams` instance.
            """

            # Break.
            if rsparam.cache_path is None: return

            # Delete.
            rfile = File(rsparam.cache_path)
            rfile.remove()


        # Add handler.
        self.add_handler(handler_delete_cache_file)


    def _send(
        self,
        rsparam: WeChatSendParameter
    ) -> None:
        """
        Send message.

        Parameters
        ----------
        rsparam : `RSendParams` instance.
        """

        # Handle parameter.
        for key, value in rsparam.params.items():

            ## Callable.
            if callable(value):
                rsparam.params[key] = value()

        # File.

        ## From file ID.
        if (file_id := rsparam.params.get('file_id')) is not None:
            rsparam.params['path'], rsparam.params['file_name'] = self.rwechat.rdatabase._download_file(file_id)

        ## Set file name.
        if (
            (path := rsparam.params.get('path')) is not None
            and (file_name := rsparam.params.get('file_name')) is not None
        ):
            rfile = File(path)
            copy_path = os_join(self.rwechat.dir_file, file_name)
            rfile.copy(copy_path)
            rsparam.cache_path = copy_path
            path = copy_path

        # Send.
        match rsparam.send_type:

            ## Text.
            case WeChatSendType.SEND_TEXT:
                self.rwechat.rclient.send_text(
                    rsparam.receive_id,
                    rsparam.params['text']
                )

            ## Text with '@'.
            case WeChatSendType.SEND_TEXT_AT:
                self.rwechat.rclient.send_text_at(
                    rsparam.receive_id,
                    rsparam.params['user_id'],
                    rsparam.params['text']
                )

            ## File.
            case WeChatSendType.SEND_FILE:
                self.rwechat.rclient.send_file(
                    rsparam.receive_id,
                    path
                )

            ## Image.
            case WeChatSendType.SEND_IMAGE:
                self.rwechat.rclient.send_image(
                    rsparam.receive_id,
                    path
                )

            ## Emotion.
            case WeChatSendType.SEND_EMOTION:
                self.rwechat.rclient.send_emotion(
                    rsparam.receive_id,
                    path
                )

            ## Pat.
            case WeChatSendType.SEND_PAT:
                self.rwechat.rclient.send_pat(
                    rsparam.receive_id,
                    rsparam.params['user_id']
                )

            ## Public account.
            case WeChatSendType.SEND_PUBLIC:
                self.rwechat.rclient.send_public(
                    rsparam.receive_id,
                    rsparam.params['page_url'],
                    rsparam.params['title'],
                    rsparam.params['text'],
                    rsparam.params['image_url'],
                    rsparam.params['public_name'],
                    rsparam.params['public_id']
                )

            ## Forward.
            case WeChatSendType.SEND_FORWARD:
                self.rwechat.rclient.send_forward(
                    rsparam.receive_id,
                    rsparam.params['message_id']
                )

            ## Throw exception.
            case _:
                throw(ValueError, rsparam.send_type)

        # Wait.
        self._wait(rsparam)


    def _wait(
        self,
        rsparam: WeChatSendParameter
    ) -> None:
        """
        Waiting after sending.

        Parameters
        ----------
        rsparam : `RSendParams` instance.
        """

        # Get parameter.
        seconds = randn(0.8, 1.2, precision=2)

        ## File.
        if rsparam.send_type in (2, 3, 4):
            stream_time = compute_stream_time(rsparam.params['path'], self.bandwidth_upstream)
            if stream_time > seconds:
                seconds = stream_time

        # Wait.
        sleep(seconds)


    @overload
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_TEXT],
        receive_id: str,
        send_id: int | None = None,
        *,
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_TEXT_AT],
        receive_id: str,
        send_id: int | None = None,
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_FILE, WeChatSendType.SEND_IMAGE, WeChatSendType.SEND_EMOTION],
        receive_id: str,
        send_id: int | None = None,
        *,
        path: str,
        file_name: str | None = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_PAT],
        receive_id: str,
        send_id: int | None = None,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_PUBLIC],
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
    def send(
        self,
        send_type: Literal[WeChatSendType.SEND_FORWARD],
        receive_id: str,
        send_id: int | None = None,
        *,
        message_id: str
    ) -> None: ...

    def send(
        self,
        send_type: WeChatSendType,
        receive_id: str | None = None,
        send_id: int | None = None,
        **params: Any
    ) -> None:
        """
        Put parameters into the send queue.

        Parameters
        ----------
        send_type : Send type.
            - `Literal[WeChatSendType.SEND_TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendType.SEND_TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendType.SEND_FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendType.SEND_IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendType.SEND_EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendType.SEND_PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendType.SEND_PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendType.SEND_FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        receive_id : User ID or chat room ID of receive message.
        send_id : Send ID of database.
        params : Send parameters.
            - `Callable`: Use execute return value.
            - `Any`: Use this value.
                `Key 'file_name'`: Given file name.
        """

        # Check.
        if send_type not in WeChatSendType:
            throw(ValueError, send_type)

        rsparam = WeChatSendParameter(
            self,
            send_type,
            receive_id,
            params,
            send_id
        )

        # Put.
        self.queue.put(rsparam)


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
        member_dict = self.rwechat.rclient.get_room_member_dict(room_id)
        login_id = self.rwechat.rclient.login_info['id']
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
                            0,
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


    __call__ = send


    __del__ = end
