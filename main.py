#!/usr/bin/env python3
"""
Bitcoin Trading System - Main Entry Point

Clean entry point for both the core prediction system and autonomous agent.
No system-specific references in the root directory.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the Bitcoin trading system."""
    parser = argparse.ArgumentParser(
        description="Bitcoin Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Systems:
  core      Bitcoin prediction system (standalone)
  agent     Autonomous agent orchestrator

Examples:
  python main.py core predict              # Make core prediction
  python main.py core test                 # Test core system
  python main.py agent predict             # Agent prediction
  python main.py agent test                # Test agent system
  
Alternative (direct module access):
  python -m bitcoin_predictor.main test   # Direct core access
  python -m autonomous_agent.main test    # Direct agent access
        """
    )
    
    parser.add_argument(
        'system',
        choices=['core', 'agent'],
        help='Which system to run'
    )
    
    parser.add_argument(
        'command',
        help='Command to execute'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Additional arguments'
    )
    
    args = parser.parse_args()
    
    # Dispatch to the appropriate system
    if args.system == 'core':
        from bitcoin_predictor.main import main as core_main
        # Reconstruct argv for the core system
        sys.argv = [sys.argv[0]] + [args.command] + args.args
        return core_main()
    
    elif args.system == 'agent':
        from autonomous_agent.main import main as agent_main
        # Reconstruct argv for the agent system
        sys.argv = [sys.argv[0]] + [args.command] + args.args
        return agent_main()


if __name__ == "__main__":
    sys.exit(main()) 