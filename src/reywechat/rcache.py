# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-13 22:58:31
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Cache methods.
"""


from os.path import join as os_join
from reykit.ros import Folder

from .rbase import BaseWeChat
from .rwechat import WeChat


__all__ = (
    'WeChatCache',
)


class WeChatCache(BaseWeChat):
    """
    WeChat cache type.
    """


    def __init__(
        self,
        wechat: WeChat
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        wechat : `WeChatClient` instance.
        """

        # Set attribute.
        self.wechat = wechat

        # Make directory.
        self.folder = self.__make_dir()


    def __make_dir(self) -> Folder:
        """
        Make directory 'project_dir/cache'.

        Parameters
        ----------
        project_dir: Project directory.

        Returns
        -------
        Folder instance.
        """

        # Set parameter.
        dir_path = os_join(self.wechat.project_dir, 'cache')

        # Make.
        folder = Folder(dir_path)
        folder.make()

        return folder
