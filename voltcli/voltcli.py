from __future__ import unicode_literals, print_function

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from pygments.lexers.sql import SqlLexer
from subprocess import call
import click

from voltcompleter import VoltCompleter
from voltrefresher import VoltRefresher
from voltexecuter import VoltExecuter

click.disable_unicode_literals_warning = True

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


class VoltCli(object):
    def __init__(self, server, port, user, password, credentials, kerberos, query_timeout):
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.credentials = credentials
        self.kerberos = kerberos
        self.query_timeout = query_timeout

        self.completer = VoltCompleter()
        self.refresher = VoltRefresher()
        self.executer = VoltExecuter(self.server, self.port, self.user, self.password,
                                     self.query_timeout)
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
        self.refresher.refresh(self.executer, self.completer, [])
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=self.completer, style=style,
            auto_suggest=AutoSuggestFromHistory(), bottom_toolbar=self.bottom_toolbar,
            key_bindings=self.create_key_bindings(), multiline=self.multiline)
        option_str = "--servers={server} --port={port_number}{user}{password}{credentials}{kerberos} --query-timeout={number_of_milliseconds}".format(
            server=self.server, port_number=self.port,
            user="--user=" + self.user if self.user else "",
            password="--password=" + self.password if self.password else "",
            credentials="--credentials=" + self.credentials if self.credentials else "",
            kerberos="--kerberos=" + self.kerberos if self.kerberos else "",
            number_of_milliseconds=self.query_timeout)
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
                    self.refresher.refresh(self.executer, self.completer, [])
                    continue
                call(
                    "echo \"{sql_cmd}\" | sqlcmd {options}".format(
                        sql_cmd=sql_cmd, options=option_str),
                    shell=True)
                if self.auto_refresh:
                    self.refresher.refresh(self.executer, self.completer, [])
        print('GoodBye!')


@click.command()
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
def cli(server, port, user, password, credentials, kerberos, query_timeout):
    volt_cli = VoltCli(server, port, user, password, credentials, kerberos, query_timeout)
    volt_cli.run_cli()


if __name__ == '__main__':
    cli()
