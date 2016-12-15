from __future__ import division, print_function
import time
import arrow
from glogcli.graylog_api import SearchRange
from glogcli.utils import LOCAL_TIMEZONE

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class SimpleBuffer(object):
    
    def __init__(self):
        self.buffer = []

    def insert(self, object):
        self.buffer.append(object)

    def _clean_buffer(self):
        self.buffer = []

    def is_object_buffered(self, object):
        is_object_buffered = object in self.buffer
        if len(self.buffer) > 1000:
            self._clean_buffer()

        return is_object_buffered


class LogPrinter(object):

    def __init__(self):
        self.message_buffer = SimpleBuffer()

    def run_logprint(self, api, query, formatter, follow=False, output=None, header=None, interval=1000):
        if follow:
            assert query.limit is None

            close_output = False
            if output is not None and isinstance(output, basestring):
                output = open(output, "a")
                close_output = True

            try:
                while True:
                    self.run_logprint(api, query, formatter, follow=False, output=output)
                    new_range = SearchRange(to_time=arrow.now(LOCAL_TIMEZONE), from_time=arrow.now(LOCAL_TIMEZONE).replace(seconds=-5))
                    query = query.copy_with_range(new_range)
                    time.sleep(interval/1000.0)
            except KeyboardInterrupt:
                print("\nInterrupted follow mode. Exiting...")

            if close_output:
                output.close()

        else:
            result = api.search(query, fetch_all=True)
            formatted_msgs = []
            for message in result.messages:
                message_id = message.message_dict.get('_id')
                if not self.message_buffer.is_object_buffered(message_id):
                    formatted_msgs.append(formatter.format(message))
                    self.message_buffer.insert(message_id)

            formatted_msgs.reverse()

            if formatted_msgs:
                if output is None:
                    for msg in formatted_msgs:
                        print(msg.encode('utf-8').strip())
                else:
                    if isinstance(output, basestring):
                        with open(output, "a") as f:
                            f.writelines(('\n'.join(formatted_msgs) + '\n').encode('utf-8').strip())
                    else:
                        output.writelines(('\n'.join(formatted_msgs)+ '\n').encode('utf-8').strip())
            return result
