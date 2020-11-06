import unittest
import arrow
import syslog
from pygray import utils
from termcolor import colored
from pygray.formats import TailFormatter, DumpFormatter, LogLevel
from pygray.graylog_api import Message


class FormatterTestCase(unittest.TestCase):

    def setUp(self):
        self.timestamp = arrow.utcnow()
        self.message = Message({
            'index': 'graylog',
            'message': {
                'a': 1,
                'b': 2,
                'c': 3,
                'level': 7,
                'message': 'dummy message',
                'source': 'dummy.source',
                'timestamp': self.timestamp
            }
        })        


class TailFormatterTestCase(FormatterTestCase):

    def test_format(self):
        log = TailFormatter('({source}) - {message}', color=False).format(self.message)
        self.assertEqual('(dummy.source) - dummy message', log)

    def test_format_colored_with_level_debug(self):
        self.message.level = syslog.LOG_DEBUG
        log = TailFormatter('({source}) - {message}', color=True).format(self.message)
        self.assertEqual(colored('(dummy.source) - dummy message', 'cyan'), log)

    def test_format_colored_with_level_error(self):
        self.message.level = syslog.LOG_ERR
        log = TailFormatter('({source}) - {message}', color=True).format(self.message)
        self.assertEqual(colored('(dummy.source) - dummy message', 'red'), log)

    def test_format_colored_with_level_info(self):
        self.message.level = syslog.LOG_INFO
        log = TailFormatter('({source}) - {message}', color=True).format(self.message)
        self.assertEqual(colored('(dummy.source) - dummy message', 'green'), log)

    def test_format_colored_with_level_warning(self):
        self.message.level = syslog.LOG_WARNING
        log = TailFormatter('({source}) - {message}', color=True).format(self.message)
        self.assertEqual(colored('(dummy.source) - dummy message', 'yellow'), log)

    def test_format_colored_with_level_critical(self):
        self.message.level = syslog.LOG_CRIT
        log = TailFormatter('({source}) - {message}', color=True).format(self.message)
        self.assertEqual(colored('(dummy.source) - dummy message', 'white', 'on_red'), log)

    def test_format_with_log_level(self):
        log = TailFormatter('({level}) - {message}', color=False).format(self.message)
        self.assertEqual('(DEBUG) - dummy message', log)

    def test_format_with_timestamp(self):
        log = TailFormatter('({timestamp}) - {message}', color=False).format(self.message)
        timestamp_local_format = self.timestamp.to('local').format(utils.DEFAULT_DATE_FORMAT)
        self.assertEqual('({}) - dummy message'.format(timestamp_local_format), log)

    def test_format_with_custom_fields(self):
        log = TailFormatter('{a} {b} {c}', fields=['a', 'b', 'c'], color=False).format(self.message)
        self.assertEqual('1 2 3', log)

    def test_format_with_blank_fields(self):
        log = TailFormatter('{blank_field}', fields=['blank_field'], color=False).format(self.message)
        self.assertEqual('', log)


class DumpFormatterTestCase(FormatterTestCase):

    def test_format(self):
        log = DumpFormatter(None, fields=['level', 'message']).format(self.message)
        self.assertEqual("'DEBUG';'dummy message'", log)

    def test_format_with_custom_fields(self):
        log = DumpFormatter(None, fields=['a', 'b']).format(self.message)
        self.assertEqual("'1';'2'", log)

    def test_format_with_blank_field(self):
        log = DumpFormatter(None, fields=['level', 'blank_fields']).format(self.message)
        self.assertEqual("'DEBUG';''", log)


class LogLevelTestCase(unittest.TestCase):

    def test_get_log_level_from_code(self):
        self.assertEqual('CRITICAL', LogLevel.find_by_syslog_code(syslog.LOG_CRIT)['name'])
        self.assertEqual('WARNING', LogLevel.find_by_syslog_code(syslog.LOG_WARNING)['name'])
        self.assertEqual('DEBUG', LogLevel.find_by_syslog_code(syslog.LOG_DEBUG)['name'])
        self.assertEqual('INFO', LogLevel.find_by_syslog_code(syslog.LOG_INFO)['name'])
        self.assertEqual('ERROR', LogLevel.find_by_syslog_code(syslog.LOG_ERR)['name'])
        self.assertEqual('NOTICE', LogLevel.find_by_syslog_code(syslog.LOG_NOTICE)['name'])
        self.assertEqual('', LogLevel.find_by_syslog_code(9999)['name'])

    def test_get_log_level_code(self):
        self.assertEqual(syslog.LOG_CRIT, LogLevel.find_by_level_name('CRITICAL'))
        self.assertEqual(syslog.LOG_WARNING, LogLevel.find_by_level_name('WARNING'))
        self.assertEqual(syslog.LOG_DEBUG, LogLevel.find_by_level_name('DEBUG'))
        self.assertEqual(syslog.LOG_INFO, LogLevel.find_by_level_name('INFO'))
        self.assertEqual(syslog.LOG_ERR, LogLevel.find_by_level_name('ERROR'))
        self.assertEqual(syslog.LOG_NOTICE, LogLevel.find_by_level_name('NOTICE'))
        self.assertIsNone(LogLevel.find_by_level_name('UNKNOWN'))

    def test_list_levels(self):
        self.assertEqual(['CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG'], LogLevel.list_levels())
