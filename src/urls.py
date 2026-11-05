from urllib.parse import urljoin, urlsplit, urlunsplit


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()
    if not url or any(character.isspace() for character in url):
        return None
    if "\\" in url:
        return None

    try:
        parts = urlsplit(url)
        hostname = parts.hostname
        port = parts.port
    except ValueError:
        return None

    if parts.scheme not in ("http", "https") or not hostname:
        return None

    hostname = hostname.lower()
    if ":" in hostname:
        hostname = "[" + hostname + "]"

    if parts.scheme == "http" and port == 80:
        port = None
    if parts.scheme == "https" and port == 443:
        port = None

    address = hostname
    if port is not None:
        address += ":" + str(port)
    if "@" in parts.netloc:
        address = parts.netloc.rsplit("@", 1)[0] + "@" + address

    path = parts.path or "/"
    return urlunsplit((parts.scheme, address, path, parts.query, ""))


def validate_start_url(url):
    normalized = normalize_url(url)
    if normalized is None:
        raise ValueError("Enter an absolute HTTP or HTTPS URL with a hostname")
    return normalized


def resolve_url(href, page_url):
    if not isinstance(href, str):
        return None

    href = href.strip()
    if not href or href.startswith("#"):
        return None
    if any(character.isspace() for character in href) or "\\" in href:
        return None

    base_url = normalize_url(page_url)
    if base_url is None:
        return None

    try:
        if urlsplit(href).scheme:
            return normalize_url(href)
        return normalize_url(urljoin(base_url, href))
    except ValueError:
        return None


def get_origin(url):
    normalized = normalize_url(url)
    if normalized is None:
        return None

    parts = urlsplit(normalized)
    port = parts.port
    if port is None:
        if parts.scheme == "https":
            port = 443
        else:
            port = 80
    return parts.scheme, parts.hostname, port


def same_origin(first_url, second_url):
    origin = get_origin(first_url)
    return origin is not None and origin == get_origin(second_url)
