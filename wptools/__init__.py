"""
Wikipedia Tools library

Get the plain text, wikitext, HTML, or parse tree of an article via
MediaWiki API. You may get the whole article in those formats, just
the "lead" section (summary), or just the Infobox (if extant).
"""

__author__ = "Archer4499(originally by siznax)"
__contact__ = "https://github.com/Archer4499/m4a_tagger"  # Originally: https://github.com/siznax/wptools
__license__ = "MIT"
__title__ = "wptools"
__version__ = "0.0.2a"

from .extract import get_infobox, parsetree
from .fetch import WPToolsFetch, get_parsetree
