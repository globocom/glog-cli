from __future__ import division, print_function
import parsedatetime.parsedatetime as pdt
import datetime
import arrow
import six
from pygray.utils import LOCAL_TIMEZONE


def datetime_parser(s):
    try:
        ts = arrow.get(s)
        if ts.tzinfo == arrow.get().tzinfo:
            ts = ts.replace(tzinfo=LOCAL_TIMEZONE)
    except:
        c = pdt.Calendar()
        result, what = c.parse(s)

        ts = None
        if what in (1, 2, 3):
            ts = datetime.datetime(*result[:6])
            ts = arrow.get(ts)
            ts = ts.replace(tzinfo=LOCAL_TIMEZONE)
            return ts

    if ts is None:
        raise ValueError("Cannot parse timestamp '{0}'".format(s))

    return ts


def datetime_converter(dt):
    if dt is None:
        return None
    elif isinstance(dt, six.string_types):
        return datetime_parser(dt)
    else:
        return arrow.get(dt)
