"""Async web scraper with security hardening.

This module validates URLs, blocks dangerous targets, and extracts
clean text from recipe web pages using httpx + BeautifulSoup.
"""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────
URL_REGEX = re.compile(
    r"^https?://"                        # scheme
    r"(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%])+$"  # valid URL chars
)

ALLOWED_SCHEMES = frozenset({"http", "https"})

# SSRF Mitigation — Private / internal IP ranges that MUST be blocked.
# An attacker could submit a URL pointing to an internal service
# (e.g., http://169.254.169.254/latest/meta-data/ on AWS) to exfiltrate
# cloud metadata or access internal APIs. We block all private ranges.
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),      # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),     # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),          # "This" network
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]


class ScraperError(Exception):
    """Raised when scraping fails for any reason."""


# ── URL Validation ───────────────────────────────────────────────────

def validate_url(url: str) -> str:
    """Validate URL format and scheme. Returns the cleaned URL.

    Raises ScraperError if the URL is malformed or uses a blocked scheme.
    """
    if not URL_REGEX.match(url):
        raise ScraperError(f"Invalid URL format: {url}")

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ScraperError(
            f"Blocked scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed."
        )

    if not parsed.hostname:
        raise ScraperError("URL has no hostname.")

    return url


def _is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private/internal IP address.

    SSRF Mitigation: Prevents requests to internal network resources.
    An attacker could use DNS rebinding or direct IPs to bypass naive checks,
    so we resolve the hostname and check the actual IP.
    """
    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        return any(ip_obj in network for network in BLOCKED_IP_NETWORKS)
    except socket.gaierror:
        # If DNS resolution fails, block the request to be safe
        logger.warning("DNS resolution failed for %s — blocking request.", hostname)
        return True


def check_ssrf(url: str) -> None:
    """Block requests to private/internal IP addresses.

    SSRF (Server-Side Request Forgery) Mitigation:
    Without this check, an attacker could submit URLs like:
      - http://127.0.0.1:8000/admin
      - http://169.254.169.254/latest/meta-data/  (AWS metadata)
      - http://10.0.0.1:5432/  (internal database)
    This would let them probe or exfiltrate data from internal services.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        raise ScraperError("URL has no hostname.")

    if _is_private_ip(hostname):
        logger.warning("SSRF blocked: %s resolves to a private IP.", hostname)
        raise ScraperError(
            "This URL points to an internal/private network address "
            "and has been blocked for security reasons."
        )


# ── Content Extraction ───────────────────────────────────────────────

def _extract_text(html: str) -> str:
    """Parse HTML and extract meaningful text content.

    Strips scripts, styles, nav, footer, and other non-content elements
    to give the LLM a clean signal.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


# ── Main Scraper ─────────────────────────────────────────────────────

async def scrape_recipe_url(url: str) -> str:
    """Scrape a URL and return cleaned text content.

    Pipeline:
    1. Validate URL format and scheme
    2. Check for SSRF (private IP resolution)
    3. Fetch with strict timeout and custom User-Agent
    4. Extract and truncate text

    Returns:
        Clean text content from the page, capped at MAX_CONTENT_LENGTH.

    Raises:
        ScraperError: On any validation, network, or parsing failure.
    """
    validate_url(url)
    check_ssrf(url)

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.scraper_timeout_seconds),
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": settings.scraper_user_agent,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            response.raise_for_status()

    except httpx.TimeoutException as exc:
        logger.error("Timeout scraping %s: %s", url, exc)
        raise ScraperError(f"Request timed out after {settings.scraper_timeout_seconds}s.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("HTTP %d from %s", exc.response.status_code, url)
        raise ScraperError(f"HTTP {exc.response.status_code} error.") from exc
    except httpx.RequestError as exc:
        logger.error("Network error scraping %s: %s", url, exc)
        raise ScraperError(f"Network error: {exc}") from exc

    text = _extract_text(response.text)

    if len(text) < 50:
        raise ScraperError("Page contained too little text to extract a recipe.")

    # Cap content length to prevent prompt injection via malicious page content.
    # A very large page could stuff adversarial instructions into the prompt,
    # potentially causing the LLM to output attacker-controlled text.
    # Truncating at 50,000 chars limits the attack surface.
    if len(text) > settings.scraper_max_content_length:
        logger.info(
            "Truncating content from %d to %d chars.",
            len(text),
            settings.scraper_max_content_length,
        )
        text = text[: settings.scraper_max_content_length]

    return text
