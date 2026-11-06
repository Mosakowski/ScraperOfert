"""Validated OLX category definitions used by profiles and domain logic."""

from __future__ import annotations

from typing import Any


CATEGORY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "televisions": {
        "label": "Telewizory",
        "path": "/elektronika/tv/telewizory/",
        "allowed_filter_params": ["search[filter_enum_size][0]"],
        "domain": "televisions",
    },
    "laptops": {
        "label": "Laptopy",
        "path": "/elektronika/komputery/laptopy/",
        "allowed_filter_params": [],
        "domain": "laptops",
    },
}


def get_category_definition(category_id: str | None) -> dict[str, Any]:
    return CATEGORY_DEFINITIONS.get(category_id or "televisions", CATEGORY_DEFINITIONS["televisions"])
