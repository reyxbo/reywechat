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
from .rreceive import WeChatMessage, WechatReceiver


__all__ = (
    'WeChatTrigger',
)


TriggerRule = TypedDict('TriggerRule', {'level': float, 'execute': Callable[[WeChatMessage], None], 'is_reply': bool})


class WeChatTrigger(BaseWeChat):
    """
    WeChat trigger type.
    """


    def __init__(
        self,
        receiver: WechatReceiver
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        receiver : `WechatReceiver` instance.
        """

        # Set attribute.
        self.receiver = receiver
        self.rules: list[TriggerRule] = []

        # Add handler.
        self.handler = self._trigger_by_rule()

        # Add trigger.
        self._add_trigger_valid()


    def _trigger_by_rule(self) -> Callable[[WeChatMessage], None]:
        """
        Add handler, trigger message by rules.

        Returns
        -------
        Handler.
        """


        # Define.
        def handler_trigger_by_rule(message: WeChatMessage) -> None:
            """
            Trigger message by rules.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Loop.
            for rule in self.rules:
                message.trigger_rule = rule

                # Replied.
                if (
                    message.replied
                    and rule['is_reply']
                ):
                    continue

                # Trigger.
                try:
                    rule['execute'](message)

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
                    message.exc_reports.append(exc_report)

                finally:
                    message.trigger_rule = None


        # Add handler.
        self.receiver.add_handler(handler_trigger_by_rule)

        return handler_trigger_by_rule


    def add_rule(
        self,
        execute: Callable[[WeChatMessage], Any],
        level: float = 0
    ) -> None:
        """
        Add trigger rule.

        Parameters
        ----------
        execute : Trigger execute function. The parameter is the `WeChatMessage` instance.
            Function name must start with `reply_` to allow use of `WeChatMessage.reply`.
            When throw `WeChatTriggerContinueExit` type exception, then continue next execution.
            When throw `WeChatTriggerBreakExit` type exception, then stop executes.
        level : Priority level, sort from large to small.
        """

        # Get parameter.
        rule: TriggerRule = {
            'level': level,
            'execute': execute,
            'is_reply': execute.__name__.startswith('reply_')
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
        Continue trigger by throwing `WeChatTriggerContinueExit` type exception.
        """

        # Raise.
        raise WeChatTriggerContinueExit


    def break_(self) -> NoReturn:
        """
        Break trigger by throwing `WeChatTriggerBreakExit` type exception.
        """

        # Raise.
        raise WeChatTriggerBreakExit


    def _add_trigger_valid(self) -> None:
        """
        Add trigger, trigger rule judge valid.

        Returns
        -------
        Handler.
        """


        # Define.
        def trigger_valid(message: WeChatMessage) -> None:
            """
            Trigger rule judge valid.

            Parameters
            ----------
            message : `WeChatMessage` instance.
            """

            # Judge.
            if not message.valid:

                # Break.
                message.trigger_break()


        # Add.
        self.add_rule(trigger_valid, float('inf'))
