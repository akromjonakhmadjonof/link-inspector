import httpx

from src.checker import check_url, create_client


def test_client_settings():
    with create_client() as client:
        assert client.headers["user-agent"] == "CourseLinkChecker"
        assert client.timeout.read == 5.0


def test_redirect_to_html():
    cases = [301, 302, 303, 307, 308]
    for redirect_code in cases:
        requests = []
        page = '<a href="notes.html">Notes</a>'

        def handler(request):
            requests.append((request.method, request.url.path))
            if request.url.path == "/start/old":
                return httpx.Response(redirect_code, headers={"Location": "../manual/#top"})
            return httpx.Response(200, headers={"Content-Type": "Text/HTML; charset=utf-8"}, text=page)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result, html = check_url("https://AKHMADJONOFF.UZ:443/start/old#top", client)

        assert requests == [("GET", "/start/old"), ("GET", "/manual/")]
        assert result["requested_url"] == "https://akhmadjonoff.uz/start/old"
        assert result["final_url"] == "https://akhmadjonoff.uz/manual/"
        assert result["status_code"] == 200
        assert result["category"] == "ok"
        assert html == page


def test_pdf_is_ok_without_html():
    def handler(request):
        return httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=b"%PDF-1.4")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://akhmadjonoff.uz/manual.pdf", client)

    assert result["status_code"] == 200
    assert result["category"] == "ok"
    assert html is None


def test_status_categories():
    cases = [
        (404, "broken"), (410, "broken"), (401, "restricted"), (403, "restricted"),
        (429, "rate-limited"), (503, "server-error"), (418, "unverified"),
        (304, "unverified"),
    ]
    for status_code, category in cases:
        def handler(request):
            return httpx.Response(status_code, headers={"Content-Type": "text/html"}, text="<p>Result</p>")

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result, html = check_url("https://akhmadjonoff.uz/", client)

        assert result["status_code"] == status_code
        assert result["category"] == category
        assert result["reason"]
        assert html is None


def test_request_failure_after_redirect():
    cases = [
        (httpx.ReadTimeout, "Request timed out"),
        (httpx.ConnectError, "Could not complete the request"),
    ]
    for error, reason in cases:
        def handler(request):
            if request.url.path == "/start":
                return httpx.Response(302, headers={"Location": "/unavailable"})
            raise error("Simulated network failure", request=request)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result, html = check_url("https://akhmadjonoff.uz/start", client)

        assert result["requested_url"] == "https://akhmadjonoff.uz/start"
        assert result["final_url"] == "https://akhmadjonoff.uz/unavailable"
        assert result["status_code"] is None
        assert result["category"] == "unverified"
        assert result["reason"] == reason
        assert html is None


def test_invalid_redirect():
    cases = [{}, {"Location": "https://"}, {"Location": "https://[akhmadjonoff.uz"}]
    for headers in cases:
        def handler(request):
            assert request.url.path == "/start"
            return httpx.Response(302, headers=headers)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result, html = check_url("https://akhmadjonoff.uz/start", client)

        assert result["status_code"] == 302
        assert result["category"] == "unverified"
        assert "location" in result["reason"]
        assert html is None


def test_unsupported_redirect_does_not_request_target():
    def handler(request):
        assert str(request.url) == "https://akhmadjonoff.uz/start"
        return httpx.Response(302, headers={"Location": "mailto:team@akhmadjonoff.uz"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result, html = check_url("https://akhmadjonoff.uz/start", client)

    assert result["category"] == "unverified"
    assert html is None


def test_redirect_loop():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        location = "/other" if request.url.path == "/start" else "/start#top"
        return httpx.Response(302, headers={"Location": location})

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        result, html = check_url("https://akhmadjonoff.uz/start", client)

    assert paths == ["/start", "/other"]
    assert result["final_url"] == "https://akhmadjonoff.uz/other"
    assert result["category"] == "unverified"
    assert result["reason"] == "Redirect loop"
    assert html is None


def test_redirect_limit():
    cases = [(200, "ok"), (302, "unverified")]
    for last_status, category in cases:
        paths = []

        def handler(request):
            paths.append(request.url.path)
            number = int(request.url.path[1:])
            if number == 5 and last_status == 200:
                return httpx.Response(200)
            return httpx.Response(302, headers={"Location": f"/{number + 1}"})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result, html = check_url("https://akhmadjonoff.uz/0", client)

        assert paths == ["/0", "/1", "/2", "/3", "/4", "/5"]
        assert result["final_url"] == "https://akhmadjonoff.uz/5"
        assert result["status_code"] == last_status
        assert result["category"] == category
        assert html is None
