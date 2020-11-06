from __future__ import division, print_function
import re
import click
import requests
import arrow
import syslog
import six
from pygray import utils
from pygray.dateutils import datetime_converter

from pygray.utils import cli_error, store_password_in_keyring, get_password_from_keyring, write_config_entry
from pygray.formats import LogLevel
from pygray.input import CliInterface

from requests.packages.urllib3 import disable_warnings

disable_warnings()

class Message(object):

    def __init__(self, message_dict={}):
        self.message_dict = dict(message_dict[utils.MESSAGE])
        self.timestamp = arrow.get(self.message_dict.get("timestamp", None))
        self.level = self.message_dict.get("level", syslog.LOG_INFO)
        self.message = self.message_dict.get(utils.MESSAGE, "")


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

    def __init__(self, host, port, username, api_path=utils.DEFAULT_API_PATH, password=None, host_tz='local', default_stream=None, scheme='http', proxies=None, insecure_https=False, session_id=None, store_session=False):
        self.host = host
        self.port = port
        if api_path.endswith("/") or len(api_path) == 0:
            self.api_path = api_path
        else:
            self.api_path = api_path + "/"
        self.username = username
        self.password = password
        self.user = None
        self.session_id = session_id

        self.post_header = {"Accept": "application/json", "Content-Type": "application/json" }
        self.host_tz = host_tz
        self.default_stream = default_stream
        self.proxies = proxies
        self.scheme = scheme
        self.get_header = {"Accept": "application/json"}
        self.post_header = {"Accept": "application/json", "Content-Type": "application/json", "X-Requested-By": "pygray"}
        self.base_url = "{scheme}://{host}:{port}/{api_path}".format(host=host, port=port, scheme=scheme, api_path=api_path)
        self.insecure_https = insecure_https
        self.store_session = store_session

    def post(self, url, **kwargs):
        skip_auth, ignore_errors = kwargs.get("skip_auth", False), kwargs.get("ignore_errors", False)
        if not self.session_id and not skip_auth:
            self.auth_session()
        verify = not self.insecure_https    
        r = requests.post(self.base_url + url, verify=verify, json=kwargs["data"], headers=self.post_header, proxies=self.proxies)
        return self._parse_response(r, url, ignore_errors)

    def update_host_timezone(self, timezone):
        if timezone:
            self.host_tz = timezone

    def get(self, url, **kwargs):
        skip_auth, ignore_errors = kwargs.get("skip_auth", False), kwargs.get("ignore_errors", False)
        if not self.session_id and not skip_auth:
            self.auth_session()
        params = {}

        for label, item in six.iteritems(kwargs):
            if isinstance(item, list):
                params[label + "[]"] = item
            else:
                params[label] = item

        verify = not self.insecure_https
        get_args = dict(verify=verify, params=params, headers=self.get_header, proxies=self.proxies)
        if not skip_auth:
            get_args["auth"] = (self.session_id, "session")
        r = requests.get(self.base_url + url, **get_args)
        return self._parse_response(r, url, ignore_errors)

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

    def auth_session(self):
        must_authenticate = True
        if self.is_session_active():
            must_authenticate = False
        if must_authenticate:
            if not self.password:
                self.password = CliInterface.prompt_password(self.scheme, self.host, self.port, self.username, self.api_path)
            result = self.post(url="system/sessions", data=dict(username=self.username,password=self.password,host=""), skip_auth=True)
            self.session_id = result["session_id"]
            if self.store_session:
                self.store_current_session()
        self.update_host_timezone(self.user_info().get('timezone'))



    def store_current_session(self):
        write_config_entry("sessions", self.host, self.session_id)


    def is_session_active(self):
        if not self.session_id:
            return False
        value = self.get(url=("users/" + self.username), ignore_errors=True)
        return value is not None

    def user_info(self):
        if not self.user:
            self.user = self.get(url=("users/" + self.username))
        return self.user

    def streams(self):
        return self.get(url="streams/enabled")

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

    def _parse_response(self, r, url, ignore_errors):
        if r.status_code == requests.codes.ok:
            return r.json()
        elif ignore_errors:
            return None
        elif r.status_code == 401:
            click.echo("API error: {} Message: User authorization denied.".format(r.status_code))
            exit()
        else:
            click.echo("API error: URL: {} Status: {} Message: {}".format(self.base_url + url, r.status_code, r.content))
            exit()


class GraylogAPIFactory(object):

    @staticmethod
    def get_graylog_api(cfg, environment, host, password, port, proxy, no_tls, username, keyring, insecure_https, store_session):
        gl_api = None

        scheme = "https"

        if no_tls:
            scheme = "http"

        if scheme == "https" and port is None:
            port = 443
        port = port or 80

        proxies = {scheme: proxy} if proxy else None

        if environment is not None:
            gl_api = GraylogAPIFactory.api_from_config(cfg, environment, port, proxies, no_tls, username, insecure_https, store_session)
        else:
            if host is not None:
                if username is None:
                    username = CliInterface.prompt_username(scheme, host, port)

                gl_api = GraylogAPIFactory.api_from_host(
                    host=host, port=port, username=username, password=password, scheme=scheme, proxies=proxies, tls=no_tls,
                    insecure_https=insecure_https, store_session=store_session)
            else:
                if cfg.has_section("environment:default"):
                    gl_api = GraylogAPIFactory.api_from_config(cfg, "default", port, proxies, no_tls, username)
                else:
                    cli_error("Error: No host or environment configuration specified and no default found.")

        if not password and keyring:
            password = get_password_from_keyring(gl_api.host, gl_api.username)

        if not password and not gl_api.session_id:
            password = CliInterface.prompt_password(scheme, gl_api.host, gl_api.port, gl_api.username, gl_api.api_path)

        gl_api.password = password

        if keyring:
            store_password_in_keyring(gl_api.host, gl_api.username, password)

        return gl_api

    @staticmethod
    def api_from_host(host, port, username, password, scheme, proxies=None, tls=True, insecure_https=False, session_id=None, store_session=False):
        scheme = "https" if tls else "http"
        return GraylogAPI(host=host, port=port, username=username, password=password, scheme=scheme, proxies=proxies, insecure_https=insecure_https, session_id=session_id, store_session=store_session)

    @staticmethod
    def api_from_config(cfg, env_name, port, proxies, no_tls, username, insecure_https, store_session):
        section_name = "environment:" + env_name

        host = None
        if cfg.has_option(section_name, utils.HOST):
            host = cfg.get(section_name, utils.HOST)
        else:
            cli_error("'host' option is not available in section [%(section_name)s]" % {'section_name': section_name})

        if not port and cfg.has_option(section_name, utils.PORT):
            port = cfg.get(section_name, utils.PORT)

        if cfg.has_option(section_name, utils.API_PATH):
            api_path = cfg.get(section_name, utils.API_PATH)
        else:
            api_path = utils.DEFAULT_API_PATH

        scheme = "https"

        if no_tls:
            scheme = "http"

        if not username and cfg.has_option(section_name, utils.USERNAME):
            username = cfg.get(section_name, utils.USERNAME)
        elif not username:
            username = CliInterface.prompt_username(scheme, host, port)

        if cfg.has_section("sessions") and cfg.get("sessions", host):
            session_id = cfg.get("sessions", host)
        else:
            session_id = None


        if not proxies and cfg.has_option(section_name, utils.PROXY):
            proxies = {scheme: cfg.get(section_name, utils.PROXY)}

        default_stream = None
        if cfg.has_option(section_name, utils.DEFAULT_STREAM):
            default_stream = cfg.get(section_name, utils.DEFAULT_STREAM)

        return GraylogAPI(
            host=host, port=port, api_path=api_path, username=username, default_stream=default_stream, scheme=scheme, proxies=proxies, insecure_https=insecure_https,
            session_id=session_id, store_session=store_session
        )
