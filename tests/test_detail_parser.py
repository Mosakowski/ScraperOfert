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

def test_parse_current_olx_laptop_detail_markup_and_redact_contacts():
    html = r"""
    <html><head><meta property="og:title" content="Laptop test · OLX.pl"></head>
      <body>
        <h4 data-nx-name="H4">HP ZBook 14 G6 i5 16GB</h4>
        <div data-testid="ad-price-container"><h3 data-nx-name="H3">1 099 zł</h3></div>
        <div data-testid="ad-parameters-container">
          <p>Marka: HP</p><p>Seria procesora: Intel Core i5</p>
          <p>Wielkość pamięci RAM: 16GB</p><p>Typ dysku twardego: SSD</p>
        </div>
        <div data-testid="ad_description"><h3>Opis</h3><div>Sprawny sprzęt. Kontakt test@example.com, 600 /|\ 440 /|\ 570</div></div>
      </body>
    </html>
    """
    data = parse_detail(html)
    assert data["full_title"] == "HP ZBook 14 G6 i5 16GB"
    assert data["raw_price"] == "1 099 zł"
    assert data["params"]["Seria procesora"] == "Intel Core i5"
    assert "test@example.com" not in data["description"]
    assert "600 440 570" not in data["description"]
    assert "600 /|" not in data["description"]
