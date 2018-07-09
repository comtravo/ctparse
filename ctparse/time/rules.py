import logging
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from .. rule import rule, predicate, dimension, _regex_to_join
from .. types import Time, Interval, pod_hours


logger = logging.getLogger(__name__)

# Named things:
# - weekdays (Monday, etc.)
# - months (January, etc.)
# - today, tomorrow, etc.
# - seasons
# - holidays


# Numbers used for
# - day
# - month
# - year
# - hour
# - minute
# - relations

# What can we find:
# - Fullly specified expressions
#   - Date
#   - DateTime
#   - A - B Ranges where A, B are a Date or a DateTime
#     Ranges can be left or right open
# - Partially specified expressions
#   - Time
#   - DOM (Day of month, aka "the 5th")
#   - DOW (Day of week, aka "Monday")
#   - POD (Part of day, i.e. "morning")
#   - MOY (Month if year, aka "January")
#   - YR (Year)


# More general:
# Time: yyyy-mm-dd hh:mm, all fields are optional
# Interval: Time - Time, where either side can be None

@rule(r'at|on|am|um|gegen|den|der|the|ca\.?|approx\.?|about|in( the)?', dimension(Time))
def ruleAbsorbOnTime(ts, _, t):
    return t


@rule(r'von|vom|from', dimension(Interval))
def ruleAbsorbFromInterval(ts, _, i):
    return i


@rule(predicate('hasDOW'), r',( de(n|m|r))?')
def ruleAbsorbDOWComma(ts, dow, _):
    return dow


_wd_mod_re = (r'((?P<morning>morning|morgend?s?|früh)'
              r'|(?P<beforenoon>vormittags?)'
              r'|(?P<noon>noon|mittags?)'
              r'|(?P<afternoon>afternoon|nachmittags?)'
              r'|(?P<evening>evening|abends?)'
              r'|(?P<night>nights?|nachts?))?')


def _get_wd_pod(m):
    if m.match.group('morning'):
        return 'morning'
    elif m.match.group('beforenoon'):
        return 'beforenoon'
    elif m.match.group('noon'):
        return 'noon'
    elif m.match.group('afternoon'):
        return 'afternoon'
    elif m.match.group('evening'):
        return 'evening'
    elif m.match.group('night'):
        return 'night'
    else:
        return


@rule(r'(montags?|mondays?|mon?\.?)\s*' + _wd_mod_re)
def ruleMonday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=0, POD=pod)


@rule(r'(die?nstags?|die?\.?|tuesdays?|tue?\.?)\s*' + _wd_mod_re)
def ruleTuesday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=1, POD=pod)


@rule(r'(mittwochs?|mi\.?|wednesday?|wed\.?)\s*' + _wd_mod_re)
def ruleWednesday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=2, POD=pod)


@rule(r'(donn?erstags?|don?\.?|thursdays?|thur?\.?)\s*' + _wd_mod_re)
def ruleThursday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=3, POD=pod)


@rule(r'(freitags?|fridays?|fri?\.?)\s*' + _wd_mod_re)
def ruleFriday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=4, POD=pod)


@rule(r'(samstags?|sonnabends?|saturdays?|sat?\.?)\s*' + _wd_mod_re)
def ruleSaturday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=5, POD=pod)


@rule(r'(sonntags?|so\.?|sundays?|sun?\.?)\s*' + _wd_mod_re)
def ruleSunday(ts, m):
    pod = _get_wd_pod(m)
    return Time(DOW=6, POD=pod)


def mkMonths(months):
    for month_num, (month, month_ex) in enumerate(months):
        exec('''@rule(r"({})")
def ruleMonth{}(ts, m): return Time(month={})'''.format(
            month_ex, month, month_num + 1))


mkMonths([
    ("January", r"january?|jan\.?"),
    ("February", r"february?|feb\.?"),
    ("March", r"märz|march|mar\.?|mär\.?"),
    ("April", r"april|apr\.?"),
    ("May", r"mai|may\.?"),
    ("June", r"juni|june|jun\.?"),
    ("July", r"juli|july|jul\.?"),
    ("August", r"august|aug\.?"),
    ("September", r"september|sept?\.?"),
    ("October", r"oktober|october|oct\.?|okt\.?"),
    ("November", r"november|nov\.?"),
    ("December", r"december|dezember|dez\.?|dec\.?")])


def mkDDMonths(months):
    for month_num, (month, month_ex) in enumerate(months):
        exec('''@rule(r"(?P<day>(?&_day))\.?\s*({})")
def ruleDDMonth{}(ts, m): return Time(month={}, day=int(m.match.group('day')))'''.format(
            month_ex, month, month_num + 1))


mkDDMonths([
    ("January", r"january?|jan\.?"),
    ("February", r"february?|feb\.?"),
    ("March", r"märz|march|mar\.?|mär\.?"),
    ("April", r"april|apr\.?"),
    ("May", r"mai|may\.?"),
    ("June", r"juni|june|jun\.?"),
    ("July", r"juli|july|jul\.?"),
    ("August", r"august|aug\.?"),
    ("September", r"september|sept?\.?"),
    ("October", r"oktober|october|oct\.?|okt\.?"),
    ("November", r"november|nov\.?"),
    ("December", r"december|dezember|dez\.?|dec\.?")])


@rule(r'(erster?|first|earliest|as early|frühe?st(ens?)?|so früh)'
      '( (as )?possible| (wie )?möglich(er?)?)?')
def rulePODFirst(ts, m):
    return Time(POD='first')


@rule(r'(letzter?|last|latest|as late as possible|spätest möglich(er?)?|so spät wie möglich(er?)?)')
def rulePODFLast(ts, m):
    return Time(POD='last')


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


@rule(r'(very early|sehr früh)')
def rulePODEarlyMorning(ts, m):
    return Time(POD='earlymorning')


@rule(r'(morning|morgend?s?|(in der )?frühe?|early)')
def rulePODMorning(ts, m):
    return Time(POD='morning')


@rule(r'(before\s*noon|vor\s*mittags?)')
def rulePODBeforeNoon(ts, m):
    return Time(POD='beforenoon')


@rule(r'(noon|mittags?)')
def rulePODNoon(ts, m):
    return Time(POD='noon')


@rule(r'(after\s*noon|nach\s*mittags?)')
def rulePODAfterNoon(ts, m):
    return Time(POD='afternoon')


@rule(r'(evening|tonight|late|abend?s?|spät)')
def rulePODEvening(ts, m):
    return Time(POD='evening')


@rule(r'(very late|sehr spät)')
def rulePODLateEvening(ts, m):
    return Time(POD='lateevening')


@rule(r'(night|nachts?)')
def rulePODNight(ts, m):
    return Time(POD='night')


@rule(r'(?!<\d|\.)(?P<day>(?&_day))\.?(?!\d)')
def ruleDOM1(ts, m):
    # Ordinal day "5."
    return Time(day=int(m.match.group('day')))


@rule(r'(?!<\d|\.)(?P<month>(?&_month))\.?(?!\d)')
def ruleMonthOrdinal(ts, m):
    # Ordinal day "5."
    return Time(month=int(m.match.group('month')))


@rule(r'(?!<\d|\.)(?P<day>(?&_day))\s*(?:st|rd|th|ten|ter)')
# a "[0-31]" followed by a th/st
def ruleDOM2(ts, m):
    return Time(day=int(m.match.group('day')))


@rule(r'(?!<\d|\.)(?P<year>(?&_year))(?!\d)')
def ruleYear(ts, m):
    y = int(m.match.group('year'))
    if y < 1900:
        y += 2000
    return Time(year=y)


@rule(r'heute|(um diese zeit|zu dieser zeit|um diesen zeitpunkt|zu diesem zeitpunkt)|'
      'todays?|(at this time)')
def ruleToday(ts, _):
    return Time(year=ts.year, month=ts.month, day=ts.day)


@rule(r'(genau)? ?jetzt|diesen moment|in diesem moment|gerade eben|'
      '((just|right)\s*)now|immediately')
def ruleNow(ts, _):
    return Time(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, minute=ts.minute)


@rule(r'morgen|tmrw?|tomm?or?rows?')
def ruleTomorrow(ts, _):
    dm = ts + relativedelta(days=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(r'gestern|yesterdays?')
def ruleYesterday(ts, _):
    dm = ts + relativedelta(days=-1)
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
    # Set the time to the prededined POD values, but - contrary to
    # other rules - keep the POD information. The date is chosen based
    # on what ever is the next possible slot for these times)
    h_from, h_to = pod_hours[pod.POD]
    t_from = ts + relativedelta(hour=h_from)
    if t_from <= ts:
        t_from += relativedelta(days=1)
    return Time(year=t_from.year, month=t_from.month, day=t_from.day,
                POD=pod.POD)
    # t_to = t_from + relativedelta(hour=h_to)
    # t_from = Time(year=t_from.year, month=t_from.month, day=t_from.day,
    #               hour=t_from.hour, minute=0)
    # t_to = Time(year=t_to.year, month=t_to.month, day=t_to.day,
    #             hour=t_to.hour, minute=0)
    # return Interval(t_from=t_from, t_to=t_to, POD=pod.POD)


@rule(r'(?!<\d|\.)(?P<day>(?&_day))[\./\-](?P<month>(?&_month))\.?(?!\d)')
def ruleDDMM(ts, m):
    return Time(month=int(m.match.group('month')),
                day=int(m.match.group('day')))


@rule(r'(?!<\d|\.)(?P<day>(?&_day))[-/\.](?P<month>(?&_month))[-/\.]'
      '(?P<year>(?&_year))(?!\d)')
def ruleDDMMYYYY(ts, m):
    y = int(m.match.group('year'))
    if y < 2000:
        y += 2000
    return Time(year=y,
                month=int(m.match.group('month')),
                day=int(m.match.group('day')))


@rule(r'(?!<\d|\.)(?P<hour>(?&_hour))((:|uhr|h|\.)?'
      '(?P<minute>(?&_minute))?\s*(uhr|h)?)(?P<ampm>\s*[ap]\.?m\.?)?(?!\d)')
def ruleHHMM(ts, m):
    # hh [am|pm]
    # hh:mm
    # hhmm
    t = Time(hour=int(m.match.group('hour')),
             minute=int(m.match.group('minute') or 0))
    if m.match.group('ampm') is None:
        return t
    elif m.match.group('ampm').startswith('a') and t.hour <= 12:
        return t
    elif m.match.group('ampm').startswith('p') and t.hour <= 12:
        return Time(hour=t.hour+12, minute=t.minute)
    else:
        # the case m.match.group('ampm').startswith('a') and t.hour >
        # 12 (e.g. 13:30am) makes no sense, lets ignore the ampm
        return t


@rule(r'(?!<\d|\.)(?P<hour>(?&_hour))\s*(uhr|h|o\'?clock)')
def ruleHHOClock(ts, m):
    return Time(hour=int(m.match.group('hour')))


def ruleMinutesBeforeHH():
    pass


def ruleMinutesAfterHH():
    pass


def ruleQuarterBeforeHH():
    pass


def ruleQuarterAfterHH():
    # quarter to one
    pass


def ruleHalfPastHH():
    # half past one
    pass


def ruleHalfBeforeHH():
    # halb eins
    pass


@rule(predicate('isTOD'), predicate('isPOD'))
def ruleTODPOD(ts, tod, pod):
    # time of day may only be an hour as in "3 in the afternoon"; this
    # is only relevant for time <= 12
    # logger.warning('check ruleTODPOD - there might be more cases that need special handling')
    if tod.hour <= 12 and ('afternoon' in pod.POD or
                           'evening' in pod.POD or
                           'night' in pod.POD):
        h = tod.hour + 12
    elif tod.hour > 12 and ('beforenoon' in pod.POD or
                            'morning' in pod.POD):
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


def ruleAfter():
    pass


@rule(r'vor|before|spätestens|latest', dimension(Time))
def ruleBeforeTime(ts, _, t):
    return Interval(t_from=None, t_to=t)


@rule(r'nach|ab|after|frühe?stens|earliest', dimension(Time))
def ruleAfterTime(ts, _, t):
    return Interval(t_from=t, t_to=None)


def rulePrevious():
    pass


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
    if t1.hour > t2.hour:
        return
    if t1.hour == t2.hour:
        if t1.minute is not None and t2.minute is not None and t1.minute >= t2.minute:
            # 6:30 - 6:30?
            return
        if t1.minute is None and t2.minute is not None:
            # 6:30 - 6?
            return
        if t1.minute is None and t2.minute is None:
            # 6 - 6?
            return
    return Interval(t_from=t1, t_to=t2)


@rule(predicate('isDate'), dimension(Interval))
def ruleDateInterval(ts, d, i):
    # only makes sense if i is a time interval
    if not ((i.t_from is None or i.t_from.isTOD) and
            (i.t_to is None or i.t_to.isTOD)):
        return
    if i.t_from is None:
        return Interval(t_to=Time(year=d.year, month=d.month, day=d.day,
                                  hour=i.t_to.hour, minute=i.t_to.minute))
    elif i.t_to is None:
        return Interval(t_from=Time(year=d.year, month=d.month, day=d.day,
                                    hour=i.t_from.hour, minute=i.t_from.minute))
    else:
        return Interval(t_from=Time(year=d.year, month=d.month, day=d.day,
                                    hour=i.t_from.hour, minute=i.t_from.minute),
                        t_to=Time(year=d.year, month=d.month, day=d.day,
                                  hour=i.t_to.hour, minute=i.t_to.minute))
