
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


def get_config():
    config = configparser.ConfigParser()
    config.read(['glogcli.cfg', os.path.expanduser('~/.glogcli.cfg')])

    return config

def get_message_format_template(cfg, format_template_name):
    section_name = "format:" + format_template_name
    try:
        format = cfg.get(section_name, "format")
    except:
        format = "{host} {level} {timestamp} {facility} {message}"
    return format

def cli_error(msg):
    click.echo(click.style(msg, fg='red'))
    sys.exit(1)

def _get_host(cfg, section_name):
    return cfg.has_option(section_name, "host")

def api_from_config(cfg, node_name="default"):
    section_name = "environment:" + node_name

    if cfg.has_option(section_name, "host"):
        host = cfg.get(section_name, "host")
    else:
        raise Exception("'host' option is not available in section [%(section_name)s]" % {'section_name': section_name})

    port = 80
    if cfg.has_option(section_name, "port"):
        port = cfg.get(section_name, "port")

    if cfg.has_option(section_name, "username"):
        username = cfg.get(section_name, "username")
    else:
        username = getpass.getuser()

    scheme = "http"
    if cfg.has_option(section_name, "tls"):
        tls = cfg.get(section_name, "tls")
        if (tls.lower()=="true" or tls==True):
            scheme = "https"

    if cfg.has_option(section_name, "proxy"):
        proxies = {scheme: cfg.get(section_name, "proxy")}
    else:
        proxies = None

    default_stream = None
    if cfg.has_option(section_name, "default_stream"):
        default_stream = cfg.get(section_name, "default_stream")

    return GraylogAPI(host=host, port=port, username=username, default_stream=default_stream,
                      scheme=scheme, proxies=proxies)


def api_from_host(host, port, username, scheme, proxies=None):
    return GraylogAPI(host=host, port=port, username=username,
                      scheme=scheme, proxies=proxies)