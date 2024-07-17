# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-07-15 15:19:38
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Decorator methods.
"""


from typing import Any, List, Callable, Union
from functools import wraps as functools_wraps
from reytool.rexception import catch_exc

from .rexception import RWeChatContinueError, RWeChatBreakError
from .rwechat import RWeChat


__all__ = (
    "wrap_try_send",
)


def wrap_try_send(
    rwechat: RWeChat,
    receive_id: Union[str, List[str]],
    func: Callable
) -> Callable:
    """
    Decorator, send exception information.

    Parameters
    ----------
    rwechat : `RWeChat` instance.
    receive_id : Receive user ID or chat room ID.
        - `str` : An ID.
        - `List[str]` : Multiple ID.

    func : Function.

    Returns
    -------
    Decorated function.
    """

    # Handle parameter.
    if receive_id.__class__ == str:
        receive_ids = [receive_id]
    else:
        receive_ids = receive_id

    # Define.
    @functools_wraps(func)
    def wrap(
        *arg: Any,
        **kwargs: Any
    ) -> Any:
        """
        Decorate.

        Parameters
        ----------
        args : Position arguments of decorated function.
        kwargs : Keyword arguments of decorated function.

        Returns
        -------
        Function execution result.
        """

        # Execute.
        try:
            result = func(
                *arg,
                **kwargs
            )
        except:
            _, _, exc_instance, _ = catch_exc()

            # Report.
            if not isinstance(
                exc_instance,
                (RWeChatContinueError, RWeChatBreakError)
            ):
                text = "\n".join(
                    [
                        str(arg)
                        for arg in exc_instance.args
                    ]
                )
                for receive_id in receive_ids:
                    rwechat.rsend.send(
                        0,
                        receive_id,
                        text=text
                    )

            # Throw exception.
            raise exc_instance

        return result


    return wrap