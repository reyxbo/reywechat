# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-03 22:53:18
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Send methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Literal, Callable, Optional, NoReturn, overload
from os.path import join as os_join
from queue import Queue
from re import escape as re_escape
from reytool.rcomm import get_file_stream_time
from reytool.rrandom import randn
from reytool.rregex import sub
from reytool.ros import RFile
from reytool.rsystem import throw, catch_exc
from reytool.rtime import sleep
from reytool.rwrap import wrap_thread, wrap_exc

from .rwechat import RWeChat


__all__ = (
    "RSend",
)


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
        self.queue: Queue[Dict] = Queue()
        self.handlers: List[Callable[[Dict, bool], Any]] = []
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

            ## Stop.
            if self.started is False:
                sleep(0.1)
                continue

            ## End.
            elif self.started is None:
                break

            ## Send.
            exc_reports: List[str] = []
            params = self.queue.get()
            try:
                self._send(params)
            except:
                send_success = False
                exc_report, *_ = catch_exc()
                exc_reports.append(exc_report)
            else:
                send_success = True

            ## Handle.

            ### Define.
            def handle_handler_exception() -> None:
                """
                Handle Handler exception.
                """

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                exc_reports.append(exc_report)


            ### Loop.
            for handler in self.handlers:
                wrap_exc(
                    handler,
                    params,
                    send_success,
                    _handler=handle_handler_exception
                )

            ## Log.
            self.rwechat.rlog.log_send(params, exc_reports)


    def _delete_cache_file(self) -> None:
        """
        Add handler, Delete cache file.
        """


        # Define.
        def handler_delete_cache_file(
            params: Dict,
            success: bool
        ) -> None:
            """
            Delete cache file.

            Parameters
            ----------
            params : Send parameters.
            success : Whether the sending was successful.
            """

            # Break.
            cache_path: Optional[str] = params.get("cache_path")
            if cache_path is None: return

            # Delete.
            rfile = RFile(cache_path)
            rfile.remove()


        # Add handler.
        self.add_handler(handler_delete_cache_file)


    def _send(
        self,
        params: Any
    ) -> None:
        """
        Send message.

        Parameters
        ----------
        params : Send parameters.
            - `Key 'file_name'` : Given file name.
        """

        # Get parameter.
        send_type: int = params["send_type"]
        receive_id: str = params["receive_id"]

        # File.
        path = params.get("path")
        file_name = params.get("file_name")
        if (
            path is not None
            and file_name is not None
        ):
            rfile = RFile(path)
            copy_path = os_join(self.rwechat.dir_file, file_name)
            rfile.copy(copy_path)
            params["cache_path"] = copy_path
            path = copy_path

        # Send.

        ## Text.
        if send_type == 0:
            self.rwechat.rclient.send_text(
                receive_id,
                params["text"]
            )

        ## Text with "@".
        elif send_type == 1:
            self.rwechat.rclient.send_text_at(
                receive_id,
                params["user_id"],
                params["text"]
            )

        ## File.
        elif send_type == 2:
            self.rwechat.rclient.send_file(
                receive_id,
                path
            )

        ## Image.
        elif send_type == 3:
            self.rwechat.rclient.send_image(
                receive_id,
                path
            )

        ## Emotion.
        elif send_type == 4:
            self.rwechat.rclient.send_emotion(
                receive_id,
                path
            )

        ## Pat.
        elif send_type == 5:
            self.rwechat.rclient.send_pat(
                receive_id,
                params["user_id"]
            )

        ## Public account.
        elif send_type == 6:
            self.rwechat.rclient.send_public(
                receive_id,
                params["page_url"],
                params["title"],
                params["text"],
                params["image_url"],
                params["public_name"],
                params["public_id"]
            )

        ## Forward.
        elif send_type == 7:
            self.rwechat.rclient.send_forward(
                receive_id,
                params["message_id"]
            )

        ## Raise.
        else:
            throw(ValueError, send_type)

        # Wait.
        self._wait(params)


    def _wait(
        self,
        params: Any
    ) -> None:
        """
        Waiting after sending.

        Parameters
        ----------
        params : Send parameters.
        """

        # Get parameter.
        send_type: str = params["send_type"]
        seconds = randn(0.8, 1.2, precision=2)

        ## File.
        if send_type in (2, 3, 4):
            stream_time = get_file_stream_time(params["path"], self.bandwidth_upstream)
            if stream_time > seconds:
                seconds = stream_time

        # Wait.
        sleep(seconds)


    @overload
    def send(
        self,
        send_type: Literal[0],
        receive_id: str,
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[1],
        receive_id: str,
        user_id: str | List[str],
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[2, 3, 4],
        receive_id: str,
        path: str,
        file_name: Optional[str] = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[5],
        receive_id: str,
        user_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[6],
        receive_id: str,
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
        message_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Any,
        receive_id: str,
        **params: Any
    ) -> NoReturn: ...

    def send(
        self,
        send_type: Literal[0, 1, 2, 3, 4, 5, 6, 7],
        receive_id: str,
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
        params : Send parameters.
            - `Callable` : Use execute return value.
            - `Any` : Use this value.
                * `Key 'file_name'` : Given file name.
        """

        # Check parameter.
        if send_type not in (0, 1, 2, 3, 4, 5, 6, 7):
            throw(ValueError, send_type)

        # Handle parameters.
        for key, value in params.items():
            if callable(value):
                params[key] = value()
        params = {
            "send_type": send_type,
            "receive_id": receive_id,
            **params
        }

        # Put.
        self.queue.put(params)


    def add_handler(
        self,
        handler: Callable[[Dict, bool], Any]
    ) -> None:
        """
        Add send handler function.

        Parameters
        ----------
        handler : Handler method, input parameters are send parameters and whether the sending was successful.
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
        del member_dict[login_id]

        # Add.
        names = [
            re_escape(name)
            for name in member_dict.values()
            if len(name) != 1
        ]
        pattern = "(?<!@)(%s) *" % "|".join(names)
        replace = lambda match: "@%s " % match[1]
        text_at = sub(pattern, text, replace)

        return text_at


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