"""
This module extends the functionality of `urllib.request.Request` to support multipart requests, to support passing
instances of serial models to the `data` parameter/property for `urllib.request.Request`, and to
support casting requests as `str` or `bytes` (typically for debugging purposes and/or to aid in producing
non-language-specific API documentation).
"""
# region Backwards Compatibility
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from .utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

import random
import re
import string
import urllib.request

try:
    from typing import Dict, Sequence, Set, Iterable
except ImportError:
    Dict = Sequence = Set = None

from serial.marshal import serialize
from .abc.model import Model
from .utilities import collections_abc


class Headers(object):
    """
    A dictionary of headers for a `Request`, `Part`, or `MultipartRequest` instance.
    """

    def __init__(self, items, request):
        # type: (Dict[str, str], Union[Part, Request]) -> None
        self._dict = {}
        self.request = request  # type: Data
        self.update(items)

    def pop(self, key, default=None):
        # type: (str, Optional[str]) -> str
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.pop(key, default=default)

    def popitem(self):
        # type: (str, Optional[str]) -> str
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.popitem()

    def setdefault(self, key, default=None):
        # type: (str, Optional[str]) -> str
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.setdefault(key, default=default)

    def update(self, iterable=None, **kwargs):
        # type: (Union[Dict[str, str], Sequence[Tuple[str, str]]], Union[Dict[str, str]]) -> None
        cd = {}
        if iterable is None:
            d = kwargs
        else:
            d = dict(iterable, **kwargs)
        for k, v in d.items():
            cd[k.capitalize()] = v
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.update(cd)

    def __delitem__(self, key):
        # type: (str) -> None
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        del self._dict[key]

    def __setitem__(self, key, value):
        # type: (str, str) -> None
        key = key.capitalize()
        if key != 'Content-length':
            if hasattr(self.request, '_boundary'):
                self.request._boundary = None
            if hasattr(self.request, '_bytes'):
                self.request._bytes = None
            return self._dict.__setitem__(key, value)

    def __getitem__(self, key):
        # type: (str) -> None
        key = key.capitalize()
        if key == 'Content-length':
            data = self.request.data
            if data is None:
                content_length = 0
            else:
                content_length = len(data)
            value = str(content_length)
        else:
            try:
                value = self._dict.__getitem__(key)
            except KeyError as e:
                if key == 'Content-type':
                    if hasattr(self.request, 'parts') and self.request.parts:
                        value = 'multipart/form-data'
            if (
                (value is not None) and
                value.strip().lower()[:9] == 'multipart' and
                hasattr(self.request, 'boundary')
            ):
                value += '; boundary=' + str(self.request.boundary, encoding='utf-8')
        return value

    def keys(self):
        # type: (...) -> Iterable[str]
        return (k for k in self)

    def values(self):
        return (self[k] for k in self)

    def __len__(self):
        return len(tuple(self))

    def __iter__(self):
        # type: (...) -> Iterable[str]
        keys = set()
        for k in self._dict.keys():
            keys.add(k)
            yield k
        if type(self.request) is not Part:
            # *Always* include "Content-length"
            if 'Content-length' not in keys:
                yield 'Content-length'
        if (
            hasattr(self.request, 'parts') and
            self.request.parts and
            ('Content-type' not in keys)
        ):
            yield 'Content-type'

    def __contains__(self, key):
        # type: (str) -> bool
        return True if key in self.keys() else False

    def items(self):
        # type: (...) -> Iterable[Tuple[str, str]]
        for k in self:
            yield k, self[k]

    def copy(self):
        # type: (...) -> Headers
        return self.__class__(
            self._dict,
            request=self.request
        )

    def __copy__(self):
        # type: (...) -> Headers
        return self.copy()


class Data(object):
    """
    One of a multipart request's parts.
    """

    def __init__(
        self,
        data=None,  # type: Optional[Union[bytes, str, Sequence, Set, dict, Model]]
        headers=None  # type: Optional[Dict[str, str]]
    ):
        """
        Parameters:

            - data (bytes|str|collections.Sequence|collections.Set|dict|serial.abc.Model): The payload.

            - headers ({str: str}): A dictionary of headers (for this part of the request body, not the main request).
              This should (almost) always include values for "Content-Disposition" and "Content-Type".
        """
        self._bytes = None  # type: Optional[bytes]
        self._headers = None
        self._data = None
        self.headers = headers  # type: Dict[str, str]
        self.data = data  # type: Optional[bytes]

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._bytes = None
        if headers is None:
            headers = Headers({}, self)
        elif isinstance(headers, Headers):
            headers.request = self
        else:
            headers = Headers(headers, self)
        self._headers = headers

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        # type: (Optional[Union[bytes, str, Sequence, Set, dict, Model]]) -> None
        self._bytes = None
        if data is not None:
            serialize_type = None
            if 'Content-type' in self.headers:
                ct = self.headers['Content-type']
                if re.search(r'/json\b', ct) is not None:
                    serialize_type = 'json'
                if re.search(r'/xml\b', ct) is not None:
                    serialize_type = 'xml'
                if re.search(r'/yaml\b', ct) is not None:
                    serialize_type = 'yaml'
            if isinstance(data, (Model, dict)) or (
                isinstance(data, (collections_abc.Sequence, collections_abc.Set)) and not
                isinstance(data, (str, bytes))
            ):
                data = serialize(data, serialize_type or 'json')
            if isinstance(data, str):
                data = bytes(data, encoding='utf-8')
        self._data = data

    def __bytes__(self):
        if self._bytes is None:
            lines = []
            for k, v in self.headers.items():
                lines.append(bytes(
                    '%s: %s' % (k, v),
                    encoding='utf-8'
                ))
            lines.append(b'')
            data = self.data
            if data:
                lines.append(self.data)
            self._bytes = b'\r\n'.join(lines) + b'\r\n'
        return self._bytes

    def __str__(self):
        b = self.__bytes__()
        if not isinstance(b, native_str):
            b = repr(b)[2:-1].replace('\\r\\n', '\r\n').replace('\\n', '\n')
        return b


class Part(Data):

    def __init__(
        self,
        data=None,  # type: Optional[Union[bytes, str, Sequence, Set, dict, Model]]
        headers=None,  # type: Optional[Dict[str, str]]
        parts=None  # type: Optional[Sequence[Part]]
    ):
        """
        Parameters:

            - data (bytes|str|collections.Sequence|collections.Set|dict|serial.abc.Model): The payload.

            - headers ({str: str}): A dictionary of headers (for this part of the request body, not the main request).
              This should (almost) always include values for "Content-Disposition" and "Content-Type".
        """
        self._boundary = None  # type: Optional[bytes]
        self._parts = None  # type: Optional[Parts]
        self.parts = parts
        Data.__init__(self, data=data, headers=headers)

    @property
    def boundary(self):
        """
        Calculates a boundary which is not contained in any of the request parts.
        """
        if self._boundary is None:
            data = b'\r\n'.join(
                [self._data or b''] +
                [bytes(p) for p in self.parts]
            )
            boundary = b''.join(
                bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding='utf-8'
                )
                for i in range(16)
            )
            while boundary in data:
                boundary += bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding='utf-8'
                )
            self._boundary = boundary
        return self._boundary

    @property
    def data(self):
        # type: (bytes) -> None
        if self.parts:
            data = (b'\r\n--' + self.boundary + b'\r\n').join(
                [self._data or b''] +
                [bytes(p).rstrip() for p in self.parts]
            ) + (b'\r\n--' + self.boundary + b'--')
        else:
            data = self._data
        return data

    @data.setter
    def data(self, data):
        return Data.data.__set__(self, data)

    @property
    def parts(self):
        # type: (...) -> Parts
        return self._parts

    @parts.setter
    def parts(self, parts):
        # type: (Optional[Sequence[Part]]) -> None
        if parts is None:
            parts = Parts([], request=self)
        elif isinstance(parts, Parts):
            parts.request = self
        else:
            parts = Parts(parts, request=self)
        self._boundary = None
        self._parts = parts


class Parts(list):

    def __init__(self, items, request):
        # type: (typing.Sequence[Part], MultipartRequest) -> None
        self.request = request
        super().__init__(items)

    def append(self, item):
        # type: (Part) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().append(item)

    def clear(self):
        # type: (...) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().clear()

    def extend(self, items):
        # type: (Iterable[Part]) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().extend(items)

    def reverse(self):
        # type: (...) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().reverse()

    def __delitem__(self, key):
        # type: (str) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().__delitem__(key)

    def __setitem__(self, key, value):
        # type: (str) -> None
        self.request._boundary = None
        self.request._bytes = None
        super().__setitem__(key, value)


class Request(Data, urllib.request.Request):
    """
    A sub-class of `urllib.request.Request` which accommodates additional data types, and serializes `data` in
    accordance with what is indicated by the request's "Content-Type" header.
    """

    def __init__(
        self,
        url,
        data=None,  # type: Optional[Union[bytes, str, Sequence, Set, dict, Model]]
        headers=None,  # type: Optional[Dict[str, str]]
        origin_req_host=None,  # type: Optional[str]
        unverifiable=False,  # type: bool
        method=None  # type: Optional[str]
    ):
        # type: (...) -> None
        self._bytes = None  # type: Optional[bytes]
        self._headers = None
        self._data = None
        self.headers = headers
        urllib.request.Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method
        )


class MultipartRequest(Part, Request):
    """
    A sub-class of `Request` which adds a property (and initialization parameter) to hold the `parts` of a
    multipart request.

    https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
    """

    def __init__(
        self,
        url,
        data=None,  # type: Optional[Union[bytes, str, Sequence, Set, dict, Model]]
        headers=None,  # type: Optional[Dict[str, str]]
        origin_req_host=None,  # type: Optional[str]
        unverifiable=False,  # type: bool
        method=None,  # type: Optional[str]
        parts=None  # type: Optional[Sequence[Part]]
    ):
        # type: (...) -> None
        Part.__init__(
            self,
            data=data,
            headers=headers,
            parts=parts
        )
        Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method
        )
