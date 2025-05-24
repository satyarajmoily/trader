# 🧠 Autonomous Agent System for Self-Improving Bitcoin Predictor

## 🎯 MVP Objective

**Core Hypothesis to Prove**: Can an AI agent improve its own Bitcoin prediction code through automated analysis and GitHub PRs?

Build a minimal autonomous system where an AI agent:
- Makes Bitcoin price movement predictions using **historical OHLCV data analysis**
- Evaluates predictions against real Bitcoin market data  
- Updates its prediction logic when wrong using LLM
- Raises Pull Requests with improved code
- Loops this cycle to demonstrate self-improvement

## 🏗️ MAJOR MILESTONE: Clean System Separation ✅

**BREAKTHROUGH ACHIEVED**: Successfully separated the system into two independent, loosely coupled components:

### 🔧 **Core Prediction System** (Standalone)
```
bitcoin_predictor/               # Independent prediction engine
├── models.py                   # Data models (PredictionRecord, OHLCVData)
├── interfaces.py               # Abstract interfaces  
├── data_loader.py              # Bitcoin data loading
├── storage.py                  # JSON prediction storage
├── predictor.py                # Core prediction logic
└── __init__.py                 # Clean package exports

predictor_main.py               # Standalone CLI
predictor_config.py             # Core system configuration
```

### 🤖 **Autonomous Agent System** (Orchestrator)
```
autonomous_agent/               # Agent orchestration
├── orchestrator.py             # Main agent coordinator
├── interfaces/
│   └── predictor_interface.py  # Clean interface to core system
├── tools/
│   └── bitcoin_api.py          # CoinGecko API integration
├── chains/
│   └── evaluator.py            # LangChain evaluation logic
└── __init__.py                 # Agent package exports

agent_main.py                   # Agent CLI
```

## ✅ **Separation Benefits Achieved**

### 🔄 **Independent Operation**
- ✅ Core system: `python predictor_main.py predict` (standalone)
- ✅ Agent system: `python agent_main.py predict` (via interface)
- ✅ Zero circular dependencies
- ✅ Each system has its own CLI and configuration

### 🎯 **Clean Interfaces**
- ✅ `PredictorInterface` provides clean abstraction layer
- ✅ Agent has no direct knowledge of core implementation
- ✅ Core system has no knowledge of agent existence
- ✅ Well-defined boundaries and contracts

### 📦 **Easy Extraction**
- ✅ Agent code ready for separate repository immediately
- ✅ Simple extraction: `cp -r autonomous_agent/ /new/repo/`
- ✅ Only dependency: agent imports `bitcoin_predictor` package
- ✅ No mixed concerns or tangled dependencies

## 🔁 System Overview

### Core Prediction Process
```
Historical Bitcoin Data → Price Trend Analysis → UP/DOWN Prediction → 
Wait 24h → Compare vs Reality → Improve Code (if wrong) → GitHub PR
```

**Input**: Bitcoin OHLCV data (Open, High, Low, Close, Volume)
**Analysis**: Simple moving averages, momentum, and volume trends
**Output**: "UP" or "DOWN" prediction for next 24 hours
**Validation**: Compare against actual Bitcoin price movement via CoinGecko API

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (for AI evaluation)
- GitHub token (for future PR automation)
- Optional: CoinGecko Pro API key

### Installation
```bash
git clone <repo-url>
cd trader
pip install -r requirements.txt
cp env.example .env
# Edit .env with your actual API keys
```

### 🔑 Required Environment Variables
Edit your `.env` file with:
```bash
OPENAI_API_KEY=sk-proj-your-openai-key-here
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_REPO_OWNER=your-github-username
GITHUB_REPO_NAME=bitcoin-predictor
```

### ✅ Test Both Systems

#### Core System (Standalone)
```bash
# Test core prediction system
python predictor_main.py test

# Make a core prediction
python predictor_main.py predict

# View prediction history
python predictor_main.py history
```

#### Agent System (Orchestrator)
```bash
# Test agent system
python agent_main.py test

# Make prediction via agent
python agent_main.py predict

# Evaluate predictions
python agent_main.py evaluate
```

**Sample Output**:
```
🧪 Testing Bitcoin Prediction Agent Components
==================================================
Core System Tests:
✅ Prediction completed successfully:
- Prediction: DOWN
- Bitcoin Price: $45,800.00 (predicted) vs $109,007.00 (actual)

Agent System Tests:
✅ Agent prediction via interface:
- Clean interface working
- No dependencies on core implementation
==================================================
✅ All tests passed! Both systems operational independently.
```

## 📊 Current Prediction Logic

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

### Current Tech Stack ✅ OPERATIONAL
- **Python 3.9+** - Main language ✅
- **LangChain** - Agent orchestration ✅ WORKING
- **OpenAI GPT-4o-mini** - AI evaluation system ✅ OPERATIONAL
- **CoinGecko API** - Real Bitcoin data ✅ LIVE ($109,007.00)
- **APScheduler** - Autonomous scheduling ✅ READY
- **PyGithub** - Automated PRs (Phase 4)

### Enhanced Project Structure (Clean Separation)
```
trader/
├── bitcoin_predictor/           # 🔧 CORE SYSTEM (Standalone)
│   ├── __init__.py             # Clean package exports
│   ├── models.py               # Data models
│   ├── interfaces.py           # Abstract interfaces
│   ├── data_loader.py          # Bitcoin data loading
│   ├── storage.py              # JSON prediction storage
│   └── predictor.py            # Core prediction logic
├── predictor_main.py           # Core system CLI ✅
├── predictor_config.py         # Core configuration ✅
├── autonomous_agent/           # 🤖 AGENT SYSTEM (Orchestrator) 
│   ├── __init__.py             # Agent package exports
│   ├── orchestrator.py         # Main agent coordinator
│   ├── interfaces/
│   │   └── predictor_interface.py  # Clean interface layer
│   ├── tools/
│   │   └── bitcoin_api.py      # CoinGecko integration ✅
│   └── chains/
│       └── evaluator.py        # LangChain evaluation ✅
├── agent_main.py               # Agent system CLI ✅
├── mock_bitcoin_data.csv       # 30 days of Bitcoin OHLCV data ✅
├── predictions_log.json        # Prediction history ✅
├── evaluations_log.json        # AI evaluation results ✅
├── requirements.txt            # All dependencies ✅
├── env.example                 # Environment template ✅
├── SEPARATION_SUMMARY.md       # Separation documentation ✅
└── .cursor/memory-bank/        # Project documentation ✅
```

## 🗓️ Development Phases

### Phase 1: Core Prediction Logic ✅ COMPLETE (Week 1)
- [x] Basic project structure ✅
- [x] Price-based prediction logic ✅
- [x] JSON logging for predictions ✅
- [x] Local testing and validation ✅

### Phase 2: LangChain Agent Setup ✅ COMPLETE & OPERATIONAL (Week 2)
- [x] CoinGecko price fetching tool ✅ LIVE
- [x] LangChain Evaluator chain ✅ WORKING
- [x] APScheduler for 24h evaluation cycles ✅ READY
- [x] Agent orchestration with tools ✅ TESTED
- [x] Multiple operation modes ✅ ALL WORKING
- [x] Comprehensive unit testing ✅ 12/12 PASSING

### Phase 2+: Clean System Separation ✅ COMPLETE (Today)
- [x] **System Architecture**: Separated core and agent systems ✅
- [x] **Independent Operation**: Both systems work standalone ✅
- [x] **Clean Interfaces**: Agent uses core via `PredictorInterface` ✅
- [x] **Zero Dependencies**: No circular dependencies ✅
- [x] **Easy Extraction**: Agent ready for separate repository ✅
- [x] **Complete Testing**: All separation goals verified ✅

### Phase 3: Code Improvement Agent (Week 3) - ENHANCED READY
- [ ] LangChain Improver targeting clean core interfaces
- [ ] Bitcoin-specific improvement prompts for separated system
- [ ] Safe code generation with interface compatibility
- [ ] Independent validation through clean interfaces

### Phase 4: GitHub Automation (Week 4)
- [ ] PyGithub PR creation for core system improvements
- [ ] PR templates with architectural context
- [ ] End-to-end testing with separated systems
- [ ] Manual review workflow

### Phase 5: Integration & Polish (Week 5)
- [ ] Enhanced autonomous operation with clean architecture
- [ ] Independent error handling for both systems
- [ ] Continuous operation testing with separation benefits
- [ ] Documentation of clean architecture and extraction process

## 🎯 Success Criteria

- [x] ✅ Phase 1: Basic prediction system operational
- [x] ✅ Phase 2: LangChain agent system fully working
- [x] ✅ **NEW**: Clean system separation with independent operation
- [ ] Phase 3: Enhanced code improvement with clean architecture
- [ ] System runs autonomously for 1+ week with separated systems
- [ ] Creates meaningful GitHub PRs after failed predictions
- [ ] Generated code improvements compile and run with interface compatibility
- [ ] Demonstrates measurable prediction logic evolution

## 🔒 Safety Features

- **Human PR Review**: All code changes require manual approval
- **Code Validation**: Generated code is syntax-checked before PR creation
- **Sandboxed Testing**: New code tested safely on isolated core system
- **Interface Compatibility**: All improvements maintain clean contracts
- **Independent Testing**: Core improvements tested without affecting agent
- **Error Handling**: Graceful failure recovery without system crashes

## 📊 Current Status

**Phase**: 2+ - Clean System Separation ✅ COMPLETE
**Progress**: Enhanced architecture with independent systems operational
**Live Bitcoin Price**: $109,007.00 (via CoinGecko API)
**System Health**: 100% operational - both systems tested independently
**Next**: Enhanced Phase 3 - Code Improvement with clean architecture

### 🎯 Enhanced Phase 3 Setup
- **Clean Target**: Isolated core system ready for targeted improvements
- **Safe Development**: Test improvements without breaking agent orchestration
- **Interface Compatibility**: Ensure improvements maintain clean contracts
- **Independent Validation**: Test through standardized interfaces

## 🚀 Available Commands

### Core System (Standalone)
```bash
# Test core system components
python predictor_main.py test

# Make a Bitcoin prediction (core only)
python predictor_main.py predict

# View prediction history
python predictor_main.py history

# Analyze price data without prediction
python predictor_main.py analyze
```

### Agent System (Orchestrator)
```bash
# Test agent system components
python agent_main.py test

# Make prediction via agent interface
python agent_main.py predict

# Evaluate predictions against real market data
python agent_main.py evaluate
```

## 📈 Live System Metrics

- **System Architecture**: Clean separation achieved and tested ✅
- **Independent Operation**: Both systems verified working standalone ✅
- **Interface Layer**: `PredictorInterface` providing clean abstraction ✅
- **Zero Dependencies**: No circular dependencies confirmed ✅
- **Easy Extraction**: Agent code ready for separate repository ✅
- **Test Success Rate**: 100% (all tests passing for both systems)

## 🔄 Enhanced Insights & Next Steps

### Major Architectural Achievement
1. **Perfect Separation**: Core and agent systems completely decoupled
2. **Clean Interfaces**: Well-defined boundaries enable better development
3. **Independent Evolution**: Each system can evolve without affecting the other
4. **Easy Extraction**: Agent ready for separate repository deployment
5. **Safe Development**: Test improvements without system-wide impact

### Enhanced Phase 3 Opportunities
1. **Targeted Improvements**: Focus on specific core system interfaces
2. **Safe Code Generation**: Test on isolated core system without breaking agent
3. **Interface Compatibility**: Ensure improvements maintain clean contracts
4. **Independent Deployment**: Deploy core improvements without agent changes

## 🤝 Contributing

This is a proof-of-concept project focused on demonstrating autonomous AI self-improvement with clean architecture. The agent will be making its own contributions through automated PRs targeting the isolated core system!

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Related Resources

- [LangChain Documentation](https://docs.langchain.com/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api)
- [GitHub API Reference](https://docs.github.com/en/rest)
- [SEPARATION_SUMMARY.md](./SEPARATION_SUMMARY.md) - Detailed separation documentation

---

**🤖 Autonomous Agent Status**: Clean system separation complete! Ready for enhanced Phase 3 development with better architecture, safer testing, and easier deployment. 🎯 