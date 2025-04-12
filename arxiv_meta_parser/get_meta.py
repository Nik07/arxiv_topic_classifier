import logging
from arxiv import Result
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_paper_meta(entry: Result) -> dict:
    try:
        entry = {
            'author': [{'name': author.name} for author in entry.authors],
            'day': entry.published.day,
            'id': entry.entry_id.split('/')[-1],
            'link': [
                {'rel': 'alternate', 'href': entry.entry_id, 'type': 'text/html'},
                {'rel': 'related', 'href': entry.pdf_url, 'type': 'application/pdf', 'title': 'pdf'}
            ],
            'month': entry.published.month,
            'summary': entry.summary,
            'tag': [{'term': category, 'scheme': 'http://arxiv.org/schemas/atom', 'label': None} 
                   for category in entry.categories],
            'title': entry.title,
            'year': entry.published.year
        }
        return entry
    except Exception as e:
        logger.error(e)
        return None