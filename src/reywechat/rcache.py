# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-13 22:58:31
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Cache methods.
"""


from reykit.ros import FileCache, join_path

from .rbase import BaseWeChat
from .rwechat import WeChat


__all__ = (
    'WeChatCache',
)


class WeChatCache(BaseWeChat, FileCache):
    """
    WeChat file cache type.
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
        path = join_path(self.wechat.project_dir, 'cache')
        self.cache = FileCache(path)
        self.folder = self.cache.folder
        self.index = self.cache.index
        self.store = self.cache.store
