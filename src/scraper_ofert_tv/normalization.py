import re
from typing import Dict, Any, Tuple
import json

# Popularne marki
BRANDS = [
    "samsung", "lg", "sony", "philips", "panasonic", "tcl", "hisense", "toshiba", 
    "sharp", "manta", "kiano", "xiaomi", "blaupunkt", "thomson", "telefunken", "jvc", "hitachi"
]

# Technologie
TECH = ["oled", "qled", "miniled", "microled", "nanocell", "led", "lcd", "plasma", "plazma"]

# Rozdzielczosci
RES = ["8k", "4k", "uhd", "fhd", "full hd", "fullhd", "hd ready", "hd", "1080p", "720p"]

def normalize_offer_data(offer: Dict[str, Any], detail: Dict[str, Any], specs_cache: Dict[Tuple[str, str], Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = {}
    diagnostics = {}
    
    full_title = detail.get('full_title', '') or ''
    description = detail.get('description', '') or ''
    full_text = f"{full_title} {description}".lower()
    
    # Cena
    price, is_free, negotiable = _normalize_price(detail.get('raw_price', offer.get('raw_price')))
    normalized['price_pln'] = price if price is not None else offer.get('price_pln')
    normalized['is_free'] = is_free if is_free else offer.get('is_free', 0)
    normalized['negotiable'] = negotiable if negotiable else offer.get('negotiable', 0)
    
    # Marka
    params = detail.get('params', {})
    brand, brand_src = _normalize_brand(params.get('Marka', ''), full_title, description)
    normalized['brand'] = brand
    diagnostics['brand_source'] = brand_src
    
    # Model
    model, model_src = _extract_model(brand, params, full_title, description)
    normalized['model_name'] = model
    diagnostics['model_source'] = model_src
    
    # Rozmiar
    inches, size_src = _normalize_size(params.get('Przekątna ekranu', ''), full_text, full_title, description, model)
    normalized['size_inches'] = inches
    normalized['native_olx_bucket'] = offer.get('olx_size_bucket')
    diagnostics['size_source'] = size_src
    
    # Technologia
    tech, tech_src = _extract_technology(params, full_title, description)
    normalized['technology'] = tech
    diagnostics['technology_source'] = tech_src
    
    # Rozdzielczosc
    res, res_src = _extract_resolution(params, full_title, description)
    normalized['resolution'] = res
    diagnostics['resolution_source'] = res_src
    
    # Lokalizacja
    loc = offer.get('raw_location', '')
    city, district = _normalize_location(loc)
    normalized['city'] = city
    normalized['district'] = district
    
    # Inne
    normalized['has_remote'] = int(bool(re.search(r'\bpilot(a|em)?\b', full_text)))
    normalized['has_stand'] = int(bool(re.search(r'\bpodstaw(a|k(a|i|ą))\b|\bn(o|ó)żk(i|ami)\b', full_text)))
    normalized['has_box'] = int(bool(re.search(r'\bpudełk(o|iem|a)\b|\bkarton(em|u)?\b|\boryginaln(e|ym) opakowani(e|em|u)\b', full_text)))
    normalized['pickup_only'] = int(bool(re.search(r'\bodbi(o|ó)r (tylko )?osobisty\b|\bnie wysyłam\b', full_text)))
    normalized['delivery_possible'] = int(bool(re.search(r'\bwysyłka\b|\bmożliwy transport\b|\bdostarczę\b', full_text)))
    
    normalized['diagnostics'] = diagnostics
    
    if specs_cache is not None:
        enrich_with_model_specs(normalized, diagnostics, specs_cache)
        
    return normalized

def enrich_with_model_specs(normalized: Dict[str, Any], diagnostics: Dict[str, Any], specs_cache: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
    brand = normalized.get('brand')
    model = normalized.get('model_name')
    if not brand or not model or brand == 'inne':
        return
        
    normalized_model = "".join(c.lower() for c in model if c.isalnum())
    spec = specs_cache.get((brand.lower(), normalized_model))
    if not spec:
        return
        
    used_fields = []
    
    # Rozmiar
    if not normalized.get('size_inches') and spec.get('screen_size_inches'):
        normalized['size_inches'] = spec['screen_size_inches']
        diagnostics['size_source'] = 'model_specs'
        used_fields.append('size_inches')
        
    # Technologia
    if not normalized.get('technology') and spec.get('technology'):
        normalized['technology'] = spec['technology']
        diagnostics['technology_source'] = 'model_specs'
        used_fields.append('technology')
        
    # Rozdzielczość
    if not normalized.get('resolution') and spec.get('resolution'):
        normalized['resolution'] = spec['resolution']
        diagnostics['resolution_source'] = 'model_specs'
        used_fields.append('resolution')
        
    if used_fields:
        diagnostics['model_specs_used'] = True
        diagnostics['model_specs_fields'] = used_fields
        diagnostics['model_specs_confidence'] = spec.get('spec_confidence', 0.8)

def _normalize_price(raw_price: str) -> Tuple[int, bool, bool]:
    if not raw_price: return None, False, False
    raw_lower = raw_price.lower()
    is_free = "za darmo" in raw_lower
    negotiable = "do negocjacji" in raw_lower
    if is_free: return 0, True, negotiable
    cleaned = re.sub(r'[^\d]', '', raw_price.split(',')[0].split('.')[0])
    try:
        if cleaned: return int(cleaned), False, negotiable
    except ValueError: pass
    return None, False, negotiable

def _normalize_size(param_size: str, full_text: str, title: str, desc: str, model: str) -> Tuple[int, str]:
    if param_size:
        cleaned = re.sub(r'[^\d]', '', param_size)
        if cleaned.isdigit():
            val = int(cleaned)
            if 10 <= val <= 150: return val, "params"
            
    if model:
        # Wzorzec: zazwyczaj pierwsze dwie cyfry w modelu TV (od 24 do 98) oznaczaja rozmiar
        m = re.search(r'(\d{2})', model)
        if m:
            val = int(m.group(1))
            if 24 <= val <= 98: return val, "model"
    
    for src_text, src_name in [(title, "title"), (desc, "description")]:
        match = re.search(r'\b(\d{2,3})\s*(cali|cale|cal|inch|"|'')\b', src_text.lower())
        if match:
            val = int(match.group(1))
            if 10 <= val <= 150: return val, src_name
            
    return None, "none"

def _normalize_brand(param_brand: str, title: str, desc: str) -> Tuple[str, str]:
    if param_brand:
        pb = param_brand.lower().strip()
        if pb in BRANDS: return pb, "params"
        for b in BRANDS:
            if b in pb: return b, "params"
            
    for src_text, src_name in [(title, "title"), (desc, "description")]:
        low = src_text.lower()
        for b in BRANDS:
            if re.search(fr'\b{b}\b', low): return b, src_name
            
    return "inne", "none"

def _extract_model(brand: str, params: dict, title: str, desc: str) -> Tuple[str, str]:
    # false positive avoid
    fps = {"4k", "led", "smart", "smarttv", "tv", "hdr", "hd", "lcd", "oled", "qled", "uhd", "sprzedam"}
    fps.add(brand.lower())
    
    # 1. Wzorce dla poszczególnych marek
    patterns = []
    if brand == "samsung":
        patterns.append(r'\b([UuQq][Ee]\d{2}[A-Za-z0-9]{2,10})\b')
        patterns.append(r'\b([Qq][Nn]\d{2}[A-Za-z0-9]{2,10})\b')
        patterns.append(r'\b([TtAaCc][Uu]\d{2}[A-Za-z0-9]{2,10})\b')
    elif brand == "lg":
        patterns.append(r'\b(?:\d{2})?(OLED\d{2}[A-Za-z0-9]{1,8})\b')
        patterns.append(r'\b(\d{2}[Uu][KkMmNnPp][A-Za-z0-9]{2,8})\b')
        patterns.append(r'\b(?:\d{2})?(NANO\d{2}[A-Za-z0-9]{1,8})\b')
    elif brand == "sony":
        patterns.append(r'\b(KD[L]?-\d{2}[A-Za-z0-9]{2,8})\b')
        patterns.append(r'\b(XR-\d{2}[A-Za-z0-9]{2,8})\b')
    elif brand == "philips":
        patterns.append(r'\b(\d{2}PUS\d{3,5})\b')
        patterns.append(r'\b(\d{2}OLED\d{3,5})\b')
    elif brand == "panasonic":
        patterns.append(r'\b(TX-\d{2}[A-Za-z0-9]{2,8})\b')
    elif brand == "tcl":
        patterns.append(r'\b(\d{2}[CP]\d{2,4}[A-Za-z0-9]{0,4})\b')
    elif brand == "hisense":
        patterns.append(r'\b([HUA]\d{2}[A-Za-z0-9]{2,8})\b')
        
    patterns.append(r'\b([A-Za-z0-9]{5,15})\b') # ogólny fallback dla np. Sharp
    
    def check_text(t: str) -> str:
        for p in patterns:
            for m in re.finditer(p, t, re.IGNORECASE):
                cand = m.group(1).upper()
                if cand.lower() not in fps and not cand.isdigit() and "cali" not in cand.lower() and "cale" not in cand.lower():
                    # model powinien miec zazwyczaj cyfry i litery (albo same litery dla niektorych wyjatkow, 
                    # ale zeby uniknac false positives, dla fallback wymuszamy cyfre i litere)
                    if any(c.isalpha() for c in cand) and any(c.isdigit() for c in cand):
                        return cand
                    # Jesli to nie jest fallback pattern, pozwalamy na same litery (np modele bez cyfr, ale to rzadkosc w TV)
                    elif p != r'\b([A-Za-z0-9]{5,15})\b' and any(c.isalpha() for c in cand):
                        return cand
        return None

    # Zwykle param nie ma modelu, ale jesli ma (np "Model"):
    if "Model" in params:
        cand = check_text(params["Model"])
        if cand: return cand, "params"

    cand = check_text(title)
    if cand: return cand, "title"
    
    cand = check_text(desc)
    if cand: return cand, "description"

    return None, "none"

def _extract_technology(params: dict, title: str, desc: str) -> Tuple[str, str]:
    # 1. Params
    for k, v in params.items():
        vlow = str(v).lower()
        for t in TECH:
            if re.search(fr'\b{t}\b', vlow):
                return t, "params"
    
    # 2. Title
    tlow = title.lower()
    for t in TECH:
        if re.search(fr'\b{t}\b', tlow):
            return t, "title"
            
    # 3. Desc
    dlow = desc.lower()
    for t in TECH:
        if re.search(fr'\b{t}\b', dlow):
            return t, "description"
            
    return None, "none"

def _extract_resolution(params: dict, title: str, desc: str) -> Tuple[str, str]:
    for k, v in params.items():
        vlow = str(v).lower()
        for r in RES:
            if r == "4k" or r == "8k":
                if re.search(fr'\b{r}\b', vlow) or re.search(fr'\b{r}uhd\b', vlow): return r, "params"
            else:
                if re.search(fr'\b{r}\b', vlow): return r, "params"
                
    for src_text, src_name in [(title, "title"), (desc, "description")]:
        low = src_text.lower()
        for r in RES:
            if r == "4k" or r == "8k":
                if re.search(fr'\b{r}\b', low) or re.search(fr'\b{r}uhd\b', low): return r, src_name
            else:
                if re.search(fr'\b{r}\b', low): return r, src_name
                
    return None, "none"

def _normalize_location(raw_loc: str) -> Tuple[str, str]:
    if not raw_loc: return None, None
    parts = raw_loc.split('-')[0].strip().split(',')
    city = parts[0].strip() if len(parts) > 0 else None
    district = parts[1].strip() if len(parts) > 1 else None
    return city, district
