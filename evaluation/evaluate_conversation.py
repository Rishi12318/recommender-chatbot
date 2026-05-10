# evaluation/evaluate_conversation.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.ground_truth_corrected import TEST_QUERIES
from app.services.agent import get_agent

print("=" * 70)
print("CONVERSATION QUALITY EVALUATION")
print("=" * 70)

agent = get_agent()
passed = 0

for test in TEST_QUERIES:
    query = test['query']
    expected = test['expected_behavior']
    
    response = agent.process_message(query, [])
    reply = response.get('reply', '')
    recommendations = response.get('recommendations', [])
    
    if expected == 'ask':
        if '?' in reply or 'role' in reply.lower():
            print(f"✅ '{query}' - Asked correctly")
            passed += 1
        else:
            print(f"⚠️ '{query}' - Should have asked")
    elif expected == 'refuse':
        if 'SHL' in reply or 'assessment' in reply.lower():
            print(f"✅ '{query}' - Refused correctly")
            passed += 1
        else:
            print(f"⚠️ '{query}' - Should have refused")
    elif expected == 'recommend':
        if len(recommendations) > 0:
            print(f"✅ '{query}' - Recommended {len(recommendations)} items")
            passed += 1
        else:
            print(f"⚠️ '{query}' - No recommendations")

print(f"\n📊 Conversation Quality: {passed}/{len([t for t in TEST_QUERIES if t['expected_behavior'] in ['ask','refuse','recommend']])}")
