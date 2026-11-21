import threading

import pytest

from ...requirements import clear_requirements_cache
from ...requirements import generate_requirements
from ...requirements._utils import base_manager
from ...requirements._utils.cache import ProcessCache
from .utils import DISTRIBUTIONS
from .utils import PYTHON_VERSION
from .utils import current_metadata


def test_process_cache_computes_once():
    cache = ProcessCache()
    calls = []

    def compute():
        calls.append(None)
        return {"a": [1]}

    assert cache.get("key", compute) == {"a": [1]}
    assert cache.get("key", compute) == {"a": [1]}
    assert len(calls) == 1

    cache.clear()
    assert cache.get("key", compute) == {"a": [1]}
    assert len(calls) == 2


def test_process_cache_returns_copies():
    cache = ProcessCache()
    value = cache.get("key", lambda: {"a": [1]})
    value["a"].append(2)
    assert cache.get("key", lambda: {"a": []}) == {"a": [1]}


def test_process_cache_does_not_cache_exceptions():
    cache = ProcessCache()

    def fail():
        raise RuntimeError("generation failed")

    with pytest.raises(RuntimeError, match="generation failed"):
        cache.get("key", fail)
    assert cache.get("key", lambda: 1) == 1


def test_process_cache_concurrent_callers_compute_once():
    cache = ProcessCache()
    started = threading.Event()
    release = threading.Event()
    calls = []

    def compute():
        calls.append(None)
        started.set()
        assert release.wait(timeout=10)
        return "value"

    results = []

    def caller():
        results.append(cache.get("key", compute))

    threads = [threading.Thread(target=caller) for _ in range(4)]
    threads[0].start()
    assert started.wait(timeout=10)
    for thread in threads[1:]:
        thread.start()
    release.set()
    for thread in threads:
        thread.join(timeout=10)

    assert results == ["value"] * 4
    assert len(calls) == 1


def test_process_cache_clear_during_computation():
    cache = ProcessCache()

    def compute():
        cache.clear()  # e.g. distributions installed while generating
        return "stale"

    assert cache.get("key", compute) == "stale"
    assert cache.get("key", lambda: "fresh") == "fresh"


def _count_gathering(monkeypatch) -> list:
    metadata = current_metadata(DISTRIBUTIONS, PYTHON_VERSION)
    monkeypatch.setattr(base_manager, "current_requirements", lambda: metadata)
    calls = []
    gather_requirements = base_manager.BaseManager.gather_requirements

    def counted(self):
        calls.append(self.NAME)
        return gather_requirements(self)

    monkeypatch.setattr(base_manager.BaseManager, "gather_requirements", counted)
    return calls


def test_generate_requirements_cached(monkeypatch):
    calls = _count_gathering(monkeypatch)

    first = generate_requirements(manager_name="pip-venv", bootstrap={"ewoks": "7"})
    second = generate_requirements(manager_name="pip-venv")

    assert calls == ["pip-venv"]
    # The bootstrap of one caller is not cached for the next one
    assert first["bootstrap"] == {"distributions": {"ewoks": "7"}}
    assert second["bootstrap"] is None
    assert {k: v for k, v in first.items() if k != "bootstrap"} == {
        k: v for k, v in second.items() if k != "bootstrap"
    }

    clear_requirements_cache()
    generate_requirements(manager_name="pip-venv")
    assert calls == ["pip-venv", "pip-venv"]
