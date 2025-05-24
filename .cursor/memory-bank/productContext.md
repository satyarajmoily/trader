# Product Context: What We're Building & Why

## 🎯 Core Product Vision

**Primary Goal**: Prove that an AI agent can autonomously improve its own Bitcoin prediction code through self-analysis and automated GitHub PRs.

**The Innovation**: Not just another Bitcoin predictor, but a **self-improving AI system** that gets better over time by analyzing its own failures and generating improved prediction algorithms.

## 💡 The Problem We're Solving

### Real Problem
Current AI prediction systems are static - they don't learn from their mistakes or improve their own code. Even when they fail, humans must manually update the logic.

### Our Hypothesis  
An AI agent can autonomously:
- Analyze Bitcoin price trends using historical OHLCV data
- Detect when its predictions fail against real market movements
- Generate improved price analysis code using LLMs
- Deploy improvements via GitHub PRs
- Create a continuous self-improvement cycle

## 🎯 Product Core: The Self-Improvement Loop

```
Make Prediction → Wait 24h → Evaluate Against Reality → 
Improve Code (if wrong) → Create PR → Manual Review & Merge → Loop
```

### Prediction Method (Updated)
**Input**: Historical Bitcoin OHLCV data (Open, High, Low, Close, Volume)
**Analysis**: Simple price trend analysis (moving averages, momentum)
**Output**: "UP" or "DOWN" prediction for next 24 hours
**Validation**: Compare against actual Bitcoin price movement

### Self-Improvement Trigger
- **When**: ANY failed prediction (immediate trigger)
- **How**: LLM analyzes price patterns that led to failure
- **Output**: Improved prediction algorithm code
- **Deployment**: Automated GitHub PR creation

## 🚀 Why This Project Exists

### Core Problem Being Solved
Traditional AI systems require human intervention to improve their performance. This project demonstrates **autonomous AI self-improvement** - an AI agent that can:
- Identify its own failures
- Analyze why it failed  
- Generate improved code
- Implement changes through automated PRs
- Continue learning without human coding intervention

### Target Demonstration
This is a **proof-of-concept** showing autonomous AI agents can evolve their own logic, using Bitcoin prediction as a concrete, measurable domain.

## 🔄 How The System Should Work

### The Self-Improvement Loop

1. **Prediction Phase**
   - Agent makes Bitcoin price movement prediction (up/down)
   - Uses simple keyword-based logic initially
   - Logs prediction with timestamp to JSON file

2. **Evaluation Phase** (24 hours later)
   - Fetches actual Bitcoin price from CoinGecko API
   - Compares prediction vs reality
   - Marks prediction as success/failure

3. **Improvement Phase** (triggered by failure)
   - LLM analyzes the failed prediction context
   - Generates improved prediction logic
   - Creates GitHub PR with enhanced code
   - Includes analysis of why previous logic failed

4. **Integration Phase** (manual)
   - Human reviews PR for safety
   - Merges approved improvements
   - System continues with updated logic

### User Experience Goals

#### For Developers/Researchers
- **Zero Code Maintenance**: Agent writes its own improvements
- **Transparent Process**: All changes visible through GitHub PRs
- **Safe Evolution**: Human approval required for changes
- **Measurable Progress**: Clear metrics on prediction accuracy

#### For AI/ML Community  
- **Reproducible Demo**: Simple setup and clear documentation
- **Observable Learning**: GitHub history shows agent's evolution
- **Extensible Framework**: Easy to adapt to other prediction domains

## 🎯 User Interaction Model

### Minimal Human Intervention Required
- **Initial Setup**: Clone repo, set API keys, run agent
- **PR Reviews**: Approve/reject agent's improvement suggestions
- **Monitoring**: Check logs and metrics periodically

### What Users Should Observe
- **Gradual Improvement**: Prediction logic becomes more sophisticated
- **GitHub Activity**: Regular PRs with thoughtful code improvements  
- **Learning Patterns**: Agent identifies and fixes recurring mistakes
- **Autonomous Operation**: Runs continuously without daily maintenance

## 📊 Expected User Value

### Short-term (Weeks 1-5)
- Working demonstration of AI self-improvement
- Concrete Bitcoin predictions with improving accuracy
- GitHub repository showing autonomous code evolution

### Medium-term (Post-MVP)
- Template for other autonomous agent applications
- Research insights into AI self-improvement patterns
- Foundation for more complex autonomous systems

### Long-term Vision
- Autonomous agents that maintain and improve themselves
- Reduced need for human intervention in AI system maintenance
- New paradigm for evolving AI applications

## 🔍 Success Indicators

### User Observes
- [ ] Agent runs autonomously for 1+ week
- [ ] Meaningful GitHub PRs created automatically
- [ ] Prediction logic visibly evolves over time
- [ ] System handles failures gracefully

### Technical Validation
- [ ] Code improvements actually compile and run
- [ ] Generated PRs include thoughtful analysis
- [ ] Prediction accuracy shows improvement trend
- [ ] No manual coding required after initial setup 