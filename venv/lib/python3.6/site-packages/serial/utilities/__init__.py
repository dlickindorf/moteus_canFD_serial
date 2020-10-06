from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from . import compatibility

compatibility.backport()  # noqa

import builtins

import os  # noqa
import sys  # noqa

from io import UnsupportedOperation  # noqa


from collections import OrderedDict  # noqa
from unicodedata import normalize  # noqa

import re  # noqa
import inspect  # noqa
from keyword import iskeyword  # noqa

# region Compatibility Conditionals

# The following detects the presence of the typing library

try:
    from typing import Union, Optional, Iterable, Tuple, Any, Callable, AnyStr, Iterator  # noqa
except ImportError:
    Union = Optional = Iterable = Tuple = Any = Callable = AnyStr = Iterator = None


# Before `collections.abc` existed, the definitions we use from this module were in `collections`
try:
    import collections.abc as collections_abc
    import collections
except ImportError:
    import collections
    collections_abc = collections

# Earlier versions of the `collections` library do not include the `Generator` class, so when this class is missing--
# we employ a workaround.

if hasattr(collections_abc, 'Generator'):
    Generator = collections_abc.Generator
else:
    Generator = type(n for n in (1, 2, 3))

# endregion

try:

    from inspect import signature

    getargspec = None

except ImportError:

    signature = None

    try:
        from inspect import getfullargspec
    except ImportError:
        from inspect import getargspec as getfullargspec


_Module = type(re)


def qualified_name(type_):
    # type: (Union[type, _Module]) -> str
    """
    >>> print(qualified_name(qualified_name))
    qualified_name

    >>> from serial import model
    >>> print(qualified_name(model.marshal))
    serial.model.marshal
    """

    if hasattr(type_, '__qualname__'):
        type_name = '.'.join(name_part for name_part in type_.__qualname__.split('.') if name_part[0] != '<')
    else:
        type_name = type_.__name__

    if isinstance(type_, _Module):

        if type_name in (
            'builtins', '__builtin__', '__main__', '__init__'
        ):
            type_name = None

    else:

        if type_.__module__ not in (
            'builtins', '__builtin__', '__main__', '__init__'
        ):
            type_name = type_.__module__ + '.' + type_name

    return type_name


def calling_functions_qualified_names(depth=1):
    # type: (int) -> Iterator[str]
    """
    >>> def my_function_a(): return calling_functions_qualified_names()
    >>> def my_function_b(): return my_function_a()
    >>> print(my_function())
    ['my_function_b', 'my_function_a']
    """

    depth += 1
    name = calling_function_qualified_name(depth=depth)
    names = []

    while name:
        if name and not (names and names[0] == name):
            names.insert(0, name)
        depth += 1
        name = calling_function_qualified_name(depth=depth)

    return names


def calling_function_qualified_name(depth=1):
    # type: (int) -> Optional[str]
    """
    >>> def my_function(): return calling_function_qualified_name()
    >>> print(my_function())
    """

    if not isinstance(depth, int):

        depth_representation = repr(depth)

        raise TypeError(
            'The parameter `depth` for `serial.utilities.calling_function_qualified_name` must be an `int`, not' +
            (
                (':\n%s' if '\n' in depth_representation else ' %s.') %
                depth_representation
            )
        )
    try:
        stack = inspect.stack()
    except IndexError:
        return None

    if len(stack) < (depth + 1):
        return None

    name_list = []
    frame_info = stack[depth]  # type: inspect.FrameInfo

    try:
        frame_function = frame_info.function
    except AttributeError:
        frame_function = frame_info[3]

    if frame_function != '<module>':

        try:
            frame = frame_info.frame
        except AttributeError:
            frame = frame_info[0]

        name_list.append(frame_function)
        arguments, _, _, frame_locals = inspect.getargvalues(frame)

        if arguments:

            argument = arguments[0]
            argument_value = frame_locals[argument]
            argument_value_type = type(argument_value)

            if (
                hasattr(argument_value_type, '__name__') and
                hasattr(argument_value_type, '__module__') and
                (
                    (argument_value_type.__name__ not in dir(builtins)) or
                    (getattr(builtins, argument_value_type.__name__) is not argument_value_type)
                )
            ):
                name_list.append(qualified_name(argument_value_type))

    if len(name_list) < 2:

        try:
            file_name = frame_info.filename
        except AttributeError:
            file_name = frame_info[1]

        module_name = inspect.getmodulename(file_name)

        if (module_name is not None) and (module_name not in sys.modules):

            path_parts = list(os.path.split(file_name))
            path_parts.pop()

            while path_parts:

                parent = path_parts.pop()
                module_name = parent + '.' + module_name

                if module_name in sys.modules:
                    break

        if module_name is None:
            raise ValueError('The path "%s" is not a python module' % file_name)
        else:
            if module_name in sys.modules:
                qualified_module_name = qualified_name(sys.modules[module_name])
                name_list.append(qualified_module_name)

    return '.'.join(reversed(name_list))


def property_name(string):
    # type: (str) -> str
    """
    Converts a "camelCased" attribute/property name, or a name which conflicts with a python keyword, to a
    pep8-compliant property name.

    >>> print(property_name('theBirdsAndTheBees'))
    the_birds_and_the_bees

    >>> print(property_name('FYIThisIsAnAcronym'))
    fyi_this_is_an_acronym

    >>> print(property_name('in'))
    in_

    >>> print(property_name('id'))
    id_
    """
    pn = re.sub(
        r'__+',
        '_',
        re.sub(
            r'[^\w]+',
            '',
            re.sub(
                r'([a-zA-Z])([0-9])',
                r'\1_\2',
                re.sub(
                    r'([0-9])([a-zA-Z])',
                    r'\1_\2',
                    re.sub(
                        r'([A-Z])([A-Z])([a-z])',
                        r'\1_\2\3',
                        re.sub(
                            r'([a-z])([A-Z])',
                            r'\1_\2',
                            re.sub(
                                r'([^\x20-\x7F]|\s)+',
                                '_',
                                normalize('NFKD', string)
                            )
                        )
                    )
                )
            )
        )
    ).lower()
    if iskeyword(pn) or (pn in dir(builtins)):
        pn += '_'
    return pn


def class_name(string):
    """
    >>> print(class_name('the birds and the bees'))
    TheBirdsAndTheBees

    >>> print(class_name('the-birds-and-the-bees'))
    TheBirdsAndTheBees

    >>> print(class_name('**the - birds - and - the - bees**'))
    TheBirdsAndTheBees

    >>> print(class_name('FYI is an acronym'))
    FYIIsAnAcronym

    >>> print(class_name('in-you-go'))
    InYouGo

    >>> print(class_name('False'))
    False_

    >>> print(class_name('True'))
    True_

    >>> print(class_name('ABC Acronym'))
    ABCAcronym
    """
    return camel(string, capitalize=True)


def camel(string, capitalize=False):
    # type: (str, bool) -> str
    """
    >>> print(camel('the birds and the bees'))
    theBirdsAndTheBees

    >>> print(camel('the-birds-and-the-bees'))
    theBirdsAndTheBees

    >>> print(camel('**the - birds - and - the - bees**'))
    theBirdsAndTheBees

    >>> print(camel('FYI is an acronym'))
    fyiIsAnAcronym

    >>> print(camel('in-you-go'))
    inYouGo

    >>> print(camel('False'))
    false

    >>> print(camel('True'))
    true

    >>> print(camel('in'))
    in_
    """
    string = normalize('NFKD', string)
    characters = []
    if not capitalize:
        string = string.lower()
    capitalize_next = capitalize
    for s in string:
        if s in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
            if capitalize_next:
                if capitalize or characters:
                    s = s.upper()
            characters.append(s)
            capitalize_next = False
        else:
            capitalize_next = True
    cn = ''.join(characters)
    if iskeyword(cn) or (cn in dir(builtins)):
        cn += '_'
    return cn


def get_source(o):
    # type: (object) -> str
    if hasattr(o, '_source') and isinstance(o._source, str):
        result = o._source
    else:
        result = inspect.getsource(o)
    return result


def camel_split(string):
    # test: (str) -> str
    """
    >>> print('(%s)' % ', '.join("'%s'" % s for s in camel_split('theBirdsAndTheBees')))
    ('the', 'Birds', 'And', 'The', 'Bees')
    >>> print('(%s)' % ', '.join("'%s'" % s for s in camel_split('theBirdsAndTheBees123')))
    ('the', 'Birds', 'And', 'The', 'Bees', '123')
    >>> print('(%s)' % ', '.join("'%s'" % s for s in camel_split('theBirdsAndTheBeesABC123')))
    ('the', 'Birds', 'And', 'The', 'Bees', 'ABC', '123')
    >>> print('(%s)' % ', '.join("'%s'" % s for s in camel_split('the-Birds-And-The-Bees-ABC--123')))
    ('the', '-', 'Birds', '-', 'And', '-', 'The', '-', 'Bees', '-', 'ABC', '--', '123')
    >>> print('(%s)' % ', '.join("'%s'" % s for s in camel_split('THEBirdsAndTheBees')))
    ('THE', 'Birds', 'And', 'The', 'Bees')
    """
    words = []
    character_type = None
    acronym = False
    for s in string:
        if s in '0123456789':
            if character_type == 0:
                words[-1].append(s)
            else:
                words.append([s])
            character_type = 0
            acronym = False
        elif s in 'abcdefghijklmnopqrstuvwxyz':
            if character_type == 1:
                words[-1].append(s)
            elif character_type == 2:
                if acronym:
                    words.append([words[-1].pop()] + [s])
                else:
                    words[-1].append(s)
            else:
                words.append([s])
            character_type = 1
            acronym = False
        elif s in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if character_type == 2:
                words[-1].append(s)
                acronym = True
            else:
                words.append([s])
                acronym = False
            character_type = 2
        else:
            if character_type == 3:
                words[-1].append(s)
            else:
                words.append([s])
            character_type = 3
    return tuple(
        ''.join(w) for w in words
    )


def properties_values(o):
    # type: (object) -> Sequence[Tuple[AnyStr, Any]]
    for a in dir(o):
        if a[0] != '_':
            v = getattr(o, a)
            if not callable(v):
                yield a, v


UNDEFINED = None


class Undefined(object):

    def __init__(self):

        if UNDEFINED is not None:
            raise RuntimeError(
                '%s may only be defined once.' % repr(self)
            )

    def __repr__(self):
        return (
            'UNDEFINED'
            if self.__module__ in ('__main__', 'builtins', '__builtin__', __name__) else
            '%s.UNDEFINED' % self.__module__
        )

    def __bool__(self):
        return False

    def __hash__(self):
        return 0

    def __eq__(self, other):
        # type: (Any) -> bool
        return other is self


UNDEFINED = Undefined()


def parameters_defaults(function):
    # type: (Callable) -> OrderedDict
    """
    Returns an ordered dictionary mapping a function's argument names to default values, or `UNDEFINED` in the case of
    positional arguments.

    >>> class X(object):
    ...
    ...    def __init__(self, a, b, c, d=1, e=2, f=3):
    ...        pass
    ...
    >>> print(list(parameters_defaults(X.__init__).items()))
    [('self', UNDEFINED), ('a', UNDEFINED), ('b', UNDEFINED), ('c', UNDEFINED), ('d', 1), ('e', 2), ('f', 3)]
    """
    pd = OrderedDict()
    if signature is None:
        spec = getfullargspec(function)
        i = - 1
        for a in spec.args:
            pd[a] = UNDEFINED
        for a in reversed(spec.args):
            try:
                pd[a] = spec.defaults[i]
            except IndexError:
                break
            i -= 1
    else:
        for pn, p in signature(function).parameters.items():
            if p.default is inspect.Parameter.empty:
                pd[pn] = UNDEFINED
            else:
                pd[pn] = p.default
    return pd


def read(data):
    # type: (Union[str, IOBase, addbase]) -> Any
    if (
        (hasattr(data, 'readall') and callable(data.readall)) or
        (hasattr(data, 'read') and callable(data.read))
    ):
        if hasattr(data, 'seek') and callable(data.seek):
            try:
                data.seek(0)
            except UnsupportedOperation:
                pass
        if hasattr(data, 'readall') and callable(data.readall):
            try:
                data = data.readall()
            except UnsupportedOperation:
                data = data.read()
        else:
            data = data.read()
        return data
    else:
        raise TypeError(
            '%s is not a file-like object' % repr(data)
        )


if __name__ == '__main__':
    import doctest
    doctest.testmod()
