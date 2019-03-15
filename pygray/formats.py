from __future__ import division, print_function
from termcolor import colored
import syslog
import six
from pygray import utils


class Formatter(object):

    DEFAULT_FIELDS = [utils.TIMESTAMP, utils.LEVEL, utils.MESSAGE, utils.SOURCE, utils.FACILITY]

    def __init__(self, format_template, fields=None, color=True):
        self.format_template = format_template
        self.color = color
        self.fields = fields if fields else self.DEFAULT_FIELDS

    def format(self, entry):
        raise NotImplementedError()

    def encode_message(self, message):
        return message


class TailFormatter(Formatter):

    def format(self, entry):
        message = entry.message
        timestamp = entry.timestamp.to("local")
        source = entry.message_dict.get("source", "")
        facility = entry.message_dict.get("facility", "")
        custom_fields = list(self.fields)

        log_level = LogLevel.find_by_syslog_code(entry.level)
        args = {
            'timestamp': timestamp.format(utils.DEFAULT_DATE_FORMAT),
            'level': log_level['name'],
            'message': self.encode_message(message),
            'source': source,
            'facility': facility
        }

        for field in custom_fields:
            if field not in self.DEFAULT_FIELDS:
                args[field] = entry.message_dict.get(field, '')

        log = self.format_template.format(**args)
        log = self.format_template.format(**args)

        if self.color:
            return colored(log, log_level['color'], log_level['bg_color'])
        else:
            return log


class DumpFormatter(Formatter):

    def format(self, entry):
        formatted_fields = dict()
        for field in self.fields:
            if field == 'timestamp':
                field_value = entry.timestamp.to('local').format(utils.DEFAULT_DATE_FORMAT)
            elif field == 'level':
                field_value = LogLevel.find_by_syslog_code(entry.level).get('name')
            else:
                field_value = entry.message_dict.get(field, "")
            formatted_fields[field] = field_value
        return ";".join(map(lambda f: "'{val}'".format(val=formatted_fields.get(f)), self.fields))


class FormatterFactory(object):

    @staticmethod
    def get_formatter(mode, cfg, format_template, fields, color):
        format_template = FormatterFactory.get_message_format_template(cfg, format_template)
        if mode == "tail":
            return TailFormatter(format_template=format_template, fields=fields, color=color)
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
        syslog.LOG_CRIT: {
            'name': 'CRITICAL',
            'color': 'white',
            'bg_color': 'on_red'
        },
        syslog.LOG_ERR: {
            'name': 'ERROR',
            'color': 'red',
            'bg_color': None
        },
        syslog.LOG_WARNING: {
            'name': 'WARNING',
            'color': 'yellow',
            'bg_color': None
        },
        syslog.LOG_NOTICE: {
            'name': 'NOTICE',
            'color': 'green',
            'bg_color': None
        },
        syslog.LOG_INFO: {
            'name': 'INFO',
            'color': 'green',
            'bg_color': None
        },
        syslog.LOG_DEBUG: {
            'name': 'DEBUG',
            'color': 'cyan',
            'bg_color': None
        },
    }

    DEFAULT_CONFIG = {
        'name': '',
        'color': 'green',
        'bg_color': None
    }

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
