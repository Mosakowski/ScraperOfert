import re
from typing import Dict, Any, Tuple
import json

# Popularne marki
BRANDS = [
    "samsung", "lg", "sony", "philips", "panasonic", "tcl", "hisense", "toshiba", 
    "sharp", "manta", "kiano", "xiaomi", "blaupunkt", "thomson", "telefunken", "jvc", "hitachi",
    "apple", "lenovo", "dell", "hp", "hewlett-packard", "asus", "acer", "msi", "gigabyte",
    "razer", "huawei", "microsoft", "dynabook", "fujitsu", "medion", "realme"
]

# Technologie
TECH = ["oled", "qled", "miniled", "microled", "nanocell", "led", "lcd", "plasma", "plazma"]

# Rozdzielczosci
RES = ["8k", "4k", "uhd", "fhd", "full hd", "fullhd", "hd ready", "hd", "1080p", "720p"]

def normalize_offer_data(offer: Dict[str, Any], detail: Dict[str, Any], specs_cache: Dict[Tuple[str, str], Dict[str, Any]] = None,
                        category_id: str = "televisions") -> Dict[str, Any]:
    if category_id == "laptops":
        return _normalize_laptop_offer(offer, detail)
    if category_id != "televisions":
        return _normalize_generic_offer(offer, detail, category_id)
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


def _normalize_laptop_offer(offer: Dict[str, Any], detail: Dict[str, Any]) -> Dict[str, Any]:
    params = detail.get("params") or {}
    title = detail.get("full_title") or offer.get("title") or ""
    description = detail.get("description") or ""
    full_text = f"{title} {description}"
    lower = full_text.lower()
    brand_param = next((str(v) for k, v in params.items() if k.lower() in ("marka", "producent")), "")
    brand, brand_source = _normalize_brand(brand_param, title, description)

    model_param = next((str(v) for k, v in params.items() if k.lower() in ("model", "seria")), "")
    if model_param:
        model = model_param.strip()
        model_source = "params"
    else:
        model_match = re.search(r"\b(?:thinkpad|thinkbook|ideapad|latitude|precision|inspiron|xps|probook|elitebook|pavilion|zenbook|vivobook|tuf|rog|legion|ideapad|macbook(?:\s+(?:air|pro))?|aspire|swift|travelmate|toughbook|predator|nitro|surface\s+laptop)\s*[a-z0-9 .-]{0,18}", title, re.I)
        model = re.sub(r"\s+", " ", model_match.group(0)).strip(" -") if model_match else None
        model_source = "title" if model else "none"

    def param_value(keys):
        return next((str(v).strip() for k, v in params.items() if k.lower() in keys and str(v).strip()), None)

    cpu = param_value({"procesor", "model procesora", "cpu"})
    gpu = param_value({"karta graficzna", "układ graficzny", "uklad graficzny", "gpu"})
    ram_raw = param_value({"pamięć ram", "pamiec ram", "ram", "wielkość pamięci ram", "wielkosc pamieci ram"})
    storage_raw = param_value({"dysk", "pojemność dysku", "pojemnosc dysku", "typ dysku", "storage"})
    screen_raw = param_value({"przekątna ekranu", "przekatna ekranu", "wielkość ekranu", "wielkosc ekranu", "rozmiar ekranu"})

    if not cpu:
        m = re.search(r"\b((?:intel\s+)?core\s+i[3579]-?\w+|core\s+ultra\s+[579]\s+\w+|ryzen\s+[3579]\s+\w+|apple\s+m[1-5](?:\s+(?:pro|max|ultra))?)\b", lower, re.I)
        cpu = m.group(1) if m else None
    if not gpu:
        m = re.search(r"\b(rtx\s?\d{3,4}(?:\s?ti)?|gtx\s?\d{3,4}(?:\s?ti)?|radeon\s?(?:rx\s?)?\d{3,4}|arc\s?a\d{3})\b", lower, re.I)
        gpu = m.group(1) if m else None
    ram_gb = None
    ram_source = ram_raw or ""
    if ram_raw:
        m = re.search(r"\d{1,3}", ram_raw)
        ram_gb = int(m.group()) if m else None
    if ram_gb is None:
        m = re.search(r"\b(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\s*(?:ram|d\d|lpddr)?\b|\b(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\b.{0,10}\bram\b", lower)
        ram_gb = int(next(x for x in m.groups() if x)) if m else None
        ram_source = "title" if m else "none"
    storage_gb = None
    if storage_raw:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(tb|gb)", storage_raw, re.I)
        if m:
            storage_gb = int(float(m.group(1).replace(",", ".")) * (1024 if m.group(2).lower() == "tb" else 1))
    if storage_gb is None:
        m = re.search(r"\b(128|256|512|1000|1024|2000|2048|4000|4096)\s*(gb|tb)\b.{0,12}\b(ssd|hdd|nvme)?\b|\b(ssd|nvme)\s*(\d{3,4})\s*(gb|tb)\b", lower, re.I)
        if m:
            value = m.group(1) or m.group(5)
            unit = m.group(2) or m.group(6)
            storage_gb = int(value) * (1024 if unit and unit.lower() == "tb" else 1)
    screen_inches = None
    screen_candidate = screen_raw or ""
    if not screen_candidate:
        m = re.search(r"\b(11(?:\.6)?|12(?:\.\d)?|13(?:\.\d)?|14(?:\.\d)?|15(?:\.\d)?|16(?:\.\d)?|17(?:\.\d)?|18(?:\.\d)?)\s*(?:in|inch|cala|cali|\")", lower)
        screen_candidate = m.group(1) if m else ""
    if screen_candidate:
        m = re.search(r"\d{2}(?:[.,]\d)?", screen_candidate)
        if m:
            screen_inches = int(round(float(m.group().replace(",", ".")) * 10))

    raw_price = detail.get("raw_price") or offer.get("raw_price") or ""
    price, is_free, negotiable = _normalize_price(raw_price)
    city, district = _normalize_location(offer.get("raw_location", ""))
    attributes = {
        "cpu": cpu,
        "gpu": gpu,
        "ram_gb": ram_gb,
        "storage_gb": storage_gb,
        "screen_inches_tenths": screen_inches,
        "condition": param_value({"stan", "condition"}),
        "product_kind": "laptop",
    }
    attrs = {k: v for k, v in attributes.items() if v is not None}
    return {
        "price_pln": price if price is not None else offer.get("price_pln"),
        "is_free": int(is_free), "negotiable": int(negotiable),
        "brand": brand, "model_name": model, "technology": None, "resolution": None,
        "size_inches": None, "native_olx_bucket": None, "city": city, "district": district,
        "has_remote": 0, "has_stand": 0, "has_box": 0, "pickup_only": 0, "delivery_possible": 0,
        "attributes": attrs,
        "diagnostics": {"brand_source": brand_source, "model_source": model_source,
                        "category": "laptops", "cpu_source": "params" if cpu and cpu == param_value({"procesor", "model procesora", "cpu"}) else ("title" if cpu else "none"),
                        "ram_source": "params" if ram_raw else ram_source},
    }


def _normalize_generic_offer(offer: Dict[str, Any], detail: Dict[str, Any], category_id: str) -> Dict[str, Any]:
    params = detail.get("params") or {}
    title = detail.get("full_title") or offer.get("title") or ""
    description = detail.get("description") or ""
    raw_price = detail.get("raw_price") or offer.get("raw_price") or ""
    price, is_free, negotiable = _normalize_price(raw_price)
    brand_param = next((str(v) for k, v in params.items() if k.lower() in ("marka", "producent", "manufacturer")), "")
    brand, brand_source = _normalize_brand(brand_param, title, description)
    model_param = next((str(v) for k, v in params.items() if k.lower() in ("model", "nazwa modelu")), "")
    model = model_param.strip() or title.strip() or None
    attributes = {re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_"): str(value).strip()
                  for key, value in params.items() if str(value).strip()}
    city, district = _normalize_location(offer.get("raw_location", ""))
    return {
        "price_pln": price if price is not None else offer.get("price_pln"),
        "is_free": int(is_free), "negotiable": int(negotiable), "brand": brand,
        "model_name": model, "technology": None, "resolution": None,
        "size_inches": None, "native_olx_bucket": None, "city": city, "district": district,
        "has_remote": 0, "has_stand": 0, "has_box": 0, "pickup_only": 0, "delivery_possible": 0,
        "attributes": attributes,
        "diagnostics": {"category": category_id, "brand_source": brand_source,
                        "model_source": "params" if model_param else "title_fallback"},
    }
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
