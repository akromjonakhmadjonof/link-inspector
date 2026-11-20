from time import monotonic, sleep

from .checker import check_url
from .parser import extract_links
from .robots import Robots
from .structures.directed_graph import DirectedGraph
from .structures.hash_map import HashMap
from .structures.hash_set import HashSet
from .structures.min_heap import MinHeap
from .structures.queue import Queue
from .urls import same_origin, validate_start_url


def get_retry_delay(result):
    if not result["retryable"]:
        return None
    if result["retry_after"] is None:
        return 1.0
    try:
        delay = float(result["retry_after"])
    except ValueError:
        return None
    if 0 <= delay <= 5:
        return delay
    return None


def crawl(start_url, client):
    start_url = validate_start_url(start_url)
    site_url = start_url
    robots = Robots(client)
    queue = Queue()
    retries = MinHeap()
    scheduled = HashSet()
    results = HashMap()
    graph = DirectedGraph()
    graph.add_vertex(start_url)

    def schedule(url):
        if not scheduled.contains(url):
            scheduled.add(url)
            queue.enqueue(url)

    schedule(start_url)

    while not queue.is_empty() or not retries.is_empty():
        retrying = False
        if not retries.is_empty() and retries.peek()[0] <= monotonic():
            due_time, url = retries.pop()
            retrying = True
        elif not queue.is_empty():
            url = queue.dequeue()
        else:
            sleep(max(0, retries.peek()[0] - monotonic()))
            continue

        result, html = check_url(url, client, robots)
        results.put(url, result)
        if not retrying:
            delay = get_retry_delay(result)
            if delay is not None:
                retries.push((monotonic() + delay, url))
        final_url = result["final_url"]
        graph.add_vertex(final_url)
        if url == start_url and result["category"] == "ok":
            site_url = final_url
        if html is None:
            continue
        if url != start_url and (
            not same_origin(url, site_url) or not same_origin(final_url, site_url)
        ):
            continue

        for link in extract_links(html, final_url):
            graph.add_edge(final_url, link)
            schedule(link)

    return graph, results
