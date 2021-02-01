"""Those rules are applied as postprocessing steps after scoring has been already
done. Needed for backwards compatibility."""
from ctparse.types import Artifact, Interval, Time
from datetime import datetime
from dateutil.relativedelta import relativedelta


def apply_postprocessing_rules(ts: datetime, art: Artifact) -> Artifact:
    """Apply postprocessing rules to a resolution *art*. This is
    introduced for backwards compatibility reasons.

    Example:

    8:00 pm, ts=2020.01.01 07:00

    produces a resolution:

    X-X-X 20:00

    after postprocessing this is anchored to the reference time:

    2020-01-01 20:00
    """
    if isinstance(art, Time):
        if art.isTOD:
            return _latent_tod(ts, art)
    if isinstance(art, Interval):
        if art.isTimeInterval:
            return _latent_time_interval(ts, art)

    return art


def _latent_tod(ts: datetime, tod: Time) -> Time:
    dm = ts + relativedelta(hour=tod.hour, minute=tod.minute or 0)
    if dm <= ts:
        dm += relativedelta(days=1)
    return Time(
        year=dm.year, month=dm.month, day=dm.day, hour=dm.hour, minute=dm.minute
    )


def _latent_time_interval(ts: datetime, ti: Interval) -> Interval:
    assert ti.t_from and ti.t_to  # guaranteed by the caller
    dm_from = ts + relativedelta(hour=ti.t_from.hour, minute=ti.t_from.minute or 0)
    dm_to = ts + relativedelta(hour=ti.t_to.hour, minute=ti.t_to.minute or 0)
    if dm_from <= ts:
        dm_from += relativedelta(days=1)
        dm_to += relativedelta(days=1)
    return Interval(
        t_from=Time(
            year=dm_from.year,
            month=dm_from.month,
            day=dm_from.day,
            hour=dm_from.hour,
            minute=dm_from.minute,
        ),
        t_to=Time(
            year=dm_to.year,
            month=dm_to.month,
            day=dm_to.day,
            hour=dm_to.hour,
            minute=dm_to.minute,
        ),
    )
