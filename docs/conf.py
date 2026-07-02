import os
import sys

sys.path.insert(0, os.path.abspath('..'))

import bonzo

project = 'Bonzo'
author = 'Jorge Puente Sarrín'
copyright = '2014, Jorge Puente Sarrín'
version = bonzo.version
release = bonzo.version

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
]

templates_path = ['_templates']
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = f'{project}{release.replace(".", "_")}'

latex_documents = [
    ('index', f'{project}.tex', f'{project} Documentation', author, 'manual'),
]
man_pages = [
    ('index', project.lower(), f'{project} Documentation', [author], 1),
]
texinfo_documents = [
    (
        'index',
        project,
        f'{project} Documentation',
        author,
        project,
        'SMTP server built on top of Tornado.',
        'Miscellaneous',
    ),
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'tornado': ('https://www.tornadoweb.org/en/stable/', None),
}

extlinks = {
    'gh-user': ('https://github.com/%s', '@%s'),
    'issue': ('https://github.com/puentesarrin/bonzo/issues/%s', '#%s'),
}
