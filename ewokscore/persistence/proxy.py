from typing import Any, Union, Optional
from urllib.parse import ParseResult

from .uri import parse_uri
from ..registration import Registered
from ..hashing import UniversalHashable
from ..hashing import UniversalHash


class PersistencyError(RuntimeError):
    pass


class UriNotFoundError(PersistencyError):
    pass


class DataUri:
    def __init__(self, uri: str, uhash: Union[UniversalHash, str]):
        self.__uri = uri
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
        return str(self) == str(other)

    @property
    def uhash(self):
        return self.__uhash

    def serialize(self):
        return {"uri": self.__uri, "uhash": str(self.uhash)}

    @classmethod
    def deserialize(cls, data):
        return cls(data["uri"], data["uhash"])


class DataProxy(Registered, register=False):
    SCHEME = NotImplemented

    def __init__(
        self,
        source: Union[UniversalHash, UniversalHashable, DataUri],
        root_uri: Optional[str] = None,
    ):
        """
        :param source:
        :param root_uri: is not used when the source is of type `DataUri`
        """
        self.__source = source
        if root_uri is None or self.fixed_uri:
            self._root_uri = None
        else:
            self._root_uri = parse_uri(root_uri, default_scheme=self.SCHEME)

    def __repr__(self):
        uri = self.uri
        if uri is None:
            return super().__repr__()
        else:
            return f"{super().__repr__()}(uri='{uri}')"

    @classmethod
    def instantiate(cls, scheme, *args, **kw):
        for subclass in cls.get_subclasses():
            if subclass.SCHEME == scheme:
                return subclass(*args, **kw)

    @property
    def uhash(self) -> Union[None, UniversalHash]:
        if isinstance(self.__source, UniversalHash):
            return self.__source
        return self.__source.uhash

    @property
    def _identifier(self) -> Union[None, str]:
        uhash = self.uhash
        if uhash is None:
            return None
        else:
            return str(uhash)

    @property
    def fixed_uri(self) -> bool:
        return isinstance(self.__source, DataUri)

    @property
    def uri(self) -> Union[None, DataUri]:
        if self.fixed_uri:
            return self.__source
        else:
            return self._generate_uri()

    def _generate_uri(self) -> Union[None, DataUri]:
        raise NotImplementedError

    def exists(self) -> bool:
        raise NotImplementedError

    def load(self, raise_error: bool = True) -> Any:
        raise NotImplementedError

    def dump(self, data: Any) -> bool:
        raise NotImplementedError
