from __future__ import unicode_literals

from functools import partial
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from mock import Mock

from voltcli.voltcompleter import VoltCompleter
import pytest


def completion(display_meta, text, pos=0):
    return Completion(text, start_position=pos, display_meta=display_meta)


def get_result(completer, text, position=None):
    position = len(text) if position is None else position
    return completer.get_completions(
        Document(text=text, cursor_position=position), Mock()
    )


def result_set(completer, text, position=None):
    return set(get_result(completer, text, position))


def escape(name):
    if not name.islower() or name in ('select', 'localtimestamp'):
        return '"' + name + '"'
    return name


def function(text, pos=0, display=None):
    return Completion(
        text,
        display=display or text,
        start_position=pos,
        display_meta='function'
    )


table = partial(completion, 'table')
view = partial(completion, 'view')
column = partial(completion, 'column')
keyword = partial(completion, 'keyword')
datatype = partial(completion, 'datatype')
alias = partial(completion, 'table alias')
name_join = partial(completion, 'name join')
fk_join = partial(completion, 'fk join')
join = partial(completion, 'join')


def wildcard_expansion(cols, pos=-1):
    return Completion(
        cols, start_position=pos, display_meta='columns', display='*')


class MetaData(object):
    def __init__(self, metadata):
        self.metadata = metadata

    def builtin_functions(self, pos=0):
        return [function(f, pos) for f in self.completer.functions]

    def builtin_datatypes(self, pos=0):
        return [datatype(dt, pos) for dt in self.completer.datatypes]

    def keywords(self, pos=0):
        return [keyword(kw, pos) for kw in self.completer.keywords_tree.keys()]

    def columns(self, tbl, typ='tables', pos=0):
        cols = self.metadata[typ][tbl]
        return [column(col, pos) for col in cols]

    def datatypes(self, parent='public', pos=0):
        return [
            datatype(escape(x), pos)
            for x in self.metadata.get('datatypes', {}).get(parent, [])]

    def tables(self, parent='public', pos=0):
        return [
            table(escape(x), pos)
            for x in self.metadata.get('tables', {}).get(parent, [])]

    def views(self, parent='public', pos=0):
        return [
            view(escape(x), pos)
            for x in self.metadata.get('views', {}).get(parent, [])]

    def functions(self, pos=0):
        return [
            function(
                x,
                pos
            )
            for x in self.metadata.get('functions', [])
        ]

    def functions_and_keywords(self, pos=0):
        return (
            self.functions(pos) + self.builtin_functions(pos) +
            self.keywords(pos)
        )

    # Note that the filtering parameters here only apply to the columns
    def columns_functions_and_keywords(
            self, tbl, typ='tables', pos=0
    ):
        return (
            self.functions_and_keywords(pos=pos) +
            self.columns(tbl, typ, pos)
        )

    def from_clause_items(self, parent='public', pos=0):
        return (
            self.functions(parent, pos) + self.views(parent, pos) +
            self.tables(parent, pos)
        )

    def schemas_and_from_clause_items(self, parent='public', pos=0):
        return self.from_clause_items(parent, pos) + self.schemas(pos)

    def types(self, parent='public', pos=0):
        return self.datatypes(parent, pos) + self.tables(parent, pos)

    @property
    def completer(self):
        return self.get_completer()

    def get_completer(self, casing=None):
        get_casing = lambda words: dict((word.lower(), word) for word in words)

        comp = VoltCompleter(smart_completion=True)
        comp.dbmetadata = self.metadata
        if casing:
            comp.casing = get_casing(casing)

        return comp
