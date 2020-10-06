# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from ..utilities.compatibility import backport

backport()

from future.utils import native_str  # noqa

from abc import ABCMeta, abstractmethod

# We need to inherit from `ABC` in python 3x, but in python 2x ABC is absent
try:
    from abc import ABC
except ImportError:
    ABC = object


class Property(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        types=None,  # type: Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Sequence[Union[str, serial.meta.Version]]]
    ):
        self._types = None  # type: Optional[Sequence[Union[type, Property]]]
        self.types = types
        self.name = name
        self.required = required
        self._versions = None  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]

    def __instancecheck__(self, instance):
        # type: (object) -> bool
        """
        Check an instance of a subclass to ensure it has required properties
        """

        for attribute in (
            '_types',
            '_versions',
            'name',
            'required'
        ):
            if not hasattr(self, attribute):
                return False

        # Perform any instance checks needed for our superclass(es)
        return super().__instancecheck__(instance)

    @property
    @abstractmethod
    def types(self):
        # type: (...) -> Optional[Sequence[Union[type, Property, Model]]]
        pass

    @types.setter
    @abstractmethod
    def types(self, types_or_properties):
        # type: (Optional[Sequence[Union[type, Property, Model]]]) -> None
        pass

    @property
    @abstractmethod
    def versions(self):
        # type: () -> Optional[Sequence[meta.Version]]
        pass

    @versions.setter
    @abstractmethod
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, collections_abc.Iterable, meta.Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        pass

    @abstractmethod
    def unmarshal(self, data):
        # type: (Any) -> Any
        pass

    @abstractmethod
    def marshal(self, data):
        # type: (Any) -> Any
        pass

    @abstractmethod
    def __repr__(self):
        # type: (...) -> str
        pass

    @abstractmethod
    def __copy__(self):
        # type: (...) -> Property
        pass

    @abstractmethod
    def __deepcopy__(self, memo):
        # type: (dict) -> Property
        pass
