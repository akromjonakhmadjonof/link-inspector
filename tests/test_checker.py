import httpx
import pytest

from src.checker import check_url, create_client


def test_client_settings():
    with create_client() as client:
        assert client.headers["user-agent"] == "CourseLinkChecker"
        assert client.timeout.read == 5.0


@pytest.mark.parametrize("redirect_code", [301, 302, 303, 307, 308])
def test_redirect_to_html(redirect_code):
    requests = []
    page = '<a href="notes.html">Notes</a>'

    def handler(request):
        requests.append((request.method, request.url.path))
        if request.url.path == "/start/old":
            return httpx.Response(redirect_code, headers={"Location": "../manual/#top"})
        return httpx.Response(200, headers={"Content-Type": "Text/HTML; charset=utf-8"}, text=page)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://CLUB.test:443/start/old#top", client)

    assert requests == [("GET", "/start/old"), ("GET", "/manual/")]
    assert result["requested_url"] == "https://club.test/start/old"
    assert result["final_url"] == "https://club.test/manual/"
    assert result["status_code"] == 200
    assert result["category"] == "ok"
    assert html == page


def test_pdf_is_ok_without_html():
    def handler(request):
        return httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=b"%PDF-1.4")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/manual.pdf", client)

    assert result["status_code"] == 200
    assert result["category"] == "ok"
    assert html is None


@pytest.mark.parametrize("status_code, category", [
    (404, "broken"), (410, "broken"), (401, "restricted"), (403, "restricted"),
    (429, "rate-limited"), (503, "server-error"), (418, "unverified"),
    (304, "unverified"),
])
def test_status_categories(status_code, category):
    def handler(request):
        return httpx.Response(status_code, headers={"Content-Type": "text/html"}, text="<p>Result</p>")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/", client)

    assert result["status_code"] == status_code
    assert result["category"] == category
    assert result["reason"]
    assert html is None


@pytest.mark.parametrize("error, reason", [
    (httpx.ReadTimeout, "Request timed out"),
    (httpx.ConnectError, "Could not complete the request"),
])
def test_request_failure_after_redirect(error, reason):
    def handler(request):
        if request.url.path == "/start":
            return httpx.Response(302, headers={"Location": "/unavailable"})
        raise error("Simulated network failure", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/start", client)

    assert result["requested_url"] == "https://club.test/start"
    assert result["final_url"] == "https://club.test/unavailable"
    assert result["status_code"] is None
    assert result["category"] == "unverified"
    assert result["reason"] == reason
    assert html is None


@pytest.mark.parametrize("headers", [{}, {"Location": "https://"}, {"Location": "http://[bad"}])
def test_invalid_redirect(headers):
    def handler(request):
        assert request.url.path == "/start"
        return httpx.Response(302, headers=headers)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/start", client)

    assert result["status_code"] == 302
    assert result["category"] == "unverified"
    assert "location" in result["reason"]
    assert html is None


def test_unsupported_redirect_does_not_request_target():
    def handler(request):
        assert str(request.url) == "https://club.test/start"
        return httpx.Response(302, headers={"Location": "mailto:team@club.test"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/start", client)

    assert result["category"] == "unverified"
    assert html is None


def test_redirect_loop():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        location = "/other" if request.url.path == "/start" else "/start#top"
        return httpx.Response(302, headers={"Location": location})

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        result, html = check_url("https://club.test/start", client)

    assert paths == ["/start", "/other"]
    assert result["final_url"] == "https://club.test/other"
    assert result["category"] == "unverified"
    assert result["reason"] == "Redirect loop"
    assert html is None


@pytest.mark.parametrize("last_status, category", [(200, "ok"), (302, "unverified")])
def test_redirect_limit(last_status, category):
    paths = []

    def handler(request):
        paths.append(request.url.path)
        number = int(request.url.path[1:])
        if number == 5 and last_status == 200:
            return httpx.Response(200)
        return httpx.Response(302, headers={"Location": f"/{number + 1}"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://club.test/0", client)

    assert paths == ["/0", "/1", "/2", "/3", "/4", "/5"]
    assert result["final_url"] == "https://club.test/5"
    assert result["status_code"] == last_status
    assert result["category"] == category
    assert html is None
