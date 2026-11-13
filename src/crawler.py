from .checker import check_url
from .parser import extract_links
from .structures.hash_set import HashSet
from .structures.queue import Queue
from .urls import same_origin, validate_start_url


def crawl(start_url, client):
    start_url = validate_start_url(start_url)
    queue = Queue()
    scheduled = HashSet()

    def schedule(url):
        if not scheduled.contains(url):
            scheduled.add(url)
            queue.enqueue(url)

    schedule(start_url)

    while not queue.is_empty():
        url = queue.dequeue()
        result, html = check_url(url, client)
        if html is None:
            continue

        for link in extract_links(html, result["final_url"]):
            if same_origin(start_url, link):
                schedule(link)
