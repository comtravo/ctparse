============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:


Add Rules & Increase Coverage
-----------------------------

If you find an expressions that ``ctparse`` can not resolve correctly
but you feel it should do, you can adjust the existing rules or add a
new one.

The following steps are probably a helpful guideline.

* Add your case to the ``corpus.py`` file and run the corpus tests
  using ``py.test tests/test_corpus.py``. Now basically two things can happen:

  #. **The tests pass**, which means ``ctparse`` can correctly resolve
     the expression. It might not score it highest. To check this,
     rebuild the model and try parsing the expression again:

     .. code:: bash

            make train

     To avoid issues with reloading, please restart the python
     interpreter after regenerating the model.

     If this fixes the issue please commit the updated ``corpus.py``
     and the updated model as a pull request (PR) on GitHub, see this guide for
     more information on what pull requests are and how to create them
     https://help.github.com/articles/creating-a-pull-request/.

     The scoring can be influenced by
     adding more structurally identical examples to the corpus. Seeing
     more samples where a specific sequence of rule applications leads
     to the correct ranking will drive the model to favor these. This
     comes, however, at the potential price of downranking certain
     other production sequences. Although it would generally be
     considered more favorable to add varying test cases (e.g. in
     different languages, slight variation) to the corpus, the same
     string can also just be duplicated to achive this *implict
     up-weightning* effect. The examples that are intended to influence the scoring,
     as opposed to the ones used to develop new rules, are usually appended
     to the file ``auto_corpus.py```.

  #. **The tests fail**: if this is because not all tests in the
     corpus pass, i.e. you get an error message like the following::

       ctparse.py 527 WARNING  failure: target "Time[]{2019-X-X X:X (X/X)}" never produced in "2019"
       ctparse.py 532 WARNING  failure: "Time[]{2019-X-X X:X (X/X)}" not always produced

* If the tests fail, run ``ctparse`` in debug mode to see what goes wrong:

  .. code:: python

     import logging
     from ctparse import ctparse
     from ctparse.ctparse import logger
     from datetime import datetime

     logger.addHandler(logging.StreamHandler())
     logger.setLevel(logging.DEBUG)

     # Set reference time
     ts = datetime(2018, 3, 12, 14, 30)
     r = list(ctparse('May 5th', ts=ts, debug=True))


  This gives you plenty of debugging output. First you will see
  the individual regular expressions that were matched (and the time
  this took)::

    ================================================================================
    -> matching regular expressions
    regex: RegexMatch[0-3]{114:May}
    regex: RegexMatch[4-5]{133:5}
    regex: RegexMatch[4-7]{135:5th}
    regex: RegexMatch[4-5]{134:5}
    regex: RegexMatch[4-5]{148:5}
    time in _match_regex: 1ms
    ================================================================================

  Each line has the form ``regex: RegexMatch[0-3]{114:May}`` and describes
  the matched span in the text ``[0-3]``, the ID of the matching expression
  ``114`` and the surface string that the expression matched ``May``.

  If relevant parts of your expression were not picked up, this is an
  indicator that you should either modify an existing regular
  expression or need to add a new rule (see below).

  Next you see the unique sub-sequences constructed based on these
  regular expressions (plus again the time used to build them)::

    ================================================================================
    -> building initial stack
    regex stack (RegexMatch[0-3]{114:May}, RegexMatch[4-7]{135:5th})
    regex stack (RegexMatch[0-3]{114:May}, RegexMatch[4-5]{148:5})
    regex stack (RegexMatch[0-3]{114:May}, RegexMatch[4-5]{134:5})
    regex stack (RegexMatch[0-3]{114:May}, RegexMatch[4-5]{133:5})
    time in _regex_stack: 0ms
    initial stack length: 4
    stack length after relative match length: 1
    stack length after max stack depth limit: 1
    ================================================================================

  This is followed by a summary of how many applicable rules there are
  per initial stack element::

    ================================================================================
    -> checking rule applicability
    of 75 total rules 20 are applicable in (RegexMatch[0-3]{114:May}, RegexMatch[4-7]{135:5th})
    time in _filter_rules: 0ms
    ================================================================================
    ================================================================================
    -> checking rule applicability
    of 75 total rules 20 are applicable in (RegexMatch[0-3]{114:May}, RegexMatch[4-5]{148:5})
    time in _filter_rules: 0ms
    ================================================================================
    ...

  Again, if you do not see any sequence that captures all relevant
  parts of your input, you may need to modify the regular expressions
  or add new ones via rules.

  Finally you see a list of productions that are applied to stack
  elements, where for each applicable rule the rule name and the new
  stack sequence are printed, e.g.::

    --------------------------------------------------------------------------------
    producing on (RegexMatch[0-3]{114:May}, RegexMatch[4-7]{135:5th}), score=-0.13
      ruleMonthMay -> (Time[0-3]{X-05-X X:X (X/X)}, RegexMatch[4-7]{135:5th}), score=1.41
      ruleDOM2 -> (RegexMatch[0-3]{114:May}, Time[4-7]{X-X-05 X:X (X/X)}), score=1.38
    added 2 new stack elements, depth after trunc: 2
    --------------------------------------------------------------------------------

  If no productions could be applied to a stack element the emitted
  results are printed::

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    no rules applicable: emitting
    => Time[0-7]{2018-05-05 X:X (X/X)}, score=15.91,
    --------------------------------------------------------------------------------

  If the desired production does not show up, but the regular
  expressions look fine and the initial stack elements as well, try
  increasing the ``max_stack_depth`` parameter, i.e. run
  ``ctparse(..., max_stack_depth=0)``. Also make sure that the
  ``timeout`` parameter is not set. Maybe ``ctparse`` is able to
  generate the resolution but it is too deep in the stack.


Adding a rule
~~~~~~~~~~~~~

When adding rules try to follow these guidelines:

1. Be as general as possible: instead of writing one long regular
   expression that matches only a specific case, check whether you can
   rather divide your pattern in production parts + some regular
   expressions. For example, if you have a very specific way to
   speficy the year of a date in mind, it might do no harm to just
   allow anything that with ``predicate('hasDate')`` plus your
   specific year expression, i.e.

   .. code:: python

      @rule(predicate('hasDate'), r'your funky year')

2. Keep your regex as general as possible, but avoid regular
   expressions that are likely to generate many "false positives". Often
   that can be prevented by using positive or negative lookaheads and
   lookbehinds to keep the context sane (see `Lookaround
   <https://www.regular-expressions.info/lookaround.html>`_ on the
   excellent regular-expression.info site).

3. Make sure your production covers corner cases and matches the
   ``ctparse`` opinion to resolve to times in the near future but -
   unless explicit -- never in the past (relative to the reference
   time). Also make sure it favors the close future over the further
   future.


Other Types of Contributions
----------------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/comtravo/ctparse/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

ctparse - Parse natural language time expressions in pytho could always use more documentation, whether as part of the
official ctparse - Parse natural language time expressions in pytho docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/comtravo/ctparse/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `ctparse` for local development.

1. Fork the `ctparse` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/ctparse.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv ctparse
    $ cd ctparse/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 ctparse tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.6., 3.7. and 3.8. Check
   https://travis-ci.org/comtravo/ctparse/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ py.test tests.test_ctparse


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run on the ``master`` branch::

$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags
$ make release

You will need a username and password to upload to pypi (might be
automated on Travis).
