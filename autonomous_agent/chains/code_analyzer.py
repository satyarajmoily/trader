"""LangChain code analysis chain for identifying Bitcoin prediction improvement opportunities."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Literal
from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..interfaces.predictor_interface import PredictorInterface
from ..tools.bitcoin_api import BitcoinPriceTool

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """Structured analysis result for failed predictions."""
    prediction_id: str
    failure_reason: str = Field(description="Primary reason for prediction failure")
    market_context: str = Field(description="Market conditions during prediction period")
    improvement_opportunities: List[str] = Field(description="Specific areas for code improvement")
    technical_indicators_analysis: Dict[str, str] = Field(description="Analysis of technical indicators performance")
    suggested_modifications: List[str] = Field(description="Specific code modification suggestions")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in the analysis")
    timestamp: str


class AnalysisOutputParser(BaseOutputParser[AnalysisResult]):
    """Parser for LLM analysis output."""
    
    def parse(self, text: str) -> AnalysisResult:
        """Parse LLM output into structured analysis result."""
        try:
            # Extract JSON from LLM response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group())
                return AnalysisResult(**result_dict)
            else:
                raise ValueError("No JSON found in LLM response")
        except Exception as e:
            logger.error(f"Failed to parse analysis output: {e}")
            # Return default analysis result
            return AnalysisResult(
                prediction_id="unknown",
                failure_reason=f"Parsing failed: {e}",
                market_context="Unknown market conditions",
                improvement_opportunities=["Fix parsing issues"],
                technical_indicators_analysis={"error": "Failed to parse analysis"},
                suggested_modifications=["Review analysis system"],
                confidence_score=0.0,
                timestamp=datetime.now().isoformat()
            )


class CodeAnalyzerChain:
    """LangChain-based analyzer for failed Bitcoin predictions to identify code improvements."""
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 predictor_interface: Optional[PredictorInterface] = None,
                 bitcoin_tool: Optional[BitcoinPriceTool] = None):
        """
        Initialize the code analyzer.
        
        Args:
            llm: Optional LLM instance, will create default if not provided
            predictor_interface: Interface to the core prediction system
            bitcoin_tool: Bitcoin price fetching tool
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=2000
        )
        
        self.predictor_interface = predictor_interface or PredictorInterface()
        self.bitcoin_tool = bitcoin_tool or BitcoinPriceTool()
        self.analysis_chain = self._create_analysis_chain()
        self.analyses_file = Path("code_analyses_log.json")
        
    def _create_analysis_chain(self) -> LLMChain:
        """Create the LangChain code analysis chain."""
        
        analysis_prompt = PromptTemplate(
            input_variables=[
                "prediction_id",
                "prediction_result",
                "actual_result", 
                "price_data",
                "technical_indicators",
                "market_movement",
                "current_code"
            ],
            template="""You are a Bitcoin prediction code improvement analyst. Analyze the following failed prediction to identify specific code improvements.

FAILED PREDICTION DETAILS:
- Prediction ID: {prediction_id}
- Predicted: {prediction_result} (UP or DOWN)
- Actual: {actual_result} (UP or DOWN)
- Price Data: {price_data}
- Technical Indicators Used: {technical_indicators}
- Market Movement: {market_movement}

CURRENT PREDICTION CODE:
```python
{current_code}
```

ANALYSIS REQUIREMENTS:
1. Identify why the prediction failed (market conditions, indicator limitations, logic flaws)
2. Analyze which technical indicators performed poorly
3. Suggest specific code modifications to improve prediction accuracy
4. Consider market context and volatility patterns
5. Provide actionable improvement opportunities

Focus on:
- Moving average calculation improvements
- Momentum calculation adjustments  
- Volume analysis enhancements
- Signal weighting optimizations
- Threshold adjustments for different market conditions

Respond with ONLY a JSON object in this exact format:
{{
    "prediction_id": "{prediction_id}",
    "failure_reason": "Primary reason for failure (1-2 sentences)",
    "market_context": "Market conditions during prediction period",
    "improvement_opportunities": [
        "Specific improvement area 1",
        "Specific improvement area 2",
        "..."
    ],
    "technical_indicators_analysis": {{
        "moving_averages": "Analysis of MA performance",
        "momentum": "Analysis of momentum calculation",
        "volume": "Analysis of volume trend calculation",
        "signal_weighting": "Analysis of signal combination logic"
    }},
    "suggested_modifications": [
        "Specific code change suggestion 1",
        "Specific code change suggestion 2", 
        "..."
    ],
    "confidence_score": 0.0-1.0,
    "timestamp": "{timestamp}"
}}

Make sure the JSON is valid and complete."""
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=analysis_prompt,
            output_parser=AnalysisOutputParser()
        )
    
    def _save_analysis(self, analysis: AnalysisResult):
        """Save analysis result to JSON file."""
        analyses = []
        
        # Load existing analyses
        if self.analyses_file.exists():
            try:
                with open(self.analyses_file, 'r') as f:
                    analyses = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing analyses: {e}")
        
        # Add new analysis
        analyses.append(analysis.dict())
        
        # Save back to file
        try:
            with open(self.analyses_file, 'w') as f:
                json.dump(analyses, f, indent=2)
            logger.info(f"Saved analysis for prediction {analysis.prediction_id}")
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
    
    def _extract_current_code(self) -> str:
        """Extract current prediction code for analysis."""
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
    
    def _format_technical_indicators(self, prediction_record) -> str:
        """Format technical indicators information for analysis."""
        try:
            # Extract indicator data from prediction record if available
            indicators = {
                "confidence": getattr(prediction_record, 'confidence', 'Unknown'),
                "latest_price": getattr(prediction_record, 'latest_price', 'Unknown'),
                "data_points": getattr(prediction_record, 'data_points', 'Unknown'),
                "analysis_period": getattr(prediction_record, 'analysis_period', 'Unknown')
            }
            
            return json.dumps(indicators, indent=2)
        except Exception as e:
            logger.error(f"Failed to format technical indicators: {e}")
            return "Technical indicators data not available"
    
    def analyze_failed_prediction(self, prediction_id: str) -> Optional[AnalysisResult]:
        """
        Analyze a specific failed prediction to identify improvement opportunities.
        
        Args:
            prediction_id: ID of the failed prediction to analyze
            
        Returns:
            AnalysisResult if successful, None if failed
        """
        try:
            # Get prediction from storage
            prediction_record = self.predictor_interface.storage.get_prediction_by_id(prediction_id)
            if not prediction_record:
                logger.error(f"Prediction {prediction_id} not found")
                return None
            
            # Check if prediction actually failed
            if prediction_record.success is not False:
                logger.warning(f"Prediction {prediction_id} did not fail, skipping analysis")
                return None
            
            # Get market data for context
            try:
                current_price_data = self.bitcoin_tool.get_current_price()
                market_movement = f"Current: ${current_price_data['price']:,.2f} (24h: {current_price_data['change_24h']:+.2f}%)"
            except Exception as e:
                logger.warning(f"Failed to get current market data: {e}")
                market_movement = "Market data unavailable"
            
            # Format price data
            price_data = {
                "predicted_price": prediction_record.latest_price,
                "actual_price": getattr(prediction_record, 'actual_price', 'Unknown'),
                "price_change": "Calculated from actual vs predicted"
            }
            
            # Get current prediction code
            current_code = self._extract_current_code()
            
            # Format technical indicators
            technical_indicators = self._format_technical_indicators(prediction_record)
            
            # Run analysis chain
            result = self.analysis_chain.run(
                prediction_id=prediction_id,
                prediction_result=prediction_record.prediction,
                actual_result=getattr(prediction_record, 'actual_outcome', 'Unknown'),
                price_data=json.dumps(price_data, indent=2),
                technical_indicators=technical_indicators,
                market_movement=market_movement,
                current_code=current_code,
                timestamp=datetime.now().isoformat()
            )
            
            # Save analysis
            self._save_analysis(result)
            
            logger.info(f"Completed analysis for failed prediction {prediction_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze prediction {prediction_id}: {e}")
            return None
    
    def analyze_recent_failures(self, max_failures: int = 5) -> List[AnalysisResult]:
        """
        Analyze recent failed predictions to identify improvement patterns.
        
        Args:
            max_failures: Maximum number of recent failures to analyze
            
        Returns:
            List of AnalysisResult objects
        """
        try:
            # Get recent failed predictions
            failed_predictions = self.predictor_interface.get_failed_predictions(max_failures)
            
            if not failed_predictions:
                logger.info("No recent failed predictions found")
                return []
            
            analyses = []
            for prediction in failed_predictions:
                logger.info(f"Analyzing failed prediction {prediction.id}")
                analysis = self.analyze_failed_prediction(prediction.id)
                if analysis:
                    analyses.append(analysis)
            
            logger.info(f"Completed analysis of {len(analyses)} failed predictions")
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to analyze recent failures: {e}")
            return []
    
    def get_improvement_summary(self, analyses: List[AnalysisResult]) -> Dict:
        """
        Generate a summary of improvement opportunities from multiple analyses.
        
        Args:
            analyses: List of AnalysisResult objects
            
        Returns:
            Dict with summary statistics and common patterns
        """
        if not analyses:
            return {
                "total_analyses": 0,
                "average_confidence": 0.0,
                "common_opportunities": [],
                "common_modifications": []
            }
        
        # Count opportunities and modifications
        opportunity_counts = {}
        modification_counts = {}
        
        total_confidence = 0
        
        for analysis in analyses:
            total_confidence += analysis.confidence_score
            
            for opp in analysis.improvement_opportunities:
                opportunity_counts[opp] = opportunity_counts.get(opp, 0) + 1
            
            for mod in analysis.suggested_modifications:
                modification_counts[mod] = modification_counts.get(mod, 0) + 1
        
        # Sort by frequency
        common_opportunities = sorted(opportunity_counts.items(), key=lambda x: x[1], reverse=True)
        common_modifications = sorted(modification_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_analyses": len(analyses),
            "average_confidence": total_confidence / len(analyses),
            "common_opportunities": common_opportunities,
            "common_modifications": common_modifications
        }
    
    def get_analysis_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get history of code analyses from the log file.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List of analysis records
        """
        if not self.analyses_file.exists():
            return []
        
        try:
            with open(self.analyses_file, 'r') as f:
                analyses = json.load(f)
            
            if limit:
                return analyses[-limit:]
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to load analysis history: {e}")
            return [] 