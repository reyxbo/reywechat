# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-03 22:53:18
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Send methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Literal, Callable, Optional, Union, NoReturn, overload
from functools import wraps as functools_wraps
from os.path import join as os_join
from queue import Queue
from re import escape as re_escape
from reytool.rcomm import get_file_stream_time
from reytool.rexception import throw, catch_exc
from reytool.rrandom import randn
from reytool.rregex import sub
from reytool.ros import RFile
from reytool.rtime import sleep
from reytool.rwrap import wrap_thread, wrap_exc

from .rexception import RWeChatExecuteContinueError, RWeChatExecuteBreakError
from .rwechat import RWeChat


__all__ = (
    "RSendParam",
    "RSend"
)


class RSendParam(object):
    """
    Rey's `send parameters` type.
    """


    def __init__(
        self,
        rsend: RSend,
        send_type: Literal[0, 1, 2, 3, 4, 5, 6, 7],
        receive_id: str,
        params: Dict,
        send_id: Optional[int]
    ) -> None:
        """
        Build `send parameters` instance.

        Parameters
        ----------
        rsend : `RSend` instance.
        send_type : Send type.
            - `Literal[0]` : Send text message, use `RClient.send_text` method.
            - `Literal[1]` : Send text message with `@`, use `RClient.send_text_at` method.
            - `Literal[2]` : Send file message, use `RClient.send_file` method.
            - `Literal[3]` : Send image message, use `RClient.send_image` method.
            - `Literal[4]` : Send emotion message, use `RClient.send_emotion` method.
            - `Literal[5]` : Send pat message, use `RClient.send_pat` method.
            - `Literal[6]` : Send public account message, use `RClient.send_public` method.
            - `Literal[7]` : Forward message, use `RClient.send_forward` method.

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
        self.cache_path: Optional[str] = None
        self.exc_reports: List[str] = []


class RSend(object):
    """
    Rey's `send` type.
    """


    def __init__(
        self,
        rwechat: RWeChat,
        bandwidth_upstream: float
    ) -> None:
        """
        Build `send` instance.

        Parameters
        ----------
        rwechat : `RClient` instance.
        bandwidth_upstream : Upload bandwidth, impact send interval, unit Mpbs.
        """

        # Set attribute.
        self.rwechat = rwechat
        self.bandwidth_upstream = bandwidth_upstream
        self.queue: Queue[RSendParam] = Queue()
        self.handlers: List[Callable[[RSendParam], Any]] = []
        self.started: Optional[bool] = False

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
        def handler_delete_cache_file(rsparam: RSendParam) -> None:
            """
            Delete cache file.

            Parameters
            ----------
            rsparam : `RSendParams` instance.
            """

            # Break.
            if rsparam.cache_path is None: return

            # Delete.
            rfile = RFile(rsparam.cache_path)
            rfile.remove()


        # Add handler.
        self.add_handler(handler_delete_cache_file)


    def _send(
        self,
        rsparam: RSendParam
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
        if (file_id := rsparam.params.get("file_id")) is not None:
            rsparam.params["path"], rsparam.params["file_name"] = self.rwechat.rdatabase._download_file(file_id)

        ## Set file name.
        if (
            (path := rsparam.params.get("path")) is not None
            and (file_name := rsparam.params.get("file_name")) is not None
        ):
            rfile = RFile(path)
            copy_path = os_join(self.rwechat.dir_file, file_name)
            rfile.copy(copy_path)
            rsparam.cache_path = copy_path
            path = copy_path

        # Send.
        match rsparam.send_type:

            ## Text.
            case 0:
                self.rwechat.rclient.send_text(
                    rsparam.receive_id,
                    rsparam.params["text"]
                )

            ## Text with "@".
            case 1:
                self.rwechat.rclient.send_text_at(
                    rsparam.receive_id,
                    rsparam.params["user_id"],
                    rsparam.params["text"]
                )

            ## File.
            case 2:
                self.rwechat.rclient.send_file(
                    rsparam.receive_id,
                    path
                )

            ## Image.
            case 3:
                self.rwechat.rclient.send_image(
                    rsparam.receive_id,
                    path
                )

            ## Emotion.
            case 4:
                self.rwechat.rclient.send_emotion(
                    rsparam.receive_id,
                    path
                )

            ## Pat.
            case 5:
                self.rwechat.rclient.send_pat(
                    rsparam.receive_id,
                    rsparam.params["user_id"]
                )

            ## Public account.
            case 6:
                self.rwechat.rclient.send_public(
                    rsparam.receive_id,
                    rsparam.params["page_url"],
                    rsparam.params["title"],
                    rsparam.params["text"],
                    rsparam.params["image_url"],
                    rsparam.params["public_name"],
                    rsparam.params["public_id"]
                )

            ## Forward.
            case 7:
                self.rwechat.rclient.send_forward(
                    rsparam.receive_id,
                    rsparam.params["message_id"]
                )

            ## Throw exception.
            case _:
                throw(ValueError, rsparam.send_type)

        # Wait.
        self._wait(rsparam)


    def _wait(
        self,
        rsparam: RSendParam
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
            stream_time = get_file_stream_time(rsparam.params["path"], self.bandwidth_upstream)
            if stream_time > seconds:
                seconds = stream_time

        # Wait.
        sleep(seconds)


    @overload
    def send(
        self,
        send_type: Literal[0],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[1],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        user_id: Union[str, List[str], Literal["notify@all"]],
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[2, 3, 4],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        path: str,
        file_name: Optional[str] = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[5],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[6],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        page_url: str,
        title: str,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        public_name: Optional[str] = None,
        public_id: Optional[str] = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[7],
        receive_id: str,
        send_id: Optional[int] = None,
        *,
        message_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Any,
        receive_id: str,
        send_id: Optional[int] = None,
        **params: Any
    ) -> NoReturn: ...

    def send(
        self,
        send_type: Optional[Literal[0, 1, 2, 3, 4, 5, 6, 7]] = None,
        receive_id: Optional[str] = None,
        send_id: Optional[int] = None,
        **params: Any
    ) -> None:
        """
        Put parameters into the send queue.

        Parameters
        ----------
        send_type : Send type.
            - `Literal[0]` : Send text message, use `RClient.send_text` method.
            - `Literal[1]` : Send text message with `@`, use `RClient.send_text_at` method.
            - `Literal[2]` : Send file message, use `RClient.send_file` method.
            - `Literal[3]` : Send image message, use `RClient.send_image` method.
            - `Literal[4]` : Send emotion message, use `RClient.send_emotion` method.
            - `Literal[5]` : Send pat message, use `RClient.send_pat` method.
            - `Literal[6]` : Send public account message, use `RClient.send_public` method.
            - `Literal[7]` : Forward message, use `RClient.send_forward` method.

        receive_id : User ID or chat room ID of receive message.
        send_id : Send ID of database.
        params : Send parameters.
            - `Callable` : Use execute return value.
            - `Any` : Use this value.
                * `Key 'file_name'` : Given file name.
        """

        # Check.
        if send_type not in (0, 1, 2, 3, 4, 5, 6, 7):
            throw(ValueError, send_type)

        rsparam = RSendParam(
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
        handler: Callable[[RSendParam], Any]
    ) -> None:
        """
        Add send handler function.

        Parameters
        ----------
        handler : Handler method, input parameter is `RSendParam` instance.
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
        login_id = self.rwechat.rclient.login_info["id"]
        if login_id in member_dict:
            del member_dict[login_id]

        # Add.
        names = [
            re_escape(name)
            for name in member_dict.values()
            if len(name) != 1
        ]
        pattern = r"(?<!@)(%s) *" % "|".join(names)
        replace = lambda match: "@%s " % match[1]
        text_at = sub(pattern, text, replace)

        return text_at


    def wrap_try_send(
        self,
        receive_id: Union[str, List[str]],
        func: Callable
    ) -> Callable:
        """
        Decorator, send exception information.

        Parameters
        ----------
        receive_id : Receive user ID or chat room ID.
            - `str` : An ID.
            - `List[str]` : Multiple ID.

        func : Function.

        Returns
        -------
        Decorated function.
        """

        # Handle parameter.
        if receive_id.__class__ == str:
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
                    (RWeChatExecuteContinueError, RWeChatExecuteBreakError)
                ):
                    text = "\n".join(
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
                raise exc_instance

            return result


        return wrap


    def start(self) -> None:
        """
        Start sender.
        """

        # Start.
        self.started = True

        # Report.
        print("Start sender.")


    def stop(self) -> None:
        """
        Stop sender.
        """

        # Stop.
        self.started = False

        # Report.
        print("Stop sender.")


    def end(self) -> None:
        """
        End sender.
        """

        # End.
        self.started = None

        # Report.
        print("End sender.")


    __call__ = send


    __del__ = end