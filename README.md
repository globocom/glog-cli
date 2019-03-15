PyGray
===============================

* Free software: Apache Software License 2.0

PyGray is a modified fork of the Glog-CLI, an open source command line interface for Graylog2.

## Instalation

Requirements: Python 3

Try (don't use Python2' pip!):

```bash
pip3 install pygray
```

or you can even install it from a GitHub clone:

```bash
git clone https://github.com/joaomarcusc/pygray
cd pygray/
pip3 install . -r requirements.txt
```

## Usage

PyGray enables you to make searches using the official Graylog query language. To understand how to make queries 
please see the [documentation](http://docs.graylog.org/en/2.1/pages/queries.html).

Once you've installed the tool now it's time to run some commands, the following:

```bash
pygray -h mygraylog.server.com -u john.doe -p password -@ "10 minutes ago" "source:my-app-server"
```

```bash
pygray -h mygraylog.server.com -u john.doe -p password "message:200"
```
```bash
pygray -h mygraylog.server.com -u john.doe -p password -f
```

```bash
pygray -h mygraylog.server.com -u john.doe -p password "level:DEBUG"
```

```bash
pygray -h mygraylog.server.com -u john.doe -p password "level:DEBUG" -f
```

```bash
pygray -h mygraylog.server.com -u john.doe -p password "level:DEBUG" -d --fields timestamp,level,message -o dump.csv
```

```bash
pygray -h mygraylog.server.com -u john-doe -p password -@ "2016-11-21 00:00:00" -# "2016-11-21 01:00:00" 'message:blabla'
```

```bash
pygray -e dev -r short
```

```bash
pygray -e dev -r short -st mystreamid
```

```bash
pygray -e dev -r short -st '*'
```


## Configuration


PyGray can reuse some common configurations like address of your Graylog server and your credentials, it will look for a
*~/.pygray.cfg* or a *pygray.cfg* (in your current directory). PyGray will use default environment and format 
whenever an environment or format is omitted.

Here is a example for your pygray.cfg file:

```
[environment:default]
host=mygraylogserver.com
port=443
username=john.doe

[environment:dev]
host=mygraylogserver.dev.com
port=443
proxy=mycompanyproxy.com
username=john.doe
default_stream=57e14cde6fb78216a60d35e8

[format:default]
format={host} {level} {facility} {timestamp} {message}
    
[format:short]
format=[{timestamp}] {level} {message}
    
[format:long]
format=time: [{timestamp}] level: {level} msg: {message} tags: {tags}
color=false
```

Please run the *help* command to more detailed information about all the client features.

```
Usage: pygray [OPTIONS] [QUERY]

Options:
  -v, --version                   Prints your pygray version
  -h, --host TEXT                 Your graylog node's host
  -e, --environment TEXT          Label of a preconfigured graylog node
  -sq, --saved-query              List user saved queries for selection
  --port TEXT                     Your graylog port
  --no-tls                        Not use TLS to connect to Graylog server
  -u, --username TEXT             Your graylog username
  -p, --password TEXT             Your graylog password (default: prompt)
  -k, --keyring / -nk, --no-keyring
                                  Use keyring to store/retrieve password
  -@, --search-from TEXT          Query range from
  -#, --search-to TEXT            Query range to (default: now)
  --tail                          Show the last n lines for the query
                                  (default)
  -d, --dump                      Print the query result as a csv
  --fields TEXT                   Comma separated fields to be printed in the
                                  csv.
  -o, --output TEXT               Output logs to file (only tail/dump mode)
  -f, --follow                    Poll the logging server for new logs
                                  matching the query (sets search from to now,
                                  limit to None)
  -n, --limit INTEGER             Limit the number of results (default: 100)
  -a, --latency INTEGER           Latency of polling queries (default: 2)
  -st, --stream TEXT              Stream ID of the stream to query (default:
                                  no stream filter)
  -s, --sort TEXT                 Field used for sorting (default: timestamp)
  --asc / --desc                  Sort ascending / descending
  --proxy TEXT                    Proxy to use for the http/s request
  -r, --format-template TEXT      Message format template for the log
                                  (default: default format
  --no-color                      Don't show colored logs
  -c, --config TEXT               Custom config file path
  --help                          Show this message and exit.
  ```

## Contributing
See [contributing](https://github.com/globocom/PyGray/blob/master/CONTRIBUTING.rst) document to learn how to contribute with us.
