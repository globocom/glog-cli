from __future__ import division, print_function

try:
    import configparser
except:
    from six.moves import configparser

import os
import sys
import click
import keyring


DEFAULT_DATE_FORMAT = "YYYY-MM-DD HH:mm:ss.SSS"
MESSAGE = "message"
FACILITY = "facility"
SOURCE = "source"
MODULE = "module"
LINE = "line"
LOCAL_TIMEZONE = "local"
UTF8 = "utf-8"
USERNAME = "username"
PASSWORD = "password"
PORT = "port"
TLS = "tls"
HOST = "host"
FORMAT = "format"
PROXY = "proxy"
DEFAULT_STREAM = "default_stream"
DEFAULT_MESSAGE_FORMAT_TEMPLATE = "{host} {level} {timestamp} {facility} {message}"


def get_config():
    config = configparser.ConfigParser()
    config.read(['glogcli.cfg', os.path.expanduser('~/.glogcli.cfg')])
    return config


def cli_error(msg):
    click.echo(click.style(msg, fg='red'))
    sys.exit(1)


def _get_host(cfg, section_name):
    return cfg.has_option(section_name, "host")


def store_password_in_keyring(host, username, password):
    keyring.set_password('glog_' + host, username, password)

def get_password_from_keyring(host, username):
    return keyring.get_password('glog_' + host, username)
