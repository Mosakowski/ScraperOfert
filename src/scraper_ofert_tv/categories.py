"""Validated OLX category definitions used by profiles and domain logic."""

from __future__ import annotations

from typing import Any


CATEGORY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "televisions": {
        "label": "Telewizory",
        "path": "/elektronika/tv/telewizory/",
        "allowed_filter_params": ["search[filter_enum_size][0]"],
        "filter_schema": [{
            "key": "search[filter_enum_size][0]", "label": "Przekątna TV",
            "type": "select", "options": ["lt-30", "30-39", "40-49", "50-59", "60-69", "70-79", "gt-80"],
        }],
        "attribute_schema": ["brand", "model", "screen_size_inches", "technology", "resolution", "condition"],
        "domain": "televisions",
    },
    "laptops": {
        "label": "Laptopy",
        "path": "/elektronika/komputery/laptopy/",
        "allowed_filter_params": [
            "search[filter_enum_screendiagonal_laptops][0]",
            "search[filter_enum_operatingsystem_laptops][0]",
            "search[filter_enum_graphicscardtype_laptops][0]",
            "search[filter_enum_processorseries_laptops][0]",
            "search[filter_enum_ramsize_laptops][0]",
            "search[filter_enum_harddisktype_laptops][0]",
            "search[filter_enum_disksize_laptops][0]",
        ],
        "filter_schema": [
            {"key": "search[filter_enum_screendiagonal_laptops][0]", "label": "Przekątna ekranu", "type": "select", "options": [
                "under-11", "11-12-9", "13-13-9", "14-14-9", "15-15-9", "16-and-more", "17-17-9", "18more"]},
            {"key": "search[filter_enum_operatingsystem_laptops][0]", "label": "System operacyjny", "type": "select", "options": [
                "lack", "chrome-os", "linux", "mac-os", "windows7", "windows8", "windows10", "windows11", "others"]},
            {"key": "search[filter_enum_graphicscardtype_laptops][0]", "label": "Rodzaj karty graficznej", "type": "select", "options": [
                "integrated", "dedicated"]},
            {"key": "search[filter_enum_processorseries_laptops][0]", "label": "Seria procesora", "type": "select", "options": [
                "intel-core-ultra-9", "intel-core-ultra-7", "intel-core-ultra-5", "intel-core-i9", "intel-core-i7", "intel-core-i5", "intel-core-i3",
                "intel-pentium-celeron", "apple-m4-pro-max", "apple-m3-pro-max", "apple-m2-pro-max", "apple-m1-pro-max", "apple-intel",
                "amd-ryzen-ai", "amd-ryzen9", "amd-ryzen7", "amd-ryzen5", "amd-ryzen3", "amd-athlon", "snapdragon-x", "microsoft-sq", "others"]},
            {"key": "search[filter_enum_ramsize_laptops][0]", "label": "Wielkość pamięci RAM", "type": "select", "options": [
                "up-to-4gb", "6gb-12gb", "16gb", "24gb", "32gb", "64gb", "128gb", "others"]},
            {"key": "search[filter_enum_harddisktype_laptops][0]", "label": "Typ dysku twardego", "type": "select", "options": [
                "emmc", "hdd", "ssd", "hdd-ssd", "lack"]},
            {"key": "search[filter_enum_disksize_laptops][0]", "label": "Wielkość dysku", "type": "select", "options": [
                "up-to-128gb", "129gb-256gb", "257gb-512gb", "513gb-999gb", "1tb-and-more", "2tb", "4tb-more"]},
        ],
        "attribute_schema": ["brand", "model", "cpu", "gpu", "gpu_type", "ram_gb", "storage_gb",
                             "storage_bucket", "storage_type", "screen_inches_tenths", "operating_system", "condition"],
        "domain": "laptops",
    },
}


def get_category_definition(category_id: str | None) -> dict[str, Any]:
    return CATEGORY_DEFINITIONS.get(category_id or "televisions", CATEGORY_DEFINITIONS["televisions"])
