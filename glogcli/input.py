import getpass
import click
from glogcli import utils


class CliInterface(object):

    @staticmethod
    def select_stream(graylog_api, stream):
        stream_filter = None
        if stream or (graylog_api.user["permissions"] != ["*"] and graylog_api.default_stream is None):
            if not stream:
                streams = graylog_api.streams()["streams"]
                click.echo("Please select a stream to query:")
                for i, stream in enumerate(streams):
                    stream_id = stream["id"].encode(utils.UTF8)
                    message = "{}: Stream '{}' (id: {})".format(i, stream["title"].encode(utils.UTF8), stream_id)
                    click.echo(message)
                stream_index = click.prompt("Enter stream number:", type=int, default=0)
                stream = streams[stream_index]["id"]
            stream_filter = "streams:{}".format(stream)
        return stream_filter

    @staticmethod
    def select_saved_query(graylog_api):
        searches = graylog_api.get_saved_queries()["searches"]
        for i, search in enumerate(searches):
            search_title = search["title"].encode(utils.UTF8)
            query = search["query"]["query"].encode(utils.UTF8) or "*"
            message = "{}: Query '{}' (query: {})".format(i, search_title, query)
            click.echo(message)
        search_index = click.prompt("Enter query number:", type=int, default=0)
        search = searches[search_index]
        query = search['query']['query'].encode(utils.UTF8) or '*'
        fields = search['query']['fields'].encode(utils.UTF8).split(',')
        return query, fields

    @staticmethod
    def prompt_password(host, port, username):
        prompt_message = "Enter password for {username}@{host}:{port}".format(username=username, host=host, port=port)
        return click.prompt(prompt_message, hide_input=True)

    @staticmethod
    def prompt_username(host, port):
        return click.prompt("Enter username for {host}:{port}".format(host=host, port=port), default=getpass.getuser())
