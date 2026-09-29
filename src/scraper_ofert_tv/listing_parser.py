import re
import hashlib
from typing import List, Dict, Any, Tuple
from selectolax.parser import HTMLParser
import urllib.parse

def parse_listing(html: str, base_url: str = "https://www.olx.pl") -> Tuple[List[Dict[str, Any]], str]:
    """
    Parsuje HTML strony wynikowej OLX.
    Zwraca krotke: (lista_ofert, nastepna_strona_url)
    """
    parser = HTMLParser(html)
    offers = []
    
    # 1. Znajdowanie ofert
    # OLX czesto uzywa data-cy="l-card" do oznaczania kart z ofertami
    cards = parser.css('div[data-cy="l-card"]')
    
    for i, card in enumerate(cards):
        try:
            offer = _parse_card(card, base_url, i + 1)
            if offer:
                offers.append(offer)
        except Exception as e:
            # W prawdziwym MVP moglibysmy tu logowac parser warnings
            pass
            
    # 2. Szukanie linku do nastepnej strony
    next_page_url = None
    next_link = parser.css_first('a[data-testid="pagination-forward"]')
    if next_link and next_link.attributes.get('href'):
        href = next_link.attributes.get('href')
        next_page_url = urllib.parse.urljoin(base_url, href)
        
    return offers, next_page_url

def _parse_card(card, base_url: str, position: int) -> Dict[str, Any]:
    a_tag = card.css_first('a')
    if not a_tag or not a_tag.attributes.get('href'):
        return None
        
    href = a_tag.attributes.get('href')
    # Budowanie absolutnego URL, jesli to relatywny
    url = urllib.parse.urljoin(base_url, href)
    
    # Canonical URL - do deduplikacji, pozbywamy sie np. parametrow ?reason=...
    canonical_url = url.split('?')[0] if '?' in url else url
    
    # ID oferty z OLX (mozna z atrybutu ID jesli to numeryczne, albo z konca URL np. ID12345.html)
    olx_offer_id = card.attributes.get('id')
    if not olx_offer_id or not olx_offer_id.isdigit():
        # Sprobojmy wyciagnac z URL - zazwyczaj to ID<numer>.html
        match = re.search(r'ID(\d+)\.html', url)
        if match:
            olx_offer_id = match.group(1)
            
    title_tag = card.css_first('h6')
    title = title_tag.text(strip=True) if title_tag else ""
    
    price_tag = card.css_first('p[data-testid="ad-price"]')
    raw_price = price_tag.text(strip=True) if price_tag else ""
    price_pln, is_free, negotiable = _parse_price(raw_price)
    
    loc_date_tag = card.css_first('p[data-testid="location-date"]')
    raw_location = loc_date_tag.text(strip=True) if loc_date_tag else ""
    
    img_tag = card.css_first('img')
    thumbnail = img_tag.attributes.get('src') if img_tag else None
    
    # URL Hash do deduplikacji w razie braku ID
    url_hash = hashlib.md5(canonical_url.encode('utf-8')).hexdigest()
    
    return {
        'url': url,
        'canonical_url': canonical_url,
        'url_hash': url_hash,
        'olx_offer_id': olx_offer_id,
        'title': title,
        'raw_title': title,
        'price_pln': price_pln,
        'raw_price': raw_price,
        'negotiable': int(negotiable),
        'is_free': int(is_free),
        'raw_location': raw_location,
        'listing_thumbnail_url': thumbnail,
        'listing_position': position
    }

def _parse_price(raw_price: str) -> Tuple[int, bool, bool]:
    if not raw_price:
        return None, False, False
        
    raw_lower = raw_price.lower()
    is_free = "za darmo" in raw_lower
    negotiable = "do negocjacji" in raw_lower
    
    if is_free:
        return 0, True, negotiable
        
    # Wyciagamy liczby
    # Np. "1 500 zł" -> 1500
    cleaned = re.sub(r'[^\d,.]', '', raw_price.split(',')[0].split('.')[0])
    try:
        if cleaned:
            return int(cleaned), False, negotiable
    except ValueError:
        pass
        
    return None, False, negotiable
