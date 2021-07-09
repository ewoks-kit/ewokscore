"""rm -rf doc/_generated/; python setup.py build_sphinx -E -a
"""

from ewokscore import __version__  # noqa E402

copyright = "2021, ESRF"
author = "ESRF"
release = ".".join(__version__.split(".")[:2])
version = __version__

extensions = ["sphinx.ext.autodoc", "sphinx.ext.autosummary"]
templates_path = ["_templates"]
exclude_patterns = []

html_theme = "alabaster"
html_static_path = []

autosummary_generate = True
autodoc_default_flags = [
    "members",
    "undoc-members",
    "show-inheritance",
]
