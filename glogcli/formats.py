
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
            level = entry.level
            host = entry.message_dict.get("source")
            facility = entry.message_dict.get("facility")

            log_color = 'green'
            log_background = None

            if entry.level == syslog.LOG_CRIT:
                log_color = 'white'
                log_background = 'on_red'
                level = "CRITICAL"
            elif entry.level == syslog.LOG_ERR:
                log_color = 'red'
                level = "ERROR"
            elif entry.level == syslog.LOG_WARNING:
                log_color = 'yellow'
                level = "WARNING"
            elif entry.level == syslog.LOG_NOTICE:
                log_color = 'green'
                level = "NOTICE"
            elif entry.level == syslog.LOG_INFO:
                log_color = 'green'
                level = "INFO"
            elif entry.level == syslog.LOG_DEBUG:
                log_color = 'blue'
                level = "DEBUG"

            local_fields = list(fields)

            if "message" in local_fields:
                local_fields.remove("message")

            field_text = map(lambda f: "{}:{}".format(f, entry.message_dict.get(f, "")), local_fields)

            if six.PY2:
                try:
                    message = message.encode("utf-8")
                except:
                    pass

            message = six.u(message)
            log = six.u(self.format_template).format(
                host=host or '',
                facility=facility or '',
                timestamp=timestamp.format("YYYY-MM-DD HH:mm:ss.SSS"),
                level=level or '',
                message=message,
                field_text="; ".join(field_text))

            if color:
                return colored(log, log_color, log_background)
            else:
                return log

        return format

    def dump_format(self, fields=["message", "source", "facility"]):
        def format(entry):
            timestamp = entry.timestamp.to('local').format("YYYY-MM-DD HH:mm:ss.SSS")
            return timestamp+";"+";".join(map(lambda f: "'{val}'".format(val=entry.message_dict.get(f, "")), fields))
        return format