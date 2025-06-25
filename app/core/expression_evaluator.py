"""
Safe expression evaluator for scoring rules.
Uses simpleeval for safe evaluation without exec/eval security risks.
"""

from simpleeval import simple_eval, InvalidExpression
from typing import Dict, Any, Union, Optional
import re
import math
import logging

logger = logging.getLogger(__name__)


class SafeExpressionEvaluator:
    """
    Safe expression evaluator for scoring rules.
    Provides a secure way to evaluate mathematical and logical expressions
    without the security risks of eval().
    """
    
    def __init__(self):
        """Initialize the evaluator with safe functions and operators."""
        self.safe_functions = {
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
            'int': int,
            'float': float,
            'str': str,
            'len': len,
            'sum': sum,
            'avg': lambda x: sum(x) / len(x) if x else 0,
            'sqrt': math.sqrt,
            'pow': pow,
            'log': math.log,
            'ceil': math.ceil,
            'floor': math.floor,
            # String functions
            'lower': lambda x: str(x).lower(),
            'upper': lambda x: str(x).upper(),
            'contains': lambda haystack, needle: str(needle).lower() in str(haystack).lower(),
            # List functions
            'in_list': lambda value, lst: value in lst,
            'not_in_list': lambda value, lst: value not in lst,
        }
        
        self.safe_names = {
            'True': True,
            'False': False,
            'None': None,
            'pi': math.pi,
            'e': math.e,
        }
    
    def evaluate(self, expression: str, data: Dict[str, Any]) -> Any:
        """
        Safely evaluate an expression with given data.
        
        Args:
            expression: The expression to evaluate
            data: Dictionary of variables available to the expression
            
        Returns:
            The result of the expression evaluation
            
        Raises:
            InvalidExpression: If the expression is invalid or unsafe
            ValueError: If there are issues with the data or expression
        """
        try:
            # Sanitize the expression
            expression = self._sanitize_expression(expression)
            
            # Prepare the evaluation context
            context = {**data, **self.safe_names}
            
            # Evaluate the expression
            result = simple_eval(
                expression,
                names=context,
                functions=self.safe_functions
            )
            
            logger.debug(f"Evaluated expression '{expression}' with result: {result}")
            return result
            
        except InvalidExpression as e:
            logger.error(f"Invalid expression '{expression}': {e}")
            raise ValueError(f"Invalid scoring rule expression: {e}")
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            raise ValueError(f"Error in scoring rule: {e}")
    
    def _sanitize_expression(self, expression: str) -> str:
        """
        Basic sanitization of expressions.
        
        Args:
            expression: Raw expression string
            
        Returns:
            Sanitized expression string
        """
        if not expression or not isinstance(expression, str):
            raise ValueError("Expression must be a non-empty string")
        
        # Remove extra whitespace
        expression = expression.strip()
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'__.*__',  # Dunder methods
            r'import\s',
            r'exec\s',
            r'eval\s',
            r'open\s',
            r'file\s',
            r'input\s',
            r'raw_input\s',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ValueError(f"Potentially unsafe expression: contains '{pattern}'")
        
        return expression
    
    def validate_expression(self, expression: str, sample_data: Dict[str, Any]) -> bool:
        """
        Validate an expression against sample data.
        
        Args:
            expression: The expression to validate
            sample_data: Sample data to test the expression
            
        Returns:
            True if the expression is valid, False otherwise
        """
        try:
            self.evaluate(expression, sample_data)
            return True
        except Exception:
            return False
    
    def get_score_for_rules(self, rules: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a set of scoring rules against data.
        
        Args:
            rules: Dictionary of scoring rules
            data: Applicant data
            
        Returns:
            Dictionary with scoring results
        """
        result = {
            'points': 0,
            'max_points': 0,
            'reasoning': [],
            'warnings': []
        }
        
        try:
            # Handle different rule types
            if 'thresholds' in rules:
                result.update(self._evaluate_threshold_rules(rules['thresholds'], data))
            elif 'conditions' in rules:
                result.update(self._evaluate_condition_rules(rules['conditions'], data))
            elif 'expression' in rules:
                result.update(self._evaluate_expression_rule(rules['expression'], data))
            else:
                result['warnings'].append("Unknown rule type")
                
        except Exception as e:
            result['warnings'].append(f"Error evaluating rules: {e}")
            logger.error(f"Error in get_score_for_rules: {e}")
        
        return result
    
    def _evaluate_threshold_rules(self, thresholds: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate threshold-based rules."""
        field = thresholds.get('field')
        ranges = thresholds.get('ranges', [])
        
        if not field or field not in data:
            return {
                'points': 0,
                'max_points': max([r.get('points', 0) for r in ranges], default=0),
                'reasoning': [f"Field '{field}' not available"],
                'warnings': []
            }
        
        value = data[field]
        max_points = max([r.get('points', 0) for r in ranges], default=0)
        
        for range_rule in ranges:
            min_val = range_rule.get('min', float('-inf'))
            max_val = range_rule.get('max', float('inf'))
            points = range_rule.get('points', 0)
            
            if min_val <= value <= max_val:
                return {
                    'points': points,
                    'max_points': max_points,
                    'reasoning': [f"{field}={value} falls in range [{min_val}, {max_val}], awarded {points} points"],
                    'warnings': []
                }
        
        return {
            'points': 0,
            'max_points': max_points,
            'reasoning': [f"{field}={value} does not match any threshold range"],
            'warnings': []
        }
    
    def _evaluate_condition_rules(self, conditions: list, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate condition-based rules."""
        total_points = 0
        max_points = sum([c.get('points', 0) for c in conditions])
        reasoning = []
        warnings = []
        
        for condition in conditions:
            try:
                expr = condition.get('condition')
                points = condition.get('points', 0)
                description = condition.get('description', expr)
                
                if self.evaluate(expr, data):
                    total_points += points
                    reasoning.append(f"Condition met: {description} (+{points} points)")
                else:
                    reasoning.append(f"Condition not met: {description}")
                    
            except Exception as e:
                warnings.append(f"Error evaluating condition: {e}")
        
        return {
            'points': total_points,
            'max_points': max_points,
            'reasoning': reasoning,
            'warnings': warnings
        }
    
    def _evaluate_expression_rule(self, expression: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single expression rule."""
        try:
            points = self.evaluate(expression, data)
            return {
                'points': max(0, int(points)),  # Ensure non-negative integer
                'max_points': 100,  # Default max for expression rules
                'reasoning': [f"Expression '{expression}' evaluated to {points} points"],
                'warnings': []
            }
        except Exception as e:
            return {
                'points': 0,
                'max_points': 100,
                'reasoning': [f"Expression '{expression}' failed to evaluate"],
                'warnings': [f"Expression error: {e}"]
            }