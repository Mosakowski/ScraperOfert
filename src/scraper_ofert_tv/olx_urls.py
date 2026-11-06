import urllib.parse

BASE_URL = "https://www.olx.pl"
CATEGORY_PATH = "/elektronika/tv/telewizory/"

def build_olx_search_url(
    mode: str = "national",
    location: str = "lodz",
    radius_km: int = 50,
    price_min: int = 300,
    price_max: int = 700,
    seller_type: str = "private",
    condition: str = "used",
    size_filter: str = None,
    page: int = 1,
    category_path: str = None,
    olx_filters: dict = None,
    query: str = None
) -> str:
    """
    Buduje URL wyszukiwania na OLX na podstawie podanych kryteriow.
    """
    
    # Budowa sciezki glownej
    path = category_path or CATEGORY_PATH
    if mode == "lodz_alerts" and location:
        path = f"{path.rstrip('/')}/{location.strip('/')}/"

    url = f"{BASE_URL}{path}"
    
    params = {}
    
    # Cena
    if price_min is not None:
        params["search[filter_float_price:from]"] = price_min
    if price_max is not None:
        params["search[filter_float_price:to]"] = price_max
        
    # Stan (uzywane)
    if condition == "used":
        params["search[filter_enum_state][0]"] = "used"
        
    # Typ sprzedawcy (prywatne)
    if seller_type == "private":
        # W nowszych wersjach OLX uzywa tez owner_type, ale PRD mowi private_business
        params["search[private_business]"] = "private"
        
    # Kategoriowe parametry OLX (np. native TV size filter).
    if size_filter:
        params["search[filter_enum_size][0]"] = size_filter

    if query:
        params["q"] = query

    # Definitions validate these names against the selected OLX category.
    params.update(olx_filters or {})
        
    # Promien szukania
    if mode == "lodz_alerts" and radius_km:
        params["search[dist]"] = radius_km
        
    # Strona
    if page > 1:
        params["page"] = page
        
    # Zlozenie calosci
    query_string = urllib.parse.urlencode(params)
    
    if query_string:
        return f"{url}?{query_string}"
    return url
