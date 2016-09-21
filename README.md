===============================
Glog-CLI
===============================


.. image:: https://img.shields.io/pypi/v/glogcli.svg
        :target: https://pypi.python.org/pypi/glogcli
        
.. image:: https://pyup.io/repos/github/sinvalmendes/glogcli/shield.svg
     :target: https://pyup.io/repos/github/globocom/glogcli/
     :alt: Updates


* Free software: Apache Software License 2.0

Glog-CLI is an opensource command line interface for Graylog2.

Instalation
--------
Try:

	pip install glogcli

or:

	easy_install glogcli

or you can even install it from a GitHub clone:

	git clone https://github.com/globocom/glog-cli
	cd glog-cli/
	pip install .

Usage
--------
Once you've installed glogcli, it's time to run some commands, try one of the following:

> glogcli -h mygraylog.server.com -u john.doe -p password -@ "10 minutes ago" "source:my-app-server"

-

> glogcli -h mygraylog.server.com -u john.doe -p password "message:200"

-

> glogcli -h mygraylog.server.com -u john.doe -p password -f

-

> glocli -h mygraylog.server.com -u john.doe -p password "level:DEBUG"

-

> glocli -h mygraylog.server.com -u john.doe -p password "level:DEBUG" -f



Configuration
--------

Glog-CLI can reuse some common configurations like address of your Graylog server and your credentials, it will look for a
*~/.glogcli.cfg* or a *glogcli.cfg* (in your current directory).

Here is a template for your glogcli.cfg file:

    [environment:default]
    host=1.2.3.4
    port=80
    username=john.doe

    [format:custom]
    format={host} {level} {facility} {timestamp} {message} {field_text}

Please run the *help* command to more detailed information about all the client features.
	
	glogcli --help

    Usage: glogcli [OPTIONS] [QUERY]

    Options:
      -h, --host TEXT             Your graylog node's host
      -e, --environment TEXT      Label of a preconfigured graylog node
      -sq, --saved-query          List user saved queries for selection
      --port INTEGER              Your graylog port (default: 80)
      --tls                       Uses TLS
      -u, --username TEXT         Your graylog username
      -p, --password TEXT         Your graylog password (default: prompt)
      -@, --search-from TEXT      Query range from
      -#, --search-to TEXT        Query range to (default: now)
      --tail                      Show the last n lines for the query (default)
      -d, --dump                  Print the query result as a csv
      -o, --output TEXT           Output logs to file (only tail/dump mode)
      -f, --follow                Poll the logging server for new logs matching
                                  the query (sets search from to now, limit to
                                  None)
      -n, --limit INTEGER         Limit the number of results (default: 100)
      -a, --latency INTEGER       Latency of polling queries (default: 2)
      -s, --stream TEXT           Stream ID of the stream to query (default: no
                                  stream filter)
      --field TEXT                Fields to include in the query result
      -s, --sort TEXT             Field used for sorting (default: timestamp)
      --asc / --desc              Sort ascending / descending
      --proxy TEXT                Proxy to use for the http/s request
      -r, --format-template TEXT  Message format template for the log (default:
                                  syslog format
      --help                      Show this message and exit.