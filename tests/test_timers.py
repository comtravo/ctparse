from ctparse.timers import timeout, CTParseTimeoutError, timeit
from unittest import TestCase
import time


class TimersTest(TestCase):
    def test_timeout(self):
        t_fun = timeout(0.5)
        with self.assertRaises(CTParseTimeoutError):
            time.sleep(1.0)
            t_fun()
        t_fun = timeout(0)
        t_fun()  # all good

    def test_timeit(self):
        def fun(x):
            return x * x

        result, elapsed = timeit(fun)(3)
        self.assertEqual(result, 9)
        self.assertIsInstance(elapsed, float)
