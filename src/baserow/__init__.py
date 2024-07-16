"""
.. include:: ../../README.md
   :start-after: baserowdantic
"""

import atexit
from importlib import util as importlib_util

# Tweaks the rendering of the documentation's table of contents to show three
# levels deep.
if importlib_util.find_spec("pdoc") is not None:
    from pdoc import render_helpers
    render_helpers.markdown_extensions["toc"]["depth"] = 3
