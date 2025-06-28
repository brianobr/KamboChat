"""
Input validation and security for user prompts
"""

import re
import html
from typing import Dict, List, Tuple
from loguru import logger
from src.config import settings


class InputValidator:
    """Validates and sanitizes user inputs for security"""
    
    def __init__(self):
        self.suspicious_patterns = [
            # Prompt injection attempts
            r"ignore.*previous.*instructions",
            r"forget.*previous.*instructions", 
            r"system.*prompt",
            r"ignore.*above",
            r"disregard.*previous",
            r"ignore.*all.*above",
            r"disregard.*all.*above",
            
            # Code injection attempts
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"exec\s*\(",
            
            # SQL injection patterns
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            
            # Command injection
            r"[;&|`$]",
            r"\.\./",
            r"\.\.\\",
            
            # Other malicious patterns
            r"import\s+os",
            r"import\s+subprocess",
            r"__import__",
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def validate_input(self, user_input: str, user_id: str = None) -> Tuple[bool, str, Dict]:
        """
        Validates a user input for malicious content
        
        Returns:
            Tuple of (is_valid, sanitized_input, validation_details)
        """
        validation_details = {
            "original_length": len(user_input),
            "suspicious_patterns_found": [],
            "sanitized": False,
            "user_id": user_id
        }
        
        # Check for suspicious patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(user_input):
                validation_details["suspicious_patterns_found"].append(
                    f"Pattern {i+1}: {pattern.pattern}"
                )
        
        # Check length
        if len(user_input) > settings.max_input_length:
            validation_details["error"] = "Input too long"
            logger.warning(f"Input too long: {len(user_input)} chars from user {user_id}")
            return False, "", validation_details
        
        # If suspicious patterns found, reject
        if validation_details["suspicious_patterns_found"]:
            logger.warning(f"Malicious input detected from user {user_id}: {validation_details}")
            return False, "", validation_details
        
        # Sanitize the input
        sanitized = self._sanitize_input(user_input)
        validation_details["sanitized"] = True
        validation_details["final_length"] = len(sanitized)
        
        return True, sanitized, validation_details
    
    def _sanitize_input(self, user_input: str) -> str:
        """Sanitizes the input by removing potentially dangerous content"""
        # HTML escape
        sanitized = html.escape(user_input)
        
        # Remove any remaining suspicious characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized 