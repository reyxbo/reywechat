# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-23 20:55:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : WeChatDatabase methods.
"""


from typing import Any, Literal, overload
from json import loads as json_loads
from reydb.rdb import Database
from reykit.rbase import throw
from reykit.ros import File
from reykit.rtime import to_time, time_to, sleep
from reykit.rwrap import wrap_thread

from .rbase import BaseWeChat
from .rreceive import WeChatMessage
from .rsend import WeChatSendEnum, WeChatSendParameter
from .rwechat import WeChat


__all__ = (
    'WeChatDatabase',
)


class WeChatDatabase(BaseWeChat):
    """
    WeChat database type.
    """


    def __init__(
        self,
        wechat: WeChat,
        database: Database | dict[Literal['wechat', 'file'], Database]
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChatClient` instance.
        database : `Database` instance of `reykit` package.
            - `Database`, Set all `Database`: instances.
            - `dict`, Set each `Database`: instance, all item is required.
                `Key 'wechat'`: `Database` instance used in WeChat methods.
                `Key 'file'`: `Database` instance used in file methods.
        """

        # Set attribute.
        self.wechat = wechat
        match database:
            case Database():
                self.database_wechat = self.database_file = database
            case dict():
                self.database_wechat: Database = database.get('wechat')
                self.database_file: Database = database.get('file')
                if (
                    self.database_wechat is None
                    or self.database_file is None
                ):
                    throw(ValueError, database)
            case _:
                throw(TypeError, database)

        ## Database path name.
        self.path_names = {
            'wechat': 'wechat',
            'wechat.contact_user': 'contact_user',
            'wechat.contact_room': 'contact_room',
            'wechat.contact_room_user': 'contact_room_user',
            'wechat.message_receive': 'message_receive',
            'wechat.message_send': 'message_send',
            'wechat.stats': 'stats'
        }

        # Check.
        if 'sqlite' in (self.database_wechat.backend, self.database_file.backend):
            text='not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Build.
        self.build()

        # Add handler.
        self.__add_receiver_handler_to_contact_user()
        self.__add_receiver_handler_to_contact_room()
        self.__add_receiver_handler_to_contact_room_user()
        self.__add_receiver_handler_to_message_receive()
        self.__add_sender_handler_update_send_status()

        # Loop.
        self.__start_from_message_send()


    def build(self) -> None:
        """
        Check and build all standard databases and tables, by `self.path_names`.
        """

        # Set parameter.

        ## WeChatDatabase.
        databases = [
            {
                'name': self.path_names['wechat']
            }
        ]

        ## Table.
        tables = [

            ### 'contact_user'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.contact_user']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'update_time',
                        'type': 'datetime',
                        'constraint': 'DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP',
                        'comment': 'Record update time.'
                    },
                    {
                        'name': 'user_id',
                        'type': 'varchar(24)',
                        'constraint': 'NOT NULL',
                        'comment': 'User ID.'
                    },
                    {
                        'name': 'name',
                        'type': 'varchar(32)',
                        'constraint': 'CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL',
                        'comment': 'User name.'
                    },
                    {
                        'name': 'contact',
                        'type': 'tinyint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': 'Is the contact, 0 is contact, 1 is no contact.'
                    },
                    {
                        'name': 'valid',
                        'type': 'tinyint unsigned',
                        'constraint': 'DEFAULT 1',
                        'comment': 'Is the valid, 0 is invalid, 1 is valid.'
                    }
                ],
                'primary': 'user_id',
                'comment': 'User contact table.'
            },

            ### 'contact_room'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.contact_room']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'update_time',
                        'type': 'datetime',
                        'constraint': 'DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP',
                        'comment': 'Record update time.'
                    },
                    {
                        'name': 'room_id',
                        'type': 'varchar(31)',
                        'constraint': 'NOT NULL',
                        'comment': 'Chat room ID.'
                    },
                    {
                        'name': 'name',
                        'type': 'varchar(32)',
                        'constraint': 'CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL',
                        'comment': 'Chat room name.'
                    },
                    {
                        'name': 'contact',
                        'type': 'tinyint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': 'Is the contact, 0 is contact, 1 is no contact.'
                    },
                    {
                        'name': 'valid',
                        'type': 'tinyint unsigned',
                        'constraint': 'DEFAULT 1',
                        'comment': 'Is the valid, 0 is invalid, 1 is valid.'
                    }
                ],
                'primary': 'room_id',
                'comment': 'Chat room contact table.'
            },

            ### 'contact_room_user'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.contact_room_user']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'update_time',
                        'type': 'datetime',
                        'constraint': 'DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP',
                        'comment': 'Record update time.'
                    },
                    {
                        'name': 'room_id',
                        'type': 'varchar(31)',
                        'constraint': 'NOT NULL',
                        'comment': 'Chat room ID.'
                    },
                    {
                        'name': 'user_id',
                        'type': 'varchar(24)',
                        'constraint': 'NOT NULL',
                        'comment': 'Chat room user ID.'
                    },
                    {
                        'name': 'name',
                        'type': 'varchar(32)',
                        'constraint': 'CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL',
                        'comment': 'Chat room user name.'
                    },
                    {
                        'name': 'contact',
                        'type': 'tinyint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': 'Is the contact, 0 is contact, 1 is no contact.'
                    },
                    {
                        'name': 'valid',
                        'type': 'tinyint unsigned',
                        'constraint': 'DEFAULT 1',
                        'comment': 'Is the valid, 0 is invalid, 1 is valid.'
                    }
                ],
                'primary': ['room_id', 'user_id'],
                'comment': 'Chat room user contact table.'
            },


            ### 'message_receive'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.message_receive']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'message_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL',
                        'comment': 'Message time.'
                    },
                    {
                        'name': 'message_id',
                        'type': 'bigint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': 'Message UUID.'
                    },
                    {
                        'name': 'room_id',
                        'type': 'varchar(31)',
                        'constraint': 'DEFAULT NULL',
                        'comment': 'Message chat room ID, null for private chat.'
                    },
                    {
                        'name': 'user_id',
                        'type': 'varchar(24)',
                        'constraint': 'DEFAULT NULL',
                        'comment': 'Message sender user ID, null for system message.'
                    },
                    {
                        'name': 'type',
                        'type': 'int unsigned',
                        'constraint': 'NOT NULL',
                        'comment': (
                            'Message type, '
                            '1 is text message, '
                            '3 is image message, '
                            '34 is voice message, '
                            '37 is new friend, '
                            '42 is business card, '
                            '43 is video message, '
                            '47 is emoticon message, '
                            '48 is position message, '
                            '49 is file or quote or forward or share link or transfer money or real time location message, '
                            '1000 is system message, '
                            '1002 is recall message.'
                        )
                    },
                    {
                        'name': 'data',
                        'type': 'text',
                        'constraint': 'CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL',
                        'comment': 'Message data.'
                    },
                    {
                        'name': 'file_id',
                        'type': 'mediumint unsigned',
                        'constraint': 'DEFAULT NULL',
                        'comment': 'Message file ID, from the file database.'
                    }
                ],
                'primary': 'message_id',
                'indexes': [
                    {
                        'name': 'n_message_time',
                        'fields': 'message_time',
                        'type': 'noraml',
                        'comment': 'Message time normal index.'
                    },
                    {
                        'name': 'n_room_id',
                        'fields': 'room_id',
                        'type': 'noraml',
                        'comment': 'Message chat room ID normal index.'
                    },
                    {
                        'name': 'n_user_id',
                        'fields': 'user_id',
                        'type': 'noraml',
                        'comment': 'Message sender user ID normal index.'
                    }
                ],
                'comment': 'Message receive table.'
            },

            ### 'message_send'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.message_send']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'status_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
                        'comment': 'Send status time.'
                    },
                    {
                        'name': 'plan_time',
                        'type': 'datetime',
                        'constraint': 'DEFAULT NULL',
                        'comment': 'Send plan time.'
                    },
                    {
                        'name': 'send_id',
                        'type': 'int unsigned',
                        'constraint': 'NOT NULL AUTO_INCREMENT',
                        'comment': 'Send self increase ID.'
                    },
                    {
                        'name': 'status',
                        'type': 'tinyint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': (
                            'Send status, '
                            '0 is not sent, '
                            '1 is handling, '
                            '2 is send success, '
                            '3 is send fail, '
                            '4 is send cancel.'
                        )
                    },
                    {
                        'name': 'type',
                        'type': 'tinyint unsigned',
                        'constraint': 'NOT NULL',
                        'comment': (
                            'Send type, '
                            '0 is text message, '
                            "1 is text message with \\'@\\', "
                            '2 is file message, '
                            '3 is image message, '
                            '4 is emoticon message, '
                            '5 is pat message, '
                            '6 is public account message, '
                            '7 is forward message.'
                        )
                    },
                    {
                        'name': 'receive_id',
                        'type': 'varchar(31)',
                        'constraint': 'NOT NULL',
                        'comment': 'Receive to user ID or chat room ID.'
                    },
                    {
                        'name': 'parameter',
                        'type': 'json',
                        'constraint': 'NOT NULL',
                        'comment': 'Send parameters.'
                    },
                    {
                        'name': 'file_id',
                        'type': 'mediumint unsigned',
                        'constraint': 'DEFAULT NULL',
                        'comment': 'Send file ID, from the file database.'
                    }
                ],
                'primary': 'send_id',
                'indexes': [
                    {
                        'name': 'n_status_time',
                        'fields': 'status_time',
                        'type': 'noraml',
                        'comment': 'Send status time normal index.'
                    },
                    {
                        'name': 'n_receive_id',
                        'fields': 'receive_id',
                        'type': 'noraml',
                        'comment': 'Receive to user ID or chat room ID normal index.'
                    }
                ],
                'comment': 'Message send table.'
            }

        ]

        ## View stats.
        views_stats = [

            ### 'stats'.
            {
                'path': (self.path_names['wechat'], self.path_names['wechat.stats']),
                'items': [
                    {
                        'name': 'count_receive',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.message_receive']}`'
                        ),
                        'comment': 'Message receive count.'
                    },
                    {
                        'name': 'count_send',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.message_send']}`\n'
                            'WHERE `status` = 2'
                        ),
                        'comment': 'Message send count.'
                    },
                    {
                        'name': 'count_user',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_user']}`'
                        ),
                        'comment': 'Contact user count.'
                    },
                    {
                        'name': 'count_room',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room']}`'
                        ),
                        'comment': 'Contact room count.'
                    },
                    {
                        'name': 'count_room_user',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room_user']}`'
                        ),
                        'comment': 'Contact room user count.'
                    },
                    {
                        'name': 'last_time_receive',
                        'select': (
                            'SELECT MAX(`message_time`)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.message_receive']}`'
                        ),
                        'comment': 'Message last receive time.'
                    },
                    {
                        'name': 'last_time_send',
                        'select': (
                            'SELECT MAX(`status_time`)\n'
                            f'FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.message_send']}`\n'
                            'WHERE `status` = 2'
                        ),
                        'comment': 'Message last send time.'
                    }
                ]
            }

        ]

        # Build.

        ## WeChat.
        self.database_wechat.build.build(databases, tables, views_stats=views_stats)

        ## File.
        self.database_file.file.build()

        # Update.
        self.update_contact_user()
        self.update_contact_room()
        self.update_contact_room_user()


    def update_contact_user(self) -> None:
        """
        Update table `contact_user`.
        """

        # Get data.
        contact_table = self.wechat.client.get_contact_table('user')

        user_data = [
            {
                'user_id': row['id'],
                'name': row['name'],
                'contact': 1
            }
            for row in contact_table
        ]
        user_ids = [
            row['id']
            for row in contact_table
        ]

        # Insert and update.
        conn = self.database_wechat.connect()

        ## Insert.
        if contact_table != []:
            conn.execute_insert(
                (self.path_names['wechat'], self.path_names['wechat.contact_user']),
                user_data,
                'update'
            )

        ## Update.
        if user_ids == []:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_user']}`\n'
                'SET `contact` = 0'
            )
        else:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_user']}`\n'
                'SET `contact` = 0\n'
                'WHERE `user_id` NOT IN :user_ids'
            )
        conn.execute(
            sql,
            user_ids=user_ids
        )

        ## Commit.
        conn.commit()

        ## Close.
        conn.close()


    def update_contact_room(self) -> None:
        """
        Update table `contact_room`.
        """

        # Get data.
        contact_table = self.wechat.client.get_contact_table('room')

        room_data = [
            {
                'room_id': row['id'],
                'name': row['name'],
                'contact': 1
            }
            for row in contact_table
        ]
        room_ids = [
            row['id']
            for row in contact_table
        ]

        # Insert and update.
        conn = self.database_wechat.connect()

        ## Insert.
        if contact_table != []:
            conn.execute_insert(
                (self.path_names['wechat'], self.path_names['wechat.contact_room']),
                room_data,
                'update'
            )

        ## Update.
        if room_ids == []:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room']}`\n'
                'SET `contact` = 0'
            )
        else:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room']}`\n'
                'SET `contact` = 0\n'
                'WHERE `room_id` NOT IN :room_ids'
            )
        conn.execute(
            sql,
            room_ids=room_ids
        )

        ## Commit.
        conn.commit()

        ## Close.
        conn.close()


    def update_contact_room_user(
        self,
        room_id: str | None = None
    ) -> None:
        """
        Update table `contact_room_user`.

        Parameters
        ----------
        room_id : Chat room ID.
            - `None`: Update all chat room.
            - `str`: Update this chat room.
        """

        # Get data.

        ## All.
        if room_id is None:
            contact_table = self.wechat.client.get_contact_table('room')

        ## Given.
        else:
            contact_table = [{'id': room_id}]

        room_user_data = [
            {
                'room_id': row['id'],
                'user_id': user_id,
                'name': name,
                'contact': 1
            }
            for row in contact_table
            for user_id, name
            in self.wechat.client.get_room_member_dict(row['id']).items()
        ]
        room_user_ids = [
            '%s,%s' % (
                row['room_id'],
                row['user_id']
            )
            for row in room_user_data
        ]

        # Insert and update.
        conn = self.database_wechat.connect()

        ## Insert.
        if room_user_data != []:
            conn.execute_insert(
                (self.path_names['wechat'], self.path_names['wechat.contact_room_user']),
                room_user_data,
                'update'
            )

        ## Update.
        if room_user_ids == []:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room_user']}`\n'
                'SET `contact` = 0'
            )
        elif room_id is None:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room_user']}`\n'
                'SET `contact` = 0\n'
                "WHERE CONCAT(`room_id`, ',', `user_id`) NOT IN :room_user_ids"
            )
        else:
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room_user']}`\n'
                'SET `contact` = 0\n'
                'WHERE (\n'
                '    `room_id` = :room_id\n'
                "    AND CONCAT(`room_id`, ',', `user_id`) NOT IN :room_user_ids\n"
                ')'
            )
        conn.execute(
            sql,
            room_user_ids=room_user_ids,
            room_id=room_id
        )

        ## Commit.
        conn.commit()

        ## Close.
        conn.close()


    def __add_receiver_handler_to_contact_user(self) -> None:
        """
        Add receiver handler, write record to table `contact_user`.
        """


        # Define.
        def receiver_handler_to_contact_user(message: WeChatMessage) -> None:
            """
            Write record to table `contact_user`.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Add friend.
            if message.is_new_user:

                ## Generate data.
                name = self.wechat.client.get_contact_name(message.user)
                data = {
                    'user_id': message.user,
                    'name': name,
                    'contact': 1
                }

                ## Insert.
                self.database_wechat.execute_insert(
                    (self.path_names['wechat'], self.path_names['wechat.contact_user']),
                    data,
                    'update'
                )


        # Add handler.
        self.wechat.receiver.add_handler(receiver_handler_to_contact_user)


    def __add_receiver_handler_to_contact_room(self) -> None:
        """
        Add receiver handler, write record to table `contact_room`.
        """


        # Define.
        def receiver_handler_to_contact_room(message: WeChatMessage) -> None:
            """
            Write record to table `contact_room`.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Invite.
            if message.is_new_room:

                ## Generate data.
                name = self.wechat.client.get_contact_name(message.room)
                data = {
                    'room_id': message.room,
                    'name': name,
                    'contact': 1
                }

                ## Insert.

                ### 'contact_room'.
                self.database_wechat.execute_insert(
                    (self.path_names['wechat'], self.path_names['wechat.contact_room']),
                    data,
                    'update'
                )

                ### 'contact_room_user'.
                self.update_contact_room_user(message.room)

            # Modify room name.
            elif message.is_change_room_name:

                ## Generate data.
                _, name = message.data.rsplit('“', 1)
                name = name[:-1]
                data = {
                    'room_id': message.room,
                    'name': name,
                    'limit': 1
                }

                ## Update.
                self.database_wechat.execute_update(
                    (self.path_names['wechat'], self.path_names['wechat.contact_room']),
                    data
                )

            elif (

                # Kick out.
                message.is_kick_out_room

                # Dissolve.
                or message.is_dissolve_room
            ):

                ## Generate data.
                data = {
                    'room_id': message.room,
                    'contact': 0,
                    'limit': 1
                }

                ## Update.
                self.database_wechat.execute_update(
                    (self.path_names['wechat'], self.path_names['wechat.contact_room']),
                    data
                )


        # Add handler.
        self.wechat.receiver.add_handler(receiver_handler_to_contact_room)


    def __add_receiver_handler_to_contact_room_user(self) -> None:
        """
        Add receiver handler, write record to table `contact_room_user`.
        """


        # Define.
        def receiver_handler_to_contact_room_user(message: WeChatMessage) -> None:
            """
            Write record to table `contact_room_user`.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Add memeber.
            if message.is_new_room_user:

                ## Sleep.
                sleep(1)

                ## Insert.
                self.update_contact_room_user(message.room)


        # Add handler.
        self.wechat.receiver.add_handler(receiver_handler_to_contact_room_user)


    def __add_receiver_handler_to_message_receive(self) -> None:
        """
        Add receiver handler, write record to table `message_receive`.
        """


        # Define.
        def receiver_handler_to_message_receive(message: WeChatMessage) -> None:
            """
            Write record to table `message_receive`.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Upload file.
            if message.file is None:
                file_id = None
            else:
                file_id = self.database_file.file.upload(
                    message.file['path'],
                    message.file['name'],
                    'WeChat'
                )

            # Generate data.
            message_time_obj = to_time(message.time)
            message_time_str = time_to(message_time_obj)
            data = {
                'message_time': message_time_str,
                'message_id': message.id,
                'room_id': message.room,
                'user_id': message.user,
                'type': message.type,
                'data': message.data,
                'file_id': file_id
            }

            # Insert.
            self.database_wechat.execute_insert(
                (self.path_names['wechat'], self.path_names['wechat.message_receive']),
                data,
                'ignore'
            )


        # Add handler.
        self.wechat.receiver.add_handler(receiver_handler_to_message_receive)


    def __add_sender_handler_update_send_status(self) -> None:
        """
        Add sender handler, update field `status` of table `message_send`.
        """


        # Define.
        def sender_handler_update_send_status(sendparam: WeChatSendParameter) -> None:
            """
            Update field `status` of table `message_send`.

            Parameters
            ----------
            sendparam : `WeChatSendParameter` instance.
            """

            # Handle parameter.
            if sendparam.exc_reports == []:
                status = 2
            else:
                status = 3
            data = {
                'send_id': sendparam.send_id,
                'status': status,
                'limit': 1
            }

            # Update.
            self.database_wechat.execute_update(
                (self.path_names['wechat'], self.path_names['wechat.message_send']),
                data
            )


        # Add handler.
        self.wechat.sender.add_handler(sender_handler_update_send_status)


    def __download_file(
        self,
        file_id: int
    ) -> tuple[str, str]:
        """
        Download file by ID.

        Parameters
        ----------
        file_id : File ID.

        Returns
        -------
        File save path and file name.
        """

        # Information.
        file_info = self.database_file.file.query(file_id)
        file_md5 = file_info['md5']
        file_name = file_info['name']

        # Cache.
        cache_path = self.wechat.cache.index(file_md5, file_name, True)

        ## Download.
        if cache_path is None:
            file_bytes = self.database_file.file.download(file_id)
            cache_path = self.wechat.cache.store(file_bytes, file_name)

        return cache_path, file_name


    @wrap_thread
    def __start_from_message_send(self) -> None:
        """
        Start loop read record from table `message_send`, put send queue.
        """


        # Define.
        def __from_message_send() -> None:
            """
            Read record from table `message_send`, put send queue.
            """

            # Handle parameter.
            conn = self.database_wechat.connect()

            # Read.
            where = (
                '(\n'
                '    `status` = 0\n'
                '    AND (\n'
                '        `plan_time` IS NULL\n'
                '        OR `plan_time` < NOW()\n'
                '    )\n'
                ')'
            )
            result = conn.execute_select(
                (self.path_names['wechat'], self.path_names['wechat.message_send']),
                ['send_id', 'type', 'receive_id', 'parameter', 'file_id'],
                where,
                order='`plan_time` DESC, `send_id`'
            )

            # Convert.
            if result.empty:
                return
            table = result.to_table()

            # Update.
            send_ids = [
                row['send_id']
                for row in table
            ]
            sql = (
                f'UPDATE `{self.path_names['wechat']}`.`{self.path_names['wechat.message_send']}`\n'
                'SET `status` = 1\n'
                'WHERE `send_id` IN :send_ids'
            )
            conn.execute(
                sql,
                send_ids=send_ids
            )

            # Send.
            for row in table:
                send_id, type_, receive_id, parameter, file_id = row.values()
                send_type = WeChatSendEnum(type_)
                parameter: dict = json_loads(parameter)

                ## File.
                if file_id is not None:
                    file_path, file_name = self.__download_file(file_id)
                    parameter['file_path'] = file_path
                    parameter['file_name'] = file_name

                sendparam = WeChatSendParameter(
                    self.wechat.sender,
                    send_type,
                    receive_id,
                    send_id,
                    **parameter
                )
                self.wechat.sender.queue.put(sendparam)

            # Commit.
            conn.commit()


        # Loop.
        while True:

            # Put.
            __from_message_send()

            # Wait.
            sleep(1)


    def is_valid(
        self,
        message: WeChatMessage
    ) -> bool:
        """
        Judge if is valid user or chat room from database.

        Parameters
        ----------
        message : `WeChatMessage` instance.

        Returns
        -------
        Judgment result.
            - `True`: Valid.
            - `False`: Invalid or no record.
        """

        # Judge.

        ## User.
        if message.room is None:
            result = message.receiver.wechat.database.database_wechat.execute_select(
                (self.path_names['wechat'], self.path_names['wechat.contact_user']),
                ['valid'],
                '`user_id` = :user_id',
                limit=1,
                user_id=message.user
            )

        ## Room.
        else:
            sql = (
            'SELECT (\n'
            '    SELECT `valid`\n'
            f'    FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room_user']}`\n'
            '    WHERE `room_id` = :room_id AND `user_id` = :user_id\n'
            '    LIMIT 1\n'
            ') AS `valid`\n'
            'FROM (\n'
            '    SELECT `valid`\n'
            f'    FROM `{self.path_names['wechat']}`.`{self.path_names['wechat.contact_room']}`\n'
            '    WHERE `room_id` = :room_id\n'
            '    LIMIT 1\n'
            ') AS `a`\n'
            'WHERE `valid` = 1'
            )
            result = message.receiver.wechat.database.database_wechat.execute(
                sql,
                room_id=message.room,
                user_id=message.user
            )

        valid = result.scalar()
        judge = valid == 1

        return judge


    @overload
    def send(
        self,
        send_type: Literal[WeChatSendEnum.SEND_TEXT],
        receive_id: str,
        *,
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendEnum.SEND_TEXT_AT],
        receive_id: str,
        *,
        user_id: str | list[str] | Literal['notify@all'],
        text: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendEnum.SEND_FILE, WeChatSendEnum.SEND_IMAGE, WeChatSendEnum.SEND_EMOTION],
        receive_id: str,
        *,
        file_path: str,
        file_name: str | None = None
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendEnum.SEND_PAT],
        receive_id: str,
        *,
        user_id: str
    ) -> None: ...

    @overload
    def send(
        self,
        send_type: Literal[WeChatSendEnum.SEND_PUBLIC],
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
        send_type: Literal[WeChatSendEnum.SEND_FORWARD],
        receive_id: str,
        *,
        message_id: str
    ) -> None: ...

    def send(
        self,
        send_type: WeChatSendEnum,
        receive_id: str | None = None,
        **params: Any
    ) -> None:
        """
        Insert into `wechat.message_send` table of database, wait send.

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
        receive_id : User ID or chat room ID of receive message.
        params : Send parameters.
        """

        # Handle parameter.
        data = {
            'status': 0,
            'type': send_type,
            'receive_id': receive_id,
            'parameter': params
        }

        # Upload file.
        if 'file_path' in params:
            file_path: str = params.pop('file_path')
            if 'file_name' in params:
                file_name: str = params.pop('file_name')
            else:
                file = File(file_path)
                file_name = file.name_suffix

            ## Cache.
            cache_path = self.wechat.cache.store(file_path, file_name)

            file_id = self.database_file.file.upload(
                cache_path,
                file_name,
                'WeChat'
            )
        else:
            file_id = None
        data['file_id'] = file_id

        # Insert.
        self.database_wechat.execute_insert(
            (self.path_names['wechat'], self.path_names['wechat.message_send']),
            data
        )
