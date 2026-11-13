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
        crawl("https://club.test/start", client)

    assert paths == ["/start", "/about", "/help", "/team"]


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
        crawl("https://club.test/old", client)

    assert paths == ["/old", "/docs/", "/docs/notes"]


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
