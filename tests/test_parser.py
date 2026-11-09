import httpx

from src.checker import check_url
from src.parser import extract_links


def test_guide_example():
    html = '''
        <a href="../join#form">Join</a>
        <a href="mailto:team@club.test">Email</a>
        <img src="/logo.png">
    '''

    assert extract_links(html, "https://club.test/events/today/") == [
        "https://club.test/events/join"
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

    assert extract_links(html, "https://club.test/") == [
        "https://club.test/one",
        "https://club.test/two?page=2&order=asc",
        "https://club.test/one",
    ]


def test_first_valid_base():
    html = '''
        <base>
        <base href="https://">
        <base href="../docs/">
        <base href="https://other.test/ignored/">
        <a href="notes.html">Notes</a>
    '''

    assert extract_links(html, "https://club.test/events/today/") == [
        "https://club.test/events/docs/notes.html"
    ]


def test_invalid_base_uses_page_url():
    html = '<base href="mailto:team@club.test"><a href="notes.html">Notes</a>'
    assert extract_links(html, "https://club.test/manual/") == [
        "https://club.test/manual/notes.html"
    ]
    assert extract_links("", "https://club.test/manual/") == []


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
        result, html = check_url("https://club.test/old", client)

    assert result["category"] == "ok"
    assert extract_links(html, result["final_url"]) == ["https://club.test/manual/notes.html"]
    assert paths == ["/old", "/manual/"]
