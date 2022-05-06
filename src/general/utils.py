import codecs
import re

import translitcodec  # noqa: F401
from slugify import slugify as python_slugify

from django.conf import settings

PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, separator='-', style=None):
    """Generate different types of slugs.

    The following types are supported:

    * default
    * unicode - allow unicode characters
    * translit - use translitcodec translit/long
    """
    if style is None:
        style = settings.DEFAULT_SLUGIFY_STYLE

    if style == 'translit':
        result = []
        for word in PUNCT_RE.split(text.lower()):
            word = codecs.encode(word, 'translit/long')
            if word:
                result.append(word)
        return python_slugify(separator.join(result))
    elif style == 'unicode':
        return python_slugify(text, separator=separator, allow_unicode=True)
    else:
        return python_slugify(text)
