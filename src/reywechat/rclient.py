# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Client methods.
"""


from typing import Any, TypedDict, Literal, Final
from os.path import abspath as os_abspath
from reykit.rbase import throw
from reykit.rdll import inject_dll
from reykit.rnet import request as reykit_request
from reykit.ros import find_relpath
from reykit.rsys import run_cmd, search_process, memory_read, memory_write, popup_select
from reykit.rtime import wait

from .rbase import WeChatBase, WeChatClientErorr
from .rwechat import WeChat


__all__ = (
    'CLIENT_VERSION_MEMORY_OFFSETS',
    'WeChatClient',
    'simulate_client_version'
)


WeChatResponse = TypedDict('WeChatResponse', {'code': int, 'message': str, 'data': Any})


CLIENT_VERSION_MEMORY_OFFSETS = (
    61280212,
    61372636,
    61474056,
    61638128,
    61666264,
    61674264,
    61675784
)


class WeChatClient(WeChatBase):
    """
    WeChat client type.
    """


    # Environment.
    client_version: Final[str] = '3.9.5.81'
    client_version_int: Final[int] = 1661535569
    client_version_simulate: Final[str] = '3.10.0.1'
    client_version_simulate_int: Final[int] = 1661599745
    client_api_port: Final[int] = 19088
    message_callback_port: Final[int] = 19089


    def __init__(
        self,
        wechat: WeChat
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChat` instance.
        """

        # Start.
        self.wechat = wechat
        self.start_api()

        # Set attribute.
        self.login_info = self.get_login_info()


    def start_api(self) -> None:
        """
        Start client control API.
        """

        # Check client started.
        judge = self.check_client_started()

        ## Start client.
        if not judge:
            wechat_path = popup_select(
                title='请选择微信客户端',
                filter_file=[('', ['*微信*.exe', '*WeChat*.exe'])]
            )
            if wechat_path is None:
                raise WeChatClientErorr('WeChat client not started')
            run_cmd(wechat_path)

            ## Wait.
            seconds = wait(
                self.check_client_started,
                _interval=0.2,
                _timeout=10,
                _raising=False
            )
            if seconds is None:
                raise WeChatClientErorr('WeChat client not started')

        # Check client version.
        judge = self.check_client_version()
        if not judge:
            raise WeChatClientErorr(f'WeChat client version failed, must be "{self.client_version}"')

        # Check API.
        judge = self.check_api()
        if not judge:

            # Inject DLL.
            self.inject_dll()

            # Check api.
            judge = self.check_api()
            if not judge:
                raise WeChatClientErorr('start WeChat client API failed')

        # Check client login.
        judge = self.check_client_login()
        if not judge:
            print('Please login WeChat.')

            ## Wait.
            seconds = wait(
                self.check_client_login,
                _interval=0.5,
                _timeout=30,
                _raising=False
            )
            if seconds is None:
                raise WeChatClientErorr('WeChat not logged in')

        # Report.
        print('Start WeChat client API successfully, address is "127.0.0.1:19088".')


    def check_client_started(self) -> bool:
        """
        Check if the client is started.

        Returns
        -------
        Check result.
        """

        # Search.
        processes = search_process(name='WeChat.exe')

        # Check.
        if processes == []:
            return False
        else:
            return True


    def check_client_version(self) -> bool:
        """
        Check if the client version.

        Returns
        -------
        Check result.
        """

        # Check.
        for offset in CLIENT_VERSION_MEMORY_OFFSETS:
            value = memory_read(
                'WeChat.exe',
                'WeChatWin.dll',
                offset
            )
            if value not in (
                self.client_version_int,
                self.client_version_simulate_int,
                0
            ):
                return False

        return True


    def check_api(self) -> bool:
        """
        Check if the client API is started.
        """

        # Search.
        processes = search_process(port=self.client_api_port)

        # Check.
        if processes == []:
            return False
        process = processes[0]
        with process.oneshot():
            process_name = process.name()
        if process_name != 'WeChat.exe':
            return False

        return True


    def inject_dll(self) -> None:
        """
        Inject DLL file of start API into the WeChat client process.
        """

        # Parameter.
        dll_file_relpath = './data/client_api.dll'
        dll_file_path = find_relpath(__file__, dll_file_relpath)

        # Inject.
        processes = search_process(name='WeChat.exe')
        process = processes[0]
        inject_dll(
            process.pid,
            dll_file_path
        )


    def request(
        self,
        api: str,
        data: dict | None = None,
        success_code: int | list[int] | None = None,
        fail_code: int | list[int] | None = None
    ) -> WeChatResponse:
        """
        Request client API.

        Parameters
        ----------
        api : API name.
        data : Request data.
        success_code : Suceess code, if not within the range, throw an exception.
            - `None`: Not handle.
            - `int | list[int]`: Handle.
        fail_code : Fail code, if within the range, throw an exception.
            - `None`: Not handle.
            - `int | list[int]`: Handle.

        Returns
        -------
        Client response content dictionary.
        """

        # Parameter.
        url = f'http://127.0.0.1:{self.client_api_port}/api/{api}'
        data = data or {}
        if type(success_code) == int:
            success_code = [success_code]
        if type(fail_code) == int:
            fail_code = [fail_code]

        # Request.
        response = reykit_request(
            url,
            json=data,
            method='post',
            check=True
        )

        # Extract.
        response_data = response.json()
        response = {
            'code': response_data['code'],
            'message': response_data['msg'],
            'data': response_data['data']
        }

        # Throw exception.
        if (
            (
                success_code is not None
                and response['code'] not in success_code
            ) or (
                fail_code is not None
                and response['code'] in fail_code
            )
        ):
            raise WeChatClientErorr(f'client API "{api}" request failed', data, response)

        return response


    def check_client_login(self) -> bool:
        """
        Check if the client is logged in.

        Returns
        -------
        Check result.
        """

        # Parameter.
        api = 'checkLogin'

        # Request.
        response = self.request(api)

        # Check.
        match response['code']:
            case 1:
                return True
            case 0:
                return False


    def get_login_info(
        self
    ) -> dict[
        Literal[
            'id',
            'account',
            'name',
            'phone',
            'signature',
            'city',
            'province',
            'country',
            'head_image',
            'account_data_path',
            'wechat_data_path',
            'decrypt_key'
        ],
        str | None
    ]:
        """
        Get login account information.

        Returns
        -------
        Login user account information.
            - `Key 'id'`: User ID, cannot change.
            - `Key 'account'`: User account, can change.
            - `Key 'name'`: User nickname.
            - `Key 'phone'`: Phone number.
            - `Key 'signature'`: Personal signature.
            - `Key 'city'`: City.
            - `Key 'province'`: Province.
            - `Key 'country'`: Country.
            - `Key 'head_image'`: Head image URL.
            - `Key 'account_data_path'`: Current account data save path.
            - `Key 'wechat_data_path'`: WeChat data save path.
            - `Key 'decrypt_key'`: Database decrypt key.
        """

        # Parameter.
        api = 'userInfo'

        # Request.
        response = self.request(api)

        # Extract.
        data = response['data']
        info = {
            'id': data['wxid'],
            'account': data['account'],
            'name': data['name'],
            'phone': data['mobile'],
            'signature': data['signature'],
            'city': data['city'],
            'province': data['province'],
            'country': data['country'],
            'head_image': data['headImage'],
            'account_data_path': data['currentDataPath'],
            'wechat_data_path': data['dataSavePath'],
            'decrypt_key': data['dbKey']
        }
        info = {
            key: (
                None
                if value == ''
                else value
            )
            for key, value in info.items()
        }

        return info


    def hook_message(
        self,
        host: str,
        port: str | int,
        timeout: float
    ) -> None:
        """
        Hook the message, and send the message to the TCP protocol request.

        Parameters
        ----------
        host : Request host.
        port : Request port.
        timeout : Request timeout seconds.
        """

        # Parameter.
        api = 'hookSyncMsg'
        port = str(port)
        timeout_ms_str = str(int(timeout * 1000))
        data = {
            'ip': host,
            'port': port,
            'timeout': timeout_ms_str,
            'enableHttp': '0'
        }

        # Request.
        response = self.request(api, data, [0, 2])

        # Retry.
        if response['code'] == 2:
            self.unhook_message()
            self.hook_message(
                host,
                port,
                timeout
            )

        # Report.
        else:
            print(
                'Hook message successfully, address is "%s:%s".' % (
                    host,
                    port
                )
            )


    def unhook_message(self) -> None:
        """
        Unhook the message.
        """

        # Parameter.
        api = 'unhookSyncMsg'

        # Request.
        self.request(api, success_code=0)

        # Report.
        print('Unhook message successfully.')


    def download_file(
        self,
        id_: int
    ) -> None:
        """
        Download image or video or other file.

        Parameters
        ----------
        id\\_ : Message ID.
        """

        # Parameter.
        api = 'downloadAttach'
        data = {'msgId': id_}

        # Request.
        self.request(api, data, [0, 1000])


    def download_voice(
        self,
        id_: int,
        dir_: str
    ) -> None:
        """
        Download voice.

        Parameters
        ----------
        id\\_ : Message ID.
        dir\\_ : Save directory.
        """

        # Parameter.
        api = 'getVoiceByMsgId'
        dir_ = os_abspath(dir_)
        data = {
            'msgId': id_,
            'storeDir': dir_
        }

        # Request.
        self.request(api, data, [0, 1])


    def get_contact_table(
        self,
        type_: Literal['user', 'room'] | None = None
    ) -> list[dict[Literal['id', 'name'], str]]:
        """
        Get contact table, include chat user and chat room.

        Parameters
        ----------
        type\\_ : Return contact table type.
            - `None`: Return all contact table.
            - `Literal['user']`: Return user contact table.
            - `Literal['room']`: Return chat room contact table.

        Returns
        -------
        Contact table.
            - `Key 'id'`: User ID or chat room ID.
            - `Key 'name'`: User nickname or chat room name.
        """

        # Parameter.
        api = 'getContactList'
        filter_names = {
            'filehelper': '朋友推荐消息',
            'floatbottle': '语音记事本',
            'fmessage': '漂流瓶',
            'medianote': '文件传输助手'
        }

        # Request.
        response = self.request(api, success_code=1)

        # Extract.
        data: list[dict] = response['data']
        table_user = []
        table_room = []
        for info in data:
            id_: str = info['wxid']

            # Filter system user.
            if id_ in filter_names:
                continue

            # Split table.
            row = {
                'id': id_,
                'name': info['nickname']
            }

            ## Chat room table.
            if id_.endswith('chatroom'):
                if (
                    type_ in (None, 'room')
                    and id_[-1] == 'm'
                ):
                    table_room.append(row)

            ## User table.
            else:
                if type_ in (None, 'user'):
                    table_user.append(row)

        # User no name.
        for row in table_user[::-1]:
            if row['name'] == '':
                table_user.remove(row)

        # Merge table.
        table = table_user + table_room

        return table


    def get_contact_name(
        self,
        id_: str
    ) -> str:
        """
        Get contact name, can be friend and chat room and chat room member.

        Parameters
        ----------
        id\\_ : User ID or chat room ID.

        Returns
        -------
        User nickname or chat room name.
        """

        # Parameter.
        api = 'getContactProfile'
        data = {'wxid': id_}

        # Request.
        response = self.request(api, data, [0, 1])

        # Extract.
        data: dict | None = response['data']
        if data is None:
            name = None
        else:
            name = data['nickname']

        return name


    def get_room_member_list(
        self,
        room_id: str
    ) -> list[str]:
        """
        Get list of chat room member user ID.

        Parameters
        ----------
        room_id : Chat room ID.

        Returns
        -------
        List of chat room member user ID.
        """

        # Parameter.
        api = 'getMemberFromChatRoom'
        data = {'chatRoomId': room_id}

        # Request.
        response = self.request(api, data, [0, 1])

        # Convert.
        data: dict = response['data']
        members: str = data['members']
        members_list = members.split('^G')
        members_list = list(filter(
            lambda member: member != '',
            members_list
        ))

        return members_list


    def get_room_member_dict(
        self,
        room_id: str
    ) -> dict[str, str]:
        """
        Get dictionary of chat room member user ID and user name.

        Parameters
        ----------
        room_id : Chat room ID.

        Returns
        -------
        Table of chat room member user ID and user name.
        """

        # Get member.
        members = self.get_room_member_list(room_id)

        # Loop.
        table = {}
        for member in members:
            table[member] = self.get_contact_name(member)

        return table


    def send_text(
        self,
        receive_id: str,
        text: str
    ) -> None:
        """
        Send text message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        text : Message text.
        """

        # Check.
        if text == '':
            throw(ValueError, text)

        # Parameter.
        api = 'sendTextMsg'
        data = {
            'wxid': receive_id,
            'msg': text
        }

        # Request.
        self.request(api, data, 1)


    def send_text_at(
        self,
        room_id: str,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None:
        """
        Send text message with `@`.

        Parameters
        ----------
        room_id : Chat room ID of receive message.
        user_id : User ID of `@`.
            - `str`: @ one user.
            - `list[str]`: @ multiple users.
            - `Literal['notify@all']`: @ all users.
        text : Message text.
        """

        # Check.
        if text == '':
            throw(ValueError, text)

        # Parameter.
        api = 'sendAtText'
        if type(user_id) != str:
            user_id = ','.join(user_id)
        data = {
            'chatRoomId': room_id,
            'wxids': user_id,
            'msg': text
        }

        # Request.
        self.request(api, data, fail_code=-1)


    def send_file(
        self,
        receive_id: str,
        path: str
    ) -> None:
        """
        Send file message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        path : Message file path.
        """

        # Parameter.
        api = 'sendFileMsg'
        data = {
            'wxid': receive_id,
            'filePath': path
        }

        # Request.
        self.request(api, data, fail_code=-1)


    def send_image(
        self,
        receive_id: str,
        path: str
    ) -> None:
        """
        Send image message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        path : Message image file path.
        """

        # Parameter.
        api = 'sendImagesMsg'
        data = {
            'wxid': receive_id,
            'imagePath': path
        }

        # Request.
        self.request(api, data, success_code=1)


    def send_emotion(
        self,
        receive_id: str,
        path: str
    ) -> None:
        """
        Send emotion message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        path : Message emotion file path.
        """

        # Parameter.
        api = 'sendCustomEmotion'
        data = {
            'wxid': receive_id,
            'filePath': path
        }

        # Request.
        self.request(api, data, success_code=1)


    def send_pat(
        self,
        receive_id: str,
        user_id: str,
    ) -> None:
        """
        Send pat message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        user_id : User ID of pat.
        """

        # Parameter.
        api = 'sendPatMsg'
        data = {
            'wxid': receive_id,
            'receiver': user_id
        }

        # Request.
        self.request(api, data, success_code=1)


    def send_public(
        self,
        receive_id: str,
        page_url: str,
        title: str,
        text: str | None = None,
        image_url: str | None = None,
        public_name: str | None = None,
        public_id: str | None = None
    ) -> None:
        """
        Send public account message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        page_url : Control click open page URL.
        title : Control title.
        text : Control text.
        image_url : Control image URL.
        public_name : Control public account name.
        public_id : Control public account ID.
        """

        # Parameter.
        text = text or ''
        image_url = image_url or ''
        public_name = public_name or ''
        public_id = public_id or ''
        api = 'forwardPublicMsg'
        data = {
            'wxid': receive_id,
            'url': page_url,
            'title': title,
            'digest': text,
            'thumbUrl': image_url,
            'appName': public_name,
            'userName': public_id
        }

        # Request.
        self.request(api, data, success_code=1)


    def send_forward(
        self,
        receive_id: str,
        message_id: str
    ) -> None:
        """
        Forward message.

        Parameters
        ----------
        receive_id : User ID or chat room ID of receive message.
        message_id : Forward message ID.
        """

        # Parameter.
        api = 'sendImagesMsg'
        data = {
            'wxid': receive_id,
            'forwardMsg': message_id
        }

        # Request.
        self.request(api, data, success_code=1)


def simulate_client_version() -> None:
    """
    Simulate WeChat client version.
    """

    # Check.

    ## Check client.
    judge = WeChatClient.check_client_started(WeChatClient)
    if not judge:
        raise WeChatClientErorr('WeChat client not started')

    ## Check client version.
    judge = WeChatClient.check_client_version(WeChatClient)
    if not judge:
        raise WeChatClientErorr(f'WeChat client version failed, must be "{WeChatClient.client_version}"')

    # Simulate.
    for offset in CLIENT_VERSION_MEMORY_OFFSETS:
        memory_write(
            'WeChat.exe',
            'WeChatWin.dll',
            offset,
            WeChatClient.client_version_simulate_int
        )

    # Report.
    print(f'WeChat client version simulated be "{WeChatClient.client_version_simulate}"')
