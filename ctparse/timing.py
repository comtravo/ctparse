from time import perf_counter
from functools import wraps


class CTParseTimeoutError(Exception):
    pass


def timeout(timeout_: float):
    start_time = perf_counter()

    def _tt():
        if timeout_ == 0:
            return
        if perf_counter() - start_time > timeout_:
            raise CTParseTimeoutError()
    return _tt


def timeit(f):
    """timeit wrapper, use as `timeit(f)(args)

    Will return a tuple (f(args), t) where t the time in seconds the function call
    took to run.

    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        res = f(*args, **kwargs)
        return res, perf_counter() - start_time
    return wrapper
