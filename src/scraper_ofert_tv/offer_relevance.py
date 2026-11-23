import re
from urllib.parse import parse_qs, urlsplit


def eligible_for_details(category_id: str, url: str) -> bool:
    """Exclude OLX fallback results and clearly unrelated departments."""
    parts = urlsplit(url)
    if parts.hostname not in ("www.olx.pl", "olx.pl") or not parts.path.startswith(("/d/oferta/", "/oferta/")):
        return False
    reason = parse_qs(parts.query).get("reason", [""])[0]
    if reason.startswith("extended_search"):
        return False
    if category_id in ("televisions", "laptops"):
        match = re.search(r"-CID(\d+)-", parts.path)
        if match and match.group(1) != "99":
            return False
        slug = parts.path.rsplit("/", 1)[-1].lower()
        if category_id == "televisions" and "steam-deck" in slug:
            return False
        hints = {
            "televisions": r"(?:telewiz|(?:^|-)tv(?:-|\.)|oled|qled|plazm|bravia|ambilight|\blcd\b|(?:ue|qe|qn|kd|xr)\d{2})",
            "laptops": r"(?:laptop|notebook|macbook|thinkpad|latitude|elitebook|ideapad|vivobook|zenbook|chromebook|lifebook|probook|inspiron|pavilion|legion|surface-pro)",
        }
        if not re.search(hints[category_id], slug):
            return False
    return True
