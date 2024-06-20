# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-26 11:18:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Receive methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Literal, Callable, Optional
from queue import Queue
from json import loads as json_loads
from reytool.rcomm import get_file_stream_time, listen_socket
from reytool.ros import RFile, RFolder, os_exists
from reytool.rregex import search
from reytool.rsystem import catch_exc
from reytool.rtime import sleep, wait
from reytool.rwrap import wrap_thread, wrap_exc
from reytool.rmultitask import RThreadPool

from .rwechat import RWeChat


__all__ = (
    "RMessage",
    "RReceive"
)


class RMessage(object):
    """
    Rey's `message` type.
    """


    def __init__(
        self,
        rreceive: RReceive,
        time: int,
        id_: int,
        number: int,
        type_: int,
        display: str,
        data: str,
        user: Optional[str] = None,
        room: Optional[str] = None,
        file:  Optional[Dict[Literal["path", "name", "md5", "size"], str]] = None
    ) -> None:
        """
        Build `message` instance.

        Parameters
        ----------
        rreceive : `RReceive` instance.
        time : Message timestamp.
        id : Message ID.
        number : Message local number.
        type : Message type.
        display : Message description text.
        data : Message source data.
        user : Message sender user ID.
            - `None` : System message.
            - `str` : User messages.

        room : Message chat room ID.
            - `None` : Private chat.
            - `str` : Chat room chat.

        file : Message file information.
            - `None` : Non file message.
            - `Dict` : File message.
                * `Key 'path'` : File path.
                * `Key 'name'` : File name.
                * `Key 'md5'` : File MD5.
                * `Key 'size'` : File byte size.
        """

        # Set attribute.
        self.rreceive = rreceive
        self.time = time
        self.id = id_
        self.number = number
        self.type = type_
        self.display = display
        self.data = data
        self.user = user
        self.room = room
        self.file = file
        self._user_name = None
        self._is_quote: Optional[bool] = None
        self._is_quote_self: Optional[bool] = None
        self._quote_info: Optional[Dict[Literal["text", "quote_id", "quote_type", "quote_user", "quote_user_name", "quote_data"], Any]] = None
        self._is_at: Optional[bool] = None
        self._is_at_self: Optional[bool] = None
        self._is_new_user: Optional[bool] = None
        self._is_new_room: Optional[bool] = None
        self._is_new_room_user: Optional[bool] = None
        self._new_room_user_name: Optional[str] = None
        self._is_change_room_name: Optional[bool] = None
        self._change_room_name: Optional[str] = None
        self._is_kick_out_room: Optional[bool] = None
        self._is_dissolve_room: Optional[bool] = None


    @property
    def params(self) -> Dict[
        Literal[
            "time",
            "id",
            "number",
            "room",
            "user",
            "type",
            "display",
            "data",
            "file"
        ],
        Any
    ]:
        """
        Return parameters dictionary.

        Returns
        -------
        Parameters dictionary.
        """

        # Get parameter.
        params = {
            "time": self.time,
            "id": self.id,
            "number": self.number,
            "room": self.room,
            "user": self.user,
            "type": self.type,
            "display": self.display,
            "data": self.data,
            "file": self.file
        }

        return params


    def __str__(self) -> str:
        """
        Return parameters dictionary in string format.

        Returns
        -------
        Parameters dictionary in string format.
        """

        # Convert.
        params_str = str(self.params)

        return params_str


    @property
    def user_name(self) -> str:
        """
        Message sender user name.

        Returns
        -------
        User name.
        """

        # Judged.
        if self._user_name is not None:
            return self._user_name

        # Set.
        self._user_name = self.rreceive.rwechat.rclient.get_contact_name(
            self.user
        )

        return self._user_name


    @property
    def is_quote(self) -> bool:
        """
        Whether if is message of quote message.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_quote is not None:
            return self._is_quote

        # Judge.
        self._is_quote = (
            self.type == 49
            and "<type>57</type>" in self.data
        )

        return self._is_quote


    @property
    def is_quote_self(self) -> bool:
        """
        Whether if is message of quote self.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_quote_self is not None:
            return self._is_quote_self

        # Judge.
        if self.is_quote:
            keyword = "<chatusr>%s</chatusr>" % self.rreceive.rwechat.rclient.login_info["id"]
            if keyword in self.data:
                self._is_quote_self = True
            else:
                self._is_quote_self = False
        else:
            self._is_quote_self = False

        return self._is_quote_self


    @property
    def quote_params(self) -> Dict[
        Literal["text", "quote_id", "quote_type", "quote_user", "quote_user_name", "quote_data"],
        Any
    ]:
        """
        Return quote parameters of message.

        Returns
        -------
        Quote parameters of message.
            - `Key 'text'` : Message text.
            - `Key 'quote_id'` : Quote message ID.
            - `Key 'quote_type'` : Quote message type.
            - `Key 'quote_user'` : Quote message user ID.
            - `Key 'quote_user_name'` : Quote message user name.
            - `Key 'quote_data'` : Quote message data.
        """

        # Extracted.
        if self._quote_info is not None:
            return self._quote_info

        # Extract.
        pattern = "<title>(.+?)</title>"
        text = search(pattern, self.data)
        pattern = "<svrid>(\w+?)</svrid>"
        quote_id = search(pattern, self.data)
        pattern = "<refermsg>\s*<type>(\d+?)</type>"
        quote_type = int(search(pattern, self.data))
        pattern = "<chatusr>(\w+?)</chatusr>"
        quote_user = search(pattern, self.data)
        pattern = "<displayname>(.+?)</displayname>"
        quote_user_name = search(pattern, self.data)
        pattern = "<content>(.+?)</content>"
        quote_data = search(pattern, self.data)
        self._quote_info = {
            "text": text,
            "quote_id": quote_id,
            "quote_type": quote_type,
            "quote_user": quote_user,
            "quote_user_name": quote_user_name,
            "quote_data": quote_data
        }

        return self._quote_info


    @property
    def is_at(self) -> bool:
        """
        Whether if is `@` message.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_at is not None:
            return self._is_at

        # Judge.
        if self.type == 1:
            text = self.data
        elif self.is_quote:
            text = self.quote_params["text"]
        pattern = "@\w+ "
        result = search(pattern, text)
        if result is None:
            self._is_at = False
        else:
            self._is_at = True

        return self._is_at


    @property
    def is_at_self(self) -> bool:
        """
        Whether if is message of `@` self.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_at_self is not None:
            return self._is_at_self

        # Judge.
        if self.type == 1:
            text = self.data
        elif self.is_quote:
            text = self.quote_params["text"]
        pattern = "@%s " % self.rreceive.rwechat.rclient.login_info["name"]
        result = search(pattern, text)
        if result is None:
            self._is_at_self = False
        else:
            self._is_at_self = True

        return self._is_at_self


    @property
    def is_new_user(self) -> bool:
        """
        Whether if is new user.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_new_user is not None:
            return self._is_new_user

        # Judge.
        if (
            self.type == 10000
            and (
                self.data == "以上是打招呼的内容"
                or self.data.startswith("你已添加了")
            )
        ):
            self._is_new_user = True
        else:
            self._is_new_user = False

        return self._is_new_user


    @property
    def is_new_room(self) -> bool:
        """
        Whether if is new chat room.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_new_room is not None:
            return self._is_new_room

        # Judge.
        if (
            self.type == 10000
            and (
                "邀请你和" in self.data[:38]
                or "邀请你加入了群聊" in self.data[:42]
            )
        ):
            self._is_new_room = True
        else:
            self._is_new_room = False

        return self._is_new_room


    @property
    def is_new_room_user(self) -> bool:
        """
        Whether if is new chat room user.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_new_room_user is not None:
            return self._is_new_room_user

        # Judge.
        if (
            self.type == 10000
            and "邀请\"" in self.data[:37]
            and self.data.endswith("\"加入了群聊")
        ):
            self._is_new_room_user = True
        else:
            self._is_new_room_user = False

        return self._is_new_room_user


    @property
    def new_room_user_name(self) -> bool:
        """
        Return new chat room user name.

        Returns
        -------
        Judge result.
        """

        # Extracted.
        if self._new_room_user_name is not None:
            return self._new_room_user_name

        # Extract.
        pattern = '邀请"(.+?)"加入了群聊'
        result = search(pattern, self.data)
        self._new_room_user_name = result

        return result


    @property
    def is_change_room_name(self) -> bool:
        """
        Whether if is change chat room name.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_change_room_name is not None:
            return self._is_change_room_name

        # Judge.
        if (
            self.type == 10000
            and "修改群名为“" in self.data[:40]
        ):
            self._is_change_room_name = True
        else:
            self._is_change_room_name = False

        return self._is_change_room_name


    @property
    def change_room_name(self) -> bool:
        """
        Return change chat room name.

        Returns
        -------
        Judge result.
        """

        # Extracted.
        if self._change_room_name is not None:
            return self._change_room_name

        # Extract.
        pattern = '修改群名为“(.+?)”'
        result = search(pattern, self.data)
        self._change_room_name = result

        return result


    @property
    def is_kick_out_room(self) -> bool:
        """
        Whether if is kick out chat room.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_kick_out_room is not None:
            return self._is_kick_out_room

        # Judge.
        if (
            self.type == 10000
            and self.data.startswith("你被")
            and self.data.endswith("移出群聊")
        ):
            self._is_kick_out_room = True
        else:
            self._is_kick_out_room = False

        return self._is_kick_out_room


    @property
    def is_dissolve_room(self) -> bool:
        """
        Whether if is dissolve chat room.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_dissolve_room is not None:
            return self._is_dissolve_room

        # Judge.
        if (
            self.type == 10000
            and self.data.startswith("群主")
            and self.data.endswith("已解散该群聊")
        ):
            self._is_dissolve_room = True
        else:
            self._is_dissolve_room = False

        return self._is_dissolve_room


class RReceive(object):
    """
    Rey's `receive` type.
    """


    def __init__(
        self,
        rwechat: RWeChat,
        max_receiver: int,
        bandwidth_downstream: float
    ) -> None:
        """
        Build `receive` instance.

        Parameters
        ----------
        rwechat : `RClient` instance.
        max_receiver : Maximum number of receivers.
        bandwidth_downstream : Download bandwidth, impact receive timeout, unit Mpbs.
        """

        # Set attribute.
        self.rwechat = rwechat
        self.max_receiver = max_receiver
        self.bandwidth_downstream = bandwidth_downstream
        self.queue: Queue[RMessage] = Queue()
        self.handlers: List[Callable[[RMessage], Any]] = []
        self.started: Optional[bool] = False

        # Start.
        self._start_callback()
        self._start_receiver(self.max_receiver)
        self.rwechat.rclient.hook_message(
            "127.0.0.1",
            self.rwechat.message_callback_port,
            60
        )


    @wrap_thread
    def _start_callback(self) -> None:
        """
        Start callback socket.
        """


        # Define.
        def put_queue(data: bytes) -> None:
            """
            Put message data into receive queue.

            Parameters
            ----------
            data : Socket receive data.
            """

            # Decode.
            data: Dict = json_loads(data)

            # Break.
            if "msgId" not in data: return

            # Extract.
            message = RMessage(
                self,
                data["createTime"],
                data["msgId"],
                data["msgSequence"],
                data["type"],
                data["displayFullContent"],
                data["content"],
                data["fromUser"]
            )

            # Put.
            self.queue.put(message)


        # Listen socket.
        listen_socket(
            "127.0.0.1",
            self.rwechat.message_callback_port,
            put_queue
        )


    @wrap_thread
    def _start_receiver(
        self,
        max_receiver: int
    ) -> None:
        """
        Start receiver, that will sequentially handle message in the receive queue.

        Parameters
        ----------
        max_receiver : Maximum number of receivers.
        """


        # Define.
        def handles(message: RMessage) -> None:
            """
            Use handlers to handle message.

            Parameters
            ----------
            message : `RMessage` instance.
            """

            # Set parameter.
            exc_reports: List[str] = []
            handlers = [
                self._handler_room,
                self._handler_file,
                *self.handlers
            ]

            # Handle.

            ## Define.
            def handle_handler_exception() -> None:
                """
                Handle Handler exception.
                """

                # Catch exception.
                exc_report, *_ = catch_exc()

                # Save.
                exc_reports.append(exc_report)


            ## Loop.
            for handler in handlers:
                wrap_exc(
                    handler,
                    message,
                    _handler=handle_handler_exception
                )

            # Log.
            self.rwechat.rlog.log_receive(
                message,
                exc_reports
            )


        # Thread pool.
        thread_pool = RThreadPool(
            handles,
            _max_workers=max_receiver
        )

        # Loop.
        while True:

            ## Stop.
            if self.started is False:
                sleep(0.1)
                continue

            ## End.
            elif self.started is None:
                break

            ## Submit.
            message = self.queue.get()
            thread_pool.one(message)


    def add_handler(
        self,
        handler: Callable[[RMessage], Any]
    ) -> None:
        """
        Add message handler function.

        Parameters
        ----------
        handler : Handler method, input parameter is `RMessage` instance.
        """

        # Add.
        self.handlers.append(handler)


    def _handler_room(
        self,
        message: RMessage
    ) -> None:
        """
        Handle room message.
        """

        # Break.
        if (
            message.user.__class__ != str
            or not message.user.endswith("chatroom")
        ):
            return

        # Set attribute.
        message.room = message.user
        if ":\n" in message.data:
            user, data = message.data.split(":\n", 1)
            message.user = user
            message.data = data
        else:
            message.user = None


    def _handler_file(
        self,
        message: RMessage
    ) -> None:
        """
        Handle file message.
        """

        # Save.
        rfolder = RFolder(self.rwechat.dir_file)
        generate_path = None

        ## Image.
        if message.type == 3:

            ### Get attribute.
            file_name = f"{message.id}.jpg"
            pattern = "length=\"(\d+)\".*?md5=\"([\da-f]{32})\""
            file_size, file_md5 = search(pattern, message.data)
            file_size = int(file_size)

            ### Exist.
            pattern = f"^{file_md5}$"
            search_path = rfolder.search(pattern)

            ### Generate.
            if search_path is None:
                self.rwechat.rclient.download_file(message.id)
                generate_path = "%swxhelper/image/%s.dat" % (
                    self.rwechat.rclient.login_info["account_data_path"],
                    message.id
                )

        ## Voice.
        elif message.type == 34:

            ### Get attribute.
            file_name = f"{message.id}.amr"
            pattern = "length=\"(\d+)\""
            file_size = int(search(pattern, message.data))
            file_md5 = None

            ### Generate.
            self.rwechat.rclient.download_voice(
                message.id,
                self.rwechat.dir_file
            )
            generate_path = "%s/%s.amr" % (
                self.rwechat.dir_file,
                message.id
            )

        ## Video.
        elif message.type == 43:

            ### Get attribute.
            file_name = f"{message.id}.mp4"
            pattern = "length=\"(\d+)\""
            file_size = int(search(pattern, message.data))
            pattern = "md5=\"([\da-f]{32})\""
            file_md5 = search(pattern, message.data)

            ### Exist.
            pattern = f"^{file_md5}$"
            search_path = rfolder.search(pattern)

            ### Generate.
            if search_path is None:
                self.rwechat.rclient.download_file(message.id)
                generate_path = "%swxhelper/video/%s.mp4" % (
                    self.rwechat.rclient.login_info["account_data_path"],
                    message.id
                )

        ## Other.
        elif message.type == 49:

            ### Check.
            pattern = "^.+? : \[文件\](.+)$"
            file_name = search(pattern, message.display)
            if file_name is None:
                return
            if "<type>6</type>" not in message.data:
                return

            ### Get attribute.
            pattern = "<totallen>(\d+)</totallen>"
            file_size = int(search(pattern, message.data))
            pattern = "<md5>([\da-f]{32})</md5>"
            file_md5 = search(pattern, message.data)

            ### Exist.
            pattern = f"^{file_md5}$"
            search_path = rfolder.search(pattern)

            ### Generate.
            if search_path is None:
                self.rwechat.rclient.download_file(message.id)
                generate_path = "%swxhelper/file/%s_%s" % (
                    self.rwechat.rclient.login_info["account_data_path"],
                    message.id,
                    file_name
                )

        ## Break.
        else:
            return

        # Wait.
        if generate_path is not None:
            stream_time = get_file_stream_time(file_size, self.bandwidth_downstream)
            timeout = 10 + stream_time * (self.max_receiver + 1)
            wait(
                os_exists,
                generate_path,
                _interval = 0.05,
                _timeout=timeout
            )
            sleep(0.2)

        # Move.
        if generate_path is None:
            save_path = "%s/%s" % (
                self.rwechat.dir_file,
                file_md5
            )
        else:
            rfile = RFile(generate_path)
            search_path = None
            if file_md5 is None:
                file_md5 = rfile.md5

                ### Exist.
                pattern = f"^{file_md5}$"
                search_path = rfolder.search(pattern)

            if search_path is None:
                save_path = "%s/%s" % (
                    self.rwechat.dir_file,
                    file_md5
                )
                rfile.move(save_path)

        # Set parameter.
        file = {
            "path": save_path,
            "name": file_name,
            "md5": file_md5,
            "size": file_size
        }
        message.file = file


    def start(self) -> None:
        """
        Start receiver.
        """

        # Start.
        self.started = True

        # Report.
        print("Start receiver.")


    def stop(self) -> None:
        """
        Stop receiver.
        """

        # Stop.
        self.started = False

        # Report.
        print("Stop receiver.")


    def end(self) -> None:
        """
        End receiver.
        """

        # End.
        self.started = None

        # Report.
        print("End receiver.")


    __del__ = end