class Artifact:
    def __init__(self):
        self.mstart = 0
        self.mend = 0

    def update_span(self, *args):
        self.mstart = args[0].mstart
        self.mend = args[-1].mend
        return self

    def __len__(self):
        return self.mend - self.mstart

    def __str__(self):
        return ''

    def __repr__(self):
        return '{}[{}-{}]{{{}}}'.format(
            self.__class__.__name__, self.mstart, self.mend, str(self))

    def nb_str(self):
        return '{}[]{{{}}}'.format(
            self.__class__.__name__, str(self))


class RegexMatch(Artifact):
    def __init__(self, id, m):
        super().__init__()
        self.key = 'R{}'.format(id)
        self.id = id
        self.match = m
        self.mstart = m.span(self.key)[0]
        self.mend = m.span(self.key)[1]
        self._text = m.group(self.key)

    def __str__(self):
        return '{}:{}'.format(self.id, self._text)


class Time(Artifact):
    def __init__(self, year=None, month=None, day=None, hour=None, minute=None, DOW=None, POD=None):
        super().__init__()
        # Might add some validation here, did not to avoid the overhead
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.DOW = DOW
        self.POD = POD

    # ------------------------------------------------------------------------------------
    # Make sure to not accidentially test bool(x) as False when x==0, but you meant x==None
    # ------------------------------------------------------------------------------------
    @property
    def isDOY(self):
        '''isDayOfYear <=> a dd.mm but not year
        '''
        return bool(self.month and self.day and not self.year)

    @property
    def isDOM(self):
        '''isDayOfMonth <=> a dd but no month
        '''
        return bool(self.day and not self.month)

    @property
    def isDOW(self):
        '''isDayOfWeek <=> DOW is the 0=Monday index; fragile test, as the DOW
        could be accompanied by e.g. a full date etc.; in practice,
        however, the production rules do not do that.

        '''
        return bool(self.DOW is not None)

    @property
    def isMonth(self):
        return bool(self.month and not self.day and not self.year)

    @property
    def isPOD(self):
        '''isPartOfDay <=> morning, etc.; fragile, tests only that there is a POD and neither a full date nor a full time
        '''
        return self.POD is not None and not self.hasDate and not self.hasTime

    @property
    def isTOD(self):
        '''isTimeOfDay - only a time, not date'''
        return self.hasTime and not self.hasDate

    @property
    def isDate(self):
        '''isDate - only a date, not time'''
        return self.hasDate and not self.hasTime

    @property
    def isDateTime(self):
        '''a date and a time'''
        return self.hasDate and self.hasTime

    @property
    def isYear(self):
        '''just a year'''
        return bool(not self.month and not self.day and self.year)

    @property
    def hasDate(self):
        '''at least at date'''
        return bool(self.year and self.month and self.day)

    @property
    def hasTime(self):
        '''at least a time to the hour'''
        return bool(self.hour is not None)

    def __str__(self):
        return '{}-{}-{} {}:{} ({}/{})'.format(
            '{:04d}'.format(self.year) if self.year is not None else 'X',
            '{:02d}'.format(self.month) if self.month is not None else 'X',
            '{:02d}'.format(self.day) if self.day is not None else 'X',
            '{:02d}'.format(self.hour) if self.hour is not None else 'X',
            '{:02d}'.format(self.minute) if self.minute is not None else 'X',
            '{:d}'.format(self.DOW) if self.DOW is not None else 'X',
            '{}'.format(self.POD) if self.POD is not None else 'X')


class Interval(Artifact):
    def __init__(self, t_from=None, t_to=None, POD=None):
        super().__init__()
        self.t_from = t_from
        self.t_to = t_to
        self.POD = POD

    @property
    def isPOD(self):
        return self.POD is not None

    @property
    def isTimeInterval(self):
        return self.t_from.isTOD and self.t_to.isTOD and not self.isPOD

    def __str__(self):
        return '{} - {} ({})'.format(
            str(self.t_from),
            str(self.t_to),
            '{}'.format(self.POD) if self.POD is not None else 'X')
