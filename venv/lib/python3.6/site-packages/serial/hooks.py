from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from .utilities.compatibility import backport

backport()

import serial.abc

from copy import deepcopy

import serial
from .utilities import qualified_name
from .abc.model import Model

try:
    import typing
except ImportError as e:
    typing = None


class Hooks(object):

    def __init__(
        self,
        before_marshal=None,  # Optional[Callable]
        after_marshal=None,  # Optional[Callable]
        before_unmarshal=None,  # Optional[Callable]
        after_unmarshal=None,  # Optional[Callable]
        before_serialize=None,  # Optional[Callable]
        after_serialize=None,  # Optional[Callable]
        before_deserialize=None,  # Optional[Callable]
        after_deserialize=None,  # Optional[Callable]
        before_validate=None,  # Optional[Callable]
        after_validate=None,  # Optional[Callable]
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_deserialize = before_deserialize
        self.after_deserialize = after_deserialize
        self.before_validate = before_validate
        self.after_validate = after_validate

    def __copy__(self):
        return self.__class__(**vars(self))

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        return self.__class__(**{
            k: deepcopy(v, memo=memo)
            for k, v in vars(self).items()
        })

    def __bool__(self):
        return True


class Object(Hooks):

    def __init__(
        self,
        before_marshal=None,  # Optional[Callable]
        after_marshal=None,  # Optional[Callable]
        before_unmarshal=None,  # Optional[Callable]
        after_unmarshal=None,  # Optional[Callable]
        before_serialize=None,  # Optional[Callable]
        after_serialize=None,  # Optional[Callable]
        before_deserialize=None,  # Optional[Callable]
        after_deserialize=None,  # Optional[Callable]
        before_validate=None,  # Optional[Callable]
        after_validate=None,  # Optional[Callable]
        before_setattr=None,  # Optional[Callable]
        after_setattr=None,  # Optional[Callable]
        before_setitem=None,  # Optional[Callable]
        after_setitem=None,  # Optional[Callable]
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_deserialize = before_deserialize
        self.after_deserialize = after_deserialize
        self.before_validate = before_validate
        self.after_validate = after_validate
        self.before_setattr = before_setattr
        self.after_setattr = after_setattr
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem


class Array(Hooks):

    def __init__(
        self,
        before_marshal=None,  # Optional[Callable]
        after_marshal=None,  # Optional[Callable]
        before_unmarshal=None,  # Optional[Callable]
        after_unmarshal=None,  # Optional[Callable]
        before_serialize=None,  # Optional[Callable]
        after_serialize=None,  # Optional[Callable]
        before_deserialize=None,  # Optional[Callable]
        after_deserialize=None,  # Optional[Callable]
        before_validate=None,  # Optional[Callable]
        after_validate=None,  # Optional[Callable]
        before_setitem=None,  # Optional[Callable]
        after_setitem=None,  # Optional[Callable]
        before_append=None,  # Optional[Callable]
        after_append=None,  # Optional[Callable]
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_deserialize = before_deserialize
        self.after_deserialize = after_deserialize
        self.before_validate = before_validate
        self.after_validate = after_validate
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem
        self.before_append = before_append
        self.after_append = after_append


class Dictionary(Hooks):

    def __init__(
        self,
        before_marshal=None,  # Optional[Callable]
        after_marshal=None,  # Optional[Callable]
        before_unmarshal=None,  # Optional[Callable]
        after_unmarshal=None,  # Optional[Callable]
        before_serialize=None,  # Optional[Callable]
        after_serialize=None,  # Optional[Callable]
        before_deserialize=None,  # Optional[Callable]
        after_deserialize=None,  # Optional[Callable]
        before_validate=None,  # Optional[Callable]
        after_validate=None,  # Optional[Callable]
        before_setitem=None,  # Optional[Callable]
        after_setitem=None,  # Optional[Callable]
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_deserialize = before_deserialize
        self.after_deserialize = after_deserialize
        self.before_validate = before_validate
        self.after_validate = after_validate
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem


def read(
    model_instance  # type: Union[type, serial.abc.model.Model]
):
    # type: (...) -> Hooks
    """
    Read metadata from a model instance (the returned metadata may be inherited, and therefore should not be written to)
    """

    if isinstance(model_instance, type):
        return model_instance._hooks
    elif isinstance(model_instance, Model):
        return model_instance._hooks or read(type(model_instance))


def writable(
    model_instance  # type: Union[type, serial.abc.model.Model]
):
    # type: (...) -> Hooks
    """
    Retrieve a metadata instance. If the instance currently inherits its metadata from a class or superclass,
    this funtion will copy that metadata and assign it directly to the model instance.
    """

    if isinstance(model_instance, type):

        if model_instance._hooks is None:

            model_instance._hooks = (
                Object()
                if issubclass(model_instance, serial.model.Object) else
                Array()
                if issubclass(model_instance, serial.model.Array) else
                Dictionary()
                if issubclass(model_instance, serial.model.Dictionary)
                else None
            )

        else:

            for b in model_instance.__bases__:

                if hasattr(b, '_hooks') and (model_instance._hooks is b._hooks):
                    model_instance._hooks = deepcopy(model_instance._hooks)
                    break

    elif isinstance(model_instance, Model):

        if model_instance._hooks is None:
            model_instance._hooks = deepcopy(writable(type(model_instance)))

    return model_instance._hooks


def write(
    model_instance,  # type: Union[type, serial.abc.model.Model]
    meta  # type: Hooks
):
    # type: (...) -> None
    """
    Write metadata to a class or instance
    """

    if isinstance(model_instance, type):

        t = model_instance
        mt = (
            Object
            if issubclass(model_instance, serial.model.Object) else
            Array
            if issubclass(model_instance, serial.model.Array) else
            Dictionary
            if issubclass(model_instance, serial.model.Dictionary)
            else None
        )

    elif isinstance(model_instance, Model):

        t = type(model_instance)
        mt = (
            Object
            if isinstance(model_instance, serial.model.Object) else
            Array
            if isinstance(model_instance, serial.model.Array) else
            Dictionary
            if isinstance(model_instance, serial.model.Dictionary)
            else None
        )

    if not isinstance(meta, mt):
        raise ValueError(
            'Hooks assigned to `%s` must be of type `%s`' % (
                qualified_name(t),
                qualified_name(mt)
            )
        )

    model_instance._hooks = meta
