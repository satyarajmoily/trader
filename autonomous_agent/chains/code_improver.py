"""LangChain code improvement chain for generating enhanced Bitcoin prediction algorithms.

Phase 5: Enhanced Self-Correction with Pattern Analysis
"""

import json
import logging
import ast
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .code_analyzer import AnalysisResult
from .pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)


class CodeImprovementResult(BaseModel):
    """Structured result for code improvements."""
    improvement_id: str
    analysis_id: str = Field(description="ID of the analysis that triggered this improvement")
    original_code: str = Field(description="Original prediction code")
    improved_code: str = Field(description="Generated improved code")
    improvement_description: str = Field(description="Description of what was improved")
    changes_made: List[str] = Field(description="List of specific changes made")
    expected_benefits: List[str] = Field(description="Expected performance benefits")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in the improvement")
    validation_status: str = Field(default="pending", description="Code validation status")
    timestamp: str


class CodeImprovementOutputParser(BaseOutputParser[Dict[str, Any]]):
    """Parser for LLM code improvement output."""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse LLM output into structured code improvement result."""
        try:
            # Extract JSON from LLM response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group())
                return result_dict
            else:
                raise ValueError("No JSON found in LLM response")
        except Exception as e:
            logger.error(f"Failed to parse code improvement output: {e}")
            # Return default result
            return {
                "improved_code": "# Code generation failed",
                "improvement_description": f"Failed to generate improvement: {e}",
                "changes_made": ["Fix code generation issues"],
                "expected_benefits": ["Resolve parsing problems"],
                "confidence_score": 0.0
            }


class CodeImproverChain:
    """LangChain-based code improver for Bitcoin prediction algorithms with enhanced self-correction."""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the code improver.
        
        Args:
            llm: Optional LLM instance, will create default if not provided
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,  # Slightly higher for creativity in code generation
            max_tokens=3000
        )
        
        self.improvement_chain = self._create_improvement_chain()
        self.improvements_file = Path("code_improvements_log.json")
        
        # Phase 5: Enhanced Self-Correction
        self.pattern_analyzer = PatternAnalyzer()
        self.self_correction_metrics = {
            "total_attempts": 0,
            "successful_corrections": 0,
            "pattern_guided_improvements": 0
        }
        
    def _create_improvement_chain(self) -> LLMChain:
        """Create the LangChain code improvement chain."""
        
        improvement_prompt = PromptTemplate(
            input_variables=[
                "analysis_result",
                "original_code",
                "improvement_focus"
            ],
            template="""You are a Bitcoin prediction algorithm improvement specialist. Generate improved code based on the failure analysis.

FAILURE ANALYSIS:
{analysis_result}

ORIGINAL PREDICTION CODE:
```python
{original_code}
```

IMPROVEMENT FOCUS:
{improvement_focus}

CODE IMPROVEMENT REQUIREMENTS:
1. Maintain the exact same function signature: analyze(self, price_data: List[OHLCVData]) -> AnalysisResult
2. Keep the same return structure and data models
3. Improve the technical analysis logic based on the failure analysis
4. Focus on the specific issues identified in the analysis
5. Ensure the code is syntactically correct and runnable
6. Add comments explaining the improvements made

SPECIFIC IMPROVEMENTS TO CONSIDER:
- Adjust moving average periods for better trend detection
- Improve momentum calculation to handle different market conditions
- Enhance volume analysis for better signal validation
- Optimize signal weighting and threshold values
- Add market volatility considerations
- Improve handling of edge cases and market anomalies

IMPORTANT CONSTRAINTS:
- Only modify the analyze() method implementation
- Keep all existing imports and class structure
- Maintain compatibility with existing data models
- Ensure improved logic addresses the specific failure reasons identified

Respond with ONLY a JSON object in this exact format:
{{
    "improved_code": "# Complete improved analyze() method code only",
    "improvement_description": "Clear description of what was improved and why",
    "changes_made": [
        "Specific change 1 (e.g., 'Adjusted short MA from 3 to 5 days')",
        "Specific change 2 (e.g., 'Added volatility-based momentum scaling')",
        "..."
    ],
    "expected_benefits": [
        "Expected benefit 1 (e.g., 'Better trend detection in volatile markets')",
        "Expected benefit 2 (e.g., 'Reduced false signals during consolidation')",
        "..."
    ],
    "confidence_score": 0.0-1.0
}}

Make sure the JSON is valid and the improved_code contains only the analyze() method implementation."""
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=improvement_prompt,
            output_parser=CodeImprovementOutputParser()
        )
    
    def _save_improvement(self, improvement: CodeImprovementResult):
        """Save improvement result to JSON file."""
        improvements = []
        
        # Load existing improvements
        if self.improvements_file.exists():
            try:
                with open(self.improvements_file, 'r') as f:
                    improvements = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing improvements: {e}")
        
        # Add new improvement
        improvements.append(improvement.dict())
        
        # Save back to file
        try:
            with open(self.improvements_file, 'w') as f:
                json.dump(improvements, f, indent=2)
            logger.info(f"Saved improvement {improvement.improvement_id}")
        except Exception as e:
            logger.error(f"Failed to save improvement: {e}")
    
    def _extract_analyze_method(self, code: str) -> str:
        """Extract just the analyze method from the full code."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "analyze":
                    # Get the method code
                    method_lines = code.split('\n')[node.lineno-1:node.end_lineno]
                    return '\n'.join(method_lines)
            
            logger.warning("analyze method not found in code")
            return "# analyze method not found"
            
        except Exception as e:
            logger.error(f"Failed to extract analyze method: {e}")
            return f"# Failed to extract method: {e}"
    
    def _read_current_predictor_code(self) -> str:
        """Read the current predictor code."""
        try:
            code_file = Path("bitcoin_predictor/predictor.py")
            if code_file.exists():
                with open(code_file, 'r') as f:
                    return f.read()
            else:
                logger.error("Predictor code file not found")
                return "# Predictor code not found"
        except Exception as e:
            logger.error(f"Failed to read predictor code: {e}")
            return f"# Failed to read code: {e}"
    
    def _format_analysis_for_prompt(self, analysis: AnalysisResult) -> str:
        """Format analysis result for the improvement prompt."""
        analysis_text = f"""
Prediction ID: {analysis.prediction_id}
Failure Reason: {analysis.failure_reason}
Market Context: {analysis.market_context}

Improvement Opportunities:
{chr(10).join(f"- {opp}" for opp in analysis.improvement_opportunities)}

Technical Indicators Analysis:
{chr(10).join(f"- {key}: {value}" for key, value in analysis.technical_indicators_analysis.items())}

Suggested Modifications:
{chr(10).join(f"- {mod}" for mod in analysis.suggested_modifications)}

Confidence Score: {analysis.confidence_score}
"""
        return analysis_text.strip()
    
    def generate_improved_code(self, analysis: AnalysisResult, 
                             improvement_focus: Optional[str] = None) -> Optional[CodeImprovementResult]:
        """
        Generate improved prediction code based on failure analysis.
        
        Args:
            analysis: AnalysisResult from code analysis
            improvement_focus: Optional specific focus for improvement
            
        Returns:
            CodeImprovementResult if successful, None if failed
        """
        try:
            # Read current code
            original_code = self._read_current_predictor_code()
            analyze_method = self._extract_analyze_method(original_code)
            
            # Format analysis for prompt
            analysis_text = self._format_analysis_for_prompt(analysis)
            
            # Set default improvement focus if not provided
            if not improvement_focus:
                improvement_focus = "Focus on the primary failure reasons and suggested modifications from the analysis"
            
            # Generate improvement
            result_dict = self.improvement_chain.run(
                analysis_result=analysis_text,
                original_code=analyze_method,
                improvement_focus=improvement_focus
            )
            
            # Create improvement result
            improvement_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            improvement = CodeImprovementResult(
                improvement_id=improvement_id,
                analysis_id=analysis.prediction_id,
                original_code=analyze_method,
                improved_code=result_dict["improved_code"],
                improvement_description=result_dict["improvement_description"],
                changes_made=result_dict["changes_made"],
                expected_benefits=result_dict["expected_benefits"],
                confidence_score=result_dict["confidence_score"],
                validation_status="pending",
                timestamp=datetime.now().isoformat()
            )
            
            # Save improvement
            self._save_improvement(improvement)
            
            logger.info(f"Generated code improvement {improvement_id} for analysis {analysis.prediction_id}")
            return improvement
            
        except Exception as e:
            logger.error(f"Failed to generate improved code: {e}")
            return None
    
    def generate_improvements_from_analyses(self, analyses: List[AnalysisResult]) -> List[CodeImprovementResult]:
        """
        Generate improved code from multiple analyses.
        
        Args:
            analyses: List of AnalysisResult objects
            
        Returns:
            List of CodeImprovementResult objects
        """
        improvements = []
        
        for analysis in analyses:
            logger.info(f"Generating improvement for analysis {analysis.prediction_id}")
            improvement = self.generate_improved_code(analysis)
            if improvement:
                improvements.append(improvement)
        
        logger.info(f"Generated {len(improvements)} code improvements from {len(analyses)} analyses")
        return improvements
    
    def validate_generated_code(self, improved_code: str) -> Dict[str, Any]:
        """
        Validate the generated code for syntax and basic structure.
        
        Args:
            improved_code: Generated code to validate
            
        Returns:
            Dict with validation results
        """
        try:
            # Basic syntax check
            ast.parse(improved_code)
            
            # Check for required function signature
            if "def analyze(self, price_data:" not in improved_code:
                return {
                    "valid": False,
                    "error": "Missing required analyze method signature",
                    "details": "Code must contain 'def analyze(self, price_data:' method"
                }
            
            # Check for return statement
            if "return AnalysisResult" not in improved_code:
                return {
                    "valid": False,
                    "error": "Missing required return statement",
                    "details": "Method must return AnalysisResult object"
                }
            
            return {
                "valid": True,
                "message": "Code validation passed",
                "details": "Syntax and structure checks completed successfully"
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {e}",
                "details": f"Line {e.lineno}: {e.text}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {e}",
                "details": str(e)
            }
    
    def get_improvement_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get history of code improvements.
        
        Args:
            limit: Maximum number of improvements to return
            
        Returns:
            List of improvement records
        """
        if not self.improvements_file.exists():
            return []
        
        try:
            with open(self.improvements_file, 'r') as f:
                improvements = json.load(f)
            
            if limit:
                return improvements[-limit:]
            return improvements
            
        except Exception as e:
            logger.error(f"Failed to load improvement history: {e}")
            return []
    
    def generate_improved_code_with_retry(self, analysis: AnalysisResult, 
                                        improvement_focus: Optional[str] = None,
                                        max_retries: int = 3) -> Optional[CodeImprovementResult]:
        """
        Generate improved prediction code with enhanced pattern-based self-correction.
        
        Args:
            analysis: AnalysisResult from code analysis
            improvement_focus: Optional specific focus for improvement
            max_retries: Maximum number of retry attempts
            
        Returns:
            CodeImprovementResult if successful, None if all retries failed
        """
        try:
            from ..tools.code_validator import CodeValidator
        except ImportError:
            from autonomous_agent.tools.code_validator import CodeValidator
        
        try:
            from ...monitoring.metrics_collector import record_metric, increment_counter
        except ImportError:
            # Create mock functions if monitoring not available
            def record_metric(name, value, tags=None):
                logger.debug(f"Metric: {name}={value} {tags or ''}")
            def increment_counter(name):
                logger.debug(f"Counter: {name}++")
        
        validator = CodeValidator()
        last_error = None
        error_type_detected = None
        
        # Phase 5: Track self-correction metrics
        self.self_correction_metrics["total_attempts"] += 1
        record_metric("self_correction_attempt", 1)
        
        # Phase 5: Analyze patterns before starting
        pattern_analysis = self.pattern_analyzer.analyze_improvement_history()
        logger.info(f"📊 Pattern Analysis: {len(pattern_analysis.get('error_patterns', {}).get('most_common_errors', {}))} error types identified")
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🔄 Code generation attempt {attempt + 1}/{max_retries + 1}")
                
                # Generate improved code with pattern-based enhancement
                if attempt == 0:
                    # First attempt - use original analysis with pattern insights
                    enhanced_focus = self._enhance_focus_with_patterns(improvement_focus, pattern_analysis)
                    improvement = self.generate_improved_code(analysis, enhanced_focus)
                else:
                    # Retry attempt - include validation feedback AND pattern-specific strategies
                    enhanced_focus = self._create_pattern_aware_retry_focus(
                        improvement_focus, last_error, attempt, error_type_detected, pattern_analysis
                    )
                    improvement = self.generate_improved_code(analysis, enhanced_focus)
                    self.self_correction_metrics["pattern_guided_improvements"] += 1
                
                if not improvement:
                    last_error = "Code generation failed - no improvement result"
                    continue
                
                # Validate the generated code
                logger.info(f"🔍 Validating generated code (attempt {attempt + 1})")
                validation_result = validator.comprehensive_validation(
                    improvement.improved_code, 
                    test_execution=True
                )
                
                if validation_result.get("overall_valid", False):
                    # Success! Track metrics and update status
                    improvement.validation_status = "passed"
                    self.self_correction_metrics["successful_corrections"] += 1
                    
                    # Phase 5: Record success metrics
                    record_metric("self_correction_success", 1, {"attempt": attempt + 1})
                    increment_counter("successful_self_corrections")
                    
                    logger.info(f"✅ Code generation successful on attempt {attempt + 1}")
                    logger.info(f"📈 Success rate: {self._get_success_rate():.1%}")
                    return improvement
                else:
                    # Validation failed - analyze error type for pattern recognition
                    last_error = self._extract_validation_errors(validation_result)
                    error_type_detected = self._detect_error_type(last_error, improvement.improved_code)
                    improvement.validation_status = f"failed_attempt_{attempt + 1}"
                    
                    # Phase 5: Record failure metrics
                    record_metric("self_correction_failure", 1, {
                        "attempt": attempt + 1, 
                        "error_type": error_type_detected
                    })
                    
                    logger.warning(f"❌ Validation failed on attempt {attempt + 1}: {last_error}")
                    logger.info(f"🔍 Error type detected: {error_type_detected}")
                    
                    if attempt < max_retries:
                        logger.info(f"🔄 Retrying with pattern-based feedback...")
                    else:
                        logger.error(f"💥 All {max_retries + 1} attempts failed")
                        
            except Exception as e:
                last_error = f"Generation error: {str(e)}"
                logger.error(f"Code generation attempt {attempt + 1} failed: {e}")
                
                if attempt >= max_retries:
                    break
        
        # All retries failed - record final failure
        record_metric("self_correction_total_failure", 1)
        increment_counter("failed_self_correction_sequences")
        
        logger.error(f"💥 Failed to generate valid code after {max_retries + 1} attempts.")
        logger.error(f"📊 Current success rate: {self._get_success_rate():.1%}")
        logger.error(f"🔍 Last error: {last_error}")
        return None
    
    def _create_retry_focus(self, original_focus: Optional[str], validation_error: str, attempt: int) -> str:
        """Create enhanced improvement focus based on validation failures."""
        
        retry_focus = f"""RETRY ATTEMPT #{attempt} - PREVIOUS VALIDATION FAILED

VALIDATION ERRORS TO FIX:
{validation_error}

ORIGINAL FOCUS:
{original_focus or "Focus on the primary failure reasons from analysis"}

CRITICAL RETRY REQUIREMENTS:
1. Fix the specific validation errors mentioned above
2. Pay special attention to Python syntax and indentation
3. Ensure proper f-string formatting (no line breaks in f-strings)
4. Verify all code is properly indented within the method
5. Test that logger statements are syntactically correct
6. Ensure no missing class context or method structure issues

COMMON FIXES NEEDED:
- Fix IndentationError: Add proper 4-space indentation for all code inside the method
- Fix f-string syntax errors: Don't break f-strings across lines, use proper escaping
- Fix missing class context: Generate only the method body, not standalone code
- Fix execution errors: Ensure the method can actually run with test data

VALIDATION FOCUS:
Generate clean, properly indented Python code that will pass both syntax validation and execution testing.

IMPORTANT CODE STRUCTURE:
Your response must contain ONLY the analyze() method implementation with proper indentation:

```python
def analyze(self, price_data: List[OHLCVData]) -> AnalysisResult:
    # Method body starts here with 4-space indentation
    # All code inside the method must be indented
    # No code should be at the top level
    
    # Example structure:
    if len(price_data) < 5:
        return AnalysisResult(...)
    
    # Calculate indicators
    short_ma = sum(d.close for d in price_data[-3:]) / 3
    
    # Return result
    return AnalysisResult(
        short_ma=short_ma,
        # ... other fields
    )
```

Make sure every line inside the method is indented with 4 spaces."""
        
        return retry_focus
    
    def _extract_validation_errors(self, validation_result: Dict[str, Any]) -> str:
        """Extract key validation errors for retry feedback."""
        errors = []
        
        # Check interface compatibility errors
        interface_result = validation_result.get("interface_compatibility", {})
        
        # Syntax errors
        syntax_result = interface_result.get("syntax", {})
        if not syntax_result.get("valid", False):
            error_msg = syntax_result.get("message", "Unknown syntax error")
            line = syntax_result.get("line", "unknown")
            errors.append(f"SYNTAX ERROR (line {line}): {error_msg}")
        
        # Execution errors
        exec_result = validation_result.get("execution_test", {})
        if not exec_result.get("valid", False):
            exec_error = exec_result.get("error", "Unknown execution error")
            errors.append(f"EXECUTION ERROR: {exec_error}")
        
        # Signature errors
        sig_result = interface_result.get("signature", {})
        if not sig_result.get("valid", False):
            sig_error = sig_result.get("message", "Function signature issues")
            errors.append(f"SIGNATURE ERROR: {sig_error}")
        
        # Return type errors
        return_result = interface_result.get("return_type", {})
        if not return_result.get("valid", False):
            return_error = return_result.get("message", "Return type issues")
            errors.append(f"RETURN TYPE ERROR: {return_error}")
        
        if not errors:
            errors.append("Validation failed with unknown errors")
        
        return "\n".join(errors)
    
    def _enhance_focus_with_patterns(self, original_focus: Optional[str], pattern_analysis: Dict[str, Any]) -> str:
        """Enhance improvement focus with pattern analysis insights."""
        pattern_insights = ""
        
        # Add insights from common error patterns
        error_patterns = pattern_analysis.get('error_patterns', {})
        common_errors = error_patterns.get('most_common_errors', {})
        
        if common_errors:
            pattern_insights += "\nPATTERN-BASED PREVENTION:\n"
            for error_type, count in list(common_errors.items())[:3]:  # Top 3 errors
                strategy = self.pattern_analyzer.get_adaptive_prompting_strategy(error_type)
                pattern_insights += f"- Avoid {error_type} ({count} occurrences): {strategy}\n"
        
        # Add success pattern insights
        success_patterns = pattern_analysis.get('success_patterns', {})
        effective_strategies = success_patterns.get('most_effective_strategies', {})
        
        if effective_strategies:
            pattern_insights += "\nSUCCESSFUL STRATEGIES TO EMPHASIZE:\n"
            for strategy, count in list(effective_strategies.items())[:3]:  # Top 3 strategies
                pattern_insights += f"- {strategy} (successful {count} times)\n"
        
        enhanced_focus = f"""
{original_focus or "Focus on the primary failure reasons from analysis"}

{pattern_insights}

PATTERN-BASED ENHANCEMENT:
Based on historical analysis of {pattern_analysis.get('total_attempts', 0)} attempts:
- Success rate: {success_patterns.get('success_rate', 0):.1%}
- Most common errors have been identified and should be actively avoided
- Proven successful strategies should be prioritized
"""
        return enhanced_focus
    
    def _create_pattern_aware_retry_focus(
        self, 
        original_focus: Optional[str], 
        validation_error: str, 
        attempt: int,
        error_type: Optional[str],
        pattern_analysis: Dict[str, Any]
    ) -> str:
        """Create retry focus with pattern-aware strategies."""
        
        # Get specific strategy for detected error type
        error_specific_strategy = ""
        if error_type:
            error_specific_strategy = self.pattern_analyzer.get_adaptive_prompting_strategy(error_type)
            likelihood = self.pattern_analyzer.get_error_likelihood(error_type)
            error_specific_strategy += f"\nERROR LIKELIHOOD: {likelihood:.1%} - This is a known problematic pattern.\n"
        
        pattern_aware_focus = f"""RETRY ATTEMPT #{attempt} - PATTERN-AWARE CORRECTION

CURRENT VALIDATION ERRORS TO FIX:
{validation_error}

PATTERN-SPECIFIC STRATEGY:
{error_specific_strategy}

HISTORICAL CONTEXT:
- This error type occurred {self.pattern_analyzer.error_patterns.get(error_type, 0)} times previously
- Current system success rate: {self._get_success_rate():.1%}
- Retry success rate: {pattern_analysis.get('retry_effectiveness', {}).get('retry_success_rate', 0):.1%}

ORIGINAL FOCUS:
{original_focus or "Focus on the primary failure reasons from analysis"}

ADAPTIVE REQUIREMENTS:
1. Apply the pattern-specific strategy above with HIGH PRIORITY
2. Learn from the specific error type and implement targeted fixes
3. Follow proven successful patterns from historical analysis
4. Avoid the most common error patterns identified in system history

ENHANCED VALIDATION FOCUS:
Generate clean, properly structured Python code that addresses both the current error AND prevents the historically common errors.
"""
        return pattern_aware_focus
    
    def _detect_error_type(self, validation_error: str, code: str) -> str:
        """Detect the specific error type for pattern analysis."""
        error_lower = validation_error.lower()
        
        if 'indentation' in error_lower or 'indent' in error_lower:
            return 'indentation_error'
        elif 'f-string' in error_lower or ('f"' in code and '\n' in code):
            return 'f_string_line_break'
        elif 'syntax' in error_lower and 'logger' in code:
            return 'logger_f_string_error'
        elif 'signature' in error_lower or 'def analyze(' in validation_error:
            return 'method_structure_error'
        elif 'syntax' in error_lower:
            return 'general_syntax_error'
        elif 'execution' in error_lower:
            return 'execution_error'
        else:
            return 'unknown_error'
    
    def _get_success_rate(self) -> float:
        """Calculate current self-correction success rate."""
        total = self.self_correction_metrics["total_attempts"]
        successful = self.self_correction_metrics["successful_corrections"]
        return successful / total if total > 0 else 0.0
    
    def get_self_correction_metrics(self) -> Dict[str, Any]:
        """Get comprehensive self-correction metrics."""
        success_rate = self._get_success_rate()
        pattern_metrics = self.pattern_analyzer.get_success_rate_metrics()
        
        return {
            "current_session": self.self_correction_metrics,
            "success_rate": success_rate,
            "pattern_analysis": pattern_metrics,
            "performance_status": "excellent" if success_rate > 0.8 else "good" if success_rate > 0.6 else "needs_improvement"
        } 