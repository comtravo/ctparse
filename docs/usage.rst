=====
Usage
=====

To use ctparse simply import the main ``ctparse`` function::

    
    from datetime import datetime
    from ctparse import ctparse

    ctparse('today', datetime(2018, 7, 8), timeout=1)
    
The output for the above code is `2018-07-08 X:X (X/X) s=2.273 p=(149, 'ruleToday')`

For more details on the parameters please see the docstrings.
