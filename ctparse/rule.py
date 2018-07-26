import regex
import logging
from . types import RegexMatch


logger = logging.getLogger(__name__)

rules = {}

_regex_cnt = 100  # leave this much space for ids of production types
_regex = {}  # compiled regex
_regex_str = {}  # map regex id to original string
_str_regex = {}  # map regex raw str to regex id

_regex_hour = r'(?:[01]?\d)|(?:2[0-3])'
_regex_minute = r'[0-5]\d'
_regex_day = r'[012]?[1-9]|10|20|30|31'
_regex_month = r'10|11|12|0?[1-9]'
_regex_year = r'(?:19\d\d)|(?:20[0-2]\d)|(?:\d\d)'

# used in many places in rules
_regex_to_join = (r'(\-|to( the)?|(un)?til|bis( zum)?|zum|auf( den)?|und|'
                  'no later than|spätestens?|at latest( at)?)')

_defines = (r'(?(DEFINE)(?<_hour>{regex_hour})(?P<_minute>{regex_minute})'
            '(?P<_day>{regex_day})(?P<_month>{regex_month})'
            '(?P<_year>{regex_year}))').format(
                regex_hour=_regex_hour,
                regex_minute=_regex_minute,
                regex_day=_regex_day,
                regex_month=_regex_month,
                regex_year=_regex_year)


def rule(*patterns):
    def _map(p):
        if type(p) is str:
            # its a regex
            global _regex_cnt
            if p in _str_regex:
                # have seen this regex before - recycle
                return regex_match(_str_regex[p])
            # test the regex first
            re = r'{defines}(?i)(?P<R{re_key}>{re})'.format(
                    defines=_defines,
                    re=p,
                    re_key=_regex_cnt)
            new_rr = regex.compile(
                # Removed the separator here - leads to more matches,
                # as now each rule can also match if it is not followed
                # or preceeded by a separator character
                # r'(?i)(?:{sep})(?P<{re_key}>{re})(?:{sep})'.format(
                re,
                regex.VERSION1)
            if new_rr.match(''):
                raise ValueError('expression {} matches empty strings'.format(p))
            _regex_str[_regex_cnt] = p
            _str_regex[p] = _regex_cnt
            _regex[_regex_cnt] = new_rr
            _regex_cnt += 1
            return regex_match(_regex_cnt-1)
        else:
            return p

    # check that in rules we never have a regex followed by a regex -
    # that must be merged into one regex
    def _has_consequtive_regex(ps):
        for p0, p1 in zip(ps[:-1], ps[1:]):
            if isinstance(p0, str) and isinstance(p1, str):
                return True
        return False

    if _has_consequtive_regex(patterns):
        raise ValueError('rule which contains consequtive regular expressions found')

    mapped_patterns = [_map(p) for p in patterns]

    def fwrapper(f):
        def wrapper(ts, *args):
            res = f(ts, *args)
            if res is not None:
                # upon a successful production, update the span
                # information by expanding it to that of all args
                res.update_span(*args)
            return res
        rules[f.__name__] = (wrapper, mapped_patterns)
        return wrapper
    return fwrapper


def regex_match(r_id):
    def _regex_match(r):
        return type(r) == RegexMatch and r.id == r_id
    return _regex_match


def dimension(dim):
    def _dimension(d):
        return isinstance(d, dim)
    return _dimension


def predicate(pred):
    def _predicate(d):
        return getattr(d, pred, False)
    return _predicate


from . time.rules import *  # noqa
