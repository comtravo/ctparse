===========================================================
ctparse - Parse natural language time expressions in python
===========================================================


.. image:: https://travis-ci.org/comtravo/ctparse.svg?branch=master
     :target: https://travis-ci.org/comtravo/ctparse
     :alt: Travis

.. image:: https://codecov.io/gh/comtravo/ctparse/branch/master/graph/badge.svg
     :target: https://codecov.io/gh/comtravo/ctparse
     :alt: Coverage

.. image:: https://img.shields.io/pypi/v/ctparse.svg
     :target: https://pypi.python.org/pypi/ctparse
     :alt: PyPi

.. image:: https://pyup.io/repos/github/comtravo/ctparse/shield.svg
     :target: https://pyup.io/repos/github/comtravo/ctparse/
     :alt: Updates

.. image:: https://readthedocs.org/projects/ctparse/badge/?version=latest
     :target: https://ctparse.readthedocs.io/en/latest/?badge=latest
     :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


**This code is in early alpha stage. There can and will be potentially
breaking changes right on the ``master`` branch**


* Free software: MIT license
* Documentation: https://ctparse.readthedocs.io.


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


Latent time
~~~~~~~~~~~

Normally, ``ctparse`` will anchor time expressions to the reference time. 
For example, when parsing the time expression ``8:00 pm``, ctparse will
resolve the expression to 8 pm after the reference time as follows

.. code:: python

   parse = ctparse("8:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=True) # default
   # parse.resolution -> Time(2020, 1, 1, 20, 00)

This behavior can be customized using the option ``latent_time=False``, which will
return a time resolution not anchored to a particular date

.. code:: python

   parse = ctparse("8:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=False)
   # parse.resolution -> Time(None, None, None, 20, 00)

Implementation
--------------

``ctparse`` - as ``duckling`` - is a mixture of a rule and regular
expression based system + some probabilistic modeling. In this sense it
resembles a PCFG.

Rules
~~~~~

At the core ``ctparse`` is a collection of production rules over
sequences of regular expressions and (intermediate) productions.

Productions are either of type ``Time``, ``Interval`` or ``Duration`` and can
have certain predicates (e.g. whether a ``Time`` is a part of day like
``'afternoon'``).

A typical rule than looks like this:

.. code:: python

   @rule(predicate('isDate'), dimension(Interval))

I.e. this rule is applicable when the intermediate production resulted
in something that has a date, followed by something that is in interval
(like e.g. in ``'May 5th 9-10'``).

The actual production is a python function with the following signature:

.. code:: python

   @rule(predicate('isDate'), dimension(Interval))
   def ruleDateInterval(ts, d, i):
     """
     param ts: datetime - the current refenrence time
     d: Time - a time that contains at least a full date
     i: Interval - some Interval
     """
     if not (i.t_from.isTOD and i.t_to.isTOD):
       return None
     return Interval(
       t_from=Time(year=d.year, month=d.month, day=d.day,
                   hour=i.t_from.hour, minute=i.t_from.minute),
       t_to=Time(year=d.year, month=d.month, day=d.day,
                 hour=i.t_to.hour, minute=i.t_to.minute))

This production will return a new interval at the date of
``predicate('isDate')`` spanning the time coded in
``dimension(Interval)``. If the latter does code for something else than
a time of day (TOD), no production is returned, e.g. the rule matched
but failed.


Technical Background
~~~~~~~~~~~~~~~~~~~~

Some observations on the problem:

-  Each rule is a combination of regular expressions and productions.
-  Consequently, each production must originate in a sequence of regular
   expressions that must have matched (parts of) the text.
-  Hence, only subsequence of **all** regular expressions in **all**
   rules can lead to a successful production.

To this end the algorithm proceeds as follows:

1. Input a string and a reference time
2. Find all matches of all regular expressions from all rules in the
   input strings. Each regular expression is assigned an identifier.
3. Find all distinct sequences of these matches where two matches do not
   overlap nor have a gap inbetween
4. To each such subsequence apply all rules at all possible positions
   until no further rules can be applied - in which case one solution is
   produced

Obviously, not all sequences of matching expressions and not all
sequences of rules applied on top lead to meaningful results. Here the
**P**\ CFG kicks in:

-  Based on example data (``corpus.py``) a model is calibrated to
   predict how likely a production is to lead to a/the correct result.
   Instead of doing a breadth first search, the most promising
   productions are applied first.
-  Resolutions are produced until there are no more resolutions or a
   timeout is hit.
-  Based on the same model from all resolutions the highest scoring is
   returned.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
