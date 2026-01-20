"""
Input validation utilities for the Flask authentication application.
"""
import re
from email_validator import validate_email, EmailNotValidError


def validate_username(username):
    """
    Validate username format.
    
    Args:
        username (str): Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3 and 20 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username must contain only alphanumeric characters and underscores"
    
    return True, None


def validate_email_format(email):
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    try:
        # Validate and normalize the email address
        valid = validate_email(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_password_strength(password):
    """
    Validate password strength.
    Requirements: min 8 chars, uppercase, lowercase, number, special char
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def validate_role(role):
    """
    Validate user role.
    
    Args:
        role (str): Role to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_roles = ['guest', 'user', 'admin']
    
    if role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    return True, None


def sanitize_input(value):
    """
    Basic input sanitization to prevent XSS attacks.
    
    Args:
        value (str): Input value to sanitize
        
    Returns:
        str: Sanitized value
    """
    if not isinstance(value, str):
        return value
    
    # Remove potential HTML tags
    value = re.sub(r'<[^>]*>', '', value)
    
    # Trim whitespace
    value = value.strip()
    
    return value
