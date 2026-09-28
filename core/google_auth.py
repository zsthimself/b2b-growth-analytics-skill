# -*- coding: utf-8 -*-
"""
Google Cloud OAuth 2.0 Credentials Manager.
Supports automated refresh, multi-scope protection, and safe authorization check.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Full scope set covering GA4, Search Console, and Google Ads
SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/adwords",
)

DESKTOP_TYPES = {"installed", "desktop"}


class AuthConfigurationError(ValueError):
    """Raised for missing or invalid local OAuth files."""


@dataclass(frozen=True)
class CredentialPaths:
    client_file: Path
    token_file: Path


def credential_paths_from_env() -> CredentialPaths:
    client_env = os.environ.get("GOOGLE_OAUTH_CLIENT_FILE", "./credentials/client_secret.json")
    token_env = os.environ.get("GOOGLE_TOKEN_FILE", "./credentials/token.json")
    return CredentialPaths(
        client_file=Path(client_env).expanduser().resolve(),
        token_file=Path(token_env).expanduser().resolve(),
    )


def load_credentials(paths: CredentialPaths | None = None) -> Credentials:
    """Load existing credentials, refresh if expired, or raise clear error."""
    if paths is None:
        paths = credential_paths_from_env()

    if not paths.token_file.is_file():
        raise AuthConfigurationError(
            f"Token file not found at {paths.token_file}. "
            "Please run doctor.py --reauthorize to generate it."
        )

    try:
        creds = Credentials.from_authorized_user_file(str(paths.token_file), scopes=SCOPES)
    except Exception as exc:
        raise AuthConfigurationError(f"Failed to read token file: {exc}") from exc

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                paths.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(paths.token_file, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception as exc:
                raise AuthConfigurationError(
                    f"Token refresh failed: {exc}. Please run doctor.py --reauthorize."
                ) from exc
        else:
            raise AuthConfigurationError(
                "Credentials are invalid and cannot be refreshed. Please run doctor.py --reauthorize."
            )

    return creds


def run_interactive_authorization(paths: CredentialPaths | None = None) -> Credentials:
    """Run interactive local webserver OAuth flow to authorize all scopes."""
    if paths is None:
        paths = credential_paths_from_env()

    if not paths.client_file.is_file():
        raise AuthConfigurationError(
            f"Client secret file not found at {paths.client_file}. "
            "Download it from Google Cloud Console."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(paths.client_file), scopes=SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    paths.token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(paths.token_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    return creds
