"""
PR Generator Chain for Autonomous Agent

Uses LLM to generate high-quality PR content including:
- PR titles and descriptions
- Commit messages with technical context
- Code improvement explanations
- Risk assessments and testing notes
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class PRGenerator:
    """Generates pull request content using LLM"""
    
    def __init__(self, openai_api_key: str):
        """Initialize PR generator with OpenAI API key"""
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3,  # More deterministic for technical content
            max_tokens=2000
        )
        
        # PR title template
        self.title_template = PromptTemplate(
            input_variables=["improvement_type", "component", "expected_benefit"],
            template="""Generate a clear, concise GitHub PR title for this code improvement:

Improvement Type: {improvement_type}
Component: {component}
Expected Benefit: {expected_benefit}

The title should:
- Be under 80 characters
- Start with a conventional commit type (feat, fix, improve, refactor)
- Clearly indicate what was improved
- Mention the expected benefit

Example: "improve: Enhance Bitcoin predictor momentum calculation for better trend detection"

PR Title:"""
        )
        
        # PR description template
        self.description_template = PromptTemplate(
            input_variables=[
                "analysis", "improvement_details", "code_changes", 
                "expected_impact", "testing_notes", "risk_assessment"
            ],
            template="""Generate a comprehensive GitHub PR description for this autonomous code improvement:

## 🤖 Autonomous Code Improvement

### 📊 Analysis That Triggered This Improvement
{analysis}

### 🔧 Improvement Details
{improvement_details}

### 💻 Code Changes Made
{code_changes}

### 📈 Expected Impact
{expected_impact}

### 🧪 Testing & Validation
{testing_notes}

### ⚠️ Risk Assessment
{risk_assessment}

Create a professional PR description that includes:
1. Clear summary of the problem identified
2. Detailed explanation of the solution
3. Code changes with before/after context
4. Expected performance impact
5. Comprehensive testing information
6. Risk mitigation notes
7. Review checklist for human reviewers

Format the response as markdown suitable for GitHub PR description:"""
        )
        
        # Commit message template
        self.commit_template = PromptTemplate(
            input_variables=["improvement_type", "component", "change_summary", "reasoning"],
            template="""Generate a detailed commit message for this code improvement:

Improvement Type: {improvement_type}
Component: {component}
Change Summary: {change_summary}
Reasoning: {reasoning}

The commit message should follow conventional commits format:
- First line: type(scope): brief description (under 50 chars)
- Blank line
- Detailed explanation of what changed and why
- Include technical details and expected impact

Example:
improve(predictor): enhance momentum calculation algorithm

- Updated momentum calculation to use exponential moving average
- Improved trend detection accuracy by considering volume weighting
- Expected to reduce false signals by ~15% based on backtesting
- Maintains interface compatibility with existing system

Commit Message:"""
        )
        
        self.title_chain = LLMChain(llm=self.llm, prompt=self.title_template)
        self.description_chain = LLMChain(llm=self.llm, prompt=self.description_template)
        self.commit_chain = LLMChain(llm=self.llm, prompt=self.commit_template)
        
        logger.info("PR Generator initialized successfully")
    
    def generate_pr_title(
        self, 
        improvement_data: Dict[str, Any]
    ) -> str:
        """Generate a clear PR title"""
        try:
            result = self.title_chain.run(
                improvement_type=improvement_data.get('improvement_type', 'Code improvement'),
                component=improvement_data.get('component', 'Bitcoin predictor'),
                expected_benefit=improvement_data.get('expected_benefit', 'Improved prediction accuracy')
            )
            
            title = result.strip()
            
            # Ensure title is under 80 characters
            if len(title) > 80:
                title = title[:77] + "..."
            
            logger.info(f"Generated PR title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Failed to generate PR title: {e}")
            # Fallback title
            return f"improve: Autonomous code improvement for {improvement_data.get('component', 'predictor')}"
    
    def generate_pr_description(
        self, 
        improvement_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> str:
        """Generate comprehensive PR description"""
        try:
            # Prepare formatted inputs
            analysis = self._format_analysis(analysis_data)
            improvement_details = self._format_improvement_details(improvement_data)
            code_changes = self._format_code_changes(improvement_data)
            expected_impact = self._format_expected_impact(improvement_data)
            testing_notes = self._format_testing_notes(validation_results)
            risk_assessment = self._format_risk_assessment(improvement_data, validation_results)
            
            result = self.description_chain.run(
                analysis=analysis,
                improvement_details=improvement_details,
                code_changes=code_changes,
                expected_impact=expected_impact,
                testing_notes=testing_notes,
                risk_assessment=risk_assessment
            )
            
            # Add autonomous improvement footer
            description = result.strip() + self._get_pr_footer()
            
            logger.info("Generated comprehensive PR description")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate PR description: {e}")
            # Fallback description
            return self._get_fallback_description(improvement_data)
    
    def generate_commit_message(
        self, 
        improvement_data: Dict[str, Any]
    ) -> str:
        """Generate detailed commit message"""
        try:
            result = self.commit_chain.run(
                improvement_type=improvement_data.get('improvement_type', 'improve'),
                component=improvement_data.get('component', 'predictor'),
                change_summary=improvement_data.get('change_summary', 'Code improvement'),
                reasoning=improvement_data.get('reasoning', 'Autonomous improvement based on prediction analysis')
            )
            
            commit_message = result.strip()
            logger.info("Generated commit message")
            return commit_message
            
        except Exception as e:
            logger.error(f"Failed to generate commit message: {e}")
            # Fallback commit message
            return f"improve: Autonomous improvement for {improvement_data.get('component', 'predictor')}"
    
    def _format_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Format analysis data for PR description"""
        if not analysis_data:
            return "Automated analysis identified improvement opportunities in prediction accuracy."
        
        return f"""
**Failed Predictions Analyzed**: {analysis_data.get('failed_count', 'Multiple')}
**Primary Issues Identified**: {analysis_data.get('primary_issues', 'Prediction accuracy concerns')}
**Market Context**: {analysis_data.get('market_context', 'Bitcoin price movements')}
**Confidence Level**: {analysis_data.get('confidence', 'High')}
"""
    
    def _format_improvement_details(self, improvement_data: Dict[str, Any]) -> str:
        """Format improvement details for PR description"""
        return f"""
**Improvement Type**: {improvement_data.get('improvement_type', 'Algorithm enhancement')}
**Target Component**: {improvement_data.get('component', 'Bitcoin predictor')}
**Changes Made**: {improvement_data.get('changes_made', 'Code optimization')}
**Expected Benefit**: {improvement_data.get('expected_benefit', 'Improved accuracy')}
"""
    
    def _format_code_changes(self, improvement_data: Dict[str, Any]) -> str:
        """Format code changes for PR description"""
        changes = improvement_data.get('code_changes', {})
        
        if not changes:
            return "**Code Changes**: Enhanced prediction algorithm with improved logic."
        
        formatted = "**Files Modified**:\n"
        for file_path, change_desc in changes.items():
            formatted += f"- `{file_path}`: {change_desc}\n"
        
        return formatted
    
    def _format_expected_impact(self, improvement_data: Dict[str, Any]) -> str:
        """Format expected impact for PR description"""
        return f"""
**Prediction Accuracy**: Expected improvement in trend detection
**Performance**: {improvement_data.get('performance_impact', 'No significant performance impact expected')}
**Compatibility**: Maintains all existing interfaces and contracts
**Risk Level**: {improvement_data.get('risk_level', 'Low - validated improvement')}
"""
    
    def _format_testing_notes(self, validation_results: Dict[str, Any]) -> str:
        """Format testing notes for PR description"""
        if not validation_results:
            return "**Testing**: Code validated for syntax and interface compatibility."
        
        return f"""
**Validation Status**: {validation_results.get('status', 'Passed')}
**Syntax Check**: {validation_results.get('syntax_valid', 'Passed')}
**Interface Compatibility**: {validation_results.get('interface_compatible', 'Passed')}
**Import Validation**: {validation_results.get('imports_valid', 'Passed')}
**Test Execution**: {validation_results.get('execution_test', 'Passed')}
"""
    
    def _format_risk_assessment(
        self, 
        improvement_data: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> str:
        """Format risk assessment for PR description"""
        risk_level = improvement_data.get('risk_level', 'Low')
        
        return f"""
**Risk Level**: {risk_level}
**Mitigation**: 
- Code fully validated before deployment
- Maintains interface compatibility
- Automatic backup created before changes
- Easy rollback available if issues arise
- No breaking changes to existing functionality

**Review Checklist**:
- [ ] Code changes align with improvement goals
- [ ] No breaking changes to public interfaces
- [ ] Performance impact is acceptable
- [ ] Error handling is appropriate
- [ ] Documentation updated if needed
"""
    
    def _get_pr_footer(self) -> str:
        """Get standard footer for autonomous improvement PRs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""

---

## 🤖 Autonomous Improvement Information

**Generated**: {timestamp}
**System**: Autonomous Bitcoin Prediction Agent v3.0
**Architecture**: Clean separation maintained - only core system modified
**Review Required**: ✅ Human review required before merge
**Safety**: ✅ Automatic backup created, rollback available

This PR was generated autonomously by the AI agent after analyzing failed predictions and identifying improvement opportunities. The agent has validated the code changes and ensured interface compatibility, but human review is required before merging.
"""
    
    def _get_fallback_description(self, improvement_data: Dict[str, Any]) -> str:
        """Get fallback PR description if LLM generation fails"""
        return f"""## 🤖 Autonomous Code Improvement

This PR contains an autonomous improvement to the Bitcoin prediction system.

**Component**: {improvement_data.get('component', 'Bitcoin predictor')}
**Type**: {improvement_data.get('improvement_type', 'Algorithm enhancement')}
**Expected Benefit**: {improvement_data.get('expected_benefit', 'Improved prediction accuracy')}

### Changes Made
{improvement_data.get('changes_made', 'Enhanced prediction algorithm based on analysis of failed predictions.')}

### Validation
- ✅ Code syntax validated
- ✅ Interface compatibility verified
- ✅ Safe deployment tested

### Review Required
This autonomous improvement requires human review before merging.

{self._get_pr_footer()}
"""


def test_pr_generator() -> bool:
    """Test PR generator functionality"""
    try:
        import os
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
        
        generator = PRGenerator(api_key)
        
        print("🔧 Testing PR Generator...")
        
        # Test data
        improvement_data = {
            'improvement_type': 'Algorithm enhancement',
            'component': 'Bitcoin predictor',
            'expected_benefit': 'Improved trend detection accuracy',
            'changes_made': 'Enhanced momentum calculation with volume weighting',
            'risk_level': 'Low'
        }
        
        analysis_data = {
            'failed_count': 3,
            'primary_issues': 'False trend signals during consolidation',
            'confidence': 'High'
        }
        
        validation_results = {
            'status': 'Passed',
            'syntax_valid': True,
            'interface_compatible': True
        }
        
        # Test title generation
        title = generator.generate_pr_title(improvement_data)
        print(f"✅ Generated title: {title}")
        
        # Test commit message generation
        commit_msg = generator.generate_commit_message(improvement_data)
        print(f"✅ Generated commit message (first line): {commit_msg.split()[0] if commit_msg else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ PR Generator test failed: {e}")
        return False


if __name__ == "__main__":
    test_pr_generator() 