from typing import Dict, Any, Tuple

def generate_comparable_keys(normalized: Dict[str, Any]) -> Dict[str, str]:
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

def get_strategy_cap(strategy: str) -> float:
    caps = {'A': 0.95, 'B': 0.85, 'C': 0.70, 'D': 0.50}
    return caps.get(strategy, 0.40)

def calculate_normalization_confidence(normalized: Dict[str, Any]) -> float:
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
def generate_comparable_key(normalized: Dict[str, Any]) -> str:
    keys = generate_comparable_keys(normalized)
    return keys.get('A') or keys.get('B') or keys.get('D')

def calculate_confidence(normalized: Dict[str, Any], comparable_key: str) -> float:
    # Przestarzale, zastepowane przez nowa kaskade
    return calculate_normalization_confidence(normalized)
