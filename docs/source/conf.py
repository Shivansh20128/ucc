import os
import sys

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../../"))
sys.path.insert(0, os.path.abspath("../../../"))

from ucc._version import __version__


project = "ucc"
copyright = "2024, Unitary Foundation"
author = "Unitary Foundation"
directory_of_this_file = os.path.dirname(os.path.abspath(__file__))
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "myst_parser",
    "sphinx.ext.doctest",
]
# Suppress warnings related to heading levels
suppress_warnings = ["myst.header"]

# Optionally, enable cross-referencing for `.rst` files as well
myst_crossref = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = [
    ".rst",
    ".md",
]  # Allow Sphinx to process both .rst and .md files


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = []
