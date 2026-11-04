import pytest
from scraper_ofert_tv.normalization import _extract_model

def test_extract_model_samsung():
    # UE/QE/TU/AU/CU
    assert _extract_model("samsung", {}, "Sprzedam Samsung UE55RU7102K", "")[0] == "UE55RU7102K"
    assert _extract_model("samsung", {}, "Telewizor QE65Q80A", "")[0] == "QE65Q80A"
    assert _extract_model("samsung", {}, "TV Samsung TU7102 wroclaw", "")[0] == "TU7102"
    assert _extract_model("samsung", {}, "Samsung AU8002 super", "")[0] == "AU8002"
    assert _extract_model("samsung", {}, "Kupie Samsung CU7172", "")[0] == "CU7172"
    assert _extract_model("samsung", {}, "Samsung qn90b polecam", "")[0] == "QN90B"

def test_extract_model_lg():
    assert _extract_model("lg", {}, "LG OLED55C11LB", "")[0] == "OLED55C11LB"
    assert _extract_model("lg", {}, "LG 55NANO863PA tanio", "")[0] == "NANO863PA"
    assert _extract_model("lg", {}, "LG 65UK6400LF", "")[0] == "65UK6400LF"
    assert _extract_model("lg", {}, "LG 55UM7100PLB", "")[0] == "55UM7100PLB"
    assert _extract_model("lg", {}, "LG 43UN7100", "")[0] == "43UN7100"

def test_extract_model_sony():
    assert _extract_model("sony", {}, "Sony KDL-40W605B", "")[0] == "KDL-40W605B"
    assert _extract_model("sony", {}, "Sony KD-55X85J", "")[0] == "KD-55X85J"
    assert _extract_model("sony", {}, "Sony XR-65A80J OLED", "")[0] == "XR-65A80J"

def test_extract_model_philips():
    assert _extract_model("philips", {}, "Philips 55PUS7906", "")[0] == "55PUS7906"
    assert _extract_model("philips", {}, "Philips 65OLED706", "")[0] == "65OLED706"

def test_extract_model_panasonic():
    assert _extract_model("panasonic", {}, "Panasonic TX-55HZ1000E", "")[0] == "TX-55HZ1000E"
    
def test_extract_model_tcl():
    assert _extract_model("tcl", {}, "TCL 55C725", "")[0] == "55C725"
    assert _extract_model("tcl", {}, "TCL 43P615", "")[0] == "43P615"

def test_extract_model_none():
    assert _extract_model("samsung", {}, "Sprzedam telewizor", "")[0] is None
    
def test_extract_model_false_positive():
    # 4K, Smart TV, LED, 55 cali
    assert _extract_model("samsung", {}, "Samsung 43 cale 4K Smart TV", "")[0] is None
    assert _extract_model("samsung", {}, "Samsung 75 cali", "")[0] is None
    assert _extract_model("lg", {}, "LG 55 cali OLED", "")[0] is None
    assert _extract_model("inne", {}, "Telewizor 40 cali LED", "")[0] is None
    assert _extract_model("samsung", {}, "Samsung QLED 65", "")[0] is None
    assert _extract_model("lg", {}, "LG OLED LED TV 55", "")[0] is None
