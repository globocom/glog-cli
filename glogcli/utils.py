from __future__ import division, print_function

try:
    import configparser
except:
    from six.moves import configparser

import re
import os
import sys
import click
import keyring


DEFAULT_DATE_FORMAT = "YYYY-MM-DD HH:mm:ss.SSS"
MESSAGE = "message"
FACILITY = "facility"
SOURCE = "source"
LEVEL = "level"
TIMESTAMP = "timestamp"
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
COLOR = "color"
PROXY = "proxy"
DEFAULT_STREAM = "default_stream"
DEFAULT_MESSAGE_FORMAT_TEMPLATE = "{source} {level} {timestamp} {facility} {message}"


def get_glogcli_version():
    return "0.8.1"

def get_config(config_file_path="~/.glogcli.cfg"):
    config = configparser.ConfigParser()
    try:
        open(os.path.expanduser(config_file_path))
    except Exception:
        click.echo("[WARNING] - Could not find %s file. Please create the configuration file like:" % config_file_path)
        click.echo("\n[environment:default]\n"
                   "host=mygraylogserver.com\n"
                   "port=443\n"
                   "username=john.doe\n"
                   "default_stream=*\n"
                   "\n"
                   "[environment:dev]\n"
                   "host=mygraylogserver.dev.com\n"
                   "port=443\n"
                   "proxy=mycompanyproxy.com\n"
                   "username=john.doe\n"
                   "default_stream=57e14cde6fb78216a60d35e8\n"
                   "\n"
                   "[format:default]\n"
                   "format={host} {level} {facility} {timestamp} {message}\n"
                   "\n"
                   "[format:short]\n"
                   "format=[{timestamp}] {level} {message}\n"
                   "\n"
                   "[format:long]\n"
                   "format=time: [{timestamp}] level: {level} msg: {message} tags: {tags}\n"
                   "color=false\n"
                   "\n")

    config.read(os.path.expanduser(config_file_path))
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


def extract_fields_from_format(cfg, format_name):
    if cfg.has_option("format:" + format_name, FORMAT):
        fields = re.findall('\{.*?\}', cfg.get("format:" + format_name, FORMAT))
        return [f[1:-1] for f in fields]


def get_color_option(cfg, format_name, no_color):
    if no_color:
        return False
    if cfg.has_option("format:" + format_name, COLOR):
        return cfg.get("format:" + format_name, COLOR) == 'true'
    else:
        return True
