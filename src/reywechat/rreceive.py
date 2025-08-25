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
from reykit.rbase import throw
from reykit.rimage import decode_qrcode
from reykit.rlog import Mark
from reykit.rnet import listen_socket
from reykit.ros import File, os_exists
from reykit.rre import search, search_batch, findall
from reykit.rtask import ThreadPool
from reykit.rtime import now, sleep, wait, to_time, time_to
from reykit.rwrap import wrap_thread, wrap_exc

from .rbase import WeChatBase, WeChatTriggerError
from .rsend import WeChatSendTypeEnum, WeChatSendStatusEnum
from .rwechat import WeChat


__all__ = (
    'WeChatMessage',
    'WechatReceiver'
)


MessageParameterFile = TypedDict(
    'MessageParameterFile',
    {
        'path': str,
        'name': str,
        'md5': str,
        'size': int
    }
)
MessageParameter = TypedDict(
    'MessageParameter',
    {
        'time': int,
        'id': int,
        'number': int,
        'room': str | None,
        'user': str | None,
        'type': int,
        'display': str,
        'data': str,
        'file': MessageParameterFile
    }
)
MessageShareParameter = TypedDict(
    'MessageShareParameter',
    {
        'name': str | None,
        'title': str | None,
        'des': str | None,
        'url': str | None
    }
)
MessageQuoteParameter = TypedDict(
    'MessageQuoteParameter',
    {
        'text': str,
        'quote_id': int,
        'quote_time': int,
        'quote_type': int,
        'quote_user': str,
        'quote_user_name': str,
        'quote_data': str
    }
)


class WeChatMessage(WeChatBase):
    """
    WeChat message type.
    """

    SendTypeEnum = WeChatSendTypeEnum
    SendStatusEnum = WeChatSendStatusEnum


    def __init__(
        self,
        receiver: WechatReceiver,
        time: int,
        id_: int,
        number: int,
        type_: int,
        display: str,
        data: str,
        window: str
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
        window : Message sende window ID.

        Attributes
        ----------
        is_test : Whether add test text to before reply text.
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
        self.window = window
        self.file: MessageParameterFile | None = None
        self.trigger_rule: TriggerRule | None = None
        self.trigger_continue = self.receiver.trigger.continue_
        self.trigger_break = self.receiver.trigger.break_
        self.replied: bool = False
        self.exc_reports: list[str] = []
        self.is_test: bool = False

        ## Room and user.
        if self.window.endswith('chatroom'):
            self.room = self.window
            if ':\n' in self.data:
                self.user, self.data = self.data.split(':\n', 1)
                if self.user == self.room:
                    self.user = None
            else:
                self.user = None
        else:
            self.room = None
            self.user = self.window

        ## Cache.
        self._user_name: str | None = None
        self._room_name: str | None = None
        self._window_name: str | None = None
        self._text: str | None = None
        self._voice_len: float | None = None
        self._video_len: int | None = None
        self._business_card_name: str | None = None

        ### Share.
        self._share_type: int | None = None
        self._share_params: MessageShareParameter | None = None
        self._is_file_uploading: bool | None = None
        self._file_name_uploading: str | None = None
        self._is_file_uploaded: bool | None = None
        self._is_forward: bool | None = None
        self._is_mini_program: bool | None = None
        self._is_quote: bool | None = None
        self._is_quote_me: bool | None = None
        self._quote_params: dict[Literal['text', 'quote_id', 'quote_type', 'quote_user', 'quote_user_name', 'quote_data'], str] | None = None
        self._is_money: bool | None = None
        self._money_amount: float | None = None
        self._is_app: bool | None = None

        self._at_names: list[str] = None
        self._is_at: bool | None = None
        self._is_at_me: bool | None = None
        self._is_call: bool | None = None
        self._call_text: str | None = None
        self._is_call_next: bool | None = None
        self._is_last_call: bool | None = None
        self._is_pat: bool | None = None
        self._is_pat_me: bool | None = None
        self._pat_text: str | None = None
        self._is_recall: bool | None = None
        self._is_new_user: bool | None = None
        self._is_new_room: bool | None = None
        self._is_new_room_user: bool | None = None
        self._new_room_user_name: str | None = None
        self._is_change_room_name: bool | None = None
        self._change_room_name: str | None = None
        self._is_kick_out_room: bool | None = None
        self._is_dissolve_room: bool | None = None
        self._image_qrcodes: list[str] | None = None
        self._is_html: bool | None = None
        self._is_xml: bool | None = None
        self._valid: bool | None = None

        ## Update call next.
        self.is_call_next


    @property
    def params(self) -> MessageParameter:
        """
        Return parameters dictionary.

        Returns
        -------
        Parameters dictionary.
        """

        # Handle parameter.
        params: MessageParameter = {
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

        # Cache.
        if self._user_name is not None:
            return self._user_name

        # Set.
        self._user_name = self.receiver.wechat.client.get_contact_name(
            self.user
        )

        return self._user_name


    @property
    def room_name(self) -> str | None:
        """
        Message sender chat room name.

        Returns
        -------
        Chat room name.
        """

        # Break.
        if self.room is None:
            return

        # Cache.
        if self._room_name is not None:
            return self._room_name

        # Set.
        self._room_name = self.receiver.wechat.client.get_contact_name(
            self.room
        )

        return self._room_name


    @property
    def window_name(self) -> str:
        """
        Message sender window name.

        Returns
        -------
        Window name.
        """

        # Cache.
        if self._window_name is not None:
            return self._window_name

        # Set.
        if self.room is None:
            self._window_name = self.user_name
        else:
            self._window_name = self.room_name

        return self._window_name


    @property
    def text(self) -> str:
        """
        Text description of message content.

        Returns
        -------
        Text.
        """

        # Cache.
        if self._text is not None:
            return self._text

        # Get.
        match self.type:

            ## Text.
            case 1:
                self._text = self.data

            ## Image.
            case 3:
                self._text = '[图片]'

            ## Voice.
            case 34:
                voice_len = round(self.voice_len, 1)
                self._text = f'[{voice_len}秒的语音]'

            ## New firend invitation.
            case 37:
                self._text = '[新好友邀请]'

            ## Business card.
            case 42:
                self._text = f'[分享名片"{self.business_card_name}"]'

            ## Video.
            case 43:
                self._text = f'[{self.video_len}秒的视频]'

            ## Emoticon.
            case 47:
                self._text = f'[动画表情]'

            ## Position.
            case 48:
                self._text = '[地图位置分享]'

            ## Share.
            case 49:

                ### Pure URL text.
                if self.share_type == 1:
                    self._text = '[网址]'
                    if self.share_params['title'] is not None:
                        self._text += f' {self.share_params['title']}'

                ### File uploaded.
                elif self.is_file_uploaded:
                    self._text = f'[文件"{self.file['name']}"发送完成]'

                ### Initiate real time location.
                elif self.share_type == 17:
                    self._text = '[开始实时地图位置分享]'

                ### Forword messages.
                elif self.is_forword:
                    if self.share_params['title'] is None:
                        self._text = '[转发聊天记录]'
                    else:
                        self._text = f'[转发"{self.share_params['title']}"]'
                    if self.share_params['des'] is not None:
                        self._text += f' {self.share_params['des']}'

                ### Mini program.
                elif self.is_mini_program:
                    if self.share_params['name'] is None:
                        self._text = '[小程序分享]'
                    else:
                        self._text = f'[小程序"{self.share_params['name']}"分享]'
                    if self.share_params['title'] is not None:
                        self._text += f' {self.share_params['title']}'

                ### Video channel.
                elif self.share_type == 51:
                    if self.share_params['name'] is None:
                        self._text = '[视频号分享]'
                    else:
                        self._text = f'[视频号"{self.share_params['name']}"分享]'
                    if self.share_params['title'] is not None:
                        self._text += f' {self.share_params['title']}'

                ### Quote.
                elif self.is_quote:
                    self._text = f'[引用了"{self.quote_params['quote_user_name']}"的消息并发言] {self.quote_params['text']}'

                ### Quote me.
                elif self.is_quote_me:
                    self._text = f'[引用了你的消息并发言] {self.quote_params['text']}'

                ### File uploading.
                elif self.is_file_uploading:
                    self._text = f'[文件"{self.file_name_uploading}"发送中]'

                ### Transfer money.
                elif self.is_money:
                    self._text = f'[转账{self.money_amount}￥]'

                ### App.
                elif self.is_app:
                    if self.share_params['name'] is None:
                        self._text = '[APP分享]'
                    else:
                        self._text = f'[APP"{self.share_params['name']}"分享]'
                    if self.share_params["title"] is not None:
                        self._text += f' {self.share_params["title"]}'
                    if self.share_params["des"] is not None:
                        self._text += f' {self.share_params["des"]}'

                ### Other.
                else:
                    if self.share_params['name'] is None:
                        self._text = '[分享]'
                    else:
                        self._text = f'["{self.share_params['name']}"分享]'
                    if self.share_params["title"] is not None:
                        self._text += f' {self.share_params["title"]}'
                    if self.share_params["des"] is not None:
                        self._text += f' {self.share_params["des"]}'

            ## Voice call or video call.
            case 50:
                self._text = '[视频或语音通话]'

            ## System sync.
            case 51:
                self._text = '[系统同步]'

            ## Real time position.
            case 56:
                self._text = '[实时地图位置分享中]'

            ## System.
            case 10000:
                self._text = '[系统信息]'

            ## Pat.
            case 10002 if self.is_pat:
                self._text = f'[{self.pat_text}]'

            ## Recall.
            case 10002 if self.is_recall:
                self._text = '[撤回了一条消息]'

            case _:
                self._text = '[消息]'

        return self._text


    @property
    def voice_len(self) -> float:
        """
        Voice message length, unit is seconds.

        Returns
        -------
        Voice message length.
        """

        # Cache.
        if self._voice_len is not None:
            return self._voice_len

        # Check.
        if self.type != 34:
            throw(AssertionError, self.type)

        # Get.
        pattern = r'voicelength="(\d+)"'
        voice_len_us_str = search(pattern, self.data)
        self._voice_len = int(voice_len_us_str) / 1000

        return self._voice_len


    @property
    def video_len(self) -> int:
        """
        Video message length, unit is seconds.

        Returns
        -------
        Video message length.
        """

        # Cache.
        if self._video_len is not None:
            return self._video_len

        # Check.
        if self.type != 43:
            throw(AssertionError, self.type)

        # Get.
        pattern = r'playlength="(\d+)"'
        video_len_s_str = search(pattern, self.data)
        self._video_len = int(video_len_s_str)

        return self._video_len


    @property
    def business_card_name(self) -> str:
        """
        Nickname of business card message.

        Returns
        -------
        Voice message length.
        """

        # Cache.
        if self._business_card_name is not None:
            return self._business_card_name

        # Check.
        if self.type != 42:
            throw(AssertionError, self.type)

        # Get.
        pattern = r'nickname="([^"]+)"'
        self._business_card_name = search(pattern, self.data)

        return self._business_card_name


    @property
    def share_type(self) -> int:
        """
        Type number of share message.

        Returns
        -------
        Type number.
        """

        # Cache.
        if self._share_type is not None:
            return self._share_type

        # Check.
        if self.type != 49:
            throw(AssertionError, self.type)

        # Get.
        pattern = r'<type>(\d+)</type>'
        share_type_str: str = search(pattern, self.data)
        self._share_type = int(share_type_str)

        return self._share_type


    @property
    def share_params(self) -> MessageShareParameter:
        """
        Share message parameters.

        Returns
        -------
        Parameters.
        """

        # Cache.
        if self._share_params is not None:
            return self._share_params

        # Check.
        if self.type != 49:
            throw(AssertionError, self.type)

        # Extract.
        name: str | None = search('.*<appname>([^<>]+)</appname>', self.data)
        if name is None:
            name: str | None = search('.*<sourcedisplayname>([^<>]+)</sourcedisplayname>', self.data)
        if name is None:
            name: str | None = search('.*<nickname>([^<>]+)</nickname>', self.data)
        title: str | None = search('<title>([^<>]+)</title>', self.data)
        des: str | None = search('.*<des>([^<>]+)</des>', self.data)
        if des is None:
            des: str | None = search('.*<desc>([^<>]+)</desc>', self.data)
        url: str | None = search('.*<url>([^<>]+)</url>', self.data)
        self._share_params: MessageShareParameter = {
            'name': name,
            'title': title,
            'des': des,
            'url': url
        }

        return self._share_params


    @property
    def is_file_uploading(self) -> bool:
        """
        Whether if is share message of other side file uploading.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_file_uploading is not None:
            return self._is_file_uploading

        # Judge.
        self._is_file_uploading = (
            self.type == 49
            and self.share_type == 74
        )

        return self._is_file_uploading


    @property
    def file_name_uploading(self) -> str:
        """
        Name of file uploading.

        Returns
        -------
        Text
        """

        # Cache.
        if self._file_name_uploading is not None:
            return self._file_name_uploading

        # Check.
        if not self.is_file_uploading:
            throw(AssertionError, self._is_file_uploading)

        # Get.
        self._file_name_uploading: str = search(r'<title><!\[CDATA\[([^<>]+)\]\]></title>', self.data)

        return self._file_name_uploading


    @property
    def is_file_uploaded(self) -> bool:
        """
        Whether if is share message of other side file uploaded.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_file_uploaded is not None:
            return self._is_file_uploaded

        # Judge.
        self._is_file_uploading = (
            self.type == 49
            and self.share_type == 6
        )

        return self._is_file_uploaded


    @property
    def is_forword(self) -> bool:
        """
        Whether if is share message of forward messages.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_forward is not None:
            return self._is_forward

        # Judge.
        self._is_forward = (
            self.type == 49
            and self.share_type in (19, 40)
        )

        return self._is_forward


    @property
    def is_mini_program(self) -> bool:
        """
        Whether if is share message of mini program.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_mini_program is not None:
            return self._is_mini_program

        # Judge.
        self._is_mini_program = (
            self.type == 49
            and self.type == 33
        )

        return self._is_mini_program


    @property
    def is_quote(self) -> bool:
        """
        Whether if is share message of quote.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_quote is not None:
            return self._is_quote

        # Judge.
        self._is_quote = (
            self.type == 49
            and self.share_type == 57
        )

        return self._is_quote


    @property
    def is_quote_me(self) -> bool:
        """
        Whether if is share message of quote me.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_quote_me is not None:
            return self._is_quote_me

        # Judge.
        self._is_quote_me = (
            self.is_quote
            and '<chatusr>%s</chatusr>' % self.receiver.wechat.client.login_info['id'] in self.data
        )

        return self._is_quote_me


    @property
    def quote_params(self) -> MessageQuoteParameter:
        """
        Quote message parameters.

        Returns
        -------
        Quote parameters of message.
            - `Key 'text'`: Message text.
            - `Key 'quote_id'`: Quote message ID.
            - `Key 'quote_time'`: Quote message timestamp, unit is seconds.
            - `Key 'quote_type'`: Quote message type.
            - `Key 'quote_user'`: Quote message user ID.
            - `Key 'quote_user_name'`: Quote message user name.
            - `Key 'quote_data'`: Quote message data.
        """

        # Cache.
        if self._quote_params is not None:
            return self._quote_params

        # Check.
        if not self.is_quote:
            throw(AssertionError, self._is_quote)

        # Extract.
        pattern = '<title>(.+?)</title>'
        text: str = search(pattern, self.data)
        pattern = r'<svrid>(\w+?)</svrid>'
        quote_id = search(pattern, self.data)
        quote_id = int(quote_id)
        pattern = r'<createtime>(\d{10})</createtime>'
        quote_time = search(pattern, self.data)
        quote_time = int(quote_time)
        pattern = r'<refermsg>\s*<type>(\d+?)</type>'
        quote_type = search(pattern, self.data)
        quote_type = int(quote_type)
        pattern = r'<chatusr>(\w+?)</chatusr>'
        quote_user: str = search(pattern, self.data)
        pattern = '<displayname>(.+?)</displayname>'
        quote_user_name: str = search(pattern, self.data)
        pattern = '<content>(.+?)</content>'
        quote_data: str = search(pattern, self.data)
        self._quote_params: MessageQuoteParameter = {
            'text': text,
            'quote_id': quote_id,
            'quote_time': quote_time,
            'quote_type': quote_type,
            'quote_user': quote_user,
            'quote_user_name': quote_user_name,
            'quote_data': quote_data
        }

        return self._quote_params


    @property
    def is_money(self) -> bool:
        """
        Whether if is message of transfer money.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_money is not None:
            return self._is_money

        # Judge.
        self._is_money = (
            self.type == 49
            and self.share_type == 2000
        )

        return self._is_money


    @property
    def money_amount(self) -> float:
        """
        Transfer money amount.

        Returns
        -------
        Amount.
        """

        # Cache.
        if self._money_amount is not None:
            return self._money_amount

        # Check.
        if not self.is_money:
            throw(AssertionError, self._is_money)

        # Judge.
        amount_str: str = search(r'<feedesc><!\[CDATA\[￥([\d.,]+)\]\]></feedesc>', self.data)
        self._money_amount = float(amount_str)

        return self._money_amount


    @property
    def is_app(self) -> bool:
        """
        Whether if is application share.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_app is not None:
            return self._is_app

        # Judge.
        self._is_app = (
            self.type == 49
            and search('<appname>[^<>]+</appname>', self.data) is not None
        )

        return self._is_app


    @property
    def at_names(self) -> list[str]:
        """
        Return `@` names.

        Returns
        -------
        `@` names.
        """

        # Cache.
        if self._at_names is not None:
            return self._at_names

        # Get.
        if self.type == 1:
            text = self.data
        elif self.is_quote:
            text = self.quote_params['text']
        pattern = r'@(\w+)\u2005'
        self._at_names = findall(pattern, text)

        return self._at_names


    @property
    def is_at(self) -> bool:
        """
        Whether if is `@` message.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_at is not None:
            return self._is_at

        # Judge.
        self._is_at = self.at_names != []

        return self._is_at


    @property
    def is_at_me(self) -> bool:
        """
        Whether if is message of `@` me.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_at_me is not None:
            return self._is_at_me

        # Judge.
        self._is_at_me = self.receiver.wechat.client.login_info['name'] in self.at_names

        return self._is_at_me


    @property
    def is_call(self) -> bool:
        """
        Whether if is message of call self name.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_call is not None:
            return self._is_call

        # Judge.
        self._is_call = (

            ## Last call.
            self.is_last_call

            ## Private chat.
            or (
                self.room is None
                and self.user is not None
            )

            ## Pat me.
            or self.is_pat_me

            ## At self.
            or '@%s\u2005' % self.receiver.wechat.client.login_info['name'] in self.data

            ## Call self.
            or self.data.lstrip().startswith(self.receiver.call_name)

            ## Quote me.
            or self.is_quote_me

        )

        return self._is_call


    @property
    def call_text(self) -> str:
        """
        Message call text of call self name.

        Returns
        -------
        Call text.
        """

        # Cache.
        if self._call_text is not None:
            return self._call_text

        # Check.
        if not self.is_call:
            throw(AssertionError, self._is_call)

        # Get.
        text = self.text

        ## Replace.

        ### At.
        at_me_keyword = '@%s\u2005' % self.receiver.wechat.client.login_info['name']
        text = text.replace(at_me_keyword, '')

        ### Call.
        pattern = fr'^\s*{self.receiver.call_name}[\s,，]*(.*)$'
        result: str | None = search(pattern, text)
        if result is not None:
            text = result

        text = text.strip()

        return self._call_text


    @property
    def is_call_next(self) -> bool:
        """
        Whether if is message of call next message.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_call_next is not None:
            return self._is_call_next

        # Judge.
        self._is_call_next = (
            self.room is not None
            and self.is_call
            and self.call_text == ''
        )

        ### Mark.
        if self._is_call_next:
            call_next_mark_value = f'{self.user}_{self.room}'
            self.receiver.mark(call_next_mark_value, 'is_call_next')

        return self._is_call_next


    @property
    def is_last_call(self) -> bool:
        """
        Whether if is message of last message call this time.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_last_call is not None:
            return self._is_last_call

        # Judge.
        call_next_mark_value = f'{self.user}_{self.room}'
        self._is_last_call = self.receiver.mark.is_marked(call_next_mark_value, 'is_call_next')

        # Mark.
        if self._is_last_call:
            call_next_mark_value = f'{self.user}_{self.room}'
            self.receiver.mark.remove(call_next_mark_value, 'is_call_next')

        return self.is_last_call


    @property
    def is_pat(self) -> bool:
        """
        Whether if is message of pat.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_pat is not None:
            return self._is_pat

        # Judge.
        self._is_pat = (
            self.type == 10002
            and self.data.startswith('<sysmsg type="pat">')
        )

        return self._is_pat


    @property
    def is_pat_me(self) -> bool:
        """
        Whether if is message of pat me.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_pat_me is not None:
            return self._is_pat_me

        # Judge.
        pattern = r'<template><!\[CDATA\["\$\{[\da-z_]+\}" 拍了拍我\]\]></template>'
        self._is_pat_me = (
            self.is_pat
            and search(pattern, self.data) is not None
        )

        return self._is_pat_me


    @property
    def pat_text(self) -> str:
        """
        Text of pat message.

        Returns
        -------
        Text
        """

        # Cache.
        if self._pat_text is not None:
            return self._pat_text

        # Check.
        if not self.is_pat:
            throw(AssertionError, self._is_pat)

        # Get.

        ## Text.
        pattern = r'<template><!\[CDATA\[([^<>]+)\]\]></template>'
        text: str = search(pattern, self.data)

        ## User name.
        pattern = r'"\$\{([\da-z_]+)\}"'
        users_id: list[str] = findall(pattern, text)
        for user_id in users_id:
            user_name = self.receiver.wechat.client.get_contact_name(user_id)
            old_text = '${%s}' % user_id
            text = text.replace(old_text, user_name)

        self._pat_text = text

        return self._pat_text


    @property
    def is_recall(self) -> bool:
        """
        Whether if is message of recall.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_recall is not None:
            return self._is_recall

        # Judge.
        self._is_recall = (
            self.type == 10002
            and self.data.startswith('<sysmsg type="revokemsg">')
        )

        return self._is_recall


    @property
    def is_new_user(self) -> bool:
        """
        Whether if is new user.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_new_user is not None:
            return self._is_new_user

        # Judge.
        self._is_new_user = (
            self.type == 10000
            and (
                self.data == '以上是打招呼的内容'
                or self.data.startswith('你已添加了')
                or self.data.endswith('，现在可以开始聊天了。')
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

        # Cache.
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

        # Cache.
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
        result: str = search(pattern, self.data)
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

        # Cache.
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
        result: str = search(pattern, self.data)
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

        # Cache.
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

        # Cache.
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
    def image_qrcodes(self) -> list[str]:
        """
        Return image QR code texts.

        Returns
        -------
        Image QR code texts.
        """

        # Cache.
        if self._image_qrcodes is not None:
            return self._image_qrcodes

        # Check.
        if self.type != 3:
            throw(AssertionError, self.type)

        # Extract.
        self._image_qrcodes = decode_qrcode(self.file['path'])

        return self._image_qrcodes


    @property
    def is_html(self) -> bool:
        """
        Whether if is HTML format.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_html is not None:
            return self._is_html

        # Judge.
        self._is_html = (
            self.type != 1
            and search(r'^<(\S+)[ >].*</\1>\s*', self.data) is not None
        )

        return self._is_html


    @property
    def is_xml(self) -> bool:
        """
        Whether if is XML format.

        Returns
        -------
        Judge result.
        """

        # Cache.
        if self._is_xml is not None:
            return self._is_xml

        # Judge.
        self._is_xml = (
            self.type != 1
            and self.data.startswith('<?xml ')
            and self.data.rstrip().endswith('</msg>')
        )

        return self._is_xml


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
        self._valid = self.receiver.wechat.database.is_valid(self)

        return self._valid


    def check_call(self) -> None:
        """
        Check if is call self name, if not, throw exception `WeChatTriggerContinueExit`.
        """

        # Check.
        if not self.is_call:
            self.trigger_continue()


    def check_search_text(self, *patterns: str, text: str | None = None) -> str | tuple[str | None, ...]:
        """
        Regular search text, return first successful match.
        When no match, then throw exception `WeChatTriggerContinueExit`.

        Parameters
        ----------
        pattern : Regular pattern, period match any character.
        text : Match text.
            - `None`: Use `self.data`.

        Returns
        -------
        Matching result.
            - When match to and not use `group`, then return `str`.
            - When match to and use `group`, then return tuple with value `str` or `None`.
                If tuple length is `1`, extract and return `str`.
            - When no match, then return `None`.
        """

        # Handle parameter.
        text = text or self.data

        # Search.
        result = search_batch(text, *patterns)

        # Check.
        if result is None:
            self.trigger_continue()

        return result


    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendTypeEnum.TEXT],
        *,
        text: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendTypeEnum.TEXT_AT],
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendTypeEnum.FILE, WeChatSendTypeEnum.IMAGE, WeChatSendTypeEnum.EMOTION],
        *,
        path: str,
        file_name: str | None = None
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendTypeEnum.PAT],
        *,
        user_id: str
    ) -> None: ...

    @overload
    def reply(
        self,
        send_type: Literal[WeChatSendTypeEnum.PUBLIC],
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
        send_type: Literal[WeChatSendTypeEnum.FORWARD],
        *,
        message_id: str
    ) -> None: ...

    def reply(
        self,
        send_type: WeChatSendTypeEnum,
        **params: Any
    ) -> None:
        """
        Send reply message.

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
        params : Send parameters.
        """

        # Check.
        if (
            self.trigger_rule is None
            or not self.trigger_rule['is_reply']
        ):
            text = 'can only be used by reply trigger'
            throw(WeChatTriggerError, self.trigger_rule, text=text)

        # Test.
        if (
            self.is_test
            and send_type in (WeChatSendTypeEnum.TEXT, WeChatSendTypeEnum.TEXT_AT)
        ):
            message_time = time_to(to_time(self.time).time())
            receive_time = now('time_str')
            send_time = ':time:'
            test_text = f'{message_time} M\n{receive_time} R\n{send_time} S'
            if params['text'] == '':
                params['text'] = test_text
            else:
                params['text'] = f'{test_text}\n\n{params['text']}'
            params['is_test'] = True

        # Status.
        self.replied = True

        # Send.
        self.receiver.wechat.sender.send(
            send_type,
            receive_id=self.window,
            **params
        )


class WechatReceiver(WeChatBase):
    """
    WeChat receiver type.
    """


    def __init__(
        self,
        wechat: WeChat,
        max_receiver: int,
        call_name: str | None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChatClient` instance.
        max_receiver : Maximum number of receivers.
        call_name : Trigger call name.
            - `None`: Use account nickname.
        """

        # Import.
        from .rtrigger import WeChatTrigger

        # Set attribute.
        self.wechat = wechat
        self.max_receiver = max_receiver
        call_name = call_name or self.wechat.client.login_info['name']
        self.call_name = call_name
        self.queue: Queue[WeChatMessage] = Queue()
        self.handlers: list[Callable[[WeChatMessage], Any]] = []
        self.started: bool | None = False
        self.mark = Mark()
        self.trigger = WeChatTrigger(self)

        # Start.
        self.__start_callback()
        self.__start_receiver(self.max_receiver)
        self.wechat.client.hook_message(
            '127.0.0.1',
            self.wechat.client.message_callback_port,
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
            self.wechat.client.message_callback_port,
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
                self.__receiver_handler_file,
                *self.handlers
            ]

            # Handle.

            ## Define.
            def handle_handler_exception(exc_text, *_) -> None:
                """
                Handle Handler exception.

                Parameters
                ----------
                exc_text : Exception report text.
                """

                # Save.
                message.exc_reports.append(exc_text)


            ## Loop.
            for handler in handlers:
                handler = wrap_exc(handler, handler=handle_handler_exception)
                handler(message)

            # Log.
            self.wechat.error.log_receive(message)


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


    def __receiver_handler_file(
        self,
        message: WeChatMessage
    ) -> None:
        """
        Handle file message.
        """

        # Download.
        match message.type:

            ## Image.
            case 3:
                pattern = r' md5="([\da-f]{32})"'
                file_md5: str = search(pattern, message.data)
                file_name = f'{file_md5}.jpg'
                cache_path = self.wechat.cache.index(file_md5, file_name, copy=True)

                ### Download.
                if cache_path is None:
                    self.wechat.client.download_file(message.id)
                    download_path = '%swxhelper/image/%s.dat' % (
                        self.wechat.client.login_info['account_data_path'],
                        message.id
                    )

            ## Voice.
            case 34:
                file_name = None
                file_name_suffix = 'amr'
                cache_path = None

                ### Download.
                self.wechat.client.download_voice(
                    message.id,
                    self.wechat.cache.folder.path
                )
                download_path = self.wechat.cache.folder + f'{message.id}.amr'

            ## Video.
            case 43:
                pattern = r' md5="([\da-f]{32})"'
                file_md5: str = search(pattern, message.data)
                file_name = f'{file_md5}.mp4'
                cache_path = self.wechat.cache.index(file_md5, file_name, copy=True)

                ### Download.
                if cache_path is None:
                    self.wechat.client.download_file(message.id)
                    download_path = '%swxhelper/video/%s.mp4' % (
                        self.wechat.client.login_info['account_data_path'],
                        message.id
                    )

            ## Other.
            case 49 if message.is_file_uploaded:
                pattern = r'<md5>([\da-f]{32})</md5>'
                file_md5: str = search(pattern, message.data)
                cache_path = self.wechat.cache.index(file_md5, file_name, copy=True)

                ### Download.
                if cache_path is None:
                    self.wechat.client.download_file(message.id)
                    download_path = '%swxhelper/file/%s_%s' % (
                        self.wechat.client.login_info['account_data_path'],
                        message.id,
                        file_name
                    )

            ## Break.
            case _:
                return

        if cache_path is None:

            ## Wait.
            wait(
                os_exists,
                download_path,
                _interval = 0.05,
                _timeout=3600
            )
            sleep(0.2)

            ## Cache.
            download_file = File(download_path)
            file_name = file_name or f'{download_file.md5}.{file_name_suffix}'
            cache_path = self.wechat.cache.store(download_path, file_name, delete=True)

        # Set parameter.
        cache_file = File(cache_path)
        message_file: MessageParameterFile = {
            'path': cache_path,
            'name': cache_file.name_suffix,
            'md5': cache_file.md5,
            'size': cache_file.size
        }
        message.file = message_file


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
