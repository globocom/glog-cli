import unittest
import arrow
from glogcli.dateutils import datetime_parser, datetime_converter


class DateUtilsTestCase(unittest.TestCase):

    def test_datetime_parser(self):
        now = arrow.now()
        ts_tuples = [
            ("10 minutes ago", lambda x: x.replace(minutes=-10, microsecond=0, tzinfo='local')),
            ("1 day ago", lambda x: x.replace(days=-1, microsecond=0, tzinfo='local')),
            ("yesterday midnight",
             lambda x: x.replace(days=-1, hour=0, minute=0, second=0, microsecond=0, tzinfo='local')),
            ("1986-04-24 00:51:24+02:00", lambda x: arrow.get("1986-04-24 00:51:24+02:00")),
            ("2001-01-01 01:01:01", lambda x: arrow.get("2001-01-01 01:01:01").replace(tzinfo="local")),
            (now, lambda x: now)]

        for (s, ts) in ts_tuples:
            self.assertEqual(datetime_parser(s), ts(arrow.now()))

        with self.assertRaises(ValueError):
            datetime_parser("fdjkldfhskl")

    def test_datetime_converter(self):
        now = arrow.now()
        self.assertIsNone(datetime_converter(None))
        self.assertEqual(datetime_converter(now), now)
        self.assertEqual(datetime_converter("1 day ago") , arrow.now().replace(days=-1, microsecond=0, tzinfo='local'))