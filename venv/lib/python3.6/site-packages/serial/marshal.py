# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from .utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

from copy import deepcopy

import json
from decimal import Decimal
from base64 import b64encode
from numbers import Number

import yaml
from datetime import date, datetime

from itertools import chain

import serial
from . import utilities, abc, properties, errors, meta, hooks
from .utilities import Generator, qualified_name, read, collections, collections_abc


try:
    from typing import Union, Optional, Sequence, Any, Callable
except ImportError:
    Union = Optional = Sequence = Any = Callable = None

try:
    from abc import ABC
except ImportError:
    ABC = None


UNMARSHALLABLE_TYPES = tuple({
    str, bytes, native_str, Number, Decimal, date, datetime, bool,
    dict, collections.OrderedDict,
    collections_abc.Set, collections_abc.Sequence, Generator,
    abc.model.Model, properties.Null, properties.NoneType
})


def ab2c(abc_or_property):
    # type: (ABC) -> Union[model.Object, model.Dict, model.Array, properties.Property]
    """
    Get the corresponding model class from an abstract base class, or if none exists--return the original class or type
    """

    class_or_property = abc_or_property  # type: (type)

    if isinstance(abc_or_property, type):

        if abc_or_property in {abc.model.Dictionary, abc.model.Array, abc.model.Object}:

            class_or_property = getattr(
                serial.model,
                abc_or_property.__name__.split('.')[-1]
            )

    elif isinstance(abc_or_property, properties.Property):

        class_or_property = deepcopy(abc_or_property)

        for types_attribute in ('types', 'value_types', 'item_types'):

            if hasattr(class_or_property, types_attribute):

                setattr(
                    class_or_property,
                    types_attribute,
                    tuple(
                        ab2c(type_) for type_ in getattr(class_or_property, types_attribute)
                    )
                )

    return class_or_property


def ab2cs(abcs_or_properties):
    # type: (Sequence[Union[ABC, properties.Property]]) -> Sequence[model.Model, properties.Property]
    for abc_or_property in abcs_or_properties:
        yield ab2c(abc_or_property)


class _Marshal(object):

    pass


def marshal(
    data,  # type: Any
    types=None,  # type: Optional[Sequence[Union[type, properties.Property, Callable]]]
    value_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
    item_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
):
    # type: (...) -> Any

    """
    Recursively converts instances of `serial.abc.model.Model` into JSON/YAML/XML serializable objects.
    """

    if hasattr(data, '_marshal'):
        return data._marshal()  # noqa - this is *our* protected member, so linters can buzz off

    if data is None:
        return data

    if callable(types):
        types = types(data)

    # If data types have been provided, validate the un-marshalled data by attempting to initialize the provided type(s)
    # with `data`

    if types is not None:

        if (str in types) and (native_str is not str) and (native_str not in types):

            types = tuple(chain(*(
                ((type_, native_str) if (type_ is str) else (type_,))
                for type_ in types
            )))

        matched = False

        for type_ in types:

            if isinstance(type_, properties.Property):

                try:
                    data = type_.marshal(data)
                    matched = True
                    break
                except TypeError:
                    pass

            elif isinstance(type_, type) and isinstance(data, type_):

                matched = True

                break

        if not matched:
            raise TypeError(
                '%s cannot be interpreted as any of the designated types: %s' % (
                    repr(data),
                    repr(types)
                )
            )

    if value_types is not None:
        for k, v in data.items():
            data[k] = marshal(v, types=value_types)

    if item_types is not None:

        for i in range(len(data)):
            data[i] = marshal(data[i], types=item_types)

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, (date, datetime)):
        return data.isoformat()

    if isinstance(data, native_str):
        return data

    if isinstance(data, (bytes, bytearray)):
        return str(b64encode(data), 'ascii')

    if hasattr(data, '__bytes__'):
        return str(b64encode(bytes(data)), 'ascii')

    return data


class _Unmarshal(object):
    """
    This class should be used exclusively by `serial.marshal.unmarshal`.
    """

    def __init__(
        self,
        data,  # type: Any
        types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
        value_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
        item_types=None  # type: Optional[Sequence[Union[type, properties.Property]]]
    ):
        # type: (...) -> None

        if not isinstance(
            data,
            UNMARSHALLABLE_TYPES
        ):
            # Verify that the data can be parsed before attempting to un-marshall it

            raise errors.UnmarshalTypeError(
                '%s, an instance of `%s`, cannot be un-marshalled. ' % (repr(data), type(data).__name__) +
                'Acceptable types are: ' + ', '.join((
                    qualified_name(data_type)
                    for data_type in UNMARSHALLABLE_TYPES
                ))
            )

        # If only one type was passed for any of the following parameters--we convert it to a tuple
        # If any parameters are abstract base classes--we convert them to the corresponding models

        if types is not None:

            if not isinstance(types, collections_abc.Sequence):
                types = (types,)

        if value_types is not None:

            if not isinstance(value_types, collections_abc.Sequence):
                value_types = (value_types,)

        if item_types is not None:

            if not isinstance(item_types, collections_abc.Sequence):
                item_types = (item_types,)

        # Member data

        self.data = data  # type: Any
        self.types = types  # type: Optional[Sequence[Union[type, properties.Property]]]
        self.value_types = value_types   # type: Optional[Sequence[Union[type, properties.Property]]]
        self.item_types = item_types   # type: Optional[Sequence[Union[type, properties.Property]]]
        self.meta = None  # type: Optional[meta.Meta]

    def __call__(self):
        # type: (...) -> Any
        """
        Return `self.data` unmarshalled
        """

        unmarshalled_data = self.data

        if (
            (self.data is not None) and
            (self.data is not properties.NULL)
        ):
            # If the data is a serial `Model`, get it's metadata
            if isinstance(self.data, abc.model.Model):

                self.meta = meta.read(self.data)

            if self.meta is None:  # Only un-marshall models if they have no metadata yet (are generic)

                # If `types` is a function, it should be one which expects to receive marshalled data and returns a list
                # of types which are applicable
                if callable(self.types):
                    self.types = self.types(self.data)

                # If the data provided is a `Generator`, make it static by casting the data into a tuple
                if isinstance(self.data, Generator):
                    self.data = tuple(self.data)

                if self.types is None:

                    # If no types are provided, we unmarshal the data into one of serial's generic container types
                    unmarshalled_data = self.as_container_or_simple_type

                else:

                    self.backport_types()

                    unmarshalled_data = None
                    successfully_unmarshalled = False

                    first_error = None  # type: Optional[Exception]

                    # Attempt to un-marshal the data as each type, in the order provided
                    for type_ in self.types:

                        error = None  # type: Optional[Union[AttributeError, KeyError, TypeError, ValueError]]

                        try:

                            unmarshalled_data = self.as_type(type_)

                            # if (self.data is not None) and (unmarshalled_data is None):
                            #     raise RuntimeError(self.data)

                            # If the data is un-marshalled successfully, we do not need to try any further types
                            successfully_unmarshalled = True
                            break

                        except (AttributeError, KeyError, TypeError, ValueError) as e:

                            error = e

                        if (first_error is None) and (error is not None):
                            first_error = error

                    if not successfully_unmarshalled:

                        if (first_error is None) or isinstance(first_error, TypeError):

                            raise errors.UnmarshalTypeError(
                                self.data,
                                types=self.types,
                                value_types=self.value_types,
                                item_types=self.item_types
                            )

                        elif isinstance(first_error, ValueError):

                            raise errors.UnmarshalValueError(
                                self.data,
                                types=self.types,
                                value_types=self.value_types,
                                item_types=self.item_types
                            )

                        else:

                            raise first_error  # noqa - pylint erroneously identifies this as raising `None`

        return unmarshalled_data

    @property
    def as_container_or_simple_type(self):
        # type: (...) -> Any

        """
        This function unmarshalls and returns the data into one of serial's container types, or if the data is of a
        simple data type--it returns that data unmodified
        """

        unmarshalled_data = self.data

        if isinstance(self.data, abc.model.Dictionary):

            type_ = type(self.data())

            if self.value_types is not None:
                unmarshalled_data = type_(self.data, value_types=self.value_types)

        elif isinstance(self.data, abc.model.Array):

            if self.item_types is not None:
                unmarshalled_data = serial.model.Array(self.data, item_types=self.item_types)

        elif isinstance(self.data, (dict, collections.OrderedDict)):

            unmarshalled_data = serial.model.Dictionary(self.data, value_types=self.value_types)

        elif (
            isinstance(self.data, (collections_abc.Set, collections_abc.Sequence))
        ) and (
            not isinstance(self.data, (str, bytes, native_str))
        ):

            unmarshalled_data = serial.model.Array(self.data, item_types=self.item_types)

        elif not isinstance(self.data, (str, bytes, native_str, Number, Decimal, date, datetime, bool, abc.model.Model)):

            raise errors.UnmarshalValueError(
                '%s cannot be un-marshalled' % repr(self.data)
            )

        return unmarshalled_data

    def backport_types(self):
        # type: (...) -> None
        """
        This examines a set of types passed to `unmarshal`, and resolves any compatibility issues with the python
        version being utilized
        """

        if (str in self.types) and (native_str is not str) and (native_str not in self.types):

            self.types = tuple(chain(*(
                ((type_, native_str) if (type_ is str) else (type_,))
                for type_ in self.types
            )))  # type: Tuple[Union[type, properties.Property], ...]

    def as_type(
        self,
        type_,  # type: Union[type, properties.Property]
    ):
        # type: (...) -> bool

        unmarshalled_data = None  # type: Union[abc.model.Model, Number, str, bytes, date, datetime]

        if isinstance(
            type_,
            properties.Property
        ):

            unmarshalled_data = type_.unmarshal(self.data)

        elif isinstance(type_, type):

            if isinstance(
                self.data,
                (dict, collections.OrderedDict, abc.model.Model)
            ):

                if issubclass(type_, abc.model.Object):

                    unmarshalled_data = type_(self.data)

                elif issubclass(
                    type_,
                    abc.model.Dictionary
                ):

                    unmarshalled_data = type_(self.data, value_types=self.value_types)

                elif issubclass(
                    type_,
                    (dict, collections.OrderedDict)
                ):

                    unmarshalled_data = serial.model.Dictionary(self.data, value_types=self.value_types)

                else:

                    raise TypeError(self.data)

            elif (
                isinstance(self.data, (collections_abc.Set, collections_abc.Sequence, abc.model.Array)) and
                (not isinstance(self.data, (str, bytes, native_str)))
            ):

                if issubclass(type_, abc.model.Array):

                    unmarshalled_data = type_(self.data, item_types=self.item_types)

                elif issubclass(
                    type_,
                    (collections_abc.Set, collections_abc.Sequence)
                ) and not issubclass(
                    type_,
                    (str, bytes, native_str)
                ):

                    unmarshalled_data = serial.model.Array(self.data, item_types=self.item_types)

                else:

                    raise TypeError('%s is not of type `%s`' % (repr(self.data), repr(type_)))

            elif isinstance(self.data, type_):

                if isinstance(self.data, Decimal):
                    unmarshalled_data = float(self.data)
                else:
                    unmarshalled_data = self.data

            else:

                raise TypeError(self.data)

        return unmarshalled_data


def unmarshal(
    data,  # type: Any
    types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    value_types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    item_types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
):
    # type: (...) -> Optional[Union[abc.model., str, Number, date, datetime]]
    """
    Converts `data` into an instance of a serial model, and recursively does the same for all member data.

    Parameters:

     - data ([type|serial.properties.Property]): One or more data types. Each type

    This is done by attempting to cast that data into a series of `types`.

    to "un-marshal" data which has been deserialized from bytes or text, but is still represented
    by generic containers
    """

    unmarshalled_data = _Unmarshal(
        data,
        types=types,
        value_types=value_types,
        item_types=item_types
    )()

    return unmarshalled_data


def serialize(data, format_='json'):
    # type: (Union[abc.model.Model, str, Number], Optional[str]) -> str
    """
    Serializes instances of `serial.model.Object` as JSON or YAML.
    """
    instance_hooks = None

    if isinstance(data, abc.model.Model):

        instance_hooks = hooks.read(data)

        if (instance_hooks is not None) and (instance_hooks.before_serialize is not None):
            data = instance_hooks.before_serialize(data)

    if format_ not in ('json', 'yaml'):  # , 'xml'

        format_ = format_.lower()

        if format_ not in ('json', 'yaml'):

            raise ValueError(
                'Supported `serial.model.serialize()` `format_` values include "json" and "yaml" (not "%s").' %
                format_
            )

    if format_ == 'json':
        data = json.dumps(marshal(data))
    elif format_ == 'yaml':
        data = yaml.dump(marshal(data))

    if (instance_hooks is not None) and (instance_hooks.after_serialize is not None):
        data = instance_hooks.after_serialize(data)

    if not isinstance(data, str):
        if isinstance(data, native_str):
            data = str(data)

    return data


def deserialize(data, format_):
    # type: (Optional[Union[str, IOBase, addbase]], str) -> Any
    """
    Parameters:

        - data (str|io.IOBase|io.addbase):

          This can be a string or file-like object containing JSON, YAML, or XML serialized inforation.

        - format_ (str):

          This can be "json", "yaml" or "xml".

    Returns:

        A deserialized representation of the information you provided.
    """
    if format_ not in ('json', 'yaml'):  # , 'xml'
        raise NotImplementedError(
            'Deserialization of data in the format %s is not currently supported.' % repr(format_)
        )
    if not isinstance(data, (str, bytes)):
        data = read(data)
    if isinstance(data, bytes):
        data = str(data, encoding='utf-8')
    if isinstance(data, str):
        if format_ == 'json':
            data = json.loads(
                data,
                object_hook=collections.OrderedDict,
                object_pairs_hook=collections.OrderedDict
            )
        elif format_ == 'yaml':
            data = yaml.load(data)
    return data


def detect_format(data):
    # type: (Optional[Union[str, IOBase, addbase]]) -> Tuple[Any, str]
    """
    Parameters:

        - data (str|io.IOBase|io.addbase):

          This can be a string or file-like object containing JSON, YAML, or XML serialized inforation.

    Returns:

        A tuple containing the deserialized information and a string indicating the format of that information.
    """
    if not isinstance(data, str):
        try:
            data = utilities.read(data)
        except TypeError:
            return data, None
    formats = ('json', 'yaml')  # , 'xml'
    format_ = None
    for potential_format in formats:
        try:
            data = deserialize(data, potential_format)
            format_ = potential_format
            break
        except (ValueError, yaml.YAMLError):
            pass
    if format is None:
        raise ValueError(
            'The data provided could not be parsed:\n' + repr(data)
        )
    return data, format_


def validate(
    data,  # type: Optional[abc.model.Model]
    types=None,  # type: Optional[Union[type, properties.Property, model.Object, Callable]]
    raise_errors=True  # type: bool
):
    # type: (...) -> Sequence[str]
    """
    This function verifies that all properties/items/values in an instance of `serial.abc.model.Model` are of the
    correct data type(s), and that all required attributes are present (if applicable). If `raise_errors` is `True`
    (this is the default)--violations will result in a validation error. If `raise_errors` is `False`--a list of error
    messages will be returned if invalid/missing information is found, or an empty list otherwise.
    """

    if isinstance(data, Generator):
        data = tuple(data)

    error_messages = []

    error_message = None

    if types is not None:

        if callable(types):
            types = types(data)

        if (str in types) and (native_str is not str) and (native_str not in types):

            types = tuple(chain(*(
                ((type_, native_str) if (type_ is str) else (type_,))
                for type_ in types
            )))

        valid = False

        for type_ in types:

            if isinstance(type_, type) and isinstance(data, type_):

                valid = True
                break

            elif isinstance(type_, properties.Property):

                if type_.types is None:

                    valid = True
                    break

                try:

                    validate(data, type_.types, raise_errors=True)
                    valid = True
                    break

                except errors.ValidationError:

                    pass

        if not valid:

            error_message = (
                'Invalid data:\n\n%s\n\nThe data must be one of the following types:\n\n%s' % (
                    '\n'.join(
                        '  ' + line
                        for line in repr(data).split('\n')
                    ),
                    '\n'.join(chain(
                        ('  (',),
                        (
                            '    %s,' % '\n'.join(
                                '    ' + line
                                for line in repr(type_).split('\n')
                            ).strip()
                            for type_ in types
                        ),
                        ('  )',)
                    ))
                )
            )

    if error_message is not None:

        if (not error_messages) or (error_message not in error_messages):

            error_messages.append(error_message)

    if ('_validate' in dir(data)) and callable(data._validate):

        error_messages.extend(
            error_message for error_message in
            data._validate(raise_errors=False)
            if error_message not in error_messages
        )

    if raise_errors and error_messages:
        raise errors.ValidationError('\n' + '\n\n'.join(error_messages))

    return error_messages
