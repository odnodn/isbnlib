# -*- coding: utf-8 -*-
"""Query the openlibrary.org service for metadata."""

import logging
import re

from .dev import stdmeta
from .dev._bouth23 import u
from .dev._exceptions import RecordMappingError
from .dev.webquery import query as wquery

UA = 'isbnlib (gzip)'
SERVICE_URL = ('http://openlibrary.org/api/books?bibkeys='
               'ISBN:{isbn}&format=json&jscmd=data')
LOGGER = logging.getLogger(__name__)


# pylint: disable=broad-except
def _mapper(isbn, records):
    """Map canonical <- records."""
    # canonical:
    # -> ISBN-13, Title, Authors, Publisher, Year, Language
    try:
        # mapping: canonical <- records
        canonical = {}
        canonical['ISBN-13'] = u(isbn)
        title = records.get('title', u('')).replace(' :', ':')
        subtitle = records.get('subtitle', u(''))
        title = title + ' - ' + subtitle if subtitle else title
        canonical['Title'] = title
        # canonical['Title'] = records.get('title', u('')).replace(' :', ':')
        canonical['Authors'] = [
            a['name'] for a in records.get('authors', ({
                'name': u(''),
            }, ))
        ]
        canonical['Publisher'] = records.get('publishers', [
            {
                'name': u(''),
            },
        ])[0]['name']
        canonical['Year'] = u('')
        strdate = records.get('publish_date', u(''))
        if strdate:  # pragma: no cover
            match = re.search(r'\d{4}', strdate)
            if match:
                canonical['Year'] = match.group(0)
    except Exception:  # pragma: no cover
        LOGGER.debug('RecordMappingError for %s with data %s', isbn, records)
        raise RecordMappingError(isbn)
    # call stdmeta for extra cleanning and validation
    return stdmeta(canonical)


# pylint: disable=broad-except
def _records(isbn, data):
    """Classify (canonically) the parsed data."""
    try:
        # put the selected data in records
        records = data['ISBN:%s' % isbn]
    except Exception:  # pragma: no cover
        # don't raise exception!
        LOGGER.debug('No data from "openl" for isbn %s', isbn)
        return {}

    # map canonical <- records
    return _mapper(isbn, records)


def query(isbn):
    """Query the openlibrary.org service for metadata."""
    data = wquery(SERVICE_URL.format(isbn=isbn), user_agent=UA)
    return _records(isbn, data)
