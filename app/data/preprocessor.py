# app/data/preprocessor.py

import json
import re
from pathlib import Path
from app.core.config import settings

def process_catalog():
    """Process raw catalog into clean format"""
    
    raw_path = settings.RAW_CATALOG_PATH
    processed_path = settings.PROCESSED_CATALOG_PATH
    
    if not raw_path.exists():
        print(f"❌ Raw catalog not found at {raw_path}")
        print("Please add your raw_catalog.json file to app/data/")
        return None
    
    # Load raw catalog with error handling
    with open(raw_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Remove control characters
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        raw_data = json.loads(content)
    
    processed_data = []
    
    # Handle different possible structures
    if isinstance(raw_data, dict):
        if 'assessments' in raw_data:
            raw_data = raw_data['assessments']
        elif 'data' in raw_data:
            raw_data = raw_data['data']
        elif 'items' in raw_data:
            raw_data = raw_data['items']
        else:
            raw_data = [raw_data]
    
    for item in raw_data:
        processed_item = {
            "entity_id": item.get("entity_id", ""),
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "url": item.get("link", item.get("url", "")),
            "duration": item.get("duration", ""),
            "job_levels": item.get("job_levels", []),
            "languages": item.get("languages", []),
            "test_types": item.get("keys", item.get("test_type", [])),
            "remote_support": item.get("remote", "unknown"),
            "adaptive": item.get("adaptive", "unknown")
        }
        
        if isinstance(processed_item["test_types"], str):
            processed_item["test_types"] = [processed_item["test_types"]]
        
        processed_data.append(processed_item)
    
    # Save processed catalog
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Processed {len(processed_data)} items successfully!")
    print(f"📁 Saved to: {processed_path}")
    
    return processed_data

if __name__ == "__main__":
    process_catalog()