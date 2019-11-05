==================
Time Parse Dataset
==================

The dataset included in ``datasets/timeparse_corpus.json`` contains a set of ~2000 human annotated time expression in english and german.

The dataset is a list of json records with the following fields:

- *text*: the text for the time expression
- *ref_time*: a timestamp in ISO 8601 format ``YYYY-MM-DDTHH:MM:SS``
- *gold_parse*: the human annotation of the time expression. It can be a ``Time`` or ``Interval``. 
- *language*: a two-digit code indicating the language. In this dataset it is either "en" or "de".


For ``Time``, the format is as follows

    Time[]{YYYY-MM-DD HH:MM (dow/tod)} 

Where:
- ``YYYY`` is a four-digit year or ``X``, if year is missing
- ``MM`` is a two-digit month or ``X``, if month is missing
- ``DD`` is a two-digit day or ``X``, if day is missing
- ``HH`` is a two-digit hour (24 hour clock) or ``X``, if hour is missing
- ``MM`` is a two-digit minute or ``X``, if minute is missing
- ``dow`` is an integer between 0 and 6 representing day of week or X, if missing (in the dataset, day of week is always missing)
- ``tod`` is a string representing the time of day (such as earlymorning, morning, forenoon, noon, afternoon, evening, lateevening) or X if not specified.

Example:

    Morning of the 11th June 2017
    Time[]{2017-06-11 X:X (X/morning)}

For ``Interval`` the format is as follows:

    Interval[]{<START_T> - <END_T>}

Where ``<START_T>`` and ``<END_T>`` are the beginning and end of the interval. ``<START_T>`` or ``<END_T>`` can be None if the interval is open-ended. They can be specified
using the same representation for times, as described above:

    YYYY-MM-DD HH:MM (dow/tod)

Example:

    Wed, Oct 11 2017 8:30 PM - 9:47 PM
    Interval[]{2017-10-11 08:30 (X/X) - 2017-10-11 09:47 (X/X)}