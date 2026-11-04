import pytest
from pathlib import Path
from scraper_ofert_tv.listing_parser import parse_listing, _parse_price

def test_parse_price():
    price, is_free, is_nego = _parse_price("1 500 zł")
    assert price == 1500
    assert not is_free
    assert not is_nego
    
    price, is_free, is_nego = _parse_price("1500,50 zł do negocjacji")
    assert price == 1500
    assert not is_free
    assert is_nego
    
    price, is_free, is_nego = _parse_price("Za darmo")
    assert price == 0
    assert is_free
    assert not is_nego

def test_parse_listing():
    fixture_path = Path(__file__).parent / "fixtures" / "listing.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    offers, next_url, warnings = parse_listing(html)
    
    assert len(offers) == 2
    
    assert offers[0]['title'] == "Telewizor Samsung 55 cali"
    assert offers[0]['price_pln'] == 500
    assert offers[0]['olx_offer_id'] == "123456789" # z atrybutu ID
    assert offers[0]['canonical_url'] == "https://www.olx.pl/oferta/telewizor-samsung-55-cali-ID12345.html"
    assert offers[0]['listing_thumbnail_url'] == "https://image.url/thumb.jpg"
    assert offers[0]['raw_location'] == "Warszawa, Mokotów - Dzisiaj o 10:00"
    
    assert offers[1]['title'] == "LG OLED 65 Uszkodzony"
    assert offers[1]['price_pln'] == 0
    assert offers[1]['is_free'] == 1
    # Sprawdzamy wyciaganie z URL
    assert offers[1]['olx_offer_id'] == "987654321" 
    
    assert next_url == "https://www.olx.pl/elektronika/telewizory/?page=2"
