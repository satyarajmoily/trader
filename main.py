#!/usr/bin/env python3
"""
Bitcoin Trading System - Main Entry Point

Clean entry point for all system components including Phase 5 production features:
- Core prediction system
- Autonomous agent orchestrator  
- Health monitoring and observability
- Production deployment automation
- Performance monitoring and optimization

No system-specific references in the root directory.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Any


def main():
    """Main entry point for the Bitcoin trading system."""
    parser = argparse.ArgumentParser(
        description="Bitcoin Trading System - Phase 5: Production Ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Systems:
  core      Bitcoin prediction system (standalone)
  agent     Autonomous agent orchestrator
  health    System health monitoring (Phase 5)
  deploy    Production deployment (Phase 5)
  monitor   Monitoring and observability (Phase 5)

Examples:
  # Core System
  python main.py core predict              # Make core prediction
  python main.py core test                 # Test core system
  
  # Agent System  
  python main.py agent predict             # Agent prediction
  python main.py agent test                # Test agent system
  python main.py agent auto-cycle          # Full autonomous cycle
  
  # Phase 5: Enhanced Autonomous Operations 🚀
  python main.py agent autonomous --mode local --continuous      # Local continuous operation
  python main.py agent autonomous --mode production              # Production PR workflow  
  python main.py agent demo                                      # Fast demonstration mode
  
  # Phase 5: Production & Monitoring
  python main.py health check              # System health check
  python main.py health detailed           # Detailed health report
  python main.py deploy production         # Deploy to production
  python main.py monitor start             # Start monitoring dashboard
  
Alternative (direct module access):
  python -m bitcoin_predictor.main test   # Direct core access
  python -m autonomous_agent.main test    # Direct agent access
        """
    )
    
    parser.add_argument(
        'system',
        choices=['core', 'agent', 'health', 'deploy', 'monitor'],
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
    
    elif args.system == 'health':
        return handle_health_commands(args.command, args.args)
    
    elif args.system == 'deploy':
        return handle_deployment_commands(args.command, args.args)
    
    elif args.system == 'monitor':
        return handle_monitoring_commands(args.command, args.args)


def handle_health_commands(command: str, args: List[str]) -> int:
    """Handle health monitoring commands."""
    try:
        from monitoring.health_checker import HealthChecker
        
        health_checker = HealthChecker()
        
        if command == 'check':
            print("🏥 Performing comprehensive system health check...")
            health = health_checker.perform_comprehensive_health_check()
            
            # Print summary
            print(f"\n📊 Overall Status: {health.overall_status.upper()}")
            print(f"⏱️  Uptime: {health.uptime_seconds / 3600:.1f} hours")
            print(f"🕐 Timestamp: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Print component status
            print(f"\n🔧 Component Health:")
            for component in health.components:
                status_emoji = "✅" if component.status == "healthy" else "⚠️" if component.status == "degraded" else "❌"
                print(f"  {status_emoji} {component.component}: {component.status} ({component.response_time_ms:.1f}ms)")
                if component.error_message:
                    print(f"     Error: {component.error_message}")
            
            return 0 if health.overall_status == "healthy" else 1
            
        elif command == 'detailed':
            print("🏥 Performing detailed system health check...")
            health = health_checker.perform_comprehensive_health_check()
            summary = health_checker.get_health_summary(detailed=True)
            
            print(json.dumps(summary, indent=2, default=str))
            return 0
            
        elif command == 'export':
            filename = health_checker.export_health_history()
            print(f"📁 Health history exported to: {filename}")
            return 0
            
        else:
            print(f"❌ Unknown health command: {command}")
            print("Available commands: check, detailed, export")
            return 1
            
    except ImportError as e:
        print(f"❌ Health monitoring not available: {e}")
        print("Make sure monitoring package is properly installed.")
        return 1
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1


def handle_deployment_commands(command: str, args: List[str]) -> int:
    """Handle deployment commands."""
    try:
        if command == 'production':
            print("🚀 Deploying to production environment...")
            
            # Check Docker availability
            import subprocess
            try:
                subprocess.run(['docker', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Docker not available. Please install Docker to deploy.")
                return 1
            
            # Run Docker Compose
            compose_file = Path("deployment/docker/docker-compose.yml")
            if not compose_file.exists():
                print(f"❌ Compose file not found: {compose_file}")
                return 1
            
            print("📦 Building and starting containers...")
            result = subprocess.run([
                'docker-compose', 
                '-f', str(compose_file),
                'up', '--build', '-d'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Production deployment successful!")
                print("🌐 Services available:")
                print("  - Core System: Internal network")
                print("  - Agent System: Internal network") 
                print("  - Health Monitor: http://localhost:8080")
                print("  - Kibana Dashboard: http://localhost:5601")
                return 0
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return 1
                
        elif command == 'staging':
            print("🧪 Deploying to staging environment...")
            # Similar to production but with staging configuration
            print("ℹ️  Staging deployment not yet implemented")
            return 1
            
        elif command == 'stop':
            print("🛑 Stopping deployment...")
            import subprocess
            compose_file = Path("deployment/docker/docker-compose.yml")
            subprocess.run(['docker-compose', '-f', str(compose_file), 'down'])
            print("✅ Deployment stopped")
            return 0
            
        else:
            print(f"❌ Unknown deployment command: {command}")
            print("Available commands: production, staging, stop")
            return 1
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1


def handle_monitoring_commands(command: str, args: List[str]) -> int:
    """Handle monitoring commands."""
    try:
        if command == 'start':
            print("📊 Starting monitoring dashboard...")
            # This would start a simple web server for monitoring
            print("ℹ️  Monitoring dashboard startup not yet implemented")
            print("💡 Use 'python main.py deploy production' for full monitoring stack")
            return 0
            
        elif command == 'status':
            print("📈 System monitoring status...")
            from monitoring.health_checker import HealthChecker
            health_checker = HealthChecker()
            summary = health_checker.get_health_summary()
            
            if "error" in summary:
                print("⚠️  No health data available yet")
                return 1
                
            print(f"📊 Overall Status: {summary['overall_status']}")
            print(f"⏱️  Uptime: {summary['uptime_hours']} hours") 
            print(f"🔧 Components: {summary['components_summary']}")
            return 0
            
        else:
            print(f"❌ Unknown monitoring command: {command}")
            print("Available commands: start, status")
            return 1
            
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 