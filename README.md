# 🧠 Autonomous Agent System for Self-Improving Bitcoin Predictor

## 🎯 MVP Objective

**Core Hypothesis to Prove**: Can an AI agent improve its own Bitcoin prediction code through automated analysis and GitHub PRs?

Build a minimal autonomous system where an AI agent:
- Makes Bitcoin price movement predictions using **historical OHLCV data analysis**
- Evaluates predictions against real Bitcoin market data  
- Updates its prediction logic when wrong using LLM
- Raises Pull Requests with improved code
- Loops this cycle to demonstrate self-improvement

## 🔁 System Overview

### Core Prediction Process
```
Historical Bitcoin Data → Price Trend Analysis → UP/DOWN Prediction → 
Wait 24h → Compare vs Reality → Improve Code (if wrong) → GitHub PR
```

**Input**: Bitcoin OHLCV data (Open, High, Low, Close, Volume)
**Analysis**: Simple moving averages, momentum, and volume trends
**Output**: "UP" or "DOWN" prediction for next 24 hours
**Validation**: Compare against actual Bitcoin price movement

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Git repository for automated PRs

### Installation
```bash
git clone <repo-url>
cd bitcoin-predictor
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Make a Prediction
```bash
python predictor.py
```

**Sample Output**:
```
Bitcoin Price Prediction System
========================================
Latest Bitcoin Price: $45,800.00
Data Period: 2024-01-01 to 2024-01-30
Data Points: 30
Prediction: UP
Timestamp: 2024-01-30T15:30:45
========================================
Price-based prediction system ready!
```

## 📊 Prediction Logic (Current Implementation)

The system analyzes Bitcoin price trends using:

### Technical Indicators
- **Short MA (3-day)** vs **Long MA (5-day)**: Trend direction
- **Price Momentum**: 5-day price change percentage  
- **Volume Trend**: Recent volume increase/decrease

### Bullish Signals
- Short MA > Long MA (trend reversal)
- Positive momentum > 2% (strong momentum)
- Increasing volume trend (confirmation)

### Prediction Logic
```python
def predict(price_data: List[Dict]) -> Literal["up", "down"]:
    # Calculate moving averages and momentum
    # Count bullish signals
    # Return "up" if >= 1.5 signals, "down" otherwise
```

## 🛠️ Technical Architecture

### Current Tech Stack (MVP)
- **Python 3.9+** - Main language
- **CSV Data** - Mock Bitcoin OHLCV data (Phase 1)
- **CoinGecko API** - Real Bitcoin data (Phase 2+)
- **LangChain** - Agent orchestration (Phase 2+)
- **OpenAI/Claude** - Code improvement (Phase 3+)
- **PyGithub** - Automated PRs (Phase 4+)

### Project Structure
```
bitcoin-predictor/
├── predictor.py              # Core price-based prediction logic
├── mock_bitcoin_data.csv     # 30 days of Bitcoin OHLCV data
├── predictions_log.json     # Prediction history
├── requirements.txt
├── .env.example
├── tools/                   # API integrations (Phase 2+)
├── chains/                  # LangChain agents (Phase 2+)
└── .cursor/memory-bank/     # Project documentation
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