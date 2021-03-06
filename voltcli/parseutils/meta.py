from collections import namedtuple

_ColumnMetadata = namedtuple(
    'ColumnMetadata',
    ['name', 'datatype', 'foreignkeys', 'default', 'has_default']
)


def ColumnMetadata(
        name, datatype, foreignkeys=None, default=None, has_default=False
):
    return _ColumnMetadata(
        name, datatype, foreignkeys or [], default, has_default
    )


TableMetadata = namedtuple('TableMetadata', 'name columns')
