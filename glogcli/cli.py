#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import click
import arrow
from glogcli.graylog_api import SearchRange, SearchQuery, GraylogAPIFactory
from glogcli.utils import get_config, get_color_option
from glogcli.output import LogPrinter
from glogcli.input import CliInterface
from glogcli.formats import FormatterFactory
from glogcli import utils


@click.command()
@click.option("-h", "--host", default=None, help="Your graylog node's host")
@click.option("-e", "--environment", default=None,  help="Label of a preconfigured graylog node")
@click.option("-sq", "--saved-query", is_flag=True, default=False, help="List user saved queries for selection")
@click.option("--port", default=80, help="Your graylog port (default: 80)")
@click.option("--tls",  default=False, is_flag=True, help="Uses TLS")
@click.option("-u", "--username", default=None, help="Your graylog username")
@click.option("-p", "--password", default=None, help="Your graylog password (default: prompt)")
@click.option("-k/-nk", "--keyring/--no-keyring", default=False, help="Use keyring to store/retrieve password")
@click.option("-@", "--search-from", default="5 minutes ago", help="Query range from")
@click.option("-#", "--search-to", default=None, help="Query range to (default: now)")
@click.option('--tail', 'mode', flag_value='tail', default=True, help="Show the last n lines for the query (default)")
@click.option('-d', '--dump', 'mode', flag_value='dump', help="Print the query result as a csv")
@click.option('--fields', default=None, help="Comma separated fields to be printed in the csv. ", callback=lambda ctx, param, v: v.split(',') if v else None)
@click.option('-o', '--output', default=None, help="Output logs to file (only tail/dump mode)")
@click.option("-f", "--follow", default=False, is_flag=True, help="Poll the logging server for new logs matching the query (sets search from to now, limit to None)")
@click.option("-n", "--limit", default=100, help="Limit the number of results (default: 100)")
@click.option("-a", "--latency", default=2, help="Latency of polling queries (default: 2)")
@click.option("-st", "--stream", default=None, help="Stream ID of the stream to query (default: no stream filter)")
@click.option('--sort', '-s', default=None, help="Field used for sorting (default: timestamp)")
@click.option("--asc/--desc", default=False, help="Sort ascending / descending")
@click.option("--proxy", default=None, help="Proxy to use for the http/s request")
@click.option('-r', '--format-template', default="default", help="Message format template for the log (default: default format")
@click.option("--no-color", default=False, is_flag=True, help="Don't show colored logs")
@click.argument('query', default="*")
def run(host,
        environment,
        saved_query,
        port,
        tls,
        username,
        password,
        keyring,
        search_from,
        search_to,
        mode,
        fields,
        output,
        follow,
        limit,
        latency,
        stream,
        sort,
        asc,
        proxy,
        format_template,
        no_color,
        query):

    cfg = get_config()

    graylog_api = GraylogAPIFactory.get_graylog_api(cfg, environment, host, password, port, proxy, tls, username, keyring)

    sr = SearchRange(from_time=search_from, to_time=search_to)

    if follow:
        limit = None
        sort = None
        sr.from_time = arrow.now().replace(seconds=-latency-1)
        sr.to_time = arrow.now().replace(seconds=-latency)

    limit = None if limit <= 0 else limit
    fields = fields if mode == 'dump' else utils.extract_fields_from_format(cfg, format_template)
    color = get_color_option(cfg, format_template, no_color)

    stream_filter = CliInterface.select_stream(graylog_api, stream)
    if saved_query:
        query, fields = CliInterface.select_saved_query(graylog_api)

    q = SearchQuery(search_range=sr, query=query, limit=limit, filter=stream_filter, fields=fields, sort=sort, ascending=asc)

    formatter = FormatterFactory.get_formatter(mode, cfg, format_template, fields, color)
    LogPrinter().run_logprint(graylog_api, q, formatter, follow, output)


if __name__ == "__main__":
    run()