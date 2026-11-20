import subprocess
import sys

import pytest

from src.urls import get_origin, normalize_url, resolve_url, same_origin, validate_start_url


def test_guide_examples():
    base = "https://akhmadjonoff.uz/events/index.html"
    cases = [
        ("../join#apply", "https://akhmadjonoff.uz/join"),
        ("/events?page=2#top", "https://akhmadjonoff.uz/events?page=2"),
        ("https://AKHMADJONOFF.UZ:443", "https://akhmadjonoff.uz/"),
        ("#top", None),
        ("mailto:team@akhmadjonoff.uz", None),
    ]
    for href, expected in cases:
        assert resolve_url(href, base) == expected


def test_skipped_links():
    for href in ["", "  ", "#hours", "tel:123", "javascript:alert(1)", "data:text/plain,hi", None]:
        assert resolve_url(href, "https://akhmadjonoff.uz/") is None


def test_malformed_links():
    links = [
        "https://",
        "https:/akhmadjonoff.uz",
        "https:///akhmadjonoff.uz",
        "https://akhmadjonoff.uz:bad/",
        "https://akhmadjonoff.uz:70000/",
        "https://[akhmadjonoff.uz",
        "https://akhmadjonoff .uz/",
        "https://akhmadjonoff.\nuz/",
        "https://akhmadjonoff.uz\\other/",
    ]
    for href in links:
        assert resolve_url(href, "https://akhmadjonoff.uz/") is None


def test_start_normalization():
    assert validate_start_url("  HTTPS://AKHMADJONOFF.UZ:443#top  ") == "https://akhmadjonoff.uz/"
    assert normalize_url("http://AKHMADJONOFF.UZ:80") == "http://akhmadjonoff.uz/"
    assert normalize_url("https://akhmadjonoff.uz:8443/Path/?b=2&a=1#top") == "https://akhmadjonoff.uz:8443/Path/?b=2&a=1"


def test_invalid_starts():
    for url in ["", "relative/path", "//akhmadjonoff.uz/", "ftp://akhmadjonoff.uz/", "https://", "https://akhmadjonoff.uz:bad/", None]:
        with pytest.raises(ValueError):
            validate_start_url(url)


def test_distinct_paths_and_queries():
    assert normalize_url("https://akhmadjonoff.uz/?page=1") != normalize_url("https://akhmadjonoff.uz/?page=2")
    assert normalize_url("https://akhmadjonoff.uz/?a=1&b=2") != normalize_url("https://akhmadjonoff.uz/?b=2&a=1")
    assert normalize_url("https://akhmadjonoff.uz/Path") != normalize_url("https://akhmadjonoff.uz/path")
    assert normalize_url("https://akhmadjonoff.uz/path") != normalize_url("https://akhmadjonoff.uz/path/")


def test_relative_and_protocol_relative_links():
    assert resolve_url("notes.html", "https://akhmadjonoff.uz/manual/") == "https://akhmadjonoff.uz/manual/notes.html"
    assert resolve_url("//WWW.AKHMADJONOFF.UZ:8080/Path", "https://akhmadjonoff.uz/") == "https://www.akhmadjonoff.uz:8080/Path"
    assert resolve_url("notes.html", "invalid base") is None


def test_origins():
    assert get_origin("https://AKHMADJONOFF.UZ:443/page") == ("https", "akhmadjonoff.uz", 443)
    assert get_origin("http://akhmadjonoff.uz/page") == ("http", "akhmadjonoff.uz", 80)
    assert same_origin("https://akhmadjonoff.uz/", "https://AKHMADJONOFF.UZ:443/other")
    assert not same_origin("https://akhmadjonoff.uz/", "http://akhmadjonoff.uz/")
    assert not same_origin("https://akhmadjonoff.uz/", "https://akhmadjonoff.uz:8443/")
    assert not same_origin("https://akhmadjonoff.uz/", "https://www.akhmadjonoff.uz/")
    assert not same_origin("invalid", "invalid")


def test_command_rejects_invalid_start():
    for url in ["relative/path", "https://", "mailto:team@akhmadjonoff.uz"]:
        result = subprocess.run(
            [sys.executable, "-m", "src.main", url], capture_output=True, text=True
        )
        assert result.returncode == 2
        assert "Enter an absolute HTTP or HTTPS URL with a hostname" in result.stderr
        assert "Traceback" not in result.stderr
        assert result.stdout == ""


def test_command_uses_normalized_start():
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "HTTPS://AKHMADJONOFF.UZ:443#top"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "https://akhmadjonoff.uz/\n"
    assert result.stderr == ""
