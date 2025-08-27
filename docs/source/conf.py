# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'atlantic-signatures'
copyright = '2025, Luc Tourangeau, Jeffrey Gill'
author = 'Luc Tourangeau, Jeffrey Gill'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinxcontrib.programoutput',
    'sphinxcontrib.video',
]

autodoc_default_options = {
    'members': True,
    'private-members': True,  # include members starting with an underscore
}

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://alabaster.readthedocs.io/en/latest/customization.html

html_theme = 'alabaster'
html_theme_options = {
    'description': 'Bioinspired magnetic navigation software for the iRobot '
                   'Create 2 and Vicon motion capture',
    'description_font_style': 'italic',
    'font_family': 'Arial',
    'page_width': '1200px',  # default is 940
    'sidebar_width': '280px',  # default is 220
    'show_relbars': True,
    'fixed_sidebar': True,
}
html_static_path = ['_static']
