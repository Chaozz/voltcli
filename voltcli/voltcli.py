from __future__ import unicode_literals, print_function

import sys
from subprocess import call

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from voltcompleter import VoltCompleter
from voltexecutor import VoltExecutor
from voltrefresher import VoltRefresher

click.disable_unicode_literals_warning = True
isatty = True

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


class VoltCli(object):
    def __init__(self, server, port, user, password, credentials, kerberos, query_timeout, ssl, ssl_set,
                 output_format, output_skip_metadata, stop_on_error):
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.credentials = credentials
        self.kerberos = kerberos
        self.query_timeout = query_timeout
        self.ssl = ssl
        self.ssl_set = ssl_set
        self.output_format = output_format
        self.output_skip_metadata = output_skip_metadata
        self.stop_on_error = stop_on_error

        self.completer = VoltCompleter()
        self.refresher = VoltRefresher()
        self.executor = VoltExecutor(self.server, self.port, self.user, self.password,
                                     self.query_timeout, self.kerberos, self.ssl, self.ssl_set, self.credentials)
        self.multiline = True
        self.auto_refresh = True

    def create_key_bindings(self):
        bindings = KeyBindings()

        @bindings.add('f2')
        def _(event):
            self.completer.smart_completion = not self.completer.smart_completion

        @bindings.add('f3')
        def _(event):
            self.multiline = not self.multiline
            event.app.current_buffer.multiline = ~event.app.current_buffer.multiline

        @bindings.add('f4')
        def _(event):
            self.auto_refresh = not self.auto_refresh

        return bindings

    def bottom_toolbar(self):
        toolbar_result = []
        if self.completer.smart_completion:
            toolbar_result.append(
                '<style bg="ansiyellow">[F2]</style> <b><style bg="ansigreen">Smart Completion:</style></b> ON')
        else:
            toolbar_result.append(
                '<style bg="ansiyellow">[F2]</style> <b><style bg="ansired">Smart Completion:</style></b> OFF')

        if self.multiline:
            toolbar_result.append(
                '<style bg="ansiyellow">[F3]</style> <b><style bg="ansigreen">Multiline:</style></b> ON')
        else:
            toolbar_result.append(
                '<style bg="ansiyellow">[F3]</style> <b><style bg="ansired">Multiline:</style></b> OFF')
        if self.auto_refresh:
            toolbar_result.append(
                '<style bg="ansiyellow">[F4]</style> <b><style bg="ansigreen">Auto Refresh:</style></b> ON')
        else:
            toolbar_result.append(
                '<style bg="ansiyellow">[F4]</style> <b><style bg="ansired">Auto Refresh:</style></b> OFF')

        return HTML('  '.join(toolbar_result))

    def run_cli(self):
        # get catalog data before start
        self.refresher.refresh(self.executor, self.completer, [])
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=self.completer, style=style,
            auto_suggest=AutoSuggestFromHistory(), bottom_toolbar=self.bottom_toolbar,
            key_bindings=self.create_key_bindings(), multiline=self.multiline)
        option_str = "--servers={server} --port={port_number}{user}{password}{credentials}" \
                     "{ssl}{output_format}{output_skip_metadata}{stop_on_error}{kerberos} " \
                     "--query-timeout={number_of_milliseconds}".format(
                        server=self.server, port_number=self.port,
                        user=" --user=" + self.user if self.user else "",
                        password=" --password=" + self.password if self.password else "",
                        credentials=" --credentials=" + self.credentials if self.credentials else "",
                        kerberos=" --kerberos=" + self.kerberos if self.kerberos else "",
                        number_of_milliseconds=self.query_timeout,
                        ssl=" --ssl=" + self.ssl_set if self.ssl_set else " --ssl" if self.ssl else "",
                        output_format=" --output-format=" + self.output_format if self.output_format else "",
                        output_skip_metadata=" --output-skip-metadata" if self.output_skip_metadata else "",
                        stop_on_error=" --stop-on-error=false" if not self.stop_on_error else ""
                        )
        while True:
            try:
                sql_cmd = session.prompt('> ')
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            else:
                if sql_cmd.lower() == "update":
                    # use "update" command to force a fresh
                    self.refresher.refresh(self.executor, self.completer, [])
                    continue
                call(
                    "echo \"{sql_cmd}\" | sqlcmd {options}".format(
                        sql_cmd=sql_cmd, options=option_str),
                    shell=True)
                if self.auto_refresh:
                    self.refresher.refresh(self.executor, self.completer, [])
        print('GoodBye!')


class RegisterReaderOption(click.Option):
    """ Mark this option as getting a _set option """
    register_reader = True


class RegisterWriterOption(click.Option):
    """ Fix the help for the _set suffix """

    def get_help_record(self, ctx):
        help = super(RegisterWriterOption, self).get_help_record(ctx)
        return (help[0].replace('_set ', '='),) + help[1:]


class RegisterWriterCommand(click.Command):
    def parse_args(self, ctx, args):
        """ Translate any opt= to opt_set= as needed """
        options = [o for o in ctx.command.params
                   if getattr(o, 'register_reader', None)]
        prefixes = {p for p in sum([o.opts for o in options], [])
                    if p.startswith('--')}
        for i, a in enumerate(args):
            a = a.split('=')
            if a[0] in prefixes and len(a) > 1:
                a[0] += '_set'
                args[i] = '='.join(a)

        return super(RegisterWriterCommand, self).parse_args(ctx, args)


@click.command(cls=RegisterWriterCommand)
@click.option('-s', '--server', default='localhost',
              help='VoltDB server to connect to.')
@click.option('-p', '--port', default=21212,
              help='Client port to connect to on cluster nodes.')
@click.option('-u', '--user', default='',
              help='Name of the user for database login.')
@click.option('-p', '--password', default='', hide_input=True,
              help='Password of the user for database login.')
@click.option('-c', '--credentials', default='',
              help='File that contains username and password information.')
@click.option('-k', '--kerberos', default='',
              help='Enable kerberos authentication for user database login by specifying the JAAS login configuration '
                   'file entry name')
@click.option('-t', '--query-timeout', default=10000,
              help='Read-only queries that take longer than this number of milliseconds will abort.')
@click.option('--ssl', cls=RegisterReaderOption, is_flag=True,
              help='Enable ssl.')
@click.option('--ssl_set', cls=RegisterWriterOption,
              help='Specifying ssl-configuration-file.')
@click.option('--output-format', type=click.Choice(['fixed', 'csv', 'tab']),
              help='Format of returned resultset data (Fixed-width, CSV or Tab-delimited).\nDefault: fixed.')
@click.option('--output-skip-metadata', is_flag=True,
              help='Removes metadata information such as column headers and row count from produced output.\n'
                   'Default: metadata output is enabled.')
@click.option('--stop-on-error', default=True, type=bool,
              help='Causes the utility to stop immediately or continue after detecting an error. '
                   'In interactive mode, a value of "true" discards any unprocessed input and returns '
                   'to the command prompt. Default: true.')
def cli(server, port, user, password, credentials, kerberos, query_timeout, ssl, ssl_set,
        output_format, output_skip_metadata, stop_on_error):
    if not isatty:
        # if pipe from stdin
        sql_cmd = sys.stdin.read()
        option_str = "--servers={server} --port={port_number}{user}{password}{credentials}" \
                     "{ssl}{output_format}{output_skip_metadata}{stop_on_error}{kerberos} " \
                     "--query-timeout={number_of_milliseconds}".format(
                        server=server, port_number=port,
                        user=" --user=" + user if user else "",
                        password=" --password=" + password if password else "",
                        credentials=" --credentials=" + credentials if credentials else "",
                        kerberos=" --kerberos=" + kerberos if kerberos else "",
                        number_of_milliseconds=query_timeout,
                        ssl=" --ssl=" + ssl_set if ssl_set else " --ssl" if ssl else "",
                        output_format=" --output-format=" + output_format if output_format else "",
                        output_skip_metadata=" --output-skip-metadata" if output_skip_metadata else "",
                        stop_on_error=" --stop-on-error=false" if not stop_on_error else ""
                        )

        call(
            "echo \"{sql_cmd}\" | sqlcmd {options}".format(
                sql_cmd=sql_cmd, options=option_str),
            shell=True)
        return

    volt_cli = VoltCli(server, port, user, password, credentials, kerberos, query_timeout, ssl, ssl_set,
                       output_format, output_skip_metadata, stop_on_error)
    volt_cli.run_cli()


if __name__ == '__main__':
    isatty = sys.stdin.isatty()
    cli()
