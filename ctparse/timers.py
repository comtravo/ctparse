"""Utilities for tracking time spent in functions.

Although this module is not part of the public API, it is used in various parts of
the ctparse package.

"""
from time import perf_counter
from typing import Any, Callable, TypeVar, Union, Tuple
from functools import wraps

T = TypeVar("T")


def timeout(timeout: Union[float, int]) -> Callable[[], None]:
    """Generate a functions that raises an exceptions if a timeout has passed.

    Example:

        sentinel = timeout(1.0)
        time.sleep(0.5)
        sentinel() # Do nothing
        time.sleep(0.6)
        sentinel() # Raises CTParseTimeoutException

    :param timeout:
       time in seconds. If it is equal to zero, it means to never raise an exception.
    :returns:
        A function that raises a `CTParseTimeoutException` if `timeout` seconds have
        expired.
    """
    start_time = perf_counter()

    def _tt() -> None:
        if timeout == 0:
            return
        if perf_counter() - start_time > timeout:
            raise CTParseTimeoutError()

    return _tt


def timeit(f: Callable[..., T]) -> Callable[..., Tuple[T, float]]:
    """Wrapper to time a function.

    The wrapped function is modified so that it returns a tuple `(f(args), t)`
    where `t` the time in seconds the function call took to run.

    Example:

        def fun(x):
            return x * x

        result, exec_time = timeit(fun)(3)

    """

    @wraps(f)
    def _wrapper(*args: Any, **kwargs: Any) -> Tuple[T, float]:
        start_time = perf_counter()
        res = f(*args, **kwargs)
        return res, perf_counter() - start_time

    return _wrapper


# NOTE: TimeoutError is a built-in exception that means that
# system function timed out at the system level. Hence we opt
# for a custom exception.
class CTParseTimeoutError(Exception):
    """Exception raised by the `timeout` function."""
