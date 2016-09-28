from __future__ import division, print_function
from termcolor import colored
import syslog
import six
from glogcli import utils


class Formatter(object):

    def __init__(self, format_template, fields=None, color=True):
        self.format_template = format_template
        self.color = color
        self.fields = fields if fields else [utils.MESSAGE, utils.SOURCE, utils.FACILITY]

    def format(self, entry):
        raise NotImplementedError()

    def encode_message(self, message):
        if six.PY2:
            try:
                message = message.encode(utils.UTF8)
            except:
                pass
        return six.u(message)


class TailFormatter(Formatter):

    def format(self, entry):
        message = entry.message
        timestamp = entry.timestamp.to("local")
        host = entry.message_dict.get("source")
        facility = entry.message_dict.get("facility")
        local_fields = list(self.fields)

        if utils.MESSAGE in local_fields:
            local_fields.remove(utils.MESSAGE)

        log_level = LogLevel.find_by_syslog_code(entry.level)
        args = {
            'timestamp': timestamp.format(utils.DEFAULT_DATE_FORMAT),
            'level': log_level['name'],
            'message': self.encode_message(message) ,
            'host': host or '',
            'facility': facility or ''
        }

        for field in local_fields:
            args[field] = entry.message_dict.get(field, '')

        log = six.u(self.format_template).format(**args)

        if self.color:
            return colored(log, log_level['color'], log_level['bg_color'])
        else:
            return log


class DumpFormatter(Formatter):

    def format(self, entry):
        timestamp = entry.timestamp.to('local').format(utils.DEFAULT_DATE_FORMAT)
        return timestamp + ";" + ";".join(map(lambda f: "'{val}'".format(val=entry.message_dict.get(f, "")), self.fields))


class FormatterFactory(object):

    @staticmethod
    def get_formatter(mode, cfg, format_template, fields):
        format_template = FormatterFactory.get_message_format_template(cfg, format_template)
        if mode == "tail":
            return TailFormatter(format_template=format_template, fields=fields)
        elif mode == "dump":
            return DumpFormatter(format_template=format_template, fields=fields)

    @staticmethod
    def get_message_format_template(cfg, format_template_name):
        section_name = "format:" + format_template_name
        try:
            return cfg.get(section_name, utils.FORMAT)
        except:
            return utils.DEFAULT_MESSAGE_FORMAT_TEMPLATE


class LogLevel(object):

    LEVELS = {
        syslog.LOG_CRIT:    {'name': 'CRITICAL', 'color': 'white', 'bg_color': 'on_red'},
        syslog.LOG_ERR:     {'name': 'ERROR', 'color': 'red', 'bg_color': None},
        syslog.LOG_WARNING: {'name': 'WARNING', 'color': 'yellow', 'bg_color': None},
        syslog.LOG_NOTICE:  {'name': 'NOTICE', 'color': 'green', 'bg_color': None},
        syslog.LOG_INFO:    {'name': 'INFO', 'color': 'green', 'bg_color': None},
        syslog.LOG_DEBUG:   {'name': 'DEBUG', 'color': 'cyan', 'bg_color': None},
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
