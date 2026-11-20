import httpx

from src.crawler import crawl


SITE = "https://akhmadjonoff.uz"
WWW_SITE = "https://www.akhmadjonoff.uz"


def run_crawl(pages, start_url=SITE + "/"):
    requests = []

    def handler(request):
        url = str(request.url)
        requests.append(url)
        if request.url.path == "/robots.txt" and url not in pages:
            return httpx.Response(404)
        page = pages[url]
        if isinstance(page, str):
            return httpx.Response(200, headers={"Content-Type": "text/html"}, text=page)
        return page

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"User-Agent": "CourseLinkChecker"},
    ) as client:
        graph, results = crawl(start_url, client)
    return graph, results, requests


def test_breadth_first_order():
    pages = {
        SITE + "/": '<a href="/about">About</a><a href="/help">Help</a>',
        SITE + "/about": '<a href="/team">Team</a>',
        SITE + "/help": "",
        SITE + "/team": "",
    }

    graph, results, requests = run_crawl(pages)

    assert requests == [
        SITE + "/robots.txt", SITE + "/", SITE + "/about",
        SITE + "/help", SITE + "/team",
    ]


def test_relative_links_after_redirect():
    pages = {
        SITE + "/old": httpx.Response(302, headers={"Location": "/docs/"}),
        SITE + "/docs/": '<a href="notes">Notes</a>',
        SITE + "/docs/notes": "",
    }

    graph, results, requests = run_crawl(pages, SITE + "/old")

    assert requests == [
        SITE + "/robots.txt", SITE + "/old", SITE + "/docs/", SITE + "/docs/notes",
    ]
    assert graph.edges() == [(SITE + "/docs/", SITE + "/docs/notes")]
    assert SITE + "/old" in graph.vertices()


def test_duplicate_links_and_cycles():
    pages = {
        SITE + "/a": '<a href="/b">B</a><a href="/b">Again</a><a href="/b#top">Top</a>',
        SITE + "/b": '<a href="/a">Back</a>',
    }

    for scan in range(2):
        graph, results, requests = run_crawl(pages, "https://AKHMADJONOFF.UZ:443/a#top")
        assert requests == [SITE + "/robots.txt", SITE + "/a", SITE + "/b"]


def test_different_queries():
    pages = {
        SITE + "/": '<a href="/search?q=one">One</a><a href="/search?q=two">Two</a>',
        SITE + "/search?q=one": '<a href="/search?q=two#top">Two again</a>',
        SITE + "/search?q=two": "",
    }

    graph, results, requests = run_crawl(pages)

    assert requests == [
        SITE + "/robots.txt", SITE + "/", SITE + "/search?q=one", SITE + "/search?q=two",
    ]


def test_two_sources_for_one_missing_page():
    pages = {
        SITE + "/": '<a href="/guide.html">Guide</a><a href="/faq.html">FAQ</a>',
        SITE + "/guide.html": '<a href="/missing">Link</a><a href="/missing#top">Again</a>',
        SITE + "/faq.html": '<a href="/missing">Link</a>',
        SITE + "/missing": httpx.Response(404),
    }

    graph, results, requests = run_crawl(pages)

    assert sorted(graph.sources(SITE + "/missing")) == [
        SITE + "/faq.html", SITE + "/guide.html",
    ]
    assert graph.edge_count == 4
    assert requests == [
        SITE + "/robots.txt", SITE + "/", SITE + "/guide.html",
        SITE + "/faq.html", SITE + "/missing",
    ]


def test_saved_results():
    pages = {
        SITE + "/old": httpx.Response(302, headers={"Location": "/manual/"}),
        SITE + "/manual/": '<a href="/missing">Missing</a>',
        SITE + "/missing": httpx.Response(404),
    }

    graph, results, requests = run_crawl(pages, "https://AKHMADJONOFF.UZ:443/old#top")
    old = results.get(SITE + "/old")
    missing = results.get(SITE + "/missing")

    assert old["requested_url"] == SITE + "/old"
    assert old["final_url"] == SITE + "/manual/"
    assert old["status_code"] == 200
    assert old["category"] == "ok"
    assert old["reason"] == "Request succeeded"
    assert old["retryable"] is False
    assert old["retry_after"] is None
    assert not results.contains(SITE + "/manual/")
    assert missing["status_code"] == 404
    assert missing["category"] == "broken"
    assert graph.has_edge(SITE + "/manual/", SITE + "/missing")
    assert results.size() == 2
    assert len(results.items()) == 2
    assert requests == [
        SITE + "/robots.txt", SITE + "/old", SITE + "/manual/", SITE + "/missing",
    ]


def test_separate_scans():
    first_graph, first_results, first_requests = run_crawl(
        {SITE + "/first": ""}, SITE + "/first"
    )
    second_graph, second_results, second_requests = run_crawl(
        {SITE + "/second": ""}, SITE + "/second"
    )

    assert first_results is not second_results
    assert first_results.keys() == [SITE + "/first"]
    assert second_results.keys() == [SITE + "/second"]
    assert first_graph.vertices() == [SITE + "/first"]
    assert second_graph.vertices() == [SITE + "/second"]
    assert first_requests == [SITE + "/robots.txt", SITE + "/first"]
    assert second_requests == [SITE + "/robots.txt", SITE + "/second"]


def test_saved_timeout():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        raise httpx.ReadTimeout("Timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl(SITE + "/slow", client)

    result = results.get(SITE + "/slow")
    assert result["status_code"] is None
    assert result["category"] == "unverified"
    assert result["reason"] == "Request timed out"
    assert results.size() == 1
    assert graph.edges() == []


def test_start_redirect_sets_the_site_origin():
    start = "http://akhmadjonoff.uz/"
    pages = {
        start: httpx.Response(301, headers={"Location": SITE + "/"}),
        SITE + "/": '<a href="/about">About</a>',
        SITE + "/about": "",
    }

    graph, results, requests = run_crawl(pages, start)

    assert requests == [
        "http://akhmadjonoff.uz/robots.txt", start,
        SITE + "/robots.txt", SITE + "/", SITE + "/about",
    ]
    assert results.get(start)["final_url"] == SITE + "/"
    assert graph.has_edge(SITE + "/", SITE + "/about")


def test_checks_the_other_origin_once():
    pages = {
        SITE + "/": '<a href="https://www.akhmadjonoff.uz/page">Page</a>'
        '<a href="https://www.akhmadjonoff.uz/page#top">Again</a>',
        WWW_SITE + "/page": '<a href="/nested">Nested</a>',
    }

    graph, results, requests = run_crawl(pages)

    assert requests == [
        SITE + "/robots.txt", SITE + "/", WWW_SITE + "/robots.txt", WWW_SITE + "/page",
    ]
    assert results.get(WWW_SITE + "/page")["category"] == "ok"
    assert graph.edges() == [(SITE + "/", WWW_SITE + "/page")]


def test_redirects_between_origins_do_not_expand_links():
    cases = [
        (SITE + "/go", WWW_SITE + "/landing"),
        (WWW_SITE + "/go", SITE + "/landing"),
    ]
    for requested_url, final_url in cases:
        pages = {
            SITE + "/": '<a href="' + requested_url + '">Go</a>',
            requested_url: httpx.Response(302, headers={"Location": final_url}),
            final_url: '<a href="/nested">Nested</a>',
        }

        graph, results, requests = run_crawl(pages)

        assert results.get(requested_url)["final_url"] == final_url
        assert graph.edges() == [(SITE + "/", requested_url)]
        assert len(requests) == 5


def test_pdf_has_no_outgoing_links():
    pages = {
        SITE + "/": '<a href="/resume.pdf">Resume</a>',
        SITE + "/resume.pdf": httpx.Response(
            200, headers={"Content-Type": "application/pdf"}, text='<a href="/nested">Link</a>'
        ),
    }

    graph, results, requests = run_crawl(pages)

    assert requests == [SITE + "/robots.txt", SITE + "/", SITE + "/resume.pdf"]
    assert results.get(SITE + "/resume.pdf")["category"] == "ok"
    assert graph.edges() == [(SITE + "/", SITE + "/resume.pdf")]


def test_robots_blocks_pages_and_redirects():
    pages = {
        SITE + "/robots.txt": httpx.Response(
            200, text="User-agent: CourseLinkChecker\nDisallow: /private"
        ),
        SITE + "/": '<a href="/private">Private</a><a href="/redirect">Redirect</a>',
        SITE + "/redirect": httpx.Response(302, headers={"Location": "/private/redirected"}),
    }

    graph, results, requests = run_crawl(pages)

    assert requests == [SITE + "/robots.txt", SITE + "/", SITE + "/redirect"]
    for path in ("/private", "/redirect"):
        result = results.get(SITE + path)
        assert result["category"] == "skipped"
        assert result["status_code"] is None
        assert result["reason"] == "Disallowed by robots.txt"
        assert graph.has_edge(SITE + "/", SITE + path)
    assert results.size() == 3


def test_missing_or_unavailable_robots_rules():
    cases = [(404, "ok"), (410, "ok"), (403, "skipped"), (503, "skipped")]
    for status, category in cases:
        pages = {
            SITE + "/robots.txt": httpx.Response(status),
            SITE + "/": "",
        }

        graph, results, requests = run_crawl(pages)

        result = results.get(SITE + "/")
        assert result["category"] == category
        assert requests.count(SITE + "/robots.txt") == 1
        if category == "skipped":
            assert requests == [SITE + "/robots.txt"]
            assert result["status_code"] is None
            assert result["reason"]
        else:
            assert requests == [SITE + "/robots.txt", SITE + "/"]


def test_robots_timeout():
    requests = []

    def handler(request):
        requests.append(request.url.path)
        raise httpx.ReadTimeout("Rules unavailable", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        graph, results = crawl(SITE + "/", client)

    assert requests == ["/robots.txt"]
    assert results.get(SITE + "/")["category"] == "skipped"
    assert results.get(SITE + "/")["status_code"] is None


def test_html_robots_response():
    pages = {SITE + "/robots.txt": "<!DOCTYPE html><html><body>Home page</body></html>"}

    graph, results, requests = run_crawl(pages)

    result = results.get(SITE + "/")
    assert result["category"] == "skipped"
    assert result["status_code"] is None
    assert result["reason"] == "robots.txt returned an HTML page instead of rules"
    assert requests == [SITE + "/robots.txt"]
