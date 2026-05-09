# SHL Assessment Recommender

An intelligent conversational system that recommends SHL assessments based on user needs using AI and vector search.

## Features
- Conversational chat interface
- AI-powered assessment recommendations
- Vector semantic search over catalog
- Session management
- REST API

## Project Structure
```
shl-assessment-recommender/
├── app/                    # Main application
│   ├── api/               # API routes and schemas
│   ├── core/              # Configuration and prompts
│   ├── services/          # Business logic
│   ├── data/              # Data processing
│   └── utils/             # Helper functions
├── data/                  # Data storage
├── tests/                 # Test suite
├── evaluation/            # Evaluation metrics
├── deployment/            # Docker and deployment
└── docs/                  # Documentation
```

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application
```bash
uvicorn app.main:app --reload
```

### Running Tests
```bash
pytest
```

## API Endpoints
- `GET /health` - Health check
- `POST /chat` - Chat with the recommender

## Documentation
See [docs/approach.md](docs/approach.md) for detailed approach and architecture.
