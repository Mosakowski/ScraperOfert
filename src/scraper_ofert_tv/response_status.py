import re


def classify_response(status: int, html: str) -> str | None:
    """Classify the document response, ignoring CAPTCHA text in app configuration."""
    if status == 404:
        return "not_found"
    if status == 410:
        return "gone"
    if status in (401, 403):
        return "forbidden_403"
    if status == 429:
        return "rate_limited"
    if status >= 500:
        return f"server_error_{status}"

    # OLX embeds captcha translations and a captchaSiteKey in ordinary pages.
    # Only a rendered challenge element is evidence of an active challenge.
    if re.search(r'<(?:iframe|form|div)[^>]+(?:id|class|src)=["\'][^"\']*(?:captcha|datadome|challenge)[^"\']*["\']', html, re.I):
        return "captcha_detected"
    return None
