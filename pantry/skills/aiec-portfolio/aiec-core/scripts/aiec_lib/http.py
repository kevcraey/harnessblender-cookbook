"""Keychain-tokens en REST-calls met Bearer-PAT. Redirects worden nooit gevolgd: een 302 op een
REST-endpoint betekent dat de server het token weigert (of dat de VPN weg is) en wordt als
AuthError gemeld. Tokens worden nooit geprint.

Een Client is alleen-lezen. De enige weg naar POST/PUT is http.writer(cfg, target, scope, apply):
die roept config.guard aan en geeft pas met apply=True een schrijvende client terug. Zonder apply
krijg je een leesclient, zodat dry-run nooit per ongeluk schrijft."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from aiec_lib import config

KEYCHAIN = {"confluence": "confluence-personal-token", "jira": "jira-personal-token"}
ENV = {"confluence": "CONFLUENCE_PERSONAL_TOKEN", "jira": "JIRA_PERSONAL_TOKEN"}
PAUSE = float(os.environ.get("AIEC_HTTP_PAUSE", "0.15"))   # seconden tussen REST-calls


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = ""):
        self.status, self.url, self.body = status, url.split("?")[0], body[:400]
        super().__init__(f"{status} op {self.url}: {self.body}")


class AuthError(HttpError):
    pass


def keychain(service: str, account: str | None = None) -> str | None:
    args = ["security", "find-generic-password", "-s", service, "-w"]
    if account:
        args[3:3] = ["-a", account]
    out = subprocess.run(args, capture_output=True, text=True)
    return out.stdout.strip() or None


def token(kind: str) -> str:
    t = os.environ.get(ENV[kind]) or keychain(KEYCHAIN[kind], os.environ.get("USER")) \
        or keychain(KEYCHAIN[kind])
    if not t:
        raise AuthError(0, kind, f"geen token: env {ENV[kind]} of keychain-item '{KEYCHAIN[kind]}'")
    return t


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class Client:
    def __init__(self, base_url: str, tok: str):
        self.base = base_url.rstrip("/")
        self.writable = False      # enkel http.writer() zet dit
        self.scope = None
        self._hdr = {"Authorization": "Bearer " + tok, "Accept": "application/json",
                     "Content-Type": "application/json", "X-Atlassian-Token": "no-check"}

    def request(self, method: str, path: str, params: dict | None = None, body=None, *, raw=None, content_type=None):
        if method != "GET" and not self.writable:
            raise config.GuardRefused(f"{method} {path}: client is alleen-lezen; schrijven kan enkel via "
                                      "http.writer(cfg, target, scope, apply=True)")
        url = self.base + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
        if raw is not None and (body is not None or not isinstance(raw, bytes)):
            raise ValueError('Gebruik JSON of bytes, niet beide')
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        headers = dict(self._hdr)
        if content_type: headers['Content-Type'] = content_type
        req = urllib.request.Request(url, method=method, headers=headers, data=data)
        time.sleep(PAUSE)   # de WAF knijpt bursts af (connection reset); een korte pauze per call voorkomt dat
        try:
            with _OPENER.open(req, timeout=90) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            if e.code in (301, 302, 303, 307, 401, 403):
                raise AuthError(e.code, url, "token geweigerd of VPN weg (redirect naar login)") from None
            raise HttpError(e.code, url, detail) from None
        except urllib.error.URLError as e:
            raise HttpError(0, url, f"geen verbinding: {e.reason}") from None

    def upload_attachment(self, page_id, filename, content):
        import re
        from uuid import uuid4
        if not re.fullmatch(r'\d+', str(page_id)) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,175}\.png', filename) or '..' in filename:
            raise ValueError('Onveilige bijlagebestemming')
        if not isinstance(content, bytes) or not content.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Alleen gegenereerde PNG-rapportbijlagen')
        boundary = 'aiec-'+uuid4().hex
        header = ('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="'+filename+'"\r\nContent-Type: image/png\r\n\r\n').encode('ascii')
        payload = header+content+('\r\n--'+boundary+'--\r\n').encode('ascii')
        return self.request('POST', f'/rest/api/content/{page_id}/child/attachment', raw=payload,
                            content_type='multipart/form-data; boundary='+boundary)

    def get(self, path, params=None):
        return self.request("GET", path, params)

    def post(self, path, body=None, params=None):
        return self.request("POST", path, params, body)

    def put(self, path, body=None, params=None):
        return self.request("PUT", path, params, body)


def confluence(cfg: dict) -> Client:
    return Client(cfg["atlassian"]["confluence_url"], token("confluence"))


def jira(cfg: dict) -> Client:
    return Client(cfg["atlassian"]["jira_url"], token("jira"))


def writer(cfg: dict, target: str, scope: str, apply: bool) -> Client:
    """De guard. target 'confluence' | 'jira'; scope = space-key of projectsleutel. Met apply=True
    en een toelatende mode: schrijvende client. Zonder apply: leesclient (dry-run). Anders
    GuardRefused (exit 3)."""
    config.guard(cfg, target, scope, apply)
    c = confluence(cfg) if target == "confluence" else jira(cfg)
    c.writable = bool(apply)
    c.scope = scope
    return c
