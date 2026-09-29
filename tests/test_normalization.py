from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.comparison import generate_comparable_key, calculate_confidence

def test_normalization():
    offer = {
        'raw_price': '2 000 zł',
        'is_free': 0,
        'olx_size_bucket': '50-59',
        'raw_location': 'Warszawa, Śródmieście'
    }
    detail = {
        'full_title': 'Telewizor LG 55 cali OLED',
        'description': 'Sprzedam sprawny telewizor z pilotem. Odbior osobisty.',
        'params': {
            'Marka': 'LG',
            'Przekątna ekranu': '55'
        }
    }
    
    normalized = normalize_offer_data(offer, detail)
    assert normalized['brand'] == 'lg'
    assert normalized['size_inches'] == 55
    assert normalized['technology'] == 'oled'
    assert normalized['has_remote'] == 1
    assert normalized['has_box'] == 0
    assert normalized['pickup_only'] == 1
    assert normalized['city'] == 'Warszawa'
    
    comp_key = generate_comparable_key(normalized)
    assert comp_key == 'lg_55_oled_unknown'
    
    confidence = calculate_confidence(normalized, comp_key)
    # Od 1.0 odejmujemy 0.1 za unknown resolution, i 0.1 za brak modelu = 0.8
    assert confidence == 0.9

def test_normalization_no_size():
    offer = {
        'olx_size_bucket': '40-49'
    }
    detail = {
        'full_title': 'Telewizor Sony'
    }
    normalized = normalize_offer_data(offer, detail)
    comp_key = generate_comparable_key(normalized)
    
    assert comp_key == 'sony_40-49_unknown_unknown'
    
    confidence = calculate_confidence(normalized, comp_key)
    # Zaczynamy z 1.0, odejmujemy: 0.5 (brak rozmiaru w calach), 0.1 tech, 0.1 res, 0.1 model = 0.2
    assert round(confidence, 1) == 0.4
