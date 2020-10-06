from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from .utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

from serial.utilities import qualified_name, calling_function_qualified_name
from serial.abc.model import Model

from warnings import warn

import collections
import json as _json
from itertools import chain

import yaml as _yaml

import serial

try:
    import typing
except ImportError as e:
    typing = None


def _object_discrepancies(a, b):
    # type: (serial.model.Object, serial.model.Object) -> dict
    discrepancies = {}
    a_properties = set(serial.meta.read(a).properties.keys())
    b_properties = set(serial.meta.read(b).properties.keys())
    for property_ in a_properties | b_properties:
        try:
            a_value = getattr(a, property_)
        except AttributeError:
            a_value = None
        try:
            b_value = getattr(b, property_)
        except AttributeError:
            b_value = None
        if a_value != b_value:
            discrepancies[property_] = (a_value, b_value)
    return discrepancies


def json(
    model_instance,  # type: serial.model.Model
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    model(
        model_instance=model_instance,
        format_='json',
        raise_validation_errors=raise_validation_errors
    )


def yaml(
    model_instance,  # type: serial.model.Model
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    model(
        model_instance=model_instance,
        format_='yaml',
        raise_validation_errors=raise_validation_errors
    )


def xml(
    model_instance,  # type: serial.model.Model
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    raise NotImplementedError()
    # model(
    #     model_instance=model_instance,
    #     format_='xml',
    #     raise_validation_errors=raise_validation_errors
    # )


def model(
    model_instance,  # type: serial.model.Model
    format_,  # type: str
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    """
    Tests an instance of a `serial.model.Model` sub-class.

    Parameters:

        - model_instance (serial.model.Model):

            An instance of a `serial.model.Model` sub-class.

        - format_ (str):

            The serialization format being tested: 'json', 'yaml' or 'xml'.

        - raise_validation_errors (bool):

            The function `serial.model.validate` verifies that all required attributes are present, as well as any
            additional validations implemented using the model's validation hooks `after_validate` and/or
            `before_validate`.

                - If `True`, errors resulting from `serial.model.validate` are raised.

                - If `False`, errors resulting from `serial.model.validate` are expressed only as warnings.
    """
    if not isinstance(model_instance, Model):

        value_representation = repr(model_instance)

        raise TypeError(
            '`%s` requires an instance of `%s` for the parameter `model_instance`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(Model),
                (
                    (':\n%s' if '\n' in value_representation else ' `%s`') %
                    value_representation
                )
            )
        )

    serial.meta.format_(model_instance, format_)

    if isinstance(model_instance, serial.model.Object):

        errors = serial.marshal.validate(model_instance, raise_errors=raise_validation_errors)

        if errors:
            warn('\n' + '\n'.join(errors))

        model_type = type(model_instance)

        string = str(model_instance)

        assert string != ''

        reloaded_model_instance = model_type(string)
        qualified_model_name = qualified_name(type(model_instance))

        try:

            assert model_instance == reloaded_model_instance

        except AssertionError as e:

            sa = serial.marshal.serialize(model_instance)
            sb = serial.marshal.serialize(reloaded_model_instance)

            ra = ''.join(l.strip() for l in repr(model_instance).split('\n'))
            rb = ''.join(l.strip() for l in repr(reloaded_model_instance).split('\n'))

            message = [
                'Discrepancies were found between the instance of `%s` provided and ' % qualified_model_name +
                'a serialized/deserialized clone:'
            ]

            if sa != sb:

                message.append(
                    '\n    :\n\n        %s\n        !=\n        %s' % (
                        sa,
                        sb
                    )
                )

            if ra != rb:

                message.append(
                    '\n        %s\n        !=\n        %s\n' % (
                        ra,
                        rb
                    )
                )

            for k, a_b in _object_discrepancies(model_instance, reloaded_model_instance).items():

                a, b = a_b

                assert a != b

                sa = serial.marshal.serialize(a)
                sb = serial.marshal.serialize(b)

                if sa != sb:

                    message.append(
                        '\n    %s().%s:\n\n        %s\n        %s\n        %s' % (
                            qualified_model_name,
                            k,
                            sa,
                            '==' if sa == sb else '!=',
                            sb
                        )
                    )

                ra = ''.join(l.strip() for l in repr(a).split('\n'))
                rb = ''.join(l.strip() for l in repr(b).split('\n'))

                if ra != rb:

                    message.append(
                        '\n        %s\n        %s\n        %s' % (
                            ra,
                            '==' if ra == rb else '!=',
                            rb
                        )
                    )

            e.args = tuple(
                chain(
                    (e.args[0] + '\n' + '\n'.join(message) if e.args else '\n'.join(message),),
                    e.args[1:] if e.args else tuple()
                )
            )

            raise e

        reloaded_string = str(reloaded_model_instance)

        try:
            assert string == reloaded_string
        except AssertionError as e:
            m = '\n%s\n!=\n%s' % (string, reloaded_string)
            if e.args:
                e.args = tuple(chain(
                    (e.args[0] + '\n' + m,),
                    e.args[1:]
                ))
            else:
                e.args = (m,)
            raise e

        if format_ == 'json':
            reloaded_marshalled_data = _json.loads(
                string,
                object_hook=collections.OrderedDict,
                object_pairs_hook=collections.OrderedDict
            )
        elif format_ == 'yaml':
            reloaded_marshalled_data = _yaml.load(string)
        elif format_ == 'xml':
            raise NotImplementedError()
        else:
            format_representation = repr(format_)
            raise ValueError(
                'Valid serialization types for parameter `format_` are "json", "yaml", or "xml'", not" + (
                    (
                        ':\n%s' if '\n' in format_representation else ' %s.'
                    ) % format_representation
                )
            )

        keys = set()

        for property_name, property in serial.meta.read(model_instance).properties.items():

            keys.add(property.name or property_name)
            property_value = getattr(model_instance, property_name)

            if isinstance(property_value, Model) or (
                hasattr(property_value, '__iter__') and
                (not isinstance(property_value, (str, native_str, bytes)))
            ):
                model(property_value, format_=format_, raise_validation_errors=raise_validation_errors)

        for k in reloaded_marshalled_data.keys():

            if k not in keys:
                raise KeyError(
                    '"%s" not found in serialized/re-deserialized data: %s' % (
                        k,
                        string
                    )
                )

    elif isinstance(model_instance, serial.model.Array):

        serial.marshal.validate(model_instance)

        for item in model_instance:

            if isinstance(item, Model) or (
                hasattr(item, '__iter__') and
                (not isinstance(item, (str, native_str, bytes)))
            ):
                model(item, format_=format_, raise_validation_errors=raise_validation_errors)

    elif isinstance(model_instance, serial.model.Dictionary):

        serial.marshal.validate(model_instance)

        for key, value in model_instance.items():

            if isinstance(value, Model) or (
                hasattr(value, '__iter__') and
                (not isinstance(value, (str, native_str, bytes)))
            ):
                model(value, format_=format_, raise_validation_errors=raise_validation_errors)
