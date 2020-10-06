from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from .utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

import numbers
import operator
import re
import collections
from collections import OrderedDict
from copy import copy, deepcopy
from itertools import chain
from numbers import Number

try:
    from typing import Optional, Dict, Sequence, Tuple, Mapping, Union, Any, List
except ImportError:
    Optional = Sequence = Dict = Tuple = Mapping = Union = Any = List = None

import serial
from serial.utilities import qualified_name, properties_values, collections_abc
from serial.abc.model import Model
from serial.abc.properties import Property

_DOT_SYNTAX_RE = re.compile(
    r'^\d+(\.\d+)*$'
)


class Meta(object):

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (Optional[dict]) -> Meta
        new_instance = self.__class__()
        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance

    def __bool__(self):
        return True

    def __repr__(self):
        return ('\n'.join(
            ['%s(' % qualified_name(type(self))] +
            [
                '    %s=%s,' % (p, repr(v))
                for p, v in properties_values(self)
            ] +
            [')']
        ))


class Version(Meta):

    def __init__(
        self,
        version_number=None,  # type: Optional[str]
        specification=None,  # type: Optional[Sequence[str]]
        equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        not_equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
    ):
        if isinstance(version_number, str) and (
            (specification is None) and
            (equals is None) and
            (not_equals is None) and
            (less_than is None) and
            (less_than_or_equal_to is None) and
            (greater_than is None) and
            (greater_than_or_equal_to is None)
        ):
            specification = None
            for s in version_number.split('&'):
                if '==' in s:
                    s, equals = s.split('==')
                elif '<=' in s:
                    s, less_than_or_equal_to = s.split('<=')
                elif '>=' in s:
                    s, greater_than_or_equal_to = s.split('>=')
                elif '<' in s:
                    s, less_than = s.split('<')
                elif '>' in s:
                    s, greater_than = s.split('>')
                elif '!=' in s:
                    s, not_equals = s.split('!=')
                elif '=' in s:
                    s, equals = s.split('=')
                if specification:
                    if s != specification:
                        raise ValueError(
                            'Multiple specifications cannot be associated with an instance of ' +
                            '`serial.meta.Version`: ' + repr(version_number)
                        )
                elif s:
                    specification = s
            self.specification = specification
        self.equals = equals
        self.not_equals = not_equals
        self.less_than = less_than
        self.less_than_or_equal_to = less_than_or_equal_to
        self.greater_than = greater_than
        self.greater_than_or_equal_to = greater_than_or_equal_to

    def __eq__(self, other):
        # type: (Any) -> bool

        compare_properties_functions = (
            ('equals', operator.eq),
            ('not_equals', operator.ne),
            ('less_than', operator.lt),
            ('less_than_or_equal_to', operator.le),
            ('greater_than', operator.gt),
            ('greater_than_or_equal_to', operator.ge),
        )

        if (
            (isinstance(other, str) and _DOT_SYNTAX_RE.match(other)) or
            isinstance(other, (collections_abc.Sequence, int))
        ):
            if isinstance(other, (native_str, bytes, numbers.Number)):
                other = str(other)
            if isinstance(other, str):

                other = other.rstrip('.0')
                if other == '':
                    other_components = (0,)
                else:
                    other_components = tuple(int(other_component) for other_component in other.split('.'))
            else:
                other_components = tuple(other)
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if compare_value is not None:
                    compare_values = tuple(int(n) for n in compare_value.split('.'))
                    other_values = copy(other_components)
                    ld = len(other_values) - len(compare_values)
                    if ld < 0:
                        other_values = tuple(chain(other_values, [0] * (-ld)))
                    elif ld > 0:
                        compare_values = tuple(chain(compare_values, [0] * ld))
                    if not compare_function(other_values, compare_values):
                        return False
        else:
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if (compare_value is not None) and not compare_function(other, compare_value):
                    return False
        return True

    def __str__(self):
        representation = []
        for property, operator in (
            ('equals', '=='),
            ('not_equals', '!='),
            ('greater_than', '>'),
            ('greater_than_or_equal_to', '>='),
            ('less_than', '<'),
            ('less_than_or_equal_to', '<='),
        ):
            v = getattr(self, property)
            if v is not None:
                representation.append(
                    self.specification + operator + v
                )
        return '&'.join(representation)


class Object(Meta):

    def __init__(
        self,
        properties=None,  # type: Optional[Properties]
    ):
        self._properties = None  # type: Optional[Properties]
        self.properties = properties

    @property
    def properties(self):
        # type: () -> Optional[Properties]
        return self._properties

    @properties.setter
    def properties(
        self,
        properties_
        # type: Optional[Union[Dict[str, Property], Sequence[Tuple[str, Property]]]]
    ):
        # type: (...) -> None
        self._properties = Properties(properties_)


class Dictionary(Meta):

    def __init__(
        self,
        value_types=None,  # type: Optional[Sequence[Property, type]]
    ):
        self._value_types = None  # type: Optional[Tuple]
        self.value_types = value_types

    @property
    def value_types(self):
        # type: () -> Optional[Dict[str, Union[type, Property, serial.model.Object]]]
        return self._value_types

    @value_types.setter
    def value_types(self, value_types):
        # type: (Optional[Sequence[Union[type, Property, serial.model.Object]]]) -> None

        if value_types is not None:

            if isinstance(value_types, (type, Property)):
                value_types = (value_types,)

            if native_str is not str:

                if isinstance(value_types, collections.Callable):

                    _types = value_types

                    def value_types(d):
                        # type: (Any) -> Any

                        ts = _types(d)

                        if (ts is not None) and (str in ts) and (native_str not in ts):
                            ts = tuple(chain(*(
                                ((t, native_str) if (t is str) else (t,))
                                for t in ts
                            )))

                        return ts

                elif (str in value_types) and (native_str is not str) and (native_str not in value_types):

                    value_types = chain(*(
                        ((t, native_str) if (t is str) else (t,))
                        for t in value_types
                    ))

            if not isinstance(value_types, collections_abc.Callable):
                value_types = tuple(value_types)

        self._value_types = value_types


class Array(Meta):

    def __init__(
        self,
        item_types=None,  # type: Optional[Sequence[Property, type]]
    ):
        self._item_types = None  # type: Optional[Tuple]
        self.item_types = item_types

    @property
    def item_types(self):
        return self._item_types

    @item_types.setter
    def item_types(self, item_types):
        # type: (Optional[Sequence[Union[type, Property, serial.model.Object]]]) -> None
        if item_types is not None:
            if isinstance(item_types, (type, Property)):
                item_types = (item_types,)
            if native_str is not str:
                if isinstance(item_types, collections.Callable):
                    _types = item_types

                    def item_types(d):
                        # type: (Any) -> Any
                        ts = _types(d)
                        if (ts is not None) and (str in ts) and (native_str not in ts):
                            ts = tuple(chain(*(
                                ((t, native_str) if (t is str) else (t,))
                                for t in ts
                            )))
                        return ts
                elif (str in item_types) and (native_str is not str) and (native_str not in item_types):
                    item_types = chain(*(
                        ((t, native_str) if (t is str) else (t,))
                        for t in item_types
                    ))
            if not callable(item_types):
                item_types = tuple(item_types)
        self._item_types = item_types


class Properties(OrderedDict):

    def __init__(
        self,
        items=(
            None
        )  # type: Optional[Union[Dict[str, Property], List[Tuple[str, Property]]]]
    ):
        if items is None:
            super().__init__()
        else:
            if isinstance(items, OrderedDict):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(items.items())
            super().__init__(items)

    def __setitem__(self, key, value):
        # type: (str, Property) -> None
        if not isinstance(value, Property):
            raise ValueError(value)
        super().__setitem__(key, value)

    def __copy__(self):
        # type: () -> Properties
        return self.__class__(self)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Properties
        return self.__class__(
            tuple(
                (k, deepcopy(v, memo=memo))
                for k, v in self.items()
            )
        )

    def __repr__(self):
        representation = [
            qualified_name(type(self)) + '('
        ]
        items = tuple(self.items())
        if len(items) > 0:
            representation[0] += '['
            for k, v in items:
                rv = (
                    qualified_name(v) if isinstance(v, type) else
                    repr(v)
                )
                rvls = rv.split('\n')
                if len(rvls) > 1:
                    rvs = [rvls[0]]
                    for rvl in rvls[1:]:
                        rvs.append('        ' + rvl)
                    rv = '\n'.join(rvs)
                    representation += [
                        '    (',
                        '        %s,' % repr(k),
                        '        %s' % rv,
                        '    ),'
                    ]
                else:
                    representation.append(
                        '    (%s, %s),' % (repr(k), rv)
                    )
            representation[-1] = representation[-1][:-1]
            representation.append(
                ']'
            )
        representation[-1] += ')'
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)


def read(
    model  # type: Union[type, serial.abc.model.Model]
):
    # type: (...) -> Optional[Meta]

    if isinstance(
        model,
        Model
    ):

        return model._meta or read(type(model))

    elif isinstance(model, type) and issubclass(model, Model):

        return model._meta

    else:

        try:

            repr_model = repr(model)

        except:

            repr_model = object.__repr__(model)

        raise TypeError(
            '%s requires a parameter which is an instance or sub-class of `%s`, not%s' % (
                serial.utilities.calling_function_qualified_name(),
                qualified_name(Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )


def writable(
    model  # type: Union[type, serial.abc.model.Model]
):
    # type: (...) -> Optional[Meta]
    if isinstance(model, Model):
        if model._meta is None:
            model._meta = deepcopy(writable(type(model)))
    elif isinstance(model, type) and issubclass(model, Model):
        if model._meta is None:
            model._meta = (
                Object()
                if issubclass(model, serial.model.Object) else
                Array()
                if issubclass(model, serial.model.Array) else
                Dictionary()
                if issubclass(model, serial.model.Dictionary)
                else None
            )
        else:
            for b in model.__bases__:
                if hasattr(b, '_meta') and (model._meta is b._meta):
                    model._meta = deepcopy(model._meta)
                    break
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a parameter which is an instance or sub-class of `%s`, not%s' % (
                serial.utilities.calling_function_qualified_name(),
                qualified_name(Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )
    return model._meta


def write(
    model,  # type: Union[type, serial.model.Object]
    meta  # type: Meta
):
    # type: (...) -> None
    if isinstance(model, Model):
        model_type = type(model)
    elif isinstance(model, type) and issubclass(model, Model):
        model_type = model
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a value for the parameter `model` which is an instance or sub-class of `%s`, not%s' % (
                serial.utilities.calling_function_qualified_name(),
                qualified_name(Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )
    metadata_type = (
        Object
        if issubclass(model_type, serial.model.Object) else
        Array
        if issubclass(model_type, serial.model.Array) else
        Dictionary
        if issubclass(model_type, serial.model.Dictionary)
        else None
    )
    if not isinstance(meta, metadata_type):
        raise ValueError(
            'Metadata assigned to `%s` must be of type `%s`' % (
                qualified_name(model_type),
                qualified_name(metadata_type)
            )
        )
    model._meta = meta


_UNIDENTIFIED = None


def xpath(model, xpath_=_UNIDENTIFIED):
    # type: (serial.abc.model.Model, Optional[str]) -> Optional[str]
    """
    Return the xpath at which the element represented by this object was found, relative to the root document. If
    the parameter `xpath_` is provided--set the value
    """

    if not isinstance(model, Model):

        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(Model), repr(model))
        )

    if xpath_ is not _UNIDENTIFIED:

        if not isinstance(xpath_, str):

            if isinstance(xpath_, native_str):
                xpath_ = str(xpath_)
            else:
                raise TypeError(
                    '`xpath_` must be a `str`, not %s.' % repr(xpath_)
                )

        model._xpath = xpath_

        if isinstance(model, serial.model.Dictionary):
            for k, v in model.items():
                if isinstance(v, Model):
                    xpath(v, '%s/%s' % (xpath_, k))
        elif isinstance(model, serial.model.Object):
            for pn, p in read(model).properties.items():
                k = p.name or pn
                v = getattr(model, pn)
                if isinstance(v, Model):
                    xpath(v, '%s/%s' % (xpath_, k))
        elif isinstance(model, serial.model.Array):
            for i in range(len(model)):
                v = model[i]
                if isinstance(v, Model):
                    xpath(v, '%s[%s]' % (xpath_, str(i)))
    return model._xpath


def pointer(model, pointer_=_UNIDENTIFIED):
    # type: (serial.abc.model.Model, Optional[str]) -> Optional[str]

    if not isinstance(model, Model):
        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(Model), repr(model))
        )

    if pointer_ is not _UNIDENTIFIED:

        if not isinstance(pointer_, (str, native_str)):
            raise TypeError(
                '`pointer_` must be a `str`, not %s (of type `%s`).' % (repr(pointer_), type(pointer_).__name__)
            )

        model._pointer = pointer_

        if isinstance(model, serial.model.Dictionary):

            for k, v in model.items():
                if isinstance(v, Model):
                    pointer(v, '%s/%s' % (pointer_, k.replace('~', '~0').replace('/', '~1')))

        elif isinstance(model, serial.model.Object):

            for pn, property in read(model).properties.items():

                k = property.name or pn
                v = getattr(model, pn)

                if isinstance(v, Model):
                    pointer(v, '%s/%s' % (pointer_, k.replace('~', '~0').replace('/', '~1')))

        elif isinstance(model, serial.model.Array):

            for i in range(len(model)):

                v = model[i]

                if isinstance(v, Model):
                    pointer(v, '%s[%s]' % (pointer_, str(i)))

    return model._pointer


def url(model, url_=_UNIDENTIFIED):
    # type: (serial.abc.model.Model, Optional[str]) -> Optional[str]
    if not isinstance(model, serial.abc.model.Model):
        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(Model), repr(model))
        )
    if url_ is not _UNIDENTIFIED:
        if not isinstance(url_, str):
            raise TypeError(
                '`url_` must be a `str`, not %s.' % repr(url_)
            )
        model._url = url_
        if isinstance(model, serial.model.Dictionary):
            for v in model.values():
                if isinstance(v, Model):
                    url(v, url_)
        elif isinstance(model, serial.model.Object):
            for pn in read(model).properties.keys():
                v = getattr(model, pn)
                if isinstance(v, Model):
                    url(v, url_)
        elif isinstance(model, serial.model.Array):
            for v in model:
                if isinstance(v, Model):
                    url(v, url_)
    return model._url


def format_(model, serialization_format=_UNIDENTIFIED):

    # type: (serial.abc.model.Model, Optional[str]) -> Optional[str]
    if not isinstance(model, Model):

        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(Model), repr(model))
        )

    if serialization_format is not _UNIDENTIFIED:

        if not isinstance(serialization_format, str):

            if isinstance(serialization_format, native_str):
                serialization_format = str(serialization_format)
            else:
                raise TypeError(
                    '`serialization_format` must be a `str`, not %s.' % repr(serialization_format)
                )

        model._format = serialization_format

        if isinstance(model, serial.model.Dictionary):
            for v in model.values():
                if isinstance(v, Model):
                    format_(v, serialization_format)
        elif isinstance(model, serial.model.Object):
            for pn in read(model).properties.keys():
                v = getattr(model, pn)
                if isinstance(v, Model):
                    format_(v, serialization_format)
        elif isinstance(model, serial.model.Array):
            for v in model:
                if isinstance(v, Model):
                    format_(v, serialization_format)

    return model._format


def version(data, specification, version_number):
    # type: (serial.abc.model.Model, str, Union[str, int, Sequence[int]]) -> None
    """
    Recursively alters model class or instance metadata based on version number metadata associated with an
    object's properties. This allows one data model to represent multiple versions of a specification and dynamically
    change based on the version of a specification represented.

    Arguments:

        - data (serial.abc.model.Model)

        - specification (str):

            The specification to which the `version_number` argument applies.

        - version_number (str|int|[int]):

            A version number represented as text (in the form of integers separated by periods), an integer, or a
            sequence of integers.
    """
    if not isinstance(data, serial.abc.model.Model):
        raise TypeError(
            'The data provided is not an instance of serial.abc.model.Model: ' + repr(data)
        )

    def version_match(property_):
        # type: (serial.properties.Property) -> bool
        if property_.versions is not None:
            version_matched = False
            specification_matched = False
            for applicable_version in property_.versions:
                if applicable_version.specification == specification:
                    specification_matched = True
                    if applicable_version == version_number:
                        version_matched = True
                        break
            if specification_matched and (not version_matched):
                return False
        return True

    def version_properties(properties_):
        # type: (Sequence[serial.properties.Property]) -> Optional[Sequence[Meta]]
        changed = False
        nps = []

        for property in properties_:

            if isinstance(property, serial.properties.Property):
                if version_match(property):
                    np = version_property(property)
                    if np is not property:
                        changed = True
                    nps.append(np)
                else:
                    changed = True
            else:
                nps.append(property)
        if changed:
            return tuple(nps)
        else:
            return None

    def version_property(property):
        # type: (serial.properties.Property) -> Meta
        changed = False
        if isinstance(property, serial.properties.Array) and (property.item_types is not None):
            item_types = version_properties(property.item_types)
            if item_types is not None:
                if not changed:
                    property = deepcopy(property)
                property.item_types = item_types
                changed = True
        elif isinstance(property, serial.properties.Dictionary) and (property.value_types is not None):
            value_types = version_properties(property.value_types)
            if value_types is not None:
                if not changed:
                    property = deepcopy(property)
                property.value_types = value_types
                changed = True
        if property.types is not None:
            types = version_properties(property.types)
            if types is not None:
                if not changed:
                    property = deepcopy(property)
                property.types = types
        return property

    instance_meta = read(data)
    class_meta = read(type(data))

    if isinstance(data, serial.abc.model.Object):

        for property_name in tuple(instance_meta.properties.keys()):

            property = instance_meta.properties[property_name]

            if version_match(property):
                np = version_property(property)
                if np is not property:
                    if instance_meta is class_meta:
                        instance_meta = writable(data)
                    instance_meta.properties[property_name] = np
            else:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                del instance_meta.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    raise serial.errors.VersionError(
                        '%s - the property `%s` is not applicable in %s version %s:\n%s' % (
                            qualified_name(type(data)),
                            property_name,
                            specification,
                            version_number,
                            str(data)
                        )
                    )

            value = getattr(data, property_name)

            if isinstance(value, serial.abc.model.Model):
                version(value, specification, version_number)

    elif isinstance(data, serial.abc.model.Dictionary):

        if instance_meta and instance_meta.value_types:

            new_value_types = version_properties(instance_meta.value_types)

            if new_value_types:

                if instance_meta is class_meta:
                    instance_meta = writable(data)

                instance_meta.value_types = new_value_types

        for value in data.values():
            if isinstance(value, serial.abc.model.Model):
                version(value, specification, version_number)

    elif isinstance(data, serial.abc.model.Array):

        if instance_meta and instance_meta.item_types:

            new_item_types = version_properties(instance_meta.item_types)

            if new_item_types:

                if instance_meta is class_meta:
                    instance_meta = writable(data)

                instance_meta.item_types = new_item_types

        for item in data:
            if isinstance(item, serial.abc.model.Model):
                version(item, specification, version_number)
