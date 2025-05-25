"""
Autonomous Agent Package for Bitcoin Prediction System

Phase 4: Enhanced with GitHub Automation
- GitHub PR creation for code improvements
- Automated branching and commit management
- LLM-powered PR content generation
- End-to-end autonomous improvement workflow
"""

from .orchestrator import AutonomousAgent
from .interfaces.predictor_interface import PredictorInterface

# Phase 2 & 3 Components
from .tools.bitcoin_api import BitcoinPriceTool
from .tools.code_validator import CodeValidator
from .tools.core_system_manager import CoreSystemManager

# Phase 4: GitHub Integration Components
from .tools.github_manager import GitHubManager

# LangChain Chains
from .chains.evaluator import EvaluatorChain
from .chains.code_analyzer import CodeAnalyzerChain
from .chains.code_improver import CodeImproverChain

# Phase 4: PR Generation Chain
from .chains.pr_generator import PRGenerator

__all__ = [
    # Core orchestration
    'AutonomousAgent',
    'PredictorInterface',
    
    # Phase 2 & 3 Tools
    'BitcoinPriceTool',
    'CodeValidator', 
    'CoreSystemManager',
    
    # Phase 4: GitHub Tools
    'GitHubManager',
    
    # LangChain Chains (Phase 2 & 3)
    'EvaluatorChain',
    'CodeAnalyzerChain',
    'CodeImproverChain',
    
    # Phase 4: PR Chain
    'PRGenerator'
] 