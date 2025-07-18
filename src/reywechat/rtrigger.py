# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-16 16:20:34
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Trigger methods.
"""


from typing import Any, TypedDict, Literal, NoReturn
from collections.abc import Callable
from reykit.rbase import catch_exc

from .rbase import BaseWeChat, WeChatTriggerContinueExit, WeChatTriggerBreakExit
from .rreceive import WeChatMessage, WechatReceive


__all__ = (
    'WeChatTrigger',
)


TriggerRule = TypedDict('TriggerRule', {'mode': Literal['trigger', 'reply'], 'executer': Callable[[WeChatMessage], None], 'level': float})


class WeChatTrigger(BaseWeChat):
    """
    WeChat trigger type.
    """


    def __init__(
        self,
        rreceive: WechatReceive
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rreceive : `WechatReceive` instance.
        """

        # Set attribute.
        self.rreceive = rreceive
        self.rules: list[TriggerRule] = []

        # Add handler.
        self.handler = self._execute_by_rule()

        # Add executer.
        self._add_execute_valid()


    def _execute_by_rule(self) -> Callable[[WeChatMessage], None]:
        """
        Add handler, execute message by rules.

        Returns
        -------
        Handler.
        """


        # Define.
        def handler_execute_by_rule(rmessage: WeChatMessage) -> None:
            """
            Execute message by rules.

            Parameters
            ----------
            rmessage : `WeChatMessage` instance.
            """

            # Loop.
            for rule in self.rules:
                rmessage.ruling = rule

                # Break.
                if (
                    rule['mode'] == 'reply'
                    and rmessage.replied
                ):
                    break

                # Execute.
                try:
                    rule['executer'](rmessage)

                # Continue.
                except WeChatTriggerContinueExit:
                    continue

                # Break.
                except WeChatTriggerBreakExit:
                    break

                # Exception.
                except:

                    ## Catch exception.
                    exc_report, *_ = catch_exc()

                    ## Save.
                    rmessage.exc_reports.append(exc_report)

                finally:
                    rmessage.ruling = None


        # Add handler.
        self.rreceive.add_handler(handler_execute_by_rule)

        return handler_execute_by_rule


    def add_rule(
        self,
        mode: Literal['trigger', 'reply'],
        executer: Callable[[WeChatMessage], Any],
        level: float = 0
    ) -> None:
        """
        Add execute rule.

        Parameters
        ----------
        mode : Execute mode.
        executer : Function of execute. The parameter is the `WeChatMessage` instance.
            When throw `WeChatTriggerContinueExit` type exception, then continue next execution.
            When throw `WeChatTriggerBreakExit` type exception, then stop executes.
        level : Priority level, sort from large to small.
        """

        # Get parameter.
        rule = {
            'mode': mode,
            'executer': executer,
            'level': level
        }

        # Add.
        self.rules.append(rule)

        # Sort.
        fund_sort = lambda rule: rule['level']
        self.rules.sort(
            key=fund_sort,
            reverse=True
        )


    def continue_(self) -> NoReturn:
        """
        Continue execute by throwing `WeChatTriggerContinueExit` type exception.
        """

        # Raise.
        raise WeChatTriggerContinueExit


    def break_(self) -> NoReturn:
        """
        Break execute by throwing `WeChatTriggerBreakExit` type exception.
        """

        # Raise.
        raise WeChatTriggerBreakExit


    def _add_execute_valid(self) -> None:
        """
        Add executer, execute rule judge valid.

        Returns
        -------
        Handler.
        """


        # Define.
        def execute_valid(rmessage: WeChatMessage) -> None:
            """
            Execute rule judge valid.

            Parameters
            ----------
            rmessage : `WeChatMessage` instance.
            """

            # Judge.
            if not rmessage.valid:

                # Break.
                rmessage.execute_break()


        # Add.
        self.add_rule('trigger', execute_valid, float('inf'))
