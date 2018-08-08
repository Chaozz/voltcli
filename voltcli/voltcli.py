from __future__ import unicode_literals
from __future__ import print_function

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from pygments.lexers.sql import SqlLexer

from subprocess import call
from voltcompleter import VoltCompleter

import click

click.disable_unicode_literals_warning = True

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

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

        return bindings


    def bottom_toolbar(self):
        toolbar_result = []
        if self.completer.smart_completion:
            toolbar_result.append('[F2] <b><style bg="ansired">Smart Completion:</style></b> ON  ')
        else:
            toolbar_result.append('[F2] <b><style bg="ansired">Smart Completion:</style></b> OFF  ')

        if self.multiline:
            toolbar_result.append('[F3] <b><style bg="ansired">Multiline:</style></b> ON  ')
        else:
            toolbar_result.append('[F3] <b><style bg="ansired">Multiline:</style></b> OFF  ')

        return HTML(''.join(toolbar_result))

    def run_cli(self, servers, port, user, password, credentials, kerberos, query_timeout):
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=self.completer, style=style,
            auto_suggest=AutoSuggestFromHistory(), bottom_toolbar=self.bottom_toolbar,
            key_bindings=self.create_key_bindings())
        while True:
            try:
                sql_cmd = session.prompt('> ', multiline=self.multiline)
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            else:
                call("echo \"{sql_cmd}\" | sqlcmd".format(sql_cmd=sql_cmd), shell=True)
        print('GoodBye!')


@click.command()
@click.option('-s', '--servers', default='localhost',
              help='List of servers to connect to (comma-separated).')
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
def cli(servers, port, user, password, credentials, kerberos, query_timeout):
    volt_cli = VoltCli(VoltCompleter())
    volt_cli.run_cli(servers, port, user, password, credentials, kerberos, query_timeout)
    # sql_completer = VoltCompleter()
    #
    # session = PromptSession(
    #     lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style, multiline=True,
    #     auto_suggest=AutoSuggestFromHistory(), bottom_toolbar=bottom_toolbar)
    #
    # while True:
    #     try:
    #         sql_cmd = session.prompt('> ')
    #     except KeyboardInterrupt:
    #         break
    #     except EOFError:
    #         break
    #     else:
    #         call("echo \"{sql_cmd}\" | sqlcmd".format(sql_cmd=sql_cmd), shell=True)
    # print('GoodBye!')


if __name__ == '__main__':
    cli()
