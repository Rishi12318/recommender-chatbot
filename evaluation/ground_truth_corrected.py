# evaluation/ground_truth_corrected.py - UPDATED with actual catalog names
import json
from pathlib import Path

def load_catalog():
    # Fix path to be relative to the project root
    root_dir = Path(__file__).parent.parent
    catalog_path = root_dir / 'app' / 'data' / 'processed_catalog.json'
    if catalog_path.exists():
        with open(catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_java_assessments():
    catalog = load_catalog()
    return [a['name'] for a in catalog if 'java' in a.get('name', '').lower()][:5]

def get_personality_assessments():
    catalog = load_catalog()
    return [a['name'] for a in catalog if any(k in a.get('name', '').lower() 
            for k in ['personality', 'leadership', 'opq'])]

def get_cognitive_assessments():
    catalog = load_catalog()
    return [a['name'] for a in catalog if any(k in a.get('name', '').lower() 
            for k in ['verify', 'cognitive', 'ability'])]

def get_python_assessments():
    catalog = load_catalog()
    return [a['name'] for a in catalog if 'python' in a.get('name', '').lower()]

TEST_QUERIES = [
    {
        "query": "Java developer with 3 years experience",
        "expected_behavior": "recommend",
        "relevant_assessments": get_java_assessments()
    },
    {
        "query": "I need an assessment",
        "expected_behavior": "ask",
        "relevant_assessments": []
    },
    {
        "query": "What's the weather today?",
        "expected_behavior": "refuse",
        "relevant_assessments": []
    },
    {
        "query": "Need personality assessment for managers",
        "expected_behavior": "recommend",
        "relevant_assessments": get_personality_assessments()[:5]
    },
    {
        "query": "Python programming test",
        "expected_behavior": "recommend",
        "relevant_assessments": get_python_assessments()
    },
    {
        "query": "Cognitive ability test",
        "expected_behavior": "recommend",
        "relevant_assessments": get_cognitive_assessments()[:5]
    }
]

print(f"Loaded {len(TEST_QUERIES)} test queries")
print(f"Java: {len(get_java_assessments())} assessments")
print(f"Personality: {len(get_personality_assessments())}")
print(f"Cognitive: {len(get_cognitive_assessments())}")
print(f"Python: {len(get_python_assessments())}")
