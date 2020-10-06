# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from serial.utilities.compatibility import backport

backport()

from abc import ABCMeta, abstractmethod

# We need ABCs to inherit from `ABC` in python 3x, but in python 2x ABC is absent and we need classes to inherit from
# `object` in order to be new-style classes
try:
    from abc import ABC
except ImportError:
    ABC = object

from ..utilities import collections


class Model(ABC):

    __metaclass__ = ABCMeta

    _format = None  # type: Optional[str]
    _meta = None  # type: Optional[meta.Object]
    _hooks = None  # type: Optional[hooks.Object]

    @abstractmethod
    def __init__(self):
        self._format = None  # type: Optional[str]
        self._meta = None  # type: Optional[meta.Meta]
        self._hooks = None  # type: Optional[hooks.Hooks]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]

    @classmethod
    def __subclasscheck__(cls, subclass):
        # type: (object) -> bool
        """
        Check a subclass to ensure it has required properties
        """

        if cls is subclass or type.__subclasscheck__(cls, subclass):
            return True

        for attribute in (
            '_format',
            '_meta',
            '_hooks'
        ):
            if not hasattr(subclass, attribute):
                return False

        return True

    def __instancecheck__(self, instance):
        # type: (object) -> bool
        """
        Check an instance of a subclass to ensure it has required properties
        """

        for attribute in (
            '_format',
            '_meta',
            '_hooks',
            '_url',
            '_xpath',
            '_pointer'
        ):
            if not hasattr(self, attribute):
                return False

        # Perform any instance checks needed for our superclass(es)
        try:
            return super().__instancecheck__(instance)
        except AttributeError:  # There is no further instance-checking to perform
            return True

    @abstractmethod
    def _marshal(self):
        # type: (...) -> Union[collections.OrderedDict, list]
        pass

    @abstractmethod
    def _validate(self, raise_errors=True):
        # type: (bool) -> None
        pass

    @abstractmethod
    def __str__(self):
        # type: (...) -> str
        pass

    @abstractmethod
    def __repr__(self):
        # type: (...) -> str
        pass

    @abstractmethod
    def __copy__(self):
        # type: (...) -> Object
        pass

    @abstractmethod
    def __deepcopy__(self, memo):
        # type: (Optional[dict]) -> Object
        pass

    @abstractmethod
    def __eq__(self, other):
        # type: (Any) -> bool
        pass

    @abstractmethod
    def __ne__(self, other):
        # type: (Any) -> bool
        pass


class Object(Model):

    @abstractmethod
    def _marshal(self):
        # type: (...) -> collections.OrderedDict
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        pass

    @abstractmethod
    def __getitem__(self, key):
        # type: (str, Any) -> None
        pass

    @abstractmethod
    def __setattr__(self, property_name, value):
        # type: (Object, str, Any) -> None
        pass

    @abstractmethod
    def __getattr__(self, key):
        # type: (str) -> Any
        pass

    @abstractmethod
    def __delattr__(self, key):
        # type: (str) -> None
        pass


class Dictionary(Model):

    @classmethod
    def __subclasscheck__(cls, subclass):
        # type: (object) -> bool
        """
        Verify inheritance
        """
        if cls is subclass or type.__subclasscheck__(cls, subclass):
            return True

        if not issubclass(subclass, collections.OrderedDict):
            return False

        # Perform any subclass checks needed for our superclass(es)
        return super().__subclasscheck__(subclass)

    def __instancecheck__(self, instance):
        # type: (object) -> bool
        """
        Check an instance of a subclass to ensure it has required properties
        """

        if not isinstance(self, collections.OrderedDict):
            return False

        # Perform any instance checks needed for our superclass(es)
        return super().__instancecheck__(instance)

    @abstractmethod
    def _marshal(self):
        # type: (...) -> collections.OrderedDict
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        pass

    def keys(self):
        # type: (...) -> Iterable[str]
        pass

    def values(self):
        # type: (...) -> Iterable[Any]
        pass


class Array(Model):

    @classmethod
    def __subclasscheck__(cls, subclass):
        # type: (object) -> bool
        """
        Verify inheritance
        """

        if cls is subclass or type.__subclasscheck__(cls, subclass):
            return True

        if not issubclass(subclass, list):
            return False

        # Perform any subclass checks needed for our superclass(es)
        return super().__subclasscheck__(subclass)

    def __instancecheck__(self, instance):
        # type: (object) -> bool
        """
        Check an instance of a subclass to ensure it has required properties
        """

        if not isinstance(self, list):
            return False

        # Perform any instance checks needed for our superclass(es)
        return super().__instancecheck__(instance)

    @abstractmethod
    def _marshal(self):
        # type: (...) -> list
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        pass

    @abstractmethod
    def append(self, value):
        # type: (Any) -> None
        pass


