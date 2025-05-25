"""Code validation tool for ensuring safe and compatible code improvements."""

import ast
import json
import logging
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..interfaces.predictor_interface import PredictorInterface

logger = logging.getLogger(__name__)


class CodeValidator:
    """Validator for generated Bitcoin prediction code improvements."""
    
    def __init__(self, predictor_interface: Optional[PredictorInterface] = None):
        """
        Initialize the code validator.
        
        Args:
            predictor_interface: Interface to the core prediction system
        """
        self.predictor_interface = predictor_interface or PredictorInterface()
        self.validation_log = Path("code_validation_log.json")
        
    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate code syntax using Python AST parser.
        
        Args:
            code: Code to validate
            
        Returns:
            Dict with validation results
        """
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Check for basic structure
            has_function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            
            return {
                "valid": True,
                "has_function": has_function,
                "message": "Syntax validation passed",
                "ast_nodes": len(list(ast.walk(tree)))
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "error": "Syntax error",
                "message": str(e),
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            return {
                "valid": False,
                "error": "Parsing error",
                "message": str(e)
            }
    
    def validate_function_signature(self, code: str, expected_function: str = "analyze") -> Dict[str, Any]:
        """
        Validate that the code contains the expected function signature.
        
        Args:
            code: Code to validate
            expected_function: Expected function name
            
        Returns:
            Dict with validation results
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == expected_function:
                    # Check function signature
                    args = [arg.arg for arg in node.args.args]
                    
                    # Expected signature: analyze(self, price_data: List[OHLCVData]) -> AnalysisResult
                    has_self = len(args) >= 1 and args[0] == "self"
                    has_price_data = len(args) >= 2 and args[1] == "price_data"
                    
                    return {
                        "valid": True,
                        "function_found": True,
                        "has_self": has_self,
                        "has_price_data": has_price_data,
                        "arg_count": len(args),
                        "args": args,
                        "message": "Function signature validation passed"
                    }
            
            return {
                "valid": False,
                "function_found": False,
                "error": f"Function '{expected_function}' not found",
                "message": f"Code must contain a function named '{expected_function}'"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Signature validation failed",
                "message": str(e)
            }
    
    def validate_imports_and_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Validate that the code doesn't introduce dangerous imports or dependencies.
        
        Args:
            code: Code to validate
            
        Returns:
            Dict with validation results
        """
        try:
            tree = ast.parse(code)
            
            # Collect all imports
            imports = []
            dangerous_imports = ['os', 'subprocess', 'sys', 'exec', 'eval', '__import__']
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            # Check for dangerous imports
            dangerous_found = [imp for imp in imports if any(danger in imp for danger in dangerous_imports)]
            
            return {
                "valid": len(dangerous_found) == 0,
                "imports": imports,
                "dangerous_imports": dangerous_found,
                "message": "Safe imports" if not dangerous_found else f"Dangerous imports found: {dangerous_found}"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Import validation failed",
                "message": str(e)
            }
    
    def validate_return_type(self, code: str) -> Dict[str, Any]:
        """
        Validate that the function returns the expected type.
        
        Args:
            code: Code to validate
            
        Returns:
            Dict with validation results
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "analyze":
                    # Look for return statements
                    return_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                    
                    if not return_nodes:
                        return {
                            "valid": False,
                            "error": "No return statement found",
                            "message": "Function must return AnalysisResult"
                        }
                    
                    # Check if any return contains AnalysisResult
                    has_analysis_result = "AnalysisResult" in code
                    
                    return {
                        "valid": has_analysis_result,
                        "return_count": len(return_nodes),
                        "has_analysis_result": has_analysis_result,
                        "message": "Return type validation passed" if has_analysis_result else "Must return AnalysisResult"
                    }
            
            return {
                "valid": False,
                "error": "Function not found",
                "message": "analyze function not found for return type validation"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Return type validation failed",
                "message": str(e)
            }
    
    def test_code_execution(self, code: str, use_mock_data: bool = True) -> Dict[str, Any]:
        """
        Test code execution in a safe environment.
        
        Args:
            code: Code to test
            use_mock_data: Whether to use mock data for testing
            
        Returns:
            Dict with execution test results
        """
        try:
            # Create a temporary file with the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                test_code = self._create_test_code(code, use_mock_data)
                temp_file.write(test_code)
                temp_file_path = temp_file.name
            
            try:
                # Run the test code in a subprocess for safety
                result = subprocess.run(
                    [sys.executable, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                if result.returncode == 0:
                    return {
                        "valid": True,
                        "executed": True,
                        "output": result.stdout,
                        "message": "Code execution test passed"
                    }
                else:
                    return {
                        "valid": False,
                        "executed": False,
                        "error": result.stderr,
                        "message": "Code execution failed"
                    }
                    
            finally:
                # Clean up temporary file
                Path(temp_file_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "error": "Execution timeout",
                "message": "Code execution took too long (>30s)"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": "Test execution failed",
                "message": str(e)
            }
    
    def _create_test_code(self, method_code: str, use_mock_data: bool = True) -> str:
        """Create complete test code for execution testing."""
        if use_mock_data:
            test_code = f"""
import sys
from datetime import datetime
from typing import List
from dataclasses import dataclass

# Mock data models
@dataclass
class OHLCVData:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass 
class AnalysisResult:
    short_ma: float
    long_ma: float
    momentum: float
    volume_trend: float
    bullish_signals: float
    prediction: str
    confidence: float
    reasoning: List[str]

# Mock predictor class with the improved method
class TestPredictor:
{method_code}

# Test the method
try:
    # Create mock data
    mock_data = [
        OHLCVData("2024-01-01", 40000, 41000, 39000, 40500, 1000000),
        OHLCVData("2024-01-02", 40500, 42000, 40000, 41500, 1100000),
        OHLCVData("2024-01-03", 41500, 43000, 41000, 42000, 1200000),
        OHLCVData("2024-01-04", 42000, 43500, 41500, 43000, 1300000),
        OHLCVData("2024-01-05", 43000, 44000, 42500, 43500, 1400000),
        OHLCVData("2024-01-06", 43500, 45000, 43000, 44000, 1500000),
        OHLCVData("2024-01-07", 44000, 45500, 43500, 45000, 1600000),
    ]
    
    predictor = TestPredictor()
    result = predictor.analyze(mock_data)
    
    print(f"Test passed: prediction={{result.prediction}}, confidence={{result.confidence}}")
    print(f"Technical indicators: MA={{result.short_ma:.2f}}/{{result.long_ma:.2f}}, momentum={{result.momentum:.4f}}")
    
except Exception as e:
    print(f"Test failed: {{e}}")
    sys.exit(1)
"""
        else:
            # Use actual data if available
            test_code = f"""
# Real data test would go here
# For now, just test syntax
{method_code}
print("Syntax test passed")
"""
        
        return test_code
    
    def validate_interface_compatibility(self, code: str) -> Dict[str, Any]:
        """
        Validate that the code maintains interface compatibility.
        
        Args:
            code: Code to validate
            
        Returns:
            Dict with compatibility validation results
        """
        try:
            # Check all validation aspects
            syntax_result = self.validate_syntax(code)
            signature_result = self.validate_function_signature(code)
            imports_result = self.validate_imports_and_dependencies(code)
            return_result = self.validate_return_type(code)
            
            # Overall compatibility check
            all_valid = all([
                syntax_result.get("valid", False),
                signature_result.get("valid", False),
                imports_result.get("valid", False),
                return_result.get("valid", False)
            ])
            
            return {
                "valid": all_valid,
                "syntax": syntax_result,
                "signature": signature_result,
                "imports": imports_result,
                "return_type": return_result,
                "message": "Interface compatibility validated" if all_valid else "Interface compatibility issues found"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Compatibility validation failed",
                "message": str(e)
            }
    
    def comprehensive_validation(self, code: str, test_execution: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive validation of generated code.
        
        Args:
            code: Code to validate
            test_execution: Whether to test code execution
            
        Returns:
            Dict with comprehensive validation results
        """
        validation_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run all validation checks
            results = {
                "validation_id": validation_id,
                "timestamp": datetime.now().isoformat(),
                "code_length": len(code),
                "interface_compatibility": self.validate_interface_compatibility(code)
            }
            
            # Add execution test if requested
            if test_execution:
                results["execution_test"] = self.test_code_execution(code)
            
            # Overall validation result
            interface_valid = results["interface_compatibility"].get("valid", False)
            execution_valid = results.get("execution_test", {}).get("valid", True)  # Default True if not tested
            
            results["overall_valid"] = interface_valid and execution_valid
            results["summary"] = self._create_validation_summary(results)
            
            # Save validation result
            self._save_validation_result(results)
            
            return results
            
        except Exception as e:
            return {
                "validation_id": validation_id,
                "overall_valid": False,
                "error": "Comprehensive validation failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_validation_summary(self, results: Dict) -> str:
        """Create a human-readable validation summary."""
        if results.get("overall_valid", False):
            return "✅ All validation checks passed - code is safe and compatible"
        
        issues = []
        
        interface_result = results.get("interface_compatibility", {})
        if not interface_result.get("valid", False):
            if not interface_result.get("syntax", {}).get("valid", False):
                issues.append("Syntax errors")
            if not interface_result.get("signature", {}).get("valid", False):
                issues.append("Function signature issues")
            if not interface_result.get("imports", {}).get("valid", False):
                issues.append("Unsafe imports")
            if not interface_result.get("return_type", {}).get("valid", False):
                issues.append("Return type issues")
        
        execution_result = results.get("execution_test", {})
        if execution_result and not execution_result.get("valid", False):
            issues.append("Execution test failed")
        
        return f"❌ Validation failed: {', '.join(issues)}"
    
    def _save_validation_result(self, result: Dict):
        """Save validation result to log file."""
        validations = []
        
        # Load existing validations
        if self.validation_log.exists():
            try:
                with open(self.validation_log, 'r') as f:
                    validations = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing validations: {e}")
        
        # Add new validation
        validations.append(result)
        
        # Save back to file
        try:
            with open(self.validation_log, 'w') as f:
                json.dump(validations, f, indent=2)
            logger.info(f"Saved validation result {result.get('validation_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to save validation result: {e}")
    
    def get_validation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get history of code validations.
        
        Args:
            limit: Maximum number of validations to return
            
        Returns:
            List of validation records
        """
        if not self.validation_log.exists():
            return []
        
        try:
            with open(self.validation_log, 'r') as f:
                validations = json.load(f)
            
            if limit:
                return validations[-limit:]
            return validations
            
        except Exception as e:
            logger.error(f"Failed to load validation history: {e}")
            return [] 