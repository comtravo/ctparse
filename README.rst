===========================================================
ctparse - Parse natural language time expressions in python
===========================================================


Build Status`_

.. image:: https://img.shields.io/pypi/v/ctparse.svg
        :target: https://pypi.python.org/pypi/ctparse

.. image:: https://img.shields.io/travis/comtravo/ctparse.svg
        :target: https://travis-ci.org/comtravo/ctparse

.. image:: https://readthedocs.org/projects/ctparse/badge/?version=latest
        :target: https://ctparse.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Parse natural language time expressions in python


* Free software: MIT license
* Documentation: https://ctparse.readthedocs.io.


**This code is in early alpha stage. There can and will be potentially
breaking changes right on the ``master`` branch**


Comtravo Time Parser
====================

Background
----------

The package ``ctparse`` is a pure python package to parse time
expressions from natural language (i.e. strings). In many ways it builds
on similar concepts as Facebook’s ``duckling`` package
(https://github.com/facebook/duckling). However, for the time being it
only targets times and only German and English text.

In principle ``ctparse`` can be used to **detect** time expressions in a
text, however its main use case is the semantic interpretation of such
expressions. Detecting time expressions in the first place can - to our
experience - be done more efficiently (and precisely) using e.g. CRFs or
other models targeted at this specific task.

``ctparse`` is designed with the use case in mind where interpretation
of time expressions is done under the following assumptions:

-  All expressions are relative to some pre-defined reference times
-  Unless explicitly specified in the time expression, valid resolutions
   are in the future relative to the reference time (i.e. ``12.5.`` will
   be the next 12th of May, but ``12.5.2012`` should correctly resolve
   to the 12th of May 2012).
-  If in doubt, resolutions in the near future are more likely than
   resolutions in the far future (not implemented yet, but any
   resolution more than i.e. 3 month in the future is extremely
   unlikely).

The specific comtravo use-case is resolving time expressions in booking
requests which almost always refer to some point in time within the next
4-8 weeks.

``ctparse`` currently is language agnostic and supports German and
English expressions. This might get an extension in the future. The main
reason is that in real world communication more often than not people
write in one language (their business language) but use constructs to
express times that are based on their mother tongue and/or what they
believe to be the way to express dates in the target language. This
leads to text in German with English time expressions and vice-versa.
Using a language detection upfront on the complete original text is for
obvious no solution - rather it would make the problem worse.

Example
-------

.. code:: python

   from ctparse import ctparse
   from datetime import datetime

   # Set reference time
   ts = datetime(2018, 3, 12, 14, 30)
   ctparse('May 5th 2:30 in the afternoon', ts=ts)

This should return a ``Time`` object represented as
``Time[0-29]{2018-05-05 14:30 (X/X)}``, indicating that characters
``0-29`` were used in the resolution, that the resolved date time is the
5th of May 2018 at 14:30 and that this resolution is neither based on a
day of week (first ``X``) nor a part of day (second ``X``).

Implementation
--------------

``ctparse`` - as ``duckling`` - is a mixture of a rule and regular
expression based system + some probabilistic modeling. In this sense it
resembles a PC


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Build Status: https://travis-ci.org/comtravo/ctparse
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
