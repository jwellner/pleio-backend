import bs4

from core.utils.html_to_draftjs.converter import SoupConverter
from purifier.purifier import HTMLPurifier

def html_to_draftjs(html, features="lxml", strict=False):

    # first cleanup HTML with only the following allowed tags:
    purifier = HTMLPurifier({
        'p': ['*'],
        'ul': ['*'],
        'ol': ['*'],
        'li': ['*'],
        'img': ['*'],
        'a': ['*'],
        'blockquote': ['*'],
        'pre': ['*'],
        'h1': ['*'],
        'h2': ['*'],
        'h3': ['*'],
        'h4': ['*'],
        'h5': ['*'],
        'h6': ['*'],
        'strong': ['*'],
        'br':['*'],
        'div':['*']
    })
    html = purifier.feed(html)

    soup = bs4.BeautifulSoup(html, features)
    return SoupConverter(strict=strict).convert(soup).to_dict()


def soup_to_draftjs(soup: bs4.BeautifulSoup, strict=False):
    return SoupConverter(strict=strict).convert(soup).to_dict()
