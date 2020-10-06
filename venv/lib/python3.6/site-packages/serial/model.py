"""
This module defines the building blocks of a `serial` based data model.
"""

# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from .utilities.compatibility import backport, BACKWARDS_COMPATIBILITY_IMPORTS

backport()  # noqa

from future.utils import native_str

# region Built-In Imports

import re
import sys

from urllib.parse import urljoin

from copy import deepcopy
from io import IOBase
from itertools import chain
from numbers import Number

# endregion

# region 3rd-Party Maintained Package Imports

# endregion

# region Serial Imports

from .utilities import qualified_name, collections, Generator
from . import properties, meta, errors, hooks, abc
from .marshal import marshal, unmarshal, serialize, detect_format, validate, UNMARSHALLABLE_TYPES


# endregion


# region Compatibility Conditionals

# The following detects the presence of the typing library, and utilizes typing classes if possible.
# All typing classes in this package are referenced in a backwards-compatible fashion, so if this library
# is not present, the package will still function.

try:
    from typing import Union, Dict, Any, AnyStr, IO, Sequence, Mapping, Callable, Tuple, Optional, Set  # noqa
except ImportError:
    Union = Dict = Any = AnyStr = IO = Sequence = Mapping = Callable = Tuple = Optional = Set = None

# endregion


class Object(object):

    _format = None  # type: Optional[str]
    _meta = None  # type: Optional[meta.Object]
    _hooks = None  # type: Optional[hooks.Object]

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
    ):

        self._meta = None  # type: Optional[meta.Object]
        self._hooks = None  # type: Optional[hooks.Object]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]

        url = None

        if _ is not None:

            if isinstance(_, Object):

                instance_meta = meta.read(_)

                if meta.read(self) is not instance_meta:
                    meta.write(self, deepcopy(instance_meta))

                instance_hooks = hooks.read(_)

                if hooks.read(self) is not instance_hooks:
                    hooks.write(self, deepcopy(instance_hooks))

                for property_name in instance_meta.properties.keys():

                    try:

                        setattr(self, property_name, getattr(_, property_name))

                    except TypeError as error:

                        label = '\n - %s.%s: ' % (qualified_name(type(self)), property_name)

                        if error.args:
                            error.args = tuple(
                                chain(
                                    (label + error.args[0],),
                                    error.args[1:]
                                )
                            )
                        else:
                            error.args = (label + serialize(_),)
                        raise error
            else:

                if isinstance(_, IOBase):

                    if hasattr(_, 'url'):
                        url = _.url
                    elif hasattr(_, 'name'):
                        url = urljoin('file:', _.name)

                _, format_ = detect_format(_)

                if isinstance(_, dict):

                    for property_name, value in _.items():

                        if value is None:
                            value = properties.NULL

                        try:

                            self[property_name] = value

                        except KeyError as error:

                            if error.args and len(error.args) == 1:

                                error.args = (
                                    r'%s.%s: %s' % (qualified_name(type(self)), error.args[0], repr(_)),
                                )

                            raise error

                else:
                    if format_ is None:
                        _dir = tuple(property_name for property_name in dir(_) if property_name[0] != '_')
                        for property_name in meta.writable(self.__class__).properties.keys():
                            if property_name in _dir:
                                setattr(self, getattr(_, property_name))
                    else:
                        raise TypeError(
                            'The `_` parameter must be a string, file-like object, or dictionary, not `%s`' %
                            repr(_)
                        )
                if format_ is not None:
                    meta.format_(self, format_)
            if url is not None:
                meta.url(self, url)
            if meta.pointer(self) is None:
                meta.pointer(self, '#')
            if meta.xpath(self) is None:
                meta.xpath(self, '')

    def __hash__(self):
        return id(self)

    def __setattr__(self, property_name, value):
        # type: (Object, str, Any) -> None

        instance_hooks = None

        unmarshalled_value = value

        if property_name[0] != '_':

            instance_hooks = hooks.read(self)  # type: hooks.Object

            if instance_hooks and instance_hooks.before_setattr:
                property_name, value = instance_hooks.before_setattr(self, property_name, value)

            try:

                property_definition = meta.read(self).properties[property_name]

            except KeyError:

                raise KeyError(
                    '`%s` has no attribute "%s".' % (
                        qualified_name(type(self)),
                        property_name
                    )
                )

            if value is not None:

                if isinstance(value, Generator):
                    value = tuple(value)

                try:

                    unmarshalled_value = property_definition.unmarshal(value)

                except (TypeError, ValueError) as error:

                    message = '\n - %s.%s: ' % (
                        qualified_name(type(self)),
                        property_name
                    )

                    if error.args and isinstance(error.args[0], str):

                        error.args = tuple(
                            chain(
                                (message + error.args[0],),
                                error.args[1:]
                            )
                        )

                    else:

                        error.args = (message + repr(value),)

                    raise error

        super().__setattr__(property_name, unmarshalled_value)

        if instance_hooks and instance_hooks.after_setattr:
            instance_hooks.after_setattr(self, property_name, value)

    def __setitem__(self, key, value):
        # type: (str, Any) -> None

        instance_hooks = hooks.read(self)  # type: hooks.Object

        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)

        instance_meta = meta.read(self)

        if key in instance_meta.properties:

            property_name = key

        else:

            property_name = None

            for potential_property_name, property in instance_meta.properties.items():
                if key == property.name:
                    property_name = potential_property_name
                    break

            if property_name is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        qualified_name(type(self)),
                        key
                    )
                )

        setattr(self, property_name, value)

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, key, value)

    def __delattr__(self, key):
        # type: (str) -> None

        instance_meta = meta.read(self)

        if key in instance_meta.properties:
            setattr(self, key, None)
        else:
            super().__delattr__(key)

    def __getitem__(self, key):
        # type: (str, Any) -> None

        instance_meta = meta.read(self)

        if key in instance_meta.properties:

            property_name = key

        else:

            property_definition = None
            property_name = None

            for pn, pd in instance_meta.properties.items():
                if key == pd.name:
                    property_name = pn
                    property_definition = pd
                    break

            if property_definition is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        qualified_name(type(self)),
                        key
                    )
                )

        return getattr(self, property_name)

    def __copy__(self):
        # type: () -> Object
        return self.__class__(self)

    def __deepcopy__(self, memo):
        # type: (Optional[dict]) -> Object

        new_instance = self.__class__()

        instance_meta = meta.read(self)
        class_meta = meta.read(type(self))

        if instance_meta is class_meta:
            meta_ = class_meta  # type: meta.Object
        else:
            meta.write(new_instance, deepcopy(instance_meta, memo))
            meta_ = instance_meta  # type: meta.Object

        instance_hooks = hooks.read(self)
        class_hooks = hooks.read(type(self))

        if instance_hooks is not class_hooks:
            hooks.write(new_instance, deepcopy(instance_hooks, memo))

        if meta_ is not None:

            for property_name in meta_.properties.keys():

                try:

                    value = getattr(self, property_name)

                    if isinstance(value, Generator):
                        value = tuple(value)

                    if value is not None:

                        if not callable(value):
                            value = deepcopy(value, memo)

                        setattr(new_instance, property_name, value)

                except TypeError as error:

                    label = '%s.%s: ' % (qualified_name(type(self)), property_name)

                    if error.args:
                        error.args = tuple(
                            chain(
                                (label + error.args[0],),
                                error.args[1:]
                            )
                        )
                    else:
                        error.args = (label + serialize(self),)

                    raise error

        return new_instance

    def _marshal(self):
        # type: (...) -> collections.OrderedDict
        object_ = self
        instance_hooks = hooks.read(object_)
        if (instance_hooks is not None) and (instance_hooks.before_marshal is not None):
            object_ = instance_hooks.before_marshal(object_)
        data = collections.OrderedDict()
        instance_meta = meta.read(object_)
        for property_name, property in instance_meta.properties.items():
            value = getattr(object_, property_name)
            if value is not None:
                key = property.name or property_name
                data[key] = property.marshal(value)
        if (instance_hooks is not None) and (instance_hooks.after_marshal is not None):
            data = instance_hooks.after_marshal(data)
        return data

    def __str__(self):
        # type: (...) -> str
        return serialize(self)

    def __repr__(self):
        # type: (...) -> str
        representation = [
            '%s(' % qualified_name(type(self))
        ]
        instance_meta = meta.read(self)
        for property_name in instance_meta.properties.keys():
            value = getattr(self, property_name)
            if value is not None:
                repr_value = (
                    qualified_name(value)
                    if isinstance(value, type) else
                    repr(value)
                )
                repr_value_lines = repr_value.split('\n')
                if len(repr_value_lines) > 2:
                    rvs = [repr_value_lines[0]]
                    for rvl in repr_value_lines[1:]:
                        rvs.append('    ' + rvl)
                    repr_value = '\n'.join(rvs)
                representation.append(
                    '    %s=%s,' % (property_name, repr_value)
                )
        representation.append(')')
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)

    def __eq__(self, other):
        # type: (Any) -> bool
        if type(self) is not type(other):
            return False
        instance_meta = meta.read(self)
        om = meta.read(other)
        self_properties = set(instance_meta.properties.keys())
        other_properties = set(om.properties.keys())
        if self_properties != other_properties:
            return False
        for property_name in (self_properties & other_properties):
            value = getattr(self, property_name)
            ov = getattr(other, property_name)
            if value != ov:
                return False
        return True

    def __ne__(self, other):
        # type: (Any) -> bool
        return False if self == other else True

    def __iter__(self):
        instance_meta = meta.read(self)
        for property_name, property in instance_meta.properties.items():
            yield property.name or property_name

    def _validate(self, raise_errors=True):
        # type: (bool) -> None

        validation_errors = []
        object_ = self

        instance_hooks = hooks.read(self)

        if (instance_hooks is not None) and (instance_hooks.before_validate is not None):
            object_ = instance_hooks.before_validate(object_)

        instance_meta = meta.read(object_)

        for property_name, property in instance_meta.properties.items():

            value = getattr(object_, property_name)

            if value is None:

                if callable(property.required):
                    required = property.required(object_)
                else:
                    required = property.required

                if required:

                    validation_errors.append(
                        'The property `%s` is required for `%s`:\n%s' % (
                            property_name,
                            qualified_name(type(object_)),
                            str(object_)
                        )
                    )
            else:

                if value is properties.NULL:

                    types = property.types

                    if callable(types):
                        types = types(value)

                    if types is not None:

                        if (str in types) and (native_str is not str) and (native_str not in types):
                            types = tuple(chain(*(
                                ((type_, native_str) if (type_ is str) else (type_,))
                                for type_ in types
                            )))

                        if properties.Null not in types:

                            validation_errors.append(
                                'Null values are not allowed in `%s.%s`, ' % (
                                    qualified_name(type(object_)), property_name
                                ) +
                                'permitted types include: %s.' % ', '.join(
                                    '`%s`' % qualified_name(type_) for type_ in types
                                )
                            )
                else:

                    try:
                        value_validation_error_messages = validate(value, property.types, raise_errors=False)

                        if value_validation_error_messages:

                            index = 0

                            for error_message in value_validation_error_messages:
                                value_validation_error_messages[index] = (
                                    'Error encountered ' +
                                    'while attempting to validate property `%s`:\n\n' % property_name +
                                    error_message
                                )

                            validation_errors.extend(value_validation_error_messages)

                    except errors.ValidationError as error:

                        message = '%s.%s:\n' % (qualified_name(type(object_)), property_name)

                        if error.args:
                            error.args = tuple(chain(
                                (error.args[0] + message,),
                                error.args[1:]
                            ))
                        else:
                            error.args = (
                                message,
                            )

        if (instance_hooks is not None) and (instance_hooks.after_validate is not None):
            instance_hooks.after_validate(object_)
        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))
        return validation_errors


abc.model.Object.register(Object)


class Array(list):

    _format = None  # type: Optional[str]
    _hooks = None  # type: Optional[hooks.Array]
    _meta = None  # type: Optional[meta.Array]

    def __init__(
        self,
        items=None,  # type: Optional[Union[Sequence, Set]]
        item_types=(
            None
        ),  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    ):
        self._meta = None  # type: Optional[meta.Array]
        self._hooks = None  # type: Optional[hooks.Array]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]
        url = None
        if isinstance(items, IOBase):
            if hasattr(items, 'url'):
                url = items.url
            elif hasattr(items, 'name'):
                url = urljoin('file:', items.name)
        items, format_ = detect_format(items)
        if item_types is None:
            if isinstance(items, Array):
                m = meta.read(items)
                if meta.read(self) is not m:
                    meta.write(self, deepcopy(m))
        else:
            meta.writable(self).item_types = item_types
        if items is not None:
            for item in items:
                self.append(item)
            if meta.pointer(self) is None:
                meta.pointer(self, '#')
            if meta.xpath(self) is None:
                meta.xpath(self, '')
        if url is not None:
            meta.url(self, url)
        if format_ is not None:
            meta.format_(self, format_)

    def __hash__(self):
        return id(self)

    def __setitem__(
        self,
        index,  # type: int
        value,  # type: Any
    ):
        instance_hooks = hooks.read(self)  # type: hooks.Object

        if instance_hooks and instance_hooks.before_setitem:
            index, value = instance_hooks.before_setitem(self, index, value)

        m = meta.read(self)  # type: Optional[meta.Array]

        if m is None:
            item_types = None
        else:
            item_types = m.item_types

        value = unmarshal(value, types=item_types)
        super().__setitem__(index, value)

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, index, value)

    def append(self, value):
        # type: (Any) -> None
        if not isinstance(value, UNMARSHALLABLE_TYPES):
            raise errors.UnmarshalTypeError(value)

        instance_hooks = hooks.read(self)  # type: hooks.Array

        if instance_hooks and instance_hooks.before_append:
            value = instance_hooks.before_append(self, value)

        instance_meta = meta.read(self)  # type: Optional[meta.Array]

        if instance_meta is None:
            item_types = None
        else:
            item_types = instance_meta.item_types

        value = unmarshal(value, types=item_types)

        super().append(value)

        if instance_hooks and instance_hooks.after_append:
            instance_hooks.after_append(self, value)

    def __copy__(self):
        # type: () -> Array
        return self.__class__(self)

    def __deepcopy__(self, memo=None):
        # type: (Optional[dict]) -> Array
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, deepcopy(im, memo=memo))
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, deepcopy(ih, memo=memo))
        for i in self:
            new_instance.append(deepcopy(i, memo=memo))
        return new_instance

    def _marshal(self):
        a = self
        h = hooks.read(a)
        if (h is not None) and (h.before_marshal is not None):
            a = h.before_marshal(a)
        m = meta.read(a)
        a = tuple(
            marshal(
                i,
                types=None if m is None else m.item_types
            ) for i in a
        )
        if (h is not None) and (h.after_marshal is not None):
            a = h.after_marshal(a)
        return a

    def _validate(
        self,
        raise_errors=True
    ):
        # type: (bool) -> None
        validation_errors = []
        a = self
        h = hooks.read(a)

        if (h is not None) and (h.before_validate is not None):
            a = h.before_validate(a)

        m = meta.read(a)

        if m.item_types is not None:

            for i in a:

                validation_errors.extend(validate(i, m.item_types, raise_errors=False))

        if (h is not None) and (h.after_validate is not None):
            h.after_validate(a)

        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))

        return validation_errors

    def __repr__(self):
        representation = [
            qualified_name(type(self)) + '('
        ]
        if len(self) > 0:
            representation.append('    [')
            for i in self:
                ri = (
                    qualified_name(i) if isinstance(i, type) else
                    repr(i)
                )
                rils = ri.split('\n')
                if len(rils) > 1:
                    ris = [rils[0]]
                    ris += [
                        '        ' + rvl
                        for rvl in rils[1:]
                    ]
                    ri = '\n'.join(ris)
                representation.append(
                    '        %s,' % ri
                )
            im = meta.read(self)
            cm = meta.read(type(self))
            m = None if (im is cm) else im  # type: Optional[meta.Array]
            representation.append(
                '    ]' + (''
                if m is None or m.item_types is None
                else ',')
            )
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            if im.item_types:
                representation.append(
                    '    item_types=(',
                )
                for it in im.item_types:
                    ri = (
                        qualified_name(it) if isinstance(it, type) else
                        repr(it)
                    )
                    rils = ri.split('\n')
                    if len(rils) > 2:
                        ris = [rils[0]]
                        ris += [
                            '        ' + rvl
                            for rvl in rils[1:-1]
                        ]
                        ris.append('        ' + rils[-1])
                        ri = '\n'.join(ris)
                    representation.append('        %s,' % ri)
                m = meta.read(self)
                if len(m.item_types) > 1:
                    representation[-1] = representation[-1][:-1]
                representation.append('    )')
        representation.append(')')
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)

    def __eq__(self, other):
        # type: (Any) -> bool
        if type(self) is not type(other):
            return False
        length = len(self)
        if length != len(other):
            return False
        for i in range(length):
            if self[i] != other[i]:
                return False
        return True

    def __ne__(self, other):
        # type: (Any) -> bool
        if self == other:
            return False
        else:
            return True

    def __str__(self):
        return serialize(self)


abc.model.Array.register(Array)


class Dictionary(collections.OrderedDict):

    _format = None  # type: Optional[str]
    _hooks = None  # type: Optional[hooks.Dictionary]
    _meta = None  # type: Optional[meta.Dictionary]

    def __init__(
        self,
        items=None,  # type: Optional[Mapping]
        value_types=(
            None
        ),  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    ):
        self._meta = None  # type: Optional[meta.Dictionary]
        self._hooks = None  # type: Optional[hooks.Dictionary]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]

        url = None

        if isinstance(items, IOBase):

            if hasattr(items, 'url'):
                url = items.url
            elif hasattr(items, 'name'):
                url = urljoin('file:', items.name)

        items, format_ = detect_format(items)

        if value_types is None:

            if isinstance(items, Dictionary):

                m = meta.read(items)

                if meta.read(self) is not m:
                    meta.write(self, deepcopy(m))
        else:

            meta.writable(self).value_types = value_types

        if items is None:

            super().__init__()

        else:

            if isinstance(items, (collections.OrderedDict, Dictionary)):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(items.items(), key=lambda kv: kv)

            super().__init__(items)

            if meta.pointer(self) is None:
                meta.pointer(self, '#')

            if meta.xpath(self) is None:
                meta.xpath(self, '')

        if url is not None:
            meta.url(self, url)

        if format_ is not None:
            meta.format_(self, format_)

    def __hash__(self):
        return id(self)

    def __setitem__(
        self,
        key,  # type: int
        value  # type: Any
    ):
        instance_hooks = hooks.read(self)  # type: hooks.Dictionary

        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)

        instance_meta = meta.read(self)  # type: Optional[meta.Dictionary]

        if instance_meta is None:
            value_types = None
        else:
            value_types = instance_meta.value_types

        try:

            unmarshalled_value = unmarshal(
                value,
                types=value_types
            )

        except TypeError as error:

            message = "\n - %s['%s']: " % (
                qualified_name(type(self)),
                key
            )

            if error.args and isinstance(error.args[0], str):

                error.args = tuple(
                    chain(
                        (message + error.args[0],),
                        error.args[1:]
                    )
                )

            else:

                error.args = (message + repr(value),)

            raise error

        if value is None:
            raise RuntimeError(key)

        super().__setitem__(
            key,
            unmarshalled_value
        )

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, key, unmarshalled_value)

    def __copy__(self):
        # type: (Dictionary) -> Dictionary
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, im)
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, ih)
        for k, v in self.items():
            new_instance[k] = v
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Dictionary
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, deepcopy(im, memo=memo))
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, deepcopy(ih, memo=memo))
        for k, v in self.items():
            new_instance[k] = deepcopy(v, memo=memo)
        return new_instance

    def _marshal(self):
        """
        This method marshals an instance of `Dictionary` as built-in type `OrderedDict` which can be serialized into
        JSON/YAML/XML.
        """

        # This variable is needed because before-marshal hooks are permitted to return altered *copies* of `self`, so
        # prior to marshalling--this variable may no longer point to `self`
        data = self  # type: Union[Dictionary, collections.OrderedDict]

        # Check for hooks
        instance_hooks = hooks.read(data)

        # Execute before-marshal hooks, if applicable
        if (instance_hooks is not None) and (instance_hooks.before_marshal is not None):
            data = instance_hooks.before_marshal(data)

        # Get the metadata, if any has been assigned
        instance_meta = meta.read(data)  # type: Optional[meta.Dictionary]

        # Check to see if value types are defined in the metadata
        if instance_meta is None:
            value_types = None
        else:
            value_types = instance_meta.value_types

        # Recursively convert the data to generic, serializable, data types
        unmarshalled_data = collections.OrderedDict(
            [
                (
                    k,
                    marshal(v, types=value_types)
                ) for k, v in data.items()
            ]
        )  # type: collections.OrderedDict

        # Execute after-marshal hooks, if applicable
        if (instance_hooks is not None) and (instance_hooks.after_marshal is not None):
            unmarshalled_data = instance_hooks.after_marshal(unmarshalled_data)

        return unmarshalled_data

    def _validate(self, raise_errors=True):
        # type: (Callable) -> None
        """
        Recursively validate
        """

        validation_errors = []
        d = self
        h = d._hooks or type(d)._hooks

        if (h is not None) and (h.before_validate is not None):
            d = h.before_validate(d)

        m = meta.read(d)  # type: Optional[meta.Dictionary]

        if m is None:
            value_types = None
        else:
            value_types = m.value_types

        if value_types is not None:

            for k, v in d.items():

                value_validation_errors = validate(v, value_types, raise_errors=False)\

                validation_errors.extend(value_validation_errors)

        if (h is not None) and (h.after_validate is not None):
            h.after_validate(d)

        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))

        return validation_errors

    def __repr__(self):
        representation = [
            qualified_name(type(self)) + '('
        ]
        items = tuple(self.items())
        if len(items) > 0:
            representation.append('    [')
            for k, v in items:
                rv = (
                    qualified_name(v) if isinstance(v, type) else
                    repr(v)
                )
                rvls = rv.split('\n')
                if len(rvls) > 1:
                    rvs = [rvls[0]]
                    for rvl in rvls[1:]:
                        rvs.append('            ' + rvl)
                    # rvs.append('            ' + rvs[-1])
                    rv = '\n'.join(rvs)
                    representation += [
                        '        (',
                        '            %s,' % repr(k),
                        '            %s' % rv,
                        '        ),'
                    ]
                else:
                    representation.append(
                        '        (%s, %s),' % (repr(k), rv)
                    )
            representation[-1] = representation[-1][:-1]
            representation.append(
                '    ]'
                if self._meta is None or self._meta.value_types is None else
                '    ],'
            )
        cm = meta.read(type(self))
        im = meta.read(self)
        if cm is not im:
            if self._meta.value_types:
                representation.append(
                    '    value_types=(',
                )
                for vt in im.value_types:
                    rv = (
                        qualified_name(vt) if isinstance(vt, type) else
                        repr(vt)
                    )
                    rvls = rv.split('\n')
                    if len(rvls) > 1:
                        rvs = [rvls[0]]
                        rvs += [
                            '        ' + rvl
                            for rvl in rvls[1:]
                        ]
                        rv = '\n'.join(rvs)
                    representation.append('        %s,' % rv)
                if len(self._meta.value_types) > 1:
                    representation[-1] = representation[-1][:-1]
                representation.append('    )')
        representation.append(')')
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)

    def __eq__(self, other):
        # type: (Any) -> bool
        if type(self) is not type(other):
            return False
        keys = tuple(self.keys())
        other_keys = tuple(other.keys())
        if keys != other_keys:
            return False
        for k in keys:
            if self[k] != other[k]:
                return False
        return True

    def __ne__(self, other):
        # type: (Any) -> bool
        if self == other:
            return False
        else:
            return True

    def __str__(self):
        return serialize(self)


abc.model.Dictionary.register(Dictionary)


def from_meta(name, metadata, module=None, docstring=None):
    # type: (meta.Meta, str, Optional[str]) -> type
    """
    Constructs an `Object`, `Array`, or `Dictionary` sub-class from an instance of `serial.meta.Meta`.

    Arguments:

        - name (str): The name of the class.

        - class_meta (serial.meta.Meta)

        - module (str): Specify the value for the class definition's `__module__` property. The invoking module will be
          used if this is not specified (if possible).

        - docstring (str): A docstring to associate with the class definition.
    """

    def typing_from_property(p):
        # type: (properties.Property) -> str
        if isinstance(p, type):
            if p in (
                Union, Dict, Any, Sequence, IO
            ):
                type_hint = p.__name__
            else:
                type_hint = qualified_name(p)
        elif isinstance(p, properties.DateTime):
            type_hint = 'datetime'
        elif isinstance(p, properties.Date):
            type_hint = 'date'
        elif isinstance(p, properties.Bytes):
            type_hint = 'bytes'
        elif isinstance(p, properties.Integer):
            type_hint = 'int'
        elif isinstance(p, properties.Number):
            type_hint = qualified_name(Number)
        elif isinstance(p, properties.Boolean):
            type_hint = 'bool'
        elif isinstance(p, properties.String):
            type_hint = 'str'
        elif isinstance(p, properties.Array):
            item_types = None
            if p.item_types:
                if len(p.item_types) > 1:
                    item_types = 'Union[%s]' % (
                        ', '.join(
                           typing_from_property(it)
                           for it in p.item_types
                        )
                    )
                else:
                    item_types = typing_from_property(p.item_types[0])
            type_hint = 'Sequence' + (
                '[%s]' % item_types
                if item_types else
                ''
            )
        elif isinstance(p, properties.Dictionary):
            value_types = None
            if p.value_types:
                if len(p.value_types) > 1:
                    value_types = 'Union[%s]' % (
                        ', '.join(
                           typing_from_property(vt)
                           for vt in p.value_types
                        )
                    )
                else:
                    value_types = typing_from_property(p.value_types[0])
            type_hint = (
                'Dict[str, %s]' % value_types
                if value_types else
                'dict'
            )
        elif p.types:
            if len(p.types) > 1:
                type_hint = 'Union[%s]' % ', '.join(
                    typing_from_property(t) for t in p.types
                )
            else:
                type_hint = typing_from_property(p.types[0])
        else:
            type_hint = 'Any'
        return type_hint
    if docstring is not None:
        if '\t' in docstring:
            docstring = docstring.replace('\t', '    ')
        lines = docstring.split('\n')
        indentation_length = float('inf')
        for line in lines:
            match = re.match(r'^[ ]+', line)
            if match:
                indentation_length = min(
                    indentation_length,
                    len(match.group())
                )
            else:
                indentation_length = 0
                break
        wrapped_lines = []
        for line in lines:
            line = '    ' + line[indentation_length:]
            if len(line) > 120:
                indent = re.match(r'^[ ]*', line).group()
                li = len(indent)
                words = re.split(r'([\w]*[\w,/"\'.;\-?`])', line[li:])
                wrapped_line = ''
                for word in words:
                    if (len(wrapped_line) + len(word) + li) <= 120:
                        wrapped_line += word
                    else:
                        wrapped_lines.append(indent + wrapped_line)
                        wrapped_line = '' if not word.strip() else word
                if wrapped_line:
                    wrapped_lines.append(indent + wrapped_line)
            else:
                wrapped_lines.append(line)
        docstring = '\n'.join(
            ['    """'] +
            wrapped_lines +
            ['    """']
        )
    if isinstance(metadata, meta.Dictionary):
        out = [
            'class %s(serial.model.Dictionary):' % name
        ]
        if docstring is not None:
            out.append(docstring)
        out.append('\n    pass')
    elif isinstance(metadata, meta.Array):
        out = [
            'class %s(serial.model.Array):' % name
        ]
        if docstring is not None:
            out.append(docstring)
        out.append('\n    pass')
    elif isinstance(metadata, meta.Object):
        out = [
            'class %s(serial.model.Object):' % name
        ]
        if docstring is not None:
            out.append(docstring)
        out += [
            '',
            '    def __init__(',
            '        self,',
            '        _=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]'
        ]
        for n, p in metadata.properties.items():
            out.append(
                '        %s=None,  # type: Optional[%s]' % (n, typing_from_property(p))
            )
        out.append(
            '    ):'
        )
        for n in metadata.properties.keys():
            out.append(
                '        self.%s = %s' % (n, n)
            )
        out.append('        super().__init__(_)\n\n')
    else:
        raise ValueError(metadata)
    class_definition = '\n'.join(out)
    namespace = dict(__name__='from_meta_%s' % name)
    imports = '\n'.join([
        'import serial',
        '',
        'serial.utilities.compatibility.backport()',
        ''
        'try:',
        '    from typing import Union, Dict, Any, Sequence, IO',
        'except ImportError:',
        '    Union = Dict = Any = Sequence = IO = None',
    ])
    source = '%s\n\n\n%s' % (imports, class_definition)
    exec(source, namespace)
    result = namespace[name]
    result._source = source

    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass

    if module is not None:
        result.__module__ = module

    result._meta = metadata

    return result
