from .checker import check_url
from .parser import extract_links
from .robots import Robots
from .structures.directed_graph import DirectedGraph
from .structures.hash_map import HashMap
from .structures.hash_set import HashSet
from .structures.queue import Queue
from .urls import same_origin, validate_start_url


def crawl(start_url, client):
    start_url = validate_start_url(start_url)
    robots = Robots(client)
    queue = Queue()
    scheduled = HashSet()
    results = HashMap()
    graph = DirectedGraph()
    graph.add_vertex(start_url)

    def schedule(url):
        if not scheduled.contains(url):
            scheduled.add(url)
            queue.enqueue(url)

    schedule(start_url)

    while not queue.is_empty():
        url = queue.dequeue()
        result, html = check_url(url, client, robots)
        results.put(url, result)
        final_url = result["final_url"]
        graph.add_vertex(final_url)
        if html is None:
            continue

        for link in extract_links(html, final_url):
            graph.add_edge(final_url, link)
            if same_origin(start_url, link):
                schedule(link)

    return graph, results
