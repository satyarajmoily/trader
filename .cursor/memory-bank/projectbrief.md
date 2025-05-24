# Project Brief: Autonomous Agent System for Self-Improving Bitcoin Predictor

## 🎯 Core Hypothesis

**Primary Objective**: Prove that an AI agent can improve its own Bitcoin prediction code through automated analysis and GitHub PRs.

## 📋 Project Definition

### What We're Building
A minimal autonomous system where an AI agent:
- Makes Bitcoin price movement predictions using simple logic
- Evaluates predictions against real Bitcoin market data  
- Updates its prediction logic when wrong using LLM
- Raises Pull Requests with improved code
- Loops this cycle to demonstrate self-improvement

### Success Criteria
- [ ] System runs locally for 1+ week without crashing
- [ ] Creates at least 1 meaningful GitHub PR after a failed prediction  
- [ ] Generated code improvement actually compiles and runs
- [ ] Shows measurable change in prediction logic over time

## 🔍 Scope Definition

### MVP Components (Must-Have Only)
- **Single Python Repo** (bitcoin-predictor)
- **CoinGecko API** - Bitcoin price data
- **GitHub API** - Automated PR creation
- **LangChain** - Agent orchestration
- **OpenAI/Claude API** - Code improvement

### Explicitly DEFERRED (Post-MVP)
- FastAPI endpoints and web interface
- SQLite database and complex data models  
- Docker deployment and CI/CD pipelines
- News API integration and sentiment analysis
- Machine learning prediction models
- Real-time streaming data
- Automated trading integration

## 📈 Key Metrics

### Basic Tracking
- **Prediction Count**: Total predictions made
- **Failure Rate**: % of wrong predictions  
- **PR Creation**: Number of improvement PRs generated
- **Uptime**: System runs continuously without manual intervention

## 🗓️ Timeline

**5-Week Implementation Phases**:
- **Week 1**: Basic prediction + JSON logging
- **Week 2**: LangChain evaluation agent  
- **Week 3**: Code improvement with LLM
- **Week 4**: GitHub PR automation
- **Week 5**: End-to-end testing

**Success Milestone**: Agent creates its first self-improvement PR after a failed Bitcoin prediction.

## 🔑 Strategic Decisions

1. **MVP-First Approach**: Focus on core functionality only
2. **Simple Storage**: JSON files instead of databases
3. **Manual PR Review**: No automated merging for safety
4. **24-Hour Evaluation Cycles**: Simple timing for MVP
5. **Single Asset Focus**: Bitcoin only, no multi-asset complexity 