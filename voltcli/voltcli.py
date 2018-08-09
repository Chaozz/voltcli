from __future__ import unicode_literals
from __future__ import print_function

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from pygments.lexers.sql import SqlLexer

from subprocess import call
from voltcompleter import VoltCompleter

import click

click.disable_unicode_literals_warning = True

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


class VoltCli(object):
    def __init__(self, completer):
        self.completer = completer
        self.multiline = True

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
            self.completer.update_functions(["HelloWol", 'tTest'])

        return bindings

    def bottom_toolbar(self):
        toolbar_result = []
        if self.completer.smart_completion:
            toolbar_result.append(
                '<style bg="ansiyellow">[F2]</style> <b><style bg="ansigreen">Smart Completion:</style></b> ON  ')
        else:
            toolbar_result.append(
                '<style bg="ansiyellow">[F2]</style> <b><style bg="ansired">Smart Completion:</style></b> OFF  ')

        if self.multiline:
            toolbar_result.append(
                '<style bg="ansiyellow">[F3]</style> <b><style bg="ansigreen">Multiline:</style></b> ON  ')
        else:
            toolbar_result.append(
                '<style bg="ansiyellow">[F3]</style> <b><style bg="ansired">Multiline:</style></b> OFF  ')

        return HTML(''.join(toolbar_result))

    def refresh_completions(self, history=None, persist_priorities='all'):
        """ Refresh outdated completions

        :param history: A prompt_toolkit.history.FileHistory object. Used to
                        load keyword and identifier preferences

        :param persist_priorities: 'all' or 'keywords'
        """

        # callback = functools.partial(self._on_completions_refreshed,
        #                              persist_priorities=persist_priorities)
        # self.completion_refresher.refresh(self.pgexecute, self.pgspecial,
        #     callback, history=history, settings=self.settings)
        # return [(None, None, None,
        #         'Auto-completion refresh started in the background.')]
        pass

    def run_cli(self, server, port, user, password, credentials, kerberos, query_timeout):
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=self.completer, style=style,
            auto_suggest=AutoSuggestFromHistory(), bottom_toolbar=self.bottom_toolbar,
            key_bindings=self.create_key_bindings(), multiline=self.multiline)
        while True:
            try:
                sql_cmd = session.prompt('> ')
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            else:
                call("echo \"{sql_cmd}\" | sqlcmd".format(sql_cmd=sql_cmd), shell=True)
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
    volt_cli = VoltCli(VoltCompleter())
    volt_cli.run_cli(server, port, user, password, credentials, kerberos, query_timeout)


if __name__ == '__main__':
    cli()
