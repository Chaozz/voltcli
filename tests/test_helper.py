from mock import Mock
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document


def completion(display_meta, text, pos=0):
    return Completion(text, start_position=pos, display_meta=display_meta)


def get_result(completer, text, position=None):
    position = len(text) if position is None else position
    return completer.get_completions(
        Document(text=text, cursor_position=position), Mock()
    )


def get_result_set(completer, text, position=None):
    return set(get_result(completer, text, position))