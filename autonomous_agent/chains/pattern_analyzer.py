"""
Pattern Analyzer for Enhanced Self-Correction

Analyzes past self-correction attempts to identify patterns and improve future success rates.
Phase 5: Production Deployment & Enhanced Self-Correction
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Analyzes self-correction patterns to improve success rates.
    
    Features:
    - Error pattern recognition
    - Success rate tracking by error type
    - Adaptive prompting recommendations
    - Learning from successful corrections
    """
    
    def __init__(self):
        self.improvements_file = Path("code_improvements_log.json")
        self.patterns_file = Path("self_correction_patterns.json")
        
        # Initialize pattern tracking
        self.error_patterns = {}
        self.success_rates = {}
        self.correction_strategies = {}
        
        # Load existing patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load existing pattern analysis data."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    self.error_patterns = data.get('error_patterns', {})
                    self.success_rates = data.get('success_rates', {})
                    self.correction_strategies = data.get('correction_strategies', {})
                logger.info("Loaded existing self-correction patterns")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save pattern analysis data."""
        try:
            data = {
                'error_patterns': self.error_patterns,
                'success_rates': self.success_rates,
                'correction_strategies': self.correction_strategies,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved self-correction patterns")
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def analyze_improvement_history(self) -> Dict[str, Any]:
        """Analyze the complete improvement history for patterns."""
        if not self.improvements_file.exists():
            return {"error": "No improvement history found"}
        
        try:
            with open(self.improvements_file, 'r') as f:
                improvements = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load improvement history: {e}")
            return {"error": str(e)}
        
        analysis = {
            "total_attempts": len(improvements),
            "error_patterns": self._analyze_error_patterns(improvements),
            "success_patterns": self._analyze_success_patterns(improvements),
            "retry_effectiveness": self._analyze_retry_patterns(improvements),
            "recommendations": self._generate_recommendations(improvements)
        }
        
        # Update internal patterns
        self._update_patterns(analysis)
        
        return analysis
    
    def _analyze_error_patterns(self, improvements: List[Dict]) -> Dict[str, Any]:
        """Analyze common error patterns in failed attempts."""
        error_types = Counter()
        error_details = defaultdict(list)
        
        for improvement in improvements:
            validation_status = improvement.get('validation_status', 'unknown')
            
            # Look for failed attempts
            if 'failed_attempt' in validation_status:
                # Extract error type from the improved code (common patterns)
                code = improvement.get('improved_code', '')
                
                # Common error patterns
                if 'f"' in code and '\n' in code:
                    error_types['f_string_line_break'] += 1
                    error_details['f_string_line_break'].append(improvement['improvement_id'])
                
                if not code.startswith('    def analyze'):
                    error_types['indentation_error'] += 1
                    error_details['indentation_error'].append(improvement['improvement_id'])
                
                if 'logger.info(f"' in code and '\\' in code:
                    error_types['logger_f_string_error'] += 1
                    error_details['logger_f_string_error'].append(improvement['improvement_id'])
                
                if 'def analyze(' in code and not code.strip().startswith('def analyze('):
                    error_types['method_structure_error'] += 1
                    error_details['method_structure_error'].append(improvement['improvement_id'])
        
        return {
            "most_common_errors": dict(error_types.most_common(10)),
            "error_details": dict(error_details),
            "total_failed_attempts": sum(error_types.values())
        }
    
    def _analyze_success_patterns(self, improvements: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in successful corrections."""
        successful_attempts = [
            imp for imp in improvements 
            if imp.get('validation_status') == 'passed'
        ]
        
        success_patterns = {
            "total_successful": len(successful_attempts),
            "success_rate": len(successful_attempts) / len(improvements) if improvements else 0,
            "successful_strategies": []
        }
        
        # Analyze what made successful attempts work
        for success in successful_attempts:
            changes = success.get('changes_made', [])
            success_patterns['successful_strategies'].extend(changes)
        
        # Count successful strategy patterns
        strategy_counter = Counter(success_patterns['successful_strategies'])
        success_patterns['most_effective_strategies'] = dict(strategy_counter.most_common(5))
        
        return success_patterns
    
    def _analyze_retry_patterns(self, improvements: List[Dict]) -> Dict[str, Any]:
        """Analyze effectiveness of retry logic by improvement ID."""
        retry_analysis = {
            "improvements_with_retries": 0,
            "average_retries_to_success": 0,
            "retry_success_rate": 0
        }
        
        # Group by analysis_id to track retry sequences
        retry_sequences = defaultdict(list)
        for improvement in improvements:
            analysis_id = improvement.get('analysis_id')
            if analysis_id:
                retry_sequences[analysis_id].append(improvement)
        
        sequences_with_retries = 0
        successful_sequences = 0
        total_retries = 0
        
        for analysis_id, sequence in retry_sequences.items():
            if len(sequence) > 1:  # Has retries
                sequences_with_retries += 1
                total_retries += len(sequence) - 1
                
                # Check if any attempt in sequence succeeded
                if any(imp.get('validation_status') == 'passed' for imp in sequence):
                    successful_sequences += 1
        
        if sequences_with_retries > 0:
            retry_analysis.update({
                "improvements_with_retries": sequences_with_retries,
                "average_retries_to_success": total_retries / sequences_with_retries,
                "retry_success_rate": successful_sequences / sequences_with_retries
            })
        
        return retry_analysis
    
    def _generate_recommendations(self, improvements: List[Dict]) -> List[str]:
        """Generate recommendations for improving self-correction."""
        recommendations = []
        
        # Analyze recent failures
        recent_failures = [
            imp for imp in improvements[-20:]  # Last 20 attempts
            if 'failed_attempt' in imp.get('validation_status', '')
        ]
        
        if len(recent_failures) > 10:
            recommendations.append(
                "HIGH: High failure rate detected. Consider enhancing prompting strategies."
            )
        
        # Check for specific error patterns
        f_string_errors = sum(1 for imp in recent_failures 
                             if 'f"' in imp.get('improved_code', '') and '\n' in imp.get('improved_code', ''))
        
        if f_string_errors > 3:
            recommendations.append(
                "MEDIUM: Frequent f-string formatting errors. Add specific guidance about single-line f-strings."
            )
        
        # Check indentation issues
        indentation_errors = sum(1 for imp in recent_failures 
                               if not imp.get('improved_code', '').startswith('    def analyze'))
        
        if indentation_errors > 3:
            recommendations.append(
                "HIGH: Frequent indentation errors. Emphasize proper method structure in prompts."
            )
        
        return recommendations
    
    def _update_patterns(self, analysis: Dict[str, Any]):
        """Update internal pattern tracking with new analysis."""
        # Update error patterns
        error_patterns = analysis.get('error_patterns', {})
        for error_type, count in error_patterns.get('most_common_errors', {}).items():
            self.error_patterns[error_type] = count
        
        # Update success rates
        success_patterns = analysis.get('success_patterns', {})
        self.success_rates['overall'] = success_patterns.get('success_rate', 0)
        
        # Update retry effectiveness
        retry_patterns = analysis.get('retry_effectiveness', {})
        self.success_rates['retry_effectiveness'] = retry_patterns.get('retry_success_rate', 0)
        
        # Save updated patterns
        self._save_patterns()
    
    def get_adaptive_prompting_strategy(self, error_type: str) -> str:
        """Get adaptive prompting strategy for specific error type."""
        strategies = {
            'f_string_line_break': """
CRITICAL F-STRING FORMATTING:
- Never break f-strings across multiple lines
- Keep all f-string content on a single line
- Use proper escaping for quotes within f-strings
- Example: logger.info(f"Analysis complete: {result}")
- WRONG: logger.info(f"Analysis: {result} \\
                      more text")
""",
            'indentation_error': """
CRITICAL INDENTATION REQUIREMENTS:
- The method body MUST start with proper 4-space indentation
- ALL code inside the method must be indented
- NO code should be at the top level
- Structure: def analyze(self, price_data): → 4 spaces → method body
- Every line inside the method needs 4-space indentation from the def line
""",
            'logger_f_string_error': """
CRITICAL LOGGER STATEMENT FORMATTING:
- Logger statements with f-strings must be on single lines
- No line continuation in logger.info() calls
- Example: logger.info(f"Technical Analysis - MA: {short_ma:.2f}")
- WRONG: logger.info(f"Technical Analysis \\
                      - MA: {short_ma:.2f}")
""",
            'method_structure_error': """
CRITICAL METHOD STRUCTURE:
- Generate ONLY the method implementation
- Start with: def analyze(self, price_data: List[OHLCVData]) -> AnalysisResult:
- Include proper docstring and method body
- NO standalone code outside the method
- Return AnalysisResult with all required fields
"""
        }
        
        return strategies.get(error_type, "Focus on proper Python syntax and structure.")
    
    def get_error_likelihood(self, error_type: str) -> float:
        """Get likelihood of specific error type based on history."""
        total_errors = sum(self.error_patterns.values()) if self.error_patterns else 1
        error_count = self.error_patterns.get(error_type, 0)
        return error_count / total_errors
    
    def get_success_rate_metrics(self) -> Dict[str, float]:
        """Get success rate metrics for monitoring."""
        return {
            "overall_success_rate": self.success_rates.get('overall', 0.0),
            "retry_success_rate": self.success_rates.get('retry_effectiveness', 0.0),
            "improvement_needed": self.success_rates.get('overall', 0.0) < 0.5
        }
    
    def export_pattern_analysis(self, filename: str = None) -> str:
        """Export comprehensive pattern analysis."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pattern_analysis_{timestamp}.json"
        
        analysis = self.analyze_improvement_history()
        export_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "pattern_analysis": analysis,
            "stored_patterns": {
                "error_patterns": self.error_patterns,
                "success_rates": self.success_rates,
                "correction_strategies": self.correction_strategies
            },
            "recommendations": analysis.get('recommendations', [])
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Pattern analysis exported to {filename}")
        return filename 