from __future__ import unicode_literals
from __future__ import print_function

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from subprocess import call

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


class PGCli(object):
    pass


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
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

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


if __name__ == '__main__':
    cli()
