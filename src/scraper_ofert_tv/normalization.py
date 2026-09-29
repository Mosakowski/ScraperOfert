import re
from typing import Dict, Any, Tuple

# Popularne marki dla prostej normalizacji
BRANDS = [
    "samsung", "lg", "sony", "philips", "panasonic", "tcl", "hisense", "toshiba", 
    "sharp", "manta", "kiano", "xiaomi", "blaupunkt", "thomson", "telefunken", "jvc", "hitachi"
]

# Technologie
TECH = ["oled", "qled", "led", "lcd", "plasma", "plazma", "miniled", "microled", "nanocell"]

# Rozdzielczosci
RES = ["8k", "4k", "uhd", "fhd", "full hd", "fullhd", "hd ready", "hd", "1080p", "720p"]

def normalize_offer_data(offer: Dict[str, Any], detail: Dict[str, Any]) -> Dict[str, Any]:
    """
    Przyjmuje podstawowe dane oferty i jej detale, 
    zwraca slownik znormalizowanych wartosci i flag.
    """
    normalized = {}
    
    # 1. Tytul kombi
    full_text = f"{detail.get('full_title', '')} {detail.get('description', '')}".lower()
    
    # 2. Cena
    price, is_free, negotiable = _normalize_price(detail.get('raw_price', offer.get('raw_price')))
    normalized['price_pln'] = price if price is not None else offer.get('price_pln')
    normalized['is_free'] = is_free if is_free else offer.get('is_free', 0)
    normalized['negotiable'] = negotiable if negotiable else offer.get('negotiable', 0)
    
    # 3. Rozmiar
    params = detail.get('params', {})
    inches = _normalize_size(params.get('Przekątna ekranu', ''), full_text)
    normalized['size_inches'] = inches
    normalized['native_olx_bucket'] = offer.get('olx_size_bucket')
    
    # 4. Marka
    brand = _normalize_brand(params.get('Marka', ''), full_text)
    normalized['brand'] = brand
    
    # 5. Model (uproszczony)
    normalized['model_name'] = _extract_model(full_text, brand)
    
    # 6. Technologia i rozdzielczosc
    normalized['technology'] = _extract_keyword(full_text, TECH)
    normalized['resolution'] = _extract_keyword(full_text, RES)
    
    # 7. Lokalizacja
    loc = offer.get('raw_location', '')
    city, district = _normalize_location(loc)
    normalized['city'] = city
    normalized['district'] = district
    
    # 8. Akcesoria / Wyposazenie (flagi binarne)
    normalized['has_remote'] = int(bool(re.search(r'\bpilot(a|em)?\b', full_text)))
    normalized['has_stand'] = int(bool(re.search(r'\bpodstaw(a|k(a|i|ą))\b|\bn(o|ó)żk(i|ami)\b', full_text)))
    normalized['has_box'] = int(bool(re.search(r'\bpudełk(o|iem|a)\b|\bkarton(em|u)?\b|\boryginaln(e|ym) opakowani(e|em|u)\b', full_text)))
    
    # 9. Dostawa / Odbior
    normalized['pickup_only'] = int(bool(re.search(r'\bodbi(o|ó)r (tylko )?osobisty\b|\bnie wysyłam\b', full_text)))
    normalized['delivery_possible'] = int(bool(re.search(r'\bwysyłka\b|\bmożliwy transport\b|\bdostarczę\b', full_text)))
    
    # 10. Budowa comparable_key
    # Bedzie budowany w oddzielnym module comparison.py
    return normalized

def _normalize_price(raw_price: str) -> Tuple[int, bool, bool]:
    if not raw_price:
        return None, False, False
        
    raw_lower = raw_price.lower()
    is_free = "za darmo" in raw_lower
    negotiable = "do negocjacji" in raw_lower
    
    if is_free:
        return 0, True, negotiable
        
    cleaned = re.sub(r'[^\d]', '', raw_price.split(',')[0].split('.')[0])
    try:
        if cleaned:
            return int(cleaned), False, negotiable
    except ValueError:
        pass
        
    return None, False, negotiable

def _normalize_size(param_size: str, text: str) -> int:
    # 1. Z parametrow
    if param_size:
        cleaned = re.sub(r'[^\d]', '', param_size)
        if cleaned.isdigit():
            val = int(cleaned)
            if 10 <= val <= 150:
                return val
                
    # 2. Z tekstu np. "55 cali", "55\"", "65inch"
    match = re.search(r'\b(\d{2,3})\s*(cali|cale|cal|inch|"|'')\b', text)
    if match:
        val = int(match.group(1))
        if 10 <= val <= 150:
            return val
            
    return None

def _normalize_brand(param_brand: str, text: str) -> str:
    if param_brand:
        pb = param_brand.lower().strip()
        if pb in BRANDS:
            return pb
        # Niektóre marki mogą być wpisane ręcznie
        for b in BRANDS:
            if b in pb:
                return b
                
    for b in BRANDS:
        # szukaj po granicy slowa zeby nie zlapac np 'lg' w algorytm
        if re.search(fr'\b{b}\b', text):
            return b
            
    return "inne"

def _extract_keyword(text: str, keywords: list) -> str:
    for kw in keywords:
        if kw == "4k" or kw == "8k":
            # specjalne traktowanie 4k
            if re.search(fr'\b{kw}\b', text) or re.search(fr'\b{kw}uhd\b', text):
                return kw
        elif re.search(fr'\b{kw}\b', text):
            return kw
    return None

def _extract_model(text: str, brand: str) -> str:
    """Bardzo uproszczona ekstrakcja modelu dla MVP"""
    # W MVP modelu mozna nie ustalac, albo sprobowac zlapac ciag liter i cyfr.
    # Uznajemy ze jak nie umiemy znalezc pewnego modelu, zwracamy None.
    # TODO: Mozna dodac lepsze regexy dla znanych marek.
    return None

def _normalize_location(raw_loc: str) -> Tuple[str, str]:
    if not raw_loc:
        return None, None
        
    # Np. "Warszawa, Mokotów - Dzisiaj o 10:00"
    parts = raw_loc.split('-')[0].strip().split(',')
    city = parts[0].strip() if len(parts) > 0 else None
    district = parts[1].strip() if len(parts) > 1 else None
    
    return city, district
