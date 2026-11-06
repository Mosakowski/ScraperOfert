from typing import Dict, Any, Tuple

def generate_comparable_keys(normalized: Dict[str, Any], category_id: str = "televisions") -> Dict[str, str]:
    if category_id == "laptops":
        return _generate_laptop_comparable_keys(normalized)
    if category_id != "televisions":
        return _generate_generic_comparable_keys(normalized, category_id)
    brand = normalized.get('brand') or 'inne'
    size = normalized.get('size_inches')
    tech = normalized.get('technology') or 'unknown'
    res = normalized.get('resolution') or 'unknown'
    model = normalized.get('model_name')
    bucket = normalized.get('native_olx_bucket') or 'unknown_size'
    
    keys = {}
    
    # D: brand + bucket
    keys['D'] = f"{brand}_{bucket}"
    
    # C: brand + bucket + tech
    if tech and tech not in ('unknown', '-'):
        keys['C'] = f"{brand}_{bucket}_{tech}"
    
    # B: brand + exact size + tech + res
    if size and tech and tech not in ('unknown', '-') and res and res not in ('unknown', '-') and brand != 'inne':
        keys['B'] = f"{brand}_{size}_{tech}_{res}"
        
    # A: brand + exact model
    if model:
        clean_model = "".join(c.lower() for c in model if c.isalnum())
        keys['A'] = f"{brand}_{clean_model}"
        
    return keys


def _generate_laptop_comparable_keys(normalized: Dict[str, Any]) -> Dict[str, str]:
    attrs = normalized.get("attributes") or {}
    brand = (normalized.get("brand") or "unknown").strip().lower()
    model = normalized.get("model_name")
    clean_model = "".join(c.lower() for c in model if c.isalnum()) if model else None
    cpu = "".join(c.lower() for c in str(attrs.get("cpu", "")).split() if c.isalnum())
    gpu = "".join(c.lower() for c in str(attrs.get("gpu", "")).split() if c.isalnum())
    ram = attrs.get("ram_gb")
    storage = attrs.get("storage_gb")
    keys = {}
    if clean_model:
        keys["A"] = f"laptops|model|{brand}|{clean_model}|{cpu}|{gpu}|{ram}|{storage}"
        keys["B"] = f"laptops|model|{brand}|{clean_model}|{cpu}|{gpu}"
        keys["C"] = f"laptops|model|{brand}|{clean_model}"
    if cpu and gpu:
        keys["D"] = f"laptops|config|{cpu}|{gpu}|{ram}"
    return keys


def _generate_generic_comparable_keys(normalized: Dict[str, Any], category_id: str) -> Dict[str, str]:
    brand = (normalized.get("brand") or "unknown").strip().lower()
    model = normalized.get("model_name") or ""
    clean_model = "".join(c.lower() for c in model if c.isalnum())
    attributes = normalized.get("attributes") or {}
    signature = "|".join(f"{k}={str(v).lower()}" for k, v in sorted(attributes.items())[:4])
    keys = {}
    if clean_model:
        keys["A"] = f"{category_id}|model|{brand}|{clean_model}"
    if signature:
        keys["B"] = f"{category_id}|attrs|{brand}|{signature}"
    if brand != "unknown":
        keys["D"] = f"{category_id}|brand|{brand}"
    return keys

def get_strategy_cap(strategy: str) -> float:
    caps = {'A': 0.95, 'B': 0.85, 'C': 0.70, 'D': 0.50}
    return caps.get(strategy, 0.40)

def calculate_normalization_confidence(normalized: Dict[str, Any], category_id: str = "televisions") -> float:
    if category_id == "laptops":
        attrs = normalized.get("attributes") or {}
        score = 0.2
        if normalized.get("brand") not in (None, "", "inne", "unknown"):
            score += 0.2
        if normalized.get("model_name"):
            score += 0.3
        if attrs.get("cpu"):
            score += 0.15
        if attrs.get("gpu") or attrs.get("ram_gb"):
            score += 0.15
        return min(1.0, score)
    if category_id != "televisions":
        attributes = normalized.get("attributes") or {}
        return min(0.65, 0.25 + (0.2 if normalized.get("brand") not in (None, "", "inne") else 0)
                   + (0.2 if normalized.get("model_name") else 0) + min(0.2, len(attributes) * 0.04))
    score = 1.0
    diagnostics = normalized.get('diagnostics', {})
    spec_conf = diagnostics.get('model_specs_confidence')
    
    if not normalized.get('resolution') or normalized.get('resolution') == 'unknown':
        score -= 0.1
    elif diagnostics.get('resolution_source') == 'model_specs' and spec_conf is not None:
        score -= (1.0 - spec_conf) * 0.1
        
    if not normalized.get('technology') or normalized.get('technology') == 'unknown':
        score -= 0.1
    elif diagnostics.get('technology_source') == 'model_specs' and spec_conf is not None:
        score -= (1.0 - spec_conf) * 0.1
        
    if not normalized.get('size_inches'):
        score -= 0.2
    elif diagnostics.get('size_source') == 'model_specs' and spec_conf is not None:
        score -= (1.0 - spec_conf) * 0.2
        
    return max(0.2, score)

# Zachowujemy dla kompatybilnosci w niektorych miejscach (np. eksport)
def generate_comparable_key(normalized: Dict[str, Any], category_id: str = "televisions") -> str:
    keys = generate_comparable_keys(normalized, category_id)
    return keys.get('A') or keys.get('B') or keys.get('D')

def calculate_confidence(normalized: Dict[str, Any], comparable_key: str, category_id: str = "televisions") -> float:
    # Przestarzale, zastepowane przez nowa kaskade
    return calculate_normalization_confidence(normalized, category_id)
