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
    "RWeChatReplyError",
    "RWeChatExecuteError",
    "RWeChatContinueError",
    "RWeChatBreakError",
    "RWeChatReplyContinueError",
    "RWeChatReplyBreakError",
    "RWeChatExecuteContinueError",
    "RWeChatExecuteBreakError"
)


class RWeChatError(RError):
    """
    Rey's `WeChat error` type.
    """


class RWeChatReplyError(RWeChatError):
    """
    Rey's `WeChat reply error` type.
    """


class RWeChatExecuteError(RWeChatError):
    """
    Rey's `WeChat execute error` type.
    """


class RWeChatContinueError(RWeChatError, AssertionError):
    """
    Rey's `WeChat continue error` type.
    """


class RWeChatBreakError(RWeChatError, AssertionError):
    """
    Rey's `WeChat break error` type.
    """


class RWeChatReplyContinueError(RWeChatReplyError, RWeChatContinueError):
    """
    Rey's `WeChat reply continue error` type.
    """


class RWeChatReplyBreakError(RWeChatReplyError, RWeChatBreakError):
    """
    Rey's `WeChat reply break error` type.
    """


class RWeChatExecuteContinueError(RWeChatExecuteError, RWeChatContinueError):
    """
    Rey's `WeChat execute continue error` type.
    """


class RWeChatExecuteBreakError(RWeChatExecuteError, RWeChatBreakError):
    """
    Rey's `WeChat execute break error` type.
    """