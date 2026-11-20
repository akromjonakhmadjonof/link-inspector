from time import sleep
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from .urls import get_origin


class Robots:
    def __init__(self, client):
        self.client = client
        self.rules = {}
        self.user_agent = client.headers.get("User-Agent", "CourseLinkChecker")

    def get(self, url):
        sleep(0.1)
        return self.client.get(url, follow_redirects=False)

    def can_fetch(self, url):
        origin = get_origin(url)
        if origin not in self.rules:
            parts = urlsplit(url)
            robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
            parser = RobotFileParser(robots_url)
            reason = ""
            try:
                response = self.get(robots_url)
            except (httpx.RequestError, httpx.InvalidURL):
                parser = None
                reason = "Could not read robots.txt"
            else:
                if 200 <= response.status_code < 300:
                    if response.text.lstrip().lower().startswith(("<!doctype html", "<html")):
                        parser = None
                        reason = "robots.txt returned an HTML page instead of rules"
                    else:
                        parser.parse(response.text.splitlines())
                elif response.status_code in (404, 410):
                    parser.parse([])
                else:
                    parser = None
                    reason = "Could not read robots.txt (HTTP " + str(response.status_code) + ")"
            self.rules[origin] = parser, reason

        parser, reason = self.rules[origin]
        if parser is None:
            return False, reason
        if not parser.can_fetch(self.user_agent, url):
            return False, "Disallowed by robots.txt"
        return True, ""
