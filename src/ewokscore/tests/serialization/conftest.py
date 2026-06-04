import pytest

pytest.register_assert_rewrite(
    "ewokscore.tests.serialization.example_data.compare_json"
)
pytest.register_assert_rewrite(
    "ewokscore.tests.serialization.example_data.compare_hdf5"
)
