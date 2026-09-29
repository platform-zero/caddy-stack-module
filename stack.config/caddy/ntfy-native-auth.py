#!/usr/bin/env python3
"""Authorize native ntfy Basic requests against Keycloak."""

import base64
import binascii
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlsplit
from urllib.request import Request, urlopen


KEYCLOAK_TOKEN_URL = os.environ["KEYCLOAK_TOKEN_URL"]
CLIENT_SECRET = os.environ["NTFY_NATIVE_CLIENT_SECRET"]
GATEWAY_SECRET = os.environ["NTFY_NATIVE_GATEWAY_SECRET"]
MAX_AUTH_LENGTH = 8192
TOPIC = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
READ_METHODS = {"GET", "HEAD"}
WRITE_METHODS = {"POST", "PUT"}
ALERT_TOPICS = {"webservices-alerts", "webservices-critical", "webservices-warnings"}


def basic_credentials(value):
    if not value or len(value) > MAX_AUTH_LENGTH or not value.startswith("Basic "):
        return None
    try:
        raw = base64.b64decode(value[6:], validate=True).decode("utf-8")
        username, password = raw.split(":", 1)
    except (ValueError, UnicodeError, binascii.Error):
        return None
    if not username or not password or len(username) > 128:
        return None
    return username, password


def keycloak_identity(username, password):
    body = urlencode({
        "client_id": "ntfy-native",
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "openid profile groups",
    }).encode()
    request = Request(KEYCLOAK_TOKEN_URL, data=body,
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(request, timeout=5) as response:
            token = json.load(response)["access_token"]
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if claims.get("preferred_username", "").casefold() != username.casefold():
            return None
        return claims
    except (HTTPError, URLError, KeyError, ValueError, UnicodeError, IndexError):
        return None


def permitted(identity, method, original_uri):
    username = identity["preferred_username"].casefold()
    groups = {group.strip("/").casefold() for group in identity.get("groups", [])}
    if "onboarding_required" in groups or "onboarding-required" in groups:
        return False
    if method in READ_METHODS and urlsplit(original_uri).path in {
        "/v1/health", "/v1/config", "/v1/account", "/v1/stats"
    }:
        return True
    path = urlsplit(original_uri).path
    if "%2f" in path.casefold() or "%5c" in path.casefold():
        return False
    parts = unquote(path).strip("/").split("/")
    if not parts or not parts[0] or len(parts) > 2:
        return False
    topics = parts[0].split(",")
    if not all(TOPIC.fullmatch(topic) for topic in topics):
        return False
    if len(parts) == 2 and parts[1] not in {"auth", "ws", "json", "sse", "raw"}:
        return False
    if method not in READ_METHODS | WRITE_METHODS:
        return False
    if method in WRITE_METHODS and len(parts) != 1:
        return False
    personal_topic = re.sub(r"[^a-z0-9_-]", "_", username) + "_alerts"
    for topic in topics:
        if topic.casefold() == personal_topic:
            continue
        if "ntfy-topic-" + topic.casefold() in groups:
            continue
        if topic in ALERT_TOPICS and method in READ_METHODS and groups & {"admins", "operators"}:
            continue
        return False
    return True


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path != "/auth" or self.headers.get("X-Ntfy-Gateway-Secret") != GATEWAY_SECRET:
            self.send_error(403)
            return
        credentials = basic_credentials(self.headers.get("Authorization"))
        if not credentials:
            self.send_response(401)
            self.end_headers()
            return
        identity = keycloak_identity(*credentials)
        if not identity:
            self.send_response(401)
        elif not permitted(identity, self.headers.get("X-Forwarded-Method", ""),
                           self.headers.get("X-Forwarded-Uri", "")):
            self.send_response(403)
        else:
            self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        # Do not record credentials, usernames, URLs, or Keycloak responses.
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 25017), Handler).serve_forever()
