# test_agent_fix.py
import sys
sys.path.insert(0, '.')

from app.services.agent import get_agent

agent = get_agent()

# Test 1: Normal query
response = agent.process_message("I need a Java developer", [])
print(f"Reply: {response.get('reply', 'N/A')[:100]}...")
print(f"Recommendations: {len(response.get('recommendations', []))}")
print(f"End of conversation: {response.get('end_of_conversation', False)}")
print(f"Has 'reply'? {'reply' in response}")
print(f"Has 'recommendations'? {'recommendations' in response}")
print(f"Has 'end_of_conversation'? {'end_of_conversation' in response}")