import os
import pytest
import sqlite3
import yaml
from pathlib import Path
from scraper_ofert_tv.model_specs import import_model_specs, export_missing_specs
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.normalization import enrich_with_model_specs, normalize_offer_data
import tempfile

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    apply_migrations(Path(path))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    yield path, conn
    conn.close()
    os.remove(path)

def test_import_yaml(temp_db):
    db_path, conn = temp_db
    yaml_content = [
        {
            'brand': 'sony',
            'model': '46HX850',
            'screen_size_inches': 46,
            'technology': 'led',
            'resolution': 'full_hd',
            'spec_confidence': 0.9
        }
    ]
    fd, yaml_path = tempfile.mkstemp(suffix='.yaml')
    with open(fd, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f)
        
    import_model_specs(yaml_path, Path(db_path))
    
    c = conn.cursor()
    c.execute("SELECT * FROM model_specs")
    rows = c.fetchall()
    assert len(rows) == 1
    assert rows[0]['normalized_model'] == '46hx850'
    assert rows[0]['technology'] == 'led'
    
    # Test upsert not overwriting with empty
    yaml_content2 = [
        {
            'brand': 'sony',
            'model': '46HX850',
            # missing technology, size
        }
    ]
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content2, f)
        
    import_model_specs(yaml_path, Path(db_path))
    c.execute("SELECT * FROM model_specs")
    rows = c.fetchall()
    assert len(rows) == 1
    assert rows[0]['technology'] == 'led' # should not be overwritten
    assert rows[0]['screen_size_inches'] == 46
    
    os.remove(yaml_path)

def test_enrich_with_model_specs():
    normalized = {'brand': 'sony', 'model_name': '46HX850', 'technology': None}
    diagnostics = {}
    specs_cache = {
        ('sony', '46hx850'): {
            'technology': 'led',
            'screen_size_inches': 46,
            'spec_confidence': 0.9
        }
    }
    
    enrich_with_model_specs(normalized, diagnostics, specs_cache)
    
    assert normalized['technology'] == 'led'
    assert normalized['size_inches'] == 46
    assert diagnostics['model_specs_used'] is True
    assert 'technology' in diagnostics['model_specs_fields']
    assert diagnostics['model_specs_confidence'] == 0.9
