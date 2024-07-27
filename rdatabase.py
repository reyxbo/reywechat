# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-23 20:55:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Tuple, Dict, Literal, Union, Optional
from json import loads as json_loads
from reydb.rconnection import RDatabase as RRDatabase
from reytool.rexception import throw
from reytool.ros import RFolder
from reytool.rtime import to_time, time_to, sleep
from reytool.rwrap import wrap_thread

from .rreceive import RMessage
from .rsend import RSendParam
from .rwechat import RWeChat


__all__ = (
    "RDatabase",
)


class RDatabase(object):
    """
    Rey's `database` type.
    """


    def __init__(
        self,
        rwechat: RWeChat,
        rrdatabase: Union[RRDatabase, Dict[Literal["wechat", "file"], RRDatabase]]
    ) -> None:
        """
        Build `database` instance.

        Parameters
        ----------
        rwechat : `RClient` instance.
        rrdatabase : `RDatabase` instance of `reytool` package.
            - `RDatabase` : Set all `RDatabase` instances.
            - `Dict` : Set each `RDatabase` instance, all item is required.
                * `Key 'wechat'` : `RDatabase` instance used in WeChat methods.
                * `Key 'file'` : `RDatabase` instance used in file methods.
        """

        # Set attribute.
        self.rwechat = rwechat
        if rrdatabase.__class__ == RRDatabase:
            self.rrdatabase_wechat = self.rrdatabase_file = rrdatabase
        elif rrdatabase.__class__ == dict:
            self.rrdatabase_wechat = rrdatabase.get("wechat")
            self.rrdatabase_file = rrdatabase.get("file")
            if (
                self.rrdatabase_wechat
                or self.rrdatabase_file
            ):
                throw(ValueError, rrdatabase)
        else:
            throw(TypeError, rrdatabase)

        # Build.
        self.build()

        # Add handler.
        self._to_contact_user()
        self._to_contact_room()
        self._to_contact_room_user()
        self._to_message_receive()
        self._to_message_send()
        self._from_message_send_loop()


    def build(self) -> None:
        """
        Check and build all standard databases and tables.
        """

        # Set parameter.

        ## Database.
        databases = [
            {
                "database": "wechat"
            }
        ]

        ## Table.
        tables = [

            ### "contact_user".
            {
                "path": ("wechat", "contact_user"),
                "fields": [
                    {
                        "name": "create_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "update_time",
                        "type_": "datetime",
                        "constraint": "DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP",
                        "comment": "Record update time."
                    },
                    {
                        "name": "user_id",
                        "type_": "varchar(24)",
                        "constraint": "NOT NULL",
                        "comment": "User ID."
                    },
                    {
                        "name": "name",
                        "type_": "varchar(32)",
                        "constraint": "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL",
                        "comment": "User name."
                    },
                    {
                        "name": "contact",
                        "type_": "tinyint unsigned",
                        "constraint": "NOT NULL",
                        "comment": "Is the contact, 0 is contact, 1 is no contact."
                    },
                    {
                        "name": "valid",
                        "type_": "tinyint unsigned",
                        "constraint": "DEFAULT 1",
                        "comment": "Is the valid, 0 is invalid, 1 is valid."
                    }
                ],
                "primary": "user_id",
                "comment": "User contact table."
            },

            ### "contact_room".
            {
                "path": ("wechat", "contact_room"),
                "fields": [
                    {
                        "name": "create_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "update_time",
                        "type_": "datetime",
                        "constraint": "DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP",
                        "comment": "Record update time."
                    },
                    {
                        "name": "room_id",
                        "type_": "varchar(31)",
                        "constraint": "NOT NULL",
                        "comment": "Chat room ID."
                    },
                    {
                        "name": "name",
                        "type_": "varchar(32)",
                        "constraint": "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL",
                        "comment": "Chat room name."
                    },
                    {
                        "name": "contact",
                        "type_": "tinyint unsigned",
                        "constraint": "NOT NULL",
                        "comment": "Is the contact, 0 is contact, 1 is no contact."
                    },
                    {
                        "name": "valid",
                        "type_": "tinyint unsigned",
                        "constraint": "DEFAULT 1",
                        "comment": "Is the valid, 0 is invalid, 1 is valid."
                    }
                ],
                "primary": "room_id",
                "comment": "Chat room contact table."
            },

            ### "contact_room_user".
            {
                "path": ("wechat", "contact_room_user"),
                "fields": [
                    {
                        "name": "create_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "update_time",
                        "type_": "datetime",
                        "constraint": "DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP",
                        "comment": "Record update time."
                    },
                    {
                        "name": "room_id",
                        "type_": "varchar(31)",
                        "constraint": "NOT NULL",
                        "comment": "Chat room ID."
                    },
                    {
                        "name": "user_id",
                        "type_": "varchar(24)",
                        "constraint": "NOT NULL",
                        "comment": "Chat room user ID."
                    },
                    {
                        "name": "name",
                        "type_": "varchar(32)",
                        "constraint": "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL",
                        "comment": "Chat room user name."
                    },
                    {
                        "name": "contact",
                        "type_": "tinyint unsigned",
                        "constraint": "NOT NULL",
                        "comment": "Is the contact, 0 is contact, 1 is no contact."
                    },
                    {
                        "name": "valid",
                        "type_": "tinyint unsigned",
                        "constraint": "DEFAULT 1",
                        "comment": "Is the valid, 0 is invalid, 1 is valid."
                    }
                ],
                "primary": ["room_id", "user_id"],
                "comment": "Chat room user contact table."
            },


            ### "message_receive".
            {
                "path": ("wechat", "message_receive"),
                "fields": [
                    {
                        "name": "create_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "message_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL",
                        "comment": "Message time."
                    },
                    {
                        "name": "message_id",
                        "type_": "bigint unsigned",
                        "constraint": "NOT NULL",
                        "comment": "Message UUID."
                    },
                    {
                        "name": "room_id",
                        "type_": "varchar(31)",
                        "constraint": "DEFAULT NULL",
                        "comment": "Message chat room ID, null for private chat."
                    },
                    {
                        "name": "user_id",
                        "type_": "varchar(24)",
                        "constraint": "DEFAULT NULL",
                        "comment": "Message sender user ID, null for system message."
                    },
                    {
                        "name": "type",
                        "type_": "int unsigned",
                        "constraint": "NOT NULL",
                        "comment": (
                            "Message type, "
                            "1 is text message, "
                            "3 is image message, "
                            "34 is voice message, "
                            "37 is new friend, "
                            "42 is business card, "
                            "43 is video message, "
                            "47 is emoticon message, "
                            "48 is position message, "
                            "49 is file or quote or forward or share link or transfer money or real time location message, "
                            "1000 is system message, "
                            "1002 is recall message."
                        )
                    },
                    {
                        "name": "data",
                        "type_": "text",
                        "constraint": "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL",
                        "comment": "Message data."
                    },
                    {
                        "name": "file_id",
                        "type_": "mediumint unsigned",
                        "constraint": "DEFAULT NULL",
                        "comment": "Message file ID, from the file database."
                    }
                ],
                "primary": "message_id",
                "indexes": [
                    {
                        "name": "n_message_time",
                        "fields": "message_time",
                        "type": "noraml",
                        "comment": "Message time normal index."
                    },
                    {
                        "name": "n_room_id",
                        "fields": "room_id",
                        "type": "noraml",
                        "comment": "Message chat room ID normal index."
                    },
                    {
                        "name": "n_user_id",
                        "fields": "user_id",
                        "type": "noraml",
                        "comment": "Message sender user ID normal index."
                    }
                ],
                "comment": "Message receive table."
            },

            ### "message_send".
            {
                "path": ("wechat", "message_send"),
                "fields": [
                    {
                        "name": "create_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "status_time",
                        "type_": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
                        "comment": "Send status time."
                    },
                    {
                        "name": "plan_time",
                        "type_": "datetime",
                        "constraint": "DEFAULT NULL",
                        "comment": "Send plan time."
                    },
                    {
                        "name": "send_id",
                        "type_": "int unsigned",
                        "constraint": "NOT NULL AUTO_INCREMENT",
                        "comment": "Send self increase ID."
                    },
                    {
                        "name": "status",
                        "type_": "tinyint unsigned",
                        "constraint": "NOT NULL",
                        "comment": (
                            "Send status, "
                            "0 is not sent, "
                            "1 is handling, "
                            "2 is send success, "
                            "3 is send fail, "
                            "4 is send cancel."
                        )
                    },
                    {
                        "name": "type",
                        "type_": "tinyint unsigned",
                        "constraint": "NOT NULL",
                        "comment": (
                            "Send type, "
                            "0 is text message, "
                            "1 is text message with \"@\", "
                            "2 is file message, "
                            "3 is image message, "
                            "4 is emoticon message, "
                            "5 is pat message, "
                            "6 is public account message, "
                            "7 is forward message."
                        )
                    },
                    {
                        "name": "receive_id",
                        "type_": "varchar(31)",
                        "constraint": "NOT NULL",
                        "comment": "Receive to user ID or chat room ID."
                    },
                    {
                        "name": "parameter",
                        "type_": "json",
                        "constraint": "NOT NULL",
                        "comment": (
                            "Send parameters, "
                            "when parameter \"file_id\" exists, then download file and convert to parameter \"path\"."
                        )
                    }
                ],
                "primary": "send_id",
                "indexes": [
                    {
                        "name": "n_status_time",
                        "fields": "status_time",
                        "type": "noraml",
                        "comment": "Send status time normal index."
                    },
                    {
                        "name": "n_receive_id",
                        "fields": "receive_id",
                        "type": "noraml",
                        "comment": "Receive to user ID or chat room ID normal index."
                    }
                ],
                "comment": "Message send table."
            }
        ]

        ## View stats.
        views_stats = [

            ### "stats".
            {
                "path": ("wechat", "stats"),
                "items": [
                    {
                        "name": "count_receive",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `wechat`.`message_receive`"
                        ),
                        "comment": "Message receive count."
                    },
                    {
                        "name": "count_send",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `wechat`.`message_send`\n"
                            "WHERE `status` = 2"
                        ),
                        "comment": "Message send count."
                    },
                    {
                        "name": "count_user",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `wechat`.`contact_user`"
                        ),
                        "comment": "Contact user count."
                    },
                    {
                        "name": "count_room",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `wechat`.`contact_room`"
                        ),
                        "comment": "Contact room count."
                    },
                    {
                        "name": "count_room_user",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `wechat`.`contact_room_user`"
                        ),
                        "comment": "Contact room user count."
                    },
                    {
                        "name": "last_time_receive",
                        "select": (
                            "SELECT MAX(`message_time`)\n"
                            "FROM `wechat`.`message_receive`"
                        ),
                        "comment": "Message last receive time."
                    },
                    {
                        "name": "last_time_send",
                        "select": (
                            "SELECT MAX(`status_time`)\n"
                            "FROM `wechat`.`message_send`\n"
                            "WHERE `status` = 2"
                        ),
                        "comment": "Message last send time."
                    }
                ]
            }
        ]

        # Build.

        ## WeChat.
        self.rrdatabase_wechat.build.build(databases, tables, views_stats=views_stats)

        ## File.
        self.rrdatabase_file.file.build()

        # Update.
        self.update_contact_user()
        self.update_contact_room()
        self.update_contact_room_user()


    def update_contact_user(self) -> None:
        """
        Update table `contact_user`.
        """

        # Get data.
        contact_table = self.rwechat.rclient.get_contact_table("user")

        user_data = [
            {
                "user_id": row["id"],
                "name": row["name"],
                "contact": 1
            }
            for row in contact_table
        ]
        user_ids = [
            row["id"]
            for row in contact_table
        ]

        # Insert and update.
        conn = self.rrdatabase_wechat.connect()

        ## Insert.
        if contact_table != []:
            conn.execute_insert(
                ("wechat", "contact_user"),
                user_data,
                "update"
            )

        ## Update.
        if user_ids == []:
            sql = (
                "UPDATE `wechat`.`contact_user`\n"
                "SET `contact` = 0"
            )
        else:
            sql = (
                "UPDATE `wechat`.`contact_user`\n"
                "SET `contact` = 0\n"
                "WHERE `user_id` NOT IN :user_ids"
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
        contact_table = self.rwechat.rclient.get_contact_table("room")

        room_data = [
            {
                "room_id": row["id"],
                "name": row["name"],
                "contact": 1
            }
            for row in contact_table
        ]
        room_ids = [
            row["id"]
            for row in contact_table
        ]

        # Insert and update.
        conn = self.rrdatabase_wechat.connect()

        ## Insert.
        if contact_table != []:
            conn.execute_insert(
                ("wechat", "contact_room"),
                room_data,
                "update"
            )

        ## Update.
        if room_ids == []:
            sql = (
                "UPDATE `wechat`.`contact_room`\n"
                "SET `contact` = 0"
            )
        else:
            sql = (
                "UPDATE `wechat`.`contact_room`\n"
                "SET `contact` = 0\n"
                "WHERE `room_id` NOT IN :room_ids"
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
        room_id: Optional[str] = None
    ) -> None:
        """
        Update table `contact_room_user`.

        Parameters
        ----------
        room_id : Chat room ID.
            - `None` : Update all chat room.
            - `str` : Update this chat room.
        """

        # Get data.

        ## All.
        if room_id is None:
            contact_table = self.rwechat.rclient.get_contact_table("room")

        ## Given.
        else:
            contact_table = [{"id": room_id}]

        room_user_data = [
            {
                "room_id": row["id"],
                "user_id": user_id,
                "name": name,
                "contact": 1
            }
            for row in contact_table
            for user_id, name
            in self.rwechat.rclient.get_room_member_dict(row["id"]).items()
        ]
        room_user_ids = [
            "%s,%s" % (
                row["room_id"],
                row["user_id"]
            )
            for row in room_user_data
        ]

        # Insert and update.
        conn = self.rrdatabase_wechat.connect()

        ## Insert.
        if room_user_data != []:
            conn.execute_insert(
                ("wechat", "contact_room_user"),
                room_user_data,
                "update"
            )

        ## Update.
        if room_user_ids == []:
            sql = (
                "UPDATE `wechat`.`contact_room_user`\n"
                "SET `contact` = 0"
            )
        elif room_id is None:
            sql = (
                "UPDATE `wechat`.`contact_room_user`\n"
                "SET `contact` = 0\n"
                "WHERE CONCAT(`room_id`, ',', `user_id`) NOT IN :room_user_ids"
            )
        else:
            sql = (
                "UPDATE `wechat`.`contact_room_user`\n"
                "SET `contact` = 0\n"
                "WHERE (\n"
                "    `room_id` = :room_id\n"
                "    AND CONCAT(`room_id`, ',', `user_id`) NOT IN :room_user_ids\n"
                ")"
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


    def _to_contact_user(self) -> None:
        """
        Add handler, write record to table `contact_user`.
        """


        # Define.
        def handler_to_contact_user(rmessage: RMessage) -> None:
            """
            Write record to table `contact_user`.

            Parameters
            ----------
            rmessage : `RMessage` instance.
            """

            # Add friend.
            if rmessage.is_new_user:

                ## Generate data.
                name = self.rwechat.rclient.get_contact_name(rmessage.user)
                data = {
                    "user_id": rmessage.user,
                    "name": name,
                    "contact": 1
                }

                ## Insert.
                self.rrdatabase_wechat.execute_insert(
                    ("wechat", "contact_user"),
                    data,
                    "update"
                )


        # Add handler.
        self.rwechat.rreceive.add_handler(handler_to_contact_user)


    def _to_contact_room(self) -> None:
        """
        Add handler, write record to table `contact_room`.
        """


        # Define.
        def handler_to_contact_room(rmessage: RMessage) -> None:
            """
            Write record to table `contact_room`.

            Parameters
            ----------
            rmessage : `RMessage` instance.
            """

            # Invite.
            if rmessage.is_new_room:

                ## Generate data.
                name = self.rwechat.rclient.get_contact_name(rmessage.room)
                data = {
                    "room_id": rmessage.room,
                    "name": name,
                    "contact": 1
                }

                ## Insert.

                ### "contact_room".
                self.rrdatabase_wechat.execute_insert(
                    ("wechat", "contact_room"),
                    data,
                    "update"
                )

                ### "contact_room_user".
                self.update_contact_room_user(rmessage.room)

            # Modify room name.
            elif rmessage.is_change_room_name:

                ## Generate data.
                _, name = rmessage.data.rsplit("“", 1)
                name = name[:-1]
                data = {
                    "room_id": rmessage.room,
                    "name": name,
                    "limit": 1
                }

                ## Update.
                self.rrdatabase_wechat.execute_update(
                    ("wechat", "contact_room"),
                    data
                )

            elif (

                # Kick out.
                rmessage.is_kick_out_room

                # Dissolve.
                or rmessage.is_dissolve_room
            ):

                ## Generate data.
                data = {
                    "room_id": rmessage.room,
                    "contact": 0,
                    "limit": 1
                }

                ## Update.
                self.rrdatabase_wechat.execute_update(
                    ("wechat", "contact_room"),
                    data
                )


        # Add handler.
        self.rwechat.rreceive.add_handler(handler_to_contact_room)


    def _to_contact_room_user(self) -> None:
        """
        Add handler, write record to table `contact_room_user`.
        """


        # Define.
        def handler_to_contact_room_user(rmessage: RMessage) -> None:
            """
            Write record to table `contact_room_user`.

            Parameters
            ----------
            rmessage : `RMessage` instance.
            """

            # Add memeber.
            if rmessage.is_new_room_user:

                ## Sleep.
                sleep(1)

                ## Insert.
                self.update_contact_room_user(rmessage.room)


        # Add handler.
        self.rwechat.rreceive.add_handler(handler_to_contact_room_user)


    def _to_message_receive(self) -> None:
        """
        Add handler, write record to table `message_receive`.
        """


        # Define.
        def handler_to_message_receive(rmessage: RMessage) -> None:
            """
            Write record to table `message_receive`.

            Parameters
            ----------
            rmessage : `RMessage` instance.
            """

            # Upload file.
            if rmessage.file is None:
                file_id = None
            else:
                file_id = self.rrdatabase_file.file.upload(
                    rmessage.file["path"],
                    rmessage.file["name"],
                    "WeChat"
                )

            # Generate data.
            message_time_obj = to_time(rmessage.time)
            message_time_str = time_to(message_time_obj)
            data = {
                "message_time": message_time_str,
                "message_id": rmessage.id,
                "room_id": rmessage.room,
                "user_id": rmessage.user,
                "type": rmessage.type,
                "data": rmessage.data,
                "file_id": file_id
            }

            # Insert.
            self.rrdatabase_wechat.execute_insert(
                ("wechat", "message_receive"),
                data,
                "ignore"
            )


        # Add handler.
        self.rwechat.rreceive.add_handler(handler_to_message_receive)


    def _to_message_send(self) -> None:
        """
        Add handler, write record to table `message_send`.
        """


        # Define.
        def handler_to_message_send(rsparam: RSendParam) -> None:
            """
            Write record to table `message_send`.

            Parameters
            ----------
            rsparam : `RSendParams` instance.
            """

            # Break.
            if rsparam.send_id is not None: return

            # Generate data.
            path = rsparam.params.get("path")
            params = {
                key: value
                for key, value in rsparam.params.items()
                if key not in (
                    "send_type",
                    "receive_id",
                    "path"
                )
            }

            ## Upload file.
            if path is not None:
                file_id = self.rrdatabase_file.file.upload(
                    path,
                    note="WeChat"
                )
                params["file_id"] = file_id

            if rsparam.exc_reports == []:
                status = 2
            else:
                status = 3
            data = {
                "status": status,
                "type": rsparam.send_type,
                "receive_id": rsparam.receive_id,
                "parameter": params
            }

            # Insert.
            self.rrdatabase_wechat.execute_insert(
                ("wechat", "message_send"),
                data
            )


        # Add handler.
        self.rwechat.rsend.add_handler(handler_to_message_send)


    def _download_file(
        self,
        file_id: int
    ) -> Tuple[str, str]:
        """
        Download file by ID.

        Parameters
        ----------
        file_id : File ID.

        Returns
        -------
        File save path and file name.
        """

        # Select.
        file_info = self.rrdatabase_file.file.query(file_id)

        # Check.
        file_md5 = file_info["md5"]
        rfolder = RFolder(self.rwechat.dir_file)
        pattern = f"^{file_md5}$"
        search_path = rfolder.search(pattern)

        # Download.
        if search_path is None:
            save_path = "%s/%s" % (
                self.rwechat.dir_file,
                file_md5
            )
            save_path = self.rrdatabase_file.file.download(
                file_id,
                save_path
            )
        else:
            save_path = search_path

        file_name = file_info["name"]
        return save_path, file_name


    def _from_message_send(self) -> None:
        """
        Read record from table `message_send`, put send queue.
        """

        # Get parameter.
        conn = self.rrdatabase_wechat.connect()

        # Read.
        where = (
            "(\n"
            "    `status` = 0\n"
            "    AND (\n"
            "        `plan_time` IS NULL\n"
            "        OR `plan_time` < NOW()\n"
            "    )\n"
            ")"
        )
        result = conn.execute_select(
            ("wechat", "message_send"),
            ["send_id", "type", "receive_id", "parameter"],
            where,
            order="`plan_time` DESC, `send_id`"
        )

        # Convert.
        if result.empty:
            return
        table = result.fetch_table()

        # Update.
        send_ids = [
            row["send_id"]
            for row in table
        ]
        sql = (
            "UPDATE `wechat`.`message_send`\n"
            "SET `status` = 1\n"
            "WHERE `send_id` IN :send_ids"
        )
        conn.execute(
            sql,
            send_ids=send_ids
        )

        # Send.
        for row in table:
            send_id, type_, receive_id, parameter = row.values()
            parameter: Dict = json_loads(parameter)

            ## Save file.
            file_id = parameter.get("file_id")
            if file_id is not None:
                file_path, file_name = self._download_file(file_id)
                parameter["path"] = file_path
                parameter["file_name"] = file_name

            self.rwechat.send(
                type_,
                receive_id,
                send_id,
                **parameter
            )

        # Commit.
        conn.commit()


    @wrap_thread
    def _from_message_send_loop(self) -> None:
        """
        In the thread, loop read record from table `message_send`, put send queue.
        """


        # Define.
        def handler_update_send_status(rsparam: RSendParam) -> None:
            """
            Update field `status` of table `message_send`.

            Parameters
            ----------
            rsparam : `RSendParams` instance.
            """

            # Break.
            if rsparam.send_id is None:
                return

            # Get parameter.
            if rsparam.exc_reports == []:
                status = 2
            else:
                status = 3
            data = {
                "send_id": rsparam.send_id,
                "status": status,
                "limit": 1
            }

            # Update.
            self.rrdatabase_wechat.execute_update(
                ("wechat", "message_send"),
                data
            )


        # Add handler.
        self.rwechat.rsend.add_handler(handler_update_send_status)

        # Loop.
        while True:

            # Put.
            self._from_message_send()

            # Wait.
            sleep(1)


def is_valid(rmessage: RMessage) -> bool:
    """
    Judge if is valid user or chat room from database.

    Parameters
    ----------
    rmessage : `RMessage` instance.

    Returns
    -------
    Judgment result.
        - `True` : Valid.
        - `False` : Invalid or no record.
    """

    # Judge.

    ## User.
    if rmessage.room is None:
        result = rmessage.rreceive.rwechat.rdatabase.rrdatabase_wechat.execute_select(
            ("wechat", "contact_user"),
            ["valid"],
            "`user_id` = :user_id",
            limit=1,
            user_id=rmessage.user
        )

    ## Room.
    else:
        sql = (
        "SELECT (\n"
        "    SELECT `valid`\n"
        "    FROM `wechat`.`contact_room_user`\n"
        "    WHERE `room_id` = :room_id AND `user_id` = :user_id\n"
        "    LIMIT 1\n"
        ") AS `valid`\n"
        "FROM (\n"
        "    SELECT `valid`\n"
        "    FROM `wechat`.`contact_room`\n"
        "    WHERE `room_id` = :room_id\n"
        "    LIMIT 1\n"
        ") AS `a`\n"
        "WHERE `valid` = 1"
        )
        result = rmessage.rreceive.rwechat.rdatabase.rrdatabase_wechat.execute(
            sql,
            room_id=rmessage.room,
            user_id=rmessage.user
        )

    valid = result.scalar()
    judge = valid == 1

    return judge