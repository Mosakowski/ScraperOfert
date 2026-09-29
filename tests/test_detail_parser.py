import pytest
from pathlib import Path
from scraper_ofert_tv.detail_parser import parse_detail

def test_parse_detail():
    fixture_path = Path(__file__).parent / "fixtures" / "detail.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    data = parse_detail(html)
    
    assert data["full_title"] == "Telewizor LG OLED 65 cali C1"
    assert data["raw_price"] == "2 500 zł"
    assert "Sprzedam telewizor LG OLED 65 cali model C1" in data["description"]
    assert "Tylko odbior osobisty." in data["description"]
    
    # Parametry
    assert data["params"]["Stan"] == "Używane"
    assert data["params"]["Marka"] == "LG"
    assert data["params"]["Przekątna ekranu"] == "65"
    
    # Zdjecia i sprzedawca
    assert data["images_count"] == 2
    assert data["main_image_url"] == "https://image.url/photo1_full.jpg"
    assert data["seller_name"] == "Jan Kowalski"
    assert data["seller_url"] == "https://www.olx.pl/oferty/uzytkownik/12345/"
    
    assert data["status"] == "active"
