
from __future__ import division, print_function

try:
    import configparser
except:
    from six.moves import configparser

import os
import sys
import click
import getpass
from graylog_api import GraylogAPI


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

def get_message_format_template(cfg, format_template_name):
    section_name = "format:" + format_template_name
    try:
        format = cfg.get(section_name, FORMAT)
    except:
        format = DEFAULT_MESSAGE_FORMAT_TEMPLATE
    return format

def cli_error(msg):
    click.echo(click.style(msg, fg='red'))
    sys.exit(1)

def _get_host(cfg, section_name):
    return cfg.has_option(section_name, HOST)

def api_from_config(cfg, node_name="default"):
    section_name = "environment:" + node_name

    if cfg.has_option(section_name, HOST):
        host = cfg.get(section_name, HOST)
    else:
        raise Exception("'host' option is not available in section [%(section_name)s]" % {'section_name': section_name})

    port = 80
    if cfg.has_option(section_name, PORT):
        port = cfg.get(section_name, PORT)

    if cfg.has_option(section_name, USERNAME):
        username = cfg.get(section_name, USERNAME)
    else:
        username = getpass.getuser()

    scheme = "http"
    if cfg.has_option(section_name, TLS):
        tls = cfg.get(section_name, TLS)
        if (tls.lower()=="true" or tls==True):
            scheme = "https"

    if cfg.has_option(section_name, PROXY):
        proxies = {scheme: cfg.get(section_name, PROXY)}
    else:
        proxies = None

    default_stream = None
    if cfg.has_option(section_name, DEFAULT_STREAM):
        default_stream = cfg.get(section_name, DEFAULT_STREAM)

    return GraylogAPI(host=host, port=port, username=username, default_stream=default_stream,
                      scheme=scheme, proxies=proxies)


def api_from_host(host, port, username, scheme, proxies=None):
    return GraylogAPI(host=host, port=port, username=username,
                      scheme=scheme, proxies=proxies)