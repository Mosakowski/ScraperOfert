from scraper_ofert_tv.normalization import normalize_offer_data


def _tv(title, params, description=""):
    return normalize_offer_data(
        {"raw_price": "300 zł", "price_pln": 300, "olx_size_bucket": "30-39", "raw_location": "Łódź"},
        {"full_title": title, "description": description, "params": params},
        category_id="televisions",
    )


def test_daewoo_model_and_size_from_olx_fields():
    result = _tv("Telewizor LED Daewoo 32 cale", {"Producent": "Pozostałe", "Model": "DLP-32H1", "Rozmiar": "30-39"})
    assert result["brand"] == "daewoo"
    assert result["model_name"] == "DLP-32H1"
    assert result["size_inches"] == 32
    assert result["attributes"]["sale_format"] == "single"


def test_bundle_and_accessory_are_distinct():
    bundle = _tv("Zestaw Telewizor Thomson 32 + szafka pod TV + antena + dekoder", {})
    multiple = _tv("Telewizory i elektronika tylko całość", {})
    accessory = _tv("Telewizor Philips 32 cale z dekoderem", {})
    assert bundle["attributes"]["sale_format"] == "bundle_multiple"
    assert multiple["attributes"]["sale_format"] == "bundle_multiple"
    assert accessory["attributes"]["sale_format"] == "single_with_accessories"
