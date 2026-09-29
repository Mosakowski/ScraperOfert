import re
from typing import Dict, Any, Tuple
from selectolax.parser import HTMLParser

def parse_detail(html: str) -> Dict[str, Any]:
    parser = HTMLParser(html)
    
    # 1. Tytul
    title_tag = parser.css_first('div[data-cy="ad_title"] h1')
    title = title_tag.text(strip=True) if title_tag else ""
    
    # 2. Cena
    price_tag = parser.css_first('div[data-testid="ad-price-container"] h3')
    raw_price = price_tag.text(strip=True) if price_tag else ""
    
    # 3. Opis
    desc_tag = parser.css_first('div[data-cy="ad_description"] div')
    description = desc_tag.text(strip=True, separator='\n') if desc_tag else ""
    
    # 4. Parametry
    params = {}
    param_list = parser.css('ul > li > p')
    for p in param_list:
        text = p.text(strip=True)
        if ":" in text:
            key, val = text.split(":", 1)
            params[key.strip()] = val.strip()
            
    # 5. Zdjecia (tylko glowne!)
    images = parser.css('div.swiper-slide img')
    num_images = len(images)
    main_image = images[0].attributes.get('src') if num_images > 0 else None
    
    # 6. Sprzedawca
    seller_name = ""
    seller_url = None
    seller_card = parser.css_first('div[data-cy="seller_card"]')
    if seller_card:
        h2 = seller_card.css_first('h2')
        if h2:
            seller_name = h2.text(strip=True)
        a = seller_card.css_first('a')
        if a:
            seller_url = a.attributes.get('href')
            
    # Status na OLX - zazwyczaj jesli jest "To ogloszenie jest nieaktualne" to cos wiemy, 
    # w przeciwnym razie zakladamy ze aktywna
    status = "active"
    if "To ogłoszenie nie jest już dostępne" in html or "Ogloszenie nieaktualne" in html:
        status = "inactive"
        
    return {
        "full_title": title,
        "raw_price": raw_price,
        "description": description,
        "params": params,
        "images_count": num_images,
        "main_image_url": main_image,
        "seller_name": seller_name,
        "seller_url": seller_url,
        "status": status
    }
