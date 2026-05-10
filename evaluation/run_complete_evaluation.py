# evaluation/run_complete_evaluation.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from single source of truth
from evaluation.ground_truth_corrected import TEST_QUERIES
from app.services.agent import get_agent

print("=" * 70)
print("SHL ASSESSMENT RECOMMENDER - COMPLETE EVALUATION")
print("=" * 70)
print(f"Loaded {len(TEST_QUERIES)} test queries from ground_truth_corrected")
print("=" * 70)

agent = get_agent()
total_recall = 0
recall_count = 0
tests_passed = 0

for i, test in enumerate(TEST_QUERIES, 1):
    print(f"\n[TEST {i}] Query: {test['query']}")
    print(f"   Expected: {test['expected_behavior']}")
    print(f"   Ground truth: {test.get('relevant_assessments', [])[:3]}...")
    
    response = agent.process_message(test['query'], [])
    recommendations = response.get('recommendations', [])
    rec_names = [r.get('name', '') for r in recommendations]
    
    print(f"   Recommendations returned: {len(recommendations)}")
    
    relevant = test.get('relevant_assessments', [])
    if relevant:
        matches = set(rec_names[:10]) & set(relevant)
        recall = len(matches) / len(relevant)
        total_recall += recall
        recall_count += 1
        print(f"   Recall@10: {recall:.3f}")
        print(f"   Matches: {list(matches) if matches else 'None'}")
        if recall > 0:
            tests_passed += 1
            print(f"   [PASS]")
        else:
            print(f"   [FAIL]")
    else:
        reply = response.get('reply', '')
        if test['expected_behavior'] == 'ask':
            if '?' in reply or 'role' in reply.lower():
                print(f"   [PASS] - Asked clarifying question")
                tests_passed += 1
            else:
                print(f"   [!] Reply: {reply[:100]}...")
        elif test['expected_behavior'] == 'refuse':
            if 'SHL' in reply or 'assessment' in reply.lower():
                print(f"   [PASS] - Properly refused")
                tests_passed += 1
            else:
                print(f"   [!] Reply: {reply[:100]}...")
        else:
            print(f"   Reply: {reply[:100]}...")

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)

avg_recall = total_recall / recall_count if recall_count > 0 else 0
print(f"\nMean Recall@10: {avg_recall:.3f}")
print(f"Tests Passed: {tests_passed}/{len(TEST_QUERIES)}")

if avg_recall >= 0.5:
    print("EXCELLENT: Recall score meets target!")
elif avg_recall >= 0.3:
    print("GOOD: Recall score acceptable")
else:
    print("[!] NEEDS IMPROVEMENT: Review retrieval strategy")

print("\n" + "=" * 70)
