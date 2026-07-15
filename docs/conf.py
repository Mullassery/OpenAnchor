# Configuration file for Sphinx documentation builder
# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath('..'))

project = 'OpenAnchor'
copyright = '2026, Georgi Mammen Mullassery'
author = 'Georgi Mammen Mullassery'
release = '0.1.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Google-style docstrings
    'sphinx.ext.viewcode',  # Link to source code
    'sphinx.ext.intersphinx',  # Link to other docs
    'myst_parser',  # Markdown support
]

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_method = True
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

# Theme
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': 'view',
    'style_nav_header_background': '#2980B9',
}

# HTML output options
html_static_path = ['_static']
html_logo = None
html_title = f'{project} v{release} Documentation'

# Source files
source_suffix = {
    '.rst': None,
    '.md': 'myst-nb',
}

# Pygments style
pygments_style = 'sphinx'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# MyST parser config
myst_enable_extensions = ['colon_fence', 'html_image']

# Master document
master_doc = 'index'
