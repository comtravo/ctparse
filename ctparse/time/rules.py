import logging
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from .. rule import rule, predicate, dimension, _regex_to_join
from .. types import Time, Interval, pod_hours


logger = logging.getLogger(__name__)


@rule(r'at|on|am|um|gegen|den|dem|der|the|ca\.?|approx\.?|about|in( the)?', dimension(Time))
def ruleAbsorbOnTime(ts, _, t):
    return t


@rule(r'von|vom|from|between', dimension(Interval))
def ruleAbsorbFromInterval(ts, _, i):
    return i


_dows = [('mon', r'montags?|mondays?|mon?\.?'),
         ('tue', r'die?nstags?|die?\.?|tuesdays?|tue?\.?'),
         ('wed', r'mittwochs?|mi\.?|wednesday?|wed\.?'),
         ('thu', r'donn?erstags?|don?\.?|thursdays?|thur?\.?'),
         ('fri', r'freitags?|fridays?|fri?\.?'),
         ('sat', r'samstags?|sonnabends?|saturdays?|sat?\.?'),
         ('sun', r'sonntags?|so\.?|sundays?|sun?\.?')]
_rule_dows = r'|'.join(r'(?P<{}>{})'.format(dow, expr) for dow, expr in _dows)
_rule_dows = r'({})\s*'.format(_rule_dows)


@rule(_rule_dows)
def ruleNamedDOW(ts, m):
    for i, (name, _) in enumerate(_dows):
        if m.match.group(name):
            return Time(DOW=i)


_months = [("january", r"january?|jan\.?"),
           ("february", r"february?|feb\.?"),
           ("march", r"märz|march|mar\.?|mär\.?"),
           ("april", r"april|apr\.?"),
           ("may", r"mai|may\.?"),
           ("june", r"juni|june|jun\.?"),
           ("july", r"juli|july|jul\.?"),
           ("august", r"august|aug\.?"),
           ("september", r"september|sept?\.?"),
           ("october", r"oktober|october|oct\.?|okt\.?"),
           ("november", r"november|nov\.?"),
           ("december", r"december|dezember|dez\.?|dec\.?")]
_rule_months = '|'.join(r'(?P<{}>{})'.format(name, expr) for name, expr in _months)


@rule(_rule_months)
def ruleNamedMonth(ts, m):
    match = m.match
    for i, (name, _) in enumerate(_months):
        if match.group(name):
            return Time(month=i+1)


_named_ts = ((1, r'one|eins'),
             (2, r'two|zwei'),
             (3, r'three|drei'),
             (4, r'four|vier'),
             (5, r'five|fünf'),
             (6, r'six|sechs'),
             (7, r'seven|sieben'),
             (8, r'eight|acht'),
             (9, r'nine|neun'),
             (10, r'ten|zehn'),
             (11, r'eleven|elf'),
             (12, r'twelve|zwölf'))
_rule_named_ts = '|'.join(r'(?P<t_{}>{})'.format(n, expr) for n, expr in _named_ts)


@rule(_rule_named_ts + r'(uhr|h|o\'?clock)?')
def ruleNamedHour(ts, m):
    match = m.match
    for n, _, in _named_ts:
        if match.group('t_{}'.format(n)):
            return Time(hour=n, minute=0)


@rule('mitternacht|midnight')
def ruleMidnight(ts, _):
    return Time(hour=0, minute=0)


def _pod_from_match(pod, m):
    mod = ''
    if m.match.group('mod_early'):
        if m.match.group('mod_very'):
            mod = 'veryearly'
        else:
            mod = 'early'
    elif m.match.group('mod_late'):
        if m.match.group('mod_very'):
            mod = 'verylate'
        else:
            mod = 'late'
    return mod + pod


@rule(r'(?P<mod_very>(sehr|very)\s+)?'
      '((?P<mod_early>früh(er)?|early)'
      '|(?P<mod_late>(spät(er)?|late)))',
      predicate('isPOD'))
def ruleEarlyLatePOD(ts, m, p):
    return Time(POD=_pod_from_match(p.POD, m))


_pods = [('first', (r'(erster?|first|earliest|as early|frühe?st(ens?)?|so früh)'
                    '( (as )?possible| (wie )?möglich(er?)?)?')),
         ('last', (r'(letzter?|last|latest|as late as possible|spätest möglich(er?)?|'
                   'so spät wie möglich(er?)?)')),
         ('earlymorning', r'very early|sehr früh'),
         ('lateevening', r'very late|sehr spät'),
         ('morning', r'morning|morgend?s?|(in der )?frühe?|early'),
         ('forenoon', r'forenoon|vormittags?'),
         ('afternoon', r'afternoon|nachmittags?'),
         ('noon', r'noon|mittags?'),
         ('evening', r'evening|tonight|late|abend?s?|spät'),
         ('night', r'night|nachts?')]

_rule_pods = '|'.join('(?P<{}>{})'.format(pod, expr) for pod, expr in _pods)


@rule(_rule_pods)
def rulePOD(ts, m):
    for i, (pod, _) in enumerate(_pods):
        if m.match.group(pod):
            return Time(POD=pod)


@rule(r'(?<!\d|\.)(?P<day>(?&_day))\.?(?!\d)')
def ruleDOM1(ts, m):
    # Ordinal day "5."
    return Time(day=int(m.match.group('day')))


@rule(r'(?<!\d|\.)(?P<month>(?&_month))\.?(?!\d)')
def ruleMonthOrdinal(ts, m):
    # Ordinal day "5."
    return Time(month=int(m.match.group('month')))


@rule(r'(?<!\d|\.)(?P<day>(?&_day))\s*(?:st|rd|th|s?ten|ter)')
# a "[0-31]" followed by a th/st
def ruleDOM2(ts, m):
    return Time(day=int(m.match.group('day')))


@rule(r'(?<!\d|\.)(?P<year>(?&_year))(?!\d)')
def ruleYear(ts, m):
    y = int(m.match.group('year'))
    if y < 1900:
        y += 2000
    return Time(year=y)


@rule(r'heute|(um diese zeit|zu dieser zeit|um diesen zeitpunkt|zu diesem zeitpunkt)|'
      'todays?|(at this time)')
def ruleToday(ts, _):
    return Time(year=ts.year, month=ts.month, day=ts.day)


@rule(r'(genau\s*)?jetzt|diesen moment|in diesem moment|gerade eben|'
      '((just|right)\s*)?now|immediately')
def ruleNow(ts, _):
    return Time(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, minute=ts.minute)


@rule(r'morgen|tmrw?|tomm?or?rows?')
def ruleTomorrow(ts, _):
    dm = ts + relativedelta(days=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'übermorgen')
def ruleAfterTomorrow(ts, _):
    dm = ts + relativedelta(days=2)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'gestern|yesterdays?')
def ruleYesterday(ts, _):
    dm = ts + relativedelta(days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'vor\s?gestern')
def ruleBeforeYesterday(ts, _):
    dm = ts + relativedelta(days=-2)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'(das )?ende (des|dieses) monats?|(the )?(EOM|end of (the )?month)')
def ruleEOM(ts, _):
    dm = ts + relativedelta(day=1, months=1, days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'(das )?(EOY|jahr(es)? ?ende|ende (des )?jahr(es)?)|(the )?(EOY|end of (the )?year)')
def ruleEOY(ts, _):
    dm = ts + relativedelta(day=1, month=1, years=1, days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate('isDOM'), predicate('isMonth'))
def ruleDOMMonth(ts, dom, m):
    return Time(day=dom.day, month=m.month)


@rule(predicate('isDOM'), r'of', predicate('isMonth'))
def ruleDOMMonth2(ts, dom, _, m):
    return Time(day=dom.day, month=m.month)


@rule(predicate('isMonth'), predicate('isDOM'))
def ruleMonthDOM(ts, m, dom):
    return Time(month=m.month, day=dom.day)


@rule(r'am|diese(n|m)|at|on|this', predicate('hasDOW'))
def ruleAtDOW(ts, _, dow):
    dm = ts + relativedelta(weekday=dow.DOW)
    if dm.date() == ts.date():
        dm += relativedelta(weeks=1)
    return Time.intersect(Time(year=dm.year, month=dm.month, day=dm.day), dow, exclude='DOW')


@rule(r'((am )?(dem |den )?(kommenden|nächsten))|((on |at )?(the )?(next|following))',
      predicate('hasDOW'))
def ruleNextDOW(ts, _, dow):
    dm = ts + relativedelta(weekday=dow.DOW, weeks=1)
    return Time.intersect(Time(year=dm.year, month=dm.month, day=dm.day), dow, exclude='DOW')


@rule(predicate('isDOY'), predicate('isYear'))
def ruleDOYYear(ts, doy, y):
    return Time(year=y.year, month=doy.month, day=doy.day)


@rule(predicate('isDOW'), predicate('isPOD'))
def ruleDOWPOD(ts, dow, pod):
    return Time(DOW=dow.DOW, POD=pod.POD)


@rule(predicate('hasDOW'), predicate('isDOM'))
def ruleDOWDOM(ts, dow, dom):
    # Monday 5th
    # Find next date at this day of week and day of month
    dm = rrule(MONTHLY, dtstart=ts,
               byweekday=dow.DOW, bymonthday=dom.day, count=1)[0]
    return Time.intersect(Time(year=dm.year, month=dm.month, day=dm.day), dow, exclude='DOW')


@rule(predicate('hasDOW'), predicate('isDate'))
def ruleDOWDate(ts, dow, date):
    # Monday 5th December - ignore DOW
    return Time.intersect(date, dow, exclude='DOW')


# LatentX: handle time entities that are not grounded to a date yet
# and assume the next date+time in the future
@rule(predicate('isDOM'))
def ruleLatentDOM(ts, dom):
    dm = ts + relativedelta(day=dom.day)
    if dm <= ts:
        dm += relativedelta(months=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate('hasDOW'))
def ruleLatentDOW(ts, dow):
    dm = ts + relativedelta(weekday=dow.DOW)
    if dm <= ts:
        dm += relativedelta(weeks=1)
    return Time.intersect(Time(year=dm.year, month=dm.month, day=dm.day), dow, exclude='DOW')


@rule(predicate('isDOY'))
def ruleLatentDOY(ts, doy):
    dm = ts + relativedelta(month=doy.month, day=doy.day)
    if dm <= ts:
        dm += relativedelta(years=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate('isTOD'))
def ruleLatentTOD(ts, tod):
    dm = ts + relativedelta(hour=tod.hour, minute=tod.minute or 0)
    if dm <= ts:
        dm += relativedelta(days=1)
    return Time(year=dm.year, month=dm.month, day=dm.day,
                hour=dm.hour, minute=dm.minute)


@rule(predicate('isTimeInterval'))
def ruleLatentTimeInterval(ts, ti):
    dm_from = ts + relativedelta(hour=ti.t_from.hour, minute=ti.t_from.minute or 0)
    dm_to = ts + relativedelta(hour=ti.t_to.hour, minute=ti.t_to.minute or 0)
    if dm_from <= ts:
        dm_from += relativedelta(days=1)
        dm_to += relativedelta(days=1)
    return Interval(t_from=Time(year=dm_from.year, month=dm_from.month, day=dm_from.day,
                                hour=dm_from.hour, minute=dm_from.minute),
                    t_to=Time(year=dm_to.year, month=dm_to.month, day=dm_to.day,
                              hour=dm_to.hour, minute=dm_to.minute))


@rule(predicate('isPOD'))
def ruleLatentPOD(ts, pod):
    # Set the time to the pre-defined POD values, but keep the POD
    # information. The date is chosen based on what ever is the next
    # possible slot for these times
    h_from, h_to = pod_hours[pod.POD]
    t_from = ts + relativedelta(hour=h_from, minute=0)
    if t_from <= ts:
        t_from += relativedelta(days=1)
    return Time(year=t_from.year, month=t_from.month, day=t_from.day,
                POD=pod.POD)


@rule(r'(?<!\d|\.)(?P<day>(?&_day))[\./\-](?P<month>(?&_month))\.?(?!\d)')
def ruleDDMM(ts, m):
    return Time(month=int(m.match.group('month')),
                day=int(m.match.group('day')))


@rule(r'(?<!\d|\.)(?P<day>(?&_day))[-/\.](?P<month>(?&_month))[-/\.]'
      '(?P<year>(?&_year))(?!\d)')
def ruleDDMMYYYY(ts, m):
    y = int(m.match.group('year'))
    if y < 2000:
        y += 2000
    return Time(year=y,
                month=int(m.match.group('month')),
                day=int(m.match.group('day')))


@rule(r'(?<!\d|\.)(?P<hour>(?&_hour))((:|uhr|h|\.)?'
      '(?P<minute>(?&_minute))?\s*(uhr|h)?)(?P<ampm>\s*[ap]\.?m\.?)?(?!\d)')
def ruleHHMM(ts, m):
    # hh [am|pm]
    # hh:mm
    # hhmm
    t = Time(hour=int(m.match.group('hour')),
             minute=int(m.match.group('minute') or 0))
    if m.match.group('ampm') is None:
        return t
    elif m.match.group('ampm').lower().startswith('a') and t.hour <= 12:
        return t
    elif m.match.group('ampm').lower().startswith('p') and t.hour < 12:
        return Time(hour=t.hour+12, minute=t.minute)
    else:
        # the case m.match.group('ampm').startswith('a') and t.hour >
        # 12 (e.g. 13:30am) makes no sense, lets ignore the ampm
        # likewise if hour >= 12 no 'pm' action is needed
        return t


@rule(r'(?<!\d|\.)(?P<hour>(?&_hour))\s*(uhr|h|o\'?clock)')
def ruleHHOClock(ts, m):
    return Time(hour=int(m.match.group('hour')))


@rule(r'(a |one )?quarter( to| till| before| of)|vie?rtel vor', predicate('isTOD'))
def ruleQuarterBeforeHH(ts, _, t):
    # no quarter past hh:mm where mm is not 0 or missing
    if t.minute:
        return
    if t.hour > 0:
        return Time(hour=t.hour-1, minute=45)
    else:
        return Time(hour=23, minute=45)


@rule(r'((a |one )?quarter( after| past)|vie?rtel nach)', predicate('isTOD'))
def ruleQuarterAfterHH(ts, _, t):
    if t.minute:
        return
    return Time(hour=t.hour, minute=15)


@rule(r'halfe?( to| till| before| of)?|halb( vor)?', predicate('isTOD'))
def ruleHalfBeforeHH(ts, _, t):
    if t.minute:
        return
    if t.hour > 0:
        return Time(hour=t.hour-1, minute=30)
    else:
        return Time(hour=23, minute=30)


@rule(r'halfe?( after| past)|halb nach', predicate('isTOD'))
def ruleHalfAfterHH(ts, _, t):
    if t.minute:
        return
    return Time(hour=t.hour, minute=30)


@rule(predicate('isTOD'), predicate('isPOD'))
def ruleTODPOD(ts, tod, pod):
    # time of day may only be an hour as in "3 in the afternoon"; this
    # is only relevant for time <= 12
    # logger.warning('check ruleTODPOD - there might be more cases that need special handling')
    if tod.hour < 12 and ('afternoon' in pod.POD or
                          'evening' in pod.POD or
                          'night' in pod.POD or
                          'last' in pod.POD):
        h = tod.hour + 12
    elif tod.hour > 12 and ('forenoon' in pod.POD or
                            'morning' in pod.POD or
                            'first' in pod.POD):
        # 17Uhr morgen -> do not merge
        return
    else:
        h = tod.hour
    return Time(hour=h, minute=tod.minute)


@rule(predicate('isPOD'), predicate('isTOD'))
def rulePODTOD(ts, pod, tod):
    return ruleTODPOD(ts, tod, pod)


@rule(predicate('isDate'), predicate('isTOD'))
def ruleDateTOD(ts, date, tod):
    return Time(year=date.year, month=date.month, day=date.day,
                hour=tod.hour, minute=tod.minute)


@rule(predicate('isTOD'), predicate('isDate'))
def ruleTODDate(ts, tod, date):
    return Time(year=date.year, month=date.month, day=date.day,
                hour=tod.hour, minute=tod.minute)


@rule(predicate('isDate'), predicate('isPOD'))
def ruleDatePOD(ts, d, pod):
    return Time(year=d.year, month=d.month, day=d.day,
                POD=pod.POD)


@rule(r'((?P<not>not |nicht )?(vor|before))|(bis )?spätestens( bis)?|bis|latest',
      dimension(Time))
def ruleBeforeTime(ts, r, t):
    if r.match.group('not'):
        return Interval(t_from=t, t_to=None)
    else:
        return Interval(t_from=None, t_to=t)


@rule(r'((?P<not>not |nicht )?(nach|after))|(ab )?frühe?stens( ab)?|ab|'
      '(from )?earliest( after)?|from', dimension(Time))
def ruleAfterTime(ts, r, t):
    if r.match.group('not'):
        return Interval(t_from=None, t_to=t)
    else:
        return Interval(t_from=t, t_to=None)


@rule(predicate('isDate'), _regex_to_join, predicate('isDate'))
def ruleDateDate(ts, d1, _, d2):
    if d1.year > d2.year:
        return
    if d1.year == d2.year and d1.month > d2.month:
        return
    if d1.year == d2.year and d1.month == d2.month and d1.day >= d2.day:
        return
    return Interval(t_from=d1, t_to=d2)


@rule(predicate('isDOM'), _regex_to_join, predicate('isDate'))
def ruleDOMDate(ts, d1, _, d2):
    if d1.day >= d2.day:
        return
    return Interval(t_from=Time(year=d2.year, month=d2.month, day=d1.day),
                    t_to=d2)


@rule(predicate('isDOY'), _regex_to_join, predicate('isDate'))
def ruleDOYDate(ts, d1, _, d2):
    if d1.month > d2.month:
        return None
    elif d1.month == d2.month and d1.day >= d2.day:
        return None
    return Interval(t_from=Time(year=d2.year, month=d1.month, day=d1.day),
                    t_to=d2)


@rule(predicate('isDateTime'), _regex_to_join, predicate('isDateTime'))
def ruleDateTimeDateTime(ts, d1, _, d2):
    if d1.year > d2.year:
        return
    if d1.year == d2.year and d1.month > d2.month:
        return
    if d1.year == d2.year and d1.month == d2.month and d1.day > d2.day:
        return
    if d1.year == d2.year and d1.month == d2.month and d1.day == d2.day and d1.hour > d2.hour:
        return
    if (d1.year == d2.year and d1.month == d2.month and d1.day == d2.day and
       d1.hour == d2.hour and d1.minute >= d2.minute):
        return
    return Interval(t_from=d1, t_to=d2)


@rule(predicate('isTOD'), _regex_to_join, predicate('isTOD'))
def ruleTODTOD(ts, t1, _, t2):
    return Interval(t_from=t1, t_to=t2)


@rule(predicate('isDate'), dimension(Interval))
def ruleDateInterval(ts, d, i):
    if not ((i.t_from is None or i.t_from.isTOD or i.t_from.isPOD) and
            (i.t_to is None or i.t_to.isTOD or i.t_to.isPOD)):
        return
    t_from = t_to = None
    if i.t_from is not None:
        t_from = Time(year=d.year, month=d.month, day=d.day,
                      hour=i.t_from.hour, minute=i.t_from.minute,
                      POD=i.t_from.POD)
    if i.t_to is not None:
        t_to = Time(year=d.year, month=d.month, day=d.day,
                    hour=i.t_to.hour, minute=i.t_to.minute,
                    POD=i.t_to.POD)
    if t_from and t_to and t_from.dt >= t_to.dt:
        t_to = t_to.dt + relativedelta(days=1)
        t_to = Time(year=t_to.year, month=t_to.month, day=t_to.day,
                    hour=t_to.hour, minute=t_to.minute)
    return Interval(t_from=t_from, t_to=t_to)


@rule(predicate('isPOD'), dimension(Interval))
def rulePODInterval(ts, p, i):
    def _adjust_h(t):
        if t.hour < 12 and ('afternoon' in p.POD or
                            'evening' in p.POD or
                            'night' in p.POD or
                            'last' in p.POD):
            return t.hour + 12
        else:
            return t.hour
    # only makes sense if i is a time interval
    if not ((i.t_from is None or i.t_from.hasTime) and
            (i.t_to is None or i.t_to.hasTime)):
        return
    t_to = t_from = None
    if i.t_to is not None:
        t_to = Time(year=i.t_to.year, month=i.t_to.month, day=i.t_to.day,
                    hour=_adjust_h(i.t_to), minute=i.t_to.minute,
                    DOW=i.t_to.DOW)
    if i.t_from is not None:
        t_from = Time(year=i.t_from.year, month=i.t_from.month, day=i.t_from.day,
                      hour=_adjust_h(i.t_from), minute=i.t_from.minute,
                      DOW=i.t_from.DOW)
    return Interval(t_from=t_from, t_to=t_to)
