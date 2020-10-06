# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from .utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

import numbers  # noqa

from base64 import b64decode, b64encode  # noqa
from copy import deepcopy  # noqa
from datetime import date, datetime  # noqa

try:
    from typing import Union, Optional, Sequence, Mapping, Set, Sequence, Callable, Dict, Any, Hashable, Collection,\
        Tuple
except ImportError:
    Union = Optional = Sequence = Mapping = Set = Sequence = Callable = Dict = Any = Hashable = Collection = Tuple =\
        Iterable = None

import iso8601  # noqa

from .utilities import collections, collections_abc, qualified_name, properties_values, parameters_defaults,\
    calling_function_qualified_name

from serial import abc, errors, meta
import serial


NoneType = type(None)


NULL = None


class Null(object):  # noqa - inheriting from object is intentional, as this is needed for python 2x compatibility
    """
    Instances of this class represent an *explicit* null value, rather than the absence of a
    property/attribute/element, as would be inferred from a value of `None`.
    """

    def __init__(self):
        if NULL is not None:
            raise errors.DefinitionExistsError(
                '%s may only be defined once.' % repr(self)
            )

    def __bool__(self):
        # type: (...) -> bool
        return False

    def __eq__(self, other):
        # type: (Any) -> bool
        return id(other) == id(self)

    def __hash__(self):
        # type: (...) -> int
        return 0

    def __str__(self):
        # type: (...) -> str
        return 'null'

    def _marshal(self):
        # type: (...) -> None
        return None

    def __repr__(self):
        # type: (...) -> str
        return (
            'NULL'
            if self.__module__ in ('__main__', 'builtins', '__builtin__') else
            '%s.NULL' % self.__module__
        )

    def __copy__(self):
        # type: (...) -> Null
        return self

    def __deepcopy__(self, memo):
        # type: (Dict[Hashable, Any]) -> Null
        return self


NULL = Null()


def _validate_type_or_property(type_or_property):
    # type: (Union[type, Property]) -> (Union[type, Property])

    if not isinstance(type_or_property, (type, Property)):
        raise TypeError(type_or_property)

    if not (
        (type_or_property is Null) or
        (
            isinstance(type_or_property, type) and
            issubclass(
                type_or_property,
                (
                        abc.model.Model,
                        str,
                        native_str,
                        bytes,
                        numbers.Number,
                        date,
                        datetime,
                        Null,
                        collections_abc.Iterable,
                        dict,
                        collections.OrderedDict,
                        bool
                )
            )
        ) or
        isinstance(type_or_property, Property)
    ):
        raise TypeError(type_or_property)

    return type_or_property


class Types(list):
    """
    Instances of this class are lists which will only take values which are valid types for describing a property
    definition.
    """

    def __init__(
        self,
        property_,  # type: Property
        items=None  # type: Optional[Union[Sequence[Union[type, Property], Types], type, Property]]
    ):
        # (...) -> None
        if not isinstance(property_, Property):
            raise TypeError(
                'The parameter `property` must be a `type`, or an instance of `%s`.' % qualified_name(Property)
            )

        self.property_ = property_

        if isinstance(items, (type, Property)):
            items = (items,)

        if items is None:
            super().__init__()
        else:
            super().__init__(items)

    def __setitem__(self, index, value):
        # type: (int, Union[type, Property]) -> None
        super().__setitem__(index, _validate_type_or_property(value))
        if value is str and (native_str is not str) and (native_str not in self):
            super().append(native_str)

    def append(self, value):
        # type: (Union[type, Property]) -> None
        super().append(_validate_type_or_property(value))
        if value is str and (native_str is not str) and (native_str not in self):
            super().append(native_str)

    def __delitem__(self, index):
        # type: (int) -> None
        value = self[index]
        super().__delitem__(index)
        if (value is str) and (native_str in self):
            self.remove(native_str)

    def pop(self, index=-1):
        # type: (int) -> Union[type, Property]
        value = super().pop(index)
        if (value is str) and (native_str in self):
            self.remove(native_str)
        return value

    def __copy__(self):
        # type: () -> Types
        return self.__class__(self.property_, self)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Types
        return self.__class__(
            self.property_,
            tuple(
                deepcopy(v, memo=memo)
                for v in self
            )
        )

    def __repr__(self):

        representation = [
            qualified_name(type(self)) + '('
        ]

        if self:

            representation[0] += '['

            for v in self:

                rv = (
                    qualified_name(v) if isinstance(v, type) else
                    repr(v)
                )
                rvls = rv.split('\n')

                if len(rvls) > 1:

                    rvs = [rvls[0]]

                    for rvl in rvls[1:]:
                        rvs.append('    ' + rvl)

                    rv = '\n'.join(rvs)
                    representation += [
                        '    %s' % rv,
                    ]

                else:

                    representation.append(
                        '    %s,' % rv
                    )

            representation[-1] = representation[-1][:-1]
            representation.append(
                ']'
            )

        representation[-1] += ')'

        return '\n'.join(representation) if len(representation) > 2 else ''.join(representation)


class Property(object):
    """
    This is the base class for defining a property.

    Properties

        - value_types ([type|Property]): One or more expected value_types or `Property` instances. Values are checked,
          sequentially, against each type or `Property` instance, and the first appropriate match is used.

        - required (bool|collections.Callable): If `True`--dumping the json_object will throw an error if this value
          is `None`.

        - versions ([str]|{str:Property}): The property should be one of the following:

            - A set/tuple/list of version numbers to which this property applies.
            - A mapping of version numbers to an instance of `Property` applicable to that version.

          Version numbers prefixed by "<" indicate any version less than the one specified, so "<3.0" indicates that
          this property is available in versions prior to 3.0. The inverse is true for version numbers prefixed by ">".
          ">=" and "<=" have similar meanings, but are inclusive.

          Versioning can be applied to an json_object by calling `serial.meta.set_version` in the `__init__` method of
          an `serial.model.Object` sub-class. For an example, see `oapi.model.OpenAPI.__init__`.

        - name (str): The name of the property when loaded from or dumped into a JSON/YAML/XML json_object. Specifying a
          `name` facilitates mapping of PEP8 compliant property to JSON or YAML attribute names, or XML element names,
          which are either camelCased, are python keywords, or otherwise not appropriate for usage in python code.

    """

    def __init__(
        self,
        types=None,  # type: Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Sequence[Union[str, meta.Version]]]
    ):
        self._types = None  # type: Optional[Sequence[Union[type, Property]]]
        self.types = types
        self.name = name
        self.required = required
        self._versions = None  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]

    @property
    def types(self):
        return self._types

    @types.setter
    def types(self, types_or_properties):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Model]]]) -> None

        if types_or_properties is not None:

            if callable(types_or_properties):

                if native_str is not str:

                    _types_or_properties = types_or_properties

                    def types_or_properties(d):
                        # type: (Sequence[Union[type, Property, abc.model.Model]]) -> Types
                        return Types(self, _types_or_properties(d))

            else:

                types_or_properties = Types(self, types_or_properties)

        self._types = types_or_properties

    @property
    def versions(self):
        # type: () -> Optional[Sequence[meta.Version]]
        return self._versions

    @versions.setter
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, collections_abc.Iterable, meta.Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        if versions is not None:

            if isinstance(versions, (str, Number, meta.Version)):
                versions = (versions,)

            if isinstance(versions, collections_abc.Iterable):
                versions = tuple(
                    (v if isinstance(v, meta.Version) else meta.Version(v))
                    for v in versions
                )

            else:

                repr_versions = repr(versions)

                raise TypeError(
                    (
                        '`%s` requires a sequence of version strings or ' %
                        calling_function_qualified_name()
                    ) + (
                        '`%s` instances, not' % qualified_name(meta.Version)
                    ) + (
                        ':\n' + repr_versions
                        if '\n' in repr_versions else
                        ' `%s`.' % repr_versions
                    )
                )

        self._versions = versions

    def unmarshal(self, data):
        # type: (Any) -> Any
        # return data if self.types is None else unmarshal(data, types=self.types)

        if isinstance(
            data,
            collections_abc.Iterable
        ) and not isinstance(
            data,
            (str, bytes, bytearray, native_str)
        ) and not isinstance(
            data,
            abc.model.Model
        ):

            if isinstance(data, (dict, collections.OrderedDict)):

                for k, v in data.items():
                    if v is None:
                        data[k] = NULL

            else:

                data = tuple((NULL if i is None else i) for i in data)

        return serial.marshal.unmarshal(data, types=self.types)

    def marshal(self, data):
        # type: (Any) -> Any
        return serial.marshal.marshal(data, types=self.types)  #, types=self.types, value_types=self.value_types)

    def __repr__(self):
        representation = [qualified_name(type(self)) + '(']
        pd = parameters_defaults(self.__init__)
        for p, v in properties_values(self):
            if (p not in pd) or pd[p] == v:
                continue
            if (v is not None) and (v is not NULL):
                if isinstance(v, collections_abc.Sequence) and not isinstance(v, (str, bytes)):
                    rvs = ['(']
                    for i in v:
                        ri = (
                            qualified_name(i)
                            if isinstance(i, type) else
                            "'%s'" % str(i)
                            if isinstance(i, meta.Version) else
                            repr(i)
                        )
                        rils = ri.split('\n')
                        if len(rils) > 1:
                            ris = [rils[0]]
                            for ril in rils[1:]:
                                ris.append('        ' + ril)
                            ri = '\n'.join(ris)
                        rvs.append('        %s,' % ri)
                    if len(v) > 1:
                        rvs[-1] = rvs[-1][:-1]
                    rvs.append('    )')
                    rv = '\n'.join(rvs)
                else:
                    rv = (
                        qualified_name(v)
                        if isinstance(v, type) else
                        "'%s'" % str(v)
                        if isinstance(v, meta.Version) else
                        repr(v)
                    )
                    rvls = rv.split('\n')
                    if len(rvls) > 2:
                        rvs = [rvls[0]]
                        for rvl in rvls[1:]:
                            rvs.append('    ' + rvl)
                        rv = '\n'.join(rvs)
                representation.append(
                    '    %s=%s,' % (p, rv)
                )
        representation.append(')')
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)

    def __copy__(self):

        new_instance = self.__class__()

        for a in dir(self):

            if a[0] != '_' and a != 'data':

                v = getattr(self, a)

                if not callable(v):
                    setattr(new_instance, a, v)

        return new_instance

    def __deepcopy__(self, memo):
        # type: (dict) -> Property

        new_instance = self.__class__()

        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo))

        return new_instance


abc.properties.Property.register(Property)


class String(Property):
    """
    See `serial.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(str,),
            name=name,
            required=required,
            versions=versions,
        )


class Date(Property):
    """
    See `serial.properties.Property`

    Additional Properties:

        - marshal (collections.Callable): A function, taking one argument (a python `date` json_object), and returning
          a date string in the desired format. The default is `date.isoformat`--returning an iso8601 compliant date
          string.

        - unmarshal (collections.Callable): A function, taking one argument (a date string), and returning a python
          `date` json_object. By default, this is `iso8601.parse_date`.
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
        date2str=date.isoformat,  # type: Optional[Callable]
        str2date=iso8601.parse_date  # type: Callable
    ):
        super().__init__(
            types=(date,),
            name=name,
            required=required,
            versions=versions,
        )
        self.date2str = date2str
        self.str2date = str2date

    def unmarshal(self, data):
        # type: (Optional[str]) -> Union[date, NoneType]
        if data is None:
            return data
        else:
            if isinstance(data, date):
                date_ = data
            elif isinstance(data, str):
                date_ = self.str2date(data)
            else:
                raise TypeError(
                    '%s is not a `str`.' % repr(data)
                )
            if isinstance(date_, date):
                return date_
            else:
                raise TypeError(
                    '"%s" is not a properly formatted date string.' % data
                )

    def marshal(self, data):
        # type: (Optional[date]) -> Optional[str]
        if data is None:
            return data
        else:
            ds = self.date2str(data)
            if not isinstance(ds, str):
                if isinstance(ds, native_str):
                    ds = str(ds)
                else:
                    raise TypeError(
                        'The date2str function should return a `str`, not a `%s`: %s' % (
                            type(ds).__name__,
                            repr(ds)
                        )
                    )
        return ds


class DateTime(Property):
    """
    See `serial.properties.Property`

    Additional Properties:

        - marshal (collections.Callable): A function, taking one argument (a python `datetime` json_object), and
          returning a date-time string in the desired format. The default is `datetime.isoformat`--returning an
          iso8601 compliant date-time string.

        - unmarshal (collections.Callable): A function, taking one argument (a datetime string), and returning a python
          `datetime` json_object. By default, this is `iso8601.parse_date`.
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
        datetime2str=datetime.isoformat,  # type: Optional[Callable]
        str2datetime=iso8601.parse_date  # type: Callable
    ):
        self.datetime2str = datetime2str
        self.str2datetime = str2datetime
        super().__init__(
            types=(datetime,),
            name=name,
            required=required,
            versions=versions,
        )

    def unmarshal(self, data):
        # type: (Optional[str]) -> Union[datetime, NoneType]
        if data is None:
            return data
        else:
            if isinstance(data, datetime):
                datetime_ = data
            elif isinstance(data, str):
                datetime_ = self.str2datetime(data)
            else:
                raise TypeError(
                    '%s is not a `str`.' % repr(data)
                )
            if isinstance(datetime_, datetime):
                return datetime_
            else:
                raise TypeError(
                    '"%s" is not a properly formatted date-time string.' % data
                )

    def marshal(self, data):
        # type: (Optional[datetime]) -> Optional[str]
        if data is None:
            return data
        else:
            datetime_string = self.datetime2str(data)
            if not isinstance(datetime_string, str):
                if isinstance(datetime_string, native_str):
                    datetime_string = str(datetime_string)
                else:
                    repr_datetime_string = repr(datetime_string).strip()
                    raise TypeError(
                        'The datetime2str function should return a `str`, not:' + (
                            '\n'
                            if '\n' in repr_datetime_string else
                            ' '
                        ) + repr_datetime_string
                    )
            return datetime_string


class Bytes(Property):
    """
    See `serial.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(bytes, bytearray),
            name=name,
            required=required,
            versions=versions,
        )

    def unmarshal(self, data):
        # type: (str) -> Optional[bytes]
        """
        Un-marshal a base-64 encoded string into bytes
        """
        if data is None:
            return data
        elif isinstance(data, str):
            return b64decode(data)
        elif isinstance(data, bytes):
            return data
        else:
            raise TypeError(
                '`data` must be a base64 encoded `str` or `bytes`--not `%s`' % qualified_name(type(data))
            )

    def marshal(self, data):
        # type: (bytes) -> str
        """
        Marshal bytes into a base-64 encoded string
        """
        if (data is None) or isinstance(data, str):
            return data
        elif isinstance(data, bytes):
            return str(b64encode(data), 'ascii')
        else:
            raise TypeError(
                '`data` must be a base64 encoded `str` or `bytes`--not `%s`' % qualified_name(type(data))
            )


class Enumerated(Property):
    """
    See `serial.properties.Property`...

    + Properties:

        - values ([Any]):  A list of possible values. If the parameter `types` is specified--typing is
          applied prior to validation.
    """

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[Union[type, Property]]]
        values=None,  # type: Optional[Union[Sequence, Set]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._values = None

        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions
        )

        self.values = values  # type: Optional[Sequence]

    @property
    def values(self):
        # type: () -> Optional[Union[Tuple, Callable]]
        return self._values

    @values.setter
    def values(self, values):
        # type: (Iterable) -> None

        if not ((values is None) or callable(values)):

            if (values is not None) and (not isinstance(values, (collections_abc.Sequence, collections_abc.Set))):
                raise TypeError(
                    '`values` must be a finite set or sequence, not `%s`.' % qualified_name(type(values))
                )

            if values is not None:
                values = [
                    serial.marshal.unmarshal(v, types=self.types)
                    for v in values
                ]

        self._values = values

    def unmarshal(self, data):
        # type: (Any) -> Any

        if self.types is not None:
            data = serial.marshal.unmarshal(data, types=self.types)

        if (
            (data is not None) and
            (self.values is not None) and
            (data not in self.values)
        ):
            raise ValueError(
                'The value provided is not a valid option:\n%s\n\n' % repr(data) +
                'Valid options include:\n%s' % (
                    ', '.join(repr(t) for t in self.values)
                )
            )
        return data


class Number(Property):
    """
    See `serial.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        # type: (...) -> None
        super().__init__(
            types=(numbers.Number,),
            name=name,
            required=required,
            versions=versions,
        )


class Integer(Property):
    """
    See `serial.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(int,),
            name=name,
            required=required,
            versions=versions,
        )

    # def unmarshal(self, data):
    #     # type: (Any) -> Any
    #     if data is None:
    #         return data
    #     else:
    #         return int(data)
    #
    # def marshal(self, data):
    #     # type: (Any) -> Any
    #     if data is None:
    #         return data
    #     else:
    #         return int(data)


class Boolean(Property):
    """
    See `serial.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        # type: (...) -> None
        super().__init__(
            types=(bool,),
            name=name,
            required=required,
            versions=versions,
        )


class Array(Property):
    """
    See `serial.properties.Property`...

    + Properties:

        - item_types (type|Property|[type|Property]): The type(s) of values/objects contained in the array. Similar to
          `serial.properties.Property().value_types`, but applied to items in the array, not the array itself.
    """

    def __init__(
        self,
        item_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._item_types = None
        self.item_types = item_types
        super().__init__(
            types=(serial.model.Array,),
            name=name,
            required=required,
            versions=versions,
        )

    def unmarshal(self, data):
        # type: (Any) -> Any
        return serial.marshal.unmarshal(data, types=self.types, item_types=self.item_types)

    def marshal(self, data):
        # type: (Any) -> Any
        return serial.marshal.marshal(data, types=self.types, item_types=self.item_types)

    @property
    def item_types(self):
        return self._item_types

    @item_types.setter
    def item_types(self, item_types):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Object]]]) -> None
        if item_types is not None:
            if callable(item_types):
                if native_str is not str:
                    _item_types = item_types

                    def item_types(d):
                        # type: (Sequence[Union[type, Property, abc.model.Object]]) -> Types
                        return Types(self, _item_types(d))
            else:
                item_types = Types(self, item_types)
        self._item_types = item_types


class Dictionary(Property):
    """
    See `serial.properties.Property`...

    + Properties:

        - value_types (type|Property|[type|Property]): The type(s) of values/objects comprising the mapped
          values. Similar to `serial.properties.Property.types`, but applies to *values* in the dictionary
          object, not the dictionary itself.
    """

    def __init__(
        self,
        value_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._value_types = None
        self.value_types = value_types
        super().__init__(
            types=(serial.model.Dictionary,),
            name=name,
            required=required,
            versions=versions,
        )

    def unmarshal(self, data):
        # type: (Any) -> Any
        return serial.marshal.unmarshal(data, types=self.types, value_types=self.value_types)

    @property
    def value_types(self):
        return self._value_types

    @value_types.setter
    def value_types(self, value_types_):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Object]]]) -> None
        """
        The `types` can be either:

            - A sequence of types and/or `serial.properties.Property` instances.

            - A function which accepts exactly one argument (a dictionary), and which returns a sequence of types and/or
              `serial.properties.Property` instances.

        If more than one type or property definition is provided, un-marshalling is attempted using each `value_type`,
        in sequential order. If a value could be cast into more than one of the `types` without throwing a
        `ValueError`, `TypeError`, or `serial.errors.ValidationError`, the value type occuring *first* in the sequence
        will be used.
        """

        if value_types_ is not None:

            if callable(value_types_):

                if native_str is not str:

                    original_value_types_ = value_types_

                    def value_types_(data):
                        # type: (Sequence[Union[type, Property, abc.model.Object]]) -> Types
                        return Types(self, original_value_types_(data))

            else:

                value_types_ = Types(self, value_types_)

        self._value_types = value_types_
