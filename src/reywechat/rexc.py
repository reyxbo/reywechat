# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-17 10:49:26
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Exception methods.
"""


from reykit.rexc import Error, ActiveError

from .rtype import WeChatBase


__all__ = (
    'WeChatError',
    'WeChatClientErorr',
    'WeChatExecuteError',
    'WeChatExecuteContinueError',
    'WeChatExecuteBreakError',
    'WeChatExecuteReplyError',
    'WeChatExecuteNoRuleReplyError',
    'WeChatExecuteTriggerReplyError'
)


class WeChatError(Error, WeChatBase):
    """
    WeChat error type.
    """


class WeChatClientErorr(WeChatError):
    """
    WeChat client exception type.
    """


class WeChatExecuteError(WeChatError):
    """
    WeChat execute error type.
    """


class WeChatExecuteContinueError(ActiveError, WeChatExecuteError):
    """
    WeChat execute continue error type.
    """


class WeChatExecuteBreakError(ActiveError, WeChatExecuteError):
    """
    WeChat execute break error type.
    """


class WeChatExecuteReplyError(WeChatExecuteError):
    """
    WeChat execute reply error type.
    """


class WeChatExecuteNoRuleReplyError(WeChatExecuteReplyError):
    """
    WeChat execute no rule reply error type.
    """


class WeChatExecuteTriggerReplyError(WeChatExecuteReplyError):
    """
    WeChat execute trigger function reply error type.
    """
