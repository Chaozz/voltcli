from __future__ import print_function, unicode_literals

import operator
import re
from collections import namedtuple, OrderedDict
from itertools import chain

from prompt_toolkit.completion import Completer, Completion

from parseutils.utils import last_word
from prioritization import PrevalenceCounter
from sqlcompletion import suggest_type, Column
from voltliterals.literals import get_literals

Match = namedtuple('Match', ['completion', 'priority'])

_Candidate = namedtuple(
    'Candidate', 'completion prio meta synonyms prio2 display'
)

# Used to strip trailing '::some_type' from default-value expressions
arg_default_type_strip_regex = re.compile(r'::[\w\.]+(\[\])?$')

normalize_ref = lambda ref: ref if ref[0] == '"' else '"' + ref.lower() + '"'


def generate_alias(tbl):
    """ Generate a table alias, consisting of all upper-case letters in
    the table name, or, if there are no upper-case letters, the first letter +
    all letters preceded by _
    param tbl - unescaped name of the table to alias
    """
    return ''.join([l for l in tbl if l.isupper()] or
                   [l for l, prev in zip(tbl, '_' + tbl) if prev == '_' and l != '_'])


def Candidate(
        completion, prio=None, meta=None, synonyms=None, prio2=None,
        display=None
):
    return _Candidate(
        completion, prio, meta, synonyms or [completion], prio2,
                                display or completion
    )


class VoltCompleter(Completer):
    # keywords_tree: A dict mapping keywords to well known following keywords.
    # e.g. 'CREATE': ['TABLE', 'USER', ...],
    keywords_tree = get_literals('keywords', type_=dict)
    keywords = tuple(set(chain(keywords_tree.keys(), *keywords_tree.values())))
    functions = get_literals('functions')
    datatypes = get_literals('datatypes')
    reserved_words = set(get_literals('reserved'))

    def __init__(self, smart_completion=True):
        self.smart_completion = smart_completion
        self.prioritizer = PrevalenceCounter()
        self.keyword_casing = "upper"
        self.name_pattern = re.compile(r"^[_a-z][_a-z0-9\$]*$")
        self.databases = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.casing = {}

        self.all_completions = set(self.keywords + self.functions)

    def escape_name(self, name):
        """ Quote a string."""
        if name and ((not self.name_pattern.match(name))
                     or (name.upper() in self.reserved_words)
                     or (name.upper() in self.functions)):
            name = '"%s"' % name

        return name

    def unescape_name(self, name):
        """ Unquote a string."""
        if name and name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

    def escaped_names(self, names):
        return [self.escape_name(name) for name in names]

    def reset_completions(self):
        self.databases = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.all_completions = set(self.keywords + self.functions)

    def case(self, word):
        return self.casing.get(word, word)

    def find_matches(self, text, collection, mode='fuzzy', meta=None):
        """Find completion matches for the given text.

        Given the user's input text and a collection of available
        completions, find completions matching the last word of the
        text.

        `collection` can be either a list of strings or a list of Candidate
        namedtuples.
        `mode` can be either 'fuzzy', or 'strict'
            'fuzzy': fuzzy matching, ties broken by name prevalance
            `keyword`: start only matching, ties broken by keyword prevalance

        yields prompt_toolkit Completion instances for any matches found
        in the collection of available completions.

        """
        if not collection:
            return []
        priority_order = [
            'keyword', 'function', 'view', 'table', 'datatype', 'database',
            'schema', 'column', 'table alias', 'join', 'name join', 'fk join',
            'table format'
        ]
        type_priority = priority_order.index(meta) if meta in priority_order else -1
        text = last_word(text, include='most_punctuations').lower()
        text_len = len(text)

        if text and text[0] == '"':
            # text starts with double quote; user is manually escaping a name
            # Match on everything that follows the double-quote. Note that
            # text_len is calculated before removing the quote, so the
            # Completion.position value is correct
            text = text[1:]

        if mode == 'fuzzy':
            fuzzy = True
            priority_func = self.prioritizer.name_count
        else:
            fuzzy = False
            priority_func = self.prioritizer.keyword_count

        # Construct a `_match` function for either fuzzy or non-fuzzy matching
        # The match function returns a 2-tuple used for sorting the matches,
        # or None if the item doesn't match
        # Note: higher priority values mean more important, so use negative
        # signs to flip the direction of the tuple
        if fuzzy:
            regex = '.*?'.join(map(re.escape, text))
            pat = re.compile('(%s)' % regex)

            def _match(item):
                if item.lower()[:len(text) + 1] in (text, text + ' '):
                    # Exact match of first word in suggestion
                    # This is to get exact alias matches to the top
                    # E.g. for input `e`, 'Entries E' should be on top
                    # (before e.g. `EndUsers EU`)
                    return float('Infinity'), -1
                r = pat.search(self.unescape_name(item.lower()))
                if r:
                    return -len(r.group()), -r.start()
        else:
            match_end_limit = len(text)

            def _match(item):
                match_point = item.lower().find(text, 0, match_end_limit)
                if match_point >= 0:
                    # Use negative infinity to force keywords to sort after all
                    # fuzzy matches
                    return -float('Infinity'), -match_point

        matches = []
        for cand in collection:
            # TODO
            if isinstance(cand, _Candidate):
                item, prio, display_meta, synonyms, prio2, display = cand
                if display_meta is None:
                    display_meta = meta
                syn_matches = (_match(x) for x in synonyms)
                # Nones need to be removed to avoid max() crashing in Python 3
                syn_matches = [m for m in syn_matches if m]
                sort_key = max(syn_matches) if syn_matches else None
            else:
                item, display_meta, prio, prio2, display = cand, meta, 0, 0, cand
                sort_key = _match(cand)

            if sort_key:
                if display_meta and len(display_meta) > 50:
                    # Truncate meta-text to 50 characters, if necessary
                    display_meta = display_meta[:47] + u'...'

                # Lexical order of items in the collection, used for
                # tiebreaking items with the same match group length and start
                # position. Since we use *higher* priority to mean "more
                # important," we use -ord(c) to prioritize "aa" > "ab" and end
                # with 1 to prioritize shorter strings (ie "user" > "users").
                # We first do a case-insensitive sort and then a
                # case-sensitive one as a tie breaker.
                # We also use the unescape_name to make sure quoted names have
                # the same priority as unquoted names.
                lexical_priority = (tuple(0 if c in (' _') else -ord(c)
                                          for c in self.unescape_name(item.lower())) + (1,)
                                    + tuple(c for c in item))

                item = self.case(item)
                display = self.case(display)
                priority = (
                    sort_key, type_priority, prio, priority_func(item),
                    prio2, lexical_priority
                )
                matches.append(
                    Match(
                        completion=Completion(
                            text=item,
                            start_position=-text_len,
                            display_meta=display_meta,
                            display=display
                        ),
                        priority=priority
                    )
                )
        return matches

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            matches = self.find_matches(word_before_cursor, self.all_completions,
                                        mode='strict')
            completions = [m.completion for m in matches]
            return sorted(completions, key=operator.attrgetter('text'))

        matches = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:
            suggestion_type = type(suggestion)

            # Map suggestion type to method
            # e.g. 'table' -> self.get_table_matches
            matcher = self.suggestion_matchers[suggestion_type]
            matches.extend(matcher(self, suggestion, word_before_cursor))

        # Sort matches so highest priorities are first
        matches = sorted(matches, key=operator.attrgetter('priority'),
                         reverse=True)

        return [m.completion for m in matches]

    # TODO: currently return all column names
    def get_column_matches(self, suggestion, word_before_cursor):
        tables = suggestion.table_refs

        def make_candidate(name):
            synonyms = (name, generate_alias(self.case(name)))
            return Candidate(self.case(name), 0, 'column', synonyms)

        # TODO: make sure fit the real dbmetadata structure
        return self.find_matches(word_before_cursor,
                                 [make_candidate(c.name) for t in self.dbmetadata['tables'] for c in t['columns']],
                                 meta='column')

    suggestion_matchers = {
        Column: get_column_matches,
    }