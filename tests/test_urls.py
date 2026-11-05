import subprocess
import sys

import pytest

from src.urls import get_origin, normalize_url, resolve_url, same_origin, validate_start_url


def test_guide_examples():
    base = "https://club.test/events/index.html"
    cases = [
        ("../join#apply", "https://club.test/join"),
        ("/events?page=2#top", "https://club.test/events?page=2"),
        ("https://CLUB.test:443", "https://club.test/"),
        ("#top", None),
        ("mailto:team@club.test", None),
    ]
    for href, expected in cases:
        assert resolve_url(href, base) == expected


def test_skipped_links():
    for href in ["", "  ", "#hours", "tel:123", "javascript:alert(1)", "data:text/plain,hi", None]:
        assert resolve_url(href, "https://club.test/") is None


def test_malformed_links():
    links = [
        "https://",
        "https:/missing-host",
        "https:///missing-host",
        "https://club.test:bad/",
        "https://club.test:70000/",
        "http://[bad",
        "https://bad host/",
        "https://club.\ntest/",
        "https://club.test\\other/",
    ]
    for href in links:
        assert resolve_url(href, "https://club.test/") is None


def test_start_normalization():
    assert validate_start_url("  HTTPS://CLUB.test:443#top  ") == "https://club.test/"
    assert normalize_url("http://CLUB.test:80") == "http://club.test/"
    assert normalize_url("https://club.test:8443/Path/?b=2&a=1#top") == "https://club.test:8443/Path/?b=2&a=1"
    assert normalize_url("http://[::1]:80/path") == "http://[::1]/path"


def test_invalid_starts():
    for url in ["", "relative/path", "//club.test/", "ftp://club.test/", "https://", "https://club.test:bad/", None]:
        with pytest.raises(ValueError):
            validate_start_url(url)


def test_distinct_paths_and_queries():
    assert normalize_url("https://club.test/?page=1") != normalize_url("https://club.test/?page=2")
    assert normalize_url("https://club.test/?a=1&b=2") != normalize_url("https://club.test/?b=2&a=1")
    assert normalize_url("https://club.test/Path") != normalize_url("https://club.test/path")
    assert normalize_url("https://club.test/path") != normalize_url("https://club.test/path/")


def test_relative_and_protocol_relative_links():
    assert resolve_url("notes.html", "https://club.test/manual/") == "https://club.test/manual/notes.html"
    assert resolve_url("//OTHER.test:8080/Path", "https://club.test/") == "https://other.test:8080/Path"
    assert resolve_url("notes.html", "invalid base") is None


def test_origins():
    assert get_origin("https://CLUB.test:443/page") == ("https", "club.test", 443)
    assert get_origin("http://club.test/page") == ("http", "club.test", 80)
    assert same_origin("https://club.test/", "https://CLUB.test:443/other")
    assert not same_origin("https://club.test/", "http://club.test/")
    assert not same_origin("https://club.test/", "https://club.test:8443/")
    assert not same_origin("https://club.test/", "https://other.test/")
    assert not same_origin("invalid", "invalid")


def test_command_rejects_invalid_start():
    for url in ["relative/path", "https://", "mailto:team@club.test"]:
        result = subprocess.run(
            [sys.executable, "-m", "src.main", url], capture_output=True, text=True
        )
        assert result.returncode == 2
        assert "Enter an absolute HTTP or HTTPS URL with a hostname" in result.stderr
        assert "Traceback" not in result.stderr
        assert result.stdout == ""


def test_command_uses_normalized_start():
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "HTTPS://CLUB.test:443#top"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "https://club.test/\n"
    assert result.stderr == ""
