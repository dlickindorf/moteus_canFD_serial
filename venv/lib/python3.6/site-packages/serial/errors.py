from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from .utilities.compatibility import backport

backport()

from future.utils import native_str

from datetime import date, datetime
from decimal import Decimal
from numbers import Number

try:
    import typing
except ImportError as e:
    typing = None

from .abc.model import Model
from .utilities import qualified_name, collections, collections_abc, Generator


class ValidationError(Exception):

    pass


class VersionError(AttributeError):

    pass


class DefinitionExistsError(Exception):

    pass


class UnmarshalValueError(ValueError):

    pass


UNMARSHALLABLE_TYPES = tuple({
    str, bytes, native_str, Number, Decimal, date, datetime, bool,
    dict, collections.OrderedDict,
    collections_abc.Set, collections_abc.Sequence, Generator,
    Model
})


class UnmarshalError(Exception):

    def __init__(
        self,
        data,  # type: Any
        types=None,  # type: Optional[Sequence[Model, Property, type]]
        item_types=None,  # type: Optional[Sequence[Model, Property, type]]
        value_types=None  # type: Optional[Sequence[Model, Property, type]]
    ):
        # type: (...) -> None
        """
        Generate a comprehensible error message for data which could not be un-marshalled according to spec, and raise
        the appropriate exception
        """

        self._message = None  # type: Optional[str]
        self._parameter = None  # type: Optional[str]
        self._index = None  # type: Optional[int]
        self._key = None  # type: Optional[str]

        error_message_lines = ['']

        # Identify which parameter is being used for type validation

        types_label = None

        if types:
            types_label = 'types'
        elif item_types:
            types_label = 'item_types'
            types = item_types
        elif value_types:
            types_label = 'value_types'
            types = value_types

        # Assemble the error message

        # Assemble a text representation of the `data`

        data_lines = []

        lines = repr(data).strip().split('\n')

        if len(lines) == 1:

            data_lines.append(lines[0])

        else:

            data_lines.append('')

            for line in lines:
                data_lines.append(
                    '     ' + line
                )

        # Assemble a text representation of the `types`, `item_types`, or `value_types`.

        if types is None:

            error_message_lines.append('The data provided is not an instance of an un-marshallable type:')

        else:

            error_message_lines.append(
                'The data provided does not match any of the expected types and/or property definitions:'
            )

        error_message_lines.append(
            ' - data: %s' % '\n'.join(data_lines)
        )

        if types is None:

            types = UNMARSHALLABLE_TYPES
            types_label = 'un-marshallable types'

        types_lines = ['(']

        for type_ in types:

            if isinstance(type_, type):
                lines = (qualified_name(type_),)
            else:
                lines = repr(type_).split('\n')

            for line in lines:
                types_lines.append(
                    '     ' + line
                )

            types_lines[-1] += ','

        types_lines.append('   )')

        error_message_lines.append(
            ' - %s: %s' % (types_label, '\n'.join(types_lines))
        )

        self.message = '\n'.join(error_message_lines)

    @property
    def paramater(self):
        # type: (...) -> Optional[str]
        return self._parameter

    @paramater.setter
    def paramater(self, paramater_name):
        # type: (str) -> None
        if paramater_name != self.paramater:
            self._parameter = paramater_name
            self.assemble_message()

    @property
    def message(self):
        # type: (...) -> Optional[str]
        return self._message

    @message.setter
    def message(self, message_text):
        # type: (str) -> None
        if message_text != self.message:
            self._message = message_text
            self.assemble_message()

    @property
    def index(self):
        # type: (...) -> Optional[int]
        return self._message

    @index.setter
    def index(self, index_or_key):
        # type: (Union[str, int]) -> None
        if index_or_key != self.index:
            self._index = index_or_key
            self.assemble_message()

    def assemble_message(self):

        messages = []

        if self.paramater:
            messages.append(
                'Errors encountered in attempting to un-marshal %s:' % self.paramater
            )

        if self.index is not None:
            messages.append(
                'Errors encountered in attempting to un-marshal the value at index %s:' % repr(self.index)
            )

        if self.message:
            messages.append(self.message)

        super().__init__('\n'.join(messages))


class UnmarshalTypeError(UnmarshalError, TypeError):

    pass


class UnmarshalValueError(UnmarshalError, ValueError):

    pass
