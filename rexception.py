# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-17 10:49:26
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Exception methods.
"""


from reytool.rtype import RError, RActiveError


__all__ = (
    "RWeChatError",
    "RWeChatExecuteError",
    "RWeChatExecuteContinueError",
    "RWeChatExecuteBreakError",
    "RWeChatExecuteReplyError",
    "RWeChatExecuteNoRuleReplyError",
    "RWeChatExecuteTriggerReplyError"
)


class RWeChatError(RError):
    """
    Rey's `WeChat error` type.
    """


class RWeChatExecuteError(RWeChatError):
    """
    Rey's `WeChat execute error` type.
    """


class RWeChatExecuteContinueError(RActiveError, RWeChatExecuteError):
    """
    Rey's `WeChat execute continue error` type.
    """


class RWeChatExecuteBreakError(RActiveError, RWeChatExecuteError):
    """
    Rey's `WeChat execute break error` type.
    """


class RWeChatExecuteReplyError(RWeChatExecuteError):
    """
    Rey's `WeChat execute reply error` type.
    """


class RWeChatExecuteNoRuleReplyError(RWeChatExecuteReplyError):
    """
    Rey's `WeChat execute no rule reply error` type.
    """


class RWeChatExecuteTriggerReplyError(RWeChatExecuteReplyError):
    """
    Rey's `WeChat execute trigger function reply error` type.
    """