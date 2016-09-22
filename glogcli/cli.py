#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import click
import arrow
from glogcli.graylog_api import SearchRange, SearchQuery, GraylogAPIFactory
from glogcli.utils import get_config, get_message_format_template
from glogcli.output import LogPrinter
from glogcli.formats import Formatter
from glogcli.utils import UTF8


@click.command()
@click.option("-h", "--host", default=None, help="Your graylog node's host")
@click.option("-e", "--environment", default=None,  help="Label of a preconfigured graylog node")
@click.option("-sq", "--saved-query", is_flag=True, default=False, help="List user saved queries for selection")
@click.option("--port", default=80, help="Your graylog port (default: 80)")
@click.option("--tls",  default=False, is_flag=True, help="Uses TLS")
@click.option("-u", "--username", default=None, help="Your graylog username")
@click.option("-p", "--password", default=None, help="Your graylog password (default: prompt)")
@click.option("-@", "--search-from", default="5 minutes ago", help="Query range from")
@click.option("-#", "--search-to", default=None, help="Query range to (default: now)")
@click.option('--tail', 'mode', flag_value='tail', default=True, help="Show the last n lines for the query (default)")
@click.option('-d', '--dump', 'mode', flag_value='dump', help="Print the query result as a csv")
@click.option('-o', '--output', default=None, help="Output logs to file (only tail/dump mode)")
@click.option("-f", "--follow", default=False, is_flag=True, help="Poll the logging server for new logs matching the query (sets search from to now, limit to None)")
@click.option("-n", "--limit", default=100, help="Limit the number of results (default: 100)")
@click.option("-a", "--latency", default=2, help="Latency of polling queries (default: 2)")
@click.option("-s", "--stream", default=None, help="Stream ID of the stream to query (default: no stream filter)")
@click.option('--field', multiple=True, help="Fields to include in the query result")
@click.option('--sort', '-s', default=None, help="Field used for sorting (default: timestamp)")
@click.option("--asc/--desc", default=False, help="Sort ascending / descending")
@click.option("--proxy", default=None, help="Proxy to use for the http/s request")
@click.option('-r', '--format-template', default="syslog", help="Message format template for the log (default: syslog format")
@click.argument('query', default="*")
def run(host,
        environment,
        saved_query,
        port,
        tls,
        username,
        password,
        search_from,
        search_to,
        mode,
        output,
        follow,
        limit,
        latency,
        stream,
        field,
        sort,
        asc,
        proxy,
        format_template,
        query):

    cfg = get_config()

    gl_api = GraylogAPIFactory.get_graylog_api(cfg, environment, host, password, port, proxy, tls, username)

    sr = SearchRange(from_time=search_from, to_time=search_to)
    fields = None
    if field:
        fields = list(field)

    if limit <= 0:
        limit = None

    if follow:
        limit = None
        sort = None
        sr.from_time = arrow.now().replace(seconds=-latency-1)
        sr.to_time = arrow.now().replace(seconds=-latency)

    userinfo = gl_api.user_info()

    stream_filter = None
    if stream or (userinfo["permissions"] != ["*"] and gl_api.default_stream is None):
        if not stream:
            streams = gl_api.streams()["streams"]
            click.echo("Please select a stream to query:")
            for i, stream in enumerate(streams):
                click.echo("{}: Stream '{}' (id: {})".format(i, stream["title"].encode(UTF8), stream["id"].encode(UTF8)))
            i = click.prompt("Enter stream number:", type=int, default=0)
            stream = streams[i]["id"]
        stream_filter = "streams:{}".format(stream)

    if saved_query:
        searches = gl_api.get_saved_queries()["searches"]
        for i, search in enumerate(searches):
            click.echo("{}: Query '{}' (query: {})".format(i, search["title"].encode(UTF8), search["query"]["query"].encode(UTF8) or "*"))
        i = click.prompt("Enter query number:", type=int, default=0)
        search = searches[i]
        query = search['query']['query'].encode(UTF8) or '*'
        fields = search['query']['fields'].encode(UTF8).split(',')

    q = SearchQuery(search_range=sr, query=query, limit=limit, filter=stream_filter, fields=fields, sort=sort, ascending=asc)

    formatter = get_formatter(cfg, fields, format_template, mode)
    LogPrinter().run_logprint(gl_api, q, formatter, follow, latency, output)


def get_formatter(cfg, fields, format_template, mode):
    format_template = get_message_format_template(cfg, format_template)
    formatter = Formatter(format_template)
    if mode == "tail":
        if fields:
            formatter = formatter.tail_format(fields)
        else:
            formatter = formatter.tail_format()
    elif mode == "dump":
        formatter = formatter.dump_format()
    return formatter


if __name__ == "__main__":
    run()