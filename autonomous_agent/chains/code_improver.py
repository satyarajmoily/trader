"""LangChain code improvement chain for generating enhanced Bitcoin prediction algorithms."""

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
    """LangChain-based code improver for Bitcoin prediction algorithms."""
    
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