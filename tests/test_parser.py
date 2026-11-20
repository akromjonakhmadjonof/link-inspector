import httpx

from src.checker import check_url
from src.parser import extract_links


def test_guide_example():
    html = '''
        <a href="../join#form">Join</a>
        <a href="mailto:team@akhmadjonoff.uz">Email</a>
        <img src="/logo.png">
    '''

    assert extract_links(html, "https://akhmadjonoff.uz/events/today/") == [
        "https://akhmadjonoff.uz/events/join"
    ]


def test_ignored_links_and_repeated_anchors():
    html = '''
        <a href="/one">First</a>
        <a href="#top">Top</a>
        <a href="">Empty</a>
        <a>No href</a>
        <a href="javascript:alert(1)">Script</a>
        <script src="/script.js"></script>
        <form action="/submit"></form>
        <a href="/two?page=2&amp;order=asc">Second</a>
        <a href="/one#again">First again</a>
    '''

    assert extract_links(html, "https://akhmadjonoff.uz/") == [
        "https://akhmadjonoff.uz/one",
        "https://akhmadjonoff.uz/two?page=2&order=asc",
        "https://akhmadjonoff.uz/one",
    ]


def test_first_valid_base():
    html = '''
        <base>
        <base href="https://">
        <base href="../docs/">
        <base href="https://www.akhmadjonoff.uz/ignored/">
        <a href="notes.html">Notes</a>
    '''

    assert extract_links(html, "https://akhmadjonoff.uz/events/today/") == [
        "https://akhmadjonoff.uz/events/docs/notes.html"
    ]


def test_invalid_base_uses_page_url():
    html = '<base href="mailto:team@akhmadjonoff.uz"><a href="notes.html">Notes</a>'
    assert extract_links(html, "https://akhmadjonoff.uz/manual/") == [
        "https://akhmadjonoff.uz/manual/notes.html"
    ]
    assert extract_links("", "https://akhmadjonoff.uz/manual/") == []


def test_relative_link_after_redirect():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path == "/old":
            return httpx.Response(302, headers={"Location": "/manual/"})
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text='<a href="notes.html">Notes</a>',
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://akhmadjonoff.uz/old", client)

    assert result["category"] == "ok"
    assert extract_links(html, result["final_url"]) == ["https://akhmadjonoff.uz/manual/notes.html"]
    assert paths == ["/old", "/manual/"]
