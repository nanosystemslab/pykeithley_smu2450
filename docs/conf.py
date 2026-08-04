"""Sphinx configuration."""

project = "PyKeithley_SMU2450"
author = "Nanosystems Lab"
copyright = "2026, Nanosystems Lab"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxarg.ext",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
