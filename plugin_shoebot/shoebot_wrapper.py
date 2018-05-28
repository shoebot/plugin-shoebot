"""
Run Shoebot in a separate process.

Communication by sending commands over stdin/out.
"""
from plugin_shoebot._vendor.asynchronousfilereader import AsynchronousFileReader

try:
    import queue
except ImportError:
    import Queue as queue

import base64
import collections
import os
import re
import subprocess
import sys
import uuid

PY3 = sys.version_info[0] == 3

CMD_LOAD_BASE64 = 'load_base64'

RESPONSE_CODE_OK = "CODE_OK"
RESPONSE_REVERTED = "REVERTED"


class CommandResponse(collections.namedtuple("CommandResponse", ['cmd', 'cookie', 'status', 'info'])):
    __slots__ = ()

    def __new__(cls, cmd, cookie, status=None, info=[]):
        return super(CommandResponse, cls).__new__(cls, cmd, cookie, status, info)

    def __str__(self):
        return 'cmd: {0} info{1}'.format(self.cmd, self.info)


class ShoebotProcess(object):
    """
    Runs an instance of Shoebot

    use send_command to control the instance, CommandResponse objects
    come back in the response_queue

    """

    def __init__(self, source, use_socketserver, show_varwindow, use_fullscreen, verbose, title, cwd=None,
                 handle_stdout=None, handle_stderr=None, sbot=None):
        # start with -w for window -l for shell'
        command = [sbot, '-wl', '-t%s - Shoebot on gedit' % title]

        if use_socketserver:
            command.append('-s')

        if not show_varwindow:
            command.append('-dv')

        if use_fullscreen:
            command.append('-f')

        if verbose:
            command.append("-V")

        command.append(source)

        # Setup environment so shoebot directory is first
        _env = os.environ.copy()
        if sbot:
            _env.update(
                PATH=os.path.realpath(os.path.dirname(sbot)) + os.pathsep + os.environ.get('PATH', ''),
                # PYTHONUNBUFFERED='1'
            )
        else:
            sys.err.write('no sbot!\n')

        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        bufsize=1, close_fds=os.name != 'nt', shell=False, cwd=cwd)

        self.running = True

        self.responses = {}

        # Launch the asynchronous readers of the process' stdout and stderr.
        self.stdout_queue = queue.Queue()
        self.stdout_reader = AsynchronousFileReader(self.process.stdout, self.stdout_queue)
        self.stderr_queue = queue.Queue()
        self.stderr_reader = AsynchronousFileReader(self.process.stderr, self.stderr_queue)

        self.response_queue = queue.Queue()

        self.handle_stdout = handle_stdout
        self.handle_stderr = handle_stderr
        self.changed_handler_id = None

        self.source = source.rstrip('\n')

        # self.setup_io()

    def setup_io(self):
        # Turn off user prompts
        self.send_command('prompt', 'off')
        self.send_command('')

        # Make responses single lines
        self.send_command("escape_nl")
        self.send_command('')

    def live_source_load(self, source):
        """
        Send new source code to the bot

        :param source:
        :param good_cb: callback called if code was good
        :param bad_cb: callback called if code was bad (will get contents of exception)
        :return:
        """
        source = source.rstrip('\n')
        if source != self.source:
            self.source = source
            b64_source = base64.b64encode(bytes(bytearray(source, "ascii")))
            self.send_command(CMD_LOAD_BASE64, b64_source)

    def pause(self, callback=None):
        self.send_command('pause', callback=callback)

    def send_command(self, cmd, *args):
        """
        :param cmd:
        :param args:
        :return:
        """
        # Test in python 2 and 3 before modifying (gedit2 + 3)
        if True:
            # Create a CommandResponse using a cookie as a unique id
            cookie = str(uuid.uuid4())
            response = CommandResponse(cmd, cookie, None, info=[])
            self.responses[cookie] = response
            args = list(args) + [b'cookie=' + bytes(cookie, "ascii")]
        if args:
            bytes_args = []
            for arg in args:
                if isinstance(arg, bytes):
                    bytes_args.append(arg)
                else:
                    bytes_args.append(bytearray(arg, "ascii"))
            data = bytearray(cmd, "ascii") + b' ' + b' '.join(bytes_args) + b'\n'
        else:
            data = bytearray(cmd, "ascii") + b'\n'

        self.process.stdin.write(data)
        self.process.stdin.flush()

    def close(self):
        """
        Close outputs of process.
        """
        self.process.stdout.close()
        self.process.stderr.close()
        self.running = False

    def filter_command_response(self, line):
        """
        :param line: Line from bots stdout
        :return:  True if the line was part of a response to a command
        """
        line = line.rstrip()
        for cookie, response in list(self.responses.items()):
            if line.startswith(cookie):
                pattern = r"^" + cookie + "\s?(?P<status>(.*?))[\:>](?P<info>.*)"

                match = re.match(pattern, line)
                d = match.groupdict()
                status = d.get('status')
                info = d.get('info')

                if not response.status and status:
                    self.responses[cookie] = response = \
                        CommandResponse(response.cmd, cookie, response.status or status, response.info)

                response.info.append(info)

                # If delimiter was '>' there are more lines
                # If delimiter was ':' request is complete
                delimiter = re.match('.*([:>])', line).group(1)
                if delimiter == ':':
                    del self.responses[cookie]
                    self.response_queue.put_nowait(response)

                return True  # response was handled

    def get_output(self):
        """
        :yield: stdout_line, stderr_line, running

        Generator that outputs lines captured from stdout and stderr

        These can be consumed to output on a widget in an IDE
        """

        if self.process.poll() is not None:
            self.close()
            yield None, None

        while not (self.stdout_queue.empty() and self.stderr_queue.empty()):
            if not self.stdout_queue.empty():
                line = self.stdout_queue.get().decode('utf-8')
                if self.filter_command_response(line):
                    continue

                yield line, None

            if not self.stderr_queue.empty():
                line = self.stderr_queue.get().decode('utf-8')
                yield None, line

    def get_command_responses(self):
        """
        Get responses to commands sent
        """
        if not self.response_queue.empty():
            yield None
        while not self.response_queue.empty():
            line = self.response_queue.get()
            if line is not None:
                yield line
