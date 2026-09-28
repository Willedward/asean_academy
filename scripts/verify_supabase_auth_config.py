#!/usr/bin/env python3
"""Fail closed when hosted Supabase Google OAuth redirects are misconfigured."""

from __future__ import annotations

import argparse
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

PROJECT_REF = re.compile(r"^[a-z0-9]{8,64}$")


def normalize_origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("The hosted web URL must be an HTTPS origin.")
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError(
            "The hosted web URL must not contain credentials, a path, query, or fragment."
        )
    netloc = parsed.hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit(("https", netloc, "", "", ""))


def fetch_auth_config(project_ref: str, access_token: str) -> dict:
    url = f"https://api.supabase.com/v1/projects/{project_ref}/config/auth"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "asean-academy-staging-config/1.0",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(
            f"Supabase Auth configuration returned HTTP {exc.code}."
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Supabase Auth configuration could not be reached: {exc.reason}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Supabase Auth configuration returned invalid JSON.") from exc


def verify_auth_config(config: dict, web_origin: str) -> dict:
    callback = f"{web_origin}/auth/callback"
    allow_list = {
        item.strip().rstrip("/")
        for item in str(config.get("uri_allow_list") or "").split(",")
        if item.strip()
    }
    problems: list[str] = []
    if config.get("external_google_enabled") is not True:
        problems.append("enable the Google provider")
    try:
        configured_site = normalize_origin(str(config.get("site_url") or ""))
    except ValueError:
        configured_site = None
    if configured_site != web_origin:
        problems.append(f"set Site URL to {web_origin}")
    if callback not in allow_list:
        problems.append(f"add {callback} to the redirect allow list")
    if config.get("disable_signup") is True:
        problems.append("enable new user sign-ups so invited first-time Google users can authenticate")
    if problems:
        raise RuntimeError("Supabase Auth configuration is incomplete: " + "; ".join(problems) + ".")
    return {
        "status": "passed",
        "google_provider": True,
        "site_url": web_origin,
        "callback_allowlisted": True,
        "new_user_authentication": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--web-url", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not PROJECT_REF.fullmatch(args.project_ref):
        raise SystemExit("The Supabase project reference is invalid.")
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    if not access_token:
        raise SystemExit("Set SUPABASE_ACCESS_TOKEN in the protected environment.")
    web_origin = normalize_origin(args.web_url)
    result = verify_auth_config(
        fetch_auth_config(args.project_ref, access_token),
        web_origin,
    )
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
