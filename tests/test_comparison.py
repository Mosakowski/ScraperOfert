from scraper_ofert_tv.comparison import generate_comparable_keys

def test_strategy_c_not_used_when_tech_unknown():
    keys = generate_comparable_keys({
        'brand': 'lg',
        'native_olx_bucket': '40-49',
        'technology': 'unknown'
    })
    assert 'C' not in keys
    assert 'D' in keys
    
def test_strategy_b_not_used_when_missing_exact_data():
    # brand = 'inne'
    keys = generate_comparable_keys({
        'brand': 'inne',
        'size_inches': 55,
        'technology': 'oled',
        'resolution': '4k'
    })
    assert 'B' not in keys
    
    # size missing
    keys = generate_comparable_keys({
        'brand': 'samsung',
        'technology': 'qled',
        'resolution': '4k'
    })
    assert 'B' not in keys
    
    # tech unknown
    keys = generate_comparable_keys({
        'brand': 'samsung',
        'size_inches': 55,
        'technology': 'unknown',
        'resolution': '4k'
    })
    assert 'B' not in keys

    # resolution unknown
    keys = generate_comparable_keys({
        'brand': 'samsung',
        'size_inches': 55,
        'technology': 'qled',
        'resolution': 'unknown'
    })
    assert 'B' not in keys
