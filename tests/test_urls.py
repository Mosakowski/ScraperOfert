from scraper_ofert_tv.olx_urls import build_olx_search_url
import urllib.parse

def test_national_url():
    url = build_olx_search_url(
        mode="national",
        price_min=300,
        price_max=700,
        size_filter="40-49"
    )
    url_decoded = urllib.parse.unquote(url)
    assert "https://www.olx.pl/elektronika/tv/telewizory/" in url_decoded
    assert "search[filter_float_price:from]=300" in url_decoded
    assert "search[filter_float_price:to]=700" in url_decoded
    assert "search[filter_enum_state][0]=used" in url_decoded
    assert "search[private_business]=private" in url_decoded
    assert "search[filter_enum_size][0]=40-49" in url_decoded

def test_lodz_alerts_url():
    url = build_olx_search_url(
        mode="lodz_alerts",
        location="lodz",
        radius_km=50,
        size_filter="50-59"
    )
    url_decoded = urllib.parse.unquote(url)
    assert "https://www.olx.pl/elektronika/tv/telewizory/lodz/" in url_decoded
    assert "search[dist]=50" in url_decoded
    assert "search[filter_enum_size][0]=50-59" in url_decoded

def test_pagination_url():
    url = build_olx_search_url(page=3)
    assert "page=3" in url
