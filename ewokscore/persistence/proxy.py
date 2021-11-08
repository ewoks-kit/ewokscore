import numpy
from typing import Any, Dict, Union, Optional
from urllib.parse import ParseResult

from .uri import parse_query, parse_uri, join_uri, uri_as_string
from ..registration import Registered
from ..hashing import UniversalHash
from ..hashing import HasUhash


class PersistenceError(RuntimeError):
    pass


class UriNotFoundError(PersistenceError):
    pass


class DataUri(HasUhash):
    def __init__(self, uri: str, uhash: Union[UniversalHash, str]):
        if isinstance(uri, numpy.ndarray):
            uri = uri.item()
        if isinstance(uhash, numpy.ndarray):
            uhash = uhash.item()
        self.__uri = uri_as_string(uri)
        if isinstance(uhash, str):
            uhash = UniversalHash(uhash)
        self.__uhash = uhash

    def __repr__(self):
        return f"{type(self).__name__}({self.__uri})"

    def __str__(self):
        return self.__uri

    def parse(self) -> ParseResult:
        return parse_uri(self.__uri)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == str(other)
        elif isinstance(other, DataUri):
            return str(self) == str(other) and self.uhash == other.uhash
        else:
            return False

    def __copy__(self):
        return type(self)(self.__uri, self.__uhash)

    @property
    def uhash(self) -> UniversalHash:
        return self.__uhash

    def serialize(self) -> Dict[str, str]:
        return {"uri": self.__uri, "uhash": str(self.uhash)}

    @classmethod
    def deserialize(cls, data: Dict[str, str]):
        if not isinstance(data, dict):
            return None
        try:
            uri = data["uri"]
            uhash = data["uhash"]
        except KeyError:
            return None
        return cls(uri, uhash)


class DataProxy(Registered, HasUhash, register=False):
    SCHEME = NotImplemented
    """name of the DataProxy scheme like json or nexus"""

    def __init__(
        self,
        uri: Optional[DataUri] = None,
        root_uri: Optional[str] = None,
        relative_uri: Optional[str] = None,
        uhash_source: Optional[Union[UniversalHash, HasUhash]] = None,
    ):
        """Either the URI is provided or the root + relative URI with a uhash source (the URI can be derived from those)"""
        self.__parsed_root_uri = None
        self.__fixed_uri = uri
        self.__uhash_source = uri
        if uri is None:
            self.__uhash_source = uhash_source
        else:
            root_uri = str(uri)
            relative_uri = None
        if root_uri:
            parsed_root_uri = parse_uri(root_uri)
            if relative_uri:
                parsed_root_uri = join_uri(parsed_root_uri, relative_uri)
            self.__parsed_root_uri = parsed_root_uri

    def __repr__(self):
        uri = self.uri
        if uri is None:
            return super().__repr__()
        else:
            return f"{super().__repr__()}(uri='{uri}')"

    @classmethod
    def instantiate(
        cls,
        scheme: Optional[str] = None,
        uri: Optional[DataUri] = None,
        uhash_source: Optional[Union[UniversalHash, HasUhash]] = None,
        root_uri: Optional[str] = None,
        relative_uri: Optional[str] = None,
    ):
        if uri is not None:
            scheme = uri.parse().scheme
        elif isinstance(root_uri, DataProxy):
            scheme = root_uri.SCHEME
        elif isinstance(root_uri, DataUri):
            scheme = root_uri.parse().scheme
        for subclass in cls.get_subclasses():
            if subclass.SCHEME == scheme:
                return subclass(
                    uri=uri,
                    uhash_source=uhash_source,
                    root_uri=root_uri,
                    relative_uri=relative_uri,
                )
        raise ValueError(f"Data proxy scheme '{scheme}' is not supported")

    def serialize(self) -> Dict[str, str]:
        return self.uri.serialize()

    @classmethod
    def deserialize(self, data: Dict[str, str]):
        uri = DataUri.deserialize(data)
        if uri is None:
            return None
        return self.instantiate(uri=uri)

    @property
    def uhash(self) -> Optional[UniversalHash]:
        if self.is_fixed_uri:
            return self.__fixed_uri.uhash
        elif isinstance(self.__uhash_source, HasUhash):
            return self.__uhash_source.uhash
        elif isinstance(self.__uhash_source, UniversalHash):
            return self.__uhash_source
        else:
            return None

    @property
    def identifier(self) -> Optional[str]:
        """Return identifier DataProxy to be used as a string"""
        uhash = self.uhash
        if uhash is None:
            return None
        return str(uhash)

    @property
    def parsed_root_uri(self) -> Optional[ParseResult]:
        return self.__parsed_root_uri

    @property
    def root_uri_query(self) -> dict:
        parsed_root_uri = self.parsed_root_uri
        if parsed_root_uri:
            return parse_query(parsed_root_uri)
        return dict()

    @property
    def is_fixed_uri(self) -> bool:
        return self.__fixed_uri is not None

    @property
    def uri(self) -> Optional[DataUri]:
        """
        Return an Unified Resource Identifier. Defined as:
        URI = scheme ":" "//" path ["?" query] ["#" fragment]

        see https://en.wikipedia.org/wiki/Uniform_Resource_Identifier

        .. warning:: query can be ?path= which is different from path
        """
        if self.is_fixed_uri:
            return self.__fixed_uri
        return self._generate_uri()

    def _generate_uri(self) -> Optional[DataUri]:
        """Generate a URI based on the root URI and the universal hash"""
        raise NotImplementedError

    def exists(self) -> bool:
        """return True if the data exists"""
        raise NotImplementedError

    def load(self, raise_error: bool = True) -> Any:
        """Load data from the uri"""
        raise NotImplementedError

    def dump(self, data: Any) -> bool:
        """Dump data to the uri"""
        raise NotImplementedError
