from bs4 import BeautifulSoup

from .urls import resolve_url


def extract_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    base_url = page_url
    for base in soup.find_all("base", href=True):
        resolved_base = resolve_url(base["href"], page_url)
        if resolved_base is not None:
            base_url = resolved_base
            break

    links = []
    for anchor in soup.find_all("a", href=True):
        url = resolve_url(anchor["href"], base_url)
        if url is not None:
            links.append(url)
    return links
