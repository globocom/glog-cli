from __future__ import division, print_function
import re
import click
import requests
import arrow
import syslog
import six
import getpass
from dateutils import datetime_converter
from glogcli import utils
from glogcli.utils import cli_error
from glogcli.formats import LogLevel


class Message(object):

    def __init__(self, message_dict={}):
        self.message_dict = dict(message_dict[utils.MESSAGE])
        self.timestamp = arrow.get(self.message_dict.get("timestamp", None))
        self.level = self.message_dict.get("level", syslog.LOG_INFO)
        self.message = self.message_dict.get(utils.MESSAGE, "")

    def simple_formatted(self):
        return "[{}] {}: {}".format(self.timestamp, self.level, self.message)


class SearchResult(object):

    def __init__(self, result_dict={}):
        self.query = result_dict.get("query", None)
        self.query_object = None
        self.used_indices = result_dict.get("used_indices", None)
        self.queried_range = result_dict.get("queried_range", None)
        self.range_from = arrow.get(result_dict.get("from", None))
        self.range_to = arrow.get(result_dict.get("to", None))
        self.range_duration = result_dict.get("time", None)
        self.fields = result_dict.get("fields", [])
        self.total_results = result_dict.get("total_results", None)

        self.messages = list(map(Message, result_dict.get("messages", [])))

    def simple_formatted(self):
        return "\n".join(map(lambda m: m.simple_formatted(), self.messages))


class SearchRange(object):

    def __init__(self, from_time=None, to_time=None, relative=False):
        self.from_time = datetime_converter(from_time)
        self.to_time = datetime_converter(to_time)
        self.relative = relative

    def is_relative(self):
        return self.relative

    def range_in_seconds(self):
        if self.is_relative():
            range = arrow.now('local').timestamp - self.from_time.timestamp
        else:
            range = (self.to_time - self.from_time).seconds

        if range < 1:
            return 1
        return range


class SearchQuery(object):

    def __init__(self, search_range, query="*", limit=None, offset=None, filter=None, fields=None, sort=None, ascending=False):
        self.search_range = search_range
        self.query = SearchQuery.replace_log_level(query)
        self.limit = limit
        self.offset = offset
        self.filter = filter
        self.fields = fields
        self.sort = sort
        self.ascending = ascending

    @staticmethod
    def replace_log_level(query):
        log_level_regex = 'level\:\s*[a-zA-Z]+\s*'
        match = re.search(log_level_regex, query)
        if match:
            log_level_name = match.group(0).split(':')[1].strip().upper()
            log_level_code = LogLevel.find_by_level_name(log_level_name)
            if not log_level_code:
                message = "The given log level({}) is invalid. Use one of the following: {}"
                cli_error(message.format(log_level_name, LogLevel.list_levels()))
                exit()
            return re.sub(log_level_regex, 'level:%s ' % log_level_code, query)
        else:
            return query

    def copy_with_range(self, search_range):
        return SearchQuery(search_range, self.query, self.limit, self.offset, self.filter, self.fields, self.sort, self.ascending)


class GraylogAPI(object):

    def __init__(self, host, port, username, password=None, host_tz='local', default_stream=None, scheme='http', proxies=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.host_tz = host_tz
        self.default_stream = default_stream
        self.proxies = proxies
        self.get_header = {"Accept": "application/json"}
        self.base_url = "{scheme}://{host}:{port}/api/".format(host=host, port=port, scheme=scheme)

    def get(self, url, **kwargs):
        params = {}

        for label, item in six.iteritems(kwargs):
            if isinstance(item, list):
                params[label + "[]"] = item
            else:
                params[label] = item

        r = requests.get(self.base_url + url, params=params, headers=self.get_header, auth=(self.username, self.password), proxies=self.proxies)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            click.echo("API error: Status: {} Message: {}".format(r.status_code, r.content))
            exit()

    def search(self, query, fetch_all=False):
        sort = None
        if query.sort is not None:
            if query.ascending:
                sort = query.sort + ":asc"
            else:
                sort = query.sort + ":desc"

        if fetch_all and query.limit is None:
            result = self.search_raw(
                query.query, query.search_range, 1, query.offset, query.filter, query.fields, sort
            )

            sr = SearchRange(from_time=result.range_from, to_time=result.range_to)

            if result.total_results > 10000:
                raise RuntimeError("Query returns more than 10000 log entries. Use offsets to query in chunks.")

            result = self.search_raw(
                query.query, sr, result.total_results, query.offset, query.filter, query.fields, sort
            )

        else:
            result = self.search_raw(
                query.query, query.search_range, query.limit, query.offset, query.filter, query.fields, sort
            )

        result.query_object = query
        return result

    def user_info(self):
        return self.get(url=("users/" + self.username))

    def streams(self):
        return self.get(url="streams")

    def get_saved_queries(self):
        return self.get(url="search/saved")

    def search_raw(self, query, search_range, limit=None, offset=None, filter=None, fields=None, sort=None):
        url = "search/universal/"
        range_args = {}

        if filter is None and self.default_stream is not None:
            filter = "streams:{}".format(self.default_stream)

        if search_range.is_relative():
            url += "relative"
            range_args["range"] = search_range.range_in_seconds()
        else:
            url += "absolute"
            range_args["from"] = search_range.from_time.to(self.host_tz).format(utils.DEFAULT_DATE_FORMAT)
            to_time = arrow.now(self.host_tz) if search_range.to_time is None else search_range.to_time.to(self.host_tz)
            range_args["to"] = to_time.format(utils.DEFAULT_DATE_FORMAT)

        if fields is not None:
            fields = ",".join(fields)

        result = self.get(
            url=url,
            query=query,
            limit=limit,
            offset=offset,
            filter=filter,
            fields=fields,
            sort=sort,
            **range_args
        )

        return SearchResult(result)

    def get_saved_query(self):
        searches = self.get_saved_queries()["searches"]
        for i, search in enumerate(searches):
            click.echo("{}: Query '{}' (query: {})".format(i, search["title"].encode(utils.UTF8),
                                                           search["query"]["query"].encode(utils.UTF8) or "*"))
        i = click.prompt("Enter query number:", type=int, default=0)
        search = searches[i]
        query = search['query']['query'].encode(utils.UTF8) or '*'
        fields = search['query']['fields'].encode(utils.UTF8).split(',')
        return query, fields

    def get_stream(self, stream, userinfo):
        stream_filter = None
        if stream or (userinfo["permissions"] != ["*"] and self.default_stream is None):
            if not stream:
                streams = self.streams()["streams"]
                click.echo("Please select a stream to query:")
                for i, stream in enumerate(streams):
                    click.echo(
                        "{}: Stream '{}' (id: {})".format(i, stream["title"].encode(utils.UTF8), stream["id"].encode(utils.UTF8)))
                i = click.prompt("Enter stream number:", type=int, default=0)
                stream = streams[i]["id"]
            stream_filter = "streams:{}".format(stream)
        return stream_filter


class GraylogAPIFactory(object):

    @staticmethod
    def get_graylog_api(cfg, environment, host, password, port, proxy, tls, username):
        gl_api = None
        if environment is not None:
            gl_api = GraylogAPIFactory.api_from_config(cfg, env_name=environment)
        else:
            if host is not None:
                if username is None:
                    username = click.prompt(
                        "Enter username for {host}:{port}".format(host=host, port=port), default=getpass.getuser()
                    )
                scheme = "https" if tls else "http"
                proxies = {scheme: proxy} if proxy else None

                gl_api = GraylogAPIFactory.api_from_host(
                    host=host, port=port, username=username, scheme=scheme, proxies=proxies
                )
            else:
                if cfg.has_section("environment:default"):
                    gl_api = GraylogAPIFactory.api_from_config(cfg)
                else:
                    cli_error("Error: No host or environment configuration specified and no default found.")

        if username is not None:
            gl_api.username = username

        if password is None:
            prompt_message = "Enter password for {username}@{host}:{port}".format(
                username=gl_api.username, host=gl_api.host, port=gl_api.port
            )
            password = click.prompt(prompt_message, hide_input=True)

        gl_api.password = password
        return gl_api

    @staticmethod
    def api_from_host(host, port, username, scheme, proxies=None):
        return GraylogAPI(host=host, port=port, username=username, scheme=scheme, proxies=proxies)

    @staticmethod
    def api_from_config(cfg, env_name="default"):
        section_name = "environment:" + env_name

        host = None
        if cfg.has_option(section_name, utils.HOST):
            host = cfg.get(section_name, utils.HOST)
        else:
            cli_error("'host' option is not available in section [%(section_name)s]" % {'section_name': section_name})

        port = 80
        if cfg.has_option(section_name, utils.PORT):
            port = cfg.get(section_name, utils.PORT)

        if cfg.has_option(section_name, utils.USERNAME):
            username = cfg.get(section_name, utils.USERNAME)
        else:
            username = getpass.getuser()

        scheme = "http"
        if cfg.has_option(section_name, utils.TLS):
            tls = cfg.get(section_name, utils.TLS)
            if tls.lower() == "true" or tls is True:
                scheme = "https"

        if cfg.has_option(section_name, utils.PROXY):
            proxies = {scheme: cfg.get(section_name, utils.PROXY)}
        else:
            proxies = None

        default_stream = None
        if cfg.has_option(section_name, utils.DEFAULT_STREAM):
            default_stream = cfg.get(section_name, utils.DEFAULT_STREAM)

        return GraylogAPI(host=host, port=port, username=username, default_stream=default_stream, scheme=scheme, proxies=proxies)
