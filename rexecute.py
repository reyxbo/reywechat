# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-16 16:20:34
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Execute methods.
"""


from typing import Any, List, TypedDict, Literal, Callable, NoReturn
from reykit.rexception import catch_exc

from .rexception import RWeChatExecuteContinueError, RWeChatExecuteBreakError
from .rreceive import RMessage, RReceive


__all__ = (
    'RExecute',
)


Rule = TypedDict('Rule', {'mode': Literal['trigger', 'reply'], 'executer': Callable[[RMessage], None], 'level': float})


class RExecute(object):
    """
    Rey's `execute` type.
    """


    def __init__(
        self,
        rreceive: RReceive
    ) -> None:
        """
        Build `execute` instance.

        Parameters
        ----------
        rreceive : `RReceive` instance.
        """

        # Set attribute.
        self.rreceive = rreceive
        self.rules: List[Rule] = []

        # Add handler.
        self.handler = self._execute_by_rule()

        # Add executer.
        self._add_execute_valid()


    def _execute_by_rule(self) -> Callable[[RMessage], None]:
        """
        Add handler, execute message by rules.

        Returns
        -------
        Handler.
        """


        # Define.
        def handler_execute_by_rule(rmessage: RMessage) -> None:
            """
            Execute message by rules.

            Parameters
            ----------
            rmessage : `RMessage` instance.
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
                except RWeChatExecuteContinueError:
                    continue

                # Break.
                except RWeChatExecuteBreakError:
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
        executer: Callable[[RMessage], Any],
        level: float = 0
    ) -> None:
        """
        Add execute rule.

        Parameters
        ----------
        mode : Execute mode.
        executer : Function of execute. The parameter is the `RMessage` instance.
            When throw `RWeChatExecuteContinueError` type exception, then continue next execution.
            When throw `RWeChatExecuteBreakError` type exception, then stop executes.
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
        Continue execute by throwing `RWeChatExecuteContinueError` type exception.
        """

        # Raise.
        raise RWeChatExecuteContinueError


    def break_(self) -> NoReturn:
        """
        Break execute by throwing `RWeChatExecuteBreakError` type exception.
        """

        # Raise.
        raise RWeChatExecuteBreakError


    def _add_execute_valid(self) -> None:
        """
        Add executer, execute rule judge valid.

        Returns
        -------
        Handler.
        """


        # Define.
        def execute_valid(rmessage: RMessage) -> None:
            """
            Execute rule judge valid.

            Parameters
            ----------
            rmessage : `RMessage` instance.
            """

            # Judge.
            if not rmessage.valid:

                # Break.
                rmessage.execute_break()


        # Add.
        self.add_rule('trigger', execute_valid, float('inf'))
