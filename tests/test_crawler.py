import httpx

from src.crawler import crawl


def test_crawls_in_breadth_first_order():
    pages = {
        "/start": '<a href="/about">About</a><a href="/help">Help</a>'
        '<a href="https://other.test/outside">Outside</a>',
        "/about": '<a href="/team">Team</a>',
        "/help": "",
        "/team": "",
    }
    paths = []

    def handler(request):
        assert request.url.host == "club.test"
        paths.append(request.url.path)
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text=pages[request.url.path],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl("https://club.test/start", client)

    assert paths == ["/start", "/about", "/help", "/team"]
    assert graph.has_edge("https://club.test/start", "https://other.test/outside")


def test_crawls_relative_links_from_final_url():
    paths = []

    def handler(request):
        path = request.url.path
        paths.append(path)
        if path == "/old":
            return httpx.Response(302, headers={"Location": "/docs/"})
        if path == "/docs/":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text='<a href="notes">Notes</a>',
            )
        return httpx.Response(200, headers={"Content-Type": "application/pdf"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl("https://club.test/old", client)

    assert paths == ["/old", "/docs/", "/docs/notes"]
    assert graph.edges() == [("https://club.test/docs/", "https://club.test/docs/notes")]
    assert "https://club.test/old" in graph.vertices()


def test_duplicate_anchors_and_cycles_are_checked_once_per_crawl():
    pages = {
        "/a": '<a href="/b">B</a><a href="/b">B again</a><a href="/b#top">Top</a>',
        "/b": '<a href="/a">Back to A</a>',
    }
    paths = []

    def handler(request):
        assert request.method == "GET"
        path = request.url.path
        assert path not in paths
        paths.append(path)
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text=pages[path],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        for _ in range(2):
            paths.clear()
            crawl("https://CLUB.test:443/a#start", client)
            assert paths == ["/a", "/b"]


def test_different_query_values_are_separate_jobs():
    urls = []

    def handler(request):
        urls.append(str(request.url))
        html = ""
        if request.url.path == "/start":
            html = '<a href="/search?q=one">One</a><a href="/search?q=two">Two</a>'
        if request.url.params.get("q") == "one":
            html = '<a href="/search?q=two#again">Two again</a>'
        return httpx.Response(200, headers={"Content-Type": "text/html"}, text=html)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        crawl("https://club.test/start", client)

    assert urls == [
        "https://club.test/start",
        "https://club.test/search?q=one",
        "https://club.test/search?q=two",
    ]


def test_records_both_sources_for_one_missing_url():
    pages = {
        "/start": '<a href="/guide.html">Guide</a><a href="/faq.html">FAQ</a>',
        "/guide.html": '<a href="/missing">Link</a><a href="/missing#top">Again</a>',
        "/faq.html": '<a href="/missing">Link</a>',
    }
    paths = []

    def handler(request):
        path = request.url.path
        paths.append(path)
        if path == "/missing":
            return httpx.Response(404)
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text=pages[path],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl("https://club.test/start", client)

    missing_url = "https://club.test/missing"
    edges_to_missing = [edge for edge in graph.edges() if edge[1] == missing_url]
    assert sorted(edges_to_missing) == [
        ("https://club.test/faq.html", missing_url),
        ("https://club.test/guide.html", missing_url),
    ]
    assert paths == ["/start", "/guide.html", "/faq.html", "/missing"]


def test_results_keep_original_urls_after_redirects_and_missing_pages():
    paths = []

    def handler(request):
        path = request.url.path
        paths.append(path)
        if path == "/old":
            return httpx.Response(302, headers={"Location": "/manual/"})
        if path == "/manual/":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text='<a href="/missing">Missing</a>',
            )
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl("https://CLUB.test:443/old#top", client)

    assert paths == ["/old", "/manual/", "/missing"]
    assert results.get("https://club.test/old") == {
        "requested_url": "https://club.test/old",
        "final_url": "https://club.test/manual/",
        "status_code": 200,
        "category": "ok",
        "reason": "Request succeeded",
    }
    assert not results.contains("https://club.test/manual/")
    missing = results.get("https://club.test/missing")
    assert missing["status_code"] == 404
    assert missing["category"] == "broken"
    assert graph.has_edge("https://club.test/manual/", "https://club.test/missing")
    assert results.size() == 2
    assert len(results.items()) == 2
    assert paths == ["/old", "/manual/", "/missing"]


def test_results_are_independent_between_scans():
    requests = []

    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, headers={"Content-Type": "text/html"}, text="")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first_graph, first_results = crawl("https://club.test/first", client)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        second_graph, second_results = crawl("https://club.test/second", client)

    assert first_results is not second_results
    assert first_results.keys() == ["https://club.test/first"]
    assert second_results.keys() == ["https://club.test/second"]
    assert first_graph.vertices() == ["https://club.test/first"]
    assert second_graph.vertices() == ["https://club.test/second"]
    assert requests == ["https://club.test/first", "https://club.test/second"]


def test_results_keep_failed_requests_without_html():
    def handler(request):
        raise httpx.ReadTimeout("Timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl("https://club.test/slow", client)

    result = results.get("https://club.test/slow")
    assert result["status_code"] is None
    assert result["category"] == "unverified"
    assert result["reason"] == "Request timed out"
    assert results.size() == 1
    assert graph.edges() == []
