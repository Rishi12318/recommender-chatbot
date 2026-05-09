# SHL Assessment Recommender - Approach Document

## Overview
This document outlines the approach for building a conversational AI system that recommends SHL assessments based on user needs.

## Architecture

### Components
1. **FastAPI Backend**: REST API for chat and recommendations
2. **LLM Integration**: Groq/Gemini for conversational AI
3. **Vector Search**: Semantic search over assessment catalog
4. **Conversation Manager**: Session management and context tracking

### Data Pipeline
- **Scraper**: Collect SHL assessment data
- **Preprocessor**: Clean and structure catalog
- **Embeddings**: Generate vector representations
- **Retrieval**: Search relevant assessments

## Evaluation Metrics
- **Recall@10**: Measure recommendation accuracy
- **Coverage**: Assess breadth of recommendations
- **Behavior Probes**: Test conversational quality

## Implementation Plan
1. Set up FastAPI application structure
2. Implement LLM client integration
3. Build vector search retrieval
4. Create conversation management
5. Evaluate against test traces
6. Deploy to production
