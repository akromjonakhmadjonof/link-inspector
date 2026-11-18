import httpx

from .urls import resolve_url, validate_start_url


REDIRECT_CODES = (301, 302, 303, 307, 308)
MAX_REDIRECTS = 5


def create_client():
    return httpx.Client(timeout=5.0, headers={"User-Agent": "CourseLinkChecker"})


def status_outcome(status_code):
    if 200 <= status_code < 300:
        return "ok", "Request succeeded"
    if status_code in (404, 410):
        return "broken", "Page is missing"
    if status_code in (401, 403):
        return "restricted", "Access is restricted"
    if status_code == 429:
        return "rate-limited", "Too many requests"
    if 500 <= status_code < 600:
        return "server-error", "Server returned an error"
    return "unverified", "Unexpected HTTP status"


def check_url(url, client, robots=None):
    requested_url = validate_start_url(url)
    current_url = requested_url
    visited = [requested_url]
    category = "unverified"
    html = None

    while True:
        status_code = None
        if robots is not None:
            allowed, reason = robots.can_fetch(current_url)
            if not allowed:
                category = "skipped"
                break
        try:
            if robots is None:
                response = client.get(current_url, follow_redirects=False)
            else:
                response = robots.get(current_url)
        except httpx.TimeoutException:
            reason = "Request timed out"
            break
        except (httpx.RequestError, httpx.InvalidURL):
            reason = "Could not complete the request"
            break

        status_code = response.status_code
        if status_code not in REDIRECT_CODES:
            category, reason = status_outcome(status_code)
            content_type = response.headers.get("content-type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if category == "ok" and media_type == "text/html":
                html = response.text
            break

        location = response.headers.get("location", "").strip()
        if location.startswith("#"):
            target = current_url
        else:
            target = resolve_url(location, current_url)
        if target is None:
            reason = "Redirect has a missing or invalid location"
            break
        if target in visited:
            reason = "Redirect loop"
            break
        if len(visited) > MAX_REDIRECTS:
            reason = "More than five redirects"
            break

        visited.append(target)
        current_url = target

    result = {
        "requested_url": requested_url,
        "final_url": current_url,
        "status_code": status_code,
        "category": category,
        "reason": reason,
    }
    return result, html
