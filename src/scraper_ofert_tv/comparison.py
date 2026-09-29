from typing import Dict, Any, Tuple

def generate_comparable_key(normalized: Dict[str, Any]) -> str:
    """
    Generuje klucz uzywany do grupowania ofert w rynku.
    Np: lg_65_oled_4k
    """
    brand = normalized.get('brand') or 'inne'
    size = normalized.get('size_inches')
    tech = normalized.get('technology') or 'unknown'
    res = normalized.get('resolution') or 'unknown'
    
    # Jesli nie mamy rozmiaru, nie mozemy wygenerowac sensownego klucza
    if not size:
        # Fallback na bucket OLX, jesli jest dostepny
        bucket = normalized.get('native_olx_bucket') or 'unknown_size'
        return f"{brand}_{bucket}_{tech}_{res}"
        
    return f"{brand}_{size}_{tech}_{res}"

def calculate_confidence(normalized: Dict[str, Any], comparable_key: str) -> float:
    """
    Oblicza pewnosc co do poprawnosci klucza porownywalnosci i normalizacji.
    0.0 do 1.0 (100%). Zgodnie z AGENT_GUIDE.md "nie udawaj wysokiej pewnosci, jesli dane sa slabe".
    """
    score = 1.0
    
    # Brak dokladnego rozmiaru w calach to ogromny spadek pewnosci
    if not normalized.get('size_inches'):
        score -= 0.5
        
    if normalized.get('brand') == 'inne':
        score -= 0.3
        
    if normalized.get('technology') == 'unknown':
        score -= 0.1
        
    if normalized.get('resolution') == 'unknown':
        score -= 0.1
        
    # Jesli brak modelu to lekki minus (choc w MVP rzadko jest model)
    if not normalized.get('model_name'):
        score -= 0.1
        
    return max(0.0, score)
