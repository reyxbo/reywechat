# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-16 16:20:34
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Execute methods.
"""


from typing import Any, List, Dict, Literal, Callable, NoReturn

from .rreceive import RMessage, RStopError, is_valid
from .rwechat import RWeChat


__all__ = (
    "RExecuteStopError",
    "RExecute"
)


class RExecuteStopError(RStopError):
    """
    Rey's `execute stop error` type.
    """


class RExecute(object):
    """
    Rey's `execute` type.
    """


    def __init__(
        self,
        rwechat: RWeChat
    ) -> None:
        """
        Build `execute` instance.

        Parameters
        ----------
        rwechat : `RWeChat` instance.
        """

        # Set attribute.
        self.rwechat = rwechat
        self.rules: List[Dict[Literal["executer", "level"], Any]] = []

        # Add handler.
        self._execute_by_rule()


    def _execute_by_rule(self) -> None:
        """
        Add handler, execute message by rules.
        """


        # Define.
        def handler_execute_by_rule(message: RMessage) -> None:
            """
            Execute message by rules.

            Parameters
            ----------
            message : `RMessage` instance.
            """

            # Valid.
            if is_valid(message) is False:
                return

            # Loop.
            for rule in self.rules:
                executer: Callable[[RMessage], Any] = rule["executer"]

                # Execute.
                try:
                    executer(message)

                # Stop.
                except RExecuteStopError:
                    break


        # Add handler.
        self.rwechat.rreceive.add_handler(handler_execute_by_rule)


    def add_rule(
        self,
        executer: Callable[[RMessage], Any],
        level: float = 0
    ) -> None:
        """
        Add execute rule.

        Parameters
        ----------
        executer : Function of execute. The parameter is the `RMessage` instance.
        When throw `RExecuteStopError` type exception, then stop executes.
        level : Priority level, sort from large to small.
        """

        # Get parameter.
        rule = {
            "executer": executer,
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


    def stop(self) -> NoReturn:
        """
        Stop reply by throwing `RExecuteStopError` type exception.
        """

        # Raise.
        raise RExecuteStopError