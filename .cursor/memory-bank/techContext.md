# Tech Context: Technology Stack & Implementation

## 🛠️ Technology Stack

### Core Framework
- **Python 3.9+** - Main programming language
- **LangChain** - Agent orchestration and LLM interactions
- **APScheduler** - Simple task scheduling for evaluation cycles

### LLM Integration
- **OpenAI GPT-4** - Primary choice for code improvement
- **Anthropic Claude** - Alternative/backup LLM option
- **LangChain LLM abstractions** - Provider-agnostic implementation

### External APIs
- **CoinGecko API** (Free tier)
  - Bitcoin price data
  - Historical price information
  - No authentication required for basic usage
- **GitHub API** via **PyGithub**
  - Automated PR creation
  - Repository file management
  - Requires GitHub token
- **NewsAPI** - Deferred for MVP, future feature

### Data Storage (MVP)
- **JSON files** - Simple persistence for predictions
- **File system** - No database complexity for MVP
- **Future**: SQLite for post-MVP if needed

## 📦 Dependencies

### Core Requirements
```
python>=3.9
langchain>=0.1.0
openai>=1.0.0
anthropic>=0.15.0
requests>=2.31.0
PyGithub>=1.59.0
APScheduler>=3.10.0
python-dotenv>=1.0.0
```

### Development Dependencies
```
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
```

## 🏗️ Development Environment Setup

### Local Development
```bash
# 1. Clone repository
git clone <repo-url>
cd bitcoin-predictor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with API keys

# 5. Run initial tests
python -m pytest tests/

# 6. Start agent
python agent_main.py
```

### Required API Keys
```bash
# .env file structure
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=ant-...
GITHUB_TOKEN=ghp_...
GITHUB_REPO_OWNER=username
GITHUB_REPO_NAME=bitcoin-predictor
```

## 🔧 Technical Constraints

### MVP Limitations
- **No database** - JSON file persistence only
- **No web interface** - Command line operation
- **Manual PR merging** - No automated code deployment
- **24-hour cycles** - Fixed evaluation timing
- **Single threaded** - No concurrent processing

### API Rate Limits
- **CoinGecko Free**: 30 calls/minute
- **GitHub API**: 5000 requests/hour (authenticated)
- **OpenAI**: Depends on plan, typically sufficient for MVP
- **Claude**: 200k tokens/minute (Claude 3.5 Sonnet)

### Error Handling Requirements
- **Graceful degradation** on API failures
- **Retry logic** with exponential backoff
- **Logging** for debugging and monitoring
- **Safe code execution** for generated code

## 📁 Project Structure

### Directory Layout
```
bitcoin-predictor/
├── agent_main.py              # Main entry point
├── predictor.py              # Core prediction logic
├── predictions_log.json     # Data persistence
├── config.py                # Configuration management
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── README.md                # Documentation
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_predictor.py
│   ├── test_evaluator.py
│   └── test_improver.py
├── tools/                   # External integrations
│   ├── __init__.py
│   ├── bitcoin_price.py     # CoinGecko integration
│   └── github_pr.py         # GitHub integration
├── chains/                  # LangChain components
│   ├── __init__.py
│   ├── evaluator.py         # Evaluation chain
│   └── improver.py          # Improvement chain
└── logs/                    # Application logs
    └── agent.log
```

## 🔒 Security Considerations

### API Key Management
- **Environment variables** only, never hardcoded
- **gitignore** for .env files
- **Minimal permissions** for GitHub token
- **Local storage** of sensitive data

### Code Safety
- **Syntax validation** before executing generated code
- **Sandboxed execution** for code testing
- **Function signature validation** for predictor updates
- **Human review** required for all PRs

### Data Privacy
- **No sensitive data** in prediction logs
- **Local JSON storage** only
- **No external data transmission** except APIs
- **Minimal data retention** for MVP

## 🚀 Deployment Strategy (MVP)

### Local Development Only
- **No cloud deployment** for MVP
- **Manual startup** and monitoring
- **Local file system** for all data
- **Terminal-based** operation

### Future Deployment Considerations
- **Docker containerization** for portability
- **Cloud hosting** for 24/7 operation
- **Database migration** from JSON files
- **Monitoring and alerting** systems

## 🧪 Testing Strategy

### Unit Testing
- **pytest** framework
- **Mock external APIs** for testing
- **Test all components** in isolation
- **Code coverage** tracking

### Integration Testing
- **End-to-end flow** testing
- **API integration** validation
- **Error handling** scenarios
- **Performance** benchmarks

### Safety Testing
- **Generated code** validation
- **API failure** simulation
- **Data corruption** recovery
- **GitHub PR** creation testing

## 📊 Monitoring & Logging

### Application Logging
```python
import logging

# Log configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)
```

### Key Metrics to Track
- **Prediction accuracy** over time
- **API call success** rates
- **Code generation** success/failure
- **PR creation** statistics
- **System uptime** and errors

### Performance Considerations
- **Memory usage** for long-running operation
- **JSON file size** growth over time
- **API response times** monitoring
- **Error recovery** time tracking 