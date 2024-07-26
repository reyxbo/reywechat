# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-10 16:24:10
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Reply methods.
"""


from typing import Any, List, Dict, Literal, Callable, NoReturn

from .rexception import RWeChatReplyContinueError, RWeChatReplyBreakError
from .rreceive import RMessage, RReceive, is_valid
from .rsend import SendParam


__all__ = (
    "RReply",
)


class RReply(object):
    """
    Rey's `reply` type.
    """


    def __init__(
        self,
        rreceive: RReceive
    ) -> None:
        """
        Build `reply` instance.

        Parameters
        ----------
        rreceive : `RReceive` instance.
        """

        # Set attribute.
        self.rreceive = rreceive
        self.rules: List[Dict[Literal["judge", "level"], Any]] = []

        # Add handler.
        self.handler = self._reply_by_rule()


    def _reply_by_rule(self) -> Callable[[RMessage], None]:
        """
        Add handler, reply message by rules.

        Returns
        -------
        Handler.
        """


        # Define.
        def handler_reply_by_rule(message: RMessage) -> None:
            """
            Reply message by rules.

            Parameters
            ----------
            message : `RMessage` instance.
            """

            # Valid.
            if is_valid(message) is False:
                return

            # Loop.
            for rule in self.rules:
                judge: Callable[[RMessage], SendParam] = rule["judge"]

                # Judge.
                try:
                    result = judge(message)

                # Continue.
                except RWeChatReplyContinueError:
                    continue

                # Break.
                except RWeChatReplyBreakError:
                    break

                # Fail.
                if result is None:
                    continue

                # Send.
                if result.__class__ == dict:
                    result = [result]
                for params in result:
                    self.rreceive.rwechat.rsend.send(**params)

                break


        # Add handler.
        self.rreceive.add_handler(handler_reply_by_rule)

        return handler_reply_by_rule


    def add_rule(
        self,
        judge: Callable[[RMessage], SendParam],
        level: float = 0
    ) -> None:
        """
        Add reply rule.

        Parameters
        ----------
        judge : Function of judgment and generate send message parameters. The parameter is the `RMessage` instance.
        When throw `RReplyBreakError` type exception, then stop executes.
            - `Return None` : Judgment failed, continue next rule.
            - `Return Dict` : Send a message and breaking judgment.
            - `Return List[Dict]` : Send multiple messages and breaking judgment.

        level : Priority level, sort from large to small.
        """

        # Get parameter.
        rule = {
            "judge": judge,
            "level": level
        }

        # Add.
        self.rules.append(rule)

        # Sort.
        fund_sort = lambda rule: rule["level"]
        self.rules.sort(
            key=fund_sort,
            reverse=True
        )


    def continue_(self) -> NoReturn:
        """
        Continue reply by throwing `RWeChatReplyContinueError` type exception.
        """

        # Raise.
        raise RWeChatReplyContinueError


    def break_(self) -> NoReturn:
        """
        Break reply by throwing `RWeChatReplyBreakError` type exception.
        """

        # Raise.
        raise RWeChatReplyBreakError