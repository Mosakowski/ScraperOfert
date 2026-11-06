import re
import sqlite3
from typing import Dict, Any, List, Tuple
from scraper_ofert_tv.storage import get_connection

def evaluate_rules(conn: sqlite3.Connection, normalized: Dict[str, Any], detail: Dict[str, Any],
                   category_id: str = "televisions") -> Tuple[List[str], List[str]]:
    """
    Ocenia znormalizowana oferte na podstawie regul opisowych w bazie.
    Zwraca: (lista dopasowanych nazw regul, lista podjetych akcji)
    """
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM description_rules WHERE enabled = 1
        AND (product_category_id IS NULL OR product_category_id = ?)""", (category_id,))
    rules = cursor.fetchall()
    
    full_text = f"{detail.get('full_title', '')} {detail.get('description', '')}"
    title_text = detail.get('full_title', '')
    desc_text = detail.get('description', '')
    
    matched_rules = []
    actions = []
    
    for row in rules:
        target_field = row['applies_to']
        match_mode = row['match_mode']
        import json
        patterns = json.loads(row['patterns_json'])
        action = row['action']
        
        text_to_search = full_text
        if target_field == 'title':
            text_to_search = title_text
        elif target_field == 'description':
            text_to_search = desc_text
            
        matched = False
        for pattern in patterns:
            if match_mode in ('contains', 'phrase'):
                if pattern.lower() in text_to_search.lower():
                    matched = True
                    break
            elif match_mode == 'regex':
                try:
                    if re.search(pattern, text_to_search, re.IGNORECASE):
                        matched = True
                        break
                except re.error:
                    pass
                
        if matched:
            matched_rules.append({
                'rule_id': row['id'],
                'category': row['category'],
                'severity': row['severity'],
                'action': action,
                'score_delta': row['score_delta']
            })
            if action not in actions:
                actions.append(action)
                
    return matched_rules, actions
