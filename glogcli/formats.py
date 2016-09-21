from __future__ import division, print_function
from termcolor import colored
import syslog
import six


class Formatter(object):

    def __init__(self, format_template):
        self.format_template = format_template

    def tail_format(self, fields=["source", "facility", "line", "module"], color=True):
        def format(entry):
            message = entry.message
            timestamp = entry.timestamp.to('local')
            host = entry.message_dict.get("source")
            facility = entry.message_dict.get("facility")
            local_fields = list(fields)

            if "message" in local_fields:
                local_fields.remove("message")

            field_text = map(lambda f: "{}:{}".format(f, entry.message_dict.get(f, "")), local_fields)

            if six.PY2:
                try:
                    message = message.encode("utf-8")
                except:
                    pass

            log_level = LogLevel.find_by_syslog_code(entry.level)
            message = six.u(message)
            log = six.u(self.format_template).format(
                host=host or '',
                facility=facility or '',
                timestamp=timestamp.format("YYYY-MM-DD HH:mm:ss.SSS"),
                level=log_level['name'],
                message=message,
                field_text="; ".join(field_text))

            if color:
                return colored(log, log_level['color'], log_level['bg_color'])
            else:
                return log

        return format

    def dump_format(self, fields=["message", "source", "facility"]):
        def format(entry):
            timestamp = entry.timestamp.to('local').format("YYYY-MM-DD HH:mm:ss.SSS")
            return timestamp+";"+";".join(map(lambda f: "'{val}'".format(val=entry.message_dict.get(f, "")), fields))
        return format


class LogLevel(object):

    LEVELS = {
        syslog.LOG_CRIT:    {'name': 'CRITICAL', 'color': 'white', 'bg_color': 'on_red'},
        syslog.LOG_ERR:     {'name': 'ERROR', 'color': 'red', 'bg_color': None},
        syslog.LOG_WARNING: {'name': 'WARNING', 'color': 'yellow', 'bg_color': None},
        syslog.LOG_NOTICE:  {'name': 'NOTICE', 'color': 'green', 'bg_color': None},
        syslog.LOG_INFO:    {'name': 'INFO', 'color': 'green', 'bg_color': None},
        syslog.LOG_DEBUG:   {'name': 'DEBUG', 'color': 'blue', 'bg_color': None},
    }

    DEFAULT_CONFIG = {'name': '', 'color': 'green', 'bg_color': None}

    @staticmethod
    def find_by_syslog_code(level):
        return LogLevel.LEVELS.get(level, LogLevel.DEFAULT_CONFIG)

    @staticmethod
    def find_by_level_name(level_name):
        for key, value in LogLevel.LEVELS.items():
            if value['name'] == level_name:
                return key

    @staticmethod
    def list_levels():
        return [l.get('name') for l in LogLevel.LEVELS.values()]
