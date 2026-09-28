# -*- coding: utf-8 -*-
"""
HTTP Transport Layer for Google APIs.
Handles Bearer tokens, retries with exponential backoff, and secret-safe error masking.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Mapping
import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials


DEFAULT_TIMEOUT = 60.0
MAX_ATTEMPTS = 3
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class GoogleAPIError(RuntimeError):
    """Classified, secret-safe REST failure."""
    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


def mask_secrets(text: str) -> str:
    """Mask potential access tokens or client secrets in logs."""
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1***", text, flags=re.IGNORECASE)
    text = re.sub(r"(developer-token\s*:\s*)[^\s,]+", r"\1***", text, flags=re.IGNORECASE)
    return text


def execute_request(
    method: str,
    url: str,
    creds: Credentials,
    headers: Mapping[str, str] | None = None,
    json_body: Any = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Execute authenticated HTTP request with token auto-refresh and retries."""
    if not creds.valid:
        creds.refresh(GoogleAuthRequest())

    req_headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    if headers:
        req_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                json=json_body,
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json() if resp.text else {}

            if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_ATTEMPTS:
                time.sleep(2.0 ** attempt)
                continue

            error_msg = mask_secrets(f"Google API error (HTTP {resp.status_code}): {resp.text}")
            raise GoogleAPIError(error_msg, status_code=resp.status_code, response_text=resp.text)
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(2.0 ** attempt)
                continue
            break

    raise GoogleAPIError(f"HTTP request failed after {MAX_ATTEMPTS} attempts: {last_error}")
