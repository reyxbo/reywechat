# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-17 10:49:26
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Exception methods.
"""


from reytool.rexception import RError


__all__ = (
    "RWeChatError",
    "RWeChatExecuteError",
    "RWeChatExecuteContinueError",
    "RWeChatExecuteBreakError"
)


class RWeChatError(RError):
    """
    Rey's `WeChat error` type.
    """


class RWeChatExecuteError(RWeChatError):
    """
    Rey's `WeChat execute error` type.
    """


class RWeChatExecuteContinueError(RWeChatExecuteError):
    """
    Rey's `WeChat execute continue error` type.
    """


class RWeChatExecuteBreakError(RWeChatExecuteError):
    """
    Rey's `WeChat execute break error` type.
    """