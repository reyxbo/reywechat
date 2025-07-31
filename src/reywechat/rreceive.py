# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-26 11:18:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Receive methods.
"""


from __future__ import annotations
from typing import Any, TypedDict, Literal, overload
from collections.abc import Callable
from queue import Queue
from json import loads as json_loads
from bs4 import BeautifulSoup as BSBeautifulSoup
from bs4.element import Tag as BSTag
from reykit.rbase import throw, catch_exc
from reykit.rimage import decode_qrcode
from reykit.rnet import compute_stream_time, listen_socket
from reykit.ros import File, Folder, os_exists
from reykit.rre import search
from reykit.rtask import ThreadPool
from reykit.rtime import sleep, wait
from reykit.rwrap import wrap_thread, wrap_exc

from .rbase import BaseWeChat, WeChatTriggerError
from .rsend import WeChatSendEnum
from .rwechat import WeChat


__all__ = (
    'WeChatMessage',
    'WechatReceiver'
)


MessageParameters = TypedDict(
        'MessageParameters',
        {
            'time': int,
            'id': int,
            'number': int,
            'room': str | None,
            'user': str | None,
            'type': int,
            'display': str,
            'data': str,
            'file': dict[Literal['path', 'name', 'md5', 'size'], str]
        }
    )


class WeChatMessage(BaseWeChat):
    """
    WeChat message type.
    """


    def __init__(
        self,
        receiver: WechatReceiver,
        time: int,
        id_: int,
        number: int,
        type_: int,
        display: str,
        data: str,
        user: str | None = None,
        room: str | None = None,
        file:  dict[Literal['path', 'name', 'md5', 'size'], str] | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        receiver : `WechatReceiver` instance.
        time : Message timestamp.
        id : Message ID.
        number : Message local number.
        type : Message type.
        display : Message description text.
        data : Message source data.
        user : Message sender user ID.
            - `None`: System message.
            - `str`: User messages.
        room : Message chat room ID.
            - `None`: Private chat.
            - `str`: Chat room chat.
        file : Message file information.
            - `None`: Non file message.
            - `dict`: File message.
                `Key 'path'`: File path.
                `Key 'name'`: File name.
                `Key 'md5'`: File MD5.
                `Key 'size'`: File byte size.
        """

        # Import.
        from .rtrigger import TriggerRule

        # Set attribute.
        self.receiver = receiver
        self.time = time
        self.id = id_
        self.number = number
        self.type = type_
        self.display = display
        self.data = data
        self.user = user
        self.room = room
        self.file = file
        self._user_name: str | None = None
        self._room_name: str | None = None
        self._is_quote: bool | None = None
        self._is_quote_self: bool | None = None
        self._quote_params: dict[Literal['text', 'quote_id', 'quote_type', 'quote_user', 'quote_user_name', 'quote_data'], str] | None = None
        self._is_at: bool | None = None
        self._is_at_self: bool | None = None
        self._is_new_user: bool | None = None
        self._is_new_room: bool | None = None
        self._is_new_room_user: bool | None = None
        self._new_room_user_name: str | None = None
        self._is_change_room_name: bool | None = None
        self._change_room_name: str | None = None
        self._is_kick_out_room: bool | None = None
        self._is_dissolve_room: bool | None = None
        self._is_image: bool | None = None
        self._image_qrcodes: list[str] | None = None
        self._is_xml: bool | None = None
        self._is_app: bool | None = None
        self._app_params: dict | None = None
        self._valid: bool | None = None
        self.trigger_rule: TriggerRule | None = None
        self.trigger_continue = self.receiver.trigger.continue_
        self.trigger_break = self.receiver.trigger.break_
        self.replied: bool = False
        self.exc_reports: list[str] = []


    @property
    def params(self) -> MessageParameters:
        """
        Return parameters dictionary.

        Returns
        -------
        Parameters dictionary.
        """

        # Get parameter.
        params = {
            'time': self.time,
            'id': self.id,
            'number': self.number,
            'room': self.room,
            'user': self.user,
            'type': self.type,
            'display': self.display,
            'data': self.data,
            'file': self.file
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
        self._user_name = self.receiver.rwechat.client.get_contact_name(
            self.user
        )

        return self._user_name


    @property
    def room_name(self) -> str:
        """
        Message sender chat room name.

        Returns
        -------
        Chat room name.
        """

        # Break.
        if self.room is None:
            return

        # Judged.
        if self._room_name is not None:
            return self._room_name

        # Set.
        self._room_name = self.receiver.rwechat.client.get_contact_name(
            self.room
        )

        return self._room_name


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
            and '<type>57</type>' in self.data
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
        self._is_quote_self = (
            self.is_quote
            and '<chatusr>%s</chatusr>' % self.receiver.rwechat.client.login_info['id'] in self.data
        )

        return self._is_quote_self


    @property
    def quote_params(self) -> dict[
        Literal['text', 'quote_id', 'quote_type', 'quote_user', 'quote_user_name', 'quote_data'],
        str | None
    ]:
        """
        Return quote parameters of message.

        Returns
        -------
        Quote parameters of message.
            - `Key 'text'`: Message text.
            - `Key 'quote_id'`: Quote message ID.
            - `Key 'quote_type'`: Quote message type.
            - `Key 'quote_user'`: Quote message user ID.
            - `Key 'quote_user_name'`: Quote message user name.
            - `Key 'quote_data'`: Quote message data.
        """

        # Extracted.
        if self._quote_params is not None:
            return self._quote_params

        # Check.
        if not self.is_quote:
            throw(AssertionError, self.is_quote)

        # Extract.
        pattern = '<title>(.+?)</title>'
        text = search(pattern, self.data)
        pattern = r'<svrid>(\w+?)</svrid>'
        quote_id = search(pattern, self.data)
        pattern = r'<refermsg>\s*<type>(\d+?)</type>'
        quote_type = int(search(pattern, self.data))
        pattern = r'<chatusr>(\w+?)</chatusr>'
        quote_user = search(pattern, self.data)
        pattern = '<displayname>(.+?)</displayname>'
        quote_user_name = search(pattern, self.data)
        pattern = '<content>(.+?)</content>'
        quote_data = search(pattern, self.data)
        self._quote_params = {
            'text': text,
            'quote_id': quote_id,
            'quote_type': quote_type,
            'quote_user': quote_user,
            'quote_user_name': quote_user_name,
            'quote_data': quote_data
        }

        return self._quote_params


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
            text = self.quote_params['text']
        pattern = r'@\w+ '
        result = search(pattern, text)
        self._is_at = result is not None

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
            text = self.quote_params['text']
        pattern = '@%s ' % self.receiver.rwechat.client.login_info['name']
        result = search(pattern, text)
        self._is_at_self = result is not None

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
        self._is_new_user = (
            self.type == 10000
            and (
                self.data == '以上是打招呼的内容'
                or self.data.startswith('你已添加了')
            )
        )

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
        self._is_new_room = (
            self.type == 10000
            and (
                '邀请你和' in self.data[:38]
                or '邀请你加入了群聊' in self.data[:42]
            )
        )

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
        self._is_new_room_user = (
            self.type == 10000
            and '邀请"' in self.data[:37]
            and self.data.endswith('"加入了群聊')
        )

        return self._is_new_room_user


    @property
    def new_room_user_name(self) -> str | None:
        """
        Return new chat room user name.

        Returns
        -------
        New chat room user name.
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
        self._is_change_room_name = (
            self.type == 10000
            and '修改群名为“' in self.data[:40]
        )

        return self._is_change_room_name


    @property
    def change_room_name(self) -> str | None:
        """
        Return change chat room name.

        Returns
        -------
        Change chat room name.
        """

        # Extracted.
        if self._change_room_name is not None:
            return self._change_room_name

        # Extract.
        pattern = '修改群名为“(.+?)”'
        result = search(pattern, self.data)
        self._change_room_name = result

        return self._change_room_name


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
        self._is_kick_out_room = (
            self.type == 10000
            and self.data.startswith('你被')
            and self.data.endswith('移出群聊')
        )

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
        self._is_dissolve_room = (
            self.type == 10000
            and self.data.startswith('群主')
            and self.data.endswith('已解散该群聊')
        )

        return self._is_dissolve_room


    @property
    def is_image(self) -> bool:
        """
        Whether if is image.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_image is not None:
            return self._is_image

        # Judge.
        self._is_image = self.type == 3

        return self._is_image


    @property
    def image_qrcodes(self) -> list[str]:
        """
        Return image QR code texts.

        Returns
        -------
        Image QR code texts.
        """

        # Extracted.
        if self._image_qrcodes is not None:
            return self._image_qrcodes

        # Check.
        if not self.is_image:
            throw(AssertionError, self.is_image)

        # Extract.
        self._image_qrcodes = decode_qrcode(self.file['path'])

        return self._image_qrcodes


    @property
    def is_xml(self) -> bool:
        """
        Whether if is XML format.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_xml is not None:
            return self._is_xml

        # Judge.
        self._is_xml = (
            self.type != 1
            and self.data.startswith('<?xml ')
        )

        return self._is_xml


    @property
    def is_app(self) -> bool:
        """
        Whether if is application share.

        Returns
        -------
        Judge result.
        """

        # Judged.
        if self._is_app is not None:
            return self._is_app

        # Judge.
        self.is_app = (
            self.type == 49
            and self.is_xml
            and '<appmsg ' in self.data[:50]
        )

        return self.is_app


    @property
    def app_params(self) -> dict:
        """
        Return application share parameters.

        Returns
        -------
        Application share parameters.
        """

        # Extracted.
        if self._app_params is not None:
            return self._app_params

        # Check.
        if not self.is_app:
            throw(AssertionError, self.is_app)

        # Extract.
        bs_document = BSBeautifulSoup(
            self.data,
            'xml'
        )
        bs_appmsg = bs_document.find('appmsg')
        self._app_params = {
            bs_element.name: bs_element.text
            for bs_element in bs_appmsg.contents
            if type(bs_element) == BSTag
        }

        return self._app_params


    @property
    def valid(self) -> bool:
        """
        Judge if is valid user or chat room or chat room user from database.

        Returns
        -------
        Judgment result.
            - `True`: Valid.
            - `False`: Invalid or no record.
        """

        # Extracted.
        if self._valid is not None:
            return self._valid

        # Judge.
        self._valid = self.receiver.rwechat.database.is_valid(self)

        return self._valid


    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_TEXT],
        *,
        text: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_TEXT_AT],
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_FILE, WeChatSendEnum.SEND_IMAGE, WeChatSendEnum.SEND_EMOTION],
        *,
        path: str,
        file_name: str | None = None
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_PAT],
        *,
        user_id: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_PUBLIC],
        *,
        page_url: str,
        title: str,
        text: str | None = None,
        image_url: str | None = None,
        public_name: str | None = None,
        public_id: str | None = None
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendEnum.SEND_FORWARD],
        *,
        message_id: str
    ) -> None: ...

    def reply(
        self,
        send_type: WeChatSendEnum | None = None,
        **params: Any
    ) -> None:
        """
        Send reply message.

        Parameters
        ----------
        send_type : Send type.
            - `Literal[WeChatSendEnum.SEND_TEXT]`: Send text message, use `WeChatClient.send_text`: method.
            - `Literal[WeChatSendEnum.SEND_TEXT_AT]`: Send text message with `@`, use `WeChatClient.send_text_at`: method.
            - `Literal[WeChatSendEnum.SEND_FILE]`: Send file message, use `WeChatClient.send_file`: method.
            - `Literal[WeChatSendEnum.SEND_IMAGE]`: Send image message, use `WeChatClient.send_image`: method.
            - `Literal[WeChatSendEnum.SEND_EMOTION]`: Send emotion message, use `WeChatClient.send_emotion`: method.
            - `Literal[WeChatSendEnum.SEND_PAT]`: Send pat message, use `WeChatClient.send_pat`: method.
            - `Literal[WeChatSendEnum.SEND_PUBLIC]`: Send public account message, use `WeChatClient.send_public`: method.
            - `Literal[WeChatSendEnum.SEND_FORWARD]`: Forward message, use `WeChatClient.send_forward`: method.
        params : Send parameters.
            - `Callable`: Use execute return value.
            - `Any`: Use this value.
                `Key 'file_name'`: Given file name.
        """

        # Check.
        if (
            self.trigger_rule is None
            or not self.trigger_rule['is_reply']
        ):
            text = 'can only be used by reply trigger'
            throw(WeChatTriggerError, self.trigger_rule, text=text)

        # Get parameter.
        if self.room is None:
            receive_id = self.user
        else:
            receive_id = self.room

        # Status.
        self.replied = True

        # Send.
        self.receiver.rwechat.sender.send(
            send_type,
            receive_id=receive_id,
            **params
        )


class WechatReceiver(BaseWeChat):
    """
    WeChat receiver type.
    """


    def __init__(
        self,
        rwechat: WeChat,
        max_receiver: int,
        bandwidth_downstream: float
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rwechat : `WeChatClient` instance.
        max_receiver : Maximum number of receivers.
        bandwidth_downstream : Download bandwidth, impact receive timeout, unit Mpbs.
        """

        # Import.
        from .rtrigger import WeChatTrigger

        # Set attribute.
        self.rwechat = rwechat
        self.max_receiver = max_receiver
        self.bandwidth_downstream = bandwidth_downstream
        self.queue: Queue[WeChatMessage] = Queue()
        self.handlers: list[Callable[[WeChatMessage], Any]] = []
        self.started: bool | None = False
        self.trigger = WeChatTrigger(self)

        # Start.
        self.__start_callback()
        self.__start_receiver(self.max_receiver)
        self.rwechat.client.hook_message(
            '127.0.0.1',
            self.rwechat.client.message_callback_port,
            60
        )


    @wrap_thread
    def __start_callback(self) -> None:
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
            data: dict = json_loads(data)

            # Break.
            if 'msgId' not in data:
                return

            # Extract.
            message = WeChatMessage(
                self,
                data['createTime'],
                data['msgId'],
                data['msgSequence'],
                data['type'],
                data['displayFullContent'],
                data['content'],
                data['fromUser']
            )

            # Put.
            self.queue.put(message)


        # Listen socket.
        listen_socket(
            '127.0.0.1',
            self.rwechat.client.message_callback_port,
            put_queue
        )


    @wrap_thread
    def __start_receiver(
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
        def handles(message: WeChatMessage) -> None:
            """
            Use handlers to handle message.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Set parameter.
            handlers = [
                self.__handler_room,
                self.__handler_file,
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
                message.exc_reports.append(exc_report)


            ## Loop.
            for handler in handlers:
                wrap_exc(
                    handler,
                    message,
                    _handler=handle_handler_exception
                )

            # Log.
            self.rwechat.log.log_receive(message)


        # Thread pool.
        thread_pool = ThreadPool(
            handles,
            _max_workers=max_receiver
        )

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

            ## Submit.
            message = self.queue.get()
            thread_pool(message)


    def add_handler(
        self,
        handler: Callable[[WeChatMessage], Any]
    ) -> None:
        """
        Add message handler function.

        Parameters
        ----------
        handler : Handler method, input parameter is `WeChatMessage` instance.
        """

        # Add.
        self.handlers.append(handler)


    def __handler_room(
        self,
        message: WeChatMessage
    ) -> None:
        """
        Handle room message.
        """

        # Break.
        if (
            type(message.user) != str
            or not message.user.endswith('chatroom')
        ):
            return

        # Set attribute.
        message.room = message.user
        if ':\n' in message.data:
            user, data = message.data.split(':\n', 1)
            message.user = user
            message.data = data
        else:
            message.user = None


    def __handler_file(
        self,
        message: WeChatMessage
    ) -> None:
        """
        Handle file message.
        """

        # Save.
        rfolder = Folder(self.rwechat.dir_file)
        generate_path = None
        match message.type:

            ## Image.
            case 3:

                ### Get attribute.
                file_name = f'{message.id}.jpg'
                pattern = r'length="(\d+)".*?md5="([\da-f]{32})"'
                file_size, file_md5 = search(pattern, message.data)
                file_size = int(file_size)

                ### Exist.
                pattern = f'^{file_md5}$'
                search_path = rfolder.search(pattern)

                ### Generate.
                if search_path is None:
                    self.rwechat.client.download_file(message.id)
                    generate_path = '%swxhelper/image/%s.dat' % (
                        self.rwechat.client.login_info['account_data_path'],
                        message.id
                    )

            ## Voice.
            case 34:

                ### Get attribute.
                file_name = f'{message.id}.amr'
                pattern = r'length="(\d+)"'
                file_size = int(search(pattern, message.data))
                file_md5 = None

                ### Generate.
                self.rwechat.client.download_voice(
                    message.id,
                    self.rwechat.dir_file
                )
                generate_path = '%s/%s.amr' % (
                    self.rwechat.dir_file,
                    message.id
                )

            ## Video.
            case 43:

                ### Get attribute.
                file_name = f'{message.id}.mp4'
                pattern = r'length="(\d+)"'
                file_size = int(search(pattern, message.data))
                pattern = r'md5="([\da-f]{32})"'
                file_md5 = search(pattern, message.data)

                ### Exist.
                pattern = f'^{file_md5}$'
                search_path = rfolder.search(pattern)

                ### Generate.
                if search_path is None:
                    self.rwechat.client.download_file(message.id)
                    generate_path = '%swxhelper/video/%s.mp4' % (
                        self.rwechat.client.login_info['account_data_path'],
                        message.id
                    )

            ## Other.
            case 49:

                ### Check.
                pattern = r'^.+? : \[文件\](.+)$'
                file_name = search(pattern, message.display)
                if file_name is None:
                    return
                if '<type>6</type>' not in message.data:
                    return

                ### Get attribute.
                pattern = r'<totallen>(\d+)</totallen>'
                file_size = int(search(pattern, message.data))
                pattern = r'<md5>([\da-f]{32})</md5>'
                file_md5 = search(pattern, message.data)

                ### Exist.
                pattern = f'^{file_md5}$'
                search_path = rfolder.search(pattern)

                ### Generate.
                if search_path is None:
                    self.rwechat.client.download_file(message.id)
                    generate_path = '%swxhelper/file/%s_%s' % (
                        self.rwechat.client.login_info['account_data_path'],
                        message.id,
                        file_name
                    )

            ## Break.
            case _:
                return

        # Wait.
        if generate_path is not None:
            stream_time = compute_stream_time(file_size, self.bandwidth_downstream)
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
            save_path = '%s/%s' % (
                self.rwechat.dir_file,
                file_md5
            )
        else:
            rfile = File(generate_path)
            search_path = None
            if file_md5 is None:
                file_md5 = rfile.md5

                ### Exist.
                pattern = f'^{file_md5}$'
                search_path = rfolder.search(pattern)

            if search_path is None:
                save_path = '%s/%s' % (
                    self.rwechat.dir_file,
                    file_md5
                )
                rfile.move(save_path)

        # Set parameter.
        file = {
            'path': save_path,
            'name': file_name,
            'md5': file_md5,
            'size': file_size
        }
        message.file = file


    def start(self) -> None:
        """
        Start receiver.
        """

        # Start.
        self.started = True

        # Report.
        print('Start receiver.')


    def stop(self) -> None:
        """
        Stop receiver.
        """

        # Stop.
        self.started = False

        # Report.
        print('Stop receiver.')


    def end(self) -> None:
        """
        End receiver.
        """

        # End.
        self.started = None

        # Report.
        print('End receiver.')


    __del__ = end
