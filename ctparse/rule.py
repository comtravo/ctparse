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
_regex_pos_before_sep = r'(?<=\pZ|\pP|\pC|^)'
_regex_pos_behind_sep = r'(?=\pZ|\pP|\pC|$)'

# used in many places in rules
_regex_to_join = (r'(\-|to( the)?|(un)?til|bis( zum)?|zum|auf( den)?|und|'
                  'no later than|spätestens?|at latest( at)?)')


def rule(*patterns):
    def _map(p):
        if type(p) is str:
            # its a regex
            global _regex_cnt
            re_id = _regex_cnt
            if p in _str_regex:
                # have seen this regex before - recycle
                return regex_match(_str_regex[p])
            # test the regex first
            defines = (r'(?(DEFINE)(?<_hour>{regex_hour})(?P<_minute>{regex_minute})'
                       '(?P<_day>{regex_day})(?P<_month>{regex_month})'
                       '(?P<_year>{regex_year})'
                       '(?P<_pos_bnd>{regex_pos_behind_sep})'
                       '(?P<_pos_bfr>{regex_pos_before_sep}))').format(
                           regex_hour=_regex_hour,
                           regex_minute=_regex_minute,
                           regex_day=_regex_day,
                           regex_month=_regex_month,
                           regex_year=_regex_year,
                           regex_pos_behind_sep=_regex_pos_behind_sep,
                           regex_pos_before_sep=_regex_pos_before_sep)
            re = r'{defines}(?i)(?P<{re_key}>{re})'.format(
                    defines=defines,
                    re=p,
                    re_key='R{}'.format(re_id))
            new_rr = regex.compile(
                # Removed the separator here - leads to more matches,
                # as now each rule can also match if it is not followed
                # or preceeded by a separator character
                # r'(?i)(?:{sep})(?P<{re_key}>{re})(?:{sep})'.format(
                re,
                regex.VERSION1)
            if new_rr.match(''):
                raise ValueError('expression {} matches empty strings'.format(p))
            _regex_cnt += 1
            _regex_str[re_id] = p
            _str_regex[p] = re_id
            defines = (r'(?(DEFINE)(?<_hour>{regex_hour})(?P<_minute>{regex_minute})'
                       '(?P<_day>{regex_day})(?P<_month>{regex_month})'
                       '(?P<_year>{regex_year})'
                       '(?P<_pos_bnd>{regex_pos_behind_sep})'
                       '(?P<_pos_bfr>{regex_pos_before_sep}))').format(
                           regex_hour=_regex_hour,
                           regex_minute=_regex_minute,
                           regex_day=_regex_day,
                           regex_month=_regex_month,
                           regex_year=_regex_year,
                           regex_pos_behind_sep=_regex_pos_behind_sep,
                           regex_pos_before_sep=_regex_pos_before_sep)
            re = r'{defines}(?i)(?P<{re_key}>{re})'.format(
                    defines=defines,
                    re=p,
                    re_key='R{}'.format(re_id))
            _regex[re_id] = new_rr
            return regex_match(re_id)
        else:
            return p

    patterns = [_map(p) for p in patterns]

    def fwrapper(f):
        def wrapper(ts, *args):
            try:
                res = f(ts, *args)
                if res is not None:
                    # upon a successful production, update the span
                    # information by expanding it to that of all args
                    res.update_span(*args)
            except ValueError:
                return None
            return res
        rules[f.__name__] = (wrapper, patterns)
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
