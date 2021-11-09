import os
from pathlib import Path
from ewokscore.persistence.uri import parse_uri
from ewokscore.persistence.uri import path_from_uri
from ewokscore.persistence.uri import parse_query


def test_file_uri():
    nonpath = str(Path("file.h5"))
    relpath = str(Path("relpath") / "file.h5")
    abspath = str(Path(os.path.sep) / "abspath" / "file.h5")
    assert not os.path.isabs(nonpath)
    assert not os.path.isabs(relpath)
    assert os.path.isabs(abspath)

    uri = nonpath
    assert parse_uri(uri).geturl() == "file:///file.h5"
    assert str(path_from_uri(parse_uri(uri))) == uri
    assert parse_query(parse_uri(uri)) == dict()

    uri = relpath
    assert parse_uri(uri).geturl() == "file:///relpath/file.h5"
    assert str(path_from_uri(parse_uri(uri))) == uri
    assert parse_query(parse_uri(uri)) == dict()

    uri = abspath
    assert parse_uri(uri).geturl() == "file:///abspath/file.h5"
    assert str(path_from_uri(parse_uri(uri))) == uri
    assert parse_query(parse_uri(uri)) == dict()

    uri = nonpath + "::/entry"
    assert parse_uri(uri).geturl() == "file:///file.h5?path=/entry"
    assert str(path_from_uri(parse_uri(uri))) == nonpath
    assert parse_query(parse_uri(uri)) == {"path": "/entry"}

    uri = relpath + "::/entry"
    assert parse_uri(uri).geturl() == "file:///relpath/file.h5?path=/entry"
    assert str(path_from_uri(parse_uri(uri))) == relpath
    assert parse_query(parse_uri(uri)) == {"path": "/entry"}

    uri = abspath + "::/entry"
    assert parse_uri(uri).geturl() == "file:///abspath/file.h5?path=/entry"
    assert str(path_from_uri(parse_uri(uri))) == abspath
    assert parse_query(parse_uri(uri)) == {"path": "/entry"}

    uri = abspath + "::/entry?name=abc"
    assert parse_uri(uri).geturl() == "file:///abspath/file.h5?path=/entry&name=abc"
    assert str(path_from_uri(parse_uri(uri))) == abspath
    assert parse_query(parse_uri(uri)) == {"path": "/entry", "name": "abc"}

    uri = abspath + "::/entry?path=xyz&name=abc"
    assert parse_uri(uri).geturl() == "file:///abspath/file.h5?path=/entry/xyz&name=abc"
    assert str(path_from_uri(parse_uri(uri))) == abspath
    assert parse_query(parse_uri(uri)) == {"path": "/entry/xyz", "name": "abc"}
