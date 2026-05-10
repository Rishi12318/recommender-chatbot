# evaluation/ground_truth.py
"""
Ground truth data for SHL assessment evaluation
"""

# Java assessments from your catalog
JAVA_ASSESSMENTS = [
    "Core Java (Advanced Level) (New)",
    "Core Java (Entry Level) (New)",
    "Java 8 (New)",
    "Java Design Patterns (New)",
    "Java Frameworks (New)",
    "Java Web Services (New)"
]

# Personality assessments
PERSONALITY_ASSESSMENTS = [
    "Occupational Personality Questionnaire OPQ32r",
    "OPQ Leadership Report",
    "Managerial Scenarios Profile Report"
]

# Cognitive ability assessments
COGNITIVE_ASSESSMENTS = [
    "Verify - General Ability Screen",
    "Verify - Numerical Ability",
    "Verify - Verbal Ability - Next Generation"
]

# Main test queries
TEST_QUERIES = [
    {
        "query": "Java developer with 3 years experience",
        "expected_behavior": "recommend",
        "relevant_assessments": JAVA_ASSESSMENTS
    },
    {
        "query": "Need personality assessment for managers",
        "expected_behavior": "recommend",
        "relevant_assessments": PERSONALITY_ASSESSMENTS
    },
    {
        "query": "I need an assessment",
        "expected_behavior": "ask",
        "relevant_assessments": []
    },
    {
        "query": "What is the weather today?",
        "expected_behavior": "refuse",
        "relevant_assessments": []
    },
    {
        "query": "Cognitive ability test",
        "expected_behavior": "recommend",
        "relevant_assessments": COGNITIVE_ASSESSMENTS
    }
]
