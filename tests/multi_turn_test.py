# multi_turn_test.py
import requests
import json

BASE = "http://localhost:8000"

# Turn 1
print("Turn 1:")
response1 = requests.post(f"{BASE}/api/chat", json={
    "messages": [{"role": "user", "content": "I need to hire someone"}]
})
data1 = response1.json()
print(f"Reply: {data1['reply'][:100]}...")

# Turn 2
print("\nTurn 2:")
response2 = requests.post(f"{BASE}/api/chat", json={
    "messages": [
        {"role": "user", "content": "I need to hire someone"},
        {"role": "assistant", "content": data1['reply']},
        {"role": "user", "content": "Java developer, mid-level"}
    ]
})
data2 = response2.json()
print(f"Reply: {data2['reply'][:100]}...")
print(f"Recommendations: {len(data2['recommendations'])}")