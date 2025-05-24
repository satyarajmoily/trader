# 🤖 Autonomous Agent System for Self-Improving Bitcoin Predictor

> **Proof-of-Concept**: Can an AI agent improve its own Bitcoin prediction code through automated analysis and GitHub PRs?

## 🎯 Overview

This project demonstrates **autonomous AI self-improvement** using Bitcoin price prediction as a concrete, measurable domain. The agent:

- Makes Bitcoin price movement predictions using simple logic
- Evaluates predictions against real market data  
- Updates its prediction logic when wrong using LLM
- Raises Pull Requests with improved code
- Loops this cycle to demonstrate continuous self-improvement

## 🔄 How It Works

### The Self-Improvement Loop

1. **Prediction Phase**: Agent makes Bitcoin price prediction (up/down) using keyword analysis
2. **Evaluation Phase** (24h later): Compares prediction vs actual Bitcoin price 
3. **Improvement Phase** (on failure): LLM analyzes failure and generates improved code
4. **Integration Phase** (manual): Human reviews and merges PR with improvements

## 🛠️ Technology Stack

- **Python 3.9+** - Core language
- **LangChain** - Agent orchestration and LLM interactions
- **OpenAI GPT-4** - Code improvement generation
- **CoinGecko API** - Bitcoin price data (free tier)
- **GitHub API** - Automated PR creation
- **JSON files** - Simple data persistence (MVP approach)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- GitHub account and repository
- OpenAI API key
- Basic command line knowledge

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd bitcoin-predictor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Test the predictor**
   ```bash
   python predictor.py
   ```

### Required Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-api-key-here
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_REPO_OWNER=your-username
GITHUB_REPO_NAME=bitcoin-predictor
```

## 📁 Project Structure

```
bitcoin-predictor/
├── agent_main.py              # Main orchestrator (coming in Phase 2)
├── predictor.py              # Core prediction logic ✅
├── predictions_log.json     # Simple JSON persistence ✅
├── config.py                # Configuration management ✅
├── requirements.txt          # Dependencies ✅
├── env.example              # Environment template ✅
├── README.md                # This file ✅
├── tools/                   # External API integrations
│   ├── bitcoin_price.py     # CoinGecko integration (Phase 2)
│   └── github_pr.py         # GitHub integration (Phase 4)
├── chains/                  # LangChain components
│   ├── evaluator.py         # Evaluation logic (Phase 2)
│   └── improver.py          # Code improvement (Phase 3)
└── tests/                   # Test suite
    └── test_predictor.py    # Unit tests
```

## 🗓️ Development Phases

### Phase 1: Core Prediction Logic ✅ (Week 1)
- [x] Basic project structure
- [x] Simple keyword-based prediction logic
- [x] JSON logging for predictions
- [ ] Local testing and validation

### Phase 2: LangChain Agent Setup (Week 2)
- [ ] CoinGecko price fetching tool
- [ ] LangChain Evaluator chain
- [ ] APScheduler for 24h evaluation cycles
- [ ] Evaluation logic testing

### Phase 3: Code Improvement Agent (Week 3)
- [ ] LangChain Improver chain
- [ ] Bitcoin-specific improvement prompts
- [ ] Code generation and validation
- [ ] Safety testing

### Phase 4: GitHub Automation (Week 4)
- [ ] PyGithub PR creation
- [ ] PR templates with analysis
- [ ] End-to-end testing
- [ ] Manual review workflow

### Phase 5: Integration & Polish (Week 5)
- [ ] Main agent loop integration
- [ ] Error handling and logging
- [ ] Continuous operation testing
- [ ] Documentation completion

## 🎯 Success Criteria

- [ ] System runs autonomously for 1+ week
- [ ] Creates meaningful GitHub PRs after failed predictions
- [ ] Generated code improvements compile and run
- [ ] Demonstrates measurable prediction logic evolution

## 🔒 Safety Features

- **Human PR Review**: All code changes require manual approval
- **Code Validation**: Generated code is syntax-checked before PR creation
- **Sandboxed Testing**: New code tested safely before deployment
- **Error Handling**: Graceful failure recovery without system crashes

## 📊 Current Status

**Phase**: 1 - Foundation Complete ✅  
**Progress**: Basic prediction logic working  
**Next**: LangChain agent setup  

## 🤝 Contributing

This is a proof-of-concept project focused on demonstrating autonomous AI self-improvement. The agent will be making its own contributions through automated PRs!

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Related Resources

- [LangChain Documentation](https://docs.langchain.com/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api)
- [GitHub API Reference](https://docs.github.com/en/rest)

---

**🤖 Autonomous Agent Status**: Foundation complete, ready for Phase 2 implementation! 